from common import *
from graph_reader import inspect_serialized
import struct,itertools
threads();resources();check(O/'reviews/pretraining_freeze.json');jobs=read(O/'logs/training_jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
tick=time.monotonic();records=[]
for ds in DS:
 cfg=read(O/'inputs'/ds/'routes.json');nc=read(O/'inputs'/ds/'native_training.json');gt=np.fromfile(nc['gt_file'],np.int64).reshape(20000,100);out=O/'results'/ds/'fit';base=dict(np.load(out/'compact_baseline.npz'));old=[raw(E66/'results'/ds/'fit'/(m+'_L128')) for m in ['baseline','mode3P']];cache={};new_parts=[];new_rows=[];new_entries=[]
 for b in old:
  for i,e in enumerate(b['entries']):
   key=(i,*map(int,e));v=(b['ids'][i].tobytes(),b['distances'][i].tobytes(),int(b['graph_ndc'][i]))
   if key in cache:assert cache[key]==v
   cache[key]=v
 count=0
 for r in read(out/'cache_accounting_final.json')['records']:
  if not r['new_keys']:continue
  z=dict(np.load(out/(r['name']+'_new.npz')));assert int(z['global_begin'])==count and len(z['rows'])==r['new_keys'];count+=len(z['rows']);new_parts.append(z);new_rows.extend(z['rows'].tolist());new_entries.extend(z['entries'].tolist())
  h,m=score(z['ids'],gt[z['rows']]);assert all(len(set(ids.tolist())&set(gt[i,:10].tolist()))==hi for i,ids,hi in zip(z['rows'],z['ids'],h))
  for j,(i,e) in enumerate(zip(z['rows'],z['entries'])):
   key=(int(i),*map(int,e));assert key not in cache,'new key already cached';cache[key]=(z['ids'][j].tobytes(),z['distances'][j].tobytes(),int(z['graph_ndc'][j]))
 new={k:np.concatenate([x[k] for x in new_parts]) for k in ['ids','distances','graph_ndc']};sources=old+[new]
 def verify_raw(a,indices):
  h,m=score(a['ids'],gt[indices]);assert np.array_equal(h,a['hits']) and np.array_equal(m,a['mask'])
  for j,i in enumerate(indices):
   key=(int(i),*map(int,a['entries'][j]));actual=(a['ids'][j].tobytes(),a['distances'][j].tobytes(),int(a['graph_ndc'][j]));assert cache[key]==actual
   src=sources[int(a['source_code'][j])];si=int(a['source_index'][j]);assert actual==(src['ids'][si].tobytes(),src['distances'][si].tobytes(),int(src['graph_ndc'][si]))
 def stats(h,g,r):
  dh=h.astype(np.int64)-base['hits'];parts=[int(dh[:10000].sum()),int(dh[10000:].sum())];fd=int(np.count_nonzero(h==0)-np.count_nonzero(base['hits']==0));cost=(np.sum(g,dtype=np.uint64)+np.sum(r,dtype=np.uint64))/(np.sum(base['graph_ndc'],dtype=np.uint64)+np.sum(base['route_ndc'],dtype=np.uint64))-1
  return dict(net_hits=int(dh.sum()),half_net_hits=parts,failure_delta=fd,total_ndc_relative=float(cost),accepted=bool(dh.sum()>0 and min(parts)>=0 and fd<=0 and cost<=.01))
 verify_raw(base,np.arange(20000));mapping=np.fromfile(cfg['method']['mapping'],np.int32);choices=read(O/'inputs'/ds/'candidates.json');saved=read(out/'edge_statistics.json');picked=[];changed=0
 for j,(e,s) in enumerate(zip(choices,saved)):
  z=dict(np.load(out/f'edge_{j:03}.npz'));ix=z['rows'];verify_raw({k:z[k] for k in ['ids','distances','entries','hits','mask','graph_ndc','source_code','source_index']},ix);changed+=len(ix)
  rr={k:base[k].copy() for k in ['entries','slots','slot_distances','route_ndc']};rr['entries'][ix]=z['entries'];rr['slots'][z['route_changed_rows']]=z['slots'];rr['slot_distances'][z['route_changed_rows']]=z['slot_distances'];rr['route_ndc']=z['route_ndc']
  for k in rr:assert hashlib.sha256(rr[k].tobytes()).hexdigest()==s['route_hashes'][k]
  for ii in z['route_changed_rows']:
   sl=rr['slots'][ii];dist=rr['slot_distances'][ii];assert np.array_equal(np.lexsort((sl,dist)),np.arange(7));hubs=list(dict.fromkeys(map(int,mapping[sl])));assert sorted(hubs[:3])==rr['entries'][ii].tolist()
  h=base['hits'].copy();g=base['graph_ndc'].copy();h[ix]=z['hits'];g[ix]=z['graph_ndc'];v=stats(h,g,z['route_ndc'])
  for k in v:assert abs(v[k]-s[k])<1e-12 if isinstance(v[k],float) else v[k]==s[k],(ds,j,k)
  if v['accepted']:picked.append(e)
 assert picked==read(O/'models'/ds/'selected_edges.json')
 before=Path(cfg['method']['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',before);nn,size=hd[2:4];W=np.fromfile(cfg['method']['W'],np.float32).reshape(nn,cfg['dim']);plans={e['slot']:e for e in picked};degree=[]
 for name,field in [('utility10','shortcut_added'),('neighbor10','neighbor_added')]:
  p=O/'models'/ds/name/'graph.hnsw';inspect_serialized(p,W,np.arange(nn));after=p.read_bytes();restore=bytearray(after);degrees=[]
  for i in range(nn):
   at=96+i*size;od=struct.unpack_from('<H',before,at)[0];nd=struct.unpack_from('<H',after,at)[0];oa=list(struct.unpack_from('<'+'I'*od,before,at+4));na=list(struct.unpack_from('<'+'I'*nd,after,at+4));assert na==oa+(plans[i][field] if i in plans else []);degrees.append(nd);restore[at:at+2]=before[at:at+2];lo=at+4+4*od;hi=at+4+4*nd;restore[lo:hi]=before[lo:hi]
  assert bytes(restore)==before;degree.append(degrees);a=dict(np.load(out/(name+'.npz')));verify_raw(a,np.arange(20000));v=stats(a['hits'],a['graph_ndc'],a['route_ndc']);s=next(x for x in read(out/'union_statistics.json') if x['model']==name)
  for k in v:assert abs(v[k]-s[k])<1e-12 if isinstance(v[k],float) else v[k]==s[k]
 assert degree[0]==degree[1]
 j=next(j for j in jobs if j['dataset']==ds);assert j['actual_NSG']==2*count+96 and j['actual_HNSW']==(len(choices)+3)*40000+256
 records.append(dict(dataset=ds,candidates=len(choices),selected=len(picked),changed_triple_rows=changed,new_unique_keys=count,new_NSG=j['actual_NSG'],HNSW=j['actual_HNSW'],verified_full_output_rows=60000,all_graph_old_edges_and_other_bytes_preserved=True))
dump(O/'reviews/training_verification.json',dict(status='PASS',records=records,seconds=time.monotonic()-tick,source_and_cached_keys_verified=True,query_GT_namespace='historically used router_train[10000:30000]',final_feedback_used=False));resources();print('E86_TRAIN_VERIFIED',records)
