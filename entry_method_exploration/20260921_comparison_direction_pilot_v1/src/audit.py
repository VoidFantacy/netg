"""Independent byte, response, model-forward and decision audits."""
from common import *

def popcount(a):
    a=np.ascontiguousarray(a,dtype=np.uint64)
    return np.unpackbits(a.view(np.uint8).reshape(a.shape+(8,)),axis=-1).sum(axis=-1)

def return_hash(ids,dist):
    ids=np.asarray(ids);bits=np.ascontiguousarray(dist,dtype=np.float32).view(np.uint32)
    h=np.full(ids.shape[:-1],1469598103934665603,dtype=np.uint64)
    for k in range(ids.shape[-1]):
        h=(h^ids[...,k].astype(np.uint64))*np.uint64(1099511628211)
        h=(h^bits[...,k].astype(np.uint64))*np.uint64(1099511628211)
    return h

def score(ids,gt,K):
    ids=np.asarray(ids);gt=np.asarray(gt);assert ids.shape==(len(gt),K)
    if K==1:return (ids[:,0]==gt[:,0]).astype(np.int64)
    assert K==100
    return np.array([len(set(i.tolist())&set(g.tolist())) for i,g in zip(ids,gt)],np.int64)

def audit_inputs(ds):
    c=LOCK['datasets'][ds];d=c['dimension'];checks=[];allhashes=set();allrows=set()
    for role,(a,b) in LOCK['roles'].items():
        p=RUN/'inputs'/ds/role
        if not(p/'identity.json').exists():continue
        rec=read(p/'identity.json')
        for f in rec['files']:assert ident(f['path'])==f
        q=np.fromfile(p/'queries.f32',np.float32).reshape(b-a,d)
        src=np.memmap(c['fit_source']['queries_file'],dtype=np.float32,mode='r',shape=(20000,d))[a:b]
        assert q.tobytes()==src.tobytes()
        hashes=[hashlib.sha256(v.tobytes()).hexdigest() for v in q];assert hashes==rec['query_hashes']
        assert len(set(hashes))==b-a and not allhashes&set(hashes);allhashes.update(hashes)
        rows=np.fromfile(p/'row_ids.i64',np.int64);assert np.array_equal(rows,np.arange(10000+a,10000+b))
        assert not allrows&set(rows);allrows.update(rows)
        if (p/'gt.i64').exists():
            gt=np.fromfile(p/'gt.i64',np.int64).reshape(b-a,100)
            sg=np.memmap(c['fit_source']['gt_file'],dtype=np.int64,mode='r',shape=(20000,100))[a:b]
            assert gt.tobytes()==sg.tobytes() and all(len(set(row.tolist()))==100 for row in gt)
        checks.append(dict(role=role,rows=b-a))
    hubs=np.fromfile(c['anchor']['ids'],np.int32);sourcehubs=np.fromfile(c['fit_source']['hub_ids'],np.int32)
    assert np.array_equal(hubs,sourcehubs),'all H action-to-real-ID identity'
    dump(RUN/'reviews'/f'input_audit_{ds}.json',dict(status='PASS',roles=checks,hub_ids_match=True))

