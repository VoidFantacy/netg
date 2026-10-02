"""Known development data audit, immutable E53 state selection; no native import."""
from shared import *

threads(8); resources()
assert not (O/'reviews/prequery_freeze.json').exists()
started = time.monotonic(); protected = set(); data_records = []; contexts = []
source_native = E46/'bin/environment.so'
shutil.copy2(source_native, O/'bin/environment.so')
shutil.copy2(E46/'src/native_cached_v2.py', O/'src/native_cached.py')
assert sha(source_native) == sha(O/'bin/environment.so')
protected.update([source_native, E46/'src/native_cached_v2.py', E46/'src/cache_environment.cpp',
                  E37/'src/environment.cpp', E53/'src/train.py', E53/'src/shared.py'])
large_verified = []

for ds in DS:
    dest = O/'inputs'/ds; dest.mkdir()
    old = read(E53/'inputs'/ds/'config.json')
    provenance_path = D/'20260909_ab_experiment_v1/inputs'/ds/'verified_sources.json'
    provenance = read(provenance_path); protected.add(provenance_path)
    for key in ['base','graph','query_train','gt_train']:
        x = provenance[key]; current = identity(x['path'])
        assert current['sha256'] == x['sha256'] and current['bytes'] == x['bytes'], key
        large_verified.append(dict(kind=key,dataset=ds,**current)); protected.add(Path(x['path']))
    d = old['dim']; h = old['hub_count']
    qsource = Path(provenance['query_train']['path']); gsource = Path(provenance['gt_train']['path'])
    qf = np.memmap(qsource, np.int32, mode='r').reshape(30000,d+1)
    gf = np.memmap(gsource, np.int32, mode='r').reshape(30000,101)
    assert np.all(qf[:,0] == d) and np.all(gf[:,0] == 100)
    qall = qf[:,1:].view(np.float32); gall = gf[:,1:]
    pfit_file = E24/'inputs'/ds/'fit/row_ids.i64'
    pfit = np.fromfile(pfit_file, np.int64); protected.add(pfit_file)
    oldrows = np.fromfile(old['row_ids'], np.int64)
    assert np.array_equal(pfit, np.arange(10000,30000))
    assert len(oldrows) == 5120 and len(np.unique(oldrows)) == 5120
    assert np.isin(oldrows,pfit).all()
    oldq = np.fromfile(old['queries_file'],np.float32).reshape(5120,d)
    oldgt = np.fromfile(old['gt_file'],np.int64).reshape(5120,100)
    assert np.array_equal(oldq,qall[oldrows]) and np.array_equal(oldgt,gall[oldrows])
    chunks_q=[]; chunks_gt=[]; chunks_id=[]; groups={}
    for split, folder, want in [('auxiliary',E57/'inputs'/ds/'cal',np.arange(1024)),
                                ('transfer',E37/'inputs'/ds/'audit',np.arange(1024,2048))]:
        qr=folder/'queries.f32'; gr=folder/'gt.i64'; ir=folder/'row_ids.i64'
        q=np.fromfile(qr,np.float32).reshape(1024,d); gt=np.fromfile(gr,np.int64).reshape(1024,100); ids=np.fromfile(ir,np.int64)
        assert np.array_equal(ids,want) and np.array_equal(q,qall[ids]) and np.array_equal(gt,gall[ids])
        assert not np.intersect1d(ids,pfit).size and not np.intersect1d(ids,oldrows).size
        chunks_q.append(q); chunks_gt.append(gt); chunks_id.append(ids)
        protected.update([qr,gr,ir])
        groups[split]=dict(count=1024,router_train_range=[int(ids.min()),int(ids.max()+1)],
                           namespace=str(qsource),namespace_sha256=provenance['query_train']['sha256'],
                           previously_used=True,initial_P_fit_overlap=0,
                           current_role='action selection training diagnostic' if split=='auxiliary' else 'fixed-rule migration description; historical, not blind')
    chunks_q.append(oldq[:16]); chunks_gt.append(oldgt[:16]); chunks_id.append(oldrows[:16])
    q=np.concatenate(chunks_q); gt=np.concatenate(chunks_gt); ids=np.concatenate(chunks_id)
    assert len(np.unique(ids)) == 2064
    assert len({row.tobytes() for row in q}) == 2064
    for name,a in [('queries.f32',q),('gt.i64',gt),('row_ids.i64',ids)]: a.tofile(dest/name)
    config=dict(old,num_queries=2064,queries_file=str(dest/'queries.f32'),gt_file=str(dest/'gt.i64'),row_ids=str(dest/'row_ids.i64'),
                native_call_cap=340000,native_hnsw_cap=331000,train=0,monitor=0,
                data_roles={'auxiliary':[0,1024],'transfer':[1024,2048],'original_train_parity':[2048,2064]},threads=1,query_cpu=15)
    dump(dest/'config.json',config)
    P=np.fromfile(old['P'],np.float32).reshape(h,d)
    B=np.fromfile(old['basis'],np.float64).reshape(d,16)
    scale_file=E53/'inputs'/ds/'local_parameters.npz'; scale=np.load(scale_file)['scale']; protected.add(scale_file)
    protected.update(Path(old[k]) for k in ['P','basis','hub_ids','queries_file','gt_file','row_ids','original_graph'])
    protected.add(E53/'inputs'/ds/'config.json')
    base_file=E37/'results'/ds/'baseline.npz'; protected.add(base_file)
    baseline=dict(np.load(base_file)); base={k:baseline[k][:4096].copy() for k in FIELDS+['hits']}
    for seed in SEEDS:
        src=E53/'models'/ds/f'rl_ls_{seed}'; W=P.copy(); current={k:v.copy() for k,v in base.items()}
        cpmeta=read(src/'checkpoints.json'); protected.add(src/'checkpoints.json')
        for step in range(1,201):
            if (step-1)%20==0:
                cpfile=src/'checkpoints'/f'{step-1:04}.npz'; protected.add(cpfile)
                with np.load(cpfile) as cp:
                    assert W.tobytes()==cp['W'].tobytes()
                    equal(current,{k:cp[k][:4096] for k in FIELDS})
            tf=src/'trajectory'/f'{step:04}.npz'; protected.add(tf)
            with np.load(tf) as t:
                slot=int(t['slot']); assert W[slot].tobytes()==t['current_row'].tobytes()
                assert raw_digest(current)==str(t['current_cache_sha'])
                if step%10==0:
                    name=f'seed{seed}_step{step:04}'; info=dict(dataset=ds,seed=seed,step=step,name=name,source=str(src),trajectory=str(tf),
                        slot=slot,current_W_sha=digest(W),current_topology_sha=str(t['current_topology_sha']),
                        d_W_sha=t['d_W_sha'].tolist(),d_topology_sha=t['d_topology_sha'].tolist(),
                        d_rewards=t['d_rewards'].tolist(),original_choice=int(t['choice']),physical_parity=step in [10,200])
                    hs=[current['hits'].copy()]
                    drift0=float(np.square(W.astype(float)-P).sum(1).mean())
                    J0=float(utility(current,base).mean()-drift0)
                    assert abs(J0-float(t['current_J']))<1e-12
                    for i in range(3):
                        row=row_profile(P[slot],B,scale[slot],t['d_coeff'][i])
                        assert row.tobytes()==t['d_rows'][i].tobytes()
                        wa=W.copy();wa[slot]=row;assert digest(wa)==str(t['d_W_sha'][i])
                        branch={k:v.copy() for k,v in current.items()}; changed=t[f'd{i}_rows']
                        for k in ['ids','distances','entries','graph_ndc','hits']:branch[k][changed]=t[f'd{i}_{k}']
                        branch['route_ndc']=t['d_route_ndc'][i]
                        assert raw_digest(branch)==str(t['d_cache_sha'][i])
                        assert np.array_equal(score(branch['ids'],oldgt[:4096]),branch['hits'])
                        J=float(utility(branch,base).mean()-np.square(wa.astype(float)-P).sum(1).mean())
                        assert abs(J-J0-float(t['d_rewards'][i]))<1e-12
                        hs.append(branch['hits'])
                    save(dest/'contexts'/f'{name}.npz',train_hits=np.stack(hs),current_row=t['current_row'],d_rows=t['d_rows'],d_coeff=t['d_coeff'])
                    contexts.append(info)
                choice=int(t['choice']); W[slot]=t['next_row']
                if choice>=0:
                    changed=t[f'd{choice}_rows']
                    for k in ['ids','distances','entries','graph_ndc','hits']:current[k][changed]=t[f'd{choice}_{k}']
                    current['route_ndc']=t['d_route_ndc'][choice]
                assert digest(W)==str(t['accepted_W_sha']) and raw_digest(current)==str(t['accepted_cache_sha'])
    data_records.append(dict(dataset=ds,groups=groups,profile_fit_count=20000,profile_fit_namespace=str(qsource),
        old_train_in_P=4096,old_monitor_in_P=1024,old_train_monitor_intersection=0,
        auxiliary_transfer_same_namespace_intersection=0,raw_copy_and_GT_parity='PASS',
        Fast30K_exposure='All 30000 router_train rows used by historical Fast prototype fitting',
        final_E34_validation='Distinct validation source namespace; no input vector, GT, row or response read in E60',
        project_wide_unused_rows_claimed=False))
    print('PREPARED',ds,'40 immutable contexts','known historical development only',flush=True)

