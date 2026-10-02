from common import *
import struct,collections
threads();resources();check(O/'reviews/pretraining_freeze.json');summary=[]
for ds in DS:
 c=read(O/'inputs'/ds/'routes.json');nc=read(O/'inputs'/ds/'native_training.json');z=dict(np.load(O/'inputs'/ds/'proposals.npz'));b=dict(np.load(E86/'results'/ds/'fit/compact_baseline.npz'));mapping=np.fromfile(c['method']['mapping'],np.int32);W=np.fromfile(c['method']['W'],np.float32).reshape(-1,c['dim']);q=np.fromfile(nc['queries_file'],np.float32).reshape(20000,c['dim']);data=Path(c['method']['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',data);n,size=hd[2:4];events=[];votes=collections.Counter();support=collections.defaultdict(set)
 for i in range(20000):
  delta=int(z['P_hits'][i])-int(z['compact_hits'][i]);source=int(b['slots'][i,0]);at=96+source*size;degree=struct.unpack_from('<H',data,at)[0];old=struct.unpack_from('<'+'I'*degree,data,at+4)
  if delta<=0:continue
  for h in z['P_entries'][i]:
   if h in z['compact_entries'][i]:continue
   candidates=np.flatnonzero(mapping==h);values=np.einsum('ij,j->i',W[candidates].astype(float),q[i].astype(float));target=int(candidates[np.argmax(values)])
   if degree==32 or target in old or target==source:continue
   events.append([i,source,target,delta,int(z['P_hits'][i]),int(z['compact_hits'][i])]);votes[source,target]+=delta;support[source,target].add(i)
 assert np.array_equal(np.asarray(events,np.int32).reshape(-1,6),z['events']);vv=np.asarray([(s,t,v,len(support[s,t])) for (s,t),v in sorted(votes.items())],np.int32).reshape(-1,4);assert np.array_equal(vv,z['votes'])
 possible=[]
 for s in sorted({s for s,t in votes}):
  target=min([t for so,t in votes if so==s],key=lambda t:(-votes[s,t],t))
  if len(support[s,target])>=2:possible.append((s,target))
 selected=sorted(possible,key=lambda x:(-votes[x],x[0],x[1]))[:64];saved=read(O/'inputs'/ds/'candidates.json');assert selected==[(e['slot'],e['shortcut_added'][0]) for e in saved]
 for e in saved:
  s=e['slot'];at=96+s*size;deg=struct.unpack_from('<H',data,at)[0];old=struct.unpack_from('<'+'I'*deg,data,at+4);scores=np.einsum('ij,j->i',W.astype(float),W[s].astype(float));valid=[i for i in range(n) if mapping[i]!=mapping[s] and i not in old];ref=min(valid,key=lambda t:(-scores[t],t));assert ref==e['neighbor_added'][0]
 summary.append(dict(dataset=ds,all_query_candidate_rules_verified=20000,all_events=len(events),candidates=len(saved),independent_full_target_and_neighbor_ranking=True))
dump(O/'reviews/proposals_independent.json',dict(status='PASS',datasets=summary,no_new_ANN=True));print('E87_PROPOSALS_INDEPENDENT_PASS',summary)
