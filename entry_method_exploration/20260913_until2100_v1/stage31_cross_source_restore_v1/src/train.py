from common import *
from routes import Routes
from native import Native
from installation import install,summary
import resource

def main(ds):
 threads();resources();check(O/'reviews/pretraining_freeze.json');limit=read(O/'config.locked.json');assert time.time()<limit['latest_training_launch']
 jobs=read(O/'logs/training_jobs.json');assert all(j['status']=='COMPLETE' for j in jobs) and not any(j['dataset']==ds for j in jobs)
 start=time.monotonic();job=dict(dataset=ds,status='RUNNING',pid=os.getpid(),reserved_NSG=32768,started_at=time.time(),actual_NSG=0,actual_HNSW=0,actual_threads=1,affinity=sorted(os.sched_getaffinity(0)));jobs.append(job);dump(O/'logs/training_jobs.json',jobs)
 models=O/'models'/ds;models.mkdir();router=env=None;accepted=[];random_actions=[];union_records=[];installs=[]
 try:
  for role,n,reg in [('support',3976,16),('fit',20000,32)]:
   cfg=read(O/'inputs'/ds/('routes_'+role+'.json'));nc=read(O/'inputs'/ds/('native_'+role+'.json'));out=O/'results'/ds/role;out.mkdir(parents=True)
   gt=np.fromfile(nc['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(nc['row_ids'],np.int64)
   if role=='support':old=[raw(E89/'results'/ds/'aux'/(m+'_L128'),n) for m in ['baseline10','compact10','restore10']]
   else:old=[raw(E66/'results'/ds/'fit/baseline_L128')]+[dict(np.load(E89/'results'/ds/'fit'/(m+'.npz'))) for m in ['compact_baseline','restore10']]
   cache={};new=[];new_count=0;resolution=[]
   for code,a in enumerate(old):
    h,mask=score(a['ids'],gt);assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask'])
    for i,ee in enumerate(a['entries']):
     key=(i,*map(int,ee))
     if key in cache:
      k,j=cache[key];same({f:a[f][i:i+1] for f in ['ids','distances','graph_ndc']},{f:old[k][f][j:j+1] for f in ['ids','distances','graph_ndc']})
     else:cache[key]=(code,i)
   router=Routes(cfg);env=Native(nc);br=router.run();same(br,old[1],('entries','route_ndc'))
   if role=='support':
    oldpath=E89/'results'/ds/'aux/compact10_L128'
    for k,fn in [('slots','candidate_slots.i32'),('slot_distances','candidate_distances.f32')]:assert br[k].tobytes()==np.fromfile(oldpath/fn,br[k].dtype,count=n*7).tobytes()
   else:same(br,old[1],tuple(br))
   def resolve(rr,name):
    nonlocal new_count
    assert time.monotonic()-start<1200 and time.time()<limit['query_hard_stop'];resources()
    ee=rr['entries'];idx=np.array([i for i,e in enumerate(ee) if (i,*map(int,e)) not in cache],np.int32)
    # Preserve total budget over both source roles, including all future 3-way baseline checks.
    assert job['actual_NSG']+env.stats()['NSG']+2*len(idx)+144<=32768
    if len(idx):
     a=env.search(idx,ee[idx],'count');p=env.search(idx,ee[idx],'plain');same(a,p,('ids','distances'));save(out/(name+'_new.npz'),rows=idx,entries=ee[idx],global_begin=np.array(new_count),**a)
     for j,i in enumerate(idx):cache[(int(i),*map(int,ee[i]))]=(3,new_count+j)
     new_count+=len(idx);new.append(a)
    big={f:np.concatenate([a[f] for a in new]) if new else old[0][f][:0].copy() for f in ['ids','distances','graph_ndc']};source=np.array([cache[(i,*map(int,e))] for i,e in enumerate(ee)],np.int32);a={f:np.empty_like(old[0][f]) for f in ['ids','distances','graph_ndc']}
    for code,s in enumerate(old+[big]):
     ix=source[:,0]==code
     for f in a:a[f][ix]=s[f][source[ix,1]]
    a.update(rr);a['hits'],a['mask']=score(a['ids'],gt);a['source_code']=source[:,0];a['source_index']=source[:,1];resolution.append(dict(name=name,new_keys=len(idx)));return a
   base=resolve(br,'compact_baseline');save(out/'compact_baseline.npz',source_rows=rows,**base)
   for mode in ['count','plain','reference']:
    a=env.search(np.arange(reg,dtype=np.int32),base['entries'][:reg],mode);same(a,{k:base[k][:reg] for k in a},('ids','distances') if mode=='plain' else ('ids','distances','graph_ndc'));save(out/('baseline_'+mode+'_regression.npz'),rows=np.arange(reg,dtype=np.int32),**a)
   if role=='support':
    choices=read(O/'inputs'/ds/'candidates.json');records=[]
    for j,e in enumerate(choices):
     r=router.run(e['hub']);a=resolve(r,f'action_{j:03}');ix=np.flatnonzero(np.any(a['entries']!=base['entries'],axis=1)).astype(np.int32);rch=np.flatnonzero(np.any(a['slots']!=base['slots'],axis=1)|np.any(a['slot_distances'].view(np.uint32)!=base['slot_distances'].view(np.uint32),axis=1)).astype(np.int32)
     save(out/f'action_{j:03}.npz',rows=ix,route_changed_rows=rch,slots=a['slots'][rch],slot_distances=a['slot_distances'][rch],route_ndc=a['route_ndc'],**{f:a[f][ix] for f in ['ids','distances','entries','hits','mask','graph_ndc','source_code','source_index']})
     rec=dict(candidate=j,hub=e['hub'],**summary(a,base),route_hashes={k:hashlib.sha256(r[k].tobytes()).hexdigest() for k in r});records.append(rec)
     if rec['accepted']:accepted.append(e)
     print('E90_SUPPORT_ACTION',ds,j+1,len(choices),len(accepted),rec['net_hits'],flush=True)
    dump(out/'action_statistics.json',records);dump(models/'selected_actions.json',accepted)
    permutation=np.random.Generator(np.random.PCG64(20260913)).permutation(len(choices));random_actions=[choices[int(i)] for i in permutation[:len(accepted)]];dump(models/'random_actions.json',random_actions);save(models/'random_permutation.npz',permutation=permutation)
    freeze(models/'before_union.json',[O/'protocol.md',O/'inputs'/ds/'candidates.json',models/'selected_actions.json',models/'random_actions.json',models/'random_permutation.npz',out/'action_statistics.json'])
    for name,groups in [('supported10',accepted),('random10',random_actions)]:
     tick=time.monotonic();m=install(cfg['method'],groups,models/name);m.update(model_name=name,name=name+'_L128');dump(models/name/'model.json',m);installs.append(dict(model=name,groups=len(groups),seconds=time.monotonic()-tick,W=identity(m['W']),graph=identity(m['graph_file'])))
   for name in ['supported10','random10']:
    m=read(models/name/'model.json');r=Routes(dict(cfg,method=m));routed=r.run();job['actual_HNSW']+=r.calls();r.close();a=resolve(routed,name);save(out/(name+'.npz'),source_rows=rows,**a);union_records.append(dict(role=role,model=name,groups=len(accepted),**summary(a,base)))
   dump(out/'cache_accounting.json',dict(records=resolution,new_unique_keys=new_count))
   stats=env.stats();assert stats['NSG']==2*new_count+reg*3 and stats['HNSW']==stats['builds']==0 and stats['actual_threads']==1;job['actual_NSG']+=stats['NSG'];job['actual_HNSW']+=router.calls();env.close();env=None;router.close();router=None
   dump(O/'logs/training_jobs.json',jobs)
  dump(O/'results'/ds/'union_statistics.json',union_records);job.update(status='COMPLETE',returncode=0,accepted_actions=len(accepted),vector_exports=4//2,installs=installs,union=union_records,seconds=time.monotonic()-start,completed_at=time.time(),max_RSS_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
  assert job['actual_NSG']<=32768 and job['max_RSS_GiB']<32;dump(O/'results'/ds/'cost.json',job)
 except BaseException as ex:
  job.update(status='FAILED_RESERVED_RETAINED',error=repr(ex),seconds=time.monotonic()-start,partial_native_NSG=env.stats()['NSG'] if env else 0,partial_route_HNSW=router.calls() if router else 0);raise
 finally:
  if router:router.close()
  if env:env.close()
  dump(O/'logs/training_jobs.json',jobs)
 print('E90_TRAIN_COMPLETE',ds,json.dumps(job),flush=True)
if __name__=='__main__':main(sys.argv[1])
