from common import *
def load_raw(p,n):
 a={}
 for k,(fn,dt,w) in FIELDS.items():
  x=np.fromfile(p/fn,dt);a[k]=x.reshape(n,w) if w>1 else x
 a['route_ndc']=np.fromfile(p/'route_ndc.u32',np.uint32)
 return a
def verify_candidates(c,m,p,a,n):
 if not m.get('distinct_hub_width'):return 0
 d=c['dim'];q=np.memmap(c['queries_file'],np.float32,mode='r').reshape(-1,d)[:n]
 W=np.fromfile(m['W'],np.float32).reshape(-1,d);mapping=np.fromfile(m['mapping'],np.int32)
 slots=np.fromfile(p/'distinct_slots.i32',np.int32).reshape(n,30);dist=np.fromfile(p/'distinct_distances.f32',np.float32).reshape(n,30)
 sizes=np.fromfile(p/'distinct_size.u32',np.uint32);hubs=np.fromfile(p/'distinct_hubs.u32',np.uint32)
 assert np.all(hubs==10) and np.all((sizes>=10)&(sizes<=30))
 for i in range(n):
  length=int(sizes[i]);s=slots[i,:length];v=dist[i,:length]
  assert len(set(s.tolist()))==length and s.min()>=0 and s.max()<len(mapping)
  assert len(set(mapping[s].tolist()))==10 and np.all(slots[i,length:]==0) and np.all(dist[i,length:]==0)
  assert np.all(np.diff(v)>=0)
  if m.get('multi_profile'):assert np.array_equal(np.lexsort((s,v)),np.arange(length))
  selected=[]
  for slot in s:
   hub=int(mapping[slot])
   if hub not in selected:selected.append(hub)
  assert sorted(selected[:3])==a['entries'][i].tolist()
  # Independent float64 scoring checks returned native float32 distances, never chooses routes.
  assert np.allclose(1-W[s].astype(float)@q[i].astype(float),v,rtol=2e-5,atol=2e-5)
 return n
