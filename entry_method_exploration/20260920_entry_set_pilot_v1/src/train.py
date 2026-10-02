from common import *

def fit_tree(X,U):
 nodes=[]
 def rec(ix,depth):
  sums=U[ix].sum(0);action=int(np.argmax(sums));value=float(sums[action]);j=len(nodes);nodes.append(dict(feature=-1,action=action,support=len(ix),training_value=value))
  if depth==LOCK['tree_depth'] or len(ix)<2*LOCK['min_leaf']:return j
  best=None
  for f in range(X.shape[1]):
   for threshold in np.unique(np.quantile(X[ix,f],LOCK['split_quantiles'])):
    mask=X[ix,f]<=threshold;n=int(mask.sum())
    if min(n,len(ix)-n)<LOCK['min_leaf']:continue
    lhs=U[ix[mask]].sum(0);rhs=sums-lhs;gain=float(lhs.max()+rhs.max())
    if gain>value+1e-12:
     value=gain;best=(f,float(threshold),ix[mask],ix[~mask])
  if best is not None:
   f,t,left,right=best;nodes[j].update(feature=f,threshold=t,left=rec(left,depth+1),right=rec(right,depth+1))
  return j
 rec(np.arange(len(X)),0);return nodes

def train():
 started=time.time();frozen=[];summaries=[]
 for ds,c in LOCK['datasets'].items():
  p=RUN/'results'/ds/'labels';cfg=read(RUN/'inputs'/ds/'fit/config.json');n=cfg['n'];gt=np.fromfile(cfg['gt'],np.int64).reshape(n,100);X=np.fromfile(p/'features.f64',np.float64).reshape(n,6);T=np.fromfile(p/'seconds.f64',np.float64).reshape(n,5,LOCK['label_repeats']);H=np.empty((n,4,2),np.int16)
  for a,variant in enumerate([0,2,3,4]):
   ids=np.fromfile(p/f'variant{variant}/ids.i32',np.int32).reshape(n,100)
   H[:,a,0]=ids[:,0]==gt[:,0];H[:,a,1]=[np.isin(row,truth).sum() for row,truth in zip(ids,gt)]
   assert all(len(set(row))==100 for row in ids)
  H.tofile(p/'hits.i16');R=H.astype(float);R[:,:,1]/=100;DR=R-R[:,0:1];dt=T[:,1:,:].mean(2)-T[:,0:1,:].mean(2);scale=float(T[:,0,:].mean());U=.5*(DR[:,:,0]+DR[:,:,1])-LOCK['cost_weight']*dt/scale
  out=RUN/'models'/ds;out.mkdir(parents=True,exist_ok=False);X.tofile(out/'fit_features.f64');H.tofile(out/'fit_hits.i16');dt.tofile(out/'fit_delta_time.f64')
  fixed=int(np.argmax(R.mean((0,2))));methods=[dict(name='GT10',action=0),*[dict(name=f'Single{a}',action=a) for a in [1,2,3]],dict(name='Feature3',action=0,features=True)];records=[]
  perm=np.random.default_rng(LOCK['shuffle_seed']).permutation(n);perm.astype(np.int32).tofile(out/'shuffle.i32')
  for name,target in [('CostTree',U),('RecallTree',.5*(DR[:,:,0]+DR[:,:,1])),('ShuffledTree',U[perm])]:
   nodes=fit_tree(X,target);choices=predict(nodes,X);chosen=R[np.arange(n),choices];selected_dt=dt[np.arange(n),choices]
   for node in nodes:
    if node['feature']>=0:continue
    # Node-specific rows reconstructed using an independent traversal below in verification.
   methods.append(dict(name=name,tree=nodes,features=True));np.asarray(choices,np.int32).tofile(out/f'{name}.fit_actions.i32')
   records.append(dict(method=name,nodes=len(nodes),actions=np.bincount(choices,minlength=4).tolist(),recall_pct=(chosen.mean(0)*100).tolist(),delta_recall_pp=((chosen-R[:,0]).mean(0)*100).tolist(),delta_training_seconds=float(selected_dt.mean()),relative_training_time=float(selected_dt.mean()/scale),fit_objective=float(target[np.arange(n),choices].mean()),fit_nonzero_K1=int(np.count_nonzero(chosen[:,0]-R[:,0,0]))))
   # Store per-leaf full vector estimates without using acceptance data.
   leaf_rows={j:[] for j,node in enumerate(nodes) if node['feature']<0}
   for i,x in enumerate(X):
    j=0
    while nodes[j]['feature']>=0:
     nd=nodes[j];j=nd['left'] if x[nd['feature']]<=nd['threshold'] else nd['right']
    leaf_rows[j].append(i)
   for j,rows in leaf_rows.items():
    z=np.asarray(rows);nodes[j]['estimates']=dict(delta_recall=DR[z].mean(0).tolist(),delta_seconds=dt[z].mean(0).tolist(),K1_nonzero=(DR[z,:,0]!=0).sum(0).tolist(),K100_nonzero=(DR[z,:,1]!=0).sum(0).tolist())
  doc=dict(dataset=ds,methods=methods,fixed_best_action=fixed,fixed_best_method='GT10' if fixed==0 else f'Single{fixed}',fit_fixed_recall_pct=(R.mean(0)*100).tolist(),fit_baseline_seconds=scale,records=records)
  dump(out/'models.json',doc);frozen.append(ident(out/'models.json'));summaries.append(doc);print('TRAINED',ds,json.dumps(records),flush=True)
 dump(RUN/'reviews/models_frozen.json',dict(created_unix=time.time(),files=frozen,training_seconds=time.time()-started,accept_payload_read=False,models=6))
 dump(RUN/'results/fit_summary.json',summaries)
if __name__=='__main__':train()