def audit_directions(ds):
    c=LOCK['datasets'][ds];d=c['dimension'];p=RUN/'results'/ds/'directions';done=read(p/'complete.json');n=done['n'];m=done['samples']
    q=np.fromfile(RUN/'inputs'/ds/'directions/queries.f32',np.float32).reshape(n,d)
    base=np.memmap(c['base'],dtype=np.float32,mode='r',shape=(c['base_n'],d+1))
    sizes=np.fromfile(p/'sample_sizes.u32',np.uint32);keys=np.fromfile(p/'pair_keys.u64',np.uint64).reshape(n,m)
    codes=np.fromfile(p/'pair_codes.u8',np.uint8).reshape(n,m)
    native=np.fromfile(p/'sample_directions.f32',np.float32).reshape(n,m,d)
    checked=ambiguous=disagree=0;maxerr=0.
    for lo in range(0,n,16):
        hi=min(lo+16,n);valid=np.arange(m)[None,:]<sizes[lo:hi,None]
        pair=keys[lo:hi][valid];ia=pair>>np.uint64(32);ib=pair&np.uint64(0xffffffff)
        assert np.all(ia<ib) and np.all(ib<c['base_n'])
        a=np.asarray(base[ia.astype(np.int64),1:],float);b=np.asarray(base[ib.astype(np.int64),1:],float);diff=a-b
        norm=np.linalg.norm(diff,axis=1);assert np.all(norm>0)
        pivot=np.abs(diff).argmax(axis=1);sign=np.where(diff[np.arange(len(diff)),pivot]>=0,1.,-1.)
        expected=diff*(sign/norm)[:,None];observed=native[lo:hi][valid]
        err=float(np.max(np.abs(expected-observed)));maxerr=max(maxerr,err);assert err<1e-7
        owner=np.broadcast_to(np.arange(lo,hi)[:,None],(hi-lo,m))[valid];queries=q[owner].astype(float)
        ipdiff=np.sum(queries*diff,axis=1)
        # Conservative scalar-float accumulation bound; report every near tie separately.
        tol=8*d*np.finfo(np.float32).eps*np.sum(np.abs(queries)*(np.abs(a)+np.abs(b)),axis=1)
        near=np.abs(ipdiff)<=tol;code=codes[lo:hi][valid]&7
        expected_sign=np.where(ipdiff>0,1,2);bad=(code!=expected_sign)&~near
        assert not np.any(bad),(ds,int(bad.sum()))
        ambiguous+=int(near.sum());disagree+=int((code!=expected_sign).sum());checked+=len(pair)
    dump(RUN/'reviews'/f'direction_audit_{ds}.json',dict(status='PASS',pairs=checked,max_vector_abs_error=maxerr,
        float_margin_ambiguous=ambiguous,float64_sign_differences=disagree,unambiguous_sign_errors=0))

