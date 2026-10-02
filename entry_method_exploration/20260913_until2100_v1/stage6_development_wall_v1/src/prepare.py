from common import *
from graph_reader import inspect_serialized
import copy
threads();resources();started=time.monotonic();E64=C/'stage5_frozen_pool_aux_v1';E34=D/'20260911_hnsw_rl_benchmark_v1'
assert not (O/'reviews/prequery_freeze.json').exists();assert read(E64/'reviews/verification.json')['status']=='PASS'
check(E64/'reviews/final_artifact_freeze.json');selection=read(E64/'results/selection.json');pool=read(E64/'inputs/pool.json')
for f in ['inputs','results','reviews','logs','bin','source_before']:(O/f).mkdir(exist_ok=True)
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,O/'source_before'/name)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
for name in ['state.json','handoff.md']:shutil.copy2(C/name,O/'source_before'/name)
shutil.copy2(E34/'bin/evaluate',O/'bin/evaluate');os.chmod(O/'bin/evaluate',0o755)
protected={E64/'reviews/final_artifact_freeze.json',E64/'results/selection.json',E34/'bin/evaluate',E34/'src/evaluate.cpp',E34/'src/benchmark_with_nsg.cpp'};records=[];matrices={}
for ds in DS:
    c=read(E64/'inputs'/ds/'config.json');d=c['dim'];folder=O/'inputs'/ds;folder.mkdir()
    q=np.fromfile(c['queries_file'],np.float32).reshape(7952,d)[:2048];gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100)[:2048];rows=np.fromfile(c['row_ids'],np.int64)[:2048]
    assert np.array_equal(rows,np.arange(2048,4096))
    for file,a in [('queries.f32',q),('gt.i64',gt),('row_ids.i64',rows)]:a.tofile(folder/file)
    original=read(E34/'inputs'/ds/'config.json');protected.add(E34/'inputs'/ds/'config.json')
    methods=[]
    for name in ['nsg','fast30k','gt10_hard']:
        methods.append(copy.deepcopy(next(m for m in original['methods'] if m['model_name']==name and m['L']==64)))
    if ds==DS[0]:methods.append(dict(pool[ds][0],model_name='baseline_soft'))
    chosen=selection['datasets'][ds]['best_new'];candidate=next(m for m in pool[ds] if m['model_name']==chosen)
    methods.append(dict(candidate,model_name='best_new',selected_source_name=chosen))
    mm=[dict(m,L=L,name=m['model_name']+f'_L{L}',component_wall=False) for L in [64,128,256,400,800] for m in methods]
    for m in methods:
        if m['family']!='nsg':
            for key in ['W','mapping','tie_ids','graph_file']:protected.add(Path(m[key]))
            mapping=np.fromfile(m['mapping'],np.int32);W=np.fromfile(m['W'],np.float32).reshape(len(mapping),d);inspect_serialized(Path(m['graph_file']),W,mapping)
    cfg=dict(c,split='E65_historical_development_router_train2048_4096',num_queries=2048,queries_file=str(folder/'queries.f32'),gt_file=str(folder/'gt.i64'),row_ids=str(folder/'row_ids.i64'),
       timing_repeats=5,methods=mm,real_call_cap=len(mm)*(7*2048+16))
    dump(folder/'config.json',cfg);matrices[ds]=cfg
    records.append(dict(dataset=ds,source_namespace=next(x['source_namespace'] for x in read(E64/'reviews/input_roles.json')['datasets'] if x['dataset']==ds),
       source_rows=[2048,4096],historical_development_exposed=True,E64_used_for_selection=True,E34_final_input_access=False,best_new=chosen,best_all=selection['datasets'][ds]['best_all']))
dump(O/'inputs/matrix.json',matrices);dump(O/'results/frozen_selection.json',selection)
dump(O/'reviews/input_roles.json',dict(status='PASS_DEVELOPMENT_ONLY',datasets=records,seconds=time.monotonic()-started))
dump(O/'config.locked.json',dict(NSG_cap=650000,planned_NSG=645840,planned_HNSW=501760,points=45,timing_batches=225,Ls=[64,128,256,400,800],repeats=5,threads=1,query_cpu=15,
     latest_launch=1789267200,query_stop=1789268400,final_validation_access=False,selection_frozen_from='E64'))
protected.update(p for folder in ['src','inputs','source_before'] for p in (O/folder).rglob('*') if p.is_file());protected.update([O/'bin/evaluate',O/'protocol.md',O/'config.locked.json',O/'results/frozen_selection.json'])
dump(O/'reviews/prequery_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(protected)]))
dump(O/'state.json',dict(status='FROZEN_BEFORE_DEVELOPMENT_WALL',new_NSG=0,formal_development_QPS_points=0,day_goal_complete=False))
state=read(C/'state.json');state.update(status='E65_PREPARED',stage='E65',native_pids=[]);dump(C/'state.json',state)
print('E65_PREPARE_PASS',records,flush=True)
