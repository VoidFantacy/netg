from common import *
from native import Native
import math, resource

assert read(O/'state.json')['status']=='PREPARED_PREFLIGHT_PENDING'
assert not (O/'reviews/preflight.json').exists()
rg=np.random.default_rng(101);eps=rg.normal(size=(8,256));r=rg.normal(size=8)
g=gradient('rl',r,eps);direct=sum((r[i]-np.delete(r,i).mean())*eps[i] for i in range(8))/(8*SIGMA)
assert np.max(np.abs(g-direct))<1e-14
assert np.max(np.abs(gradient('rl',r+7,eps)-g))<1e-13
for arm in ARMS:assert np.max(np.abs(gradient(arm,np.ones(8),eps)))==0
x,w=np.polynomial.hermite.hermgauss(20);z=x*np.sqrt(2);w=w/np.sqrt(np.pi);mu=.7;target=-.4
reward=-(mu+SIGMA*z-target)**2
analytic=-2*(mu-target);quadrature=float(np.sum(w*reward*z/SIGMA))
assert abs(quadrature-analytic)<1e-12
anti=float(np.sum(w*(-(mu+SIGMA*z-target)**2+(mu-SIGMA*z-target)**2)*z/(2*SIGMA)))
assert abs(anti-analytic)<1e-12
theta=rg.normal(size=4);a=theta+SIGMA*rg.normal(size=4);expected=(a-theta)/SIGMA**2
def logp(t):return -np.sum((a-t)**2)/(2*SIGMA**2)
num=[]
for j in range(4):
 v=np.zeros(4);v[j]=1e-6;num.append((logp(theta+v)-logp(theta-v))/2e-6)
assert np.max(np.abs(np.array(num)-expected))<1e-8
mu0=np.zeros(256);gg=rg.normal(size=256);u,m,v,norm=update(mu0,mu0,mu0,gg,1);clipped=gg/max(1,np.linalg.norm(gg))
assert np.max(np.abs(u-.03*clipped/(np.abs(clipped)+1e-8)))<1e-14
dump(O/'reviews/mathematics.json',dict(status='PASS',gaussian_analytic_gradient=analytic,quadrature=quadrature,antithetic=anti,log_density_fd_error=float(np.max(np.abs(np.array(num)-expected))),LOO_independent_baseline=True,constant_reward_zero=True,Adam_first_update=True))
freeze(O/'reviews/before_preflight_queries.json',[O/'protocol.md',O/'config.locked.json']+list((O/'src').glob('*.*'))+list((O/'bin').glob('*'))+[p for p in (O/'inputs').rglob('*') if p.is_file()])
reports=[]
for ds in DS:
 resources();check(O/'reviews/upstream.json',hashes=False);c=read(O/'inputs'/ds/'config.json');dest=O/'results'/ds;dest.mkdir()
 reserve('preflight_'+ds,6000);t=time.time();native=Native(c);p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],RANK)
 assert np.array_equal(profiles(p,b,np.zeros(256)),p)
 topology=native.build(p);native.save(dest/'baseline.hnsw');base=native.run(np.arange(5120));gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);base['hits']=score(base['ids'],gt)
 assert np.isin(base['entries'],np.fromfile(c['hub_ids'],np.int32)).all()
 oldpath=E33/'results'/ds/'baseline.npz';source=np.fromfile(O/'inputs'/ds/'source_local.i32',np.int32)
 with np.load(oldpath) as old:
  for key in ['ids','entries','route_ndc','graph_ndc','distances','hits']:
   expected=old[key][source];assert np.array_equal(base[key].view(np.uint8),expected.copy().view(np.uint8)),key
 np.savez_compressed(dest/'baseline.npz',**base);native.verify(dest/'baseline.hnsw',np.arange(32))
 assert native.build(p)==topology;repeated=native.run(np.arange(64))
 for key in repeated:assert np.array_equal(repeated[key].view(np.uint8),base[key][:64].copy().view(np.uint8)),key
 pre=[]
 for j in range(2):
  action=np.random.default_rng(701+j).normal(size=256)*SIGMA;ww=profiles(p,b,action)
  # Independent scalar accumulation on three profiles (no matrix multiplication).
  aa=np.tanh(action.reshape(16,16))/4
  for h in [0,len(p)//2,len(p)-1]:
   projected=np.array([math.fsum(float(p[h,k])*float(b[k,jj]) for k in range(c['dim'])) for jj in range(16)])
   mid=np.array([math.fsum(float(projected[k])*float(aa[k,jj]) for k in range(16)) for jj in range(16)])
   yy=np.array([float(p[h,k])+.25*math.fsum(float(mid[jj])*float(b[k,jj]) for jj in range(16)) for k in range(c['dim'])]);ref=(yy/np.linalg.norm(yy)).astype(np.float32)
   assert np.max(np.abs(ref-ww[h]))<6e-8
  top=native.build(ww);out=native.run(np.arange(64));folder=dest/f'preflight_{j}';folder.mkdir();native.save(folder/'graph.hnsw');ww.tofile(folder/'W.f32');action.tofile(folder/'action.f64');np.savez_compressed(folder/'raw.npz',**out)
  native.verify(folder/'graph.hnsw',np.arange(32));pre.append(dict(W_sha=digest(ww),topology_sha=top,changed_entries=int(np.any(out['entries']!=base['entries'][:64],axis=1).sum())))
 before=native.stats()['NSG_calls'];rejections=[]
 for tag,op in [('bad_L',lambda:native.run([0],127)),('bad_row',lambda:native.run([-1])),('NaN_profile',lambda:native.build(np.full_like(p,np.nan)))]:
  try:op();raise AssertionError('expected rejection '+tag)
  except RuntimeError:rejections.append(tag)
 assert native.stats()['NSG_calls']==before
 stats=native.stats();native.close();rec=dict(dataset=ds,status='PASS',baseline_parity_queries=5120,native_three_way_parity_queries=96,deterministic_rebuild=True,baseline_topology_sha=topology,baseline_graph_file_sha=sha(dest/'baseline.hnsw'),original_graph_file_sha=sha(c['original_graph']),perturbations=pre,invalid_inputs_rejected=rejections,seconds=time.time()-t,**stats)
 finish('preflight_'+ds,stats['NSG_calls'],**{k:v for k,v in rec.items() if k not in ['NSG_calls','status']});reports.append(rec);dump(O/'reviews/native_preflight.json',reports)
 print('NATIVE_PREFLIGHT_PASS',ds,stats,flush=True)
dump(O/'reviews/preflight.json',dict(status='PASS',mathematics='PASS',datasets=reports,new_NSG_calls=sum(x['NSG_calls'] for x in reports),validation_heldout_access=False))
dump(O/'state.json',dict(status='PREFLIGHT_PASS_TRAINING_PENDING',optimizer_updates=0,NSG_calls=sum(x['NSG_calls'] for x in reports)))
