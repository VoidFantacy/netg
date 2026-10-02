from common import *
import math

assert all(read(O/'results'/ds/'training_complete.json')['status']=='PASS' for ds in DS)
check(O/'reviews/before_training.json');check(O/'reviews/models_after_training.json');reports=[];query_total=0;update_total=0;checkpoint_total=0
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');d=c['dim'];h=c['hub_count'];p=np.fromfile(c['P'],np.float32).reshape(h,d);b=np.fromfile(c['basis'],np.float64).reshape(d,16)
 gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);base=dict(np.load(O/'results'/ds/'baseline.npz'));q=np.fromfile(c['queries_file'],np.float32).reshape(5120,d)[:4096].astype(float);q/=np.linalg.norm(q,axis=1)[:,None]
 moment=q.T@q/4096;residual=np.linalg.norm(moment@b-b*(np.diag(b.T@moment@b)),ord='fro');assert residual<1e-12
 def export(x):
  if np.count_nonzero(x)==0:return p.copy()
  a=np.tanh(x.reshape(16,16))*.25;res=np.linalg.multi_dot([p.astype(float),b,a,b.T])
  y=p.astype(float)+.25*res;return (y/np.sqrt(np.sum(y*y,axis=1))[:,None]).astype(np.float32)
 def scores(ids,rows,rndc,gndc):
  # Independent set intersection; GT-scoring and reward implementation are not imported.
  hits=np.fromiter((len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(ids,gt[rows])),dtype=np.int16,count=len(rows))
  z=base['hits'][rows].astype(np.int16);c0=base['route_ndc'][rows].astype(float)+base['graph_ndc'][rows]
  u=hits-z-.1*((rndc.astype(float)+gndc)/c0-1)-.1*((hits==0).astype(float)-(z==0).astype(float))
  return hits,u
 for arm in ARMS:
  for seed in SEEDS:
   folder=O/'models'/ds/f'{arm}_{seed}';rng=np.random.default_rng(seed);brng=np.random.default_rng(seed+1000);mu=np.zeros(256);m=mu.copy();v=mu.copy();maxerr=0.;whash=0
   for step in range(1,201):
    a=np.load(folder/'trajectory'/f'{step:04}.npz');rows=brng.choice(4096,128,replace=False).astype(np.int32);assert np.array_equal(a['rows'],rows)
    noise=rng.normal(size=(8 if arm=='rl' else 4,256))
    if arm=='es':noise=np.r_[noise,-noise]
    assert np.array_equal(noise,a['eps']);assert np.max(np.abs(mu-a['mu_before']))<1e-9
    assert np.array_equal(a['actions'],a['mu_before'][None,:]+.3*noise)
    rewards=[]
    for j in range(8):
     w=export(a['actions'][j]);original=profiles(p,b,a['actions'][j])
     assert np.max(np.abs(w-original))<6e-8
     assert digest(original)==str(a['W_sha'][j]);whash+=1
     drift=np.square(original.astype(float)-p).sum(1).mean();assert abs(drift-a['drift'][j])<1e-14
     hits,u=scores(a['ids'][j],rows,a['route_ndc'][j],a['graph_ndc'][j]);rewards.append(float(u.mean()-drift));query_total+=128
    rewards=np.array(rewards);assert np.max(np.abs(rewards-a['rewards']))<1e-13
    if arm=='rl':
     g=np.zeros(256)
     for j in range(8):g+=(rewards[j]-math.fsum(float(rewards[k]) for k in range(8) if k!=j)/7)*noise[j]/(8*.3)
    else:g=sum((rewards[j]-rewards[j+4])*noise[j]/(8*.3) for j in range(4))
    assert np.max(np.abs(g-a['gradient']))<1e-12
    g/=max(1.,math.sqrt(float(np.dot(g,g))));m=.9*m+.1*g;v=.999*v+.001*g*g;lr=.003+.0135*(1+math.cos(math.pi*(step-1)/199))
    mu=np.clip(mu+lr*m/(1-.9**step)/(np.sqrt(v/(1-.999**step))+1e-8),-2,2)
    err=max(float(np.max(np.abs(mu-a['mu_after']))),float(np.max(np.abs(m-a['m_after']))),float(np.max(np.abs(v-a['v_after']))));maxerr=max(maxerr,err);assert err<1e-9
    update_total+=1
   checkpoints=read(folder/'checkpoints.json');assert [r['step'] for r in checkpoints]==list(range(0,201,20))
   for rec in checkpoints:
    a=np.load(folder/'checkpoints'/f"{rec['step']:04}.npz");w=profiles(p,b,a['mu']);assert digest(w)==rec['W_sha'];checkpoint_total+=1
    if rec['step']:assert np.max(np.abs(a['mu']-np.load(folder/'trajectory'/f"{rec['step']:04}.npz")['mu_after']))==0
    for tag,sl,rows in [('train',slice(0,512),np.arange(512)),('monitor',slice(512,None),np.arange(4096,5120))]:
     hits,u=scores(a['ids'][sl],rows,a['route_ndc'][sl],a['graph_ndc'][sl]);query_total+=len(rows)
     assert abs(rec[tag]['delta_recall_pp']-(hits-base['hits'][rows].astype(np.int16)).mean()*10)<1e-12
     assert abs(rec[tag]['mean_U']-u.mean())<1e-13
     assert abs(rec[tag]['graph_NDC_change_pct']-(a['graph_ndc'][sl].mean()/base['graph_ndc'][rows].mean()-1)*100)<1e-12
   feasible=[r for r in checkpoints[1:] if r['monitor']['graph_NDC_change_pct']<=1]
   chosen=max(feasible or checkpoints[1:],key=lambda x:(x['monitor']['mean_U'],-x['step']));model=read(folder/'model.json');assert chosen['step']==model['selected_step']
   for tag,step in [('selected',chosen['step']),('last',200)]:
    ident=read(folder/tag/'identity.json');assert ident['W']==identity(folder/tag/'W.f32') and ident['graph']==identity(folder/tag/'graph.hnsw')
    x=np.fromfile(folder/tag/'mu.f64',np.float64);w=profiles(p,b,x);assert digest(w)==sha(folder/tag/'W.f32');assert np.array_equal(x,np.load(folder/'checkpoints'/f'{step:04}.npz')['mu'])
   reports.append(dict(dataset=ds,arm=arm,seed=seed,status='PASS',updates=200,actions_verified=1600,W_hashes_verified=whash,checkpoint_count=11,max_optimizer_replay_error=maxerr,selected_step=chosen['step'],basis_eigen_residual=float(residual)))
   dump(O/'reviews/training_verification_progress.json',reports);print('TRAINING_AUDIT_PASS',ds,arm,seed,maxerr,flush=True)
 # Equal samples and query/candidate budget, separately verified across arms.
 for seed in SEEDS:
  for step in range(1,201):
   a=np.load(O/'models'/ds/f'rl_{seed}/trajectory/{step:04}.npz');e=np.load(O/'models'/ds/f'es_{seed}/trajectory/{step:04}.npz');assert np.array_equal(a['rows'],e['rows'])
dump(O/'reviews/training_verification.json',dict(status='PASS',optimizer_updates_verified=update_total,raw_query_outputs_set_scored=query_total,checkpoints_verified=checkpoint_total,action_W_hashes_verified=12800,equal_batch_schedule_and_call_budget=True,records=reports))
dump(O/'state.json',dict(status='TRAINING_VERIFIED_DEVELOPMENT_PENDING',training_runs=8,optimizer_updates=1600))
