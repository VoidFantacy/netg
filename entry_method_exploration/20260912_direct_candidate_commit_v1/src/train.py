from shared import *
from native_cached import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json')
config=read(O/'config.locked.json');assert time.time()<LATEST_LAUNCH
if ds==DS[0]:assert time.time()+config['conservative_projection_seconds']<config['projection_latest_finish_epoch']
else:
 previous=read(O/'results'/DS[0]/'training_complete.json');assert time.time()+1.5*previous['seconds']+300<TRAIN_STOP,'insufficient time for matched second dataset'
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16)
scale=np.load(O/'inputs'/ds/'local_parameters.npz')['scale'];gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)
anchor=dict(np.load(E37/'results'/ds/'baseline.npz'));base=subset(anchor,np.arange(4096));allrows=np.arange(4096,dtype=np.int32)
started_all=time.monotonic();native=Native(c);records=[]
def stat(out,rows):
 h=out['hits'];bb=subset(anchor,rows);u=fast_utility(out,bb);total=out['route_ndc'].astype(float)+out['graph_ndc'];t0=bb['route_ndc'].astype(float)+bb['graph_ndc'];dh=h.astype(int)-bb['hits']
 return dict(recall_pct=float(h.mean()*10),delta_recall_pp=float(dh.mean()*10),mean_U=float(u.mean()),gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),
  failure_queries=int((h==0).sum()),graph_NDC_change_pct=float((out['graph_ndc'].mean()/bb['graph_ndc'].mean()-1)*100),total_NDC_change_pct=float((total.mean()/t0.mean()-1)*100))
def ensure(n):
 assert time.time()<TRAIN_STOP and time.monotonic()-started_all<1800,'time limit; retain partial run and reservation'
 assert native.stats()['NSG_calls']-before['NSG_calls']+n<=100000,'per-run NSG reservation exhausted'
def evaluate_cached(ww,parent):
 ensure(0);top=native.build(ww);route=native.route(allrows);changed=np.flatnonzero((route['entries']!=parent['entries']).any(1)).astype(np.int32)
 ensure(len(changed));new=native.search_entries(changed,route['entries'][changed]);new['hits']=score(new['ids'],gt[changed])
 out={k:parent[k].copy() for k in ['ids','distances','graph_ndc','hits']};out.update(route)
 for k in new:out[k][changed]=new[k]
 patch=dict(rows=changed,entries=route['entries'][changed],**new)
 meta=dict(topology_sha=top,W_sha=digest(ww),entries_sha=digest(route['entries']),cache_sha=raw_digest(out),new_NSG=len(changed))
 return out,patch,meta
