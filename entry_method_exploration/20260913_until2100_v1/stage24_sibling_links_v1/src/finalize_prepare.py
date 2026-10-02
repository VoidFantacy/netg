from common import *
from graph_reader import inspect_serialized
import struct
threads();resources();check(O/'reviews/preinstall_freeze.json');assert not (O/'reviews/prequery_freeze.json').exists();E73=C/'stage14_compact_modes_v1';paths=[Path(x['path']) for x in read(O/'reviews/preinstall_freeze.json')['files']];records=[];installs=[];start=time.monotonic()
for ds in DS:
 c=read(E73/'inputs'/ds/'aux.json');old=next(m for m in c['methods'] if m['model_name']=='compact10');W=np.fromfile(old['W'],np.float32).reshape(-1,c['dim']);mapping=np.fromfile(old['mapping'],np.int32);before=Path(old['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',before);n,size=hd[2:4];oldadj=[]
 for i in range(n):
  at=96+i*size;deg=struct.unpack_from('<H',before,at)[0];oldadj.append(list(struct.unpack_from('<'+'I'*deg,before,at+4)))
 changes=read(O/'models'/ds/'additions.json');byrow={x['slot']:x for x in changes};degrees=[]
 for name,field in [('sibling10','sibling_added'),('neighbor10','neighbor_added')]:
  m=read(O/'models'/ds/name/'model.json');after=Path(m['graph_file']).read_bytes();info=inspect_serialized(m['graph_file'],W,np.arange(n));restored=bytearray(after);dd=[]
  for i in range(n):
   at=96+i*size;deg=struct.unpack_from('<H',after,at)[0];dd.append(deg);a=list(struct.unpack_from('<'+'I'*deg,after,at+4));extra=byrow[i][field] if i in byrow else [];assert a==oldadj[i]+extra
   restored[at:at+2]=before[at:at+2];left=at+4+4*len(oldadj[i]);right=at+4+4*deg;restored[left:right]=before[left:right]
   if field=='sibling_added':assert extra==[j for j in range(n) if mapping[j]==mapping[i] and j!=i and j not in oldadj[i]][:32-len(oldadj[i])]
   else:assert all(mapping[j]!=mapping[i] and j not in oldadj[i] for j in extra)
  assert bytes(restored)==before;degrees.append(dd);installs.append(dict(dataset=ds,model=name,seconds=None,seconds_reason='completed all four installs before failed metadata serialization; durations not persisted',graph=identity(m['graph_file']),all_W_labels_header_upper_levels_unchanged=True,old_edge_prefix_bytes_preserved=True,only_count_and_unused_slots_changed=True,source_roundtrip_exact=True))
 assert degrees[0]==degrees[1]
 # Independent nearest-other ranking on 17 predetermined affected rows.
 for x in changes[::max(1,len(changes)//16)]:
  i=x['slot'];sc=np.sum(W.astype(float)*W[i].astype(float),axis=1);cand=[j for j in range(n) if mapping[j]!=mapping[i] and j not in oldadj[i]];assert sorted(cand,key=lambda j:(-sc[j],j))[:len(x['neighbor_added'])]==x['neighbor_added']
 missing=sum(int(sum(mapping[j]==mapping[i] and j!=i and j not in oldadj[i] for j in range(n))) for i in range(n));limited=sum(int(sum(mapping[j]==mapping[i] and j!=i and j not in oldadj[i] for j in range(n))>32-len(oldadj[i])) for i in range(n));added=sum(len(x['sibling_added']) for x in changes)
 assert (missing,added)==((1362,1359) if ds==DS[0] else (1286,1285))
 records.append(dict(dataset=ds,physical=n,missing_sibling_edges=missing,appended_edges_per_arm=added,changed_nodes=len(changes),capacity_limited_nodes=limited,old_edges=sum(map(len,oldadj)),new_edges=sum(map(len,oldadj))+added,plan_seconds=None))
dump(O/'results/construction.json',dict(status='PASS',datasets=records,installs=installs,builds=0,new_GT=0,gradient_updates=0,preparation_seconds=None,successful_recovery_verification_seconds=time.monotonic()-start,installs_performed_in='src/resume_prepare.py',no_reinstall_in_recovery=True))
dump(O/'reviews/serialization_repair.json',dict(failed_tool=79879,terminal_exit=1,reason='numpy int64 count in recovered metadata could not JSON serialize; all four graphs and input configs had been written and validated',new_source='src/finalize_prepare.py',numeric_counts_native_python_int=True,actual_installs=4,new_query_calls=0,prior_install_elapsed_seconds=None,old_sources_and_all_graphs_preserved=True))
paths+=list((O/'inputs').rglob('*.json'))+list((O/'models').rglob('*.hnsw'))+list((O/'src').glob('*.py'))+[O/'results/construction.json',O/'reviews/serialization_repair.json',O/'reviews/prepare_repair.json'];freeze(O/'reviews/prequery_freeze.json',paths);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='SIBLING_EDGES_INSTALLED_UNQUERIED',NSG=0,HNSW=0,builds=0,edge_installs=4,day_goal_complete=False));resources();print(json.dumps(records))
