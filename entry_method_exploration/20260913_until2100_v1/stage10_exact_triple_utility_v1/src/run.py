from native import *
import resource
threads();resources();ds=sys.argv[1];assert ds in DS
cfg=read(O/'inputs'/ds/'native.json');limit=read(O/'config.locked.json');assert time.time()<limit['latest_launch'];check(O/'reviews/prequery_freeze.json')
jobs=read(O/'logs/jobs.json');assert not any(j['dataset']==ds for j in jobs);assert all(j['status']=='COMPLETE' for j in jobs)
job=dict(dataset=ds,status='RUNNING',pid=os.getpid(),started_epoch=time.time(),reserved_NSG=cfg['native_call_cap']);jobs.append(job);dump(O/'logs/jobs.json',jobs)
raw=old_raw(ds,'baseline');routes=dict(np.load(O/'inputs'/ds/'routes.npz'));out=O/'results'/ds;out.mkdir()
env=None;start=time.monotonic();op=[]
try:
 env=Native(cfg);loadsec=time.monotonic()-start;assert env.stats()==dict(NSG=0,HNSW=0,builds=0,actual_threads=1)
 # Check empty batches and full-batch rejection; these execute zero NSG calls.
 good=raw['entries'][:2].copy();invalid=[]
 for mode in ['count','plain','reference']:
  z=env.search(np.empty(0,np.int32),np.empty((0,3),np.int32),mode);assert z['ids'].shape==(0,10)
  cases=[(np.array([0,7952],np.int32),good),(np.array([0,-1],np.int32),good)]
  for kind in ['duplicate','unsorted','negative','outside','nonhub']:
   bad=good.copy()
   if kind=='duplicate':bad[1,1]=bad[1,0]
   elif kind=='unsorted':bad[1]=bad[1,::-1]
   elif kind=='negative':bad[1,0]=-1
   elif kind=='outside':bad[1,2]=2147483647
   else:
    hubs=set(np.fromfile(cfg['hub_ids'],np.int32));v=next(x for x in range(1000) if x not in hubs);bad[1]=sorted([v,*good[1,1:]])
   cases.append((np.array([0,1],np.int32),bad))
  for rows,entries in cases:
   try:env.search(rows,entries,mode)
   except RuntimeError as ex:invalid.append(str(ex))
   else:raise AssertionError('invalid batch accepted')
  assert env.stats()['NSG']==0
 for label,rows,entries in [('baseline_replay',np.arange(7952,dtype=np.int32),raw['entries']),('missing',routes['missing_rows'],routes['missing_entries'])]:
  chunks=[]
  # First 128 baseline rows are a precheck within the planned all-row replay.
  for begin,end in ([(0,128),(128,len(rows))] if label=='baseline_replay' else [(0,len(rows))]):
   rr=rows[begin:end];ee=entries[begin:end];tick=time.monotonic();a=env.search(rr,ee,'count');b=env.search(rr,ee,'plain');same(a,b,('ids','distances'))
   if label=='baseline_replay':same(a,{k:raw[k][begin:end] for k in a})
   chunks.append(a);op.append(dict(stage=label,begin=begin,end=end,seconds=time.monotonic()-tick,normal_NSG=2*len(rr)))
  a={k:np.concatenate([z[k] for z in chunks]) for k in chunks[0]}
  ref=env.search(rows[:16],entries[:16],'reference');same(ref,{k:a[k][:16] for k in a})
  save(out/(label+'.npz'),rows=rows,entries=entries,**a);save(out/(label+'_reference.npz'),rows=rows[:16],entries=entries[:16],**ref)
  print(ds,label,env.stats(),flush=True);assert time.time()<limit['query_hard_stop'];resources()
 stats=env.stats();assert stats['NSG']==cfg['native_call_cap'] and stats['HNSW']==stats['builds']==0 and stats['actual_threads']==1
 job.update(status='COMPLETE',native=stats,load_seconds=loadsec,operation_seconds=op,invalid_batches_rejected=len(invalid),elapsed_seconds=time.monotonic()-start,max_RSS_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/(1<<20),completed_epoch=time.time())
 dump(out/'cost.json',job)
except BaseException as ex:
 job.update(status='FAILED',error=repr(ex),native=env.stats() if env else None);raise
finally:
 if env:env.close()
 dump(O/'logs/jobs.json',jobs)
print('TERMINATING_NORMAL',ds,flush=True)
