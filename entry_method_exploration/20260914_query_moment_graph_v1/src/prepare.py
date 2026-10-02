from common import *
os.sched_setaffinity(0,{8})
assert not (O/'config.locked.json').exists()
resources();dump(O/'logs/jobs.json',[])
inputs={};protected=[];large=[]
for ds in DS:
    a=read(E73/'inputs'/ds/'aux.json');f=read(C/'stage7_multimode_index_v1/inputs'/ds/'fit.json')
    p=next(m for m in a['methods'] if m['model_name']=='baseline10')
    assert a['num_queries']==7952 and f['num_queries']==20000 and f['input_total_rows']==22048
    inputs[ds]=dict(aux=a,fit=f,baseline=p)
    protected += [E73/'inputs'/ds/'aux.json',C/'stage7_multimode_index_v1/inputs'/ds/'fit.json']
    protected += [a[k] for k in ['queries_file','gt_file','row_ids']]
    protected += [p[k] for k in ['W','mapping','tie_ids','graph_file']]
    index=Path(a['index_path']);s=index.stat();large.append(dict(path=str(index),bytes=s.st_size,mtime_ns=s.st_mtime_ns,scope='current stat; source index inherited from E73'))
    protected += [E73/'bin/build_graph',E73/'bin/evaluate',E73/'src/evaluate.cpp',E73/'src/benchmark_with_nsg.cpp',E73/'src/build_graph.cpp']
