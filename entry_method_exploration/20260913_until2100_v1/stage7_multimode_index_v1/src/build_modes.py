from common import *
from assignment import recover
threads();resources();check(O/'reviews/prebuild_freeze.json');records=[]
for ds in DS:
    start=time.monotonic();c=read(O/'inputs'/ds/'construction.json');h=c['hub_count'];d=c['dim']
    A,Q,R,P=recover(c);mass=A.sum(0);ess=mass**2/np.square(A).sum(0)
    active=np.flatnonzero((mass>=8)&(ess>=16));B=A[:,active];total=B.T@Q
    seed0=np.argmax(B*(1+Q@P[active].astype(float).T),axis=0);cent0=Q[seed0].copy()
    seed1=np.argmax(B*(1-Q@cent0.T),axis=0);cent1=Q[seed1].copy()
    invalid=np.zeros(len(active),bool);trajectory=[];previous=None
    for it in range(20):
        # Ties choose mode 0, full dense weights retained.
        mask=(Q@cent0.T>=Q@cent1.T);B0=B*mask;S0=B0.T@Q;S1=total-S0
        norm0=np.linalg.norm(S0,axis=1);norm1=np.linalg.norm(S1,axis=1)
        bad=(norm0<=1e-12)|(norm1<=1e-12)|(B0.sum(0)<=0)|(B0.sum(0)>=B.sum(0))
        invalid|=bad;ok=~bad;cent0[ok]=S0[ok]/norm0[ok,None];cent1[ok]=S1[ok]/norm1[ok,None]
        trajectory.append(dict(iteration=it+1,changed_assignments=None if previous is None else int(np.count_nonzero(mask!=previous)),bad_hubs=int(bad.sum())))
        previous=mask.copy();assert time.monotonic()-start<900
        print(ds,'LLOYD',it+1,'seconds',round(time.monotonic()-start,3),flush=True)
    m0=B0.sum(0);m1=mass[active]-m0
    e0=np.divide(m0*m0,np.square(B0).sum(0),out=np.zeros_like(m0),where=m0>0)
    B1=B*(~mask);e1=np.divide(m1*m1,np.square(B1).sum(0),out=np.zeros_like(m1),where=m1>0)
    eligible=(~invalid)&(m0>=2)&(m1>=2)&(e0>=8)&(e1>=8)
    rho=m0/mass[active];U0=rho[:,None]*R[active]+S0;U1=(1-rho[:,None])*R[active]+S1
    assert np.max(np.abs(U0+U1-(R[active]+total)))<2e-12
    modes=np.repeat(P[:,None,:],3,axis=1);ii=active[eligible]
    modes[ii,1]=normalize(U0[eligible]).astype(np.float32);modes[ii,2]=normalize(U1[eligible]).astype(np.float32)
    ids=np.fromfile(c['hub_ids'],np.int32);folder=O/'models'/ds;folder.mkdir()
    for label,W in [('duplicate3P',np.repeat(P,3,axis=0)),('mode3P',modes.reshape(3*h,d))]:
        f=folder/label;f.mkdir();W.tofile(f/'W.f32');np.repeat(ids,3).tofile(f/'mapping.i32');np.arange(3*h,dtype=np.int32).tofile(f/'tie_ids.i32')
        assert W[::3].tobytes()==P.tobytes()
        dump(f/'manifest.json',dict(model=label,physical_profiles=3*h,unique_hubs=h,W=identity(f/'W.f32'),mapping=identity(f/'mapping.i32'),
            original_primary_bytes=True,training_namespace=c['namespace'],training_source_rows=[10000,30000],online_bias=False,raw_prior_total_across_new_modes=1))
    save(folder/'training.npz',active=active,parent_mass=mass,parent_ESS=ess,seed0=seed0,seed1=seed1,assignment_bits=np.packbits(mask,axis=0),
        child_mass=np.stack([m0,m1],1),child_ESS=np.stack([e0,e1],1),sum0=S0,sum1=S1,invalid=invalid,eligible=eligible,rho=rho)
    rec=dict(dataset=ds,assignment_sha=digest(A),original_P_byte_recovery=True,active_parents=len(active),eligible_two_modes=int(eligible.sum()),
        fallback_hubs=h-int(eligible.sum()),total_hubs=h,physical_profiles=3*h,seconds=time.monotonic()-start,iterations=trajectory,
        new_GT=0,new_NSG=0,threads=1,cpu=8,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    dump(folder/'build.json',rec);records.append(rec);resources();print('BUILD_COMPLETE',ds,rec['eligible_two_modes'],rec['seconds'],flush=True)
dump(O/'results/build.json',dict(status='PASS_ORIGINAL_RECOVERY_AND_CONSTRUCTION',datasets=records,new_GT=0,new_NSG=0,gradient_updates=0))
dump(O/'reviews/models_before_queries.json',dict(epoch=time.time(),files=[identity(p) for p in sorted((O/'models').rglob('*')) if p.is_file()]))
dump(O/'state.json',dict(status='MODELS_BUILT_UNQUERIED',new_NSG=0,day_goal_complete=False))
