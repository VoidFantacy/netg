from common import *
import struct,math

def graph(path):
 b=Path(path).read_bytes();fmt='<6QiI3QdQ';head=struct.unpack_from(fmt,b);start=struct.calcsize(fmt)
 off,mx,n,size,label,data,level,entry,M,M0,m,mult,ef=head
 assert off==0 and M==m==16 and M0==32 and ef==200 and mx==n
 adjacent=[];vectors=[];labels=[]
 for i in range(n):
  row=start+i*size;degree=struct.unpack_from('<H',b,row)[0];assert 1<=degree<=M0
  adj=np.frombuffer(b,dtype='<u4',count=degree,offset=row+4).astype(np.int32);assert (adj<n).all() and len(np.unique(adj))==degree and i not in adj
  adjacent.append(adj);vectors.append(b[row+data:row+label]);labels.append(struct.unpack_from('<Q',b,row+label)[0])
 upper=b[start+n*size:];return dict(head=head,adjacent=adjacent,vectors=vectors,labels=labels,upper=upper)

def verify_graph(path,baseline,mask,t):
 g=graph(path);assert g['head']==baseline['head'] and g['vectors']==baseline['vectors'] and g['labels']==baseline['labels'] and g['upper']==baseline['upper']
 offsets=t['offsets'];protected=np.array(t['protected'],bool);assert mask.shape==(t['edges'],) and np.isin(mask,[0,1]).all() and mask[protected].all()
 for u,row in enumerate(baseline['adjacent']):assert np.array_equal(g['adjacent'][u],row[mask[offsets[u]:offsets[u+1]].astype(bool)])
 for reverse in [False,True]:
  adj=g['adjacent']
  if reverse:
   rev=[[] for _ in adj]
   for u,row in enumerate(adj):
    for v in row:rev[v].append(u)
   adj=rev
  seen={t['start_internal_id']};stack=list(seen)
  while stack:
   for v in adj[stack.pop()]:
    if v not in seen:seen.add(int(v));stack.append(int(v))
  assert len(seen)==t['nodes']
 return dict(edges=int(mask.sum()),nodes=t['nodes'],strongly_connected=True,coordinates_labels_upper_layers_identical=True)

def result_stats(out,base,gt):
 rows=out['rows'];hits=score(out['ids'],gt[rows]);assert np.array_equal(hits,out['hits'])
 assert (np.diff(np.sort(out['ids'],axis=1),axis=1)!=0).all() and (out['ids']>=0).all()
 assert (np.diff(out['entries'],axis=1)>0).all()
 cost=out['route_ndc'].astype(float)+out['graph_ndc'];basecost=base['route_ndc'][rows].astype(float)+base['graph_ndc'][rows]
 r=hits.astype(float)-base['hits'][rows]-.1*(cost/basecost-1);assert np.array_equal(r,out['reward'])
 return dict(recall=float(hits.mean()/10),delta_pp=float((hits.astype(float)-base['hits'][rows]).mean()*10),reward=float(r.mean()),
   route_ndc=float(out['route_ndc'].mean()),graph_ndc=float(out['graph_ndc'].mean()),total_ndc=float(cost.mean()),total_change_pct=float((cost.mean()/basecost.mean()-1)*100))

