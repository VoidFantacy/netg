#!/usr/bin/env python3
"""Assemble the seven-dataset suite without copying large scientific assets."""
import hashlib
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]
E97=REPO/'entry_method_exploration/20260915_gate_l2_r1_r100_v1'
E181=REPO/'entry_method_exploration/20261016_m5_multimodal_transfer_v1'
KL={'1':[16,32,64,100,200,400,800,1200],'100':[100,128,200,400,800,1000,1200]}


def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')


def gt_role(r):
    if 'gt' in r:return dict(r['gt'])
    path=r.get('gt_raw') or r.get('gt_ivecs')
    fmt=r.get('gt_format','raw')
    if fmt=='raw':fmt='raw_i64' if r.get('gt_dtype') in ('<i8','int64') or path.endswith('.i64') else 'raw_i32'
    return {'path':path,'format':fmt,'n':r['rows'],'k':100,
            'total_n':r.get('container_rows',r['rows']),'row_start':r.get('row_start',0)}


def prepare():
    entries={}
    for fn in ('l2_assets.json','ip_assets.json'):
        x=load(ROOT/fn);assert x['status']=='PASS'
        for name,c in x['datasets'].items():
            tr=c['roles']['residual_fit'];te=c['roles']['test']
            entries[name]={'dataset':name,'metric_id':c['metric_id'],'base':c['base'],'index':c['index'],
                'routers':c['routers'],'H':c['H'],'train_queries':tr['queries'],'train_gt':gt_role(tr),
                'test_queries':te['queries'],'test_gt':gt_role(te),'source_manifest':str(E97/'inputs'/name/'manifest.json'),
                'asset_audit':str(ROOT/fn),'modality':'single_modality' if c['metric_id']==1 else 'cross_modal',
                'training_role_scope':'Residual fit shares original GT10 profile-fit prefix; test identities excluded.',
                'historical_results':str(E97/'results'/name),
                'historical_point_results':str(REPO/'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/results'/name)}
    for name in ('coco','flickr30k'):
        c=load(E181/'inputs'/name/'experiment_config.json');m=E181/'models'/name
        entry={'dataset':name,'metric_id':0,'base':{'path':c['base'],'format':'raw_f32','n':c['base_n'],'d':c['dimension']},
               'index':str(m/'nsg.index'),'H':c['H'],
               'routers':[{'name':'hard','ids':str(m/'ids.i32'),'W':str(m/'W.f32'),'graph':str(m/'router.hnsw'),'route_order':'heap_pop'}],
               'train_queries':{'path':c['residual_queries'],'format':'raw_f32','n':16000,'d':c['dimension']},
               'train_gt':{'path':str(m/'exact/residual.gt100.i64'),'format':'raw_i64','n':16000,'k':100},
               'test_queries':{'path':c['test_queries'],'format':'raw_f32','n':c['test_n'],'d':c['dimension']},
               'test_gt':{'path':str(m/'eval_gt/test.gt100.i64'),'format':'raw_i64','n':c['test_n'],'k':100},
               'source_manifest':str(E181/'inputs'/name/'prepared/manifest.json'),
               'modality':'cross_modal','training_role_scope':'Residual training role disjoint from profile-fit and test by image/caption connected identity groups.',
               'historical_results':str(E181/'results'/name)}
        entries[name]=entry
    assert len(entries)==7
    configs=[];total=0
    for name,c in entries.items():
        n=c['test_queries']['n'];d=c['base']['d'];model=ROOT/'models'/name
        common={k:c[k] for k in ('dataset','index','metric_id','base','routers')}
        common.update(threads=1,cpu=15,protocol=str(ROOT/'protocol.md'),protocol_sha256=sha(ROOT/'protocol.md'))
        teacher={**common,'queries':c['train_queries'],'teacher_K':100,'teacher_L':200,'output_dir':str(model/'teacher')}
        compile_c={'dataset':name,'base_n':c['base']['n'],'train_gt':c['train_gt'],
                   'teachers':[{'name':r['name'],'ids':r['ids'],'teacher_dir':str(model/'teacher'/r['name'])} for r in c['routers']],
                   'output_dir':str(model/'compiled'),'protocol':common['protocol'],'protocol_sha256':common['protocol_sha256']}
        methods=[{'name':'NSG','family':'NSG'}]
        models={}
        for r in c['routers']:
            rt=r['name'];base='GT10-hard' if rt=='hard' else 'GT10-soft-t1'
            methods.append({'name':base,'family':'GT10','router':rt})
            for b in (8,32):methods.append({'name':rt+f'-JOINT{b}','family':'POST','router':rt,
                                         'table':str(model/'compiled'/rt/'tables'/f'JOINT{b}.bin'),'baseline':base})
            models[rt]={'source_dir':str(model/'compiled'/rt/'source'),
                        'compile_manifest':str(model/'compiled'/rt/'compile_manifest.json'),
                        'table_rows':{f'JOINT{b}':str(model/'compiled'/rt/'tables'/f'JOINT{b}.rows.json') for b in (8,32)},
                        'training_gt':c['train_gt'],'training_n':c['train_queries']['n'],
                        'teacher_dir':str(model/'teacher'/rt)}
        benchmark={**common,'queries':c['test_queries'],'output_dir':str(ROOT/'results'/name),
                   'K_L':KL,'timing_repeats':3,'warmup_n':256,'methods':methods}
        bp=ROOT/'configs'/f'{name}.benchmark.json'
        analysis={'dataset':name,'benchmark_config':str(bp),'eval_gt':{**c['test_gt'],'width':100,
                  'dtype':'<i8' if c['test_gt']['format']=='raw_i64' else '<i4'},
                  'source_manifest':c['source_manifest'],'models':models,'catalogue_entry':c}
        for mode,cfg in (('teacher',teacher),('compile',compile_c),('benchmark',benchmark),('analysis',analysis)):
            p=ROOT/'configs'/f'{name}.{mode}.json';save(p,cfg);configs.append(str(p))
        total+=15*len(methods)
        c['benchmark_config']=str(bp);c['analysis_config']=str(ROOT/'configs'/f'{name}.analysis.json')
        c['expected_points']=15*len(methods);c['methods']=methods
    assert total==645,total
    save(ROOT/'reviews/dataset_catalogue.json',{'status':'FROZEN_SEVEN_DATASET_PLAN','datasets':entries,
         'K_L':KL,'expected_points':total,'expected_formal_batches':3*total,'configs':configs,
         'created_unix':time.time(),'timing_repeats':3,'protocol_sha256':sha(ROOT/'protocol.md')})
    print(json.dumps({'datasets':len(entries),'points':total,'formal_batches':total*3}))


if __name__=='__main__':prepare()
