from common import *
from assignment import recover
import resource,struct,csv
threads();resources();assert not (O/'reviews/offline_freeze.json').exists()
E73=C/'stage14_compact_modes_v1'
paths=[O/'protocol.md',O/'config.locked.json']+list((O/'src').glob('*.py'))
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
for ds in DS:
 c=read(E66/'inputs'/ds/'construction.json');p=O/'inputs'/ds;p.mkdir();dump(p/'construction.json',c)
 paths+=[p/'construction.json',E66/'models'/ds/'training.npz',E66/'models'/ds/'mode3P/W.f32']+[Path(c[k]) for k in ['P','queries_file','gt_file','row_ids','hub_ids','raw_hubs']]
freeze(O/'reviews/offline_freeze.json',paths)
records=[];cohorts=[]
def cluster(A,F,parent,start):
 mass=A.sum(0);ess=mass**2/np.square(A).sum(0);active=np.flatnonzero((mass>=8)&(ess>=16));B=A[:,active];total=B.T@F
 seed0=np.argmax(B*(1+F@parent[active].T),axis=0);cent0=F[seed0].copy();seed1=np.argmax(B*(1-F@cent0.T),axis=0);cent1=F[seed1].copy()
 invalid=np.linalg.norm(parent[active],axis=1)<=1e-12;trajectory=[];previous=None
 for it in range(20):
  mask=F@cent0.T>=F@cent1.T;B0=B*mask;S0=B0.T@F;S1=total-S0
  n0=np.linalg.norm(S0,axis=1);n1=np.linalg.norm(S1,axis=1);m0=B0.sum(0)
  bad=(n0<=1e-12)|(n1<=1e-12)|(m0<=0)|(m0>=mass[active]);invalid|=bad;ok=~bad
  cent0[ok]=S0[ok]/n0[ok,None];cent1[ok]=S1[ok]/n1[ok,None]
  trajectory.append(dict(iteration=it+1,changed=None if previous is None else int(np.count_nonzero(mask!=previous)),bad_hubs=int(bad.sum())))
  previous=mask.copy();assert time.monotonic()-start<900
  assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<16*(1<<20)
 m0=B0.sum(0);m1=mass[active]-m0;B1=B*(~mask)
 e0=np.divide(m0*m0,np.square(B0).sum(0),out=np.zeros_like(m0),where=m0>0);e1=np.divide(m1*m1,np.square(B1).sum(0),out=np.zeros_like(m1),where=m1>0)
 eligible=(~invalid)&(m0>=2)&(m1>=2)&(e0>=8)&(e1>=8)
 return dict(active=active,parent_mass=mass,parent_ESS=ess,seed0=seed0,seed1=seed1,mask=mask,assignment_bits=np.packbits(mask,axis=0),child_mass=np.stack([m0,m1],1),child_ESS=np.stack([e0,e1],1),invalid=invalid,eligible=eligible,rho=m0/mass[active]),trajectory
