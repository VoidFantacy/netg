from common import *
from graph_reader import inspect_serialized
import struct
threads();resources();assert not (O/'config.locked.json').exists();E73=C/'stage14_compact_modes_v1';paths=[O/'protocol.md',C/'session8_resource_protocol.json'];models={};plans={};records=[];started=time.monotonic()
def parse(path):
 data=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',data);off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head
 assert off==0 and mx==n and M0==32
 adj=[list(struct.unpack_from('<'+'I'*struct.unpack_from('<H',data,96+i*size)[0],data,96+i*size+4)) for i in range(n)]
 return data,head,adj
def reachable(adj,entry):
 seen={entry};todo=[entry]
 while todo:
  i=todo.pop()
  for j in adj[i]:
   if j not in seen:seen.add(j);todo.append(j)
 return seen
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json');assert sha(O/'bin/evaluate')==sha(E73/'bin/evaluate')
dump(O/'bin/provenance.json',dict(compile_seconds=0,evaluator=identity(O/'bin/evaluate'),source=identity(E73/'bin/evaluate'),link_reuse=True))
for ds,expected in zip(DS,[(1362,1359),(1286,1285)]):
 tick=time.monotonic();c=read(E73/'inputs'/ds/'aux.json');old=next(x for x in c['methods'] if x['model_name']=='compact10');W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim']);mapping=np.fromfile(old['mapping'],np.int32);data,head,adj=parse(old['graph_file']);inspect_serialized(old['graph_file'],W,np.arange(len(W)));n=len(W);groups={h:np.flatnonzero(mapping==h).tolist() for h in np.unique(mapping)};wf=W.astype(float);changes=[];missing=addcount=limited=0
 for i in range(n):
  siblings=[j for j in groups[mapping[i]] if j!=i and j not in adj[i]];room=32-len(adj[i]);added=siblings[:room];missing+=len(siblings);addcount+=len(added);limited+=len(siblings)>room
  if not added:continue
  score=wf@wf[i];order=np.lexsort((np.arange(n),-score));other=[int(j) for j in order if mapping[j]!=mapping[i] and int(j) not in adj[i]][:len(added)];assert len(other)==len(added)
  changes.append(dict(slot=i,real_hub=int(mapping[i]),old_degree=len(adj[i]),sibling_missing=siblings,sibling_added=added,neighbor_added=other,sibling_cosine=[float(score[j]) for j in added],neighbor_cosine=[float(score[j]) for j in other]))
 assert (missing,addcount)==expected
 dest=O/'models'/ds;dest.mkdir();models[ds]=[]
 for name in ['sibling10','neighbor10']:
  folder=dest/name;folder.mkdir();m=dict(old,model_name=name,name=name+'_L128',graph_file=str(folder/'graph.hnsw'));dump(folder/'model.json',m);models[ds].append(m)
 dump(dest/'additions.json',changes);plans[ds]=(old,W,mapping,data,head,adj,changes)
 rec=dict(dataset=ds,physical=n,missing_sibling_edges=missing,appended_edges_per_arm=addcount,changed_nodes=len(changes),capacity_limited_nodes=limited,old_edges=sum(map(len,adj)),new_edges=sum(map(len,adj))+addcount,source_reachable=len(reachable(adj,head[7])),plan_seconds=time.monotonic()-tick);records.append(rec)
 paths += [E73/'inputs'/ds/'aux.json',E73/'reviews/final_artifact_freeze.json']+[Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:paths += [Path(m[k]) for k in ['W','mapping','tie_ids','graph_file']]
 # Actual source dependency identity from final E73 seal.
 recs={x['path']:x for x in read(E73/'reviews/final_artifact_freeze.json')['files']}
 for p in set(paths):
  if str(p) in recs:assert sha(p)==recs[str(p)]['sha256']
dump(O/'config.locked.json',dict(datasets=DS,threads=1,CPU=15,NSG_expected=129536,HNSW_expected=129280,builds=0,edge_installs=4,NSG_hard_cap=132000,output_cap_MiB=64,free_min_GiB=6.65,evening_reserve_MiB=64,handoff_reserve_MiB=8,latest_launch=1789289700,query_hard_stop=1789290300,per_job_seconds=600,quality_gate='sibling vs P/compact full>0 halves>=0 failures<=0; vs neighbor full>=0 halves>=0 failures<=0',wall_measurement='only if one dataset passes; new independent full matrix'))
paths += list((O/'src').glob('*'))+list((O/'models').rglob('*.json'))+list((O/'bin').glob('*'))+[O/'config.locked.json']+[E73/'src'/x for x in ['evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']];freeze(O/'reviews/preinstall_freeze.json',paths)
installs=[]
for ds in DS:
 old,W,mapping,before,head,adj,changes=plans[ds];n,size=head[2:4]
 for m in models[ds]:
  tick=time.monotonic();data=bytearray(before);newadj=[list(x) for x in adj];which='sibling_added' if m['model_name']=='sibling10' else 'neighbor_added'
  for x in changes:
   i=x['slot'];newadj[i]+=x[which];at=96+i*size;struct.pack_into('<H',data,at,len(newadj[i]));struct.pack_into('<'+'I'*len(x[which]),data,at+4+4*x['old_degree'],*x[which])
  dest=Path(m['graph_file']);assert not dest.exists();dest.write_bytes(data);newdata,nh,na=parse(dest);assert nh==head and na==newadj
  inspect_serialized(dest,W,np.arange(n));restored=bytearray(newdata)
  for i in range(n):
   assert newadj[i][:len(adj[i])]==adj[i] and len(newadj[i])<=32 and len(set(newadj[i]))==len(newadj[i]) and i not in newadj[i]
   at=96+i*size;restored[at:at+2]=before[at:at+2]
   l=at+4+4*len(adj[i]);r=at+4+4*len(newadj[i]);restored[l:r]=before[l:r]
  assert bytes(restored)==before and reachable(adj,head[7])<=reachable(newadj,head[7])
  installs.append(dict(dataset=ds,model=m['model_name'],seconds=time.monotonic()-tick,graph=identity(dest),all_W_labels_header_upper_levels_unchanged=True,old_edge_prefix_bytes_preserved=True,only_count_and_unused_slots_changed=True,source_roundtrip_exact=True,reachable=len(reachable(newadj,head[7]))))
 # Independent all-row degree equality across two arms, exact append rule and reference dot ranking.
 got=[parse(m['graph_file'])[2] for m in models[ds]];assert list(map(len,got[0]))==list(map(len,got[1]))
 for x in changes:
  i=x['slot'];ref=sorted(j for j in range(n) if mapping[j]==mapping[i] and j!=i and j not in adj[i])[:32-len(adj[i])];assert got[0][i][len(adj[i]):]==ref
  assert all(mapping[j]!=mapping[i] and j not in adj[i] for j in got[1][i][len(adj[i]):])
 for x in changes[::max(1,len(changes)//16)]:
  i=x['slot'];scores=np.sum(wf*wf[i],axis=1) if False else np.sum(W.astype(float)*W[i].astype(float),axis=1);cand=[j for j in range(n) if mapping[j]!=mapping[i] and j not in adj[i]];ref=sorted(cand,key=lambda j:(-scores[j],j))[:len(x['neighbor_added'])];assert ref==x['neighbor_added']
for di,ds in enumerate(DS):
 old=read(E73/'inputs'/ds/'aux.json');inp=O/'inputs'/ds;inp.mkdir()
 for split,n in [('preflight',128),('aux',7952)]:
  methods=[dict(x) for x in old['methods'] if x['model_name'] in ['baseline10','compact10']]+models[ds];c=dict(old,methods=methods,split='E83_historical_aux_'+split,num_queries=n,input_total_rows=7952,dataset_order=di,real_call_cap=4*(2*n+16),timing_repeats=0);dump(inp/(split+'.json'),c)
dump(O/'results/construction.json',dict(status='PASS',datasets=records,installs=installs,builds=0,new_GT=0,gradient_updates=0,preparation_seconds=time.monotonic()-started));paths+=list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+[O/'results/construction.json'];freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='SIBLING_EDGES_INSTALLED_UNQUERIED',NSG=0,HNSW=0,builds=0,edge_installs=4,day_goal_complete=False));resources();print(json.dumps(records),flush=True)
