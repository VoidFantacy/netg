from shared import *
threads(8);resources();assert all(read(O/'results'/ds/'query_complete.json')['status']=='PASS' for ds in DS)
started=time.monotonic();contexts=[];summaries=[]
def table(p,rows):
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def paired(h1,h0):
 dh=h1.astype(int)-h0
 return dict(gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),net_hits=int(dh.sum()),
  gain_queries=int((dh>0).sum()),loss_queries=int((dh<0).sum()),new_zero_queries=int(((h1==0)&(h0>0)).sum()),rescued_zero_queries=int(((h1>0)&(h0==0)).sum()))
def cosine(a,b):
 n=np.linalg.norm(a)*np.linalg.norm(b)
 return float(a@b/n) if n>1e-20 else None
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)[:4096]
 base={k:v[:4096] for k,v in dict(np.load(E37/'results'/ds/'baseline.npz')).items()};p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  step=rec['step'];slot=rec['slot'];up=dict(np.load(O/'inputs'/ds/f'{step:04}_updates.npz'));w=np.fromfile(rec['current_W'],np.float32).reshape(p.shape)
  raw=[dict(np.load(rec['current_raw']))]+[dict(np.load(O/'results'/ds/f'{step:04}'/tag/'raw.npz')) for tag in ['batch','full']]
  h=np.stack([score(x['ids'],gt) for x in raw]);u=np.stack([utility(x,base,gt) for x in raw]);dh=h[1:].astype(int)-h[0];du=u[1:]-u[0]
  drift0=float(np.square(w.astype(float)-p).sum(1).mean());drifts=[]
  cr=dict(dataset=ds,step=step,hub=rec['hub'],slot=slot)
  for i,tag in enumerate(['batch','full'],1):
   ww=w.copy();ww[slot]=up[tag+'_row'];drift=float(np.square(ww.astype(float)-p).sum(1).mean());drifts.append(drift)
   metrics=paired(h[i],h[0]);metrics.update(mean_delta_U=float((u[i]-u[0]).mean()),mean_delta_J=float((u[i]-u[0]).mean()-(drift-drift0)),
    route_NDC_sum=int(raw[i]['route_ndc'].sum()),graph_NDC_sum=int(raw[i]['graph_ndc'].sum()),
    graph_NDC_change_pct=float((raw[i]['graph_ndc'].mean()/raw[0]['graph_ndc'].mean()-1)*100),
    entry_change_queries=int((raw[i]['entries']!=raw[0]['entries']).any(1).sum()),
    row_displacement=float(np.linalg.norm(up[tag+'_row'].astype(float)-w[slot])),gradient_norm=float(np.linalg.norm(up[tag+'_gradient'])))
   cr.update({tag+'_'+k:v for k,v in metrics.items()})
  metrics=paired(h[2],h[1]);metrics.update(mean_delta_U=float((u[2]-u[1]).mean()),mean_delta_J=float((u[2]-u[1]).mean()-(drifts[1]-drifts[0])))
  cr.update({'full_vs_batch_'+k:v for k,v in metrics.items()})
  cr.update(current_graph_NDC_sum=int(raw[0]['graph_ndc'].sum()),current_route_NDC_sum=int(raw[0]['route_ndc'].sum()),
   gradient_cosine=cosine(up['batch_gradient'],up['full_gradient']),row_update_cosine=cosine(up['batch_row'].astype(float)-w[slot],up['full_row'].astype(float)-w[slot]),
   batch_full_row_difference=float(np.linalg.norm(up['full_row'].astype(float)-up['batch_row'])))
  old=next(x for x in read(E44/'results/analysis.json')['contexts'] if x['dataset']==ds and x['step']==step)
  cr.update(sampled_positive_actions=old['positive_actions'],sampled_best_net_hits=old['best_net_hits'],sampled_oracle_hit_gain=old['oracle_hit_gain'])
  save(O/'results'/ds/f'{step:04}'/'derived.npz',hits=h,U=u,delta_hits=dh,delta_U=du,drift=np.array([drift0]+drifts),full_vs_batch_hits=h[2].astype(int)-h[1])
  contexts.append(cr)
 rr=[x for x in contexts if x['dataset']==ds];dr=dict(dataset=ds)
 for tag in ['batch','full','full_vs_batch']:
  for field in ['gain_hits','loss_hits','net_hits','gain_queries','loss_queries','new_zero_queries','rescued_zero_queries']:
   dr[tag+'_'+field]=sum(x[tag+'_'+field] for x in rr)
  for field in ['mean_delta_U','mean_delta_J']:dr[tag+'_'+field]=float(np.mean([x[tag+'_'+field] for x in rr]))
  dr[tag+'_positive_contexts']=sum(x[tag+'_net_hits']>0 for x in rr);dr[tag+'_negative_contexts']=sum(x[tag+'_net_hits']<0 for x in rr)
 for tag in ['batch','full']:
  dr[tag+'_graph_NDC_change_pct']=(sum(x[tag+'_graph_NDC_sum'] for x in rr)/sum(x['current_graph_NDC_sum'] for x in rr)-1)*100
  dr[tag+'_mean_row_displacement']=float(np.mean([x[tag+'_row_displacement'] for x in rr]))
 dr['sampled_positive_contexts']=sum(x['sampled_positive_actions']>0 for x in rr)
 dr['passed']=dr['full_net_hits']>0 and dr['full_mean_delta_U']>0 and dr['full_vs_batch_net_hits']>=0 and dr['full_vs_batch_mean_delta_U']>0 and dr['full_graph_NDC_change_pct']<=1
 summaries.append(dr)
table(O/'results/contexts.csv',contexts);table(O/'results/datasets.csv',summaries)
gate=dict(status='PASS_FULL_FEEDBACK_SINGLE_STEP_RESEARCH_GATE' if all(x['passed'] for x in summaries) else 'STOP_QUERY_SAMPLING_RESCUE_FOR_THIS_UPDATE',datasets=summaries,
 scope='20 independent same-state deterministic single-step controls; not a training run or deployable aggregate')
dump(O/'results/gate.json',gate);dump(O/'results/analysis.json',dict(contexts=contexts,datasets=summaries,seconds=time.monotonic()-started))
cost=[read(O/'results'/ds/'query_complete.json') for ds in DS]
dump(O/'results/cost.json',dict(NSG_calls=167040,HNSW_calls=166080,builds=60,normal_new_NSG=164160,parity_NSG=2880,
 reused_full_current_rows=81920,continuous_training_updates=0,counterfactual_single_steps=20,historical_update_replays=20,new_GT=0,new_development_queries=0,QPS_points=0,datasets=cost))
print(json.dumps(gate,indent=2),flush=True)
