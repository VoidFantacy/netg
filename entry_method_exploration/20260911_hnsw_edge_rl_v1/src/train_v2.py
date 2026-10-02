from native_v2 import *
import torch,math,resource
torch.set_num_threads(1);torch.set_num_interop_threads(1)
assert read(O/'reviews/router_preflight_v2.json')['status']=='PASS'
check_freeze(O/'reviews/protocol_and_implementation_before_queries.json');check_freeze(O/'reviews/initial_graphs.json');check_freeze(O/'reviews/frozen_structural_repair.json')
global_start=time.time();summary=[]

def reward(out,base,gt):
 hits=score(out['ids'],gt[out['rows']]);out['hits']=hits
 rows=out['rows'];cost=out['route_ndc'].astype(float)+out['graph_ndc']
 r=hits.astype(float)-base['hits'][rows]-.1*(cost/(base['route_ndc'][rows].astype(float)+base['graph_ndc'][rows])-1)
 out['reward']=r;return r

def save_output(path,out):np.savez_compressed(path,**out)
def stats(out):
 return dict(recall=float(out['hits'].mean()/10),reward=float(out['reward'].mean()),route_ndc=float(out['route_ndc'].mean()),graph_ndc=float(out['graph_ndc'].mean()),total_ndc=float((out['route_ndc'].astype(float)+out['graph_ndc']).mean()))

