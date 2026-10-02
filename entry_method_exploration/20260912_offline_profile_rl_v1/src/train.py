from common import *
from native import Native
import argparse, resource

parser=argparse.ArgumentParser();parser.add_argument('dataset',choices=DS);args=parser.parse_args();ds=args.dataset
assert read(O/'reviews/preflight.json')['status']=='PASS'
check(O/'reviews/before_training.json');check(O/'reviews/upstream.json',hashes=False)
c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],RANK)
gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);base=dict(np.load(O/'results'/ds/'baseline.npz'));native=Native(c);start_all=time.time()
trainprobe=np.arange(512,dtype=np.int32);monitor=np.arange(4096,5120,dtype=np.int32);probe=np.r_[trainprobe,monitor]
def stat(out,rows):
 h=score(out['ids'],gt[rows]);bb=subset(base,rows);u=utility(out,bb,gt[rows]);total=out['route_ndc'].astype(float)+out['graph_ndc'];total0=bb['route_ndc'].astype(float)+bb['graph_ndc']
 return dict(recall_pct=float(h.mean()*10),delta_recall_pp=float((h.astype(float)-bb['hits']).mean()*10),failure_pct=float((h==0).mean()*100),mean_U=float(u.mean()),graph_NDC_change_pct=float((out['graph_ndc'].mean()/bb['graph_ndc'].mean()-1)*100),total_NDC_change_pct=float((total.mean()/total0.mean()-1)*100))
records=[]
for arm in ARMS:
 for seed in SEEDS:
  name=f'train_{ds}_{arm}_{seed}';reserve(name,STEPS*POP*BATCH+11*len(probe)+384)
  dest=O/'models'/ds/f'{arm}_{seed}';dest.mkdir(parents=True);(dest/'trajectory').mkdir();(dest/'checkpoints').mkdir()
  before=native.stats();started=time.time();rng=np.random.default_rng(seed);batch_rng=np.random.default_rng(seed+1000)
  mu=np.zeros(256);m=mu.copy();v=mu.copy();curve=[];checkpoints=[];best=None;fallback=None
  for step in range(STEPS+1):
   assert time.time()-start_all<7200;assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<32*(1<<20)
   if step%20==0:
    resources();w=profiles(p,b,mu);top=native.build(w);out=native.run(probe);cut=len(trainprobe)
    tr=stat({k:x[:cut] for k,x in out.items()},trainprobe);mo=stat({k:x[cut:] for k,x in out.items()},monitor)
    feasible=mo['graph_NDC_change_pct']<=1;rec=dict(step=step,train=tr,monitor=mo,feasible=feasible,drift=float(np.square(w.astype(float)-p).sum(1).mean()),W_sha=digest(w),topology_sha=top,seconds=time.time()-started)
    np.savez_compressed(dest/'checkpoints'/f'{step:04}.npz',mu=mu,m=m,v=v,**out);checkpoints.append(rec)
    if step:
     if fallback is None or mo['mean_U']>fallback['monitor']['mean_U']:fallback=rec
     if feasible and (best is None or mo['mean_U']>best['monitor']['mean_U']):best=rec
    dump(dest/'checkpoints.json',checkpoints);print('CHECKPOINT',ds,arm,seed,step,'train',tr['delta_recall_pp'],'monitor',mo['delta_recall_pp'],'U',mo['mean_U'],flush=True)
    dump(O/'state.json',dict(status='TRAINING',dataset=ds,arm=arm,seed=seed,completed_updates=step,native=native.stats(),pid=os.getpid()))
    if step==STEPS:break
   step1=step+1;rows=batch_rng.choice(4096,BATCH,replace=False).astype(np.int32)
   eps=rng.normal(size=(POP if arm=='rl' else POP//2,256))
   if arm=='es':eps=np.concatenate([eps,-eps])
   actions=mu[None,:]+SIGMA*eps;raw=[];rewards=[];drifts=[];tops=[];wsha=[]
   for a in actions:
    w=profiles(p,b,a);tops.append(native.build(w));wsha.append(digest(w));out=native.run(rows);raw.append(out)
    drift=float(np.square(w.astype(float)-p).sum(1).mean());u=utility(out,subset(base,rows),gt[rows]);rewards.append(float(u.mean()-drift));drifts.append(drift)
   rewards=np.array(rewards);g=gradient(arm,rewards,eps);new_mu,new_m,new_v,norm=update(mu,m,v,g,step1)
   np.savez_compressed(dest/'trajectory'/f'{step1:04}.npz',rows=rows,eps=eps,actions=actions,mu_before=mu,mu_after=new_mu,m_after=new_m,v_after=new_v,rewards=rewards,drift=np.array(drifts),gradient=g,topology_sha=np.array(tops),W_sha=np.array(wsha),**{k:np.stack([x[k] for x in raw]) for k in raw[0]})
   curve.append(dict(step=step1,mean_reward=float(rewards.mean()),min_reward=float(rewards.min()),max_reward=float(rewards.max()),gradient_norm=norm,mean_drift=float(np.mean(drifts)),mean_parameter_norm=float(np.linalg.norm(new_mu)),lr=rate(step1),seconds=time.time()-started))
   mu,m,v=new_mu,new_m,new_v
   if step1%20==0:dump(dest/'training_curve.json',curve)
  chosen=best if best is not None else fallback;assert chosen is not None
  for tag,s in [('selected',chosen['step']),('last',STEPS)]:
   folder=dest/tag;folder.mkdir();x=np.load(dest/'checkpoints'/f'{s:04}.npz')['mu'];w=profiles(p,b,x);top=native.build(w);native.save(folder/'graph.hnsw');w.tofile(folder/'W.f32');x.tofile(folder/'mu.f64')
   assert top==next(k['topology_sha'] for k in checkpoints if k['step']==s)
   # Independent serialized plain and original-kernel checks on fixed train/monitor rows.
   native.verify(folder/'graph.hnsw',np.r_[np.arange(32),np.arange(4096,4128)])
   dump(folder/'identity.json',dict(step=s,W=identity(folder/'W.f32'),graph=identity(folder/'graph.hnsw'),mu=identity(folder/'mu.f64'),topology_sha=top))
  after=native.stats();cost={k:after[k]-before[k] for k in ['NSG_calls','HNSW_calls','builds','build_seconds']};cost['actual_threads']=after['actual_threads']
  rec=dict(dataset=ds,arm=arm,seed=seed,status='TRAINED',updates=STEPS,selected_step=chosen['step'],monitor_gate_feasible=best is not None,selected=chosen,last=checkpoints[-1],seconds=time.time()-started,**cost)
  dump(dest/'model.json',rec);finish(name,cost['NSG_calls'],**{k:v for k,v in rec.items() if k not in ['NSG_calls','status']});records.append(rec);dump(O/'results'/ds/'training_summary.json',records)
  print('TRAINING_RUN_COMPLETE',ds,arm,seed,'selected',chosen['step'],cost,flush=True)
dump(O/'results'/ds/'native_accounting.json',native.stats());native.close();dump(O/'results'/ds/'training_complete.json',dict(status='PASS',training_runs=4,updates=800,seconds=time.time()-start_all))
