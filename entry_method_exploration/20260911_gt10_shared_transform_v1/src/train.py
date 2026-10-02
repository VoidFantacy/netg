from setup import *
import numpy as np, torch, sys
from torch import nn
torch.set_num_threads(8);torch.set_num_interop_threads(1)
torch.set_default_dtype(torch.float64)
def logz3(z):
 e1=torch.logcumsumexp(z,dim=1)
 e2=torch.logcumsumexp(z[:,1:]+e1[:,:-1],dim=1)
 return torch.logsumexp(z[:,2:]+e2[:,:-1],dim=1)
class Transform(nn.Module):
 def __init__(self,p,family):
  super().__init__();self.register_buffer('p',p.clone());h,d=p.shape;self.family=family
  if family=='linear':self.fn=nn.Linear(d,d,bias=False);nn.init.zeros_(self.fn.weight)
  elif family=='mlp':
   self.fn=nn.Sequential(nn.Linear(d,64),nn.ReLU(),nn.Linear(64,d,bias=False));nn.init.zeros_(self.fn[-1].weight)
  elif family=='free':self.delta=nn.Parameter(torch.zeros_like(p))
  else:raise ValueError(family)
 def forward(self):return nn.functional.normalize(self.p+(self.delta if self.family=='free' else self.fn(self.p)),dim=1)
def teacher(ds):
 dest=O/'labels'/ds;assert json.loads((dest/'complete.json').read_text())['status']=='COMPLETE'
 c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());n=c['num_queries'];h=c['hub_count'];d=c['dim']
 ts=np.fromfile(O/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3)
 hits=np.fromfile(dest/'hits.u8',np.uint8).reshape(n,56);ndc=np.fromfile(dest/'graph_ndc.u32',np.uint32).reshape(n,56)
 q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(np.float64);p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(np.float64)
 scores=q@p.T;triple_scores=np.take_along_axis(scores[:,None,:],ts,axis=2).sum(2)
 chosen=np.lexsort((-triple_scores,ndc,-hits.astype(np.int16)),axis=1)[:,0];targets=ts[np.arange(n),chosen]
 targets.astype(np.int32).tofile(dest/'teacher.i32');chosen.astype(np.int32).tofile(dest/'teacher_slot.i32')
 bs=np.fromfile(O/'inputs'/ds/'proposals/baseline_triples.i32',np.int32).reshape(n,2,3)
 baseline=[]
 for b in range(2):
  matches=(ts==bs[:,b,None,:]).all(2);assert (matches.sum(1)==1).all();slots=matches.argmax(1);baseline.append(dict(hits=float(hits[np.arange(n),slots].mean()),ndc=float(ndc[np.arange(n),slots].mean())))
 info=dict(status='PASS',teacher_hits=float(hits[np.arange(n),chosen].mean()),teacher_ndc=float(ndc[np.arange(n),chosen].mean()),baseline_gt1_gt10=baseline,improved_hits_fraction=float((hits[np.arange(n),chosen]>hits[np.arange(n),(ts==bs[:,1,None,:]).all(2).argmax(1)]).mean()),teacher_identity=identity(dest/'teacher.i32'))
 dump(dest/'teacher.json',info);print(ds,info,flush=True)
 return q,p,targets
def fit(ds,family,lam,q,p,target):
 dest=O/'models'/ds/f'{family}_r{lam}';assert not dest.exists();dest.mkdir(parents=True);torch.manual_seed(20260911)
 p=torch.from_numpy(p);q=torch.from_numpy(q);q=nn.functional.normalize(q,dim=1);target=torch.from_numpy(target.astype(np.int64));model=Transform(p,family);optimizer=torch.optim.Adam(model.parameters(),lr=.003)
 start=time.time();log=[];n=len(q)
 def loss_grad():
  exported=model();w=exported.detach().requires_grad_(True);ce_sum=0.
  for begin in range(0,n,1024):
   end=min(n,begin+1024);z=q[begin:end]@w.T/.05;ce=(logz3(z)-z.gather(1,target[begin:end]).sum(1)).sum()/n
   assert torch.isfinite(ce);ce.backward();ce_sum+=ce.item()
  drift=(w-p).square().sum(1).mean();(lam*drift).backward();exported.backward(w.grad)
  gn=sum(v.grad.square().sum().item() for v in model.parameters())**.5
  return dict(ce=ce_sum,drift=drift.item(),objective=ce_sum+lam*drift.item(),gradient_norm=gn)
 for epoch in range(81):
  optimizer.zero_grad();rec=loss_grad();rec.update(epoch=epoch,seconds=time.time()-start);log.append(rec)
  if epoch%10==0:print(ds,family,lam,rec,flush=True);dump(dest/'progress.json',rec);dump(dest/'training_curve.json',log)
  if epoch<80:optimizer.step()
 assert log[-1]['objective']<log[0]['objective'],'no optimization improvement'
 wall=time.time()-start;t=time.time();w=model().detach().numpy().astype(np.float32);w.tofile(dest/'W.f32');export_seconds=time.time()-t
 torch.save(model.state_dict(),dest/'model.pt')
 cos=(w.astype(np.float64)*p.numpy()).sum(1);report=dict(status='TRAINED_FIT_ONLY',dataset=ds,family=family,lambda_anchor=lam,seed=20260911,epochs=80,parameter_count=sum(v.numel() for v in model.parameters()),training_seconds=wall,export_seconds=export_seconds,first=log[0],last=log[-1],cosine_to_anchor=dict(min=float(cos.min()),mean=float(cos.mean()),median=float(np.median(cos))),W=identity(dest/'W.f32'),cal_used=False,audit_used=False,validation_used=False)
 dump(dest/'model.json',report);return report
if __name__=='__main__':
 assert all(x['status']=='PASS' for x in json.loads((O/'reviews/label_verification.json').read_text()))
 dump(O/'reviews/frozen_before_training.json',dict(timestamp=time.time(),protocol=identity(O/'protocol.md'),sources=[identity(O/'src'/s) for s in ['train.py','test_objective.py','verify_labels.py']],labels=[identity(O/'labels'/ds/n) for ds in DS for n in ['ids.i32','hits.u8','masks.u16','graph_ndc.u32','complete.json']]))
 records=[]
 for ds in DS:
  q,p,t=teacher(ds)
  for family in ['linear','mlp','free']:
   for lam in [10,100]:records.append(fit(ds,family,lam,q,p,t));dump(O/'models/training_runs.json',records)
 dump(O/'models/frozen_before_cal.json',dict(timestamp=time.time(),runs=records,protocol=identity(O/'protocol.md'),cal_used=False,audit_used=False,validation_used=False))
