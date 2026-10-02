from common import *
from routes import Routes
from native import Native
import resource,struct,csv

def install(mc,groups,path):
 before=Path(mc['graph_file']).read_bytes();data=bytearray(before);head=struct.unpack_from('<6QiI3QdQ',data);n,size,label,coord=head[2:6]
 W=np.fromfile(mc['W'],np.float32).reshape(n,mc['dim']).copy();original=W.copy();mapping=np.fromfile(mc['mapping'],np.int32);changed=[]
 for group in groups:
  h=group['hub'];slots=np.flatnonzero(mapping==h);assert len(slots)==3 and int(slots[0])==group['parent_slot'] and list(map(int,slots[1:]))==group['child_slots']
  for slot in slots[1:]:W[slot]=original[slots[0]];changed.append(int(slot))
 restored=bytearray(data)
 for slot in changed:
  at=96+slot*size+coord;data[at:at+mc['dim']*4]=W[slot].tobytes()
 path=Path(path);path.mkdir(parents=True);assert not (path/'graph.hnsw').exists()
 (path/'graph.hnsw').write_bytes(data);W.tofile(path/'W.f32')
 restored=bytearray(data)
 for slot in changed:
  at=96+slot*size+coord;restored[at:at+mc['dim']*4]=original[slot].tobytes()
 assert bytes(restored)==before
 unchanged=np.ones(n,bool);unchanged[changed]=False;assert W[unchanged].tobytes()==original[unchanged].tobytes()
 return dict(mc,graph_file=str(path/'graph.hnsw'),W=str(path/'W.f32'),reference_graph=True)

def summary(a,b):
 d=a['hits'].astype(int)-b['hits'].astype(int);half=[int(x.sum()) for x in np.split(d,2)];f=int((a['hits']==0).sum()-(b['hits']==0).sum());cost=float((a['route_ndc'].astype(float)+a['graph_ndc']).sum()/(b['route_ndc'].astype(float)+b['graph_ndc']).sum()-1)
 return dict(net_hits=int(d.sum()),half_net_hits=half,failure_delta=f,rescued=int(((b['hits']==0)&(a['hits']>0)).sum()),new_failed=int(((a['hits']==0)&(b['hits']>0)).sum()),gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),total_ndc_relative=cost,accepted=bool(d.sum()>0 and min(half)>=0 and f<=0 and cost<=.01))

