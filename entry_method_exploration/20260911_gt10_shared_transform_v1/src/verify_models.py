from setup import *
import numpy as np,torch
torch.set_num_threads(1)
records=[]
for ds in DS:
 c=json.loads((O/'inputs'/ds/'fit/config.json').read_text());n=c['num_queries'];h=c['hub_count'];d=c['dim']
 p=np.fromfile(E24/'models'/ds/'gt10_hard/W.f32',np.float32).reshape(h,d).astype(np.float64)
 q=np.fromfile(c['queries_file'],np.float32).reshape(n,d).astype(np.float64);q/=np.linalg.norm(q,axis=1,keepdims=True)
 targets=np.fromfile(O/'labels'/ds/'teacher.i32',np.int32).reshape(n,3)
 ts=np.fromfile(O/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3);slots=np.fromfile(O/'labels'/ds/'teacher_slot.i32',np.int32)
 hits=np.fromfile(O/'labels'/ds/'hits.u8',np.uint8).reshape(n,56);ndc=np.fromfile(O/'labels'/ds/'graph_ndc.u32',np.uint32).reshape(n,56)
 assert np.array_equal(ts[np.arange(n),slots],targets);assert np.array_equal(hits.max(1),hits[np.arange(n),slots])
 top=hits==hits.max(1,keepdims=True);mincost=np.where(top,ndc,np.iinfo(np.uint32).max).min(1);assert np.array_equal(mincost,ndc[np.arange(n),slots])
 base_choices=np.argsort(-(q@p.T),axis=1,kind='stable')[:,:3]
 base_overlap=float((base_choices[:,:,None]==targets[:,None,:]).any(2).sum(1).mean()/3)
 for f in ['linear','mlp','free']:
  for lam in [10,100]:
   dest=O/'models'/ds/f'{f}_r{lam}';state=torch.load(dest/'model.pt',map_location='cpu',weights_only=True);params={k:v.numpy() for k,v in state.items()}
   assert np.array_equal(params['p'],p)
   if f=='linear':residual=p@params['fn.weight'].T
   elif f=='mlp':residual=np.maximum(p@params['fn.0.weight'].T+params['fn.0.bias'],0)@params['fn.2.weight'].T
   else:residual=params['delta']
   w=p+residual;w/=np.linalg.norm(w,axis=1,keepdims=True);stored=np.fromfile(dest/'W.f32',np.float32).reshape(h,d)
   error=float(np.max(np.abs(w-stored.astype(np.float64))));assert error<6e-8;assert np.max(np.abs(np.linalg.norm(stored,axis=1)-1))<2e-7
   ce=0;overlap=0;match=0;outside=0;candidates=np.fromfile(O/'inputs'/ds/'proposals/candidates.i32',np.int32).reshape(n,8)
   for begin in range(0,n,512):
    end=min(begin+512,n);z=q[begin:end]@w.T/.05;scale=z.max(1,keepdims=True);a=np.exp(z-scale)
    e1=np.cumsum(a,axis=1);e2=np.cumsum(a[:,1:]*e1[:,:-1],axis=1);e3=(a[:,2:]*e2[:,:-1]).sum(1)
    ref=np.log(e3)+3*scale[:,0]-np.take_along_axis(z,targets[begin:end],1).sum(1);ce+=ref.sum()/n
    chosen=np.argsort(-z,axis=1,kind='stable')[:,:3];ov=(chosen[:,:,None]==targets[begin:end,None,:]).any(2).sum(1);overlap+=ov.sum();match+=(ov==3).sum();outside+=(~(chosen[:,:,None]==candidates[begin:end,None,:]).any(2).all(1)).sum()
   report=json.loads((dest/'model.json').read_text());assert abs(ce-report['last']['ce'])<1e-9
   records.append(dict(dataset=ds,family=f,lambda_anchor=lam,status='PASS',max_export_error=error,independent_CE=float(ce),teacher_entry_overlap=float(overlap/(3*n)),teacher_exact_set_match=float(match/n),baseline_exact_teacher_overlap=base_overlap,predicted_set_outside_C8=float(outside/n)))
dump(O/'reviews/model_verification.json',dict(status='PASS',teacher_max_hits_min_ndc=True,models=records));print(json.dumps(records))
