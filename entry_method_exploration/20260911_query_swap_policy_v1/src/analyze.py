from common import *
import csv
assert read(O/'state.json')['status']=='DEVELOPMENT_AND_WALL_COMPLETE_ANALYSIS_PENDING'
points=read(O/'results/points.json');selected=read(O/'results/cal_selection.json');training=read(O/'results/training_summary.json');rows=[];checks=[];paired=[];timings=[]
def interval(x,seed=20260920):
 rng=np.random.default_rng(seed);means=x[rng.integers(0,len(x),(5000,len(x)))].mean(axis=1);return np.quantile(means,[.025,.975]).tolist()
for ds in DS:
 for phase in ['cal','audit']:
  out=O/'results'/(phase+'_'+ds);names=[p['method'] for p in points if p['dataset']==ds and p['phase']==phase];n=512;gt=np.fromfile(O/'inputs'/ds/phase/'gt.i64',np.int64).reshape(n,100);source_rows=np.fromfile(O/'inputs'/ds/phase/'row_ids.i64',np.int64)
  data={}
  for name in names:
   folder=out/name;ids=np.fromfile(folder/'ids.i32',np.int32).reshape(n,10);hits=score(ids,gt);saved=np.load(folder/'scored.npz');assert np.array_equal(hits,saved['hits']);states=np.fromfile(folder/'states.i32',np.int32).reshape(n,4);action=np.fromfile(folder/'actions.i32',np.int32).reshape(n,3)
   ndc=np.fromfile(folder/'graph_ndc.u32',np.uint32);route=np.fromfile(folder/'route_ndc.u32',np.uint32);data[name]=dict(hits=hits,ndc=ndc.astype(float)+route,states=states,actions=action,utility=saved['utility'])
   for i in range(n):rows.append(dict(dataset=ds,phase=phase,method=name,row_id=int(source_rows[i]),hits=int(hits[i]),failed=bool(hits[i]==0),route_ndc=int(route[i]),graph_ndc=int(ndc[i]),final_state=int(states[i,-1]),swaps=int((action[i]>0).sum()),utility=float(saved['utility'][i])))
  comparisons=[(a,'base') for a in names if a!='base'];comparisons += [(selected[ds]['rl']['method'],'random'),(selected[ds]['rl']['method'],selected[ds]['exact']['method'])]
  for a,b in comparisons:
   ah=data[a]['hits'];bh=data[b]['hits'];delta=(ah.astype(float)-bh)*10;fd=((ah==0).astype(float)-(bh==0))*100;du=data[a]['utility']-data[b]['utility'];ci=interval(delta);fci=interval(fd)
   paired.append(dict(dataset=ds,phase=phase,method=a,reference=b,delta_recall_pp=float(delta.mean()),recall_CI_low_pp=ci[0],recall_CI_high_pp=ci[1],failure_delta_pp=float(fd.mean()),failure_CI_low_pp=fci[0],failure_CI_high_pp=fci[1],
    utility_delta=float(du.mean()),utility_CI=interval(du),helped=int((delta>0).sum()),harmed=int((delta<0).sum()),rescued=int(((bh==0)&(ah>0)).sum()),new_failures=int(((bh>0)&(ah==0)).sum()),total_NDC_change_pct=float((data[a]['ndc'].mean()/data[b]['ndc'].mean()-1)*100)))
 for p in points:
  if p['dataset']==ds and p['phase']=='wall':
   base=next(x for x in points if x['dataset']==ds and x['phase']=='wall' and x['method']=='base');p['QPS_change_pct']=(p['QPS_median']/base['QPS_median']-1)*100
   for t in p['timings']:timings.append(dict(dataset=ds,method=p['method'],**t))
 role=[]
 for phase in ['cal','audit']:
  p=next(x for x in points if x['dataset']==ds and x['phase']==phase and x['method']==selected[ds]['rl']['method']);required=.1 if phase=='cal' else 0
  recall_ok=p['delta_recall_pp']>=required if phase=='cal' else p['delta_recall_pp']>0
  role.append(dict(phase=phase,method=p['method'],recall_delta_pp=p['delta_recall_pp'],total_NDC_change_pct=p['total_NDC_change_pct'],recall_pass=recall_ok,NDC_pass=p['total_NDC_change_pct']<=1,pass_point=recall_ok and p['total_NDC_change_pct']<=1))
 random_delta=np.mean([x['utility_delta'] for x in paired if x['dataset']==ds and x['method']==selected[ds]['rl']['method'] and x['reference']=='random']);exact_delta=np.mean([x['utility_delta'] for x in paired if x['dataset']==ds and x['method']==selected[ds]['rl']['method'] and x['reference']==selected[ds]['exact']['method']])
 checks.append(dict(dataset=ds,points=role,mean_RL_minus_random_utility=float(random_delta),mean_RL_minus_exact_utility=float(exact_delta),random_pass=random_delta>0,development_pass=all(x['pass_point'] for x in role) and random_delta>0))
gate=dict(status='PASS' if all(x['development_pass'] for x in checks) else 'STOP_DUAL_DEVELOPMENT_GATE',datasets=checks,full_frontier_run=False,default_replaced=False,
 conclusion='QUERY_SWAP_POLICY_COMPLETE_YANDEX_SIGNAL_WEBVID_AND_COST_NO_GO',single_L_wall_is_not_frontier=True)
checkpoints=[];curves=[];models=[]
for r in training:
 ds=r['dataset'];arm=r['arm'];seed=r['seed'];folder=O/'models'/ds/f'{arm}_{seed}';last=read(folder/'checkpoints.json')[-1];best=r['best']
 models.append(dict(dataset=ds,arm=arm,seed=seed,selected_step=best['step'],train_delta_pp=best['train']['delta_recall_pp'],monitor_delta_pp=best['monitor']['delta_recall_pp'],selected_monitor_utility=best['monitor']['utility'],
  last_train_delta_pp=last['train']['delta_recall_pp'],last_monitor_delta_pp=last['monitor']['delta_recall_pp'],last_monitor_utility=last['monitor']['utility'],training_seconds=r['training_seconds'],updates=r['updates']))
 for c in read(folder/'checkpoints.json'):
  for role in ['train','monitor','full_fit']:checkpoints.append(dict(dataset=ds,arm=arm,seed=seed,step=c['step'],role=role,selected=c['step']==best['step'],**c[role]))
 for c in read(folder/'training_curve.json'):curves.append(dict(dataset=ds,arm=arm,seed=seed,**c))
for name,data in [('query_results',rows),('paired',paired),('timings',timings),('training_checkpoints',checkpoints),('training_curves',curves),('models',models),('points',points)]:
 dump(O/'results'/(name+'.json'),data)
 flat=[{k:v for k,v in x.items() if not isinstance(v,(list,dict))} for x in data];fields=list(dict.fromkeys(k for x in flat for k in x))
 with (O/'results'/(name+'.csv')).open('w') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(flat)
dump(O/'results/development_gate.json',gate);dump(O/'results/analysis.json',dict(gate=gate,selected=selected,models=models,paired=paired,points=points))
print(json.dumps(gate,indent=2),flush=True)
for p in points:
 if p['phase']=='wall':print('WALL_POINT',p['dataset'],p['method'],p['recall_pct'],p['QPS_median'],p['QPS_change_pct'],p['failure_pct'],flush=True)
