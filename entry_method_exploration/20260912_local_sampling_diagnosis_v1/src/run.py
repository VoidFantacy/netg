from shared import *
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json')
assert time.time()<QUERY_STOP-900,'too late to launch bounded dataset job'
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else []
assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs),'no retry or concurrent query job'
assert sum(x['reserved'] for x in jobs)+369504<=CAP
job=dict(dataset=ds,status='RUNNING',reserved=369504,reserved_builds=90,pid=os.getpid(),started_at=time.time())
jobs.append(job);dump(ledger,jobs)
sys.path.insert(0,str(E37/'src'));from native import Native
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c)
contexts=[x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]
try:
 for rec in contexts:
  resources();assert time.time()<QUERY_STOP and time.monotonic()-started<900
  step=rec['step'];slot=rec['slot'];w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim'])
  t=dict(np.load(rec['trajectory']));assert digest(w)==rec['current_W_sha']
  for a in range(-1,8):
   assert time.time()<QUERY_STOP and time.monotonic()-started<900
   dest=O/'results'/ds/f'{step:04}'/('C' if a<0 else f'A{a}');dest.mkdir(parents=True)
   ww=w.copy()
   if a>=0:ww[slot]=t['candidate_rows'][a]
   expected=rec['current_topology_sha'] if a<0 else rec['candidate_topology_sha'][a]
   top=native.build(ww);assert top==expected
   save(dest/'topology.npz',topology=native.data(5,np.int32))
   raw=native.run(np.arange(4096,dtype=np.int32))
   old={k:t['current_'+k] if a<0 else t[k][a] for k in FIELDS};equal(subset(raw,t['rows']),old)
   save(dest/'raw.npz',**raw)
   representative=step in [20,200]
   if representative:
    native.save(dest/'graph.hnsw');native.verify(dest/'graph.hnsw',np.arange(16,dtype=np.int32))
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    equal(parity,subset(raw,np.arange(16)));save(dest/'parity.npz',**parity)
   dump(dest/'identity.json',dict(dataset=ds,step=step,action=a,W_sha=digest(ww),topology_sha=top,raw_sha=sha(dest/'raw.npz'),
    old_128_bit_regression='PASS',serialized_parity='PASS' if representative else 'NOT_REQUESTED',
    graph_sha=sha(dest/'graph.hnsw') if representative else None))
  dump(O/'state.json',dict(status='QUERYING_LOCAL_SAMPLING_DIAGNOSIS',dataset=ds,step=step,native=native.stats(),pid=os.getpid()))
  print('CONTEXT_COMPLETE',ds,step,native.stats(),flush=True)
 stats=native.stats();assert stats['NSG_calls']==369504 and stats['HNSW_calls']==369216 and stats['builds']==90 and stats['actual_threads']==1
 out=dict(status='PASS',dataset=ds,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**stats)
 dump(O/'results'/ds/'query_complete.json',out)
 job.update(status='COMPLETE',completed_at=time.time(),actual=stats['NSG_calls'],native=stats);dump(ledger,jobs)
 print('DATASET_COMPLETE',json.dumps(out),flush=True)
finally:native.close()
