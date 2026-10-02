from common import *
frozen=json.loads((RUN/'reviews/frozen_models.json').read_text());lock=json.loads((RUN/'config.locked.json').read_text())
assert frozen['status']=='PASS' and sha(RUN/'config.locked.json')==frozen['config_sha256']
for p,h in frozen['sources'].items():assert sha(p)==h,('changed frozen source',p)
for p,rec in frozen['protected'].items():
    f=Path(p);assert f.stat().st_size==rec['bytes'] and f.stat().st_mtime_ns==rec['mtime_ns'],p
rows=[]
for order,ds in enumerate(DATASETS):
    inp=RUN/'inputs'/ds;c=json.loads((inp/'manifest.json').read_text());model=RUN/'models'/ds;n=c['test_rows'];d=c['shape'][1]
    q=vecs(c['paths']['query_path']);gt=vecs(c['paths']['gt_path'],'i4')
    assert q.shape==(n,d) and gt.shape==(n,100) and np.isfinite(q).all()
    assert (gt>=0).all() and (gt<c['shape'][0]).all() and np.all(np.diff(np.sort(gt,axis=1),axis=1)>0)
    if c['metric_id']==1:
        gm=json.loads((inp/'test.gt/complete.json').read_text());assert gm['status']=='PASS' and gm['base_sha256']==c['identities']['base_path']['sha256'] and gm['independent_direct_float64_checks']
    methods=[dict(name='NSG'),dict(name='GT10-hard',ids=str(inp/'gt10.ids.i32'),W=str(model/'gt10_hard/W.f32')),dict(name='GT10-soft-t1',ids=str(inp/'gt10.ids.i32'),W=str(model/'gt10_soft_t1/W.f32')),dict(name='GATE',ids=str(inp/'gate.ids.i32'),W=str(model/GATE_MODEL/'W.f32')),dict(name='HNSW')]
    for method in methods:
        if 'ids' in method:
            ids=np.fromfile(method['ids'],'i4');w=np.fromfile(method['W'],'f4').reshape(len(ids),d)
            assert len(ids)>=3 and (ids>=0).all() and (ids<c['shape'][0]).all() and len(set(ids))==len(ids) and np.isfinite(w).all()
    for k in lock['K']:
        cfg=dict(dataset=ds,dataset_order=order,metric_id=c['metric_id'],K=k,threads=1,formal=True,n=n,index=c['paths']['index'],base=c['paths']['base_path'],queries=c['paths']['query_path'],gt=c['paths']['gt_path'],L=lock['L'][str(k)],methods=methods,hnsw_complete=str(model/'hnsw/complete.json'),hnsw_topology=str(model/'hnsw/full.topology.gz'),freeze_sha256=sha(RUN/'reviews/frozen_models.json'))
        assert min(cfg['L'])>=k and len(cfg['L'])==16
        p=inp/f'eval_k{k}.json'
        if p.exists():assert json.loads(p.read_text())==cfg
        else:dump(p,cfg)
    rows.append(dict(dataset=ds,queries=n,base_rows=c['shape'][0],dim=d,metric_id=c['metric_id'],query_sha256=sha(c['paths']['query_path']),gt_sha256=sha(c['paths']['gt_path'])))
resource_check();dump(RUN/'reviews/preflight.json',dict(status='PASS',datasets=rows,points=800,wall_rounds=2400,threads=1,unix=time.time()))
print('PREFLIGHT_PASS',flush=True)
