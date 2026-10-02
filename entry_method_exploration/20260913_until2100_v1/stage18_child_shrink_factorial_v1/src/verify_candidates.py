from common import *
from graph_reader import inspect_serialized
def load_raw(p,n):
 a={}
 for k,(fn,dt,w) in FIELDS.items():
  x=np.fromfile(p/fn,dt);a[k]=x.reshape(n,w) if w>1 else x
 a['route_ndc']=np.fromfile(p/'route_ndc.u32',np.uint32)
 return a
def verify_candidates(c,m,p,a,n):
 mapping=np.fromfile(m['mapping'],np.int32);W=np.fromfile(m['W'],np.float32).reshape(-1,c['dim'])
 inspect_serialized(m['graph_file'],W,np.arange(len(W)) if m.get('slot_labels') else mapping)
 if not m.get('multi_profile'):return 0
 q=np.memmap(c['queries_file'],np.float32,mode='r').reshape(-1,c['dim'])[:n]
 slots=np.fromfile(p/'candidate_slots.i32',np.int32).reshape(n,7);dist=np.fromfile(p/'candidate_distances.f32',np.float32).reshape(n,7)
 for i in range(n):
  s=slots[i];v=dist[i];assert len(set(s.tolist()))==7 and s.min()>=0 and s.max()<len(mapping)
  assert np.array_equal(np.lexsort((s,v)),np.arange(7));selected=[]
  for slot in s:
   hub=int(mapping[slot])
   if hub not in selected:selected.append(hub)
  assert len(selected)>=3 and sorted(selected[:3])==a['entries'][i].tolist()
  assert np.allclose(1-W[s].astype(float)@q[i].astype(float),v,rtol=2e-5,atol=2e-5)
 return n
