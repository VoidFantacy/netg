from shared import *
threads(8);resources();resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
assert all(read(O/'results'/ds/'training_complete.json')['status']=='PASS' for ds in DS)
started=time.monotonic();check(O/'reviews/prequery_freeze.json');step_rows=[];run_rows=[]
totals=dict(updates=0,candidate_branches=0,deterministic_branches=0,accepted_restorations=0,candidate_W_hashes=0,checkpoints=0,return_set_scores=0,patch_return_set_scores=0,
 logical_candidate_rows=0,logical_deterministic_rows=0,exports=0,physical_parity_rows=0,cold_baseline_rows=0)
def ihits(ids,gg):return np.array([len(set(map(int,a))&set(map(int,b[:10]))) for a,b in zip(ids,gg)],np.uint8)
def independent_row(p,b,s,z):
 if not np.any(z):return p.copy()
 y=p.astype(float).copy()
 for j in range(16):y+=.0625*float(s)*float(np.tanh(z[j]))*b[:,j]
 y/=np.sqrt(np.dot(y,y));return y
def independent_gradient(arm,values,eps):
 g=[]
 for j in range(16):
  if arm=='rl':x=sum((float(values[i])-sum(float(values[k]) for k in range(8) if k!=i)/7)*float(eps[i,j]) for i in range(8))/(8*.3)
  else:x=sum((float(values[i])-float(values[i+4]))*float(eps[i,j]) for i in range(4))/(8*.3)
  g.append(x)
 return np.array(g)
def independent_adam(mu,m,v,g,n,step):
 scale=max(1.,sum(float(x)**2 for x in g)**.5);lr=.003+.0135*(1+np.cos(np.pi*(step-1)/199));nm=[];mm=[];vv=[]
 for j in range(16):
  x=float(g[j])/scale;mj=.9*float(m[j])+.1*x;vj=.999*float(v[j])+.001*x*x
  zj=float(mu[j])+lr*(mj/(1-.9**n))/((vj/(1-.999**n))**.5+1e-8);nm.append(max(-2.,min(2.,zj)));mm.append(mj);vv.append(vj)
 return np.array(nm),np.array(mm),np.array(vv)
def utility_independent(out,base):
 h=out['hits'].astype(float);hh=base['hits'].astype(float);total=out['route_ndc'].astype(float)+out['graph_ndc'];den=base['route_ndc'].astype(float)+base['graph_ndc']
 return h-hh-.1*((total-den)/den)-.1*((h==0).astype(int)-(hh==0).astype(int))
