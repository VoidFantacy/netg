from shared import *
ds=sys.argv[1];assert ds in DS;threads(15);resources()
assert time.time()<TRAIN_STOP-3600,'insufficient time to launch full training process'
check(O/'reviews/prequery_freeze.json')
assert all(read(O/'reviews'/('preflight_'+x+'.json'))['status']=='PASS' for x in DS)
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
sys.path.insert(0,str(E37/'src'));from native import Native
c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(O/'inputs'/ds/'local_parameters.npz')['scale']
gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);base=dict(np.load(E37/'results'/ds/'baseline.npz'))
probe=np.r_[np.arange(512),np.arange(4096,5120)].astype(np.int32)
def stat(out,rows):
 h=score(out['ids'],gt[rows]);bb=subset(base,rows);u=utility(out,bb,gt[rows]);total=out['route_ndc'].astype(float)+out['graph_ndc'];t0=bb['route_ndc'].astype(float)+bb['graph_ndc'];dh=h.astype(int)-bb['hits']
 return dict(recall_pct=float(h.mean()*10),delta_recall_pp=float(dh.mean()*10),mean_U=float(u.mean()),
  gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),failure_queries=int((h==0).sum()),
  graph_NDC_change_pct=float((out['graph_ndc'].mean()/bb['graph_ndc'].mean()-1)*100),total_NDC_change_pct=float((total.mean()/t0.mean()-1)*100))
