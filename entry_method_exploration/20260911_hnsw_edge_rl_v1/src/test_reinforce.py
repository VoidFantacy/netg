from common import *
import itertools,heapq
import torch
torch.set_num_threads(1)

def toy(mask):
 # Delayed success and cost with state-dependent edge exposure; unexposed edges have no log-probability term.
 adj=[[(1,0),(2,1)],[(3,2)],[(3,3)],[]];seen={0};todo=[0];used=[];cost=1
 while todo:
  u=heapq.heappop(todo)
  for v,e in adj[u]:
   if v in seen:continue
   used.append(e)
   if mask[e]:seen.add(v);heapq.heappush(todo,v);cost+=1
 return float(3 in seen)-.07*cost,used

def expected(theta):
 p=1/(1+np.exp(-theta));value=0
 for mask in itertools.product([0,1],repeat=4):
  a=np.array(mask);pr=np.prod(np.where(a,p,1-p));value+=pr*toy(mask)[0]
 return value

theta=np.array([-.7,.3,1.,-.2]);p=1/(1+np.exp(-theta));g=np.zeros(4);gb=np.zeros(4);full=np.zeros(4)
for mask in itertools.product([0,1],repeat=4):
 a=np.array(mask);pr=np.prod(np.where(a,p,1-p));r,used=toy(mask)
 g[used]+=pr*r*(a-p)[used];gb[used]+=pr*(r-.91)*(a-p)[used];full+=pr*r*(a-p)
fd=np.zeros(4)
for e in range(4):
 d=np.eye(4)[e]*1e-5;fd[e]=(expected(theta+d)-expected(theta-d))/(2e-5)
assert np.max(np.abs(g-fd))<1e-10 and np.max(np.abs(g-gb))<1e-12 and np.max(np.abs(g-full))<1e-12
# Independently verify the training gradient, including repeated edge visits across different episodes and entropy.
ids=np.array([0,2,0,1,3,2,3]);actions=np.array([1,0,0,1,1,1,0]);adv=np.array([.2,.2,-.4,-.4,-.4,.8,.8]);b=3
t=torch.tensor(theta,requires_grad=True);idx=torch.tensor(ids);a=torch.tensor(actions,dtype=torch.float64);z=t[idx]
lp=a*torch.nn.functional.logsigmoid(z)+(1-a)*torch.nn.functional.logsigmoid(-z)
probs=z.sigmoid();ent=-(probs*torch.nn.functional.logsigmoid(z)+(1-probs)*torch.nn.functional.logsigmoid(-z))
loss=-(torch.tensor(adv)*lp).sum()/b-.001*ent.sum()/b;loss.backward()
ng=np.bincount(ids,weights=(p[ids]-actions)*adv+.001*theta[ids]*p[ids]*(1-p[ids]),minlength=4)/b
assert np.max(np.abs(ng-t.grad.numpy()))<1e-14
dump(O/'reviews/reinforce_tests.json',dict(status='PASS',enumerated_graphs=16,state_dependent_exposure=True,unexposed_actions_integrated_out=True,baseline_invariance=True,finite_difference_max_error=float(np.max(np.abs(g-fd))),training_gradient_max_error=float(np.max(np.abs(ng-t.grad.numpy())))))
print('REINFORCE_TESTS_PASS',flush=True)