def rebuild(parent,t,prefix,route_counts,entry_sha,cache_sha,gt):
 rows=t[prefix+'rows'];assert rows.dtype==np.int32 and np.array_equal(rows,np.unique(rows)) and np.all((rows>=0)&(rows<4096))
 assert t[prefix+'entries'].shape==(len(rows),3) and np.all(np.diff(t[prefix+'entries'],axis=1)>0)
 assert np.all(np.any(t[prefix+'entries']!=parent['entries'][rows],axis=1))
 out={k:parent[k].copy() for k in FIELDS+['hits']};out['route_ndc']=route_counts
 for k in ['ids','distances','entries','graph_ndc','hits']:out[k][rows]=t[prefix+k]
 independent=ihits(t[prefix+'ids'],gt[rows]);assert np.array_equal(independent,t[prefix+'hits']);totals['return_set_scores']+=len(rows);totals['patch_return_set_scores']+=len(rows)
 assert digest(out['entries'])==str(entry_sha) and raw_digest(out)==str(cache_sha)
 return out
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
 scale=np.load(O/'inputs'/ds/'local_parameters.npz')['scale'];gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);anchor=dict(np.load(E37/'results'/ds/'baseline.npz'));base=subset(anchor,np.arange(4096))
 for arm in ARMS:
  for seed in SEEDS:
   src=O/'models'/ds/f'{arm}_{seed}';meta=read(src/'model.json');cps=read(src/'checkpoints.json');curve=read(src/'training_curve.json')
   schedule=dict(np.load(O/'inputs'/ds/f'schedule_{seed}.npz'));rng=np.random.default_rng(seed);mu=np.zeros((len(p),16));m=mu.copy();v=mu.copy();counts=np.zeros(len(p),np.int32);accepts=counts.copy();w=p.copy()
   cur=dict(np.load(src/'initial.npz'));equal(cur,base);assert np.array_equal(ihits(cur['ids'],gt[:4096]),cur['hits']);totals['return_set_scores']+=4096;totals['cold_baseline_rows']+=4096
   accumulated_dh=np.zeros(4096,np.int32);new_candidate=new_deterministic=0;current_top=cps[0]["topology_sha"]
   for step in range(201):
    if step%20==0:
     cp=dict(np.load(src/'checkpoints'/f'{step:04}.npz'));cm=next(x for x in cps if x['step']==step)
     for name,value in [('mu',mu),('m',m),('v',v),('counts',counts),('accepts',accepts),('W',w)]:assert cp[name].tobytes()==value.tobytes(),(ds,arm,seed,step,name)
     cpraw={k:cp[k] for k in FIELDS+['hits']};equal(subset(cpraw,np.arange(4096)),cur);assert raw_digest(cur)==cm['cache_sha'] and digest(w)==cm['W_sha'] and cm['topology_sha']==current_top
     h=ihits(cp['ids'],gt);assert np.array_equal(h,cp['hits']);totals['return_set_scores']+=5120;totals['checkpoints']+=1
     for name,rows in [('train',np.arange(512)),('full_train',np.arange(4096)),('monitor',np.arange(4096,5120))]:
      out=subset(cpraw,rows);bb=subset(anchor,rows);d=h[rows].astype(int)-bb['hits'];u=utility_independent(out,bb)
      np.testing.assert_allclose(cm[name]['delta_recall_pp'],float(d.mean()*10),atol=1e-14);np.testing.assert_allclose(cm[name]['mean_U'],float(u.mean()),atol=2e-15)
      assert cm[name]['gain_hits']==int(np.maximum(d,0).sum()) and cm[name]['loss_hits']==int(np.maximum(-d,0).sum())
      assert cm[name]['failure_queries']==int((h[rows]==0).sum())
      graph_change=(out['graph_ndc'].mean()/bb['graph_ndc'].mean()-1)*100
      total_change=((out['route_ndc'].astype(float)+out['graph_ndc']).mean()/(bb['route_ndc'].astype(float)+bb['graph_ndc']).mean()-1)*100
      np.testing.assert_allclose(cm[name]['graph_NDC_change_pct'],graph_change,atol=1e-12,rtol=0)
      np.testing.assert_allclose(cm[name]['total_NDC_change_pct'],total_change,atol=1e-12,rtol=0)
     assert cm['feasible']==(cm['monitor']['graph_NDC_change_pct']<=1)
     assert np.array_equal(accumulated_dh,h[:4096].astype(int)-base['hits'])
     if step==200:break
    st=step+1;t=dict(np.load(src/'trajectory'/f'{st:04}.npz'));slot=int(t['slot']);assert slot==int(schedule['slots'][step])
    for name,value in [('mu_before',mu[slot]),('m_before',m[slot]),('v_before',v[slot]),('current_row',w[slot])]:assert t[name].tobytes()==value.tobytes()
    assert raw_digest(cur)==str(t['current_cache_sha']) and str(t['current_topology_sha'])==current_top;eps=rng.normal(size=(8,16))
    assert eps.tobytes()==t['eps'].tobytes();np.testing.assert_array_equal(t['actions'],mu[slot][None]+.3*eps)
    oldeps=np.load(E47/'models'/ds/f'rl_{seed}'/'trajectory'/f'{st:04}.npz')['eps'];assert oldeps.tobytes()==eps.tobytes()
    drift0=float(np.einsum('ij,ij->',w.astype(float)-p,w.astype(float)-p)/len(p));j0=float(utility_independent(cur,base).mean()-drift0)
    np.testing.assert_allclose(drift0,t['current_drift'],atol=1e-17);np.testing.assert_allclose(j0,t['current_J'],atol=2e-15)
    rewards=[];quality=[];gc=[];gf=[];changed=[]
    for a in range(8):
     row=independent_row(p[slot],b,scale[slot],t['actions'][a]);np.testing.assert_allclose(row,t['candidate_rows'][a],atol=4e-8,rtol=1e-7)
     ww=w.copy();ww[slot]=t['candidate_rows'][a];assert digest(ww)==str(t['W_sha'][a]);totals['candidate_W_hashes']+=1
     out=rebuild(cur,t,f'a{a}_',t['route_ndc'][a],t['entries_sha'][a],t['cache_sha'][a],gt[:4096]);n=len(t[f'a{a}_rows']);assert n==int(t['new_NSG'][a]);new_candidate+=n
     drift=float(np.einsum('ij,ij->',ww.astype(float)-p,ww.astype(float)-p)/len(p));np.testing.assert_allclose(drift,t['drift'][a],atol=1e-17)
     rewards.append(float(utility_independent(out,base).mean()-drift-j0));dh=out['hits'].astype(int)-cur['hits'];quality.append(dh)
     den=base['route_ndc'].astype(float)+base['graph_ndc'];nd=(out['route_ndc'].astype(float)+out['graph_ndc'])-(cur['route_ndc'].astype(float)+cur['graph_ndc'])
     gc.append(float((-.1*nd/den).mean()));gf.append(float((-.1*((out['hits']==0).astype(int)-(cur['hits']==0).astype(int))).mean()));changed.append(n)
     totals['candidate_branches']+=1;totals['logical_candidate_rows']+=4096
    np.testing.assert_allclose(rewards,t['rewards'],atol=3e-15)
    g=independent_gradient('rl',t['rewards'],eps);np.testing.assert_allclose(g,t['gradient'],atol=2e-14)
    dhs=np.stack(quality);gh=independent_gradient('rl',dhs.mean(1),eps);gcost=independent_gradient('rl',gc,eps);gfail=independent_gradient('rl',gf,eps);gd=independent_gradient('rl',-t['drift']+t['current_drift'],eps)
    np.testing.assert_allclose(gh+gcost+gfail+gd,t['gradient'],atol=3e-14)
    counts[slot]+=1;assert counts[slot]==int(t['local_count']);adam,mm,vv=independent_adam(mu[slot],m[slot],v[slot],t['gradient'],int(counts[slot]),st)
    for name,value in [('adam_mu_proposal',adam),('m_after',mm),('v_after',vv)]:np.testing.assert_allclose(value,t[name],atol=2e-14)
    direction=t['adam_mu_proposal']-mu[slot];np.testing.assert_array_equal(direction,t['direction']);dn=sum(float(x)**2 for x in direction)**.5;unit=direction/dn if dn else np.zeros(16)
    radii=sorted(sum(float(x)**2 for x in row)**.5 for row in .3*eps);radius=(radii[3]+radii[4])/2;np.testing.assert_allclose(radius,t['radius'],atol=2e-15)
    douts=[];dvalues=[]
    for i,factor in enumerate([.25,.5,1.]):
     zz=np.clip(mu[slot]+factor*radius*unit,-2,2);np.testing.assert_allclose(zz,t['d_coeff'][i],atol=2e-15);np.testing.assert_allclose(mu[slot]+factor*radius*unit,t['d_unclipped'][i],atol=2e-15)
     row=independent_row(p[slot],b,scale[slot],t['d_coeff'][i]);np.testing.assert_allclose(row,t['d_rows'][i],atol=4e-8,rtol=1e-7)
     ww=w.copy();ww[slot]=t['d_rows'][i];assert digest(ww)==str(t['d_W_sha'][i])
     out=rebuild(cur,t,f'd{i}_',t['d_route_ndc'][i],t['d_entries_sha'][i],t['d_cache_sha'][i],gt[:4096]);n=len(t[f'd{i}_rows']);assert n==int(t['d_new_NSG'][i]);new_deterministic+=n
     drift=float(np.einsum('ij,ij->',ww.astype(float)-p,ww.astype(float)-p)/len(p));np.testing.assert_allclose(drift,t['d_drift'][i],atol=1e-17)
     value=float(utility_independent(out,base).mean()-drift-j0);np.testing.assert_allclose(value,t['d_rewards'][i],atol=4e-15);douts.append(out);dvalues.append(value)
     totals['deterministic_branches']+=1;totals['logical_deterministic_rows']+=4096
    values=[(-1,0.)]+[(i,float(t['d_rewards'][i])) for i in range(3)];choice=sorted(values,key=lambda x:(-x[1],x[0]))[0][0];assert choice==int(t['choice'])
    nm=mu[slot].copy() if choice<0 else t['d_coeff'][choice];row=w[slot].copy() if choice<0 else t['d_rows'][choice];assert nm.tobytes()==t['mu_after'].tobytes() and row.tobytes()==t['next_row'].tobytes()
    dj=0. if choice<0 else float(t['d_rewards'][choice]);assert dj==float(t['selected_delta_J']) and dj>=0
    if choice>=0:accepts[slot]+=1
    assert accepts[slot]==int(t['local_accepts'])
    nxt=cur if choice<0 else douts[choice];top=str(t['current_topology_sha']) if choice<0 else str(t['d_topology_sha'][choice]);assert top==str(t['accepted_topology_sha'])
    assert digest(nxt['entries'])==str(t['accepted_entries_sha']) and raw_digest(nxt)==str(t['accepted_cache_sha'])
    w[slot]=row;mu[slot]=nm;m[slot]=t['m_after'];v[slot]=t['v_after'];assert digest(w)==str(t['accepted_W_sha'])
    ah=nxt['hits'].astype(int)-cur['hits'];accumulated_dh+=ah;cr=curve[step]
    for key,value in [('choice',choice),('accepted_gain_hits',int(np.maximum(ah,0).sum())),('accepted_loss_hits',int(np.maximum(-ah,0).sum())),('accepted_net_hits',int(ah.sum())),('candidate_new_NSG',sum(changed)),('deterministic_new_NSG',int(t['d_new_NSG'].sum()))]:assert cr[key]==value
    afterdrift=float(np.einsum('ij,ij->',w.astype(float)-p,w.astype(float)-p)/len(p));ja=float(utility_independent(nxt,base).mean()-afterdrift);np.testing.assert_allclose(ja-j0,dj,atol=4e-15);assert ja>=j0-4e-15
    step_rows.append(dict(dataset=ds,arm=arm,seed=seed,step=st,slot=slot,choice=choice,radius=radius,original_Adam_step=dn,selected_delta_J=dj,gradient_norm=float(np.linalg.norm(g)),
     hit_gradient_norm=float(np.linalg.norm(gh)),cost_gradient_norm=float(np.linalg.norm(gcost)),failure_gradient_norm=float(np.linalg.norm(gfail)),drift_gradient_norm=float(np.linalg.norm(gd)),
     candidate_new_NSG=sum(changed),deterministic_new_NSG=int(t['d_new_NSG'].sum()),accepted_gain_hits=int(np.maximum(ah,0).sum()),accepted_loss_hits=int(np.maximum(-ah,0).sum()),accepted_net_hits=int(ah.sum()),J_after=ja))
    cur=nxt;current_top=top;totals['updates']+=1;totals['accepted_restorations']+=1
   eligible=[x for x in cps[1:] if x['feasible']];chosen=max(eligible or cps[1:],key=lambda x:x['monitor']['mean_U']);assert chosen['step']==meta['selected_step']
   for tag,st in [('selected',chosen['step']),('last',200)]:
    folder=src/tag;iden=read(folder/'identity.json');cp=dict(np.load(src/'checkpoints'/f'{st:04}.npz'))
    assert sha(folder/'W.f32')==digest(cp['W'])==iden['W_sha'];assert sha(folder/'mu.f64')==digest(cp['mu'])==iden['mu_sha'];assert sha(folder/'graph.hnsw')==iden['graph_sha']
    equal(dict(np.load(folder/'parity.npz')),{k:np.r_[cp[k][:32],cp[k][4096:4128]] for k in FIELDS});totals['exports']+=1;totals['physical_parity_rows']+=64
   assert meta['NSG_calls']==15744+new_candidate+new_deterministic and meta['HNSW_calls']==9026816 and meta['builds']==2403 and meta['actual_threads']==1
   run_rows.append(dict(dataset=ds,arm=arm,seed=seed,selected_step=chosen['step'],selected=chosen,last=cps[-1],NSG_calls=meta['NSG_calls'],HNSW_calls=meta['HNSW_calls'],builds=meta['builds'],
    candidate_new_NSG=new_candidate,deterministic_new_NSG=new_deterministic,accepted_updates=int(accepts.sum()),seconds=meta['seconds']))
assert totals['updates']==800 and totals['candidate_branches']==6400 and totals['deterministic_branches']==2400 and totals['checkpoints']==44 and totals['exports']==8
assert sum(x['NSG_calls'] for x in run_rows)==62976+sum(x['candidate_new_NSG']+x['deterministic_new_NSG'] for x in run_rows)
assert all(x['accepted_updates']==read(O/'models'/x['dataset']/f"rl_ls_{x['seed']}"/'model.json')['accepted_updates'] for x in run_rows)
dump(O/'results/training_analysis.json',dict(runs=run_rows,steps=step_rows,totals=totals))
dump(O/'reviews/training_verification.json',dict(status='PASS',**totals,source_and_inputs='prequery freeze verified',new_search=0,seconds=time.monotonic()-started))
print(json.dumps(read(O/'reviews/training_verification.json'),indent=2),flush=True)
