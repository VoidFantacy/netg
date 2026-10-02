from model import *
import math,resource
os.sched_setaffinity(0,{8});torch.set_num_threads(1)
assert read(O/'state.json')['status']=='TRAINING_READY';check(O/'reviews/before_training.json');start_all=time.time();runs=[]
def metric(net,x,u,hits,ndc,route):
 fs=[];expected=[]
 with torch.no_grad():
  for begin in range(0,len(x),128):
   end=begin+128;f=net(x[begin:end]);fs.append(f.numpy());p=probabilities(f).unsqueeze(-1);values=torch.stack([u[begin:end],torch.tensor(hits[begin:end].astype(float)),torch.tensor(ndc[begin:end].astype(float))],dim=-1);v=values
   for _ in range(3):v=p[:,:,0]*values+(p[:,:,1:]*v[:,T_NEXT[:,1:]]).sum(dim=2)
   expected.append(v[:,0].numpy())
 f=np.concatenate(fs);ev=np.concatenate(expected);states,actions=greedy(f);terminal=states[:,-1].astype(int);ix=np.arange(len(x));hu=hits[ix,terminal];nu=ndc[ix,terminal];uu=u.numpy()[ix,terminal];stats={}
 for role,sl in [('train',slice(0,1792)),('monitor',slice(1792,None)),('full_fit',slice(None))]:
  stats[role]=dict(recall_pct=float(hu[sl].mean()*10),delta_recall_pp=float((hu[sl].astype(float)-hits[sl,0]).mean()*10),utility=float(uu[sl].mean()),
   expected_utility=float(ev[sl,0].mean()),expected_recall_pct=float(ev[sl,1].mean()*10),expected_graph_ndc=float(ev[sl,2].mean()),graph_ndc=float(nu[sl].mean()),graph_change_pct=float((nu[sl].mean()/ndc[sl,0].mean()-1)*100),
   failure_pct=float((hu[sl]==0).mean()*100),changed_queries=int((terminal[sl]!=0).sum()),mean_swaps=float((actions[sl]>0).sum(axis=1).mean()),stop_at_first_pct=float((actions[sl,0]==0).mean()*100),max_abs_score=float(np.abs(f[sl]).max()))
 return stats,dict(states=states,actions=actions,terminal=terminal.astype(np.uint8),greedy_hits=hu,greedy_ndc=nu,greedy_utility=uu,expected=ev)
for ds in DS:
 x,u,hits,ndc,route,mean,scale=load_fit(ds);folder=O/'models'/ds;folder.mkdir();dump(folder/'normalization.json',dict(mean=mean.tolist(),scale=scale.tolist(),source='first1792 preselected fit rows only'))
 for arm in ARMS:
  for seed in SEEDS:
   resources();dest=folder/f'{arm}_{seed}';dest.mkdir();(dest/'trajectories').mkdir();torch.manual_seed(seed);net=Network();opt=torch.optim.AdamW(net.parameters(),lr=.0003,weight_decay=1e-4)
   batch_rng=np.random.default_rng(seed);action_rng=np.random.default_rng(seed+1000);baseline=np.zeros((2048,56));curve=[];checkpoints=[];traces=[];start=time.time()
   for step in range(3001):
    assert time.time()-start<900 and time.time()-start_all<7200,'training wall cap';assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<40*(1<<20)
    if step%100==0:
     directory=dest/f'checkpoint_{step:04}';directory.mkdir();stats,prediction=metric(net,x,u,hits,ndc,route);export(directory/'model.json',net,mean,scale,dataset=ds,arm=arm,seed=seed,step=step)
     torch.save(dict(model=net.state_dict(),optimizer=opt.state_dict(),batch_rng=batch_rng.bit_generator.state,action_rng=action_rng.bit_generator.state),directory/'checkpoint.pt');np.savez_compressed(directory/'prediction.npz',**prediction)
     if arm=='rl':np.savez_compressed(directory/'baselines.npz',baseline=baseline)
     rec=dict(step=step,seconds=time.time()-start,path=str(directory),**stats);checkpoints.append(rec);dump(dest/'checkpoints.json',checkpoints)
     if traces:
      np.savez_compressed(dest/'trajectories'/f'{step-99:04}_{step:04}.npz',**{k:np.stack([t[k] for t in traces]) for k in traces[0]});traces=[]
     dump(dest/'training_curve.json',curve);dump(O/'state.json',dict(status='TRAINING_RUNNING',dataset=ds,arm=arm,seed=seed,step=step,completed_runs=len(runs),validation_read=False,heldout_read=False))
     print('CHECKPOINT',ds,arm,seed,step,'train_delta',stats['train']['delta_recall_pp'],'monitor_delta',stats['monitor']['delta_recall_pp'],'monitor_U',stats['monitor']['utility'],flush=True)
     if step==3000:break
    rows=batch_rng.choice(1792,64,replace=False);f=net(x[rows]);tt=u[rows]
    if arm=='rl':loss,trace=sample_trajectory(f,tt.numpy(),rows,baseline,action_rng);trace['step']=np.array(step+1,np.int32);traces.append(trace);sample_U=float(trace['returns'][:,0].mean())
    else:loss=-expected_terminal(f,tt).mean();sample_U=None
    opt.zero_grad();loss.backward();gn=float(torch.nn.utils.clip_grad_norm_(net.parameters(),5.));lr=.0003+(.003-.0003)*step/49 if step<50 else .0003+.5*(.003-.0003)*(1+math.cos(math.pi*(step-50)/2949))
    opt.param_groups[0]['lr']=lr;opt.step()
    assert all(torch.isfinite(p).all() for p in net.parameters()) and np.isfinite(float(loss.detach()))
    if arm=='rl':update_baseline(baseline,rows,trace['states'],trace['actions'],trace['returns'])
    curve.append(dict(step=step+1,loss=float(loss.detach()),gradient_norm=gn,lr=lr,sampled_terminal_utility=sample_U,seconds=time.time()-start))
   feasible=[c for c in checkpoints[1:] if c['monitor']['graph_change_pct']<=1.0];pool=feasible or checkpoints[1:];best=max(pool,key=lambda z:z['monitor']['utility']);selected=dest/'selected';selected.mkdir()
   for name in ['model.json','prediction.npz']:shutil.copy2(Path(best['path'])/name,selected/name)
   result=dict(dataset=ds,arm=arm,seed=seed,updates=3000,training_seconds=time.time()-start,best=best,any_cost_feasible=bool(feasible),selection='max nonzero checkpoint monitor greedy utility under graphNDC<=+1%, earliest tie; if none max utility marked infeasible',cached_RL_episodes=192000 if arm=='rl' else 0,new_NSG_calls=0)
   dump(dest/'selected.json',result);runs.append(result);dump(O/'results/training_summary.json',runs);print('RUN_COMPLETE',ds,arm,seed,result['training_seconds'],'selected',best['step'],flush=True)
freeze(O/'reviews/models_after_training.json',[p for p in (O/'models').rglob('*') if p.is_file()]);dump(O/'state.json',dict(status='TRAINING_COMPLETE_VERIFY_PENDING',training_runs=8,optimizer_updates=24000,training_seconds=time.time()-start_all,validation_read=False,heldout_read=False));print('TRAINING_COMPLETE',time.time()-start_all,flush=True)
