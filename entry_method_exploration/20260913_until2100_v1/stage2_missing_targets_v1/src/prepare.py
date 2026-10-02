"""Bind known full-fit E33 labels to current baseline and freeze missing-member supervision."""
from shared import *

threads();assert not (O/'reviews/prebuild_freeze.json').exists();started=time.monotonic()
for f in ['inputs','models','results','reviews','logs','bin','source_before']:(O/f).mkdir(exist_ok=True)
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,O/'source_before'/name)
assert read(E60/'results/gate.json')['status']=='STOP_SAME_LOCAL_ACTION_CONTINUOUS_EXPANSION'
check(E60/'reviews/final_artifact_freeze.json')
shutil.copy2(E46/'bin/environment.so',O/'bin/environment.so')
shutil.copy2(E46/'src/native_cached_v2.py',O/'src/native_cached.py')
graph_source=D/'20260912_construction_only_rl_v1/src/graph_bytes.py'
shutil.copy2(graph_source,O/'src/graph_reader.py')
from graph_reader import inspect_serialized
protected={E46/'bin/environment.so',E46/'src/native_cached_v2.py',graph_source,E60/'reviews/final_artifact_freeze.json'}
identities=[];records=[]
for ds in DS:
    folder=O/'inputs'/ds;folder.mkdir();oldpath=E33/'inputs'/ds/'config.json';old=read(oldpath);protected.add(oldpath)
    d=old['dim'];h=old['hub_count'];Ppath=Path(old['policy']['W']);P=np.fromfile(Ppath,np.float32).reshape(h,d)
    mapping=np.fromfile(old['hub_ids'],np.int32);protected.update([Ppath,Path(old['hub_ids'])])
    pmeta=read(Ppath.parent/'manifest.json');protected.add(Ppath.parent/'manifest.json')
    assert np.all(np.diff(mapping)>0) and old['L']==128 and old['policy']['canonical_entry_order'] and old['policy']['hnsw_seed']==20260828
    fitq=np.fromfile(old['queries_file'],np.float32).reshape(20000,d);fitgt=np.fromfile(old['gt_file'],np.int64).reshape(20000,100);fitids=np.fromfile(old['row_ids'],np.int64)
    assert np.array_equal(fitids,np.arange(10000,30000))
    protected.update(Path(old[k]) for k in ['queries_file','gt_file','row_ids','graph_file','index_path'])
    cachepath=E33/'results'/ds/'baseline.npz';baseline=dict(np.load(cachepath));protected.add(cachepath)
    assert np.array_equal(baseline['rows'],np.arange(20000))
    assert np.array_equal(ihits(baseline['ids'],fitgt),baseline['hits'])
    top=inspect_serialized(Path(old['graph_file']),P,mapping)['topology_sha']
    e60id=read(E60/'results'/ds/'anchor/identity.json');assert top==e60id['topology_sha'] and digest(P)==e60id['W_sha']
    c60path=E60/'inputs'/ds/'config.json';c60=read(c60path);protected.add(c60path)
    devq=np.fromfile(c60['queries_file'],np.float32).reshape(2064,d)[:2048];devgt=np.fromfile(c60['gt_file'],np.int64).reshape(2064,100)[:2048];devids=np.fromfile(c60['row_ids'],np.int64)[:2048]
    devpath=E60/'results'/ds/'anchor/raw.npz';dev=dict(np.load(devpath));protected.add(devpath)
    assert np.array_equal(devids,np.arange(2048)) and np.array_equal(ihits(dev['ids'][:2048],devgt),dev['hits'][:2048])
    protected.update(Path(c60[k]) for k in ['queries_file','gt_file','row_ids'])
    q=np.concatenate([fitq,devq]);gt=np.concatenate([fitgt,devgt]);ids=np.concatenate([fitids,devids])
    for name,a in [('queries.f32',q),('gt.i64',gt),('row_ids.i64',ids)]:a.tofile(folder/name)
    base={k:np.concatenate([baseline[k],dev[k][:2048]]) for k in FIELDS+['hits']};save(folder/'baseline.npz',**base)
    rawpath=E24/'inputs'/ds/'raw_hubs.f32';protected.add(rawpath)
    missing=~(baseline['ids'][:,:,None]==fitgt[:,None,:10]).any(1);counts=missing.sum(1)
    rng=np.random.default_rng(20260913);orders=np.argsort(rng.random((20000,10)),axis=1,kind='stable')
    sham=np.zeros((20000,10),bool)
    for i in range(20000):sham[i,orders[i,:counts[i]]]=True
    assert np.array_equal(sham.sum(1),counts) and np.array_equal(10-counts,baseline['hits'])
    save(folder/'missing_supervision.npz',missing=missing,sham=sham,counts=counts.astype(np.uint8),sham_orders=orders.astype(np.uint8))
    parity=np.r_[np.sort(np.random.default_rng(20260913).choice(20000,32,replace=False)),np.arange(20000,20016),np.arange(21024,21040)].astype(np.int32)
    parity.tofile(folder/'parity_rows.i32')
    source_audit=next(x for x in read(E60/'reviews/data_exposure_audit.json')['datasets'] if x['dataset']==ds)
    prov=read(D/'20260909_ab_experiment_v1/inputs'/ds/'verified_sources.json')
    basepath=Path(prov['base']['path']);protected.add(basepath)
    config=dict(dataset=ds,dim=d,hub_count=h,num_queries=22048,threads=1,query_cpu=15,L=128,gt_k=100,index_path=old['index_path'],hub_ids=old['hub_ids'],
        P=str(Ppath),raw_hubs=str(rawpath),base_file=str(basepath),queries_file=str(folder/'queries.f32'),gt_file=str(folder/'gt.i64'),row_ids=str(folder/'row_ids.i64'),
        native_call_cap=45000,native_hnsw_cap=67000,initial_topology_sha=top,original_assignments_sha=pmeta['assignments_sha256'],temperature=pmeta['temperature'],
        roles={'fit':[0,20000],'cal':[20000,21024],'audit':[21024,22048]},namespace=source_audit['profile_fit_namespace'],
        lambda_value=.5,sham_seed=20260913,original_policy=old['policy'],parity_rows=str(folder/'parity_rows.i32'))
    dump(folder/'config.json',config)
    records.append(dict(dataset=ds,fit_cache_source=identity(cachepath),historical_fit_label_rows=20000,historical_development_baseline_rows=2048,
        full_fit_independent_set_scoring='PASS',baseline_graph_full_vector_and_topology='PASS',source_namespace=config['namespace'],
        fit_P_exposed=True,cal_audit_historically_exposed=True,final_validation_access=False,
        missing_queries=int((counts>0).sum()),missing_members=int(counts.sum()),zero_hit_queries=int((counts==10).sum()),sham_count_match=True))
    print('PREPARED',ds,records[-1]['missing_queries'],'missing queries',flush=True)
