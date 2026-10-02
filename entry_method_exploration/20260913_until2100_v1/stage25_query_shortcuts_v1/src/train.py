from common import *
from graph_reader import inspect_serialized
import subprocess,struct,resource
threads();resources();check(O/'reviews/pretraining_freeze.json');assert not (O/'reviews/prequery_freeze.json').exists();E73=C/'stage14_compact_modes_v1';jobs=[];records=[];models={};paths=[Path(x['path']) for x in read(O/'reviews/pretraining_freeze.json')['files']];allstart=time.monotonic()
for ds in DS:
 tick=time.monotonic();out=O/'results'/ds;out.mkdir()
 for role in ['fit','route_regression']:
  cp=O/'inputs'/ds/(role+'.json');cfg=read(cp);dest=out/('routes_'+role);job=dict(dataset=ds,role=role,status='RUNNING',reserved_HNSW=2*cfg['num_queries'],started_at=time.time());jobs.append(job);dump(O/'logs/route_jobs.json',jobs)
  with (O/'logs'/(ds+'_'+role+'.log')).open('x') as log:
   proc=subprocess.Popen([str(O/'bin/route_only'),str(cp),str(dest)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),preexec_fn=lambda:os.sched_setaffinity(0,{15}));job['pid']=proc.pid;peak=0
   try:
    while proc.poll() is None:
     try:
      ss=dict(line.split(':',1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line);assert int(ss['Threads'])==1 and os.sched_getaffinity(proc.pid)=={15};peak=max(peak,int(ss.get('VmRSS','0 kB').split()[0]));assert peak<4*2**20
     except FileNotFoundError:pass
     assert time.time()-job['started_at']<300;resources()
     try:proc.wait(timeout=.5)
     except subprocess.TimeoutExpired:pass
    assert proc.returncode==0
   except BaseException:
    if proc.poll() is None:proc.kill();proc.wait()
    job.update(status='FAILED_RESERVED_RETAINED',returncode=proc.returncode);dump(O/'logs/route_jobs.json',jobs);raise
  meta=read(dest/'cost.json');assert meta['HNSW']==job['reserved_HNSW'] and meta['NSG']==meta['builds']==0 and meta['actual_threads']==1;job.update(status='COMPLETE',seconds=time.time()-job['started_at'],actual_HNSW=meta['HNSW'],peak_RSS_KiB=peak,returncode=0);dump(O/'logs/route_jobs.json',jobs)
 # Already exposed aux routing prefix is only an implementation regression, never in votes.
 reg=out/'routes_route_regression';old=E73/'results'/ds/'aux/compact10_L128'
 for newfn,oldfn,dt,w in [('entries.i32','entry_ids.i32',np.int32,3),('slots.i32','candidate_slots.i32',np.int32,7),('distances.f32','candidate_distances.f32',np.float32,7),('route_ndc.u32','route_ndc.u32',np.uint32,1)]:assert (reg/newfn).read_bytes()==np.fromfile(old/oldfn,dt,count=128*w).tobytes()
 cfg=read(O/'inputs'/ds/'fit.json');d=cfg['dim'];n=cfg['num_queries'];mc=cfg['method'];q=np.fromfile(cfg['queries_file'],np.float32,count=n*d).reshape(n,d);rows=np.fromfile(cfg['row_ids'],np.int64,count=n);assert np.array_equal(rows,np.arange(10000,30000));W=np.fromfile(mc['W'],np.float32).reshape(-1,d);wf=W.astype(float);mapping=np.fromfile(mc['mapping'],np.int32);hubs,starts,counts=np.unique(mapping,return_index=True,return_counts=True);assert np.all(np.diff(mapping)>=0)
 data=Path(mc['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',data);nn,size=hd[2:4];adj=[list(struct.unpack_from('<'+'I'*struct.unpack_from('<H',data,96+i*size)[0],data,96+i*size+4)) for i in range(nn)]
 slots=np.fromfile(out/'routes_fit/slots.i32',np.int32).reshape(n,7);entries=np.fromfile(out/'routes_fit/entries.i32',np.int32).reshape(n,3);desired=np.empty((n,3),np.int32);near=np.zeros(n,bool);votes={};miss=0
 for start in range(0,n,512):
  end=min(n,start+512);qq=q[start:end].astype(float);s=qq@wf.T;sm=np.maximum.reduceat(s,starts,axis=1);order=np.argsort(-sm,axis=1,kind='stable')[:,:4];ii=np.arange(end-start);near[start:end]=sm[ii,order[:,2]]-sm[ii,order[:,3]]<=1e-5*np.maximum(1,np.linalg.norm(qq,axis=1))
  for j in range(end-start):
   source=int(slots[start+j,0])
   for rank,h in enumerate(order[j,:3]):
    lo=int(starts[h]);target=lo+int(np.argmax(s[j,lo:lo+counts[h]]));desired[start+j,rank]=target
    if int(hubs[h]) not in entries[start+j]:
     miss+=1
     if len(adj[source])<32 and target!=source and target not in adj[source]:votes[(source,target)]=votes.get((source,target),0)+1
 oldrank=np.load(C/'stage9_profile_ranking_diagnosis_v1/results'/ds/'fit.npz');assert np.array_equal(oldrank['source_rows'],rows);different=np.any(np.sort(mapping[desired],axis=1)!=np.sort(oldrank['exact_mode_hubs'],axis=1),axis=1);assert np.all(near[different])
 # Separate explicit-query recount verifies all vote events and excludes aux rows.
 recount={}
 for i in range(n):
  so=int(slots[i,0]);found=set(map(int,entries[i]))
  for ta in desired[i]:
   ta=int(ta)
   if int(mapping[ta]) not in found and len(adj[so])<32 and ta!=so and ta not in adj[so]:recount[so,ta]=recount.get((so,ta),0)+1
 assert votes==recount
 changes=[]
 for source in sorted(set(s for s,t in votes)):
  opts=[(v,t) for (s,t),v in votes.items() if s==source];v,target=min(opts,key=lambda x:(-x[0],x[1]))
  if v<2:continue
  score=wf@wf[source];eligible=[j for j in range(nn) if mapping[j]!=mapping[source] and j not in adj[source]];other=min(eligible,key=lambda j:(-score[j],j));assert mapping[target]!=mapping[source]
  changes.append(dict(slot=int(source),real_hub=int(mapping[source]),old_degree=len(adj[source]),shortcut_added=[int(target)],neighbor_added=[int(other)],votes=int(v),target_real_hub=int(mapping[target]),shortcut_cosine=float(score[target]),neighbor_cosine=float(score[other])))
 assert changes,'no shortcut candidates';dest=O/'models'/ds;dest.mkdir();dump(dest/'additions.json',changes);vv=np.array([(s,t,v) for (s,t),v in sorted(votes.items())],np.int32);save(dest/'training.npz',source_rows=rows,source_slot=slots[:,0],actual_entries=entries,desired_slots=desired,near_tie=near,votes=vv);models[ds]=[]
 for name in ['shortcut10','neighbor10']:
  folder=dest/name;folder.mkdir();m=dict(mc,model_name=name,name=name+'_L128',graph_file=str(folder/'graph.hnsw'));dump(folder/'model.json',m);models[ds].append(m)
 rec=dict(dataset=ds,fit_queries=n,HNSW=40256,missing_ranked_hub_events=miss,eligible_vote_events=int(vv[:,2].sum()),distinct_vote_pairs=len(vv),source_nodes_with_votes=len(set(vv[:,0].tolist())),added_edges_per_arm=len(changes),support_min=min(x['votes'] for x in changes),support_max=max(x['votes'] for x in changes),physical=nn,near_ties=int(near.sum()),old_exact_mode_near_precision_differences=int(different.sum()),offline_training_seconds=time.monotonic()-tick,new_NSGlabeled_training=0);records.append(rec);print('TRAINED',json.dumps(rec),flush=True)
 paths += list(dest.rglob('*.json'))+list(dest.rglob('*.npz'))+list(out.rglob('*'))
assert sum(j['actual_HNSW'] for j in jobs)==80512
dump(O/'reviews/training_verification.json',dict(status='PASS',records=records,all_votes_recounted=True,aux128_regression_rows=256,fit_plain_count_rows=40000,HNSW=80512,NSG=0,profile_training=0,graph_supervised_fits=2,total_seconds=time.monotonic()-allstart));paths += [O/'reviews/training_verification.json'];freeze(O/'reviews/preinstall_freeze.json',[p for p in paths if p.is_file()]);installs=[]
for ds in DS:
 mc=read(O/'inputs'/ds/'fit.json')['method'];before=Path(mc['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',before);n,size=hd[2:4];W=np.fromfile(mc['W'],np.float32).reshape(n,mc['dim']);changes=read(O/'models'/ds/'additions.json');degrees=[]
 for m,field in zip(models[ds],['shortcut_added','neighbor_added']):
  t=time.monotonic();data=bytearray(before)
  for x in changes:
   at=96+x['slot']*size;struct.pack_into('<H',data,at,x['old_degree']+1);struct.pack_into('<I',data,at+4+4*x['old_degree'],x[field][0])
  Path(m['graph_file']).write_bytes(data);inspect_serialized(m['graph_file'],W,np.arange(n));restored=bytearray(data)
  for x in changes:
   at=96+x['slot']*size;restored[at:at+2]=before[at:at+2];j=at+4+4*x['old_degree'];restored[j:j+4]=before[j:j+4]
  assert bytes(restored)==before;installs.append(dict(dataset=ds,model=m['model_name'],seconds=time.monotonic()-t,graph=identity(m['graph_file']),all_old_edges_and_nonadjacency_bytes_preserved=True))
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json')
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[dict(x) for x in old['methods'] if x['model_name'] in ['baseline10','compact10']]+models[ds];c=dict(old,methods=methods,split='E84_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=4*(2*n+16),timing_repeats=0);dump(O/'inputs'/ds/(split+'.json'),c)
dump(O/'results/construction.json',dict(status='PASS',datasets=records,installs=installs,builds=0,graph_supervised_fits=2,gradient_updates=0,new_GT=0,preparation_seconds=time.monotonic()-allstart));dump(O/'config.locked.json',dict(NSG_expected=129536,NSG_hard_cap=132000,HNSW_expected=209792,route_training_HNSW=80512,query_HNSW=129280,latest_launch=1789290000,query_hard_stop=1789290600,per_job_seconds=600,output_cap_MiB=64,threads=1,CPU=15,free_min_GiB=6.65))
paths += list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+[O/'results/construction.json',O/'config.locked.json'];freeze(O/'reviews/prequery_freeze.json',[p for p in paths if p.is_file()]);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='QUERY_SHORTCUTS_TRAINED_AND_INSTALLED',HNSW=80512,NSG=0,builds=0,edge_installs=4,day_goal_complete=False));resources();print('E84_READY_QUERY')
