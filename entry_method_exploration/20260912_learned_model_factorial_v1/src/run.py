from shared import *
from native_factorial import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json');assert time.time()<1789218900
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
p=O/'logs/jobs.json';jobs=read(p) if p.exists() else [];assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved'] for x in jobs)+50000<=100000
job=dict(dataset=ds,status='RUNNING',reserved=50000,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(p,jobs)
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c);records=[];normal=0
base=dict(np.load(E37/'results'/ds/'baseline.npz'));P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);rows=np.arange(5120,dtype=np.int32);pr=np.r_[rows[:32],rows[4096:4128]]
def evaluate(key,cell,w,top,expected=None):
 global normal
 assert time.time()<QUERY_STOP and time.monotonic()-started<900;resources()
 dest=O/'results'/ds/key/cell;dest.mkdir(parents=True);native.verify_vectors(w);assert digest(native.data(5,np.int32))==top
 route=native.route(rows);changed=np.flatnonzero((route['entries']!=base['entries']).any(1)).astype(np.int32)
 patch=native.search_entries(changed,route['entries'][changed]);out={k:base[k].copy() for k in ['ids','distances','graph_ndc']};out.update(route)
 for k in patch:out[k][changed]=patch[k]
 if expected is not None:equal(out,expected)
 save(dest/'raw.npz',**out);save(dest/'patch.npz',changed_rows=changed,entries=route['entries'][changed],**patch)
 save(dest/'topology.npz',topology=native.data(5,np.int32));w.tofile(dest/'W.f32');native.save(dest/'graph.hnsw');native.verify(dest/'graph.hnsw',pr)
 parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
 equal(parity,subset(out,pr));save(dest/'parity.npz',**parity);normal+=len(changed)
 rec=dict(dataset=ds,key=key,cell=cell,W_sha=digest(w),topology_sha=top,new_NSG=len(changed),graph_sha=sha(dest/'graph.hnsw'),parity_rows=64,vector_bytes_match=True)
 dump(dest/'identity.json',rec);records.append(rec)
try:
 g0=native.build(P);t0=native.data(5,np.int32);evaluate('baseline','C',P,g0,base)
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  w=np.fromfile(rec['W'],np.float32).reshape(P.shape);g=native.build(w);assert g==rec['topology_sha'];t=native.data(5,np.int32)
  evaluate(rec['key'],'A',w,g,dict(np.load(rec['checkpoint'])));assert sha(O/'results'/ds/rec['key']/'A/graph.hnsw')==sha(rec['graph'])
  assert native.install_topology(t0)==g0;evaluate(rec['key'],'S',w,g0)
  assert native.build(P)==g0 and native.install_topology(t)==g;evaluate(rec['key'],'T',P,g)
  print('MODEL_COMPLETE',ds,rec['key'],native.stats(),flush=True)
 stats=native.stats();assert stats['NSG_calls']==normal+2496 and stats['HNSW_calls']==68224 and stats['builds']==9 and native.installation_count()==8 and stats['actual_threads']==1
 out=dict(status='PASS',dataset=ds,states=len(records),installations=8,normal_new_NSG=normal,seconds=time.monotonic()-started,**stats)
 dump(O/'results'/ds/'points.json',records);dump(O/'results'/ds/'query_complete.json',out)
 job.update(status='COMPLETE',actual=stats['NSG_calls'],native=stats,completed_at=time.time());dump(p,jobs);print('DATASET_COMPLETE',json.dumps(out),flush=True)
finally:native.close()