for ds in DS:
 c=read(O/'inputs'/ds/'config.json');folder=O/'models'/ds;folder.mkdir();ds_result=O/'results'/ds;ds_result.mkdir()
 with Environment(c,O/'inputs'/ds,load_nsg=True) as native:
  protected=np.array(native.topology['protected'],np.uint8);E=native.edges;all_keep=np.ones(E,np.uint8)
  # Verify native output and counter semantics before optimization, using two graph states.
  job='native_parity_'+ds;reserve(job,256);before=native.calls
  for mask in [all_keep,protected]:native.parity(np.arange(32,dtype=np.int32),mask,native=True)
  finish(job,native.calls-before,route_calls=native.route_calls)
  job='baseline_'+ds;reserve(job,20000);before=native.calls
  base=native.static(np.arange(20000,dtype=np.int32),O/'inputs'/ds/'base.hnsw')
  # GT is first opened after baseline raw output returns; all subsequent access is reward/scoring only.
  gt=np.fromfile(c['gt_file'],np.int64).reshape(20000,100);base['hits']=score(base['ids'],gt);base['reward']=np.zeros(20000)
  save_output(ds_result/'baseline.npz',base)
  previous=E32/'results'/('fit_v2_'+ds)/(c['policy']['model_name']+'_L128')
  for key,filename,dtype in [('ids','ids.i32',np.int32),('entries','entry_ids.i32',np.int32),('route_ndc','route_ndc.u32',np.uint32),('graph_ndc','graph_ndc.u32',np.uint32),('hits','hits.u8',np.uint8)]:
   assert np.array_equal(base[key].reshape(-1),np.fromfile(previous/filename,dtype)),(ds,key)
  finish(job,native.calls-before,original_default_full_fit_parity=True)
  train_rows=np.fromfile(O/'inputs'/ds/'train_rows.i32',np.int32);monitor=np.fromfile(O/'inputs'/ds/'monitor_rows.i32',np.int32)
  assert len(train_rows)==16000 and len(monitor)==4000 and not np.intersect1d(train_rows,monitor).size
  assert len(np.unique(np.r_[train_rows,monitor]))==20000
  for seed in SEEDS:
   job=f'train_{ds}_{seed}';reserve(job,600*128+7*4000);before=native.calls;start=time.time()
   dest=folder/str(seed);dest.mkdir();trajectory=dest/'trajectories';trajectory.mkdir();rng=np.random.default_rng(seed)
   theta=torch.zeros(E,dtype=torch.float64,requires_grad=True);optimizer=torch.optim.Adam([theta],lr=.025)
   baselines=np.zeros(20000,np.float64);history=[];checkpoints=[];best=None;exposures=np.zeros(E,np.int64)
   for step in range(601):
    assert time.time()-start<600,'per-training wall cap';assert time.time()-global_start<3600,'global wall cap'
    assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<40*(1<<20),'RSS cap'
    if step%100==0:
     resources();values=theta.detach().numpy().copy();mask=np.maximum(protected,(values>=0).astype(np.uint8))
     outdir=dest/f'checkpoint_{step:04}';outdir.mkdir();values.tofile(outdir/'logits.f64');mask.tofile(outdir/'mask.u8')
     torch.save(optimizer.state_dict(),outdir/'optimizer.pt');baselines.tofile(outdir/'query_baselines.f64')
     native.export(mask,outdir/'graph.hnsw');measured=native.static(monitor,outdir/'graph.hnsw');reward(measured,base,gt);save_output(outdir/'monitor.npz',measured)
     rec=dict(step=step,**stats(measured),retained_edges=int(mask.sum()),path=str(outdir),seconds=time.time()-start);checkpoints.append(rec)
     if step and (best is None or rec['reward']>best['reward']):best=rec
     dump(dest/'checkpoints.json',checkpoints);print('CHECKPOINT',ds,seed,step,rec,flush=True)
     if step==600:break
    rows=rng.choice(train_rows,128,replace=False);p=torch.sigmoid(theta).detach().numpy();batch_seed=int(rng.integers(0,2**63))
    sample=native.run(rows,p=p,seed=batch_seed,search=True,trace=True);r=reward(sample,base,gt);adv=r-baselines[rows]
    actions=sample['actions'];edge=actions//2;take=actions%2;lengths=np.diff(sample['offsets']);assert actions.max(initial=0)<=np.iinfo(np.uint16).max
    assert not protected[edge].any();assert sample['offsets'][0]==0 and sample['offsets'][-1]==len(actions)
    exposures+=np.bincount(edge,minlength=E)
    if step==0 or step%100==99:
     for i in range(128):assert len(np.unique(edge[sample['offsets'][i]:sample['offsets'][i+1]]))==lengths[i]
    idx=torch.tensor(edge,dtype=torch.int64);a=torch.tensor(take,dtype=torch.float64);z=theta[idx];prob=z.sigmoid()
    lp=a*torch.nn.functional.logsigmoid(z)+(1-a)*torch.nn.functional.logsigmoid(-z)
    ent=-(prob*torch.nn.functional.logsigmoid(z)+(1-prob)*torch.nn.functional.logsigmoid(-z))
    advantage=torch.tensor(np.repeat(adv,lengths));loss=-(advantage*lp).sum()/128-.001*ent.sum()/128
    optimizer.zero_grad();loss.backward();norm=float(torch.nn.utils.clip_grad_norm_([theta],1.0))
    lr=.0025+.5*(.025-.0025)*(1+math.cos(math.pi*step/599));optimizer.param_groups[0]['lr']=lr;optimizer.step()
    with torch.no_grad():theta.clamp_(-4,4)
    baselines[rows]+=.1*(r-baselines[rows])
    assert torch.isfinite(theta).all() and not theta.detach().numpy()[protected.astype(bool)].any()
    sample['actions']=sample['actions'].astype(np.uint16);sample.update(advantage=adv,batch_seed=np.array(batch_seed,np.uint64),lr=np.array(lr),gradient_norm=np.array(norm))
    save_output(trajectory/f'{step+1:04}.npz',sample)
    rec=dict(step=step+1,loss=float(loss.detach()),gradient_norm=norm,lr=lr,mean_actions=float(lengths.mean()),mean_entropy=float(ent.detach().sum()/128),**stats(sample),seconds=time.time()-start)
    history.append(rec)
    if (step+1)%25==0:dump(dest/'training_curve.json',history);dump(O/'state.json',dict(status='TRAINING_RUNNING',dataset=ds,seed=seed,updates=step+1,total_nsg_calls=native.calls))
   assert len(history)==600 and best is not None
   selected=dest/'selected';selected.mkdir()
   for name in ['graph.hnsw','mask.u8','logits.f64']:shutil.copy2(Path(best['path'])/name,selected/name)
   learned=np.fromfile(selected/'mask.u8',np.uint8);control=protected.copy();random=np.random.default_rng(seed+100);offsets=native.topology['offsets']
   for u in range(native.topology['nodes']):
    row=np.arange(offsets[u],offsets[u+1]);available=row[protected[row]==0];k=int(learned[available].sum());control[random.choice(available,k,replace=False)]=1
    assert int(control[row].sum())==int(learned[row].sum())
   control.tofile(selected/'random_mask.u8');native.export(control,selected/'random_graph.hnsw');exposures.tofile(dest/'edge_exposures.i64')
   dump(dest/'selected.json',dict(best=best,selection='highest nonzero checkpoint monitor reward, earliest tie',random_seed=seed+100,training_seconds=time.time()-start,updates=600,NSG_calls=native.calls-before,
       retained_edges=int(learned.sum()),original_edges=E,learned_changed_edges=int((learned==0).sum()),random_degree_matched=True,baseline_monitor=stats({k:(v[monitor] if hasattr(v,'shape') and len(v)==20000 else v) for k,v in base.items() if k not in ['offsets','actions']})))
   finish(job,native.calls-before,updates=600,selected_step=best['step'],training_seconds=time.time()-start);summary.append(dict(dataset=ds,seed=seed,selected=best,updates=600))
  dump(ds_result/'native_accounting.json',dict(NSG_calls=native.calls,HNSW_calls=native.route_calls))
dump(O/'results/training_summary.json',summary)
freeze(O/'reviews/models_after_training.json',[p for p in (O/'models').rglob('*') if p.is_file()])
scope=read(O/'reviews/access_scope.json');scope['fit_decoded']=True;dump(O/'reviews/access_scope.json',scope)
dump(O/'state.json',dict(status='TRAINING_COMPLETE_DEVELOPMENT_PENDING',training_runs=4,optimizer_updates=2400,NSG_calls=sum(j.get('actual_calls',0) for j in read(O/'logs/jobs.json'))))
print('TRAINING_COMPLETE',summary,flush=True)
