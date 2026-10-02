from shared import *
import ast
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
assert read(E53/'reviews/final_audit.json')['status']=='PASS';check(E53/'reviews/final_artifact_freeze_v2.json')
freeze(O/'reviews/protected.json',files(E37)+files(E48)+files(E52)+files(E53))
check(E53/'reviews/native_dependencies.json');shutil.copy2(E53/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
shutil.copy2(E48/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E48/'bin/environment.so')
contexts=[]
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=50000,native_hnsw_cap=70000);dump(O/'inputs'/ds/'config.json',c)
 for stage,root,arm in [('E52',E52,'commit'),('E53',E53,'rl_ls')]:
  for seed in SEEDS:
   p=root/'models'/ds/f'{arm}_{seed}';m=read(p/'model.json');iden=read(p/'selected/identity.json')
   contexts.append(dict(dataset=ds,key=f'{stage}_{seed}',stage=stage,seed=seed,selected_step=m['selected_step'],W=str(p/'selected/W.f32'),graph=str(p/'selected/graph.hnsw'),
    checkpoint=str(p/'checkpoints'/f'{m["selected_step"]:04}.npz'),topology_sha=iden['topology_sha']))
dump(O/'inputs/contexts.json',contexts)
dump(O/'config.locked.json',dict(datasets=DS,states=26,builds=18,installations=16,HNSW=136448,parity_NSG=4992,NSG_cap=100000,per_dataset_cap=50000,optimizer_updates=0,threads=1))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_FULL_MODEL_FACTORIAL',new_NSG=0));print('E54 PREPARED',flush=True)
