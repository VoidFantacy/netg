from common import *
import resource,csv,struct
threads();resources();E79=C/'stage20_target_space_modes_v1';E73=C/'stage14_compact_modes_v1';assert not (O/'reviews/offline_freeze.json').exists()
paths=[O/'protocol.md',O/'config.locked.json',E79/'reviews/final_artifact_freeze.json']+list((O/'src').glob('*.py'))
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
for ds in DS:
 c=read(E79/'inputs'/ds/'construction.json');p=O/'inputs'/ds;p.mkdir();dump(p/'construction.json',c)
 paths += [p/'construction.json',E79/'models'/ds/'target10/training.npz',E79/'results'/('offline_'+ds+'.json')]+[Path(c[k]) for k in ['P','queries_file','gt_file','row_ids','hub_ids','raw_hubs']]
freeze(O/'reviews/offline_freeze.json',paths);allrec=[];stats=[]
for ds in DS:
 start=time.monotonic();c=read(O/'inputs'/ds/'construction.json');h,d=c['hub_count'],c['dim'];n=20000
 rows=np.fromfile(c['row_ids'],np.int64,count=n);assert np.array_equal(rows,np.arange(10000,30000))
 P=np.fromfile(c['P'],np.float32).reshape(h,d);Q=normalize(np.fromfile(c['queries_file'],np.float32,count=n*d).reshape(n,d)).astype(float);R32=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d));R=R32.astype(float)
 GT=np.fromfile(c['gt_file'],np.int64,count=n*100).reshape(n,100)[:,:10];base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1);assert struct.unpack('<i',Path(c['base_file']).open('rb').read(4))[0]==d
 assert GT.min()>=0 and GT.max()<len(base);rank_weights=np.empty((10,n,h),np.float64);targets=np.empty((n,10,d),np.float64);A=np.zeros((n,h),np.float64);Tg=np.zeros((n,d),np.float64);ranksha=[]
 for rank in range(10):
  block=np.array(base[GT[:,rank]],copy=True);assert np.all(block[:,0].copy().view(np.int32)==d);raw=block[:,1:];assert np.isfinite(raw).all() and np.all(np.linalg.norm(raw,axis=1)>1e-12);T=normalize(raw);targets[:,rank]=T;Tg+=T.astype(float)
  for st in range(0,n,4096):
   en=min(st+4096,n);s=T[st:en]@R32.T
   if c['temperature'] is None:
    a=np.zeros(s.shape,np.float64);a[np.arange(en-st),np.argmax(s,axis=1)]=1
   else:
    a=s.astype(float);a-=a.max(1,keepdims=True);a/=c['temperature'];np.exp(a,out=a);a/=a.sum(1,keepdims=True)
   rank_weights[rank,st:en]=a;A[st:en]+=a/10
  ranksha.append(digest(rank_weights[rank]))
 assert digest(A)==c['original_assignments_sha'];S=R+A.T@Q;assert normalize(S).astype(np.float32).tobytes()==P.tobytes()
 Tg=normalize(Tg);oldrecord=read(E79/'results'/('offline_'+ds+'.json'));assert digest(Tg)==oldrecord['target_feature_sha']
 old=dict(np.load(E79/'models'/ds/'target10/training.npz'));mass=A.sum(0);ess=mass*mass/np.square(A).sum(0);active=np.flatnonzero((mass>=8)&(ess>=16));assert np.array_equal(active,old['active']);oldmask=np.unpackbits(old['assignment_bits'],axis=0,count=n).astype(bool)
 mask=np.zeros((n,len(active)),bool);seed0=[];seed1=[];invalid=[];eligible=[];masses=[];esses=[];sum0=[];sum1=[];rhos=[];bank=np.repeat(P[:,None,:],3,axis=1);features_sha=[];changed_feature_hubs=0
 fixed_hubs=set(np.linspace(0,len(active)-1,12,dtype=int).tolist());fixed_queries=np.linspace(0,n-1,32,dtype=int);rank_seconds=time.monotonic()-start
 for j,hi in enumerate(active):
  w=A[:,hi];a=rank_weights[:,:,hi].T.copy();den=a.sum(1);nonzero=den>0;assert np.array_equal(nonzero,w>0)
  beta=np.divide(a,den[:,None],out=np.zeros_like(a),where=nonzero[:,None]);assert np.allclose(beta[nonzero].sum(1),1,atol=1e-14)
  F=np.einsum('nr,nrd->nd',beta,targets,optimize=True);norm=np.linalg.norm(F,axis=1);cancel=nonzero&(norm<=1e-12);F=normalize(F);features_sha.append(digest(F))
  if j in fixed_hubs:
   for qi in fixed_queries:
    vv=np.zeros(d)
    for r in range(10):vv+=float(beta[qi,r])*targets[qi,r]
    vv=vv/max(float(np.linalg.norm(vv)),1e-12);assert np.allclose(vv,F[qi],atol=4e-15,rtol=4e-15)
  parent=w@F;pn=np.linalg.norm(parent);parent=parent/max(pn,1e-12)
  s0=int(np.argmax(w*(1+F@parent)));c0=F[s0].copy();s1=int(np.argmax(w*(1-F@c0)));c1=F[s1].copy();bad=bool(cancel.any() or pn<=1e-12);tot=w@F
  for it in range(20):
   g=F@c0>=F@c1;w0=w*g;f0=w0@F;f1=tot-f0;m0=w0.sum();nn0=np.linalg.norm(f0);nn1=np.linalg.norm(f1);b=nn0<=1e-12 or nn1<=1e-12 or m0<=0 or m0>=mass[hi];bad|=bool(b)
   if not b:c0=f0/nn0;c1=f1/nn1
  mask[:,j]=g;seed0.append(s0);seed1.append(s1);m1=mass[hi]-m0;w1=w*(~g);e0=m0*m0/max(float(w0@w0),1e-300);e1=m1*m1/max(float(w1@w1),1e-300);rho=m0/mass[hi]
  q0=w0@Q;q1=w@Q-q0;u0=rho*R[hi]+q0;u1=(1-rho)*R[hi]+q1;assert np.allclose(u0+u1,R[hi]+w@Q,atol=2e-12,rtol=2e-12)
  ok=not bad and m0>=2 and m1>=2 and e0>=8 and e1>=8 and np.linalg.norm(u0)>1e-12 and np.linalg.norm(u1)>1e-12
  if ok:bank[hi,1]=u0/np.linalg.norm(u0);bank[hi,2]=u1/np.linalg.norm(u1)
  if j in fixed_hubs:
   ss0=np.sum(w[g,None]*Q[g],axis=0);ss1=np.sum(w[~g,None]*Q[~g],axis=0);assert np.allclose(ss0,q0,atol=2e-12,rtol=2e-12) and np.allclose(ss1,q1,atol=2e-12,rtol=2e-12)
  invalid.append(bad);eligible.append(ok);masses.append([m0,m1]);esses.append([e0,e1]);sum0.append(q0);sum1.append(q1);rhos.append(rho)
  cos=np.sum(F*Tg,axis=1);drift=float(w@(1-cos)/mass[hi]);changed_feature_hubs+=drift>1e-8;xor=g!=oldmask[:,j];wt=float(w@xor);discord=min(wt,mass[hi]-wt)/mass[hi]
  effective=np.divide(1,np.square(beta).sum(1),out=np.zeros(n),where=nonzero);stats.append(dict(dataset=ds,hub_slot=int(hi),parent_mass=float(mass[hi]),weighted_target_drift=drift,effective_target_count=float(w@effective/mass[hi]),weighted_partition_disagreement_modulo_labels=float(discord),conditional_eligible=bool(ok),global_eligible=bool(old['eligible'][j]),cancelled_positive_queries=int(cancel.sum()),child0_mass=float(m0),child1_mass=float(m1),child0_ESS=float(e0),child1_ESS=float(e1)))
  assert time.monotonic()-start<900 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<16*(1<<20)
  if j%100==0:print(ds,'hub',j,'/',len(active),'seconds',round(time.monotonic()-start,2),flush=True)
 assert changed_feature_hubs>0
 folder=O/'models'/ds/'conditional10';folder.mkdir(parents=True);W0=bank.reshape(3*h,d);ids=np.fromfile(c['hub_ids'],np.int32);mp0=np.repeat(ids,3);lookup={};keep=[];o2n=[]
 for i,(hub,w) in enumerate(zip(mp0,W0)):
  key=(int(hub),w.tobytes())
  if key not in lookup:lookup[key]=len(keep);keep.append(i)
  o2n.append(lookup[key])
 keep=np.array(keep,np.int32);o2n=np.array(o2n,np.int32);W=W0[keep];mp=mp0[keep];assert W[o2n].tobytes()==W0.tobytes() and W0[::3].tobytes()==P.tobytes();assert np.allclose(np.linalg.norm(W.astype(float),axis=1),1,atol=1e-7)
 W.tofile(folder/'W.f32');mp.tofile(folder/'mapping.i32');np.arange(len(W),dtype=np.int32).tofile(folder/'tie_ids.i32');keep.tofile(folder/'original_slots.i32');o2n.tofile(folder/'old_to_compact.i32')
 save(folder/'training.npz',active=active,parent_mass=mass,parent_ESS=ess,seed0=np.array(seed0),seed1=np.array(seed1),assignment_bits=np.packbits(mask,axis=0),child_mass=np.array(masses),child_ESS=np.array(esses),invalid=np.array(invalid),eligible=np.array(eligible),rho=np.array(rhos),sum0=np.array(sum0),sum1=np.array(sum1),source_rows=rows)
 oldm=next(m for m in read(E73/'inputs'/ds/'aux.json')['methods'] if m['model_name']=='compact10');model=dict(oldm,model_name='conditional10',name='conditional10_L128',W=str(folder/'W.f32'),mapping=str(folder/'mapping.i32'),tie_ids=str(folder/'tie_ids.i32'),graph_file=str(folder/'graph.hnsw'),hub_count=len(W));dump(folder/'model.json',model)
 rec=dict(dataset=ds,status='PASS',A_P_recovered=True,A_sha=digest(A),rank_weight_sha=ranksha,global_target_sha=digest(Tg),conditional_feature_hub_sha=features_sha,changed_feature_hubs=int(changed_feature_hubs),active_hubs=len(active),eligible_hubs=int(np.sum(eligible)),physical_profiles=len(W),scalar_feature_checks=32*12,scalar_aggregate_hubs=12,rank_reconstruction_seconds=rank_seconds,seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 dump(folder/'manifest.json',rec);allrec.append(rec);dump(O/'results'/('offline_'+ds+'.json'),rec);resources();print('CONDITIONAL_COMPLETE',ds,len(W),rec['seconds'],flush=True)
 del rank_weights,targets,A,Q,R,R32,base,Tg,F,mask,oldmask
with (O/'results/conditional_support.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
check(O/'reviews/offline_freeze.json');dump(O/'results/offline.json',dict(status='PASS',datasets=allrec,offline_fits=2,new_NSG=0,new_HNSW=0,builds=0,new_GT=0,gradient_updates=0))
freeze(O/'reviews/offline_models_freeze.json',[p for p in (O/'models').rglob('*') if p.is_file()]+list((O/'results').glob('*')))
dump(O/'state.json',dict(status='CONDITIONAL_OFFLINE_PASS_UNQUERIED',NSG=0,HNSW=0,builds=0,day_goal_complete=False));print('E80_OFFLINE_PASS')
