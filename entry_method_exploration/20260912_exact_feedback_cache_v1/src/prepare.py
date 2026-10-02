from shared import *
import subprocess,ast
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
check(E45/'reviews/final_artifact_freeze.json');freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(E45/'reviews/native_dependencies.json');shutil.copy2(E45/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/34_mean_update_control.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
argv=read(E37/'bin/environment.build.json')['argv']
argv=[str(O/'src/cache_environment.cpp') if x==str(E37/'src/environment.cpp') else str(O/'bin/environment.so') if x==str(E37/'bin/environment.so') else x for x in argv]
started=time.monotonic()
with (O/'logs/build.log').open('w') as f:proc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert proc.returncode==0,'isolated cache environment build failed; inspect build.log'
dump(O/'bin/environment.build.json',dict(argv=argv,returncode=0,seconds=time.monotonic()-started,binary_sha=sha(O/'bin/environment.so'),included_original_source=str(E37/'src/environment.cpp')))
records=read(E44/'inputs/contexts.json');dump(O/'inputs/contexts.json',records)
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=4000,native_hnsw_cap=400000)
 inp=O/'inputs'/ds;inp.mkdir();dump(inp/'config.json',c)
dump(O/'config.locked.json',dict(datasets=DS,steps=STEPS,seed=20260921,arm='rl',query_rows='E37 train 0:4096',threads=1,
 NSG_hard_cap=CAP,NSG_expected=3061,normal_new_NSG_expected=1333,parity_NSG_expected=1728,HNSW_expected=738432,builds_expected=180,
 per_dataset_reserved_NSG=4000,reused_current_seed_rows=81920,full_candidate_reference_rows=655360,optimizer_updates=0,
 query_stop_epoch=QUERY_STOP,latest_launch_epoch=QUERY_STOP-600,
 gate=dict(exact_bit_recovery_required=True,candidate_new_NSG_fraction_max=.1,training_projection_factor=1.5,projection_fixed_overhead_seconds=600,projected_finish_before_epoch=1789212300)))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_EXACT_FEEDBACK_CACHE',optimizer_updates=0,NSG_calls=0))
print('E46 cache wrapper built and inputs frozen',flush=True)