started_all=time.monotonic();native=Native(c);records=[]
try:
 for arm in ARMS:
  for seed in SEEDS:
   resources();assert time.time()<TRAIN_STOP
   name=f'train_{ds}_{arm}_{seed}';reserve(name,247680);before=native.stats();started=time.monotonic()
   dest=O/'models'/ds/f'{arm}_{seed}';dest.mkdir(parents=True);(dest/'trajectory').mkdir();(dest/'checkpoints').mkdir()
   schedule=dict(np.load(O/'inputs'/ds/f'schedule_{seed}.npz'));rng=np.random.default_rng(seed)
   mu=np.zeros((len(p),16));m=mu.copy();v=mu.copy();counts=np.zeros(len(p),np.int32);w=p.copy();curves=[];checkpoints=[];best=None;fallback=None
   for step in range(STEPS+1):
    assert time.time()<TRAIN_STOP and time.monotonic()-started_all<3600,'time limit; retain partial run and reservation'
    if step%20==0:
     resources();top=native.build(w);out=native.run(probe);drift=float(np.square(w.astype(float)-p).sum(1).mean())
     tr=stat({k:x[:512] for k,x in out.items()},probe[:512]);mo=stat({k:x[512:] for k,x in out.items()},probe[512:])
     rec=dict(step=step,train=tr,monitor=mo,feasible=mo['graph_NDC_change_pct']<=1,drift=drift,W_sha=digest(w),topology_sha=top,
        active_hubs=int((counts>0).sum()),max_updates_per_hub=int(counts.max()),seconds=time.monotonic()-started)
     save(dest/'checkpoints'/f'{step:04}.npz',mu=mu,m=m,v=v,counts=counts,W=w,**out);checkpoints.append(rec)
     if step:
      if fallback is None or mo['mean_U']>fallback['monitor']['mean_U']:fallback=rec
      if rec['feasible'] and (best is None or mo['mean_U']>best['monitor']['mean_U']):best=rec
     dump(dest/'checkpoints.json',checkpoints)
     dump(O/'state.json',dict(status='TRAINING_LOCAL_PROFILE_RL',dataset=ds,arm=arm,seed=seed,step=step,native=native.stats(),pid=os.getpid()))
     print('CHECKPOINT',ds,arm,seed,step,'train',tr['delta_recall_pp'],'monitor',mo['delta_recall_pp'],'active_hubs',rec['active_hubs'],flush=True)
     if step==STEPS:break
    st=step+1;rows=schedule['rows'][step];slot=int(schedule['slots'][step]);current_row=w[slot].copy()
    current_top=native.build(w);current=native.run(rows);current_drift=float(np.square(w.astype(float)-p).sum(1).mean());current_j=float(utility(current,subset(base,rows),gt[rows]).mean()-current_drift)
    eps=rng.normal(size=(POP if arm=='rl' else POP//2,16))
    if arm=='es':eps=np.r_[eps,-eps]
    actions=mu[slot][None,:]+SIGMA*eps;raw=[];rewards=[];drifts=[];tops=[];hashes=[];candidate_rows=[]
    for action in actions:
     w[slot]=row_profile(p[slot],b,scale[slot],action);candidate_rows.append(w[slot].copy());tops.append(native.build(w));hashes.append(digest(w))
     result=native.run(rows);raw.append(result)
     drift=float(np.square(w.astype(float)-p).sum(1).mean());drifts.append(drift)
     rewards.append(float(utility(result,subset(base,rows),gt[rows]).mean()-drift-current_j))
    w[slot]=current_row;rewards=np.array(rewards);g=gradient(arm,rewards,eps);counts[slot]+=1
    nm,nmom,nvar,gnorm=update(mu[slot],m[slot],v[slot],g,int(counts[slot]),st)
    next_row=row_profile(p[slot],b,scale[slot],nm)
    save(dest/'trajectory'/f'{st:04}.npz',rows=rows,slot=np.array(slot),eps=eps,actions=actions,mu_before=mu[slot],mu_after=nm,
      m_after=nmom,v_after=nvar,local_count=np.array(counts[slot]),current_row=current_row,next_row=next_row,candidate_rows=np.stack(candidate_rows),
      rewards=rewards,current_J=np.array(current_j),current_drift=np.array(current_drift),drift=np.array(drifts),gradient=g,
      current_topology_sha=np.array(current_top),topology_sha=np.array(tops),W_sha=np.array(hashes),
      **{'current_'+k:current[k] for k in FIELDS},**{k:np.stack([x[k] for x in raw]) for k in FIELDS})
    changed_hits=np.stack([score(x['ids'],gt[rows]).astype(int)-score(current['ids'],gt[rows]) for x in raw])
    curves.append(dict(step=st,slot=slot,mean_delta_J=float(rewards.mean()),max_delta_J=float(rewards.max()),min_delta_J=float(rewards.min()),
       gradient_norm=gnorm,hit_change_candidates=int(np.any(changed_hits!=0,axis=1).sum()),hit_changed_queries=int(np.any(changed_hits!=0,axis=0).sum()),
       local_count=int(counts[slot]),seconds=time.monotonic()-started))
    mu[slot]=nm;m[slot]=nmom;v[slot]=nvar;w[slot]=next_row
    if st%20==0:dump(dest/'training_curve.json',curves)
   chosen=best if best is not None else fallback;assert chosen is not None
   for tag,s in [('selected',chosen['step']),('last',STEPS)]:
    folder=dest/tag;folder.mkdir();cp=dict(np.load(dest/'checkpoints'/f'{s:04}.npz'));ww=cp['W'];top=native.build(ww);native.save(folder/'graph.hnsw');ww.tofile(folder/'W.f32');cp['mu'].tofile(folder/'mu.f64')
    assert top==next(x['topology_sha'] for x in checkpoints if x['step']==s)
    native.verify(folder/'graph.hnsw',np.r_[np.arange(32),np.arange(4096,4128)])
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    expected={k:np.r_[cp[k][:32],cp[k][512:544]] for k in FIELDS};equal(parity,expected);save(folder/'parity.npz',**parity)
    dump(folder/'identity.json',dict(step=s,W_sha=digest(ww),graph_sha=sha(folder/'graph.hnsw'),mu_sha=sha(folder/'mu.f64'),topology_sha=top,parity='PASS'))
   after=native.stats();cost={k:after[k]-before[k] for k in ['NSG_calls','HNSW_calls','builds','build_seconds']};assert cost['NSG_calls']==247680 and cost['builds']==1813
   rec=dict(dataset=ds,arm=arm,seed=seed,status='TRAINED',updates=200,selected_step=chosen['step'],monitor_gate_feasible=best is not None,
      selected=chosen,last=checkpoints[-1],active_hubs=int((counts>0).sum()),seconds=time.monotonic()-started,actual_threads=after['actual_threads'],**cost)
   dump(dest/'model.json',rec);finish(name,cost['NSG_calls'],native=cost,actual_threads=after['actual_threads'],seconds=rec['seconds']);records.append(rec)
   dump(O/'results'/ds/'training_summary.json',records);print('RUN_COMPLETE',ds,arm,seed,rec['selected_step'],cost,flush=True)
 assert native.stats()['NSG_calls']==990720 and native.stats()['builds']==7252
 dump(O/'results'/ds/'training_complete.json',dict(status='PASS',runs=4,updates=800,seconds=time.monotonic()-started_all,
    peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native=native.stats()))
finally:native.close()
