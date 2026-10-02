from shared import *
threads(8);resources();assert not (O/'config.locked.json').exists()
for name in ['inputs','results','reviews','logs','figures','source_before']:(O/name).mkdir(exist_ok=True)
check(E44/'reviews/final_artifact_freeze_v2.json');freeze(O/'reviews/protected.json',[p for root in OLD for p in files(root)])
check(E44/'reviews/native_dependencies.json');shutil.copy2(E44/'reviews/native_dependencies.json',O/'reviews/native_dependencies.json')
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/33_local_sampling_diagnosis.md']:
 shutil.copy2(R/name,O/'source_before'/name.replace('/','__'))
records=[]
for ds in DS:
 c=read(E37/'inputs'/ds/'config.json');c['native_call_cap']=84000;inp=O/'inputs'/ds;inp.mkdir();dump(inp/'config.json',c)
 p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
 scale=np.load(E43/'inputs'/ds/'local_parameters.npz')['scale']
 for rec in [x for x in read(E44/'inputs/contexts.json') if x['dataset']==ds]:
  step=rec['step'];slot=rec['slot'];cp=dict(np.load(rec['checkpoint']));mu=cp['mu'];m=cp['m'];v=cp['v'];counts=cp['counts']
  source=E43/'models'/ds/'rl_20260921'/'trajectory'
  for k in range(((step-1)//20)*20+1,step):
   tt=dict(np.load(source/f'{k:04}.npz'));ss=int(tt['slot']);mu[ss]=tt['mu_after'];m[ss]=tt['m_after'];v[ss]=tt['v_after'];counts[ss]=tt['local_count']
  t=dict(np.load(rec['trajectory']));assert mu[slot].tobytes()==t['mu_before'].tobytes();assert counts[slot]+1==int(t['local_count'])
  w=np.fromfile(rec['current_W'],np.float32).reshape(p.shape);assert digest(w)==rec['current_W_sha']
  assert row_profile(p[slot],b,scale[slot],mu[slot]).tobytes()==w[slot].tobytes()
  gf=np.load(E44/'results'/ds/f'{step:04}'/'derived.npz')['full_gradient'];gb=t['gradient'];results={}
  for name,g in [('batch',gb),('full',gf)]:
   nm,nmom,nvar,gnorm=update(mu[slot],m[slot],v[slot],g,int(counts[slot])+1,step);nr=row_profile(p[slot],b,scale[slot],nm)
   results.update({name+'_mu':nm,name+'_m':nmom,name+'_v':nvar,name+'_row':nr,name+'_gradient':g,name+'_gradient_norm':np.array(gnorm)})
   if name=='batch':
    assert nm.tobytes()==t['mu_after'].tobytes() and nr.tobytes()==t['next_row'].tobytes()
    assert nmom.tobytes()==t['m_after'].tobytes() and nvar.tobytes()==t['v_after'].tobytes()
  save(inp/f'{step:04}_updates.npz',mu_before=mu[slot],m_before=m[slot],v_before=v[slot],count_before=np.array(counts[slot]),current_row=w[slot],**results)
  hashes={}
  for name in ['batch','full']:
   ww=w.copy();ww[slot]=results[name+'_row'];hashes[name]=digest(ww)
  records.append(dict(dataset=ds,step=step,slot=slot,hub=rec['hub'],current_W=rec['current_W'],current_W_sha=rec['current_W_sha'],
   current_topology_sha=rec['current_topology_sha'],current_raw=str(E44/'results'/ds/f'{step:04}'/'C/raw.npz'),
   trajectory=rec['trajectory'],checkpoint=rec['checkpoint'],updated_W_sha=hashes))
dump(O/'inputs/contexts.json',records)
dump(O/'config.locked.json',dict(datasets=DS,steps=STEPS,seed=20260921,arm='rl',query_rows='E37 train 0:4096',sigma=.3,
 NSG_hard_cap=CAP,NSG_expected=167040,HNSW_expected=166080,builds_expected=60,per_dataset_NSG=83520,
 continuous_training_updates=0,counterfactual_single_steps=20,historical_update_replays=20,threads=1,query_stop_epoch=QUERY_STOP,latest_launch_epoch=QUERY_STOP-600,
 gate=dict(full_net_hits_strictly_positive=True,full_mean_delta_U_strictly_positive=True,full_vs_batch_net_nonnegative=True,full_vs_batch_mean_U_strictly_positive=True,graph_NDC_increase_max_pct=1.)))
freeze(O/'reviews/prequery_freeze.json',files(O/'src')+files(O/'inputs')+[O/'protocol.md',O/'config.locked.json'])
dump(O/'state.json',dict(status='PREPARED_MEAN_UPDATE_CONTROL',counterfactual_single_steps=20,continuous_training_updates=0,NSG_calls=0))
print('E45 frozen 20 same-state gradient substitutions; all original Adam/next rows bit-exact',flush=True)
