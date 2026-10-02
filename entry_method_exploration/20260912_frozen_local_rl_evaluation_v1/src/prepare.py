from common import *
import ast,sys
assert os.sched_getaffinity(0)=={8};sys.dont_write_bytecode=True
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
resources();assert not (O/'config.locked.json').exists();check(E48/'reviews/final_artifact_freeze.json',hashes=True)
assert read(E48/'reviews/final_audit.json')['status']=='PASS'
oldroots=[Path(x['path']).parent for x in []]
oldfiles=[Path(x['path']) for x in read(E48/'reviews/protected.json')['files']]+[p for p in E48.rglob('*') if p.is_file()]
freeze(O/'reviews/protected.json',oldfiles)
shutil.copy2(E48/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/37_score_topology_factorial.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
shutil.copy2(E37/'bin/evaluate',O/'bin/evaluate');assert sha(O/'bin/evaluate')==sha(E37/'bin/evaluate')
for name in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']:
 p=O/'src/evaluation_reference'/name;p.parent.mkdir(exist_ok=True);shutil.copy2(E37/'src/evaluation_reference'/name,p)
upstream=[E37/'bin/evaluate'];models=[]
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();(O/'results'/ds).mkdir();c=read(E37/'inputs'/ds/'config.json');dump(inp/'config.json',c)
 upstream.extend(Path(c[k]) for k in ['P','hub_ids','queries_file','gt_file','row_ids']);upstream.append(E37/'results'/ds/'baseline.hnsw')
 for phase in ['cal','audit']:
  upstream.extend(E37/'inputs'/ds/phase/name for name in ['queries.f32','gt.i64','row_ids.i64'])
 for arm in ARMS:
  for seed in SEEDS:
   folder=E47/'models'/ds/f'{arm}_{seed}';m=read(folder/'model.json');models.append(dict(dataset=ds,arm=arm,seed=seed,selected_step=m['selected_step']))
   upstream.extend([folder/'model.json',folder/'selected/W.f32',folder/'selected/graph.hnsw',folder/'checkpoints'/f'{m["selected_step"]:04}.npz'])
 old=read(E34/'inputs'/ds/'config.json');upstream.append(E34/'inputs'/ds/'config.json')
 for key in ['nsg','fast30k']:
  m=next(m for m in old['methods'] if m['model_name']==key and m['L']==64)
  if key!='nsg':upstream.extend(Path(m[k]) for k in ['W','mapping','tie_ids','graph_file'])
dump(O/'config.locked.json',dict(datasets=DS,models=models,NSG_hard_cap=CAP,expected_NSG=423680,fit_points=10,cal_points=10,audit_points=10,frontier_points=50,wall_repeats=250,threads=1,
 model_selection='cal mean U then lower total NDC then smaller seed',cal_recall_gate_pp=.1,audit_recall_gate_strict_pp=0,cost_delta_max_pct=1,optimizer_updates=0,
 output_bytes=256*(1<<20),minimum_free_bytes=8.5*(1<<30),query_stop=QUERY_STOP,campaign_deadline=1789221600))
freeze(O/'reviews/upstream.json',upstream)
for p in (O/'src').rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
freeze(O/'reviews/prequery_freeze.json',[p for part in ['src','inputs','bin'] for p in (O/part).rglob('*') if p.is_file()]+[O/'config.locked.json',O/'protocol.md'])
dump(O/'state.json',dict(status='PREPARED_FROZEN_LOCAL_RL_EVALUATION',queries=0,optimizer_updates=0))
campaign=R/'entry_method_exploration/20260912_until2000_v1/campaign.json';x=read(campaign);x.update(deadline_iso='2026-09-12T22:00:00+08:00',deadline_epoch=1789221600,current_stage=str(O),stage='E49_PREPARED',E47='COMPLETE_FINAL_AUDIT_PASS',E48='COMPLETE_FINAL_AUDIT_PASS',last_updated=time.time());dump(campaign,x)
print('E49 frozen models, evaluator and rules; no queries yet',flush=True)