def audit_labels(ds):
    p=RUN/'results'/ds/'labels';done=read(p/'complete.json');n,A=done['n'],done['A']
    gt=np.fromfile(RUN/'inputs'/ds/'fit/gt.i64',np.int64).reshape(n,100);checked=0;samplechecks=0;calls=0
    all_times=[];all_delta=[]
    for z in sorted(done['blocks'],key=lambda a:a['start']):
        lo,nb=z['start'],z['n'];bp=p/f'block_{lo}'
        h1=np.fromfile(bp/'hits1.u8',np.uint8).reshape(nb,A);h100=np.fromfile(bp/'hits100.u8',np.uint8).reshape(nb,A)
        masks=np.fromfile(bp/'masks.u64',np.uint64).reshape(nb,A,2);top=np.fromfile(bp/'top1_ids.i32',np.int32).reshape(nb,A)
        assert np.array_equal(h1,(top==gt[lo:lo+nb,:1]).astype(np.uint8))
        assert np.array_equal(h100,popcount(masks).sum(axis=2)) and np.all(masks[:,:,1]>>np.uint64(36)==0)
        t=np.fromfile(bp/'seconds.f64',np.float64).reshape(nb,A,2,3);assert np.isfinite(t).all() and np.all(t>0)
        schedule=read(bp/'timing_schedule.json');assert len(schedule)==6
        assert sorted((s['repeat'],s['K']) for s in schedule)==[(r,k) for r in range(3) for k in (1,100)]
        for s in schedule:assert sorted(s['order'])==list(range(A))
        ids=np.fromfile(bp/'sample_ids.i32',np.int32).reshape(A,100);dist=np.fromfile(bp/'sample_distances.f32',np.float32).reshape(A,100)
        hashes=np.fromfile(bp/'return_hashes.u64',np.uint64).reshape(nb,A)
        assert np.array_equal(return_hash(ids,dist),hashes[0])
        truth={int(e):j for j,e in enumerate(gt[lo])}
        for a,row in enumerate(ids):
            expected=[0,0]
            for entry in row:
                if int(entry) in truth:
                    rank=truth[int(entry)];expected[rank//64]|=1<<(rank%64)
            assert expected==masks[0,a].tolist() and len(set(row.tolist()))==100
        bids=np.fromfile(bp/'baseline_ids.i32',np.int32).reshape(nb,100);bd=np.fromfile(bp/'baseline_distances.f32',np.float32).reshape(nb,100)
        assert np.array_equal(score(bids,gt[lo:lo+nb],100),h100[:,0])
        assert np.array_equal(return_hash(bids,bd),hashes[:,0])
        expected_calls=nb*A*7+3;assert z['search_calls']==expected_calls;calls+=expected_calls
        all_times.append(t);all_delta.append(t[:,1:]-t[:,:1]);checked+=nb*A;samplechecks+=A
    assert calls==done['search_calls']
    times=np.concatenate(all_times);delta=np.concatenate(all_delta);stability={}
    for ki,K in enumerate((1,100)):
        per_round=delta[:,:,ki,:];first=per_round[:,:,0];last=per_round[:,:,1:].mean(axis=2)
        corr=float(np.corrcoef(first.ravel(),last.ravel())[0,1])
        means=per_round.mean(axis=0);tmean=times[:,:,ki,:].mean(axis=(0,1))
        stability[str(K)]=dict(delta_repeat0_vs_repeats12_correlation=corr,
            per_query_hub_sign_agreement=float(np.mean((first>=0)==(last>=0))),
            hub_mean_sign_agreement=float(np.mean((means[:,0]>=0)==(means[:,1:].mean(axis=1)>=0))),
            absolute_seconds_mean_by_repeat=tmean.tolist(),
            relative_repeat_range=float((tmean.max()-tmean.min())/tmean.mean()),
            delta_seconds_quantiles=np.quantile(per_round,[0,.01,.5,.99,1]).tolist())
    dump(RUN/'reviews'/f'label_audit_{ds}.json',dict(status='PASS',all_query_actions=checked,sampled_full_returns=samplechecks,
        search_calls=calls,timing_stability=stability,timing_noise_is_diagnostic_not_automatic_method_rejection=True))

def audit_predictions(ds,role):
    c=LOCK['datasets'][ds];n=LOCK['roles'][role][1]-LOCK['roles'][role][0];hubs=np.fromfile(c['anchor']['ids'],np.int32);H=len(hubs)
    result=[];labels=load_labels(ds) if role=='fit' else None
    time_mean=labels['time'].mean(axis=3) if labels is not None else None
    training=read(RUN/'models'/ds/'training_report.json')['methods']
    for m in read(RUN/'models'/ds/'methods.json'):
        if m['type']!='learned':continue
        model=read(m['model']);f=model['features']['name'];X=np.fromfile(RUN/'results'/ds/f'{role}_features'/f'{f}.features.f32',np.float32).reshape(n,-1).astype(float)
        for K in (1,100):
            head=model['heads'][str(K)];w=np.fromfile(head['weights'],np.float32).reshape(H,-1).astype(float);b=np.fromfile(head['bias'],np.float32).astype(float)
            mp=Path(m['model']).parent;cost=model['cost_weight'];assert cost==(0. if m['name']=='GraphRecall' else LOCK['cost_weight'])
            wr=np.fromfile(mp/f'K{K}.recall_weights.f32',np.float32).reshape(w.shape).astype(float);br=np.fromfile(mp/f'K{K}.recall_bias.f32',np.float32).astype(float)
            wt=np.fromfile(mp/f'K{K}.time_weights.f32',np.float32).reshape(w.shape).astype(float);bt=np.fromfile(mp/f'K{K}.time_bias.f32',np.float32).astype(float)
            wtolerance=8*np.finfo(np.float32).eps*(np.abs(wr)+cost*np.abs(wt)+np.abs(w)+1e-30)
            btolerance=8*np.finfo(np.float32).eps*(np.abs(br)+cost*np.abs(bt)+np.abs(b)+1e-30)
            assert np.all(np.abs(w-(wr-cost*wt))<=wtolerance) and np.all(np.abs(b-(br-cost*bt))<=btolerance),'recall/time head folding'
            s=X@w.T+b;order=np.argsort(hubs,kind='stable');idx=order[np.argmax(s[:,order],axis=1)]
            mse_error=None
            if labels is not None:
                ki=0 if K==1 else 1;recall=labels['r1'] if K==1 else labels['r100'];tref=float(time_mean[:,0,ki].mean())
                assert abs(model['tref_seconds'][ki]/tref-1)<1e-12
                actual_utility=recall[:,1:]-recall[:,:1]-cost*(time_mean[:,1:,ki]-time_mean[:,:1,ki])/tref
                mse=float(np.mean((s-actual_utility)**2));expected_mse=training[m['name']]['training'][str(K)]['utility_mse']
                mse_error=abs(mse-expected_mse);assert mse_error<1e-10,'independent training utility/export MSE'
            expected=np.where(s[np.arange(n),idx]>0,idx+1,0)
            actual=np.fromfile(RUN/'results'/ds/f'{role}_predictions'/f"{m['name']}_K{K}.actions.i32",np.int32)
            assert actual.shape==(n,) and np.all((actual>=0)&(actual<=H))
            # Floating-point candidates must fall within a conservative dot-product error bound.
            err=8*np.finfo(np.float32).eps*(X.shape[1]*(np.abs(X)@np.abs(w).T)+np.abs(b)[None,:]+1e-20)
            augmented=np.concatenate([np.zeros((n,1)),s],axis=1);bounds=np.concatenate([np.zeros((n,1)),err],axis=1)
            exactmax=augmented.max(axis=1);selected=augmented[np.arange(n),actual]
            selectedbound=bounds[np.arange(n),actual];maxbound=bounds[np.arange(n),augmented.argmax(axis=1)]
            assert np.all(exactmax-selected<=selectedbound+maxbound+1e-12),'native prediction outside float error bound'
            changed=np.flatnonzero(actual!=expected)
            result.append(dict(method=m['name'],K=K,queries=n,exact_action_matches=int(n-len(changed)),
                               near_tie_differences=changed.tolist(),largest_selection_loss=float((exactmax-selected).max()),
                               max_weight_folding_error=float(np.max(np.abs(w-(wr-cost*wt)))),independent_training_utility_mse_error=mse_error))
    dump(RUN/'reviews'/f'prediction_audit_{role}_{ds}.json',dict(status='PASS',records=result))
    return result

def audit_fit_replay(ds):
    p=RUN/'results'/ds/'fit_replay';lab=RUN/'results'/ds/'labels';n=4096;done=read(lab/'complete.json');A=done['A']
    masks=[];hashes=[];top=[];baseids=[];baseentries=[]
    for z in sorted(done['blocks'],key=lambda a:a['start']):
        bp=lab/f"block_{z['start']}";nb=z['n']
        hashes.append(np.fromfile(bp/'return_hashes.u64',np.uint64).reshape(nb,A));top.append(np.fromfile(bp/'top1_ids.i32',np.int32).reshape(nb,A))
        masks.append(np.fromfile(bp/'masks.u64',np.uint64).reshape(nb,A,2))
        baseids.append(np.fromfile(bp/'baseline_ids.i32',np.int32).reshape(nb,100));baseentries.append(np.fromfile(bp/'baseline_entries.i32',np.int32).reshape(nb,3))
    hashes=np.concatenate(hashes);top=np.concatenate(top);masks=np.concatenate(masks);baseids=np.concatenate(baseids);baseentries=np.concatenate(baseentries)
    gt=np.fromfile(RUN/'inputs'/ds/'fit/gt.i64',np.int64).reshape(n,100);checked=0
    for m in read(RUN/'models'/ds/'methods.json'):
        if m['name']=='NSG':continue
        for K in (1,100):
            f=p/f"{m['name']}_K{K}_L128";a=np.fromfile(f/'actions.i32',np.int32);ids=np.fromfile(f/'ids.i32',np.int32).reshape(n,K)
            dist=np.fromfile(f/'distances.f32',np.float32).reshape(n,K);assert np.all((a>=0)&(a<A))
            assert np.array_equal(ids[:,0],top[np.arange(n),a])
            if K==100:assert np.array_equal(return_hash(ids,dist),hashes[np.arange(n),a])
            hit=score(ids,gt,K);expect=(top[np.arange(n),a]==gt[:,0]) if K==1 else popcount(masks[np.arange(n),a]).sum(axis=1)
            assert np.array_equal(hit,expect)
            if m['type']=='learned':
                pa=np.fromfile(RUN/'results'/ds/'fit_predictions'/f"{m['name']}_K{K}.actions.i32",np.int32);assert np.array_equal(a,pa)
            if m['name']=='GT10':
                assert np.array_equal(ids,baseids[:,:K]);assert np.array_equal(np.fromfile(f/'entry_ids.i32',np.int32).reshape(n,3),baseentries)
            checked+=n
    dump(RUN/'reviews'/f'fit_replay_audit_{ds}.json',dict(status='PASS',query_method_K_checks=checked,all_K100_hashes_match_labels=True))

def audit_acceptance(ds):
    root=RUN/'results'/ds;c=LOCK['datasets'][ds];n=4096;hubs=np.fromfile(c['anchor']['ids'],np.int32)
    gt=np.fromfile(RUN/'inputs'/ds/'accept/gt.i64',np.int64).reshape(n,100);checks=[];prefix_checks=[]
    old=ROOT/'entry_method_exploration/20260920_entry_set_pilot_v1'
    for fn in ('queries.f32','gt.i64','row_ids.i64'):assert sha(RUN/'inputs'/ds/'accept'/fn)==sha(old/'inputs'/ds/'accept'/fn)
    methods={m['name']:m for m in read(RUN/'models'/ds/'methods.json')}
    for batch in ('accept','curve'):
        config=read(root/batch/'config.json');assert read(root/batch/'complete.json')['status']=='PASS'
        for point in config['points']:
            K,L=point['K'],point['L'];base=root/batch/f'GT10_K{K}_L{L}'
            baseline_entries=np.fromfile(base/'entry_ids.i32',np.int32).reshape(n,3)
            for m in config['methods']:
                p=root/batch/f"{m['name']}_K{K}_L{L}";z=read(p/'complete.json');assert z['threads']==1 and len(z['seconds'])==3
                I=np.fromfile(p/'ids.i32',np.int32).reshape(n,K);D=np.fromfile(p/'distances.f32',np.float32).reshape(n,K)
                a=np.fromfile(p/'actions.i32',np.int32);E=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3)
                assert np.isfinite(D).all() and np.all((I>=0)&(I<c['base_n']))
                if K==100:assert all(len(set(row.tolist()))==100 for row in I)
                if m['type']=='learned':
                    expected=np.fromfile(root/'accept_predictions'/f"{m['name']}_K{K}.actions.i32",np.int32)
                    assert np.array_equal(a,expected)
                if m['name'] in ('GT10','FeatureDefault'):assert np.all(a==0)
                if m['name']!='NSG':
                    fallback=a==0;assert np.array_equal(E[fallback],baseline_entries[fallback])
                    assert np.array_equal(E[~fallback,0],hubs[a[~fallback]-1]) and np.all(E[~fallback,1:]==-1)
                    bi=np.fromfile(base/'ids.i32',np.int32).reshape(n,K);bd=np.fromfile(base/'distances.f32',np.float32).reshape(n,K)
                    assert np.array_equal(I[fallback],bi[fallback]) and D[fallback].tobytes()==bd[fallback].tobytes()
                if L==128 and m['name'] in ('GT10','Single1'):
                    op=old/'results'/ds/'accept'/p.name
                    for fn in ('ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64'):assert sha(p/fn)==sha(op/fn),(ds,m['name'],fn)
                h=score(I,gt,K);checks.append(dict(batch=batch,method=m['name'],K=K,L=L,hits=int(h.sum()),zero_queries=int((h==0).sum())))
        common_L=sorted({p['L'] for p in config['points'] if p['K']==1}&{p['L'] for p in config['points'] if p['K']==100})
        for L in common_L:
            for m in config['methods']:
                p1=root/batch/f"{m['name']}_K1_L{L}";p100=root/batch/f"{m['name']}_K100_L{L}"
                a1=np.fromfile(p1/'actions.i32',np.int32);a100=np.fromfile(p100/'actions.i32',np.int32);same=a1==a100
                I1=np.fromfile(p1/'ids.i32',np.int32);I100=np.fromfile(p100/'ids.i32',np.int32).reshape(n,100)
                D1=np.fromfile(p1/'distances.f32',np.float32);D100=np.fromfile(p100/'distances.f32',np.float32).reshape(n,100)
                N1=np.fromfile(p1/'graph_ndc.u64',np.uint64);N100=np.fromfile(p100/'graph_ndc.u64',np.uint64)
                assert np.array_equal(I1[same],I100[same,0]) and D1[same].tobytes()==D100[same,0].tobytes()
                assert np.array_equal(N1[same],N100[same])
                prefix_checks.append(dict(batch=batch,method=m['name'],L=L,same_action_queries=int(same.sum()),different_action_queries=int((~same).sum())))
    dump(RUN/'reviews'/f'acceptance_audit_{ds}.json',dict(status='PASS',points=checks,same_action_K_prefix_checks=prefix_checks,old_GT10_and_Single1_restored=True))
