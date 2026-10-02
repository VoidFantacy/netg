from common import *
from graph_reader import inspect_serialized
threads();resources();started=time.monotonic()
E61=C/'stage2_missing_targets_v1';E62=C/'stage3_missing_factorial_v1';E63=C/'stage4_zero_hit_mass_v1';E34=D/'20260911_hnsw_rl_benchmark_v1'
assert not (O/'reviews/prequery_freeze.json').exists()
for f in ['inputs','results','reviews','logs','bin','source_before']:(O/f).mkdir(exist_ok=True)
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
    shutil.copy2(R/name,O/'source_before'/name)
shutil.copy2(R/'experiment_history/README.md',O/'source_before/history_README.md')
for name in ['state.json','handoff.md']:shutil.copy2(C/name,O/'source_before'/name)
for stage in [E61,E62,E63]:check(stage/'reviews/final_artifact_freeze.json')
shutil.copy2(E34/'bin/evaluate',O/'bin/evaluate');os.chmod(O/'bin/evaluate',0o755)
protected={E34/'bin/evaluate',E34/'src/evaluate.cpp',E34/'src/benchmark_with_nsg.cpp'};records=[];pool={}
for ds in DS:
    c63=read(E63/'inputs'/ds/'config.json');d=c63['dim'];h=c63['hub_count'];folder=O/'inputs'/ds;folder.mkdir()
    provpath=D/'20260909_ab_experiment_v1/inputs'/ds/'verified_sources.json';prov=read(provpath);protected.add(provpath)
    qp=Path(prov['query_train']['path']);gp=Path(prov['gt_train']['path']);assert sha(qp)==prov['query_train']['sha256'] and sha(gp)==prov['gt_train']['sha256']
    fq=np.memmap(qp,np.float32,mode='r').reshape(30000,d+1);fg=np.memmap(gp,np.int32,mode='r').reshape(30000,101)
    assert np.all(fq[:,0].view(np.int32)==d) and np.all(fg[:,0]==100)
    original_rows=np.fromfile(c63['row_ids'],np.int64);q63=np.fromfile(c63['queries_file'],np.float32).reshape(22048,d);g63=np.fromfile(c63['gt_file'],np.int64).reshape(22048,100)
    assert np.array_equal(fq[original_rows,1:],q63) and np.array_equal(fg[original_rows,1:],g63)
    rows=np.arange(2048,10000,dtype=np.int64);assert not np.intersect1d(rows,original_rows).size
    np.asarray(fq[rows,1:]).tofile(folder/'queries.f32');np.asarray(fg[rows,1:],np.int64).tofile(folder/'gt.i64');rows.tofile(folder/'row_ids.i64')
    specs=[('baseline',E62,'C'),('E61_missing',E62,'A'),('E62_score',E62,'S'),('E62_topology',E62,'T'),('E63_zero_mass',E63,'zero_mass2'),('E61_sham',E61,'sham_lambda05'),('E63_sham',E63,'sham_mass2')]
    mm=[]
    for name,stage,label in specs:
        W=stage/'models'/ds/label/'W.f32';graph=stage/'results'/ds/label/'graph.hnsw'
        mapping=np.fromfile(c63['hub_ids'],np.int32);arr=np.fromfile(W,np.float32).reshape(h,d);g=inspect_serialized(graph,arr,mapping)
        m=dict(c63['original_policy'],W=str(W),graph_file=str(graph),model_name=name,name=name+'_L128',L=128,component_wall=False)
        mm.append(m);protected.update([W,graph,Path(m['mapping']),Path(m['tie_ids'])])
    config=dict(dataset=ds,split='E64_historical_router_train_aux2048_10000',num_queries=7952,dim=d,gt_k=100,
      base_count=2505000 if ds==DS[0] else 10000000,index_path=c63['index_path'],queries_file=str(folder/'queries.f32'),gt_file=str(folder/'gt.i64'),row_ids=str(folder/'row_ids.i64'),
      threads=1,query_cpu=15,dataset_order=DS.index(ds),timing_repeats=0,methods=mm,real_call_cap=111440)
    dump(folder/'config.json',config);pool[ds]=mm
    records.append(dict(dataset=ds,source_namespace=str(qp),query_source=identity(qp),GT_source=identity(gp),source_rows=[2048,10000],fit_cal_audit_row_intersection=0,
      original_22048_query_GT_rows_byte_restored=True,role='Auxiliary candidate selection training; historically used by Fast30K and earlier methods; not project-unseen',halves=[[2048,6024],[6024,10000]]))
    protected.update([qp,gp,E63/'inputs'/ds/'config.json'])
dump(O/'inputs/pool.json',pool);dump(O/'reviews/input_roles.json',dict(status='PASS_HISTORICAL_AUX_ROLES',datasets=records,final_validation_access=False,seconds=time.monotonic()-started))
dump(O/'config.locked.json',dict(NSG_cap=230000,planned_NSG=222880,new_candidates=['E61_missing','E62_score','E62_topology','E63_zero_mass'],controls=['E61_sham','E63_sham'],
    selection='positive total net hits; both fixed halves nonnegative; pooled failures nonincreasing; totalNDC<=1.01; rank net hits/fewer failures/lowerNDC/fixed index',
    best_new='Same fixed rank among four new endpoints independent of gate; diagnostic only',latest_launch=1789267500,query_stop=1789268100,threads=1,query_cpu=15))
protected.update(p for root in ['inputs','src','source_before'] for p in (O/root).rglob('*') if p.is_file());protected.update([O/'bin/evaluate',O/'protocol.md',O/'config.locked.json'])
dump(O/'reviews/prequery_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(protected)]))
dump(O/'state.json',dict(status='FROZEN_BEFORE_AUX_QUERIES',new_NSG=0,next_action='src/run.py dataset'))
state=read(C/'state.json');state.update(status='E64_PREPARED',stage='E64',native_pids=[]);dump(C/'state.json',state)
print('E64_PREPARE_PASS',time.monotonic()-started,flush=True)