if __name__=='__main__':
 assert read(O/'state.json')['status']=='TRAINING_COMPLETE_DEVELOPMENT_PENDING'
 check_freeze(O/'reviews/models_after_training.json');rows=[];verification=[]
 for ds in DS:
  c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(20000,100);base=np.load(O/'results'/ds/'baseline.npz');t=read(O/'inputs'/ds/'topology.json');original=graph(O/'inputs'/ds/'base.hnsw')
  assert np.array_equal(score(base['ids'],gt),base['hits'])
  train=np.fromfile(O/'inputs'/ds/'train_rows.i32',np.int32);monitor=np.fromfile(O/'inputs'/ds/'monitor_rows.i32',np.int32);protected=np.array(t['protected'],bool);E=t['edges']
  for seed in SEEDS:
   dest=O/'models'/ds/str(seed);checks=read(dest/'checkpoints.json');selected=read(dest/'selected.json')
   assert len(checks)==7 and selected['updates']==600
   best=max(checks[1:],key=lambda x:x['reward']);assert best==selected['best']
   graphs=0
   for rec in checks:
    p=Path(rec['path']);mask=np.fromfile(p/'mask.u8',np.uint8);logits=np.fromfile(p/'logits.f64',np.float64)
    assert np.array_equal(mask,np.maximum(protected,(logits>=0)).astype(np.uint8));verify_graph(p/'graph.hnsw',original,mask,t);graphs+=1
    out=np.load(p/'monitor.npz');assert np.array_equal(out['rows'],monitor);metric=result_stats(out,base,gt)
    for k in ['recall','reward','route_ndc','graph_ndc','total_ndc']:assert abs(metric[k]-rec[k])<1e-11
    rows.append(dict(dataset=ds,seed=seed,step=rec['step'],retained_edges=int(mask.sum()),**metric))
   for a,b in [('graph.hnsw','mask.u8'),('random_graph.hnsw','random_mask.u8')]:verify_graph(dest/'selected'/a,original,np.fromfile(dest/'selected'/b,np.uint8),t);graphs+=1
   learned=np.fromfile(dest/'selected/mask.u8',np.uint8);random=np.fromfile(dest/'selected/random_mask.u8',np.uint8)
   for u in range(t['nodes']):
    begin,end=t['offsets'][u:u+2];assert learned[begin:end].sum()==random[begin:end].sum()
   # Independent NumPy replay of REINFORCE + entropy + clipping + Adam from archived actual trajectories.
   theta=np.zeros(E);m=np.zeros(E);v=np.zeros(E);bq=np.zeros(20000);rng=np.random.default_rng(seed);visits=np.zeros(E,np.int64);maxerr=0
   history=read(dest/'training_curve.json');assert len(history)==600
   for step in range(1,601):
    sample=np.load(dest/'trajectories'/f'{step:04}.npz');r=sample['reward'];rws=sample['rows'];stats=result_stats(sample,base,gt)
    expected_rows=rng.choice(train,128,replace=False);expected_seed=int(rng.integers(0,2**63));assert np.array_equal(rws,expected_rows) and int(sample['batch_seed'])==expected_seed
    adv=r-bq[rws];assert np.array_equal(adv,sample['advantage']);packed=sample['actions'].astype(np.int32);e=packed//2;a=packed%2;off=sample['offsets']
    assert len(off)==129 and off[0]==0 and off[-1]==len(e) and not protected[e].any()
    for j in range(128):assert len(np.unique(e[off[j]:off[j+1]]))==off[j+1]-off[j]
    visits+=np.bincount(e,minlength=E);p=1/(1+np.exp(-theta));ad=np.repeat(adv,np.diff(off))
    grad=np.bincount(e,weights=(p[e]-a)*ad+.001*theta[e]*p[e]*(1-p[e]),minlength=E)/128
    norm=np.linalg.norm(grad);assert abs(norm-float(sample['gradient_norm']))<2e-10
    grad*=min(1.,1./(norm+1e-6));m=.9*m+.1*grad;v=.999*v+.001*grad*grad
    lr=.0025+.5*(.025-.0025)*(1+math.cos(math.pi*(step-1)/599));assert abs(lr-float(sample['lr']))<1e-15
    theta-=lr*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8);theta=np.clip(theta,-4,4);bq[rws]+=.1*(r-bq[rws])
    assert not theta[protected].any()
    if step%100==0:
     ref=np.fromfile(dest/f'checkpoint_{step:04}/logits.f64',np.float64);error=float(np.max(np.abs(ref-theta)));maxerr=max(maxerr,error);assert error<2e-8,(ds,seed,step,error)
     assert np.array_equal(bq,np.fromfile(dest/f'checkpoint_{step:04}/query_baselines.f64',np.float64))
   assert np.array_equal(visits,np.fromfile(dest/'edge_exposures.i64',np.int64))
   verification.append(dict(dataset=ds,seed=seed,optimizer_updates_replayed=600,trajectories=76800,graph_artifacts_checked=graphs,max_numpy_replay_error=maxerr,
     all_raw_ID_GT_rewards_verified=True,train_monitor_disjoint=True,random_degree_matched=True,changed_edges=int((learned==0).sum())))
 dump(O/'results/checkpoint_metrics.json',rows);dump(O/'reviews/training_independent_verification.json',dict(status='PASS',datasets=verification,optimizer_updates=2400,NSG_query_calls=0))
 print('TRAINING_INDEPENDENT_VERIFICATION_PASS',verification,flush=True)
