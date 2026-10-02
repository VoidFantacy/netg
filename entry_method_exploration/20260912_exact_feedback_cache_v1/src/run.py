from shared import *
from native_cached import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json')
assert time.time()<QUERY_STOP-600;resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else [];assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved'] for x in jobs)+4000<=CAP
job=dict(dataset=ds,status='RUNNING',reserved=4000,reserved_builds=90,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(ledger,jobs)
c=read(O/'inputs'/ds/'config.json');started=time.monotonic();native=Native(c);loaded=time.monotonic();contexts=[];normal_new=0
try:
 # All invalid batches must fail before modifying NSG counters.
 before=native.stats()['NSG_calls'];hubs=np.fromfile(c['hub_ids'],np.int32);valid=np.sort(hubs[:3]);rejections=0
 for rows,ent in [(np.array([-1]),valid[None]),(np.array([0]),np.array([[-1,int(valid[1]),int(valid[2])]])),(np.array([0]),valid[::-1][None]),(np.array([0]),np.array([[int(valid[0])]*3]))]:
  try:native.search_entries(rows,ent)
  except RuntimeError:rejections+=1
 assert rejections==4 and native.stats()['NSG_calls']==before
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  resources();assert time.time()<QUERY_STOP and time.monotonic()-started<600;ct=time.monotonic()
  step=rec['step'];w=np.fromfile(rec['current_W'],np.float32).reshape(c['hub_count'],c['dim']);t=dict(np.load(rec['trajectory']))
  base=dict(np.load(E44/'results'/ds/f'{step:04}'/'C/raw.npz'));points=[]
  for a in range(-1,8):
   dest=O/'results'/ds/f'{step:04}'/('C' if a<0 else f'A{a}');dest.mkdir(parents=True);point_start=time.monotonic();ww=w.copy()
   if a>=0:ww[rec['slot']]=t['candidate_rows'][a]
   bt=time.monotonic();top=native.build(ww);build_s=time.monotonic()-bt
   expected=rec['current_topology_sha'] if a<0 else rec['candidate_topology_sha'][a];assert top==expected
   save(dest/'topology.npz',topology=native.data(5,np.int32));rt=time.monotonic();route=native.route(np.arange(4096,dtype=np.int32));route_s=time.monotonic()-rt
   mt=time.monotonic();changed=np.flatnonzero((route['entries']!=base['entries']).any(1)).astype(np.int32)
   if a<0:assert len(changed)==0
   mask_s=time.monotonic()-mt;nt=time.monotonic();patch=native.search_entries(changed,route['entries'][changed]);new_s=time.monotonic()-nt;normal_new+=len(changed)
   at=time.monotonic();out={k:base[k].copy() for k in ['ids','distances','graph_ndc']};out.update(route)
   for k in patch:out[k][changed]=patch[k]
   assemble_s=time.monotonic()-at
   # The old candidate output is first opened after reconstruction is complete.
   expected_raw=dict(np.load(E44/'results'/ds/f'{step:04}'/('C' if a<0 else f'A{a}')/'raw.npz'));equal(out,expected_raw)
   save(dest/'raw.npz',**out);save(dest/'patch.npz',changed_rows=changed,entries=route['entries'][changed],**patch)
   representative=step in [20,200]
   if representative:
    native.save(dest/'graph.hnsw');native.verify(dest/'graph.hnsw',np.arange(16,dtype=np.int32))
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    equal(parity,subset(out,np.arange(16)));save(dest/'parity.npz',**parity)
   point=dict(dataset=ds,step=step,action=a,new_NSG=len(changed),reused_NSG_rows=4096-len(changed),route_calls=4096,
    build_seconds=build_s,route_seconds=route_s,change_mask_seconds=mask_s,new_NSG_seconds=new_s,assemble_seconds=assemble_s,seconds=time.monotonic()-point_start,
    W_sha=digest(ww),topology_sha=top,raw_sha=sha(dest/'raw.npz'),graph_sha=sha(dest/'graph.hnsw') if representative else None,bit_recovery='PASS')
   dump(dest/'identity.json',point);points.append(point)
  contexts.append(dict(dataset=ds,step=step,seconds=time.monotonic()-ct,new_NSG=sum(x['new_NSG'] for x in points),points=points))
  print('CONTEXT_COMPLETE',ds,step,native.stats(),flush=True)
 stats=native.stats();expected_normal=971 if ds==DS[0] else 362
 assert normal_new==expected_normal and stats['NSG_calls']==normal_new+864 and stats['HNSW_calls']==369216 and stats['builds']==90 and stats['actual_threads']==1
 out=dict(status='PASS',dataset=ds,seconds=time.monotonic()-started,load_seconds=loaded-started,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  invalid_batches_rejected=rejections,normal_new_NSG=normal_new,contexts=contexts,**stats)
 dump(O/'results'/ds/'query_complete.json',out);job.update(status='COMPLETE',actual=stats['NSG_calls'],native=stats,completed_at=time.time());dump(ledger,jobs)
 print('DATASET_COMPLETE',ds,'seconds',out['seconds'],'normal_new_NSG',normal_new,flush=True)
finally:native.close()
