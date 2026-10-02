from train import *
import itertools

rng=np.random.default_rng(SEED);rows=[]
for trial in range(12):
    n,h,d=4,8,5
    q=rng.normal(size=(n,d));q/=np.linalg.norm(q,axis=1,keepdims=True)
    p=rng.normal(size=(h,d));p/=np.linalg.norm(p,axis=1,keepdims=True)
    ts=np.tile(np.array(list(itertools.combinations(range(h),3)))[None],(n,1,1))
    hits=rng.integers(0,11,(n,56)).astype(float);ndc=rng.integers(30,300,(n,56)).astype(float)
    g=hits==hits.max(1)[:,None]
    data=tuple(torch.from_numpy(x) for x in (q,p,ts,g,hits,ndc))
    model=Transform(data[1]);beta=3.7
    rec=compute(model,data,'reward',beta)
    grad=model.fn.weight.grad.detach().numpy().copy()
    # Independent score-space expectation gradient and finite difference through shared A.
    def numpy_objective(a):
        w=p+p@a.T;w/=np.linalg.norm(w,axis=1,keepdims=True)
        z=q@w.T/.05;s=np.stack([z[:,t].sum(1) for t in ts[0]],axis=1)
        pi=np.exp(s-s.max(1)[:,None]);pi/=pi.sum(1)[:,None]
        regret=(hits.max(1)[:,None]-hits)/10
        return beta*(pi*regret).sum(1).mean()+100*np.square(w-p).sum(1).mean(),pi,s
    a=np.zeros((d,d));val,pi,s=numpy_objective(a)
    assert abs(val-rec['objective'])<1e-12
    maxerr=0.
    for i,j in [(0,0),(0,3),(2,4),(4,1)]:
        ap=a.copy();am=a.copy();ap[i,j]+=1e-6;am[i,j]-=1e-6
        fd=(numpy_objective(ap)[0]-numpy_objective(am)[0])/2e-6
        maxerr=max(maxerr,abs(fd-grad[i,j]));assert abs(fd-grad[i,j])<1e-7
    logits=torch.tensor(s,requires_grad=True);r=torch.tensor(hits/10)
    loss=-(logits.softmax(1)*r).sum(1).mean();loss.backward()
    expected=pi*((pi*(hits/10)).sum(1)[:,None]-hits/10)/n
    assert np.max(np.abs(logits.grad.numpy()-expected))<1e-13
    # Constant action rewards give exactly zero gradient; translation changes no policy.
    x=torch.tensor(s,requires_grad=True);(x.softmax(1)*torch.ones_like(x)).sum().backward()
    assert x.grad.abs().max()<1e-13
    assert np.allclose(torch.tensor(s+5).softmax(1).numpy(),pi,atol=1e-14)
    # Additive triple MAP equals the highest three entry scores for unique scores.
    scores=q@p.T/.05;chosen=np.sort(np.argsort(-scores,axis=1,kind='stable')[:,:3],axis=1)
    assert np.array_equal(ts[np.arange(n),s.argmax(1)],chosen)
    rows.append(dict(trial=trial,max_shared_A_finite_difference_error=maxerr))
dump(O/'reviews/objective_tests.json',dict(status='PASS',trials=rows,finite_differences=48,score_gradient_identity=True,
    constant_reward_zero_gradient=True,score_translation_invariance=True,additive_MAP_identity=True))
print('OBJECTIVE_TESTS_PASS',flush=True)
