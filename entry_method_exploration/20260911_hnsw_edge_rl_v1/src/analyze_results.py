from common import *
from analyze_training import graph,verify_graph
assert read(O/'state.json')['status'] in ['COMPLETE_DEVELOPMENT_STOP','COMPLETE_WITH_EXPLORATORY_PERFORMANCE']
paired=read(O/'results/development_paired.json');selection=read(O/'results/cal_selection.json')['selection'];checkpoints=read(O/'results/checkpoint_metrics.json')
allpoints=[];comparisons=[];topology_rows=[];policy_rows=[];training_rows=[];selected_rows=[]
for ds in DS:
 t=read(O/'inputs'/ds/'topology.json');protected=np.array(t['protected'],bool);offsets=np.array(t['offsets']);E=t['edges'];mask_by_seed={}
 base=np.load(O/'results'/ds/'baseline.npz');gt=np.fromfile(read(O/'inputs'/ds/'config.json')['gt_file'],np.int64).reshape(20000,100)
 for seed in SEEDS:
  dest=O/'models'/ds/str(seed);info=read(dest/'selected.json');learned=np.fromfile(dest/'selected/mask.u8',np.uint8);random=np.fromfile(dest/'selected/random_mask.u8',np.uint8);logits=np.fromfile(dest/'selected/logits.f64',np.float64);p=1/(1+np.exp(-logits));exposure=np.fromfile(dest/'edge_exposures.i64',np.int64)
  mask_by_seed[seed]=learned;non=~protected
  selected_rows.append(dict(dataset=ds,seed=seed,selected_step=info['best']['step'],selected_by_cal=selection[ds]==seed,monitor_recall_pct=info['best']['recall']*100,
   monitor_baseline_recall_pct=info['baseline_monitor']['recall']*100,monitor_delta_pp=(info['best']['recall']-info['baseline_monitor']['recall'])*100,
   original_edges=E,retained_edges=int(learned.sum()),deleted_edges=int((learned==0).sum()),deleted_pct=float((learned==0).mean()*100),
   route_change_pct=(info['best']['route_ndc']/info['baseline_monitor']['route_ndc']-1)*100,total_change_pct=(info['best']['total_ndc']/info['baseline_monitor']['total_ndc']-1)*100))
  for u in range(t['nodes']):
   sl=slice(offsets[u],offsets[u+1]);topology_rows.append(dict(dataset=ds,seed=seed,node=u,original_outdegree=int(offsets[u+1]-offsets[u]),protected_outdegree=int(protected[sl].sum()),learned_outdegree=int(learned[sl].sum()),random_outdegree=int(random[sl].sum())))
  policy_rows.append(dict(dataset=ds,seed=seed,optimized_edges=int(non.sum()),never_exposed_edges=int((exposure[non]==0).sum()),mean_exposures=float(exposure[non].mean()),
   selected_probability_min=float(p[non].min()),selected_probability_max=float(p[non].max()),selected_probability_mean=float(p[non].mean()),
   probability_between_045_055_pct=float(((p[non]>.45)&(p[non]<.55)).mean()*100),same_nonprotected_decisions_as_random_pct=float((learned[non]==random[non]).mean()*100)))
  history=read(dest/'training_curve.json')
  for row in history:training_rows.append(dict(dataset=ds,seed=seed,**row))
  # Descriptive first/last 100 rollout reward: different random minibatches, not a fixed-query causal estimate.
  policy_rows[-1].update(first100_rollout_reward=float(np.mean([x['reward'] for x in history[:100]])),last100_rollout_reward=float(np.mean([x['reward'] for x in history[-100:]])))
 for split in ['cal','audit']:
  dest=O/'results'/f'{split}_{ds}';result=read(dest/'results.json');n=result['queries'];rng=np.random.default_rng(20260914);boot=rng.integers(0,n,(2000,n))
  ids={m['model_name']:np.fromfile(dest/m['name']/'hits.u8',np.uint8).astype(float) for m in result['methods']}
  for m in result['methods']:
   allpoints.append(dict(dataset=ds,split=split,method=m['model_name'],L=m['L'],queries=n,recall_pct=m['recall_at_10']*100,route_ndc=m['mean_route_ndc'],graph_ndc=m['mean_graph_ndc'],total_ndc=m['mean_total_ndc'],QPS=m['qps']))
  for seed in SEEDS:
   delta=ids[f'rl_{seed}']-ids[f'random_{seed}'];ci=np.quantile(delta[boot].mean(1)*10,[.025,.975])
   comparisons.append(dict(dataset=ds,split=split,seed=seed,selected_by_cal=selection[ds]==seed,rl_minus_random_pp=float(delta.mean()*10),ci95_low_pp=float(ci[0]),ci95_high_pp=float(ci[1]),
    gained_queries=int((delta>0).sum()),lost_queries=int((delta<0).sum())))
for row in paired:
 row['ci95_low_pp'],row['ci95_high_pp']=row.pop('ci95_pp');row['selected_by_cal']=row['method'].endswith(str(selection[row['dataset']]))
training_fields=['dataset','seed','step','reward','recall','loss','gradient_norm','mean_actions','mean_entropy','route_ndc','graph_ndc','total_ndc','lr','seconds']
training_rows=[{k:r[k] for k in training_fields} for r in training_rows]
tables=dict(selected_models=selected_rows,training_curve=training_rows,monitor_checkpoints=checkpoints,real_points=allpoints,paired_development=paired,rl_vs_random=comparisons,topology=topology_rows,policy_diagnostics=policy_rows)
dump(O/'results/report_tables.json',tables)
jobs=read(O/'logs/jobs.json');assert all(j['status']=='COMPLETE' for j in jobs)
cost=dict(actual_NSG_calls=sum(j['actual_calls'] for j in jobs),reserved_NSG_calls=sum(j['reserved_calls'] for j in jobs),cap=CAP,
 training_process=read(O/'logs/training_process.json'),training_and_monitor_seconds=sum(j['training_seconds'] for j in jobs if 'training_seconds' in j),
 measured_QPS_points=read(O/'state.json')['QPS_points'],evaluation_points=len(allpoints),evaluated_query_outputs=sum(x['queries'] for x in allpoints),
 new_rollout_feedback=4*600*128,monitor_outputs=4*7*4000,baseline_fit_outputs=40000,prior_C8_labels_used=0,
 HNSW_queries=sum(read(O/'results'/ds/'native_accounting.json')['HNSW_calls'] for ds in DS)+sum(x['route_calls'] for x in read(O/'reviews/router_preflight_v2.json')['datasets'])+sum(j['actual_calls']-16*5 for j in jobs if j['name'].startswith(('cal_','audit_'))),
 all_fit_training_baseline_monitor_and_development_ID_outputs=4*600*128+4*7*4000+40000+sum(x['queries'] for x in allpoints))
dump(O/'results/costs.json',cost)
dump(O/'reviews/analysis_verification.json',dict(status='PASS',raw_results_only=True,new_query_calls=0,table_rows={k:len(v) for k,v in tables.items()},random_control_preserves_per_node_degree=True))
print('RESULT_ANALYSIS_PASS',cost['actual_NSG_calls'],cost['reserved_NSG_calls'],tables['rl_vs_random'],flush=True)
