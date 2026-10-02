from shared import *
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json')
name='preflight_'+ds;reserve(name,6000)
sys.path.insert(0,str(E37/'src'));from native import Native
c=read(O/'inputs'/ds/'config.json');p=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim'])
b=np.fromfile(c['basis'],np.float64).reshape(c['dim'],16);scale=np.load(O/'inputs'/ds/'local_parameters.npz')['scale']
# Check the exact baseline cancellation and independent componentwise estimators.
rng=np.random.default_rng(37143);tests=[]
for arm in ARMS:
 eps=rng.normal(size=(8 if arm=='rl' else 4,16))
 if arm=='es':eps=np.r_[eps,-eps]
 rewards=rng.normal(size=8);g=gradient(arm,rewards,eps)
 expected=[]
 for j in range(16):
  if arm=='rl':v=sum((rewards[i]-sum(rewards[k] for k in range(8) if k!=i)/7)*eps[i,j] for i in range(8))/(8*SIGMA)
  else:v=sum((rewards[i]-rewards[i+4])*eps[i,j] for i in range(4))/(8*SIGMA)
  expected.append(v)
 np.testing.assert_allclose(g,expected,atol=1e-14)
 np.testing.assert_allclose(g,gradient(arm,rewards-1.735,eps),atol=1e-14)
 np.testing.assert_allclose(gradient(arm,np.ones(8)*1.375,eps),0,atol=1e-14)
 tests.append(arm)
for i in range(len(p)):assert row_profile(p[i],b,scale[i],np.zeros(16)).tobytes()==p[i].tobytes()
z=rng.normal(size=16);slot=0;row=row_profile(p[slot],b,scale[slot],z)
y=np.array([float(p[slot,j])+.0625*scale[slot]*sum(float(np.tanh(z[k]))*float(b[j,k]) for k in range(16)) for j in range(c['dim'])])
np.testing.assert_allclose(row,y/np.linalg.norm(y),atol=4e-8,rtol=1e-7)
current=np.zeros(16);m=current.copy();v=current.copy();g=rng.normal(size=16)
mu,m1,v1,norm=update(current,m,v,g,1,1);clipped=g/max(1,np.linalg.norm(g))
np.testing.assert_allclose(mu,np.clip(.03*clipped/(np.abs(clipped)+1e-8),-2,2),atol=1e-14)
t=time.monotonic();native=Native(c);dest=O/'results'/ds/'preflight';dest.mkdir(parents=True)
top=native.build(p);native.save(dest/'baseline.hnsw');raw=native.run(np.arange(5120));old=dict(np.load(E37/'results'/ds/'baseline.npz'));equal(raw,old)
gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100);assert np.array_equal(score(raw['ids'],gt),old['hits'])
save(dest/'baseline.npz',**raw,hits=score(raw['ids'],gt));native.verify(dest/'baseline.hnsw',np.arange(32))
assert native.build(p)==top;equal(native.run(np.arange(32)),{k:raw[k][:32] for k in FIELDS})
w=p.copy();w[slot]=row;ctop=native.build(w);native.save(dest/'local.hnsw');local=native.run(np.arange(64));save(dest/'local.npz',**local,slot=np.array(slot),z=z,row=row)
native.verify(dest/'local.hnsw',np.arange(32));stats=native.stats();native.close()
assert stats['NSG_calls']==5408 and stats['builds']==3 and stats['actual_threads']==1
rec=dict(status='PASS',dataset=ds,gradient_and_baseline_cancellation=tests,zero_rows=len(p),original_baseline_rows=5120,
 baseline_topology_sha=top,local_topology_sha=ctop,scalar_profile_tolerance=4e-8,seconds=time.monotonic()-t,**stats)
dump(O/'reviews'/('preflight_'+ds+'.json'),rec);finish(name,stats['NSG_calls'],native=stats)
print(json.dumps(rec),flush=True)
