from model import *
assert read(O/'state.json')['status']=='TRAINING_COMPLETE_VERIFY_PENDING';check(O/'reviews/models_after_training.json');check(O/'reviews/before_training.json')
def expected_numpy(f,values):
 logits=f[:,NEXT];logits-=logits.max(axis=-1,keepdims=True);p=np.exp(logits);p/=p.sum(axis=-1,keepdims=True);v=values
 for _ in range(3):v=p[:,:,0,None]*values+(p[:,:,1:,None]*v[:,NEXT[:,1:]]).sum(axis=2)
 return v[:,0]
records=[];regress=[]
for ds in DS:
 p=O/'results'/('labels_'+ds);data=np.load(p/'scored.npz');raw=np.fromfile(p/'features.f32',np.float32).reshape(2048,56,76).astype(float);u=data['utility'];hits=data['hits'];ndc=data['graph_ndc'];values=np.stack([u,hits,ndc],axis=-1).astype(float)
 source=np.fromfile(O/'inputs'/ds/'source_local.i32',np.int32);old=E33/'results'/ds/'baseline.npz';provenance=next(x for x in read(E34/'reviews/E33_preserved.json')['files'] if x['path']==str(old));assert sha(old)==provenance['sha256'];base=np.load(old)
 ids=np.fromfile(p/'ids.i32',np.int32).reshape(2048,56,10);dist=np.fromfile(p/'distances.f32',np.float32).reshape(2048,56,10);ent=np.fromfile(p/'entries.i32',np.int32).reshape(2048,56,3)
 for a,b in [(ids[:,0],base['ids'][source]),(dist[:,0],base['distances'][source]),(ent[:,0],base['entries'][source]),(ndc[:,0],base['graph_ndc'][source]),(data['route_ndc'],base['route_ndc'][source]),(hits[:,0],base['hits'][source])]:assert np.array_equal(a,b),(ds,'baseline mismatch')
 regress.append(identity(old))
 for arm in ARMS:
  for seed in SEEDS:
   dest=O/'models'/ds/f'{arm}_{seed}';checks=read(dest/'checkpoints.json');curve=read(dest/'training_curve.json');sel=read(dest/'selected.json');assert len(checks)==31 and len(curve)==3000
   expected_mean=raw[:1792].mean(axis=(0,1));expected_scale=np.maximum(raw[:1792].std(axis=(0,1)),1e-6);max_forward=0.;max_value=0.;stats=[]
   for rec in checks:
    step=rec['step'];folder=dest/f'checkpoint_{step:04}';m=read(folder/'model.json');assert m['step']==step and np.array_equal(m['mean'],expected_mean) and np.array_equal(m['scale'],expected_scale)
    f=numpy_forward(raw,m);state,action=greedy(f);saved=np.load(folder/'prediction.npz');assert np.array_equal(state,saved['states']) and np.array_equal(action,saved['actions'])
    ix=np.arange(2048);terminal=state[:,-1];assert np.array_equal(hits[ix,terminal],saved['greedy_hits']) and np.array_equal(ndc[ix,terminal],saved['greedy_ndc']) and np.array_equal(u[ix,terminal],saved['greedy_utility'])
    ev=expected_numpy(f,values);error=float(np.abs(ev-saved['expected']).max());max_value=max(max_value,error);assert error<1e-8
    for role,sl in [('train',slice(0,1792)),('monitor',slice(1792,None)),('full_fit',slice(None))]:
     rr=rec[role];dh=hits[ix,terminal][sl].astype(float)-hits[sl,0]
     assert abs(rr['delta_recall_pp']-dh.mean()*10)<1e-12 and abs(rr['utility']-u[ix,terminal][sl].mean())<1e-12
     assert abs(rr['expected_utility']-ev[sl,0].mean())<1e-10 and abs(rr['graph_change_pct']-(ndc[ix,terminal][sl].mean()/ndc[sl,0].mean()-1)*100)<1e-10
    if step==0:assert not terminal.any() and all(not np.array(v).any() for k,v in m['parameters'].items() if k.startswith('net.4'))
    if step in [0,sel['best']['step'],3000]:
     pt=torch.load(folder/'checkpoint.pt',map_location='cpu',weights_only=False)
     for k,v in pt['model'].items():assert np.array_equal(v.numpy(),m['parameters'][k])
     if step:assert all(float(z['step'])==step for z in pt['optimizer']['state'].values())
   pool=[c for c in checks[1:] if c['monitor']['graph_change_pct']<=1.] or checks[1:];best=max(pool,key=lambda c:c['monitor']['utility']);assert best==sel['best']
   assert sha(dest/'selected/model.json')==sha(Path(best['path'])/'model.json') and sha(dest/'selected/prediction.npz')==sha(Path(best['path'])/'prediction.npz')
   for i,z in enumerate(curve,1):assert z['step']==i and np.isfinite(z['loss']) and np.isfinite(z['gradient_norm']) and z['gradient_norm']>=0
   trajectory_checks=0;max_lp=0.;max_ema=0.
   if arm=='rl':
    b=np.zeros((2048,56));brng=np.random.default_rng(seed);arng=np.random.default_rng(seed+1000)
    for begin in range(1,3001,100):
     trace=np.load(dest/'trajectories'/f'{begin:04}_{begin+99:04}.npz');previous_model=read(dest/f'checkpoint_{begin-1:04}/model.json');assert trace['rows'].shape==(100,64)
     for j in range(100):
      step=begin+j;rows=trace['rows'][j].astype(np.int64);assert np.array_equal(rows,brng.choice(1792,64,replace=False));assert int(trace['step'][j])==step
      states=trace['states'][j].astype(np.int64);actions=trace['actions'][j];assert not states[:,0].any();valid=actions>=0;vals=u[rows[:,None],states];rewards=np.diff(vals,axis=1);returns=(vals[:,-1,None]-vals[:,:3])*valid
      assert np.array_equal(rewards,trace['rewards'][j]) and np.array_equal(returns,trace['returns'][j]);adv=(returns-b[rows[:,None],states[:,:3]])*valid;assert np.array_equal(adv,trace['advantages'][j])
      assert np.allclose(rewards.sum(axis=1),vals[:,-1],atol=2e-15)
      alive=np.ones(64,bool)
      if j==0:f=numpy_forward(raw[rows],previous_model)
      for t in range(3):
       uniform=arng.random(64);assert np.array_equal(valid[:,t],alive)
       assert np.array_equal(states[alive,t+1],NEXT[states[alive,t],actions[alive,t]]) and np.array_equal(states[~alive,t+1],states[~alive,t])
       if j==0:
        logits=f[np.arange(64)[:,None],NEXT[states[:,t]]];a=logits.max(axis=1,keepdims=True);lp=logits-a-np.log(np.exp(logits-a).sum(axis=1,keepdims=True));prob=np.exp(lp);chosen=np.minimum(15,(uniform[:,None]>=np.cumsum(prob,axis=1)).sum(axis=1));assert np.array_equal(chosen[alive],actions[alive,t]);expected_lp=lp[np.arange(64),np.maximum(actions[:,t],0)]*alive;max_lp=max(max_lp,float(np.abs(expected_lp-trace['log_probabilities'][j,:,t]).max()))
       alive &= actions[:,t]>0
      # Independent dictionary grouping of historical state-return EMA.
      groups={}
      for i,t in zip(*np.nonzero(valid)):groups.setdefault((int(rows[i]),int(states[i,t])),[]).append(float(returns[i,t]))
      for (q,s),rr in groups.items():b[q,s]+=.05*(sum(rr)/len(rr)-b[q,s])
      trajectory_checks+=64
     saved_b=np.load(dest/f'checkpoint_{begin+99:04}/baselines.npz')['baseline'];error=float(np.abs(saved_b-b).max());max_ema=max(max_ema,error);assert error<1e-12
    assert max_lp<2e-9 and trajectory_checks==192000
   records.append(dict(dataset=ds,arm=arm,seed=seed,updates=3000,checkpoints=31,all_checkpoint_greedy_and_value_verified=True,max_expected_value_error=max_value,trajectory_episodes_verified=trajectory_checks,max_checkpoint_policy_logprob_error=max_lp,max_EMA_error=max_ema,selected_step=best['step']))
  for seed in SEEDS:
   a=read(O/'models'/ds/f'rl_{seed}/checkpoint_0000/model.json');b=read(O/'models'/ds/f'exact_{seed}/checkpoint_0000/model.json');assert a['parameters']==b['parameters']
dump(O/'reviews/training_verification.json',dict(status='PASS',runs=records,baseline_regression_outputs=4096,baseline_sources=regress,optimizer_updates=24000,NSG_calls=0))
dump(O/'state.json',dict(status='TRAINING_VERIFIED_DEPLOYMENT_PENDING',training_runs=8,optimizer_updates=24000,validation_read=False,heldout_read=False));print('TRAINING_VERIFICATION_PASS',records,flush=True)
