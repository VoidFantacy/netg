from shared import *
import ast
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','models','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
check(E46/'reviews/final_artifact_freeze.json');assert read(E46/'results_v2/gate.json')['status']=='PASS_EXACT_FEEDBACK_CACHE_AND_TRAINING_PROJECTION'
freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(E46/'reviews/native_dependencies.json');shutil.copy2(E46/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/35_exact_feedback_cache.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
shutil.copy2(E46/'bin/environment.so',O/'bin/environment.so');assert sha(O/'bin/environment.so')==sha(E46/'bin/environment.so')
dump(O/'bin/provenance.json',dict(source=str(E46/'bin/environment.so'),sha256=sha(O/'bin/environment.so'),new_compile=False,interface_source=str(E46/'src/cache_environment.cpp')))
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=400000,native_hnsw_cap=30000000);dump(inp/'config.json',c)
 shutil.copy2(E43/'inputs'/ds/'local_parameters.npz',inp/'local_parameters.npz')
 for seed in SEEDS:shutil.copy2(E43/'inputs'/ds/f'schedule_{seed}.npz',inp/f'schedule_{seed}.npz')
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
projection=read(E46/'results_v2/gate.json')['projected_training_seconds'];assert time.time()+projection<1789212300,'insufficient conservative projection before19:25'
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=200,population=8,full_train_queries=4096,rank=16,sigma=.3,
 NSG_hard_cap=800000,per_run_reserved_NSG=100000,HNSW_expected=59107328,HNSW_hard_cap=60000000,builds_expected=14424,build_hard_cap=15000,
 per_run_fixed_NSG=15744,per_run_HNSW=7388416,per_run_builds=1803,optimizer_updates_expected=1600,threads=1,
 train_stop_epoch=TRAIN_STOP,conservative_projection_seconds=projection,projection_latest_finish_epoch=1789212300,
 checkpoint_rows='train4096 + monitor1024, aligned E37 original5120',new_GT=0,new_development_queries=0,QPS_points=0))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_FULL_FEEDBACK_PROFILE_RL',optimizer_updates=0,NSG_calls=0))
print('E47 full-feedback RL/ES frozen; original schedule and cache binary preserved; projection fits',flush=True)
