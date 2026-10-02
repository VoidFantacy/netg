"""Independent rank-weighted streaming aggregation; avoids builder's full-A-then-matmul path."""
from shared import *
threads();resources();check(O/'reviews/models_before_queries.json');started=time.monotonic();records=[]
for ds in DS:
    c=read(O/'inputs'/ds/'config.json');d=c['dim'];h=c['hub_count']
    q=normalize(np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d));gt=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100)
    raw=np.fromfile(c['raw_hubs'],np.float32).reshape(h,d);hn=normalize(raw);base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1)
    labels=dict(np.load(O/'inputs'/ds/'missing_supervision.npz'));cached=dict(np.load(O/'inputs'/ds/'baseline.npz'))
    mask=np.array([[int(g) not in set(map(int,ret)) for g in row[:10]] for ret,row in zip(cached['ids'][:20000],gt)],bool)
    assert np.array_equal(mask,labels['missing']) and np.array_equal(mask.sum(1),labels['counts'])
    numbers=np.random.default_rng(20260913).random((20000,10));control=np.zeros_like(mask)
    for i in range(20000):
        inds=sorted(range(10),key=lambda j:(numbers[i,j],j))[:int(mask[i].sum())];control[i,inds]=True
    assert np.array_equal(control,labels['sham'])
    count=mask.sum(1);has=count>0;acc=[hn.astype(np.float64).copy() for _ in LABELS]
    sample=np.load(O/'models'/ds/'baseline/assignment_sample.npz')['rows'];wa=[np.zeros((len(sample),h)) for _ in LABELS]
    for rank in range(10):
        tv=normalize(np.asarray(base[gt[:,rank],1:],np.float32))
        real=np.where(has,mask[:,rank]/np.maximum(count,1),.1);fake=np.where(has,control[:,rank]/np.maximum(count,1),.1)
        coefs=[np.full(20000,.1),.05+.5*real,.05+.5*fake]
        for start in range(0,20000,4096):
            stop=min(start+4096,20000);s=tv[start:stop]@hn.T
            if c['temperature'] is None:
                a=np.zeros(s.shape,np.float64);a[np.arange(stop-start),s.argmax(1)]=1
            else:
                logits=(s.astype(float)-s.max(1)[:,None])/c['temperature'];a=np.exp(logits);a/=a.sum(1)[:,None]
            keep=np.flatnonzero((sample>=start)&(sample<stop));loc=sample[keep]-start
            for j in range(3):
                # Aggregate each rank's weighted query contribution before moving to the next rank.
                acc[j]+=a.T@(q[start:stop].astype(float)*coefs[j][start:stop,None])
                wa[j][keep]+=a[loc]*coefs[j][sample[keep],None]
    checks=[]
    for j,name in enumerate(LABELS):
        W=np.fromfile(O/'models'/ds/name/'W.f32',np.float32).reshape(h,d);reference=acc[j]/np.linalg.norm(acc[j],axis=1,keepdims=True)
        np.testing.assert_allclose(reference,W,atol=4e-8,rtol=1e-7)
        got=np.load(O/'models'/ds/name/'assignment_sample.npz')['weights'];np.testing.assert_allclose(wa[j],got,atol=2e-15,rtol=2e-13)
        checks.append(dict(model=name,full_profile_max_abs=float(np.abs(reference-W).max()),sample_assignment_max_abs=float(np.abs(wa[j]-got).max()),profiles_checked=h,assignment_rows_checked=len(sample)))
    records.append(dict(dataset=ds,checks=checks,independent_missing_member_rows=20000,sham_exact_recovery=True))
    print('PROFILE_REFERENCE_PASS',ds,flush=True)
dump(O/'reviews/profile_verification.json',dict(status='PASS_INDEPENDENT_STREAMING_PROFILE_REFERENCE',datasets=records,seconds=time.monotonic()-started,new_native_calls=0))
