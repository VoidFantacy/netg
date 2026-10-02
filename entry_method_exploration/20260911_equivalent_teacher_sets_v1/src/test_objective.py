from common import *
import itertools
import numpy as np
import torch
from train import set_loss,triple_scores

rng=np.random.default_rng(SEED)
cases=0
for h in [4,5,6]:
    ts=np.array(list(itertools.combinations(range(h),3)))
    for k in [1,2,len(ts)]:
        for trial in range(10):
            z=rng.normal(size=h);good=np.zeros(len(ts),bool);good[rng.choice(len(ts),k,replace=False)]=True
            scores=np.array([sum(z[j] for j in t) for t in ts])
            ref=max(scores[j]+(.1 if not good[j] else 0) for j in range(len(ts)))-max(scores[good])
            zz=torch.tensor(z[None,:],requires_grad=True)
            ss=triple_scores(zz,torch.tensor(ts[None,:,:]))
            loss=set_loss(ss,torch.tensor(good[None,:]))
            assert abs(loss.item()-ref)<1e-12 and ref>=-1e-12
            assert ref+1e-12>=.1*(not good[np.argmax(scores)])
            if k==len(ts):assert abs(ref)<1e-12
            shifted=set_loss(ss+50,torch.tensor(good[None,:]))
            assert abs(shifted.item()-ref)<1e-12
            loss.backward();g=zz.grad.numpy()[0];num=[]
            for j in range(h):
                vals=[]
                for sign in [-1,1]:
                    v=z.copy();v[j]+=sign*1e-6;s=np.array([sum(v[a] for a in t) for t in ts])
                    vals.append(max(s+.1*(~good))-max(s[good]))
                num.append((vals[1]-vals[0])/2e-6)
            assert np.allclose(g,num,atol=2e-8,rtol=2e-8),(h,k,g,num)
            cases+=1
# Ties: deterministic finite subgradient and zero loss when all alternatives accepted.
for good in [[True,False,True],[True,True,True]]:
    s=torch.zeros((1,3),requires_grad=True);l=set_loss(s,torch.tensor([good]));l.backward()
    assert torch.isfinite(s.grad).all()
# Singleton exactly agrees with direct known-domain structured hinge.
s=torch.tensor([[1.,1.05,0.]])
assert abs(set_loss(s,torch.tensor([[True,False,False]])).item()-.15)<1e-12
assert abs(set_loss(s,torch.tensor([[True,True,False]])).item())<1e-12
# Check the accumulated exported-W gradient through the shared normalized transform.
h,d,n=5,4,3
p=rng.normal(size=(h,d));p/=np.linalg.norm(p,axis=1,keepdims=True)
q=rng.normal(size=(n,d));q/=np.linalg.norm(q,axis=1,keepdims=True)
ts=np.tile(np.array(list(itertools.combinations(range(h),3)))[None,:,:],(n,1,1))
a=rng.normal(size=(d,d))*.003;direction=rng.normal(size=(d,d));direction/=np.linalg.norm(direction)
good=np.zeros((n,ts.shape[1]),bool);good[:,[0,2,5]]=True
aa=torch.tensor(a,requires_grad=True);pp=torch.tensor(p);qq=torch.tensor(q)
exported=torch.nn.functional.normalize(pp+pp@aa.T,dim=1)
w=exported.detach().requires_grad_(True)
for row in range(n):
    value=set_loss(triple_scores(qq[row:row+1]@w.T/.05,torch.tensor(ts[row:row+1])),torch.tensor(good[row:row+1])).sum()/n
    value.backward()
(100*(w-pp).square().sum(1).mean()).backward();exported.backward(w.grad)
def reference(mat):
    w=p+p@mat.T;w/=np.linalg.norm(w,axis=1,keepdims=True)
    z=q@w.T/.05;cost=0.
    for i in range(n):
        scores=np.array([sum(z[i,j] for j in triple) for triple in ts[i]])
        cost+=(max(scores+.1*(~good[i]))-max(scores[good[i]]))/n
    return cost+100*np.square(w-p).sum(1).mean()
num=(reference(a+1e-6*direction)-reference(a-1e-6*direction))/2e-6
actual=float((aa.grad*torch.tensor(direction)).sum())
assert abs(num-actual)<1e-6,(num,actual)
dump(O/'reviews/objective_tests.json',dict(status='PASS',enumerated_gradient_cases=cases,
    checks=['independent enumeration','finite difference','known-domain error bound','nonnegativity','shift invariance','all accepted','ties','singleton and equivalent alternatives','shared transform accumulated gradient'],NSG_calls=0))
print('OBJECTIVE_TESTS_PASS',cases,flush=True)
