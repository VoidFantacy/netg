from model_io import *
from archive import load_packets
import struct,collections
assert read(R/'reviews/formal_complete.json')['status']=='PASS_FROZEN_FOUR_WINDOW_MATRIX'
started=time.perf_counter();points=[];comparisons=[];mechanisms=[];quality=[];selection_checks=0;witness_checks=0;hash_checks=0;hits_archive={}
def wide(name,rows):
    fields=list(dict.fromkeys(k for x in rows for k in x))
    with open(R/'analysis'/name,'w') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def paired(a,b,G,K):
    rescued=lost=0
    for x,y,g in zip(a,b,G[:,:K]):
        sx=set(x)&set(g);sy=set(y)&set(g);rescued+=len(sx-sy);lost+=len(sy-sx)
    return rescued,lost
def readgt(c):
    x=c['test_gt'];n=c['queries']['n'];a=np.fromfile(x['path'],'<i4').reshape(-1,100)
    return a[x.get('row_start',0):x.get('row_start',0)+n]
for ds in DS:
  for window in ['A','B']:
    cfg=read(R/'configs'/f'{ds}.{window}.formal.json');root=Path(cfg['output_dir']);info=read(root/'complete.json');raw=load_packets(root);G=readgt(cfg);n=len(G);local=[];packets={}
    assert info['points']==len(cfg['points']) and info['batches']==3*info['points']
    for p in info['results']:
        K,L,m=p['K'],p['L'],p['method'];prefix=f'k{K}/{m}_L{L}';get=lambda fn:raw[prefix+'/raw/'+fn]
        ids=np.frombuffer(get('ids.i32'),'<i4').reshape(n,K);dist=np.frombuffer(get('distances.f32'),'<f4').reshape(n,K)
        assert np.isfinite(dist).all() and (np.diff(dist,axis=1)>=0).all()
        assert ((ids>=0)&(ids<cfg['base']['n'])).all() and all(len(set(a))==K for a in ids)
        h=hashlib.sha256(struct.pack('<QQ',n,K))
        for fn in ['ids.i32','distances.f32','entry_ids.i32','profile_distances.f32']:h.update(get(fn))
        h.update(bytes(16*n))
        for rr in p['rounds']:assert rr['threads']==1 and rr['packet_sha256']==h.hexdigest()
        hash_checks+=1
        hits=np.asarray([len(set(a)&set(g[:K])) for a,g in zip(ids,G)],dtype='int16')
        work=np.frombuffer(raw[prefix+'/work.u64'],'<u8').reshape(n,8)
        decision=np.frombuffer(raw[prefix+'/decisions.i32'],'<i4').reshape(n,4)
        packets[K,L,m]=(ids,dist,hits,work,decision)
        hits_archive['|'.join(map(str,[ds,window,K,L,m]))]=hits
        qp=[x['qps'] for x in p['rounds']];assert abs(p['qps']-sorted(qp)[1])<1e-8
        row=dict(dataset=ds,window=window,K=K,L=L,method=m,n=n,hits=int(hits.sum()),recall_pct=100*float(hits.mean())/K,
            qps=p['qps'],qps_min=min(qp),qps_max=max(qp),mean_us=1e6/p['qps'],formal_wall_seconds=sum(x['wall_seconds'] for x in p['rounds']),
            failed_lt10=int((hits<10).sum()) if K==100 else '',C_exact_per_query=float(work[:,0].mean()),aux_exact_per_query=float(work[:,2].mean()),
            aux_expanded_per_query=float(work[:,3].mean()),neighbor_slots_per_query=float(work[:,4].mean()),
            actual_enabled_queries=int((decision[:,1]>0).sum()),gate_entered_queries=int(decision[:,2].sum()),
            budget96_queries=int((decision[:,1]==96).sum()),budget384_queries=int((decision[:,1]==384).sum()))
        local.append(row)
    bykey={(p['K'],p['L'],p['method']):p for p in local}
    for key,(ids,dist,hits,work,decision) in packets.items():
        K,L,m=key;prefix=f'k{K}/{m}_L{L}';row=bykey[key]
        if prefix+'/witness.bin.gz' in raw:
            data=raw[prefix+'/witness.bin.gz'];pos=0;counts=[]
            dtype=np.dtype([('id','<i4'),('v','<f4')])
            for qi in range(n):
                i,k,ne,ns=struct.unpack_from('<IIII',data,pos);pos+=16;assert i==qi and k==K
                main=np.frombuffer(data,dtype,count=K,offset=pos);pos+=K*8
                extra=np.frombuffer(data,dtype,count=ne,offset=pos);pos+=ne*8
                seeds=np.frombuffer(data,'<i4',count=ns,offset=pos);pos+=ns*4
                ii=np.r_[main['id'],extra['id']];vv=np.r_[main['v'],extra['v']]
                assert len(set(ii))==len(ii)
                order=np.lexsort((np.arange(len(ii)),vv))[:K]
                assert np.array_equal(ii[order],ids[qi]) and np.array_equal(vv[order].view('<u4'),dist[qi].view('<u4'))
                if m in ['OPT-B32','Q8-B32']:counts.append(ne)
                if m in ['DIST96','DIST384','FAST96','FAST384','CASCADE96','CASCADE384','ADAPT','POLICY','TEACHER384','OLD-CACHED384']:
                    assert ns<=1 and (ns==0 or seeds[0]==decision[qi,0])
                    assert work[qi,2]<=decision[qi,1] and work[qi,4]<=64*decision[qi,1]
                witness_checks+=1
            assert pos==len(data)
            if counts:row['C_exact_per_query']=float(np.mean(counts))
        for bm,label in [('GT10','GT10'),('OPT-B32','fullB32'),('Q8-B32','Q8')]:
            if (K,L,bm) not in packets:continue
            base=packets[K,L,bm];g,l=paired(ids,base[0],G,K);delta=hits-base[2]
            assert g-l==int(delta.sum())
            row.update({f'gain_vs_{label}_pp':100*float(delta.mean())/K,f'rescued_vs_{label}':g,f'lost_vs_{label}':l})
        if m=='OLD-CACHED384':
            a=packets[K,L,'MODEL1'];assert np.array_equal(ids,a[0]) and np.array_equal(dist.view('<u4'),a[1].view('<u4'))
            row['cache_QPS_gain_pct']=100*(row['qps']/bykey[K,L,'MODEL1']['qps']-1)
        if m=='POLICY':
            full=packets[K,L,'ADAPT'];base=packets[K,L,'Q8-B32']
            for i in range(n):
                expected=full if decision[i,2] else base
                assert np.array_equal(ids[i],expected[0][i]) and np.array_equal(dist[i].view('<u4'),expected[1][i].view('<u4'))
            gain=(hits-base[2]).clip(0);ref=(full[2]-base[2]).clip(0)
            mechanisms.append(dict(dataset=ds,window=window,K=K,L=L,gate_entered=int(decision[:,2].sum()),action_enabled=int((decision[:,1]>0).sum()),
                adaptive_positive_hits=int(ref.sum()),policy_positive_hits=int(gain.sum()),retention=float(gain.sum()/ref.sum()) if ref.sum() else None,
                wrong_rejected_positive_queries=int(((ref>0)&(decision[:,2]==0)).sum()),
                positive_enabled_queries=int(((gain>0)&(decision[:,1]>0)).sum()),budget96=int((decision[:,1]==96).sum()),budget384=int((decision[:,1]==384).sum())))
        if m not in ['GT10','OPT-B32','REUSE-SQ']:
            controls=[p for p in local if p['K']==K and p['method'] in ['GT10','OPT-B32','REUSE-SQ']]
            covers=[p for p in controls if p['hits']>=row['hits'] and p['qps']>=row['qps'] and (p['hits']>row['hits'] or p['qps']>row['qps'])]
            qcontrols=[p for p in controls if p['hits']>=row['hits']]
            chosen=max(qcontrols,key=lambda p:p['qps']) if qcontrols else None
            comp=dict(dataset=ds,window=window,K=K,L=L,method=m,covered=bool(covers),range_covered=any(p['qps_min']>=row['qps_max'] for p in covers),
                quality_threshold_control=f"{chosen['method']}/L{chosen['L']}" if chosen else '',quality_threshold_QPS_gain_pct=100*(row['qps']/chosen['qps']-1) if chosen else None)
            fast=[p for p in controls if p['qps']>=row['qps']]
            if fast:
                best=max(fast,key=lambda p:(p['hits'],p['qps']));delta=hits-packets[K,best['L'],best['method']][2]
                rng=np.random.default_rng(198);boots=100*np.mean(delta[rng.integers(0,n,(1000,n))],axis=1)/K
                comp.update(no_slower_control=f"{best['method']}/L{best['L']}",gain_vs_no_slower_pp=100*float(delta.mean())/K,descriptive_ci_low=float(np.quantile(boots,.025)),descriptive_ci_high=float(np.quantile(boots,.975)))
            comparisons.append(comp)
    # Recompute every public seed/budget/gate decision with NumPy and exported tree structures.
    for K,L in STATES:
        data=raw[f'k{K}/POLICY_L{L}/selection.bin.gz'];pos=0;features=[];nodeid=[];groups={};gatex=[]
        for qi in range(n):
            q,nc=struct.unpack_from('<II',data,pos);pos+=8;assert q==qi
            gatex.append(np.frombuffer(data,'<f4',count=12,offset=pos).copy());pos+=48
            begin=len(features)
            for j in range(nc):
                nodeid.append(struct.unpack_from('<i',data,pos)[0]);pos+=4
                features.append(np.frombuffer(data,'<f4',count=104,offset=pos).copy());pos+=416
            if nc:groups[qi]=np.arange(begin,len(features))
        assert pos==len(data)
        f=np.asarray(features);nodeid=np.asarray(nodeid);mf=R/'storage/models'/ds/f'k{K}_L{L}'/'model.json';model=read(mf)
        ni=np.fromfile(model['node_ids'],'<i4');ne=np.fromfile(model['node_embeddings'],'<f8').reshape(-1,32)
        model['_ids']=nodeid;sp=student_predict(model,f,ne,ni);del model['_ids']
        tp=np.column_stack([predict_tree(t,f) for t in model['teacher']]);gp=predict_tree(model['gate'],np.asarray(gatex))
        selected=select(groups,sp,tp,np.zeros_like(tp),model['lam'])
        for x in selected:
            qi=x['q'];ix=groups[qi];gate=(not model['gate']['gate_all_off']) and gp[qi]>=model['gate']['threshold']
            for method,b in [('FAST96',0),('FAST384',1),('CASCADE96',0),('CASCADE384',1),('ADAPT',-1),('POLICY',-1),('TEACHER384',1),('DIST96',0),('DIST384',1)]:
                d=packets[K,L,method][4][qi];chosen=-1;budget=0
                if method.startswith('FAST'):chosen=x['fast'][b];budget=[96,384][b]
                elif method.startswith('CASCADE'):chosen=x['cascade'][b];budget=[96,384][b]
                elif method.startswith('DIST'):chosen=int(ix[0]);budget=[96,384][b]
                elif method=='TEACHER384':chosen=max(ix,key=lambda j:(tp[j,1],-j));budget=384
                elif method=='ADAPT' or gate:
                    chosen=x['action_index'];budget=[96,384][x['action_budget']] if x['action_budget']>=0 else 0
                assert d[0]==(nodeid[chosen] if chosen>=0 else -1) and d[1]==budget,(ds,window,K,L,method,qi,d,chosen,budget)
                if method=='POLICY':assert bool(d[2])==gate
                selection_checks+=1
        # Quality contribution at matched direct bank and budget.
        for method,reference in [('FAST96','DIST96'),('FAST384','DIST384'),('CASCADE96','DIST96'),('CASCADE384','DIST384'),('TEACHER384','DIST384'),('POLICY','ADAPT')]:
            a,b=bykey[K,L,method],bykey[K,L,reference]
            quality.append(dict(dataset=ds,window=window,K=K,L=L,method=method,reference=reference,gain_pp=a['recall_pct']-b['recall_pct'],QPS_change_pct=100*(a['qps']/b['qps']-1)))
    points+=local;print('ANALYZED',ds,window,len(local),flush=True)
wide('points.csv',points);wide('comparisons.csv',comparisons);wide('mechanisms.csv',mechanisms);wide('selection_quality.csv',quality)
np.savez_compressed(R/'analysis/query_hits.npz',**hits_archive)
by=collections.defaultdict(list)
for r in comparisons:by[r['dataset'],r['K'],r['L'],r['method']].append(r)
stable=[]
for key,rr in by.items():
    assert len(rr)==2
    stable.append(dict(dataset=key[0],K=key[1],L=key[2],method=key[3],both_uncovered=all(not x['covered'] for x in rr),covered_windows=sum(x['covered'] for x in rr)))
wide('stability.csv',stable)
receipt=dict(status='PASS_NATIVE_PACKET_FULLSORT_AND_INDEPENDENT_POLICY_ANALYSIS',points=len(points),packet_hash_checks=hash_checks,query_witness_fullsort_checks=witness_checks,independent_model_decision_checks=selection_checks,
             formal_batch_wall_seconds=sum(x['formal_wall_seconds'] for x in points),seconds=time.perf_counter()-started,default_changed=False,new_PDF=False)
dump(R/'analysis/analysis_receipt.json',receipt);print(json.dumps(receipt),flush=True)
