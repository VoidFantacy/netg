from common import *
import torch
torch.set_num_threads(1)
T_NEXT=torch.tensor(NEXT,dtype=torch.long);T_PRIOR=torch.tensor(PRIOR,dtype=torch.float64)
class Network(torch.nn.Module):
 def __init__(self):
  super().__init__();self.net=torch.nn.Sequential(torch.nn.Linear(76,16),torch.nn.ReLU(),torch.nn.Linear(16,16),torch.nn.ReLU(),torch.nn.Linear(16,1));self.double()
  torch.nn.init.zeros_(self.net[4].weight);torch.nn.init.zeros_(self.net[4].bias)
 def forward(self,x):return self.net(x).squeeze(-1)+T_PRIOR
def probabilities(f):return torch.softmax(f[:,T_NEXT],dim=-1)
def expected_terminal(f,value,horizon=3):
 p=probabilities(f);v=value
 for _ in range(horizon):v=p[:,:,0]*value+(p[:,:,1:]*v[:,T_NEXT[:,1:]]).sum(dim=-1)
 return v[:,0]
def greedy(f):
 f=np.asarray(f);n=len(f);state=np.zeros((n,4),np.uint8);action=np.full((n,3),-1,np.int8);alive=np.ones(n,bool);s=np.zeros(n,np.int64);index=np.arange(n)
 for step in range(3):
  best=f[index,s].copy();a=np.zeros(n,np.int64)
  for j in range(1,16):
   candidate=f[index,NEXT[s,j]];take=candidate>best+1e-9;a[take]=j;best[take]=candidate[take]
  action[alive,step]=a[alive];s[alive]=NEXT[s[alive],a[alive]];state[:,step+1]=s;alive &= a!=0
 return state,action
def load_fit(ds):
 p=O/'results'/('labels_'+ds);raw=np.fromfile(p/'features.f32',np.float32).reshape(2048,56,76).astype(np.float64);scored=np.load(p/'scored.npz')
 mean=raw[:1792].mean(axis=(0,1));scale=np.maximum(raw[:1792].std(axis=(0,1)),1e-6);x=np.clip((raw-mean)/scale,-8,8)
 return torch.tensor(x),torch.tensor(scored['utility']),scored['hits'],scored['graph_ndc'],scored['route_ndc'],mean,scale
def export(path,net,mean,scale,**metadata):dump(path,dict(mean=mean.tolist(),scale=scale.tolist(),parameters={k:v.detach().numpy().tolist() for k,v in net.state_dict().items()},**metadata))
def numpy_forward(raw,config):
 x=np.clip((raw-config['mean'])/config['scale'],-8,8);p=config['parameters']
 for layer in [0,2]:x=np.maximum(0,x@np.array(p[f'net.{layer}.weight']).T+np.array(p[f'net.{layer}.bias']))
 return (x@np.array(p['net.4.weight']).T+np.array(p['net.4.bias'])).squeeze(-1)+PRIOR
def update_baseline(b,rows,state,action,returns):
 keys=(rows[:,None]*56+state[:,:3]).reshape(-1);valid=action.reshape(-1)>=0;keys=keys[valid];ret=returns.reshape(-1)[valid];unique,inverse=np.unique(keys,return_inverse=True)
 means=np.bincount(inverse,weights=ret)/np.bincount(inverse);flat=b.reshape(-1);flat[unique]+=.05*(means-flat[unique])
def sample_trajectory(f,utility,rows,baseline,rng):
 n=len(rows);ix=np.arange(n);states=np.zeros((n,4),np.uint8);actions=np.full((n,3),-1,np.int8);s=np.zeros(n,np.int64);alive=np.ones(n,bool);logps=[]
 for step in range(3):
  logits=f[torch.arange(n)[:,None],torch.tensor(NEXT[s])];lp=torch.log_softmax(logits,dim=-1);p=lp.detach().exp().numpy();a=np.minimum(15,(rng.random(n)[:,None]>=np.cumsum(p,axis=-1)).sum(axis=-1))
  logps.append(lp[torch.arange(n),torch.tensor(a)]*torch.tensor(alive));actions[alive,step]=a[alive];s[alive]=NEXT[s[alive],a[alive]];states[:,step+1]=s;alive &= a!=0
 vals=utility[ix[:,None],states];returns=vals[:,-1,None]-vals[:,:3];reward=np.diff(vals,axis=1);valid=actions>=0;returns*=valid
 advantage=(returns-baseline[rows[:,None],states[:,:3]])*valid;logp=torch.stack(logps,dim=1);loss=-(logp*torch.tensor(advantage)).sum()/n
 trace=dict(rows=rows.astype(np.uint16),states=states,actions=actions,rewards=reward,returns=returns,advantages=advantage,log_probabilities=logp.detach().numpy())
 return loss,trace