dump(O/'inputs/contexts.json',contexts)
dump(O/'reviews/data_exposure_audit.json',dict(status='PASS_KNOWN_ROLES_NO_FRESHNESS_CLAIM',datasets=data_records,
     current_sources=large_verified,seconds=time.monotonic()-started,
     limitation='Known relevant chains audited; no claim of exhaustive historical non-use. All router_train already exposed to legacy Fast.'))
dump(O/'config.locked.json',dict(datasets=DS,seeds=SEEDS,steps=list(range(10,201,10)),points=['C','D25','D50','D100'],
     auxiliary_count=1024,transfer_count=1024,original_train_parity=16,L=128,K=10,threads=1,query_cpu=15,
     support_gate_per_dataset=10,states_per_dataset=40,per_dataset_NSG_reserved=340000,total_NSG_cap=680000,
     per_dataset_HNSW=330320,per_dataset_builds=161,per_dataset_max_NSG=330608,
     query_stop=QUERY_STOP,latest_launch=LATEST_LAUNCH,output_bytes=384*(1<<20),minimum_free_bytes=7*(1<<30)))
dump(O/'reviews/native_provenance.json',dict(source=identity(source_native),copy=identity(O/'bin/environment.so'),
     wrapper_source=identity(E46/'src/native_cached_v2.py'),wrapper_copy=identity(O/'src/native_cached.py'),modified_native=False))
protected.update(p for p in (O/'src').iterdir() if p.is_file())
protected.update(p for p in (O/'inputs').rglob('*') if p.is_file())
protected.update([O/'protocol.md',O/'config.locked.json',O/'bin/environment.so'])
dump(O/'reviews/prequery_freeze.json',dict(created_at=time.time(),files=[identity(p) for p in sorted(protected)],root_documents_protected_by=str(C/'source_before')))
dump(O/'state.json',dict(status='PREPARED_FIXED_ACTIONS_NO_NEW_NATIVE',new_NSG=0,new_HNSW=0,optimizer_updates=0,contexts=len(contexts),next_command='src/run.py <dataset>'))
print('PREPARE_PASS',len(contexts),len(protected),time.monotonic()-started,flush=True)