for ds in DS:
 start=time.monotonic();c=read(O/'inputs'/ds/'construction.json');h,d=c['hub_count'],c['dim']
 rows=np.fromfile(c['row_ids'],np.int64,count=20000);assert np.array_equal(rows,np.arange(10000,30000))
 A,Q,R,P=recover(c);recovery_sec=time.monotonic()-start
 assert np.max(abs(A.sum(1)-1))<1e-12
 old=dict(np.load(E66/'models'/ds/'training.npz'));qfit,qt=cluster(A,Q,P.astype(float),start)
 for k in ['active','seed0','seed1','assignment_bits','eligible','invalid']:assert np.array_equal(qfit[k],old[k]),(ds,k)
 active=qfit['active'];S0=(A[:,active]*qfit['mask']).T@Q;S1=A[:,active].T@Q-S0
 for k,x in [('sum0',S0),('sum1',S1),('child_mass',qfit['child_mass']),('child_ESS',qfit['child_ESS'])]:assert np.array_equal(x,old[k]),(ds,k)
 qmodes=np.repeat(P[:,None,:],3,axis=1);ii=active[qfit['eligible']];u0=qfit['rho'][:,None]*R[active]+S0;u1=(1-qfit['rho'][:,None])*R[active]+S1
 qmodes[ii,1]=normalize(u0[qfit['eligible']]).astype(np.float32);qmodes[ii,2]=normalize(u1[qfit['eligible']]).astype(np.float32)
 assert qmodes.tobytes()==Path(E66/'models'/ds/'mode3P/W.f32').read_bytes()
 oldQ_seconds=time.monotonic()-start-recovery_sec;del qmodes,S0,S1
 GT=np.fromfile(c['gt_file'],np.int64,count=20000*100).reshape(20000,100)[:,:10]
 base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1);assert struct.unpack('<i',Path(c['base_file']).open('rb').read(4))[0]==d
 assert GT.min()>=0 and GT.max()<len(base);T=np.zeros((20000,d),np.float64);chunks=[];target_start=time.monotonic();min_norm=float('inf')
 for rank in range(10):
  block=np.array(base[GT[:,rank]],copy=True);assert np.all(block[:,0].copy().view(np.int32)==d);raw=block[:,1:];norm=np.linalg.norm(raw,axis=1)
  assert np.isfinite(raw).all() and np.all(norm>1e-12);min_norm=min(min_norm,float(norm.min()));v=normalize(raw);T+=v.astype(float);chunks.append(digest(v))
 summed_norm=np.linalg.norm(T,axis=1);assert np.all(summed_norm>1e-12);T=normalize(T);assert np.isfinite(T).all()
 # Independent rank-by-rank float32 norm and scalar coordinates on fixed source rows.
 for i in np.linspace(0,19999,32,dtype=int):
  vv=np.array(base[GT[i],1:],np.float32);vv=vv/np.sqrt(np.sum(vv*vv,axis=1,keepdims=True));z=np.array([sum(float(vv[r,j]) for r in range(10)) for j in range(d)]);z/=np.sqrt(sum(float(a*a) for a in z));assert np.allclose(z,T[i],atol=3e-15,rtol=3e-15)
 target_seconds=time.monotonic()-target_start;permutation=np.random.default_rng(read(O/'config.locked.json')['permutation_seed']).permutation(20000)
 dest=O/'models'/ds;dest.mkdir();permutation.astype(np.int32).tofile(dest/'target_permutation.i32');variants=[]
 for name,F in [('target10',T),('permuted10',T[permutation])]:
  tick=time.monotonic();parent=normalize(A.T@F);fit,traj=cluster(A,F,parent,start);assert np.array_equal(fit['active'],active)
  m=fit['mask'];B0=A[:,active]*m;sum0=B0.T@Q;sum1=A[:,active].T@Q-sum0;rho=fit['rho'];u0=rho[:,None]*R[active]+sum0;u1=(1-rho[:,None])*R[active]+sum1
  assert np.max(abs(u0+u1-(R[active]+A[:,active].T@Q)))<2e-12
  eligible=fit['eligible'];norm0=np.linalg.norm(u0,axis=1);norm1=np.linalg.norm(u1,axis=1);eligible &= (norm0>1e-12)&(norm1>1e-12);fit['eligible']=eligible
  bank=np.repeat(P[:,None,:],3,axis=1);ii=active[eligible];bank[ii,1]=normalize(u0[eligible]).astype(np.float32);bank[ii,2]=normalize(u1[eligible]).astype(np.float32)
  # Scalar loop aggregation on fixed active hubs independent of matrix multiplication.
  for j in np.linspace(0,len(active)-1,12,dtype=int):
   aw=A[:,active[j]];is0=m[:,j];ss0=np.sum((aw[is0,None]*Q[is0]),axis=0);ss1=np.sum((aw[~is0,None]*Q[~is0]),axis=0)
   assert np.allclose(ss0,sum0[j],atol=2e-12,rtol=2e-12) and np.allclose(ss1,sum1[j],atol=2e-12,rtol=2e-12)
   if eligible[j]:
    v=np.stack([rho[j]*R[active[j]]+ss0,(1-rho[j])*R[active[j]]+ss1]);assert np.allclose(normalize(v),bank[active[j],1:],atol=6e-8,rtol=6e-8)
  source_bank=bank.reshape(3*h,d);ids=np.fromfile(c['hub_ids'],np.int32);mapping=np.repeat(ids,3);lookup={};keep=[];o2n=[]
  for i,(hub,w) in enumerate(zip(mapping,source_bank)):
   key=(int(hub),w.tobytes())
   if key not in lookup:lookup[key]=len(keep);keep.append(i)
   o2n.append(lookup[key])
  keep=np.array(keep,np.int32);o2n=np.array(o2n,np.int32);W=source_bank[keep];mp=mapping[keep]
  assert W[o2n].tobytes()==source_bank.tobytes() and source_bank[::3].tobytes()==P.tobytes()
  assert len(W)<=3*h and len(set(mp.tolist()))==h and np.allclose(np.linalg.norm(W.astype(float),axis=1),1,atol=1e-7)
  folder=dest/name;folder.mkdir();W.tofile(folder/'W.f32');mp.tofile(folder/'mapping.i32');np.arange(len(W),dtype=np.int32).tofile(folder/'tie_ids.i32');keep.tofile(folder/'original_slots.i32');o2n.tofile(folder/'old_to_compact.i32')
  fit.pop('mask');fit.update(sum0=sum0,sum1=sum1,source_rows=rows);save(folder/'training.npz',**fit)
  base_model=next(x for x in read(E73/'inputs'/ds/'aux.json')['methods'] if x['model_name']=='compact10')
  model=dict(base_model,model_name=name,name=name+'_L128',W=str(folder/'W.f32'),mapping=str(folder/'mapping.i32'),tie_ids=str(folder/'tie_ids.i32'),graph_file=str(folder/'graph.hnsw'),hub_count=len(W));dump(folder/'model.json',model)
  xor=m!=qfit['mask'];weighted=(A[:,active]*xor).sum(0);discord=np.minimum(weighted,fit['parent_mass'][active]-weighted)/fit['parent_mass'][active]
  for j,hidx in enumerate(active):cohorts.append(dict(dataset=ds,model=name,hub=int(ids[hidx]),active_index=j,parent_mass=float(fit['parent_mass'][hidx]),weighted_disagreement_modulo_labels=float(discord[j]),raw_label_disagreement=float(xor[:,j].mean()),eligible=bool(eligible[j]),old_Q_eligible=bool(qfit['eligible'][j]),child0_mass=float(fit['child_mass'][j,0]),child1_mass=float(fit['child_mass'][j,1]),child0_ESS=float(fit['child_ESS'][j,0]),child1_ESS=float(fit['child_ESS'][j,1])))
  rec=dict(model=name,physical_profiles=len(W),unique_hubs=h,eligible=int(eligible.sum()),invalid=int(fit['invalid'].sum()),mean_weighted_disagreement_modulo_labels=float(discord.mean()),weighted_disagreement_quantiles=np.quantile(discord,[0,.25,.5,.75,1]).tolist(),assignment_sha=digest(fit['assignment_bits']),W=identity(folder/'W.f32'),feature_sha=digest(F),seconds=time.monotonic()-tick,trajectory=traj)
  dump(folder/'manifest.json',rec);variants.append(rec);print(ds,name,'built',len(W),'seconds',rec['seconds'],flush=True);resources()
 rec=dict(dataset=ds,status='PASS',A_P_Q_original_recovery=True,assignment_sha=digest(A),source_namespace=c['namespace'],source_rows=[10000,30000],target_feature_sha=digest(T),target_rank_chunk_sha=chunks,target_sum_norm_quantiles=np.quantile(summed_norm,[0,.5,1]).tolist(),min_target_norm=min_norm,scalar_target_rows=32,permutation_sha=digest(permutation.astype(np.int32)),target_seconds=target_seconds,recovery_seconds=recovery_sec,old_Q_reconstruction_seconds=oldQ_seconds,seconds=time.monotonic()-start,variants=variants,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 records.append(rec);dump(O/'results'/('offline_'+ds+'.json'),rec);print('OFFLINE_COMPLETE',ds,rec['seconds'],flush=True)
with (O/'results/partition_comparison.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(cohorts[0]));w.writeheader();w.writerows(cohorts)
check(O/'reviews/offline_freeze.json');dump(O/'results/offline.json',dict(status='PASS',datasets=records,new_NSG=0,new_HNSW=0,builds=0,new_GT=0,offline_fits=4,old_Q_reconstructions=2,gradient_updates=0))
freeze(O/'reviews/offline_models_freeze.json',[p for p in (O/'models').rglob('*') if p.is_file()]+list((O/'results').glob('*')))
dump(O/'state.json',dict(status='OFFLINE_MODELS_PASS_UNQUERIED',NSG=0,HNSW=0,builds=0,day_goal_complete=False));print('E79_OFFLINE_PASS')
