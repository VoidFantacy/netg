from shared import *
from graph_bytes import inspect_serialized
import ast
threads(8)
for name in ['inputs','results','reviews','logs','figures','source_before','bin','models']:(O/name).mkdir(exist_ok=True)
resources();assert not (O/'config.locked.json').exists();assert read(E55/'reviews/final_audit.json')['status']=='PASS';check(E55/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',files(E53)+files(E54)+files(E55))
shutil.copy2(E55/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json');check(O/'reviews/native_dependencies.json')
E48=R/'entry_method_exploration/20260912_score_topology_factorial_v1';shutil.copy2(E48/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E48/'bin/environment.so')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
duration=read(E53/'results/cost.json')['training_process_seconds'];projection=duration*1.65+180;assert time.time()+projection<1789218600
checks=[]
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();(O/'results'/ds).mkdir();c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=150000,native_hnsw_cap=9500000);dump(inp/'config.json',c)
 for name in ['local_parameters.npz']+[f'schedule_{seed}.npz' for seed in SEEDS]:shutil.copy2(E47/'inputs'/ds/name,inp/name);assert sha(inp/name)==sha(E47/'inputs'/ds/name)
 P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);mapping=np.fromfile(c['hub_ids'],np.int32)
 base=inspect_serialized(E37/'results'/ds/'baseline.hnsw',P,mapping)
 for rec in [x for x in read(E54/'inputs/contexts.json') if x['dataset']==ds]:
  folder=E54/'results'/ds/rec['key']/'T';g=inspect_serialized(folder/'graph.hnsw',P,mapping);assert g['topology_sha']==read(folder/'identity.json')['topology_sha'];checks.append(dict(dataset=ds,model=rec['key'],profile_rows=g['profile_rows'],topology_sha=g['topology_sha']))
dump(O/'reviews/serialized_parser_preflight.json',dict(status='PASS',historical_T_graphs=8,records=checks,new_search=0))
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=200,population=8,sigma=.3,deterministic_radii=[.25,.5,1.],train_queries=4096,monitor_queries=1024,
 gradient_updates=800,decision_steps=800,NSG_hard_cap=600000,per_run_reservation=150000,fixed_NSG_per_run=15744,builds_per_run=4806,logical_constructions_per_run=2403,
 HNSW_per_run=9026816,HNSW_expected=36107264,builds_expected=19224,builds_cap=25000,topology_installations_expected=9612,score_vectors_fixed=True,native_instances_per_dataset=2,
 selection='original J over three deterministic Adam-direction radii and no-op; fixed original P online scores',gaussian_candidates_eligible_for_commit=False,
 momentum_updated_on_rejection=True,monitor_selection='same nonzero feasible checkpoint rule as E53',conservative_projection_seconds=projection,E53_seconds=duration,projection_latest_finish_epoch=1789218600,
 training_stop=TRAIN_STOP,latest_launch=LATEST_LAUNCH,threads=1,output_bytes=384*(1<<20),minimum_free_bytes=7*(1<<30)))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_CONSTRUCTION_ONLY_RL',NSG_calls=0,gradient_updates=0));print('E56 frozen, conservative projection',projection,flush=True)