def main(ds):
 threads();resources();assert ds in DS;check(O/'reviews/pretraining_freeze.json');limit=read(O/'config.locked.json');assert time.time()<limit['latest_training_launch']
 cfg=read(O/'inputs'/ds/'routes.json');ncfg=read(O/'inputs'/ds/'native_training.json');n=20000;d=cfg['dim'];out=O/'results'/ds/'fit';out.mkdir(parents=True);models=O/'models'/ds;models.mkdir()
 jobs=read(O/'logs/training_jobs.json');assert all(j['status']=='COMPLETE' for j in jobs) and not any(j['dataset']==ds for j in jobs)
 job=dict(dataset=ds,status='RUNNING',pid=os.getpid(),reserved_NSG=32768,started_at=time.time());jobs.append(job);dump(O/'logs/training_jobs.json',jobs);start=time.monotonic();router=None;env=None;routecalls=0;newcalls=0;installs=[]
 try:
  router=Routes(cfg);br=router.run();original=E84/'results'/ds/'routes_fit'
  for k,fn,dt in [('entries','entries.i32',np.int32),('slots','slots.i32',np.int32),('slot_distances','distances.f32',np.float32),('route_ndc','route_ndc.u32',np.uint32)]:assert br[k].tobytes()==np.fromfile(original/fn,dt).tobytes(),k
  gt=np.fromfile(ncfg['gt_file'],np.int64).reshape(n,100);old=[raw(E66/'results'/ds/'fit'/(m+'_L128')) for m in ['baseline','mode3P']]+[dict(np.load(E86/'results'/ds/'fit/compact_baseline.npz'))];cache={};collisions=0
  for code,b in enumerate(old):
   hits,mask=score(b['ids'],gt);assert np.array_equal(hits,b['hits']) and np.array_equal(mask,b['mask'])
   for i,e in enumerate(b['entries']):
    key=(i,*map(int,e))
    if key in cache:
     co,ix=cache[key];same({k:old[co][k][ix:ix+1] for k in ['ids','distances','graph_ndc']},{k:b[k][i:i+1] for k in ['ids','distances','graph_ndc']});collisions+=1
    else:cache[key]=(code,i)
  env=Native(ncfg);assert env.stats()==dict(NSG=0,HNSW=0,builds=0,actual_threads=1);new=[];new_count=0;resolve_records=[]
  def resolve(rr,name):
   nonlocal new_count
   ee=rr['entries'];missing=[i for i,e in enumerate(ee) if (i,*map(int,e)) not in cache];idx=np.asarray(missing,np.int32);reserved=2*len(idx);assert env.stats()['NSG']+reserved+96<=32768,'training NSG budget: preserve completed responses, stop before next call'
   if len(idx):
    a=env.search(idx,ee[idx],'count');p=env.search(idx,ee[idx],'plain');same(a,p,('ids','distances'));save(out/(name+'_new.npz'),rows=idx,entries=ee[idx],global_begin=np.array(new_count),**a)
    for j,i in enumerate(idx):cache[(int(i),*map(int,ee[i]))]=(3,new_count+j)
    new.append(a);new_count+=len(idx)
   big={k:np.concatenate([x[k] for x in new]) if new else np.empty((0,10) if k!='graph_ndc' else 0,np.float32 if k=='distances' else np.int32 if k=='ids' else np.uint32) for k in ['ids','distances','graph_ndc']}
   sources=np.array([cache[(i,*map(int,e))] for i,e in enumerate(ee)],np.int32);b={k:np.empty_like(old[0][k]) for k in ['ids','distances','graph_ndc']}
   for code,src in enumerate(old+[big]):
    mask=sources[:,0]==code
    for k in b:b[k][mask]=src[k][sources[mask,1]]
   b.update(rr);b['hits'],b['mask']=score(b['ids'],gt);b['source_code']=sources[:,0];b['source_index']=sources[:,1]
   resolve_records.append(dict(name=name,new_keys=len(idx),new_NSG=reserved,old_key_uses=int((sources[:,0]<3).sum()),new_cache_uses=int((sources[:,0]==3).sum())));return b
  base=resolve(br,'compact_baseline');save(out/'compact_baseline.npz',source_rows=np.arange(10000,30000,dtype=np.int64),**base)
  rr=np.arange(32,dtype=np.int32)
  for mode in ['count','plain','reference']:
   z=env.search(rr,base['entries'][:32],mode);same(z,{k:base[k][:32] for k in z},('ids','distances') if mode=='plain' else ('ids','distances','graph_ndc'));save(out/('baseline_'+mode+'_regression.npz'),rows=rr,entries=base['entries'][:32],**z)
  choices=read(O/'inputs'/ds/'candidates.json');records=[];accepted=[]
  for j,e in enumerate(choices):
   assert time.monotonic()-start<1200 and time.time()<limit['query_hard_stop'];resources();tick=time.monotonic();r=router.run(e['hub']);b=resolve(r,f'action_{j:03}')
   changed=np.flatnonzero(np.any(b['entries']!=base['entries'],axis=1)).astype(np.int32);rch=np.flatnonzero(np.any(b['slots']!=base['slots'],axis=1)|np.any(b['slot_distances'].view(np.uint32)!=base['slot_distances'].view(np.uint32),axis=1)).astype(np.int32)
   fields={k:b[k][changed] for k in ['entries','ids','distances','graph_ndc','hits','mask','source_code','source_index']}
   save(out/f'action_{j:03}.npz',rows=changed,route_changed_rows=rch,slots=b['slots'][rch],slot_distances=b['slot_distances'][rch],route_ndc=b['route_ndc'],**fields)
   rec=dict(candidate=j,hub=e['hub'],parent_slot=e['parent_slot'],child_slots=e['child_slots'],votes=e['votes'],support=e['support'],changed_triples=len(changed),changed_routes=len(rch),**summary(b,base),route_hashes={k:hashlib.sha256(r[k].tobytes()).hexdigest() for k in r},seconds=time.monotonic()-tick);records.append(rec)
   if rec['accepted']:accepted.append(e)
   if j==0:
    physical=install(cfg['method'],[e],models/'first_action_regression');installs.append(dict(kind='single_action_regression',graph=identity(physical['graph_file']),W=identity(physical['W'])));rp=Routes(dict(cfg,method=physical,num_queries=128));a=rp.run();same(a,{k:r[k][:128] for k in a},tuple(a));save(out/'first_action_physical_route.npz',**a);routecalls+=rp.calls();rp.close();restored=router.run(-1,128);same(restored,{k:br[k][:128] for k in restored},tuple(restored));save(out/'after_restore_route.npz',**restored)
   job.update(completed_actions=j+1,accepted_actions=len(accepted),actual_NSG=env.stats()['NSG'],actual_HNSW=routecalls+router.calls(),actual_threads=1,affinity=sorted(os.sched_getaffinity(0)));dump(O/'logs/training_jobs.json',jobs)
   if j%8==0 or j+1==len(choices):print('ACTION_PROGRESS',ds,j+1,len(choices),len(accepted),env.stats()['NSG'],flush=True)
  dump(models/'selected_actions.json',accepted);dump(out/'action_statistics.json',records);dump(out/'cache_accounting.json',dict(records=resolve_records,old_collision_checks=collisions,new_unique_keys=new_count))
  # Freeze both group lists before any merged or random-control response.
  eligible=read(O/'inputs'/ds/'eligible_groups.json');selected_hubs={e['hub'] for e in accepted}
  remaining=[g for g in eligible if g['hub'] not in selected_hubs];rng=np.random.Generator(np.random.PCG64(20260913))
  permutation=rng.permutation(len(remaining));random_groups=[remaining[int(i)] for i in permutation[:len(accepted)]]
  assert len(random_groups)==len(accepted)
  dump(models/'random_actions.json',random_groups);save(models/'random_permutation.npz',remaining_hubs=np.array([e['hub'] for e in remaining],np.int32),permutation=permutation)
  freeze(models/'before_union.json',[O/'protocol.md',O/'inputs'/ds/'candidates.json',models/'selected_actions.json',models/'random_actions.json',models/'random_permutation.npz',out/'action_statistics.json'])
  union=[]
  for name,groups in [('restore10',accepted),('random10',random_groups)]:
   assert time.monotonic()-start<1200 and time.time()<limit['query_hard_stop'];resources();tick=time.monotonic();mc=install(cfg['method'],groups,models/name);mc.update(model_name=name,name=name+'_L128');dump(models/name/'model.json',mc)
   installs.append(dict(kind=name,seconds=time.monotonic()-tick,graph=identity(mc['graph_file']),W=identity(mc['W']),groups=len(groups)))
   ur=Routes(dict(cfg,method=mc));r=ur.run();routecalls+=ur.calls();ur.close();b=resolve(r,name)
   save(out/(name+'.npz'),source_rows=np.arange(10000,30000,dtype=np.int64),**b);union.append(dict(model=name,groups=len(groups),**summary(b,base)))
  routecalls+=router.calls();router.close();router=None;stats=env.stats();assert routecalls<=1400512 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss<32*2**20;assert stats['NSG']<=32768 and stats['HNSW']==stats['builds']==0 and stats['actual_threads']==1
  dump(out/'cache_accounting_final.json',dict(records=resolve_records,old_collision_checks=collisions,new_unique_keys=new_count));dump(out/'union_statistics.json',union)
  job.update(status='COMPLETE',returncode=0,actual_NSG=stats['NSG'],actual_HNSW=routecalls,accepted_actions=len(accepted),vector_installs=len(installs),installs=installs,union=union,seconds=time.monotonic()-start,max_RSS_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,actual_threads=1,affinity=sorted(os.sched_getaffinity(0)),completed_at=time.time());dump(out/'cost.json',job)
 except BaseException as ex:
  job.update(status='FAILED_RESERVED_RETAINED',error=repr(ex),actual_NSG=env.stats()['NSG'] if env else 0,actual_HNSW=routecalls+(router.calls() if router else 0),seconds=time.monotonic()-start);raise
 finally:
  if router:router.close()
  if env:env.close()
  dump(O/'logs/training_jobs.json',jobs)
 print('E89_TRAIN_COMPLETE',ds,json.dumps(job),flush=True)
if __name__=='__main__':main(sys.argv[1])
