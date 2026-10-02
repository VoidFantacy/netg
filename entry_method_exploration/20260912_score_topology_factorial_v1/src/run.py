from shared import *
from native_factorial import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json');assert time.time()<QUERY_STOP-600
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else [];assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved'] for x in jobs)+30000<=CAP
job=dict(dataset=ds,status='RUNNING',reserved=30000,reserved_builds=170,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(ledger,jobs)
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c);normal=0;endpoint_normal=0;states=0;rejections=0;records=[]
def evaluate(tag,w,expected_top,parent,step,action,oldtag=None):
 global normal,endpoint_normal,states
 assert time.time()<QUERY_STOP and time.monotonic()-started<600
 dest=O/'results'/ds/f'{step:04}'/tag;dest.mkdir(parents=True);native.verify_vectors(w);top=native.data(5,np.int32);assert digest(top)==expected_top
 route=native.route(np.arange(4096,dtype=np.int32));changed=np.flatnonzero((route['entries']!=parent['entries']).any(1)).astype(np.int32)
 patch=native.search_entries(changed,route['entries'][changed]);normal+=len(changed)
 out={k:parent[k].copy() for k in ['ids','distances','graph_ndc']};out.update(route)
 for k in patch:out[k][changed]=patch[k]
 if oldtag is not None:
  equal(out,dict(np.load(E44/'results'/ds/f'{step:04}'/oldtag/'raw.npz')));endpoint_normal+=len(changed)
 save(dest/'raw.npz',**out);save(dest/'topology.npz',topology=top);save(dest/'patch.npz',changed_rows=changed,entries=route['entries'][changed],**patch)
 representative=step in [20,200]
 if representative:
  native.save(dest/'graph.hnsw');native.verify(dest/'graph.hnsw',np.arange(16,dtype=np.int32))
  parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
  equal(parity,subset(out,np.arange(16)));save(dest/'parity.npz',**parity)
 iden=dict(dataset=ds,step=step,action=action,tag=tag,W_sha=digest(w),topology_sha=expected_top,new_NSG=len(changed),reused_NSG=4096-len(changed),
  raw_sha=sha(dest/'raw.npz'),graph_sha=sha(dest/'graph.hnsw') if representative else None,vector_bytes_match=True,parity='PASS' if representative else 'NOT_REQUESTED',endpoint_recovery='PASS' if oldtag is not None else 'NEW_COUNTERFACTUAL')
 dump(dest/'identity.json',iden);records.append(iden);states+=1
try:
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  resources();step=rec['step'];slot=rec['slot'];w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim']);t=dict(np.load(rec['trajectory']))
  parent=E44/'results'/ds/f'{step:04}';base=dict(np.load(parent/'C/raw.npz'));gc=np.load(parent/'C/topology.npz')['topology'];assert native.build(w)==rec['current_topology_sha']
  if step==20:
   # Truncation, header shape, external ID, and late trailing data all reject before mutation.
   badshape=gc.copy();badshape[0]+=1;badid=gc.copy();badid[4]=-1
   for invalid in [gc[:-1],badshape,badid,np.r_[gc,np.array([0],np.int32)]]:
    before=native.installation_count()
    try:native.install_topology(invalid)
    except RuntimeError:rejections+=1
    assert native.installation_count()==before and digest(native.data(5,np.int32))==rec['current_topology_sha']
    native.verify_vectors(w)
  assert native.install_topology(gc)==rec['current_topology_sha'];evaluate('C',w,rec['current_topology_sha'],base,step,-1,'C')
  for a in range(8):
   wa=w.copy();wa[slot]=t['candidate_rows'][a];ga=np.load(parent/f'A{a}/topology.npz')['topology'];assert native.build(wa)==rec['candidate_topology_sha'][a]
   evaluate(f'A{a}',wa,rec['candidate_topology_sha'][a],base,step,a,f'A{a}')
   assert native.install_topology(gc)==rec['current_topology_sha'];evaluate(f'S{a}',wa,rec['current_topology_sha'],base,step,a)
   assert native.build(w)==rec['current_topology_sha'];assert native.install_topology(ga)==rec['candidate_topology_sha'][a];evaluate(f'T{a}',w,rec['candidate_topology_sha'][a],base,step,a)
  print('CONTEXT_COMPLETE',ds,step,native.stats(),'installations',native.installation_count(),flush=True)
  dump(O/'state.json',dict(status='QUERYING_SCORE_TOPOLOGY_FACTORIAL',dataset=ds,step=step,native=native.stats(),pid=os.getpid()))
 stats=native.stats();assert states==250 and stats['builds']==170 and native.installation_count()==170 and rejections==4
 assert endpoint_normal==(971 if ds==DS[0] else 362);assert stats['NSG_calls']==normal+2400 and stats['HNSW_calls']==1025600 and stats['actual_threads']==1
 out=dict(status='PASS',dataset=ds,seconds=time.monotonic()-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,normal_new_NSG=normal,endpoint_normal_NSG=endpoint_normal,
  states=states,topology_installations=native.installation_count(),invalid_topologies_rejected=rejections,**stats)
 dump(O/'results'/ds/'query_complete.json',out);dump(O/'results'/ds/'points.json',records);job.update(status='COMPLETE',actual=stats['NSG_calls'],native=stats,completed_at=time.time());dump(ledger,jobs)
 print('DATASET_COMPLETE',json.dumps(out),flush=True)
finally:native.close()
