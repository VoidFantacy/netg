"""Three fixed closed-form profiles; exact recovery before real/sham construction."""
from shared import *
threads();resources();check(O/'reviews/prebuild_freeze.json');started=time.monotonic();records=[]
for ds in DS:
    begin=time.monotonic();c=read(O/'inputs'/ds/'config.json');d=c['dim'];h=c['hub_count']
    P=np.fromfile(c['P'],np.float32).reshape(h,d);q=normalize(np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d))
    gt=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100);hn=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d))
    targetbase=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1)
    masks=dict(np.load(O/'inputs'/ds/'missing_supervision.npz'));m=masks['counts'];has=m>0
    # Each query retains mass one; missing and sham average only their chosen ranks.
    weights=[np.zeros((20000,h),np.float64) for _ in range(3)]
    for rank in range(10):
        tv=np.asarray(targetbase[gt[:,rank],1:],np.float32);tn=normalize(tv)
        for start in range(0,20000,4096):
            stop=min(start+4096,20000);s=tn[start:stop]@hn.T
            if c['temperature'] is None:
                a=np.zeros(s.shape,np.float64);a[np.arange(stop-start),np.argmax(s,axis=1)]=1
            else:
                a=s.astype(np.float64);a-=a.max(1,keepdims=True);a/=c['temperature'];np.exp(a,out=a);a/=a.sum(1,keepdims=True)
            weights[0][start:stop]+=a/10
            for j,key in [(1,'missing'),(2,'sham')]:
                coef=np.divide(masks[key][start:stop,rank],m[start:stop],out=np.zeros(stop-start),where=has[start:stop])
                weights[j][start:stop]+=a*coef[:,None]
        print('ASSIGNMENT',ds,'rank',rank+1,flush=True)
    assert digest(weights[0])==c['original_assignments_sha'],'Original A0 identity mismatch'
    sums=hn.astype(np.float64)+weights[0].T@q.astype(np.float64);recovered=(sums/np.maximum(np.linalg.norm(sums,axis=1,keepdims=True),1e-12)).astype(np.float32)
    assert recovered.tobytes()==P.tobytes(),'Original P byte recovery failed'
    raw_seconds=time.monotonic()-begin;models=[]
    for j,label in enumerate(LABELS):
        tick=time.monotonic()
        if j:
            weights[j][~has]=weights[0][~has]
            weights[j]=.5*weights[0]+.5*weights[j]
        A=weights[j];row_mass=A.sum(1);assert np.max(np.abs(row_mass-1))<2e-12 and A.min()>=0
        assert np.array_equal(A[~has],weights[0][~has])
        if j:
            S=hn.astype(np.float64)+A.T@q.astype(np.float64);W=(S/np.maximum(np.linalg.norm(S,axis=1,keepdims=True),1e-12)).astype(np.float32)
        else:W=P.copy()
        folder=O/'models'/ds/label;folder.mkdir(parents=True);W.tofile(folder/'W.f32')
        mass=A.sum(0);sq=np.square(A).sum(0);ess=np.divide(mass*mass,sq,out=np.zeros_like(mass),where=sq>0)
        save(folder/'support.npz',query_mass=row_mass,hub_mass=mass,ess=ess,profile_displacement=np.linalg.norm(W.astype(float)-P,axis=1))
        # Fixed scalar-reference queries/hubs support an independent reconstruction later.
        sample_rows=np.arange(0,20000,137,dtype=np.int32);save(folder/'assignment_sample.npz',rows=sample_rows,weights=A[sample_rows])
        meta=dict(model=label,W=identity(folder/'W.f32'),assignment_sha=digest(A),query_count=20000,lambda_value=0 if j==0 else .5,
             max_mass_error=float(np.max(np.abs(row_mass-1))),changed_profiles=int((W!=P).any(1).sum()),
             mean_profile_displacement=float(np.linalg.norm(W.astype(float)-P,axis=1).mean()),
             aggregate_seconds=time.monotonic()-tick,initial_P_byte_recovery=True)
        dump(folder/'manifest.json',meta);models.append(meta)
    records.append(dict(dataset=ds,models=models,shared_assignment_and_recovery_seconds=raw_seconds,total_seconds=time.monotonic()-begin,
        zero_missing_queries=int((m==0).sum()),full_missing_queries=int((m==10).sum())))
    print('PROFILES_COMPLETE',ds,time.monotonic()-begin,flush=True)
dump(O/'results/build.json',dict(status='PASS_ORIGINAL_A0_AND_P_BYTE_RECOVERY',datasets=records,seconds=time.monotonic()-started,new_NSG=0,new_GT=0,gradient_updates=0))
paths=[p for root in ['src','models','inputs'] for p in (O/root).rglob('*') if p.is_file()]+[O/'protocol.md',O/'config.locked.json',O/'bin/environment.so',O/'reviews/prebuild_freeze.json']
dump(O/'reviews/models_before_queries.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(paths)]))
dump(O/'state.json',dict(status='SIX_PROFILES_FROZEN_BEFORE_DEVELOPMENT',models_built=6,next_command='src/run.py <dataset>',new_NSG=0))
