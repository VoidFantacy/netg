from shared import *
threads(8); resources(); assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before']:(O/name).mkdir(exist_ok=True)
check(E43/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(E43/'reviews/native_dependencies.json')
shutil.copy2(E43/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/32_local_profile_rl.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
contexts=[]
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c['native_call_cap']=370000
 assert c['num_queries']==5120 and c['train']==4096 and c['monitor']==1024
 inp=O/'inputs'/ds;inp.mkdir();dump(inp/'config.json',c)
 hubs=np.fromfile(c['hub_ids'],np.int32);anchor=np.load(E37/'results'/ds/'baseline.npz')['entries'][:4096]
 src=E43/'models'/ds/'rl_20260921'
 for step in STEPS:
  previous=((step-1)//20)*20;cp=src/'checkpoints'/f'{previous:04}.npz';w=np.load(cp)['W'].copy()
  for k in range(previous+1,step):
   t=np.load(src/'trajectory'/f'{k:04}.npz');w[int(t['slot'])]=t['next_row']
  path=src/'trajectory'/f'{step:04}.npz';t=dict(np.load(path));slot=int(t['slot']);hub=int(hubs[slot])
  assert w[slot].tobytes()==t['current_row'].tobytes()
  near=(anchor==hub).any(1);n1=int(near.sum());n0=4096-n1;assert n1>0
  s1=min(64,n1) if n0 else 128;s0=128-s1;assert s1<=n1 and s0<=n0
  wp=inp/f'{step:04}_current.f32';w.tofile(wp)
  for a in range(8):
   ww=w.copy();ww[slot]=t['candidate_rows'][a];assert digest(ww)==str(t['W_sha'][a])
  save(inp/f'{step:04}_context.npz',near=near,candidate_rows=t['candidate_rows'],eps=t['eps'],actions=t['actions'],old_rows=t['rows'])
  rec=dict(dataset=ds,step=step,slot=slot,hub=hub,near_population=n1,far_population=n0,near_sample=s1,far_sample=s0,
   current_W=str(wp),current_W_sha=digest(w),trajectory=str(path),trajectory_sha=sha(path),checkpoint=str(cp),checkpoint_sha=sha(cp),
   current_topology_sha=str(t['current_topology_sha']),candidate_W_sha=t['W_sha'].tolist(),candidate_topology_sha=t['topology_sha'].tolist())
  contexts.append(rec)
dump(O/'inputs/contexts.json',contexts)
dump(O/'config.locked.json',dict(datasets=DS,arm='rl',seed=20260921,steps=STEPS,population=8,train_queries=4096,batch=128,sigma=.3,
 NSG_hard_cap=CAP,NSG_expected=739008,HNSW_expected=738432,builds_expected=180,per_dataset_NSG=369504,
 query_stop_epoch=QUERY_STOP,latest_launch_epoch=QUERY_STOP-900,timeout_seconds=900,threads=1,
 gate=dict(min_quality_contexts=4,variance_ratio_max=.5,nonworse_fraction_min=.6,variance_epsilon=1e-18),
 estimator='GT-free anchor-entry strata, fixed near quota 64, population weighting',optimizer_updates=0))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_LOCAL_SAMPLING_DIAGNOSIS',optimizer_updates=0,NSG_calls=0))
print('E44 frozen',len(contexts),'contexts; near counts',[(x['dataset'],x['step'],x['near_population']) for x in contexts],flush=True)
