from common import *
import struct,collections
threads();check(O/'reviews/prequery_freeze.json');records=[];tick=time.monotonic()
for ds in DS:
 c=read(O/'inputs'/ds/'fit.json');m=c['method'];d=c['dim'];q=np.fromfile(c['queries_file'],np.float32,count=20000*d).reshape(20000,d);w=np.fromfile(m['W'],np.float32).reshape(-1,d).astype(float);mapping=np.fromfile(m['mapping'],np.int32);hubs=np.unique(mapping);members=[np.flatnonzero(mapping==h) for h in hubs];z=np.load(O/'models'/ds/'training.npz');slots=np.fromfile(O/'results'/ds/'routes_fit/slots.i32',np.int32).reshape(20000,7);entries=np.fromfile(O/'results'/ds/'routes_fit/entries.i32',np.int32).reshape(20000,3);assert np.array_equal(z['source_slot'],slots[:,0]) and np.array_equal(z['actual_entries'],entries) and np.array_equal(z['source_rows'],np.arange(10000,30000))
 b=Path(m['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',b);n,size=hd[2:4];adj=[list(struct.unpack_from('<'+'I'*struct.unpack_from('<H',b,96+i*size)[0],b,96+i*size+4)) for i in range(n)];votes=collections.Counter()
 for start in range(0,20000,512):
  score=q[start:start+512].astype(float)@w.T;maxs=np.stack([score[:,ii].max(1) for ii in members],axis=1)
  for j in range(len(score)):
   hs=np.lexsort((hubs,-maxs[j]))[:3];targets=[int(members[h][np.argmax(score[j,members[h]])]) for h in hs];assert np.array_equal(targets,z['desired_slots'][start+j]);s=int(slots[start+j,0]);known=set(entries[start+j].tolist())
   for t in targets:
    if mapping[t] not in known and len(adj[s])<32 and t!=s and t not in adj[s]:votes[s,t]+=1
 assert dict(votes)=={(int(s),int(t)):int(v) for s,t,v in z['votes']}
 expected={}
 for s in sorted(set(s for s,t in votes)):
  t=min([t for so,t in votes if so==s],key=lambda t:(-votes[s,t],t))
  if votes[s,t]>=2:expected[s]=t
 plans=read(O/'models'/ds/'additions.json');assert {x['slot']:x['shortcut_added'][0] for x in plans}==expected
 for x in plans:
  s=x['slot'];eligible=np.array([j for j in range(n) if mapping[j]!=mapping[s] and j not in adj[s]]);sc=np.sum(w[eligible]*w[s],axis=1);t=int(eligible[np.lexsort((eligible,-sc))[0]]);assert x['neighbor_added']==[t] and x['votes']==votes[s,x['shortcut_added'][0]]
 for name,field in [('shortcut10','shortcut_added'),('neighbor10','neighbor_added')]:
  a=(O/'models'/ds/name/'graph.hnsw').read_bytes();restored=bytearray(a);pl={x['slot']:x for x in plans};edges=[]
  for i in range(n):
   at=96+i*size;nd=struct.unpack_from('<H',a,at)[0];new=list(struct.unpack_from('<'+'I'*nd,a,at+4));added=pl[i][field] if i in pl else [];assert new==adj[i]+added and nd<=32 and len(new)==len(set(new));edges.append(new);restored[at:at+2]=b[at:at+2];left=at+4+len(adj[i])*4;right=at+4+nd*4;restored[left:right]=b[left:right]
  assert bytes(restored)==b
  seen={hd[7]};queue=list(seen)
  for i in queue:
   for j in edges[i]:
    if j not in seen:seen.add(j);queue.append(j)
  assert len(seen)==n
 records.append(dict(dataset=ds,all_fit_targets=20000,vote_pairs=len(votes),all_source_control_rankings=len(plans),all_old_edges_and_other_bytes_preserved=True,reachable_nodes=n))
dump(O/'reviews/training_independent.json',dict(status='PASS',records=records,seconds=time.monotonic()-tick));print('E84_TRAINING_VERIFIED',records)
