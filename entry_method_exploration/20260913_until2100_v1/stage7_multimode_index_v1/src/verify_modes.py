from common import *
from assignment import recover
threads();resources();check(O/'reviews/models_before_queries.json');records=[]
for ds in DS:
    begin=time.monotonic();c=read(O/'inputs'/ds/'construction.json');A,Q,R,P=recover(c);h,d=P.shape
    folder=O/'models'/ds;t=dict(np.load(folder/'training.npz'));active=t['active'];mask=np.unpackbits(t['assignment_bits'],axis=0,count=20000).astype(bool)
    modes=np.fromfile(folder/'mode3P/W.f32',np.float32).reshape(h,3,d);duplicate=np.fromfile(folder/'duplicate3P/W.f32',np.float32).reshape(h,3,d)
    assert duplicate.tobytes()==np.repeat(P[:,None,:],3,axis=1).tobytes() and modes[:,0].tobytes()==P.tobytes()
    eligible=[];maxerr=0.;replays=[]
    for col,hub in enumerate(active):
        w=A[:,hub];parts=[w*mask[:,col],w*(~mask[:,col])];mass=np.array([x.sum() for x in parts]);ess=np.array([x.sum()**2/np.dot(x,x) if x.sum()>0 else 0 for x in parts])
        sums=np.array([np.einsum('i,ij->j',x,Q,optimize=False) for x in parts])
        assert np.allclose(mass,t['child_mass'][col],atol=1e-9,rtol=1e-12) and np.allclose(ess,t['child_ESS'][col],atol=1e-8,rtol=1e-10)
        maxerr=max(maxerr,float(np.max(np.abs(sums-np.stack([t['sum0'][col],t['sum1'][col]])))))
        good=(not t['invalid'][col]) and min(mass)>=2 and min(ess)>=8;assert good==t['eligible'][col]
        if good:
            expected=normalize(sums+mass[:,None]/mass.sum()*R[hub]).astype(np.float32)
            assert np.allclose(expected,modes[hub,1:],atol=3e-8,rtol=0);eligible.append(int(hub))
        else:assert modes[hub,1:].tobytes()==np.stack([P[hub],P[hub]]).tobytes()
    assert maxerr<2e-9
    # Independent scalar-hub replay of seven predetermined evenly spaced parents.
    for col in np.unique(np.linspace(0,len(active)-1,7,dtype=int)):
        hub=active[col];w=A[:,hub];s0=int(np.argmax(w*(1+Q@P[hub].astype(float))));s1=int(np.argmax(w*(1-Q@Q[s0])))
        assert [s0,s1]==[int(t['seed0'][col]),int(t['seed1'][col])]
        centers=np.array([Q[s0],Q[s1]]);invalid=False
        for it in range(20):
            select=Q@centers[0]>=Q@centers[1];ww=[w*select,w*(~select)];sums=np.array([np.einsum('i,ij->j',x,Q) for x in ww]);norms=np.linalg.norm(sums,axis=1)
            bad=min(norms)<=1e-12 or min(x.sum() for x in ww)<=0;invalid|=bad
            if not bad:centers=sums/norms[:,None]
        assert np.array_equal(select,mask[:,col]) and invalid==t['invalid'][col];replays.append(int(hub))
    inactive=np.setdiff1d(np.arange(h),active);assert modes[inactive].tobytes()==duplicate[inactive].tobytes()
    records.append(dict(dataset=ds,status='PASS',eligible_hubs=len(eligible),all_child_sums_checked=len(active),max_sum_error=maxerr,independent_Lloyd_replays=replays,seconds=time.monotonic()-begin))
dump(O/'reviews/profile_verification.json',dict(status='PASS',datasets=records,new_NSG=0,new_HNSW=0));print('VERIFY_MODES_PASS',records,flush=True)
