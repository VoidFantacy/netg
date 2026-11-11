from common import *
import math
rates=[1,.75,.5,.25,.1,.05,.01]
def predict(model,X):
 kind=model['kind']
 if kind in ['off','on']:return np.full(len(X),kind=='on')
 if kind=='ridge':
  z=(X[:,:model['nf']]-model['mean'])/model['scale'];pg=z@np.array(model['wg'][:-1])+model['wg'][-1];pc=z@np.array(model['wc'][:-1])+model['wc'][-1]
 else:
  pg=[];pc=[]
  for x in X:
   i=0
   while model['nodes'][i]['f']>=0:
    nd=model['nodes'][i];i=nd['left'] if x[nd['f']]<=nd['threshold'] else nd['right']
   pg.append(model['nodes'][i]['gain']);pc.append(model['nodes'][i]['cost'])
  pg=np.array(pg);pc=np.array(pc)
 return np.maximum(pg,0)/np.maximum(pc,1)
def tree(X,y,cost,nf):
 nodes=[];cuts=[np.unique(np.quantile(X[:,j],np.arange(1,17)/17)) for j in range(nf)]
 def add(ind,depth):
  i=len(nodes);nodes.append(dict(f=-1,left=-1,right=-1,threshold=0.,gain=float(y[ind].mean()),cost=float(cost[ind].mean())))
  if depth==3 or len(ind)<64:return i
  yy=y[ind];best=None;base=float(((yy-yy.mean())**2).sum())
  for j in range(nf):
   for t in cuts[j]:
    a=X[ind,j]<=t;na=a.sum();nb=len(a)-na
    if min(na,nb)<32:continue
    err=float((yy[a]**2).sum()-yy[a].sum()**2/na+(yy[~a]**2).sum()-yy[~a].sum()**2/nb)
    if best is None or err<best[0]:best=(err,j,float(t),a)
  if best is not None and best[0]<base-1e-10:
   _,j,t,a=best;l=add(ind[a],depth+1);r=add(ind[~a],depth+1);nodes[i].update(f=j,left=l,right=r,threshold=t)
  return i
 add(np.arange(len(X)),0);return dict(kind='tree',nf=nf,nodes=nodes)
def main(ds):
 cfg=read(R/f'configs/{ds}.dev.json');g=np.asarray(gt(cfg['test_gt']));root=Path(cfg['output_dir']);records=[]
 for K in [1,100]:
  b=root/f'k{K}';X=arr(b/'features.f64','<f8').reshape(-1,12);a=arr(b/'GT10_L200/raw/ids.i32','<i4').reshape(-1,K);z=arr(b/'REUSE-SQ_L200/raw/ids.i32','<i4').reshape(-1,K);y=mask(z,g,K).sum(1).astype(float)-mask(a,g,K).sum(1);cost=np.median(arr(b/'completion_cost_us.f64','<f8').reshape(3,-1),axis=0);fit=slice(0,2000);cal=slice(2000,4000);target=.9*np.maximum(y[cal],0).sum();models=[]
  for nf in [5,12]:
   xf=X[fit,:nf];mean=xf.mean(0);scale=xf.std(0);scale[scale<1e-12]=1;Z=np.c_[(xf-mean)/scale,np.ones(2000)];reg=np.eye(nf+1)*10;reg[-1,-1]=0
   wg=np.linalg.solve(Z.T@Z+reg,Z.T@y[fit]);wc=np.linalg.solve(Z.T@Z+reg,Z.T@cost[fit]);models += [dict(kind='ridge',nf=nf,mean=mean.tolist(),scale=scale.tolist(),wg=wg.tolist(),wc=wc.tolist()),tree(X[fit],y[fit],cost[fit],nf)]
  candidates=[];viable=[]
  for base in models:
   sf=predict(base,X[fit]);sc=predict(base,X[cal])
   for rate in rates:
    t=float(np.quantile(sf,1-rate));on=sc>=t;rec=dict(kind=base['kind'],nf=base['nf'],requested_rate=rate,threshold=t,cal_on_rate=float(on.mean()),cal_net_gain=float((on*y[cal]).sum()),cal_positive_gain=float(np.maximum(y[cal],0).sum()),cal_estimate_us=float((on*cost[cal]).mean()+.5));candidates.append(rec)
    if rec['cal_net_gain']>=target:viable.append((rec['cal_estimate_us'],len(candidates)-1,dict(base,threshold=t)))
  baseline=dict(kind='on' if target>0 else 'off',nf=0,threshold=0.)
  offcost=0.;oncost=float(cost[cal].mean());fallback_cost=oncost if target>0 else offcost
  if target>0 and y[cal].sum()<target:fallback_cost=float('inf')
  viable.append((fallback_cost,-1,baseline));viable.sort(key=lambda v:(v[0],v[1]));chosen=viable[0][2];assert math.isfinite(viable[0][0]);mroot=R/f'storage/gates/{ds}';mroot.mkdir(parents=True,exist_ok=True);dump(mroot/f'k{K}.json',chosen);on=predict(chosen,X[cal]);on=on if on.dtype==bool else on>=chosen['threshold'];rec=dict(dataset=ds,K=K,selected_kind=chosen['kind'],selected_nf=chosen['nf'],fit_net_gain=float(y[fit].sum()),cal_net_gain=float(y[cal].sum()),cal_improved_queries=int((y[cal]>0).sum()),cal_cost_us=float(cost[cal].mean()),cal_oracle_action_us=float((cost[cal]*(y[cal]>0)).mean()),cal_learned_action_us=float((cost[cal]*on).mean()),cal_learned_on_rate=float(on.mean()),cal_learned_net_gain=float((y[cal]*on).sum()),selected_index=viable[0][1],model_sha256=sha(mroot/f'k{K}.json'));records.append(rec);dump(R/f'analysis/{ds}.k{K}.candidates.json',candidates)
  np.asarray(y,'<f8').tofile(b/'net_gain.f64')
 dump(R/f'analysis/{ds}.fit.json',records)
 tc=read(R/f'configs/{ds}.test.json');tc['gate_models']={str(k):str(R/f'storage/gates/{ds}/k{k}.json') for k in [1,100]};tc['oracle_masks']={str(k):str(R/f'storage/oracle/{ds}/k{k}.u8') for k in [1,100]};dump(R/f'configs/{ds}.formal.json',tc);qc=dict(tc);qc['queries']=dict(tc['queries'],n=128);qc['output_dir']=str(R/f'storage/qualification/{ds}');dump(R/f'configs/{ds}.qualification.json',qc)
 print(json.dumps(records),flush=True)
if __name__=='__main__':main(sys.argv[1])
