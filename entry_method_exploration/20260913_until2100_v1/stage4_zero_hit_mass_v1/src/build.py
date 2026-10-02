"""Original GT10 assignment, positive query mass weighting, unchanged raw prior."""
from shared import *
threads();resources();check(O/'reviews/prebuild_freeze.json');started=time.monotonic();records=[]
for ds in DS:
    begin=time.monotonic();c=read(O/'inputs'/ds/'config.json');d=c['dim'];h=c['hub_count']
    P=np.fromfile(c['P'],np.float32).reshape(h,d);q=normalize(np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d))
    gt=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100);hn=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d))
    base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1);sup=dict(np.load(O/'inputs'/ds/'mass_supervision.npz'))
    A=np.zeros((20000,h),np.float64)
    for rank in range(10):
        tn=normalize(np.asarray(base[gt[:,rank],1:],np.float32))
        for start in range(0,20000,4096):
            stop=min(start+4096,20000);s=tn[start:stop]@hn.T
            if c['temperature'] is None:
                a=np.zeros(s.shape,np.float64);a[np.arange(stop-start),np.argmax(s,axis=1)]=1
            else:
                a=s.astype(np.float64);a-=a.max(1,keepdims=True);a/=c['temperature'];np.exp(a,out=a);a/=a.sum(1,keepdims=True)
            A[start:stop]+=a/10
    assert digest(A)==c['original_assignments_sha']
    S=hn.astype(float)+A.T@q.astype(float);recovered=(S/np.linalg.norm(S,axis=1,keepdims=True)).astype(np.float32)
    assert recovered.tobytes()==P.tobytes()
    assignment_seconds=time.monotonic()-begin;models=[]
    for name,w in zip(LABELS,[np.ones(20000),sup['weights'],sup['sham_weights']]):
        tick=time.monotonic();B=A*w[:,None];mass=B.sum(1)
        assert np.max(np.abs(mass-w))<2e-12 and abs(mass.sum()-20000)<1e-8 and np.all(B>=0)
        if name=='baseline':W=P.copy()
        else:
            S=hn.astype(float)+B.T@q.astype(float);W=(S/np.linalg.norm(S,axis=1,keepdims=True)).astype(np.float32)
        folder=O/'models'/ds/name;folder.mkdir(parents=True);W.tofile(folder/'W.f32')
        hm=B.sum(0);sq=np.square(B).sum(0);ess=np.divide(hm*hm,sq,out=np.zeros_like(hm),where=sq>0)
        save(folder/'support.npz',query_mass=mass,hub_mass=hm,ess=ess,profile_displacement=np.linalg.norm(W.astype(float)-P,axis=1))
        sample=np.arange(0,20000,137,dtype=np.int32);save(folder/'assignment_sample.npz',rows=sample,weights=B[sample])
        meta=dict(model=name,W=identity(folder/'W.f32'),assignment_sha=digest(B),query_count=20000,total_query_mass=float(mass.sum()),
          max_mass_error=float(np.max(np.abs(mass-w))),raw_prior_weight=1,changed_profiles=int((W!=P).any(1).sum()),
          mean_profile_displacement=float(np.linalg.norm(W.astype(float)-P,axis=1).mean()),aggregate_seconds=time.monotonic()-tick,
          initial_P_byte_recovery=True,weight_ratio=1 if name=='baseline' else 2)
        dump(folder/'manifest.json',meta);models.append(meta)
    records.append(dict(dataset=ds,models=models,shared_assignment_and_recovery_seconds=assignment_seconds,total_seconds=time.monotonic()-begin))
    print('PROFILES_COMPLETE',ds,time.monotonic()-begin,flush=True)
dump(O/'results/build.json',dict(status='PASS_ORIGINAL_A0_AND_P_BYTE_RECOVERY',datasets=records,seconds=time.monotonic()-started,new_NSG=0,new_GT=0,gradient_updates=0))
paths=[p for root in ['src','models','inputs'] for p in (O/root).rglob('*') if p.is_file()]+[O/'protocol.md',O/'config.locked.json',O/'bin/environment.so',O/'reviews/prebuild_freeze.json']
dump(O/'reviews/models_before_queries.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(paths)]))
dump(O/'state.json',dict(status='SIX_PROFILES_FROZEN_BEFORE_DEVELOPMENT',models_built=6,next_command='src/verify_profiles.py',new_NSG=0))
