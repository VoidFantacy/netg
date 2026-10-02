"""Freeze E26 before constructing any new image or accessing its new development rows."""
import argparse
import os
import shutil
import time
from pathlib import Path
import numpy as np
from common import ROOT,RUN,E24,E25,DATASETS,ALPHAS,LS,read,dump,identity,sha,check_lock,frozen_check,update_state


def raw_rows(ds, positions, stage):
    meta=read(E24/'inputs'/ds/'prepared.json');source=meta['source_train'];dim=meta['dim']
    queries=np.memmap(source['query_train']['path'],mode='r',dtype='<f4').reshape(30000,dim+1)
    gt=np.memmap(source['gt_train']['path'],mode='r',dtype='<i4').reshape(30000,101)
    assert np.all(queries[positions,0].copy().view('<i4')==dim) and np.all(gt[positions,0]==100)
    q=np.ascontiguousarray(queries[positions,1:],dtype='<f4');g=np.ascontiguousarray(gt[positions,1:],dtype='<i8')
    assert np.isfinite(q).all() and (g>=0).all() and (g<meta['base_rows']).all()
    assert all(len(set(row[:10]))==10 for row in g)
    out=RUN/'inputs'/ds/stage;out.mkdir(parents=True,exist_ok=False)
    q.tofile(out/'queries.f32');g.tofile(out/'gt.i64');positions.astype('<i8').tofile(out/'row_ids.i64')
    c={'dataset':ds,'split':stage,'num_queries':len(positions),'dim':dim,'gt_k':100,'index_path':meta['index_path'],
       'base_count':meta['base_rows'],'queries_file':str(out/'queries.f32'),'gt_file':str(out/'gt.i64'),'row_ids':str(out/'row_ids.i64')}
    dump(out/'config.json',c);dump(out/'provenance.json',{'source':source,'original_header_and_rows_verified':True,
         'row_range_half_open':[int(positions.min()),int(positions.max())+1],
         'outputs':[identity(out/p) for p in ['queries.f32','gt.i64','row_ids.i64']],
         'historically_used_development_pool':True,'prepared_unix':time.time()})


def initialize():
    start=time.monotonic();assert not (RUN/'config.locked.json').exists()
    assert read(E25/'reviews/final_audit.json')['status']=='PASS'
    assert 15 in os.sched_getaffinity(0)
    lock={'experiment':'E26_profile_shrinkage_v1','protocol_sha256':sha(RUN/'protocol.md'),
        'alphas':ALPHAS,'cal_rows':[6144,8192],'audit_rows':[8192,10000],'validation_n':2000,
        'L':LS,'development_L':[64,128],'timing_repeats':3,'query_cpu':15,
        'normal_real_call_cap':897280,'repair_real_call_cap':16384,'total_real_call_cap':913664,
        'synthetic_call_cap':4096,'rss_limit_bytes':40<<30,'output_limit_bytes':1<<30,
        'min_free_bytes':10<<30,'job_timeout_seconds':1800,'total_search_seconds':7200,
        'seed':20260910,'heldout_allowed':False,'R_target':.75,'Rh_target':.75,'A_all_target':.25,'Ah_all_target':.25}
    assert 1600+82240+72640+700800+40000==lock['normal_real_call_cap']
    assert shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    dump(RUN/'config.locked.json',lock)
    dump(RUN/'reviews/protocol_lock.json',{'locked_unix':time.time(),'config_sha256':sha(RUN/'config.locked.json'),
         'protocol_sha256':lock['protocol_sha256'],'before_any_new_alpha_W_or_development_rows':True})
    for name in ['src','bin','logs','configs','inputs','models','results','diagnostics','source_before']:(RUN/name).mkdir(exist_ok=True)
    protected={}
    def protect(path,expected=None):
        path=str(Path(path).resolve())
        if path not in protected:protected[path]=identity(path)
        if expected:assert protected[path]['sha256']==expected,path
    for item in read(E25/'reviews/immutable_integrity.json')['protected_upstream']:
        protect(item['path'],item['sha256'])
    for name in ['protocol.md','config.locked.json','state.json','report.md','results/summary.json','results/analysis.json',
                 'models/frozen_before_audit.json','reviews/final_audit.json','reviews/immutable_integrity.json','src/benchmark_with_nsg.cpp','src/legacy_reference.cpp']:
        protect(E25/name)
    for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
        shutil.copy2(ROOT/name,RUN/'source_before'/name);protect(RUN/'source_before'/name)
    for name in ['benchmark_with_nsg.cpp','legacy_reference.cpp']:
        dest=RUN/'src'/name;assert not dest.exists();shutil.copy2(E25/'src'/name,dest)
        assert sha(dest)==sha(E25/'src'/name)
    for ds in DATASETS:
        meta=read(E24/'inputs'/ds/'prepared.json')
        assert meta['H']==(815 if ds.startswith('webvid') else 821)
        raw_rows(ds,np.arange(32),'recovery');raw_rows(ds,np.arange(6144,8192),'cal')
        out=RUN/'inputs'/ds
        ids=E24/'inputs'/ds/'hub_ids.i32';shutil.copy2(ids,out/'hub_ids.i32')
        assert np.all(np.diff(np.fromfile(out/'hub_ids.i32',dtype='<i4'))>0)
        old=read(E25/'inputs'/ds/'policies.json')
        for role in ['A0','A1']:
            for key in ['W','mapping','tie_ids']:protect(old[role][key])
        dump(out/'endpoints.json',old)
    dump(RUN/'reviews/protected_before.json',list(protected.values()))
    dump(RUN/'inputs/preflight.json',{'status':'PASS','seconds':time.monotonic()-start,
        'protected_files':len(protected),'cal_rows_verified':[6144,8192],
        'audit_and_validation_preparation_deferred':True,'new_profiles_constructed':False,
        'whole_train_hash_includes_audit_bytes_for_identity_only':True,'heldout_opened':False})
    update_state(status='PROTOCOL_LOCKED_INPUTS_READY',active_job=None,heldout_opened=False,validation_opened=False)
    print('E26_PROTOCOL_AND_INPUTS_READY',len(protected),round(time.monotonic()-start,2),flush=True)


def later(stage):
    check_lock();frozen_check('audit')
    if stage=='audit':
        for ds in DATASETS:raw_rows(ds,np.arange(8192,10000),'audit')
    else:
        assert read(RUN/'reviews/audit_report.json')['status']=='REPORT_ONLY_COMPLETE'
        for ds in DATASETS:
            original=E25/'inputs'/ds/'validation';c=read(original/'config.json');out=RUN/'inputs'/ds/'validation'
            out.mkdir(exist_ok=False);sources=[]
            for key,name in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]:
                src=Path(c[key]);sources.append(identity(src));shutil.copy2(src,out/name)
                assert sha(out/name)==sources[-1]['sha256'];c[key]=str(out/name)
            c['base_count']=read(E24/'inputs'/ds/'prepared.json')['base_rows']
            dump(out/'config.json',c);dump(out/'provenance.json',{'sources':sources,'prepared_unix':time.time(),
                'historical_validation':True,'prepared_after_all_model_selection_and_audit':True})
        update_state(validation_opened=True)
    print(stage.upper()+'_INPUTS_READY',flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['initialize','audit','validation']);a=ap.parse_args()
    initialize() if a.stage=='initialize' else later(a.stage)
