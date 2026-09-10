import argparse
import time
import numpy as np
from common import DATASETS, E23, RUN, check_lock, dump, identity, read, sha
from jobs import model_method, run_job


def assert_frozen(path):
    for item in read(path)['files']:
        assert sha(item['path'])==item['sha256'],item['path']


def cal():
    lock=check_lock();assert read(RUN/'reviews/recovery_gate.json')['status']=='PASS'
    files=[]
    for ds in DATASETS:
        allmodels=read(RUN/'models'/ds/'complete.json')
        assert allmodels['status']=='ALL_EIGHT_PROFILES_BUILT_BEFORE_CAL'
        for m in allmodels['models']:
            assert sha(m['W'])==m['W_identity']['sha256']
            files.extend([identity(m['W']),identity(RUN/'models'/ds/m['name']/'manifest.json')])
        files.append(identity(RUN/'models'/ds/'complete.json'))
        files.extend(identity(RUN/'inputs'/ds/p) for p in ['hub_ids.i32','raw_hubs.f32','P0_reference.f32','prepared.json',
            'fit/queries.f32','fit/gt.i64','fit/row_ids.i64','cal/queries.f32','cal/gt.i64','cal/row_ids.i64'])
    files.extend(identity(p) for p in sorted((RUN/'src').glob('*')) if p.is_file())
    files.extend(identity(p) for p in [RUN/'bin/evaluate',RUN/'protocol.md',RUN/'config.locked.json'])
    freeze=RUN/'models/frozen_before_cal.json';assert not freeze.exists()
    dump(freeze,{'status':'ALL_PROFILES_AND_EXECUTION_FROZEN_BEFORE_CAL','unix':time.time(),'files':files})
    for ds in DATASETS:
        assert_frozen(freeze)
        models=read(RUN/'models'/ds/'complete.json')['models']
        config=read(RUN/'inputs'/ds/'cal/config.json')
        config.update({'measure_wall':True,'base_count':read(RUN/'inputs'/ds/'prepared.json')['base_rows'],
                       'methods':[model_method(ds,m,exact=exact) for m in models for exact in [False,True]]})
        run_job('cal_'+ds,config,RUN/'diagnostics'/ds/'cal')
    # No candidate decisions until both complete predeclared tables are on disk.
    decisions={};frozen=[]
    for ds in DATASETS:
        models=read(RUN/'models'/ds/'complete.json')['models']
        allresults=read(RUN/'diagnostics'/ds/'cal/results.json')
        results={m['configuration']['model_name']:m for m in allresults['methods'] if not m['configuration']['exact']}
        def key(m):
            metric=results[m['name']]
            family_order={'gt1_hard':-1,'gt10_hard':0,'gt1_soft':1,'gt10_soft':2}
            return (-metric['total_hits'],metric['mean_graph_ndc'],family_order[m['family']],m['temperature'] or 0)
        selected={family:min([m for m in models if m['family']==family],key=key)
                  for family in ['gt10_hard','gt1_soft','gt10_soft']}
        primary=min(selected.values(),key=key);baseline=results['gt1_hard'];chosen=results[primary['name']]
        gate=chosen['total_hits']>baseline['total_hits']
        decision={'status':'SELECTED_BEFORE_AUDIT_VALIDATION','selected_families':selected,
             'primary':primary,'primary_cal_hits':chosen['total_hits'],'baseline_cal_hits':baseline['total_hits'],
             'primary_cal_delta_pp':100*(chosen['recall_at_10']-baseline['recall_at_10']),
             'cal_gate_pass':gate,'best_including_fast':primary['name'] if gate else 'gt1_hard',
             'rule':lock['selection_ties'],'cal_results':identity(RUN/'diagnostics'/ds/'cal/results.json'),
             'audit_used':False,'validation_used':False,'heldout_used':False}
        dump(RUN/'models'/ds/'selection.json',decision);decisions[ds]=decision
        frozen.extend([identity(RUN/'models'/ds/'selection.json'),identity(RUN/'models'/ds/'complete.json')])
        frozen.extend(identity(m['W']) for m in models)
        print(ds,'CAL_PRIMARY',primary['name'],round(decision['primary_cal_delta_pp'],4),'pp','PASS' if gate else 'STOP',flush=True)
    gate=all(x['cal_gate_pass'] for x in decisions.values())
    dump(RUN/'reviews/cal_gate.json',{'status':'PASS' if gate else 'STOP_NO_CROSS_DATASET_CAL_GAIN',
        'datasets':decisions,'validation_allowed':gate,'rule':lock['gate'],'audit_report_still_scheduled':True})
    dump(RUN/'models/frozen_before_audit.json',{'status':'FROZEN_SELECTIONS_BEFORE_AUDIT','unix':time.time(),
                                              'files':frozen,'protocol_sha256':lock['protocol_sha256']})
    dump(RUN/'state.json',{'status':'CAL_COMPLETE_AUDIT_PENDING','cal_gate_pass':gate,
                         'validation_opened':False,'heldout_opened':False})


