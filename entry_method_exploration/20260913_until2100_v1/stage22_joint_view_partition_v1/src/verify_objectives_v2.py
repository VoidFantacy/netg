from common import *
threads();assert read(O/'results/offline.json')['status']=='PASS';records=[];t=time.monotonic()
for ds in DS:
 c=read(O/'inputs'/ds/'construction.json');f=O/'models'/ds/'joint10';a=dict(np.load(f/'training.npz'));j=dict(np.load(f/'objectives.npz'));J=j['joint_objective'];V=j['view_norms_initial_final'];assert J.shape==(len(a['active']),21) and V.shape==(len(a['active']),2,4);assert np.all(np.diff(J,axis=1)>=-1e-9);assert np.allclose(J[:,0],V[:,0].sum(1),atol=1e-12,rtol=0) and np.allclose(J[:,-1],V[:,1].sum(1),atol=1e-12,rtol=0)
 assert np.allclose(np.linalg.norm(a['sum0'],axis=1),V[:,1,0],atol=1e-12,rtol=0) and np.allclose(np.linalg.norm(a['sum1'],axis=1),V[:,1,1],atol=1e-12,rtol=0)
 assert np.all((~a['eligible']) | (~a['invalid']));ix=np.linspace(0,len(a['active'])-1,12,dtype=int);hubs=a['active'][ix];n=20000;d=c['dim'];h=c['hub_count'];R32=normalize(np.fromfile(c['raw_hubs'],np.float32).reshape(h,d));Q=normalize(np.fromfile(c['queries_file'],np.float32,count=n*d).reshape(n,d)).astype(float);gt=np.fromfile(c['gt_file'],np.int64,count=n*100).reshape(n,100)[:,:10];base=np.memmap(c['base_file'],np.float32,mode='r').reshape(-1,d+1);weights=np.empty((10,n,12),np.float64);targets=np.empty((n,10,d),np.float64)
 for rank in range(10):
  block=np.array(base[gt[:,rank]],copy=True);T=normalize(block[:,1:]);targets[:,rank]=T
  for st in range(0,n,4096):
   en=min(st+4096,n);s=T[st:en]@R32.T
   if c['temperature'] is None:aa=np.zeros(s.shape,np.float64);aa[np.arange(en-st),np.argmax(s,axis=1)]=1
   else:aa=s.astype(float);aa-=aa.max(1,keepdims=True);aa/=c['temperature'];np.exp(aa,out=aa);aa/=aa.sum(1,keepdims=True)
   weights[rank,st:en]=aa[:,hubs]
 old=dict(np.load(E66/'models'/ds/'training.npz'));g0=np.unpackbits(old['assignment_bits'],axis=0,count=n).astype(bool);g1=np.unpackbits(a['assignment_bits'],axis=0,count=n).astype(bool);maxerr=0
 for k,jj in enumerate(ix):
  rw=weights[:,:,k].T.copy();den=rw.sum(1);w=np.zeros(n)
  for rank in range(10):w+=weights[rank,:,k]/10
  beta=np.divide(rw,den[:,None],out=np.zeros_like(rw),where=den[:,None]>0);F=normalize(np.einsum('nr,nrd->nd',beta,targets,optimize=True));assert digest(F)==read(f/'manifest.json')['conditional_feature_hub_sha'][jj]
  # Scalar row selections/sums differ from training matrix-vector reduction.
  for phase,g in enumerate([g0[:,jj],g1[:,jj]]):
   ns=np.array([np.linalg.norm(np.sum(w[mask,None]*X[mask],axis=0)) for X in [Q,F] for mask in [g,~g]]);err=float(abs(ns-V[jj,phase]).max());maxerr=max(maxerr,err);assert np.allclose(ns,V[jj,phase],atol=2e-11,rtol=2e-12)
 records.append(dict(dataset=ds,all_hub_trajectories=len(J),fixed_independent_hubs=12,initial_final_views=48,max_norm_error=maxerr,min_J_increase=float(np.diff(J,axis=1).min()),total_J_increase=float((J[:,-1]-J[:,0]).sum()),query_norm_change=float((V[:,1,:2]-V[:,0,:2]).sum()),target_norm_change=float((V[:,1,2:]-V[:,0,2:]).sum())))
 del Q,F,weights,targets,g0,g1,base
resources();dump(O/'reviews/joint_objective_verification.json',dict(status='PASS',datasets=records,seconds=time.monotonic()-t,NSG=0,full_iteration_replay=False,scope='All stored objective trajectories and final Q norms; independent 12 fixed hubs initial/final two-view sums, not replay of all Lloyd steps'));print('E81_OBJECTIVES_PASS',records)