dump(O/'inputs/sources.json',inputs);dump(O/'reviews/large_asset_stat.json',large)
dump(O/'config.locked.json',dict(experiment='E95',models=['identity','full','diag'],main='full',backup='diag',N_fit=20000,N_aux=7952,halves=3976,L=[64,128],seed=20260828,threads=1,CPU=15,eigen_floor=1e-6,NSG_expected=194304,HNSW_expected=193920,builds_expected=6,NSG_hard_cap=200000,QPS=None,gate='protocol.md; all full/half net>=0 and new_zero<=0, graph<=1.01, signal recall>=.10pp or route<=.90 at one L',final_payload_access=False,heldout_access=False))
freeze(O/'reviews/protected_before.json',protected)
freeze(O/'reviews/preconstruction_freeze.json',list((O/'src').glob('*.py'))+[O/'protocol.md',O/'research.md',O/'config.locked.json',O/'inputs/sources.json']+list((O/'bin').glob('*')))
records=[]
for ds in DS:
    t=time.monotonic();s=inputs[ds];a,f,p=s['aux'],s['fit'],s['baseline'];d=a['dim'];h=p['hub_count']
    dest=O/'models'/ds;dest.mkdir()
    P=np.fromfile(p['W'],np.float32).reshape(h,d);labels=np.fromfile(p['mapping'],np.int32)
    # Read and hash only the explicitly recorded fit prefix, never fit GT or the suffix.
    Q=np.fromfile(f['queries_file'],np.float32,count=20000*d).reshape(20000,d)
    rows=np.fromfile(f['row_ids'],np.int64,count=20000);auxrows=np.fromfile(a['row_ids'],np.int64)
    assert len(set(map(int,rows)))==20000 and len(set(map(int,auxrows)))==7952
    assert not set(map(int,rows))&set(map(int,auxrows))
    assert np.isfinite(Q).all() and np.isfinite(P).all()
    Q64=Q.astype(np.float64);M=Q64.T@Q64/len(Q);scale=float(np.trace(M)/d);assert scale>0;M/=scale
    eig,U=np.linalg.eigh(M);assert eig[0]>-1e-10 and eig[-1]>0
    full=(U*np.sqrt(np.maximum(eig,1e-6)))@U.T
    diag=np.diag(np.sqrt(np.maximum(np.diag(M),1e-6)))
    np.savez(dest/'statistics.npz',M=M,eigenvalues=eig,full=full,diag=diag,source_rows=rows,aux_source_rows=auxrows)
    # Independent raw-query moments and Gram identities check the actual construction target.
    for i in [0,d//2,d-1]:
        for j in [0,d//2,d-1]:assert abs(M[i,j]-float(np.dot(Q64[:,i],Q64[:,j])/len(Q)/scale))<1e-11
    assert np.max(np.abs(full@full-M))<=1.1e-6
    G=P.astype(float)@M@P.astype(float).T
    cf=P.astype(float)@full;assert np.max(np.abs(cf@cf.T-G))<=1.2e-6
    info=dict(dataset=ds,fit_query_prefix_sha256=hashlib.sha256(Q.tobytes()).hexdigest(),fit_rows_prefix_sha256=hashlib.sha256(rows.tobytes()).hexdigest(),fit_count=20000,fit_namespace='router_train',fit_row_min=int(rows.min()),fit_row_max=int(rows.max()),aux_disjoint=True,fit_container_rows=22048,fit_GT_read=False,source_Q=f['queries_file'],source_rows=f['row_ids'],moment_scale=scale,eigen_min=float(eig[0]),eigen_max=float(eig[-1]),floored_eigenvalues=int((eig<1e-6).sum()),statistics_seconds=time.monotonic()-t)
    for name,A in [('identity',np.eye(d)),('full',full),('diag',diag)]:
        folder=dest/name;folder.mkdir();W=P.copy() if name=='identity' else (P.astype(float)@A).astype(np.float32)
        assert np.isfinite(W).all();W.tofile(folder/'construction.f32')
        build=dict(p,W=str(folder/'construction.f32'));build.pop('graph_file');build['reference_graph']=False
        dump(folder/'build.json',build)
    dump(dest/'statistics.json',info);records.append(info)
freeze(O/'reviews/prebuild_freeze.json',list((O/'models').rglob('*.f32'))+list((O/'models').rglob('*.npz'))+list((O/'models').rglob('*.json')))
for ds in DS:
    p=inputs[ds]['baseline'];d=p['dim'];P=np.fromfile(p['W'],np.float32).reshape(p['hub_count'],d);labels=np.fromfile(p['mapping'],np.int32)
    for name in ['identity','full','diag']:
        folder=O/'models'/ds/name;raw=folder/'construction.hnsw'
        native('build',f'build_{ds}_{name}',[O/'bin/build_graph',folder/'build.json',raw])
        W=np.fromfile(folder/'construction.f32',np.float32).reshape(P.shape)
        build_info=inspect_graph(raw,W,labels)
        if name=='identity':
            assert sha(raw)==sha(p['graph_file']),'identity graph differs from original'
            graph=raw;info=build_info;info['identity_graph_bit_recovery']=True
        else:
            graph=folder/'graph.hnsw';info=install(raw,W,P,labels,graph)
            assert info['edges']==build_info['edges'] and info['levels']==build_info['levels']
        info['construction_source']=ident(raw);dump(folder/'verification.json',info)
        model=dict(p,model_name=name,W=p['W'],graph_file=str(graph),reference_graph=True)
        dump(folder/'model.json',model)
    for phase,n in [('preflight',128),('aux',7952)]:
        methods=[]
        for name in ['identity','full','diag']:
            model=read(O/'models'/ds/name/'model.json')
            methods += [dict(model,L=L,name=f'{name}_L{L}') for L in [64,128]]
        cfg=dict(inputs[ds]['aux'],methods=methods,num_queries=n,input_total_rows=7952,split='E95_historical_aux_'+phase,timing_repeats=0,real_call_cap=6*(2*n+16))
        dump(O/'inputs'/f'{ds}_{phase}.json',cfg)
freeze(O/'reviews/prequery_freeze.json',list((O/'src').glob('*.py'))+list((O/'models').rglob('*.*'))+list((O/'inputs').glob('*.json'))+list((O/'bin').glob('*'))+[O/'protocol.md',O/'research.md',O/'config.locked.json'])
check(O/'reviews/protected_before.json')
dump(O/'results/construction.json',dict(status='PASS',records=records,builds=6,vector_installs=4,original_P_and_labels_bit_preserved=True,identity_graphs_bit_recovered=2,GT_labels_generated=0,gradient_updates=0))
dump(O/'state.json',dict(status='CONSTRUCTION_COMPLETE_UNQUERIED',NSG=0,HNSW=0,builds=6))
print('PREPARED',flush=True)
