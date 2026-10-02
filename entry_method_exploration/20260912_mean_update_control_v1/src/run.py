from shared import *
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json')
assert time.time()<QUERY_STOP-600;resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else []
assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs),'no retry/concurrent query'
assert sum(x['reserved'] for x in jobs)+83520<=CAP
job=dict(dataset=ds,status='RUNNING',reserved=83520,reserved_builds=30,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(ledger,jobs)
sys.path.insert(0,str(E37/'src'));from native import Native
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c)
try:
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  resources();assert time.time()<QUERY_STOP and time.monotonic()-started<600
  step=rec['step'];slot=rec['slot'];w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim']);u=dict(np.load(O/'inputs'/ds/f'{step:04}_updates.npz'))
  for tag in ['C','batch','full']:
   dest=O/'results'/ds/f'{step:04}'/tag;dest.mkdir(parents=True);ww=w.copy()
   if tag!='C':ww[slot]=u[tag+'_row']
   expected_W=rec['current_W_sha'] if tag=='C' else rec['updated_W_sha'][tag];assert digest(ww)==expected_W
   top=native.build(ww)
   if tag=='C':assert top==rec['current_topology_sha']
   native.save(dest/'graph.hnsw');save(dest/'topology.npz',topology=native.data(5,np.int32))
   raw=native.run(np.arange(16 if tag=='C' else 4096,dtype=np.int32));save(dest/'raw.npz',**raw)
   if tag=='C':equal(raw,{k:v[:16] for k,v in dict(np.load(rec['current_raw'])).items()})
   native.verify(dest/'graph.hnsw',np.arange(16,dtype=np.int32))
   parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
   equal(parity,subset(raw,np.arange(16)));save(dest/'parity.npz',**parity)
   dump(dest/'identity.json',dict(dataset=ds,step=step,tag=tag,W_sha=digest(ww),topology_sha=top,graph_sha=sha(dest/'graph.hnsw'),raw_sha=sha(dest/'raw.npz'),parity='PASS'))
  print('CONTEXT_COMPLETE',ds,step,native.stats(),flush=True)
  dump(O/'state.json',dict(status='QUERYING_MEAN_UPDATE_CONTROL',dataset=ds,step=step,native=native.stats(),pid=os.getpid()))
 stats=native.stats();assert stats['NSG_calls']==83520 and stats['HNSW_calls']==83040 and stats['builds']==30 and stats['actual_threads']==1
 out=dict(status='PASS',dataset=ds,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**stats)
 dump(O/'results'/ds/'query_complete.json',out);job.update(status='COMPLETE',actual=stats['NSG_calls'],native=stats,completed_at=time.time());dump(ledger,jobs)
 print('DATASET_COMPLETE',json.dumps(out),flush=True)
finally:native.close()
