"""Algebra and native-forward checks; run serially before real model training."""
from common import *
from train import Ridge,actions,targets
from cluster import canonical,projective_kmeans
from audit import popcount,score
from analyze import bootstrap_delta

def synthetic(ex):
    p=RUN/'reviews/synthetic';p.mkdir(exist_ok=True)
    rng=np.random.default_rng(LOCK['seed']);checks={}
    x=rng.normal(size=(128,7));w=rng.normal(size=(7,5));b=rng.normal(size=5);y=x@w+b
    fit=Ridge(x,y);wc,bc,resid=fit.solve(1e-10);err=np.max(np.abs(x@wc+bc-y));assert err<2e-8
    checks['known_response']=dict(max_abs_error=float(err),normal_residual=resid)
    for a in LOCK['ridge_alphas']:
        wc,bc,resid=fit.solve(a)
        design=np.vstack([fit.z/np.sqrt(len(x)),np.eye(x.shape[1])*np.sqrt(a)])
        response=np.vstack([(y-y.mean(0))/np.sqrt(len(x)),np.zeros_like(w)])
        independent=np.linalg.lstsq(design,response,rcond=None)[0]
        assert np.max(np.abs(wc-independent/fit.scale[:,None]))<1e-10
        assert np.max(np.abs(bc-(y.mean(0)-fit.mean@wc)))<1e-12
    checks['ridge_augmented_lstsq']='PASS'
    hubs=np.array([50,10,30],np.int32)
    scores=np.array([[0,0,0],[-1,-2,-3],[1,1,0],[0,-1,2]],float)
    assert actions(scores,hubs).tolist()==[0,0,2,3]
    checks['ties_and_fallback']='PASS'
    normals=rng.normal(size=(40,6));assert np.array_equal(canonical(normals),canonical(-normals))
    D=np.vstack([np.eye(6),-np.eye(6)]);centers,history=projective_kmeans(D,np.ones(12),6,1,5)
    assert np.min(np.max(np.abs(D@centers.T),axis=1))>1-1e-12
    checks['projective_sign_equivalence']='PASS'
    # Explicit IP branching identity including sign and query normalization.
    q=rng.normal(size=(100,6));a=rng.normal(size=(100,6));bvec=rng.normal(size=(100,6))
    lhs=(q*a).sum(1)-(q*bvec).sum(1);rhs=(q*(a-bvec)).sum(1)
    assert np.max(np.abs(lhs-rhs))<1e-12 and np.array_equal(lhs>0,rhs>0)
    checks['ip_branch_identity']='PASS'
    # Native model tests use exact axis vectors, opposite directions and exact ties.
    queries=np.array([[1,0,0,0],[-1,0,0,0],[0,1,0,0],[0,-1,0,0],[0,0,1,0]],np.float32)
    direction=np.array([[1,0,0,0],[0,1,0,0]],np.float32)
    queries.tofile(p/'queries.f32');direction.tofile(p/'directions.f32');hubs.tofile(p/'hub_ids.i32')
    spec=dict(name='graph',kind='relu',m=2,directions=str(p/'directions.f32'))
    weights=np.array([[1,0,0,0],[1,0,2,0],[0,3,0,0]],np.float32);bias=np.zeros(3,np.float32)
    weights.tofile(p/'weights.f32');bias.tofile(p/'bias.f32')
    model=dict(features=spec,heads={str(k):dict(weights=str(p/'weights.f32'),bias=str(p/'bias.f32')) for k in (1,100)})
    dump(p/'model.json',model)
    cfg=dict(dataset='synthetic',mode='features',threads=1,n=5,dimension=4,queries=str(p/'queries.f32'),features=[spec],seconds_cap=120)
    ex.execute(cfg,p/'features','synthetic_features')
    phi=np.concatenate([np.maximum(queries@direction.T,0),np.maximum(-queries@direction.T,0)],axis=1)
    assert np.array_equal(phi,np.fromfile(p/'features/graph.features.f32',np.float32).reshape(5,4))
    cfg.update(mode='predict',hub_ids=str(p/'hub_ids.i32'),models=[dict(name='synthetic',model=str(p/'model.json'))],save_all_scores=True)
    ex.execute(cfg,p/'predict','synthetic_predict')
    expected=phi@weights.T;chosen=actions(expected,hubs)
    assert chosen.tolist()==[2,2,3,0,0]
    for K in (1,100):
        assert np.array_equal(expected,np.fromfile(p/f'predict/synthetic_K{K}.scores.f32',np.float32).reshape(5,3))
        assert np.array_equal(chosen,np.fromfile(p/f'predict/synthetic_K{K}.actions.i32',np.int32))
    checks['native_features_scores_actions']='PASS'
    mask=np.array([[1|(1<<63),1|(1<<35)],[0,0]],np.uint64)
    assert popcount(mask).tolist()==[[2,2],[0,0]]
    gt=np.tile(np.arange(100,dtype=np.int64),(2,1));ids=np.tile(np.arange(100,dtype=np.int32),(2,1));ids[1]=np.arange(50,150)
    assert score(ids,gt,100).tolist()==[100,50]
    assert score(np.array([[1],[0]],np.int32),gt,1).tolist()==[0,1]
    checks['GT_scoring_and_mask_boundaries']='PASS'
    z=bootstrap_delta(np.array([-1,0,1]),1,'synthetic-symmetric')
    assert z['mean_pp']==0 and z['ci_pp']==[-100.,100.]
    z=bootstrap_delta(np.full(8,2),100,'synthetic-constant')
    assert z['mean_pp']==2 and z['ci_pp']==[2.,2.]
    checks['paired_bootstrap_known_distributions']='PASS'
    dump(RUN/'reviews/synthetic_checks.json',dict(status='PASS',checks=checks))
    return checks
