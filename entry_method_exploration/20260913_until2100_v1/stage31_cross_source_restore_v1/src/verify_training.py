from common import *
from graph_reader import inspect_serialized
import struct
threads();resources();check(O/'reviews/pretraining_freeze.json');jobs=read(O/'logs/training_jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs);report=[]
for ds in DS:
 choices=read(O/'inputs'/ds/'candidates.json');chosen=read(O/'models'/ds/'selected_actions.json');random=read(O/'models'/ds/'random_actions.json');perm=np.random.Generator(np.random.PCG64(20260913)).permutation(len(choices));assert random==[choices[int(i)] for i in perm[:len(chosen)]]
 total_new=0;checked_rows=0;role_records=[]
 for role,n,reg in [('support',3976,16),('fit',20000,32)]:
  nc=read(O/'inputs'/ds/('native_'+role+'.json'));cfg=read(O/'inputs'/ds/('routes_'+role+'.json'));gt=np.fromfile(nc['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(nc['row_ids'],np.int64);assert np.array_equal(rows,np.arange(2048,6024) if role=='support' else np.arange(10000,30000));out=O/'results'/ds/role;base=dict(np.load(out/'compact_baseline.npz'))
  if role=='support':old=[raw(E89/'results'/ds/'aux'/(m+'_L128'),n) for m in ['baseline10','compact10','restore10']]
  else:old=[raw(E66/'results'/ds/'fit/baseline_L128')]+[dict(np.load(E89/'results'/ds/'fit'/(m+'.npz'))) for m in ['compact_baseline','restore10']]
  cache={}
  for a in old:
   for i,e in enumerate(a['entries']):
    key=(i,*map(int,e));v=(a['ids'][i].tobytes(),a['distances'][i].tobytes(),int(a['graph_ndc'][i]))
    if key in cache:assert cache[key]==v
    cache[key]=v
  newparts=[];count=0
  for r in read(out/'cache_accounting.json')['records']:
   if not r['new_keys']:continue
   z=dict(np.load(out/(r['name']+'_new.npz')));assert int(z['global_begin'])==count and len(z['rows'])==r['new_keys'];count+=len(z['rows']);newparts.append(z)
   for j,(i,e) in enumerate(zip(z['rows'],z['entries'])):
    key=(int(i),*map(int,e));assert key not in cache;cache[key]=(z['ids'][j].tobytes(),z['distances'][j].tobytes(),int(z['graph_ndc'][j]))
  new={f:np.concatenate([p[f] for p in newparts]) if newparts else old[0][f][:0].copy() for f in ['ids','distances','graph_ndc']};sources=old+[new];total_new+=count
  def verify(a,indices):
   global_dummy=0
   h,mask=score(a['ids'],gt[indices]);assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask'])
   for j,i in enumerate(indices):
    assert len(set(a['ids'][j].tolist())&set(gt[i,:10].tolist()))==int(h[j]);actual=(a['ids'][j].tobytes(),a['distances'][j].tobytes(),int(a['graph_ndc'][j]));assert actual==cache[(int(i),*map(int,a['entries'][j]))]
    code,ix=int(a['source_code'][j]),int(a['source_index'][j]);source=sources[code];assert actual==(source['ids'][ix].tobytes(),source['distances'][ix].tobytes(),int(source['graph_ndc'][ix]))
  def stats(a):
   d=a['hits'].astype(np.int64)-base['hits'];halves=[int(d[:n//2].sum()),int(d[n//2:].sum())];failure=int((a['hits']==0).sum()-(base['hits']==0).sum());cost=(a['graph_ndc'].sum(dtype=np.uint64)+a['route_ndc'].sum(dtype=np.uint64))/(base['graph_ndc'].sum(dtype=np.uint64)+base['route_ndc'].sum(dtype=np.uint64))-1
   return dict(net_hits=int(d.sum()),half_net_hits=halves,failure_delta=failure,total_ndc_relative=float(cost),accepted=bool(d.sum()>0 and min(halves)>=0 and failure<=0 and cost<=.01))
  verify(base,np.arange(n));same(base,old[1],('ids','distances','entries','graph_ndc','route_ndc','hits','mask'));checked_rows+=n;additive=np.zeros(n,np.int64)
  if role=='support':
   picked=[];records=read(out/'action_statistics.json');assert len(records)==len(choices)
   for j,(e,rec) in enumerate(zip(choices,records)):
    z=dict(np.load(out/f'action_{j:03}.npz'));ix=z['rows'];verify(z,ix);checked_rows+=len(ix);a={k:base[k].copy() for k in ['entries','hits','mask','ids','distances','graph_ndc','route_ndc','slots','slot_distances']}
    for k in ['entries','hits','mask','ids','distances','graph_ndc']:a[k][ix]=z[k]
    a['route_ndc']=z['route_ndc'];a['slots'][z['route_changed_rows']]=z['slots'];a['slot_distances'][z['route_changed_rows']]=z['slot_distances']
    for k in rec['route_hashes']:assert hashlib.sha256(a[k].tobytes()).hexdigest()==rec['route_hashes'][k]
    st=stats(a)
    for k in st:assert abs(st[k]-rec[k])<1e-12 if isinstance(st[k],float) else st[k]==rec[k]
    if st['accepted']:picked.append(e);additive+=a['hits'].astype(int)-base['hits']
   assert picked==chosen
  else:
   original_records=read(E89/'results'/ds/'fit/action_statistics.json')
   for e in chosen:
    j=next(i for i,r in enumerate(original_records) if r['hub']==e['hub']);z=dict(np.load(E89/'results'/ds/'fit'/f'action_{j:03}.npz'));additive[z['rows']]+=z['hits'].astype(int)-base['hits'][z['rows']]
  for name in ['supported10','random10']:
   a=dict(np.load(out/(name+'.npz')));verify(a,np.arange(n));checked_rows+=n;st=stats(a);rec=next(r for r in read(O/'results'/ds/'union_statistics.json') if r['role']==role and r['model']==name)
   for k in st:assert abs(st[k]-rec[k])<1e-12 if isinstance(st[k],float) else st[k]==rec[k]
   if name=='supported10':
    actual=a['hits'].astype(int)-base['hits'];save(out/'interaction.npz',source_rows=rows,independent_sum=additive,actual_merged=actual,interaction=actual-additive);role_records.append(dict(role=role,independent_sum=int(additive.sum()),actual_merged=int(actual.sum()),nonadditive_queries=int(np.count_nonzero(actual!=additive)),new_keys=count))
  for mode in ['count','plain','reference']:
   z=dict(np.load(out/('baseline_'+mode+'_regression.npz')));same(z,{k:base[k][:reg] for k in ['ids','distances','graph_ndc']},('ids','distances') if mode=='plain' else ('ids','distances','graph_ndc'))
 cfg=read(O/'inputs'/ds/'routes_fit.json');mc=cfg['method'];W=np.fromfile(mc['W'],np.float32).reshape(-1,cfg['dim']);before=Path(mc['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',before);n,size,label,coord=hd[2:6]
 for name,groups in [('supported10',chosen),('random10',random)]:
  model=read(O/'models'/ds/name/'model.json');expected=W.copy()
  for g in groups:
   for slot in g['child_slots']:expected[slot]=W[g['parent_slot']]
  assert Path(model['W']).read_bytes()==expected.tobytes();inspect_serialized(model['graph_file'],expected,np.arange(n));after=Path(model['graph_file']).read_bytes();restore=bytearray(after)
  for j in range(n):at=96+j*size+coord;restore[at:at+cfg['dim']*4]=before[at:at+cfg['dim']*4]
  assert bytes(restore)==before
 job=next(j for j in jobs if j['dataset']==ds);assert job['actual_NSG']==2*total_new+144 and job['actual_HNSW']==(len(choices)+3)*3976*2+120000
 report.append(dict(dataset=ds,actions=len(choices),accepted=len(chosen),new_keys=total_new,NSG=job['actual_NSG'],HNSW=job['actual_HNSW'],verified_response_rows=checked_rows,roles=role_records))
dump(O/'reviews/training_verification.json',dict(status='PASS',records=report,all_source_keys_graph_vectors_and_nonvector_bytes_verified=True,new_ANN=0,final_feedback_used=False));print('E90_TRAINING_VERIFIED',report)
