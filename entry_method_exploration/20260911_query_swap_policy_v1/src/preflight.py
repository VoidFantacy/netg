from model import *
assert read(O/'state.json')['status']=='LABELS_COMPLETE_VERIFY_PENDING'
verification=[]
for ds in DS:
 p=O/'inputs'/ds;r=O/'results'/('labels_'+ds);c=read(p/'config.json');d=c['dim'];h=c['hub_count'];gt=np.fromfile(p/'gt.i64',np.int64).reshape(2048,100)
 ids=np.fromfile(r/'ids.i32',np.int32).reshape(2048,56,10);dist=np.fromfile(r/'distances.f32',np.float32).reshape(2048,56,10);entries=np.fromfile(r/'entries.i32',np.int32).reshape(2048,56,3);pool=np.fromfile(r/'pool.i32',np.int32).reshape(2048,8)
 hubs=np.fromfile(c['hub_ids'],np.int32);ndc=np.fromfile(r/'graph_ndc.u32',np.uint32).reshape(2048,56);route=np.fromfile(r/'route_ndc.u32',np.uint32);hits=score(ids,gt)
 assert np.isfinite(dist).all() and (ids>=0).all() and (ids<(2505000 if ds==DS[0] else 10000000)).all();assert (np.diff(np.sort(ids,axis=-1),axis=-1)!=0).all()
 assert np.array_equal(entries,np.sort(hubs[pool[:,TRIP]],axis=-1)) and (np.diff(entries,axis=-1)>0).all()
 utility=hits.astype(float)-hits[:,0,None]-.1*((ndc.astype(float)+route[:,None])/(ndc[:,0]+route)[:,None]-1);assert np.array_equal(utility[:,0],np.zeros(2048))
 np.savez_compressed(r/'scored.npz',hits=hits,graph_ndc=ndc,route_ndc=route,utility=utility)
 # Independently reconstruct all GT-free features using NumPy, before any optimizer.
 q=np.fromfile(c['queries_file'],np.float32).reshape(2048,d).astype(float);qp=(q/np.linalg.norm(q,axis=1,keepdims=True))@np.fromfile(c['projection'],np.float64).reshape(16,d).T
 hp=np.fromfile(c['hub_projection'],np.float64).reshape(h,16);pairs=np.fromfile(c['pair_cosine'],np.float32).reshape(h,h);pdist=np.fromfile(r/'pool_distance.f32',np.float32).reshape(2048,8)
 cosine=(1-pdist.astype(float))/np.linalg.norm(q,axis=1,keepdims=True);features=np.empty((2048,56,76),np.float32)
 for s,t in enumerate(TRIP):
  parts=[]
  for k in t:parts += [np.full((2048,1),k/7),cosine[:,k,None],(cosine[:,k]-cosine[:,0])[:,None],qp*hp[pool[:,k]]]
  for a,b in itertools.combinations(t,2):parts.append(pairs[pool[:,a],pool[:,b],None])
  parts.append(qp);features[:,s]=np.concatenate(parts,axis=1)
 stored=np.fromfile(r/'features.f32',np.float32).reshape(2048,56,76);err=float(np.abs(stored.astype(float)-features).max());assert err<2e-6,err
 verification.append(dict(dataset=ds,outputs=2048*56,labels_GT_verified=True,complete_real_triples=True,native_feature_numpy_max_error=err,oracle_delta_pp=float((hits.max(axis=1).astype(float)-hits[:,0]).mean()*10)))
assert len(TRIP)==56 and np.array_equal(NEXT[:,0],np.arange(56))
for s,row in enumerate(NEXT):
 assert len(set(row.tolist()))==16
 for t in row[1:]:assert len(set(TRIP[s])^set(TRIP[t]))==2
 reached={0}
 for _ in range(3):reached.update(NEXT[list(reached)].reshape(-1).tolist())
 assert len(reached)==56
# Exact path enumeration verifies the same three-step policy and score-function gradient.
rng=np.random.default_rng(20260919);f=torch.tensor(rng.normal(size=(1,56)),requires_grad=True);u=rng.normal(size=56);u[0]=0;p=probabilities(f).detach().numpy()[0];b=rng.normal(size=(3,56));grads=np.zeros((2,56));value=0.;mass=0.;leaves=0
def walk(s,depth,prob,path):
 global value,mass,leaves
 for a in range(16):
  t=NEXT[s,a];weight=prob*p[s,a];newpath=path+[(s,a)];terminal=a==0 or depth==2
  if terminal:
   mass+=weight;value+=weight*u[t];leaves+=1
   telescoping=sum(u[NEXT[ss,aa]]-u[ss] for ss,aa in newpath);assert abs(telescoping-u[t])<1e-12
   for k,(ss,aa) in enumerate(newpath):
    jac=np.zeros(56);jac[NEXT[ss]]-=p[ss];jac[NEXT[ss,aa]]+=1
    grads[0]+=weight*(u[t]-u[ss])*jac;grads[1]+=weight*(u[t]-u[ss]-b[k,ss])*jac
  else:walk(t,depth+1,weight,newpath)
walk(0,0,1.,[]);dp=expected_terminal(f,torch.tensor(u[None,:]));dp.backward();g=f.grad.detach().numpy()[0];dp_error=abs(value-float(dp.detach()))
assert abs(mass-1)<1e-12 and dp_error<1e-12
assert np.max(np.abs(grads-g))<2e-12 and abs(g.sum())<1e-12
finite=[]
for j in [0,1,2,7,17,30,42,55]:
 a=f.detach().clone();a[0,j]+=1e-5;plus=float(expected_terminal(a,torch.tensor(u[None,:])));a[0,j]-=2e-5;minus=float(expected_terminal(a,torch.tensor(u[None,:])));finite.append(abs((plus-minus)/2e-5-g[j]))
assert max(finite)<1e-9
torch.manual_seed(20260919);net=Network()
with torch.no_grad():net.net[4].weight.normal_(0,.1)
x=torch.tensor(rng.normal(size=(2,56,76)));uu=torch.tensor(rng.normal(size=(2,56)));objective=expected_terminal(net(x),uu).mean();objective.backward();errs=[]
for name,param in net.named_parameters():
 flat=param.data.reshape(-1);grad=param.grad.reshape(-1)
 for j in sorted(set([0,len(flat)//2,len(flat)-1])):
  value=float(flat[j]);flat[j]=value+1e-5;plus=float(expected_terminal(net(x),uu).mean().detach());flat[j]=value-1e-5;minus=float(expected_terminal(net(x),uu).mean().detach());flat[j]=value
  errs.append(abs((plus-minus)/2e-5-float(grad[j])))
assert max(errs)<2e-6,errs
dump(O/'reviews/preflight.json',dict(status='PASS',datasets=verification,states=56,actions_per_state=16,horizon=3,enumerated_terminal_paths=leaves,path_probability_mass=mass,DP_value_error=dp_error,score_function_max_error=float(np.max(np.abs(grads-g))),finite_difference_score_error=max(finite),network_gradient_finite_difference_error=max(errs),new_NSG_calls=0,optimizer_updates=0))
freeze(O/'reviews/before_training.json',[p for p in (O/'src').glob('*.py')]+[p for ds in DS for p in (O/'results'/('labels_'+ds)).glob('*') if p.is_file()]+[O/'protocol.md'])
dump(O/'state.json',dict(status='TRAINING_READY',training_runs=0,validation_read=False,heldout_read=False));print('PREFLIGHT_PASS',verification,flush=True)