try:
 for arm in ARMS:
  for seed in SEEDS:
   resources();ensure(0) if records else None
   name=f'train_{ds}_{arm}_{seed}';reserve(name,100000);before=native.stats();started=time.monotonic()
   dest=O/'models'/ds/f'{arm}_{seed}';dest.mkdir(parents=True);(dest/'trajectory').mkdir();(dest/'checkpoints').mkdir()
   schedule=dict(np.load(O/'inputs'/ds/f'schedule_{seed}.npz'));rng=np.random.default_rng(seed)
   mu=np.zeros((len(p),16));m=mu.copy();v=mu.copy();counts=np.zeros(len(p),np.int32);commits=counts.copy();w=p.copy();curves=[];checkpoints=[];best=fallback=None
   ensure(4096);current_top=native.build(w);current=native.run(allrows);equal(current,base);current['hits']=score(current['ids'],gt[:4096]);assert np.array_equal(current['hits'],base['hits'])
   save(dest/'initial.npz',**current)
   for step in range(201):
    ensure(0)
    if step%20==0:
     resources();ensure(1024);monitor=native.run(np.arange(4096,5120,dtype=np.int32));monitor['hits']=score(monitor['ids'],gt[4096:])
     out={k:np.concatenate([current[k],monitor[k]]) for k in FIELDS+['hits']};drift=float(np.square(w.astype(float)-p).sum(1).mean())
     tr=stat(subset(current,np.arange(512)),np.arange(512));ft=stat(current,allrows);mo=stat(monitor,np.arange(4096,5120))
     rec=dict(step=step,train=tr,full_train=ft,monitor=mo,feasible=mo['graph_NDC_change_pct']<=1,drift=drift,W_sha=digest(w),topology_sha=current_top,
      cache_sha=raw_digest(current),active_hubs=int((counts>0).sum()),max_updates_per_hub=int(counts.max()),seconds=time.monotonic()-started)
     save(dest/'checkpoints'/f'{step:04}.npz',mu=mu,m=m,v=v,counts=counts,commits=commits,W=w,**out);checkpoints.append(rec)
     if step:
      if fallback is None or mo['mean_U']>fallback['monitor']['mean_U']:fallback=rec
      if rec['feasible'] and (best is None or mo['mean_U']>best['monitor']['mean_U']):best=rec
     dump(dest/'checkpoints.json',checkpoints);dump(dest/'training_curve.json',curves)
     dump(O/'state.json',dict(status='TRAINING_DIRECT_CANDIDATE_COMMIT',dataset=ds,arm=arm,seed=seed,step=step,native=native.stats(),pid=os.getpid()))
     print('CHECKPOINT',ds,arm,seed,step,'train',tr['delta_recall_pp'],'full_train',ft['delta_recall_pp'],'monitor',mo['delta_recall_pp'],'NSG_run',native.stats()['NSG_calls']-before['NSG_calls'],flush=True)
     if step==200:break
    st=step+1;slot=int(schedule['slots'][step]);current_row=w[slot].copy();current_drift=float(np.square(w.astype(float)-p).sum(1).mean());current_j=float(fast_utility(current,base).mean()-current_drift)
    current_hash=raw_digest(current);eps=rng.normal(size=(8,16))
    actions=mu[slot][None,:]+.3*eps;rewards=[];drifts=[];candidate_rows=[];metas=[];routes=[];payload={};quality_deltas=[];candidate_outputs=[]
    for i,action in enumerate(actions):
     w[slot]=row_profile(p[slot],b,scale[slot],action);candidate_rows.append(w[slot].copy());out,patch,meta=evaluate_cached(w,current)
     drift=float(np.square(w.astype(float)-p).sum(1).mean());drifts.append(drift);rewards.append(float(fast_utility(out,base).mean()-drift-current_j))
     metas.append(meta);routes.append(out['route_ndc']);quality_deltas.append(out['hits'].astype(int)-current['hits']);candidate_outputs.append(out)
     payload.update({f'a{i}_'+k:x for k,x in patch.items()})
    w[slot]=current_row;rewards=np.array(rewards);eligible=np.all(np.abs(actions)<=2,axis=1)
    options=[-1]+[i for i in range(8) if eligible[i]];choice=max(options,key=lambda i:(0. if i<0 else float(rewards[i]),-i))
    nm=mu[slot].copy() if choice<0 else actions[choice].copy();next_row=current_row.copy() if choice<0 else candidate_rows[choice].copy()
    next_current=current if choice<0 else candidate_outputs[choice];selected_delta_J=0. if choice<0 else float(rewards[choice]);assert selected_delta_J>=0
    selected_top=current_top if choice<0 else metas[choice]['topology_sha'];w[slot]=next_row;restored_top=native.build(w);assert restored_top==selected_top
    counts[slot]+=1
    if choice>=0:commits[slot]+=1
    committed_dh=next_current['hits'].astype(int)-current['hits']
    save(dest/'trajectory'/f'{st:04}.npz',slot=np.array(slot),eps=eps,actions=actions,mu_before=mu[slot],mu_after=nm,local_count=np.array(counts[slot]),local_commits=np.array(commits[slot]),
     current_row=current_row,next_row=next_row,candidate_rows=np.stack(candidate_rows),rewards=rewards,current_J=np.array(current_j),current_drift=np.array(current_drift),drift=np.array(drifts),
     eligible=eligible,choice=np.array(choice),selected_delta_J=np.array(selected_delta_J),current_topology_sha=np.array(current_top),current_cache_sha=np.array(current_hash),
     topology_sha=np.array([x['topology_sha'] for x in metas]),W_sha=np.array([x['W_sha'] for x in metas]),entries_sha=np.array([x['entries_sha'] for x in metas]),cache_sha=np.array([x['cache_sha'] for x in metas]),
     route_ndc=np.stack(routes),new_NSG=np.array([x['new_NSG'] for x in metas]),commit_topology_sha=np.array(restored_top),commit_W_sha=np.array(digest(w)),
     commit_entries_sha=np.array(digest(next_current['entries'])),commit_cache_sha=np.array(raw_digest(next_current)),**payload)
    dh=np.stack(quality_deltas);curves.append(dict(step=st,slot=slot,choice=choice,eligible_candidates=int(eligible.sum()),mean_candidate_delta_J=float(rewards.mean()),max_candidate_delta_J=float(rewards.max()),
     selected_delta_J=selected_delta_J,hit_change_candidates=int((dh!=0).any(1).sum()),hit_changed_queries=int((dh!=0).any(0).sum()),candidate_new_NSG=sum(x['new_NSG'] for x in metas),
     commit_gain_hits=int(np.maximum(committed_dh,0).sum()),commit_loss_hits=int(np.maximum(-committed_dh,0).sum()),commit_net_hits=int(committed_dh.sum()),
     local_count=int(counts[slot]),local_commits=int(commits[slot]),seconds=time.monotonic()-started))
    mu[slot]=nm;current=next_current;current_top=restored_top
   chosen=best if best is not None else fallback;assert chosen is not None
   for tag,s in [('selected',chosen['step']),('last',200)]:
    folder=dest/tag;folder.mkdir();cp=dict(np.load(dest/'checkpoints'/f'{s:04}.npz'));ww=cp['W'];ensure(192);top=native.build(ww);native.save(folder/'graph.hnsw');ww.tofile(folder/'W.f32');cp['mu'].tofile(folder/'mu.f64')
    assert top==next(x['topology_sha'] for x in checkpoints if x['step']==s)
    native.verify(folder/'graph.hnsw',np.r_[np.arange(32),np.arange(4096,4128)])
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    expected={k:np.r_[cp[k][:32],cp[k][4096:4128]] for k in FIELDS};equal(parity,expected);save(folder/'parity.npz',**parity)
    dump(folder/'identity.json',dict(step=s,W_sha=digest(ww),graph_sha=sha(folder/'graph.hnsw'),mu_sha=sha(folder/'mu.f64'),topology_sha=top,parity='PASS'))
   after=native.stats();cost={k:after[k]-before[k] for k in ['NSG_calls','HNSW_calls','builds','build_seconds']}
   expected_nsg=15744+sum(x['candidate_new_NSG'] for x in curves)
   assert cost['NSG_calls']==expected_nsg<=100000 and cost['HNSW_calls']==6569216 and cost['builds']==1803
   rec=dict(dataset=ds,arm=arm,seed=seed,status='TRAINED_DIRECT_CANDIDATE_COMMIT',decision_steps=200,gradient_updates=0,accepted_submissions=int(commits.sum()),selected_step=chosen['step'],monitor_gate_feasible=best is not None,selected=chosen,last=checkpoints[-1],
    active_hubs=int((counts>0).sum()),seconds=time.monotonic()-started,actual_threads=after['actual_threads'],logical_candidate_rows=6553600,logical_mean_update_rows=0,
    candidate_new_NSG=sum(x['candidate_new_NSG'] for x in curves),mean_update_new_NSG=0,**cost)
   dump(dest/'model.json',rec);finish(name,cost['NSG_calls'],native=cost,actual_threads=after['actual_threads'],seconds=rec['seconds']);records.append(rec)
   dump(O/'results'/ds/'training_summary.json',records);print('RUN_COMPLETE',ds,arm,seed,rec['selected_step'],cost,flush=True)
 assert native.stats()['HNSW_calls']==13138432 and native.stats()['builds']==3606
 dump(O/'results'/ds/'training_complete.json',dict(status='PASS',runs=2,decision_steps=400,gradient_updates=0,seconds=time.monotonic()-started_all,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native=native.stats()))
finally:native.close()
