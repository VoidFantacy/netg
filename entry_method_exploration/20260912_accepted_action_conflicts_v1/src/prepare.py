from shared import *
import ast
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
assert read(E57/'reviews/final_audit.json')['status']=='PASS';check(E57/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',files(E52)+files(E53)+files(E56)+files(E57))
shutil.copy2(E57/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json');check(O/'reviews/native_dependencies.json')
shutil.copy2(E56/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E54/'bin/environment.so')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
contexts=[];budgets=[]
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=30000,native_hnsw_cap=1000000);dump(O/'inputs'/ds/'config.json',c)
 for stage,root,arm in [('E52',E52,'commit'),('E53',E53,'rl_ls'),('E56',E56,'graph_rl')]:
  for seed in SEEDS:
   p=root/'models'/ds/f'{arm}_{seed}';m=read(p/'model.json');n=m['accepted_submissions'] if stage=='E52' else m['accepted_updates'];parity_steps=sorted({0,m['selected_step'],200})
   contexts.append(dict(dataset=ds,stage=stage,arm=arm,seed=seed,key=f'{stage}_{seed}',source=str(p),selected_step=m['selected_step'],accepted=n,parity_steps=parity_steps,construction_only=stage=='E56'))
 cc=[x for x in contexts if x['dataset']==ds];states=sum(1+x['accepted'] for x in cc);graphs=sum(len(x['parity_steps']) for x in cc)
  # Six immutable trajectories per dataset; counts include every accepted step.
 budgets.append(dict(dataset=ds,normal_states=states,accepted=sum(x['accepted'] for x in cc),parity_graphs=graphs,parity_NSG=48*graphs,HNSW=1024*states+32*graphs,
  builds=sum((2 if x['construction_only'] else 1)*(1+x['accepted']) for x in cc),installations=sum(1+x['accepted'] for x in cc if x['construction_only']),NSG_reservation=30000))
 assert budgets[-1]['HNSW']<1000000 and budgets[-1]['builds']<7500
dump(O/'inputs/contexts.json',contexts);dump(O/'config.locked.json',dict(datasets=DS,runs=12,steps=2400,budgets=budgets,NSG_cap=60000,HNSW_cap=2000000,optimizer_updates=0,new_GT=0,threads=1,query_stop=QUERY_STOP,latest_launch=1789219800))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),str(p))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_IMMUTABLE_ACCEPTED_ACTION_DIAGNOSIS',NSG_calls=0,optimizer_updates=0));print('E58 PREPARED',json.dumps(budgets),flush=True)
