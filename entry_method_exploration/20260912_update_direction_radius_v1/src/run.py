from shared import *
from native_cached import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json');assert time.time()<LATEST_LAUNCH
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else [];assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs);assert sum(x['reserved'] for x in jobs)+20000<=CAP
job=dict(dataset=ds,status='RUNNING',reserved=20000,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(ledger,jobs)
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c);normal=0;states=0;points=[]
try:
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  resources();st=rec['step'];seed=rec['seed'];slot=rec['slot'];w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim']);context=dict(np.load(rec['context']));t=dict(np.load(rec['trajectory']));base={k:context['current_'+k] for k in FIELDS}
  for tag in ['C','M']+rec['tags']:
   assert time.time()<QUERY_STOP and time.monotonic()-started<600
   ww=w.copy()
   if tag=='M':ww[slot]=t['next_row']
   elif tag!='C':ww[slot]=context['proposed_rows'][rec['tags'].index(tag)]
   top=native.build(ww);route=native.route(np.arange(4096,dtype=np.int32));changed=np.flatnonzero((route['entries']!=base['entries']).any(1)).astype(np.int32)
   patch=native.search_entries(changed,route['entries'][changed]);normal+=len(changed);out={k:base[k].copy() for k in ['ids','distances','graph_ndc']};out.update(route)
   for k in patch:out[k][changed]=patch[k]
   if tag in ['C','M']:
    prefix='current_' if tag=='C' else 'mean_';equal(out,{k:context[prefix+k] for k in FIELDS});assert top==rec['current_topology_sha' if tag=='C' else 'mean_topology_sha']
   dest=O/'results'/ds/str(seed)/f'{st:04}'/tag;dest.mkdir(parents=True);save(dest/'raw.npz',**out);save(dest/'topology.npz',topology=native.data(5,np.int32));save(dest/'patch.npz',changed_rows=changed,entries=route['entries'][changed],**patch)
   representative=st in [20,200]
   if representative:
    native.save(dest/'graph.hnsw');native.verify(dest/'graph.hnsw',np.arange(16,dtype=np.int32))
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    equal(parity,subset(out,np.arange(16)));save(dest/'parity.npz',**parity)
   iden=dict(dataset=ds,seed=seed,step=st,tag=tag,W_sha=digest(ww),topology_sha=top,new_NSG=len(changed),raw_sha=sha(dest/'raw.npz'),graph_sha=sha(dest/'graph.hnsw') if representative else None,
    endpoint_recovery='PASS' if tag in ['C','M'] else 'NEW_COUNTERFACTUAL',parity='PASS' if representative else 'NOT_REQUESTED')
   dump(dest/'identity.json',iden);points.append(iden);states+=1
  dump(O/'state.json',dict(status='QUERYING_UPDATE_DIRECTION_RADIUS',dataset=ds,seed=seed,step=st,native=native.stats(),pid=os.getpid()));print('CONTEXT_COMPLETE',ds,seed,st,native.stats(),flush=True)
 stats=native.stats();assert states==140 and stats['builds']==140 and stats['HNSW_calls']==574336 and stats['NSG_calls']==normal+1344 and stats['actual_threads']==1
 result=dict(status='PASS',dataset=ds,states=states,normal_new_NSG=normal,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,**stats)
 dump(O/'results'/ds/'query_complete.json',result);dump(O/'results'/ds/'points.json',points);job.update(status='COMPLETE',actual=stats['NSG_calls'],native=stats,completed_at=time.time());dump(ledger,jobs);print('DATASET_COMPLETE',json.dumps(result),flush=True)
finally:native.close()
