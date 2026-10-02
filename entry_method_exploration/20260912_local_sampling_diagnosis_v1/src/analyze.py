from shared import *
threads(8);resources();resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS' for ds in DS)
started=time.monotonic();contexts=[];actions=[];datasets=[]
def var_srs(g,n):
 N=g.shape[1]
 return 0. if N<=1 or n==N else float((1-n/N)*g.var(axis=1,ddof=1).sum()/n)
def variance(g,near,n1,n0):
 N=g.shape[1];total=0.
 for mask,n in [(near,n1),(~near,n0)]:
  if mask.sum():total+=(mask.sum()/N)**2*var_srs(g[:,mask],n)
 return float(total)
def cos(a,b):
 d=np.linalg.norm(a)*np.linalg.norm(b)
 return float(a@b/d) if d>1e-20 else None
def table(path,rows):
 with path.open('w',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base={k:v[:4096] for k,v in dict(np.load(E37/'results'/ds/'baseline.npz')).items()}
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  step=rec['step'];inp=dict(np.load(O/'inputs'/ds/f'{step:04}_context.npz'));t=dict(np.load(rec['trajectory']))
  near=inp['near'];oldrows=inp['old_rows'];M=(inp['eps']-inp['eps'].mean(0)).T/(7*SIGMA)
  raw=[dict(np.load(O/'results'/ds/f'{step:04}'/tag/'raw.npz')) for tag in ['C']+[f'A{i}' for i in range(8)]]
  h=np.stack([score(x['ids'],gt) for x in raw]).astype(np.int16)
  u=np.stack([utility(x,base,gt) for x in raw]);dh=h[1:]-h[0];du=u[1:]-u[0]
  c0=base['route_ndc'].astype(float)+base['graph_ndc']
  totals=np.stack([x['route_ndc'].astype(float)+x['graph_ndc'] for x in raw])
  dc=-.1*(totals[1:]-totals[0])/c0
  df=-.1*((h[1:]==0).astype(float)-(h[0]==0).astype(float))
  np.testing.assert_allclose(du,dh+dc+df,atol=3e-15)
  drift=t['drift']-t['current_drift'];gd=-M@drift
  gu=M@du;gh=M@dh;gc=M@dc;gf=M@df
  np.testing.assert_allclose(gu,gh+gc+gf,atol=2e-14)
  full=gu.mean(1)+gd;old=gu[:,oldrows].mean(1)+gd
  np.testing.assert_allclose(old,t['gradient'],atol=2e-14)
  np.testing.assert_allclose(du[:,oldrows].mean(1)-drift,t['rewards'],atol=2e-14)
  n1=rec['near_sample'];n0=rec['far_sample'];vu=var_srs(gu,128);vs=variance(gu,near,n1,n0)
  hvu=var_srs(gh,128);hvs=variance(gh,near,n1,n0)
  weighted=sum(mask.sum()/4096*gu[:,mask].mean(1) for mask in [near,~near] if mask.sum())
  np.testing.assert_allclose(weighted,gu.mean(1),atol=2e-14)
  net=dh.sum(1);gain=np.maximum(dh,0).sum(1);loss=np.maximum(-dh,0).sum(1)
  best=int(np.argmax(np.r_[0,net]))-1;bestgain=int(gain[best]) if best>=0 else 0;bestloss=int(loss[best]) if best>=0 else 0
  oracle=np.maximum(0,dh.max(0));affected=(dh!=0).any(0);sampled=np.zeros(4096,bool);sampled[oldrows]=True
  cr=dict(dataset=ds,step=step,hub=rec['hub'],near_population=int(near.sum()),far_population=int((~near).sum()),near_sample=n1,far_sample=n0,
   full_hit_candidates=int((dh!=0).any(1).sum()),old_hit_candidates=int((dh[:,oldrows]!=0).any(1).sum()),
   full_affected_queries=int(affected.sum()),old_affected_queries=int(affected[oldrows].sum()),missed_affected_queries=int((affected&~sampled).sum()),
   near_affected_queries=int(affected[near].sum()),far_affected_queries=int(affected[~near].sum()),
   gained_hits_all_actions=int(gain.sum()),lost_hits_all_actions=int(loss.sum()),
   near_gained_hits_all_actions=int(np.maximum(dh[:,near],0).sum()),far_gained_hits_all_actions=int(np.maximum(dh[:,~near],0).sum()),
   near_lost_hits_all_actions=int(np.maximum(-dh[:,near],0).sum()),far_lost_hits_all_actions=int(np.maximum(-dh[:,~near],0).sum()),
   positive_actions=int((net>0).sum()),negative_actions=int((net<0).sum()),mixed_gain_loss_actions=int(((gain>0)&(loss>0)).sum()),
   oracle_hit_gain=int(oracle.sum()),best_action=best,best_net_hits=max(0,int(net.max())),best_gain_hits=bestgain,best_loss_hits=bestloss,
   oracle_coverage_gap=int(oracle.sum())-bestgain,oracle_cancellation_gap=bestloss,
   U_uniform_variance=vu,U_stratified_variance=vs,U_variance_ratio=vs/vu if vu>1e-18 else None,
   hit_uniform_variance=hvu,hit_stratified_variance=hvs,hit_population_variance=float(gh.var(axis=1,ddof=1).sum()),
   U_full_gradient_norm=float(np.linalg.norm(full)),hit_full_gradient_norm=float(np.linalg.norm(gh.mean(1))),drift_gradient_norm=float(np.linalg.norm(gd)),
   old_gradient_error_sq=float(np.square(old-full).sum()),old_full_cosine=cos(old,full),
   hit_old_gradient_error_sq=float(np.square(gh[:,oldrows].mean(1)-gh.mean(1)).sum()),
   hit_old_full_cosine=cos(gh[:,oldrows].mean(1),gh.mean(1)))
  assert cr['oracle_hit_gain']-cr['best_net_hits']==cr['oracle_coverage_gap']+cr['oracle_cancellation_gap']
  contexts.append(cr)
  for a in range(8):
   d=dh[a];ent=(raw[a+1]['entries']!=raw[0]['entries']).any(1)
   actions.append(dict(dataset=ds,step=step,action=a,hub=rec['hub'],gain_hits=int(gain[a]),loss_hits=int(loss[a]),net_hits=int(net[a]),
    gain_queries=int((d>0).sum()),loss_queries=int((d<0).sum()),entry_change_queries=int(ent.sum()),
    near_gain_hits=int(np.maximum(d[near],0).sum()),near_loss_hits=int(np.maximum(-d[near],0).sum()),
    far_gain_hits=int(np.maximum(d[~near],0).sum()),far_loss_hits=int(np.maximum(-d[~near],0).sum()),
    old_gain_hits=int(np.maximum(d[oldrows],0).sum()),old_loss_hits=int(np.maximum(-d[oldrows],0).sum()),
    new_zero_queries=int(((h[a+1]==0)&(h[0]>0)).sum()),rescued_zero_queries=int(((h[a+1]>0)&(h[0]==0)).sum()),
    delta_graph_NDC=int((raw[a+1]['graph_ndc'].astype(np.int64)-raw[0]['graph_ndc']).sum()),
    delta_route_NDC=int((raw[a+1]['route_ndc'].astype(np.int64)-raw[0]['route_ndc']).sum()),
    full_delta_J=float(du[a].mean()-drift[a]),old_delta_J=float(t['rewards'][a])))
  save(O/'results'/ds/f'{step:04}'/'derived.npz',hits=h,U=u,delta_hits=dh,delta_U=du,near=near,old_rows=oldrows,
   gradient_U=gu,gradient_hits=gh,gradient_cost=gc,gradient_failure=gf,gradient_drift=gd,full_gradient=full,old_gradient=old)
 rr=[x for x in contexts if x['dataset']==ds];aa=[x for x in actions if x['dataset']==ds]
 uv=sum(x['U_uniform_variance'] for x in rr);sv=sum(x['U_stratified_variance'] for x in rr);nv=[x for x in rr if x['U_uniform_variance']>1e-18]
 quality=sum(x['hit_population_variance']>1e-18 for x in rr);fraction=sum(x['U_stratified_variance']<=x['U_uniform_variance'] for x in nv)/len(nv) if nv else None
 passed=quality>=4 and uv>1e-18 and sv/uv<=.5 and fraction is not None and fraction>=.6
 dr=dict(dataset=ds,quality_contexts=quality,full_hit_contexts=sum(x['full_affected_queries']>0 for x in rr),old_hit_contexts=sum(x['old_affected_queries']>0 for x in rr),
  full_hit_actions=sum(x['gain_hits']+x['loss_hits']>0 for x in aa),old_hit_actions=sum(x['old_gain_hits']+x['old_loss_hits']>0 for x in aa),
  mixed_gain_loss_actions=sum(x['gain_hits']>0 and x['loss_hits']>0 for x in aa),positive_actions=sum(x['net_hits']>0 for x in aa),negative_actions=sum(x['net_hits']<0 for x in aa),
  uniform_U_variance_sum=uv,stratified_U_variance_sum=sv,U_variance_ratio=sv/uv if uv>1e-18 else None,
  nonzero_U_contexts=len(nv),nonworse_fraction=fraction,passed=passed,
  gain_hits_all_actions=sum(x['gain_hits'] for x in aa),loss_hits_all_actions=sum(x['loss_hits'] for x in aa),
  near_gain_hits_all_actions=sum(x['near_gain_hits'] for x in aa),far_gain_hits_all_actions=sum(x['far_gain_hits'] for x in aa),
  near_loss_hits_all_actions=sum(x['near_loss_hits'] for x in aa),far_loss_hits_all_actions=sum(x['far_loss_hits'] for x in aa))
 datasets.append(dr)
table(O/'results/contexts.csv',contexts);table(O/'results/actions.csv',actions);table(O/'results/datasets.csv',datasets)
gate=dict(status='PASS_WEIGHTED_SAMPLER_RESEARCH_GATE' if all(x['passed'] for x in datasets) else 'STOP_THIS_WEIGHTED_SAMPLER',datasets=datasets,
 scope='fixed states and directions, finite train population, conditional query variance only',new_training=0)
dump(O/'results/gate.json',gate);dump(O/'results/analysis.json',dict(contexts=contexts,actions=actions,datasets=datasets,seconds=time.monotonic()-started))
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS]
dump(O/'results/cost.json',dict(NSG_calls=sum(x['NSG_calls'] for x in costs),HNSW_calls=sum(x['HNSW_calls'] for x in costs),builds=sum(x['builds'] for x in costs),
 normal_queries=737280,parity_NSG=1728,optimizer_updates=0,new_GT=0,new_development_queries=0,QPS_points=0,datasets=costs))
print(json.dumps(gate,indent=2),flush=True)