dump(O/'reviews/input_audit.json',dict(status='PASS_HISTORICAL_CACHE_IDENTITY',datasets=records,seconds=time.monotonic()-started,
      reuse_scope='Fit labels are E33 current GT10 baseline only. New model results must be searched. Final validation excluded.'))
dump(O/'config.locked.json',dict(datasets=DS,models=LABELS,lambda_value=.5,sham_seed=20260913,threads=1,query_cpu=15,
      per_dataset_NSG_reserved=45000,total_NSG_cap=90000,per_dataset_HNSW=66528,per_dataset_builds=3,
      candidate_selection='only missing model; cal net hits>0, zero-hit failures nonincreasing, mean totalNDC <= baseline*1.01; sham not selectable',
      final_validation_access=False,query_stop=1789264800,latest_launch=1789264200))
protected.update(p for p in (O/'src').iterdir() if p.is_file())
protected.update(p for p in (O/'inputs').rglob('*') if p.is_file())
protected.update([O/'protocol.md',O/'config.locked.json',O/'bin/environment.so'])
dump(O/'reviews/prebuild_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(protected)]))
dump(O/'state.json',dict(status='PREPARED_FULL_FIT_MISSING_SUPERVISION',new_NSG=0,models_built=0,next_command='src/build.py'))
print('E61_PREPARE_PASS',time.monotonic()-started,flush=True)
