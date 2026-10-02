"""Query-balanced projective spherical k-means on actual comparison differences."""
from common import *

def canonical(x):
    x=np.asarray(x,dtype=np.float64).copy()
    x/=np.linalg.norm(x,axis=1,keepdims=True)
    signs=np.sign(x[np.arange(len(x)),np.abs(x).argmax(axis=1)])
    return x*signs[:,None]

def projective_kmeans(x,weights,m,seed,iters):
    rng=np.random.default_rng(seed);x=canonical(x);weights=weights/weights.sum()
    centers=[x[rng.choice(len(x),p=weights)]];distance=1-np.abs(x@centers[0])
    for k in range(1,m):
        mass=weights*np.maximum(distance,0)
        ix=int(rng.choice(len(x),p=mass/mass.sum())) if mass.sum()>0 else k%len(x)
        centers.append(x[ix]);distance=np.minimum(distance,1-np.abs(x@centers[-1]))
    centers=np.stack(centers);history=[]
    for iteration in range(iters):
        scores=x@centers.T;assign=np.abs(scores).argmax(axis=1);similarity=np.abs(scores[np.arange(len(x)),assign])
        new=np.zeros_like(centers);empty=[]
        for k in range(m):
            take=assign==k
            if take.any():
                signs=np.where(scores[take,k]>=0,1.,-1.)
                new[k]=(x[take]*(weights[take]*signs)[:,None]).sum(axis=0)
            if np.linalg.norm(new[k])<1e-14:empty.append(k)
        # Distinct deterministic farthest samples repair empty clusters.
        farthest=np.lexsort((np.arange(len(x)),similarity))
        for j,k in enumerate(empty):new[k]=x[farthest[j]]
        centers=canonical(new)
        history.append(dict(iteration=iteration,weighted_chord_objective=float((weights*(1-similarity)).sum()),empty_repaired=empty))
    return centers,history

def cluster(ds):
    start=time.time();c=LOCK['datasets'][ds];d=c['dimension'];p=RUN/'results'/ds/'directions';done=read(p/'complete.json')
    assert done['status']=='PASS' and done['trace_bit_parity']
    n,mx=done['n'],done['samples'];sizes=np.fromfile(p/'sample_sizes.u32',np.uint32)
    x=np.fromfile(p/'sample_directions.f32',np.float32).reshape(n,mx,d)
    valid=np.arange(mx)[None,:]<sizes[:,None];owner=np.broadcast_to(np.arange(n)[:,None],(n,mx))[valid]
    x=x[valid].astype(np.float64);weights=1/sizes[owner].astype(np.float64)
    assert np.max(np.abs(np.linalg.norm(x,axis=1)-1))<2e-7
    assert np.max(np.abs(np.bincount(owner,weights=weights)-1))<1e-12
    D,history=projective_kmeans(x,weights,LOCK['dictionary_size'],LOCK['seed'],LOCK['clustering_iterations'])
    pmodel=RUN/'models'/ds;pmodel.mkdir(exist_ok=True,parents=True)
    assert not(pmodel/'graph_directions.f32').exists()
    D.astype(np.float32).tofile(pmodel/'graph_directions.f32')
    random=canonical(np.random.default_rng(LOCK['seed']).normal(size=D.shape)).astype(np.float32)
    random.tofile(pmodel/'random_directions.f32')
    s=x@D.T;assignment=np.abs(s).argmax(axis=1);best=np.abs(s[np.arange(len(x)),assignment])
    support=[int(np.unique(owner[assignment==k]).size) for k in range(len(D))]
    q=np.fromfile(RUN/'inputs'/ds/'directions/queries.f32',np.float32).reshape(n,d).astype(np.float64)
    q/=np.linalg.norm(q,axis=1,keepdims=True)
    original=(x*q[owner]).sum(axis=1);approx=(D[assignment]*q[owner]).sum(axis=1)*np.where(s[np.arange(len(x)),assignment]>=0,1.,-1.)
    result=dict(status='PASS',dataset=ds,queries=n,samples=len(x),query_balanced=True,iterations=history,
                angular_cosine_quantiles=np.quantile(best,[0,.1,.5,.9,1]).tolist(),cluster_query_support=support,
                weighted_comparison_sign_agreement=float(np.average((original>=0)==(approx>=0),weights=weights)),
                comparison_margin_quantiles=np.quantile(np.abs(original),[0,.1,.5,.9,1]).tolist(),
                seconds=time.time()-start,files=[ident(pmodel/'graph_directions.f32'),ident(pmodel/'random_directions.f32')],
                scope='diagnostic only; no support/angle threshold rejects this method')
    dump(RUN/'reviews'/f'clustering_{ds}.json',result)
    return result

def feature_specs(ds):
    p=RUN/'models'/ds;m=LOCK['dictionary_size']
    return [dict(name='graph',kind='relu',m=m,directions=str(p/'graph_directions.f32')),
            dict(name='random',kind='relu',m=m,directions=str(p/'random_directions.f32')),
            dict(name='linear',kind='linear',m=m,directions=str(p/'graph_directions.f32')),
            dict(name='raw',kind='raw')]

def audit_features(ds,role):
    c=LOCK['datasets'][ds];q=np.fromfile(RUN/'inputs'/ds/role/'queries.f32',np.float32).reshape(-1,c['dimension']).astype(np.float64)
    q/=np.linalg.norm(q,axis=1,keepdims=True);records=[]
    for spec in feature_specs(ds):
        if spec['kind']=='raw':ref=q
        else:
            D=np.fromfile(spec['directions'],np.float32).reshape(-1,c['dimension']).astype(np.float64);v=q@D.T
            ref=v if spec['kind']=='linear' else np.concatenate([np.maximum(v,0),np.maximum(-v,0)],axis=1)
        actual=np.fromfile(RUN/'results'/ds/f'{role}_features'/f"{spec['name']}.features.f32",np.float32).reshape(ref.shape)
        error=float(np.max(np.abs(actual-ref)));assert error<2e-6,(ds,role,spec['name'],error)
        records.append(dict(name=spec['name'],max_abs_error=error,shape=list(actual.shape)))
    dump(RUN/'reviews'/f'features_{role}_{ds}.json',dict(status='PASS',records=records))

if __name__=='__main__':
    os.sched_setaffinity(0,{15})
    for ds in LOCK['datasets']:cluster(ds)