def audit():
    check_lock();assert_frozen(RUN/'models/frozen_before_cal.json');assert_frozen(RUN/'models/frozen_before_audit.json')
    for ds in DATASETS:
        src=E23/'inputs'/ds/'audit';old=read(src/'config.json')
        part=RUN/'inputs'/ds/'audit';assert not part.exists();part.mkdir()
        n,d=1024,old['dim'];assert old['gt_k']==100 and old['num_queries']==n
        for name,key,dtype,width in [('queries.f32','queries_file','<f4',d),('gt.i64','gt_file','<i8',100),('row_ids.i64','row_ids','<i8',1)]:
            arr=np.fromfile(old[key],dtype=dtype);assert arr.size==n*width
            if name=='row_ids.i64':assert np.array_equal(arr,np.arange(1024,2048))
            arr.tofile(part/name)
        original=read(RUN/'inputs'/ds/'prepared.json')['source_train']
        qsource=np.memmap(original['query_train']['path'],dtype='<f4',mode='r',shape=(30000,d+1))
        gsource=np.memmap(original['gt_train']['path'],dtype='<i4',mode='r',shape=(30000,101))
        assert np.array_equal(qsource[1024:2048,1:],np.fromfile(part/'queries.f32',dtype='<f4').reshape(n,d))
        assert np.array_equal(gsource[1024:2048,1:],np.fromfile(part/'gt.i64',dtype='<i8').reshape(n,100))
        config={**old,'queries_file':str(part/'queries.f32'),'gt_file':str(part/'gt.i64'),
                'row_ids':str(part/'row_ids.i64'),'measure_wall':False,
                'base_count':read(RUN/'inputs'/ds/'prepared.json')['base_rows']}
        dump(part/'config.json',config)
        selected=read(RUN/'models'/ds/'selection.json')['selected_families']
        models=[read(RUN/'models'/ds/'gt1_hard/manifest.json')]+list(selected.values())
        config['methods']=[model_method(ds,m,exact=exact) for m in models for exact in [False,True]]
        run_job('audit_'+ds,config,RUN/'diagnostics'/ds/'audit')
        dump(part/'provenance.json',{'source_config':identity(src/'config.json'),
             'source_files':[identity(old[k]) for k in ['queries_file','gt_file','row_ids']],
             'selection_freeze':identity(RUN/'models/frozen_before_audit.json'),'report_only':True})
    cal_gate=read(RUN/'reviews/cal_gate.json')
    dump(RUN/'state.json',{'status':'AUDIT_COMPLETE_P3_PENDING' if cal_gate['validation_allowed'] else 'STOP_NO_CROSS_DATASET_CAL_GAIN',
                         'validation_opened':False,'heldout_opened':False,'no_more_tuning':True})
    print('AUDIT_COMPLETE',cal_gate['status'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['cal','audit'])
    args=parser.parse_args()
    (cal if args.stage=='cal' else audit)()
