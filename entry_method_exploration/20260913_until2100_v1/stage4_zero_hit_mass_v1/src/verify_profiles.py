"""Independent set-derived weights and rank-first streaming profile reference."""
from shared import *
threads();resources();check(O/'reviews/models_before_queries.json');started=time.monotonic();records=[]
for ds in DS:
    c=read(O/'inputs'/ds/'config.json');d=c['dim'];h=c['hub_count']
    q=normalize(np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d));gt=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100)
    hn=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d));base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1)
    cache=dict(np.load(O/'inputs'/ds/'baseline.npz'));sup=dict(np.load(O/'inputs'/ds/'mass_supervision.npz'))
    z=np.array([not(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(cache['ids'][:20000],gt)])
    assert np.array_equal(z,sup['zero']);n=int(z.sum());rows=np.sort(np.random.default_rng(20260913).choice(20000,n,replace=False))
    assert np.array_equal(rows,sup['sham_rows']);sh=np.zeros(20000,bool);sh[rows]=True;assert np.array_equal(sh,sup['sham'])
    weights=[np.ones(20000)]+[np.array([20000*(2 if b else 1)/(20000+n) for b in mask]) for mask in [z,sh]]
    for w,key in zip(weights[1:],['weights','sham_weights']):assert np.array_equal(w,sup[key]) and abs(w.sum()-20000)<1e-8
    acc=[hn.astype(float).copy() for _ in LABELS];sample=np.arange(0,20000,137,dtype=np.int32);wa=[np.zeros((len(sample),h)) for _ in LABELS]
    for rank in range(10):
        tv=normalize(np.asarray(base[gt[:,rank],1:],np.float32))
        for start in range(0,20000,4096):
            stop=min(start+4096,20000);s=tv[start:stop]@hn.T
            if c['temperature'] is None:
                a=np.zeros(s.shape);a[np.arange(stop-start),s.argmax(1)]=1
            else:
                a=np.exp((s.astype(float)-s.max(1)[:,None])/c['temperature']);a/=a.sum(1)[:,None]
            keep=np.flatnonzero((sample>=start)&(sample<stop));loc=sample[keep]-start
            for j,w in enumerate(weights):
                acc[j]+=a.T@(q[start:stop].astype(float)*(w[start:stop]/10)[:,None])
                wa[j][keep]+=a[loc]*(w[sample[keep]]/10)[:,None]
    checks=[]
    for j,name in enumerate(LABELS):
        W=np.fromfile(O/'models'/ds/name/'W.f32',np.float32).reshape(h,d);ref=acc[j]/np.linalg.norm(acc[j],axis=1,keepdims=True)
        np.testing.assert_allclose(ref,W,atol=4e-8,rtol=1e-7)
        got=np.load(O/'models'/ds/name/'assignment_sample.npz')['weights'];np.testing.assert_allclose(wa[j],got,atol=2e-15,rtol=2e-13)
        mass=np.load(O/'models'/ds/name/'support.npz')['query_mass'];np.testing.assert_allclose(mass,weights[j],atol=2e-12,rtol=1e-13)
        checks.append(dict(model=name,full_profile_max_abs=float(np.abs(ref-W).max()),sample_assignment_max_abs=float(np.abs(wa[j]-got).max()),profiles_checked=h))
    records.append(dict(dataset=ds,checks=checks,independent_zero_hit_rows=20000,random_identity_replay=True,total_mass=20000))
    print('PROFILE_REFERENCE_PASS',ds,flush=True)
dump(O/'reviews/profile_verification.json',dict(status='PASS_INDEPENDENT_STREAMING_PROFILE_REFERENCE',datasets=records,seconds=time.monotonic()-started,new_native_calls=0))
