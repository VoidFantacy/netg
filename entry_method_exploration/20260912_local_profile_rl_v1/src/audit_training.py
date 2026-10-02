from shared import *
threads(8);resources();check(O/'reviews/prequery_freeze.json');started=time.monotonic()
assert all(read(O/'results'/ds/'training_complete.json')['status']=='PASS' for ds in DS)
all_steps=[];all_models=[];scored=0;updates=0;checkpoints_total=0;candidate_hashes=0
def direct_gradient(arm,reward,eps):
 if arm=='rl':
  return np.array([sum((float(reward[i])-sum(float(reward[k]) for k in range(8) if k!=i)/7)*float(eps[i,j]) for i in range(8))/(8*.3) for j in range(16)])
 return np.array([sum((float(reward[i])-float(reward[i+4]))*float(eps[i,j]) for i in range(4))/(8*.3) for j in range(16)])
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
 b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(O/'inputs'/ds/'local_parameters.npz')['scale']
 gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);truth=[set(map(int,row[:10])) for row in gt]
 base=dict(np.load(E37/'results'/ds/'baseline.npz'));baseh=np.array([len(set(map(int,ids))&truth[i]) for i,ids in enumerate(base['ids'])])
 assert np.array_equal(baseh,base['hits'])
 total0=base['route_ndc'].astype(float)+base['graph_ndc'];hubs=np.fromfile(c['hub_ids'],np.int32)
 def set_hits(ids,rows):
  global scored
  result=[]
  for ii,rr in zip(ids,rows):
   returned=set(map(int,ii));assert len(returned)==10 and len(truth[int(rr)])==10
   result.append(len(returned&truth[int(rr)]))
  scored+=len(result);return np.array(result,dtype=np.int16)
 def uvalue(raw,rows,hh):
  total=raw['route_ndc'].astype(float)+raw['graph_ndc']
  return hh-baseh[rows]-.1*(total/total0[rows]-1)-.1*((hh==0).astype(float)-(baseh[rows]==0).astype(float))
 for arm in ARMS:
  for seed in SEEDS:
   dest=O/'models'/ds/f'{arm}_{seed}';model=read(dest/'model.json');assert model['status']=='TRAINED'
   schedule=dict(np.load(O/'inputs'/ds/f'schedule_{seed}.npz'));rng=np.random.default_rng(seed)
   brng=np.random.default_rng(seed+1000);hrng=np.random.default_rng(seed+2000)
   original_entries=base['entries'][:4096].ravel();lookup={int(v):k for k,v in enumerate(hubs)}
   independent_draws=hrng.integers(len(original_entries),size=200)
   assert np.array_equal(schedule['rows'],np.stack([brng.choice(4096,128,replace=False) for _ in range(200)]))
   assert np.array_equal(schedule['slots'],[lookup[int(original_entries[i])] for i in independent_draws])
   mu=np.zeros((len(p),16));m=mu.copy();v=mu.copy();counts=np.zeros(len(p),np.int32);w=p.copy()
   cpmeta=read(dest/'checkpoints.json');probe=np.r_[np.arange(512),np.arange(4096,5120)]
   evaluated=[];trace=[]
   for step in range(201):
    if step%20==0:
     cp=dict(np.load(dest/'checkpoints'/f'{step:04}.npz'));meta=next(x for x in cpmeta if x['step']==step)
     assert cp['W'].tobytes()==w.tobytes() and digest(w)==meta['W_sha']
     assert np.array_equal(cp['counts'],counts)
     for key,val in [('mu',mu),('m',m),('v',v)]:np.testing.assert_allclose(cp[key],val,atol=3e-12,rtol=1e-11)
     hh=set_hits(cp['ids'],probe);uv=uvalue(cp,probe,hh)
     for key,sl in [('train',slice(0,512)),('monitor',slice(512,1536))]:
      rows=probe[sl];delta=hh[sl]-baseh[rows];met=meta[key]
      np.testing.assert_allclose(met['delta_recall_pp'],delta.mean()*10,atol=1e-12)
      np.testing.assert_allclose(met['mean_U'],uv[sl].mean(),atol=1e-12)
      assert met['gain_hits']==int(np.maximum(delta,0).sum()) and met['loss_hits']==int(np.maximum(-delta,0).sum())
      assert met['failure_queries']==int((hh[sl]==0).sum())
      np.testing.assert_allclose(met['graph_NDC_change_pct'],(cp['graph_ndc'][sl].mean()/base['graph_ndc'][rows].mean()-1)*100,atol=1e-12)
     assert meta['feasible']==bool(meta['monitor']['graph_NDC_change_pct']<=1)
     assert meta['active_hubs']==int((counts>0).sum()) and meta['max_updates_per_hub']==int(counts.max())
     drift=float(np.square(w.astype(float)-p).sum(1).mean());np.testing.assert_allclose(drift,meta['drift'],atol=1e-14)
     evaluated.append(meta);checkpoints_total+=1
     if step==200:break
    t=dict(np.load(dest/'trajectory'/f'{step+1:04}.npz'));rows=t['rows'];slot=int(t['slot']);assert slot==int(schedule['slots'][step])
    assert np.array_equal(rows,schedule['rows'][step]) and t['current_row'].tobytes()==w[slot].tobytes()
    eps=rng.normal(size=(8 if arm=='rl' else 4,16))
    if arm=='es':eps=np.r_[eps,-eps]
    assert eps.tobytes()==t['eps'].tobytes()
    np.testing.assert_allclose(t['actions'],mu[slot][None,:]+.3*eps,atol=2e-12,rtol=1e-11)
    np.testing.assert_allclose(t['mu_before'],mu[slot],atol=2e-12,rtol=1e-11)
    raw_current={k:t['current_'+k] for k in FIELDS};ch=set_hits(raw_current['ids'],rows)
    current_drift=np.square(w.astype(float)-p).sum(1).mean();current_j=uvalue(raw_current,rows,ch).mean()-current_drift
    np.testing.assert_allclose(current_j,t['current_J'],atol=2e-12)
    rewards=[];part_h=[];part_cost=[];part_failure=[];part_drift=[];hit_deltas=[];query_utilities=[]
    saved_row=w[slot].copy()
    for ai in range(8):
     z=t['actions'][ai];y=p[slot].astype(float)+.0625*scale[slot]*np.sum(np.tanh(z)[None,:]*b,axis=1)
     np.testing.assert_allclose(t['candidate_rows'][ai],y/np.sqrt(np.dot(y,y)),atol=4e-8,rtol=1e-7)
     w[slot]=t['candidate_rows'][ai];assert digest(w)==str(t['W_sha'][ai]);candidate_hashes+=1
     raw={k:t[k][ai] for k in FIELDS};hh=set_hits(raw['ids'],rows);uv=uvalue(raw,rows,hh)
     drift=np.square(w.astype(float)-p).sum(1).mean();np.testing.assert_allclose(drift,t['drift'][ai],atol=1e-14)
     rewards.append(uv.mean()-drift-current_j);hit_deltas.append(hh-ch);query_utilities.append(uv)
     part_h.append(float((hh-ch).mean()))
     part_cost.append(float((-.1*((raw['route_ndc'].astype(float)+raw['graph_ndc'])-(raw_current['route_ndc'].astype(float)+raw_current['graph_ndc']))/total0[rows]).mean()))
     part_failure.append(float((-.1*((hh==0).astype(float)-(ch==0).astype(float))).mean()))
     part_drift.append(float(current_drift-drift))
    w[slot]=saved_row;rewards=np.array(rewards);np.testing.assert_allclose(rewards,t['rewards'],atol=2e-12,rtol=1e-10)
    g=direct_gradient(arm,rewards,eps);np.testing.assert_allclose(g,t['gradient'],atol=1e-11,rtol=1e-9)
    parts=[direct_gradient(arm,np.array(x),eps) for x in [part_h,part_cost,part_failure,part_drift]]
    np.testing.assert_allclose(sum(parts),g,atol=1e-11,rtol=1e-9)
    counts[slot]+=1;assert int(t['local_count'])==counts[slot]
    clipped=g/max(1.,np.sqrt(np.dot(g,g)));m[slot]=.9*m[slot]+.1*clipped;v[slot]=.999*v[slot]+.001*clipped**2
    alpha=.003+.5*.027*(1+np.cos(np.pi*step/199))
    mu[slot]=np.minimum(2,np.maximum(-2,mu[slot]+alpha*(m[slot]/(1-.9**counts[slot]))/(np.sqrt(v[slot]/(1-.999**counts[slot]))+1e-8)))
    for key,val in [('mu_after',mu[slot]),('m_after',m[slot]),('v_after',v[slot])]:np.testing.assert_allclose(t[key],val,atol=3e-11,rtol=1e-8)
    y=p[slot].astype(float)+.0625*scale[slot]*np.sum(np.tanh(mu[slot])[None,:]*b,axis=1)
    if not np.any(mu[slot]):assert t['next_row'].tobytes()==p[slot].tobytes()
    else:np.testing.assert_allclose(t['next_row'],y/np.sqrt(np.dot(y,y)),atol=4e-8,rtol=1e-7)
    w[slot]=t['next_row'];delta=np.array(hit_deltas);qu=np.array(query_utilities)
    qg=(eps-eps.mean(0)).T@qu/(7*.3) if arm=='rl' else eps[:4].T@(qu[:4]-qu[4:])/(8*.3)
    np.testing.assert_allclose(qg.mean(1)+parts[3],g,atol=1e-11,rtol=1e-9)
    left=qg[:,:64].mean(1);right=qg[:,64:].mean(1);denom=np.linalg.norm(left)*np.linalg.norm(right)
    half_cos=float(np.dot(left,right)/denom) if denom>1e-30 else None
    conditional_noise=float(np.square(qg-qg.mean(1,keepdims=True)).sum()/(127*128)*(1-128/4096))
    trace.append(dict(dataset=ds,arm=arm,seed=seed,step=step+1,slot=slot,local_count=int(counts[slot]),
      hit_change_candidates=int(np.any(delta!=0,axis=1).sum()),hit_changed_queries=int(np.any(delta!=0,axis=0).sum()),
      positive_net_candidates=int((delta.sum(1)>0).sum()),negative_net_candidates=int((delta.sum(1)<0).sum()),
      positive_reward_candidates=int((rewards>0).sum()),mean_reward=float(rewards.mean()),max_reward=float(rewards.max()),
      hit_gradient_norm=float(np.linalg.norm(parts[0])),cost_gradient_norm=float(np.linalg.norm(parts[1])),
      failure_gradient_norm=float(np.linalg.norm(parts[2])),drift_gradient_norm=float(np.linalg.norm(parts[3])),gradient_norm=float(np.linalg.norm(g)),
      query_half_cosine_excluding_drift=half_cos,conditional_query_noise_trace=conditional_noise,
      conditional_denoised_signal_sq=float(np.dot(qg.mean(1),qg.mean(1))-conditional_noise),
      current_next_row_distance=float(np.linalg.norm(w[slot].astype(float)-saved_row)),candidate_mean_distance=float(np.mean(np.linalg.norm(t['candidate_rows'].astype(float)-saved_row,axis=1)))))
    updates+=1
   feasible=[x for x in evaluated[1:] if x['feasible']];pool=feasible or evaluated[1:]
   chosen=max(pool,key=lambda x:(x['monitor']['mean_U'],-x['step']))
   assert chosen['step']==model['selected_step'] and model['monitor_gate_feasible']==bool(feasible)
   for tag,step in [('selected',chosen['step']),('last',200)]:
    folder=dest/tag;cp=dict(np.load(dest/'checkpoints'/f'{step:04}.npz'));ident=read(folder/'identity.json')
    assert sha(folder/'W.f32')==digest(cp['W'])==ident['W_sha'] and sha(folder/'mu.f64')==digest(cp['mu'])==ident['mu_sha']
    assert sha(folder/'graph.hnsw')==ident['graph_sha'] and ident['parity']=='PASS'
    parity=dict(np.load(folder/'parity.npz'));equal(parity,{k:np.r_[cp[k][:32],cp[k][512:544]] for k in FIELDS})
   all_steps.extend(trace)
   all_models.append(dict(dataset=ds,arm=arm,seed=seed,selected_step=model['selected_step'],active_hubs=int((counts>0).sum()),
      min_active_updates=int(counts[counts>0].min()),median_active_updates=float(np.median(counts[counts>0])),max_active_updates=int(counts.max()),
      steps_with_hit_feedback=sum(x['hit_change_candidates']>0 for x in trace),candidates_with_hit_feedback=sum(x['hit_change_candidates'] for x in trace),
      steps_with_hit_gradient=sum(x['hit_gradient_norm']>1e-12 for x in trace),
      selected_train=chosen['train'],selected_monitor=chosen['monitor'],last_train=evaluated[-1]['train'],last_monitor=evaluated[-1]['monitor']))
   print('VERIFIED',ds,arm,seed,'updates',updates,'scored',scored,flush=True)
assert updates==1600 and checkpoints_total==88 and candidate_hashes==12800 and scored==1978368
for name,rows in [('steps.csv',all_steps),('training_models.csv',[{k:v for k,v in x.items() if not isinstance(v,dict)} for x in all_models])]:
 with (O/'results'/name).open('x') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
dump(O/'results/training_analysis.json',dict(models=all_models,scored=scored,updates=updates))
dump(O/'reviews/training_verification.json',dict(status='PASS',scored=scored,updates=updates,checkpoints=checkpoints_total,
 candidate_W_hashes=candidate_hashes,selected_last_models=16,three_way_parity_queries=1024,gradient_components=4,
 source_and_inputs='prequery_freeze verified',new_search=0,seconds=time.monotonic()-started))
print(json.dumps(read(O/'reviews/training_verification.json')),flush=True)
