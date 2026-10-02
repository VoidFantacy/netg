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
