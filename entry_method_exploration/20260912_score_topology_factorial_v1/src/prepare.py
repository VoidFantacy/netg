from shared import *
import subprocess,ast
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before','bin']:(O/name).mkdir(exist_ok=True)
check(E47/'reviews/final_artifact_freeze.json');assert read(E47/'reviews/final_audit.json')['status']=='PASS'
freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(E47/'reviews/native_dependencies.json');shutil.copy2(E47/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/36_full_feedback_profile_rl.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
for f in files(O/'src'):
 if f.suffix=='.py':ast.parse(f.read_text(),filename=str(f))
argv=read(E37/'bin/environment.build.json')['argv'];argv=[str(O/'src/factorial_environment.cpp') if x==str(E37/'src/environment.cpp') else str(O/'bin/environment.so') if x==str(E37/'bin/environment.so') else x for x in argv]
started=time.monotonic()
with (O/'logs/build.log').open('w') as f:proc=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,timeout=180)
assert proc.returncode==0,'inspect isolated build.log'
dump(O/'bin/environment.build.json',dict(argv=argv,returncode=0,seconds=time.monotonic()-started,sha256=sha(O/'bin/environment.so'),included_cache_source=str(E46/'src/cache_environment.cpp')))
contexts=read(E44/'inputs/contexts.json');dump(O/'inputs/contexts.json',contexts)
def shape(top):
 header=top[:4].tolist();i=4;nodes=[]
 for _ in range(header[0]):
  label=int(top[i]);level=int(top[i+1]);i+=2;nodes.append((label,level))
  for _ in range(level+1):degree=int(top[i]);i+=degree+1
 assert i==len(top);return header,nodes
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();c=read(E37/'inputs'/ds/'config.json');c.update(native_call_cap=30000,native_hnsw_cap=1100000);dump(inp/'config.json',c)
 for rec in [x for x in contexts if x['dataset']==ds]:
  parent=E44/'results'/ds/f'{rec["step"]:04}';base=np.load(parent/'C/topology.npz')['topology'];ss=shape(base)
  assert digest(base)==rec['current_topology_sha']
  for a in range(8):
   top=np.load(parent/f'A{a}/topology.npz')['topology'];assert shape(top)==ss and digest(top)==rec['candidate_topology_sha'][a]
dump(O/'config.locked.json',dict(datasets=DS,steps=STEPS,seed=20260921,arm='rl',states=500,normal_builds=340,topology_installations=340,
 physical_graphs=100,NSG_hard_cap=60000,per_dataset_reserved_NSG=30000,endpoint_normal_NSG_expected=1333,parity_NSG_expected=4800,
 HNSW_expected=2051200,HNSW_hard_cap=2200000,train_queries=4096,optimizer_updates=0,threads=1,query_stop_epoch=QUERY_STOP,latest_launch_epoch=QUERY_STOP-600,
 followup_gate=dict(gain_fraction_min=.75,loss_fraction_max=.5,best_static_net_sum_nonworse=True,positive_gain_required=True,both_datasets_required=True)))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+files(O/'bin')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_SCORE_TOPOLOGY_FACTORIAL',optimizer_updates=0,NSG_calls=0))
print('E48 frozen: all endpoint H/labels/levels/entry/maxlevel exactly compatible',flush=True)
