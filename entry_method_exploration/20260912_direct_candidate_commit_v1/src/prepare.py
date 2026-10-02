from shared import *
import ast
threads(8)
for name in ['inputs','results','reviews','logs','figures','source_before','bin','models']:(O/name).mkdir(exist_ok=True)
resources();assert not (O/'config.locked.json').exists();check(E51/'reviews/final_artifact_freeze.json');assert read(E51/'reviews/final_audit.json')['status']=='PASS'
freeze(O/'reviews/protected.json',[Path(x['path']) for x in read(E51/'reviews/protected.json')['files']]+files(E51))
shutil.copy2(E51/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json');check(O/'reviews/native_dependencies.json')
shutil.copy2(E46/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E46/'bin/environment.so')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/40_update_direction_radius.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
projection=0.;sources=[]
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();(O/'results'/ds).mkdir();c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=200000,native_hnsw_cap=14000000);dump(inp/'config.json',c)
 for name in ['local_parameters.npz']+[f'schedule_{seed}.npz' for seed in SEEDS]:
  shutil.copy2(E47/'inputs'/ds/name,inp/name);assert sha(inp/name)==sha(E47/'inputs'/ds/name)
 for seed in SEEDS:
  m=read(E47/'models'/ds/f'rl_{seed}'/'model.json');projection+=m['seconds'];sources.append(dict(dataset=ds,seed=seed,E47_RL_seconds=m['seconds']))
projection=1.5*projection+300;assert time.time()+projection<1789218600
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=200,population=8,sigma=.3,train_queries=4096,monitor_queries=1024,decision_steps=800,gradient_updates=0,
 NSG_hard_cap=400000,per_run_reservation=100000,fixed_NSG_per_run=15744,builds_per_run=1803,HNSW_per_run=6569216,HNSW_expected=26276864,builds_expected=7212,
 action='original RL Gaussian proposals; eligible iff all coefficients within [-2,2]',selection='original full J, no-op before candidate ordinal on ties',
 coefficient_clip_for_proposal=False,monitor_selection='same nonzero feasible checkpoint rule as E47',conservative_projection_seconds=projection,projection_sources=sources,projection_latest_finish_epoch=1789218600,
 training_stop=TRAIN_STOP,latest_launch=LATEST_LAUNCH,threads=1,output_bytes=256*(1<<20),minimum_free_bytes=8*(1<<30)))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_DIRECT_CANDIDATE_COMMIT',NSG_calls=0,decision_steps=0,gradient_updates=0))
print('E52 frozen, projection seconds',projection,flush=True)
