from shared import *
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','models','results','reviews','logs','figures','source_before']:(O/name).mkdir(exist_ok=True)
check(OLD[-1]/'reviews/final_artifact_freeze.json')
freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(OLD[2]/'reviews/native_dependencies.json')
shutil.copy2(OLD[2]/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/31_removed_profile_factorial.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c['native_call_cap']=1000000
 assert c['num_queries']==5120 and c['train']==4096 and c['monitor']==1024
 inp=O/'inputs'/ds;inp.mkdir();dump(inp/'config.json',c)
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
 np.testing.assert_allclose(b.T@b,np.eye(16),atol=1e-8)
 scale=np.linalg.norm(p.astype(float)@b,axis=1);assert np.all(scale>1e-12)
 save(inp/'local_parameters.npz',scale=scale)
 source=np.fromfile(c['row_ids'],np.int64);assert len(source)==len(set(map(int,source)))==5120
 hubs=np.fromfile(c['hub_ids'],np.int32);lookup={int(x):i for i,x in enumerate(hubs)}
 entries=np.load(E37/'results'/ds/'baseline.npz')['entries'][:4096].ravel()
 for seed in SEEDS:
  brng=np.random.default_rng(seed+1000);hrng=np.random.default_rng(seed+2000)
  rows=np.stack([brng.choice(4096,BATCH,replace=False) for _ in range(STEPS)]).astype(np.int32)
  draws=hrng.integers(len(entries),size=STEPS);slots=np.array([lookup[int(entries[i])] for i in draws],np.int32)
  save(inp/f'schedule_{seed}.npz',rows=rows,slots=slots,hub_ids=hubs[slots],independent_anchor_entry_draw=draws)
dump(O/'config.locked.json',dict(datasets=DS,arms=ARMS,seeds=SEEDS,steps=STEPS,population=POP,batch=BATCH,rank=RANK,sigma=SIGMA,
 NSG_hard_cap=CAP,NSG_expected=1992256,build_hard_cap=15000,expected_builds=14510,per_run_NSG=247680,
 deadline='2026-09-12T20:00:00+08:00',training_stop_epoch=TRAIN_STOP,latest_training_launch_epoch=TRAIN_STOP-3600,
 representation='independent H x 16 normalized local coefficients with frozen P/B/scales',threads=1))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_LOCAL_PROFILE_RL',optimizer_updates=0,NSG_calls=0))
print('E43 inputs/source/protocol frozen; target hub and query schedules GT-free and independent')
