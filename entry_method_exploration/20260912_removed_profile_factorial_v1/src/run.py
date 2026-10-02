from shared import *
ds=sys.argv[1];assert ds in DS
threads(15);resources();check(O/'reviews/prequery_freeze.json')
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else []
assert not any(x['dataset']==ds for x in jobs),'job already reserved; no automatic retry'
assert sum(x['reserved'] for x in jobs)+4288<=10000
job=dict(dataset=ds,status='RUNNING',reserved=4288,started_at=time.time(),pid=os.getpid());jobs.append(job);dump(ledger,jobs)
sys.path.insert(0,str(E37/'src'))
from native import Native
c=cfg(ds);rows=np.load(O/'inputs'/ds/'rows.npz')['rows'];begin=time.monotonic()
n=Native(c);load_seconds=time.monotonic()-begin
try:
 for cell in CELLS:
  resources();p=O/'models'/ds/cell;w=np.fromfile(p/'W.f32',np.float32).reshape(c['hub_count'],c['dim'])
  meta=read(p/'construction.json');topology=n.build(w);n.save(p/'graph.hnsw')
  if cell in ['C','F']:
   assert topology==meta['expected_topology_sha'] and sha(p/'graph.hnsw')==meta['expected_graph_sha']
  raw=n.run(rows)
  if cell in ['C','F']:
   old=dict(np.load(meta['old_result']));assert np.array_equal(old['rows'],rows);equal(raw,old)
  save_np(O/'results'/ds/(cell+'.npz'),rows=rows,**raw)
  n.verify(p/'graph.hnsw',rows[:16])
  parity=dict(ids=n.data(0,np.int32).reshape(16,10),distances=n.data(1,np.float32).reshape(16,10),
      entries=n.data(2,np.int32).reshape(16,3),route_ndc=n.data(3,np.uint32),graph_ndc=n.data(4,np.uint32))
  equal(parity,{k:raw[k][:16] for k in FIELDS});save_np(p/'parity.npz',rows=rows[:16],**parity)
  st=n.stats();assert st['actual_threads']==1
  record=dict(dataset=ds,cell=cell,W_sha=digest(w),topology_sha=topology,graph_file_sha=sha(p/'graph.hnsw'),
      original_parity='PASS',E39_regression='PASS' if cell in ['C','F'] else 'new_counterfactual',native=st)
  dump(p/'identity.json',record);print(json.dumps(record),flush=True)
 st=n.stats();assert st['NSG_calls']==4288 and st['HNSW_calls']==4224 and st['builds']==4
 job.update(status='COMPLETE',actual=st['NSG_calls'],native=st,wall_seconds=time.monotonic()-begin,
       load_seconds=load_seconds,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,completed_at=time.time())
 dump(ledger,jobs)
finally:n.close()
