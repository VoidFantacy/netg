from common import *
import struct
threads();resources();assert not (O/'reviews/pretraining_freeze.json').exists();check(E86/'reviews/final_artifact_freeze.json');paths=[O/'protocol.md',C/'session9_resource_protocol.json',E86/'reviews/final_artifact_freeze.json'];records=[]
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir();cfg=read(E86/'inputs'/ds/'routes.json');native=read(E86/'inputs'/ds/'native_training.json');dump(inp/'routes.json',cfg);dump(inp/'native_training.json',native)
 d=cfg['dim'];q=np.fromfile(native['queries_file'],np.float32).reshape(20000,d);gt=np.fromfile(native['gt_file'],np.int64).reshape(20000,100);rows=np.fromfile(native['row_ids'],np.int64);assert np.array_equal(rows,np.arange(10000,30000));p=raw(E66/'results'/ds/'fit/baseline_L128');b=dict(np.load(E86/'results'/ds/'fit/compact_baseline.npz'))
 for a in [p,b]:
  h,m=score(a['ids'],gt);assert np.array_equal(h,a['hits']) and np.array_equal(m,a['mask'])
 mapping=np.fromfile(cfg['method']['mapping'],np.int32);W=np.fromfile(cfg['method']['W'],np.float32).reshape(-1,d).astype(float);blob=Path(cfg['method']['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',blob);nn,size=hd[2:4];adj=[list(struct.unpack_from('<'+'I'*struct.unpack_from('<H',blob,96+i*size)[0],blob,96+i*size+4)) for i in range(nn)];slots={int(h):np.flatnonzero(mapping==h) for h in np.unique(mapping)}
 positive=np.flatnonzero(p['hits']>b['hits']);events=[];scores=[];votes={};support={}
 for i in positive:
  source=int(b['slots'][i,0]);weight=int(p['hits'][i])-int(b['hits'][i]);found=set(map(int,b['entries'][i]));qq=q[i].astype(float)
  for h in p['entries'][i]:
   if int(h) in found:continue
   ss=slots[int(h)];v=W[ss]@qq;target=int(ss[np.argmax(v)])
   if len(adj[source])==32 or target in adj[source] or target==source:continue
   assert mapping[source]!=mapping[target];key=(source,target);votes[key]=votes.get(key,0)+weight;support.setdefault(key,set()).add(int(i));events.append([int(i),source,target,weight,int(p['hits'][i]),int(b['hits'][i])]);scores.append(float(np.max(v)))
 all_choices=[]
 for source in sorted({s for s,t in votes}):
  opts=[(weight,t) for (s,t),weight in votes.items() if s==source];weight,target=min(opts,key=lambda x:(-x[0],x[1]));sup=len(support[source,target])
  if sup<2:continue
  cs=W@W[source];possible=[j for j in range(nn) if mapping[j]!=mapping[source] and j not in adj[source]];near=min(possible,key=lambda j:(-cs[j],j));all_choices.append(dict(slot=source,real_hub=int(mapping[source]),old_degree=len(adj[source]),shortcut_added=[target],neighbor_added=[near],votes=weight,query_support=sup,target_real_hub=int(mapping[target]),shortcut_cosine=float(cs[target]),neighbor_cosine=float(cs[near])))
 candidates=sorted(all_choices,key=lambda x:(-x['votes'],x['slot'],x['shortcut_added'][0]))[:64];dump(inp/'candidates.json',candidates);dump(inp/'all_eligible_sources.json',all_choices)
 # Independent aggregation over persisted event records; complete strategy reward is a proposal weight only.
 ev=np.asarray(events,np.int32).reshape(-1,6);vv=np.array([(s,t,w,len(support[s,t])) for (s,t),w in sorted(votes.items())],np.int32).reshape(-1,4);recount={}
 for row,s,t,w,ph,bh in ev:
  assert int(ph)-int(bh)==int(w)>0 and int(mapping[t]) in set(map(int,p['entries'][row]))-set(map(int,b['entries'][row]));recount[s,t]=recount.get((s,t),0)+int(w)
 assert recount==votes
 save(inp/'proposals.npz',source_rows=rows,P_entries=p['entries'],compact_entries=b['entries'],P_hits=p['hits'],compact_hits=b['hits'],events=ev,target_scores=np.asarray(scores),votes=vv)
 old84={(x['slot'],x['shortcut_added'][0]) for x in read(E84/'models'/ds/'additions.json')};old86={(x['slot'],x['shortcut_added'][0]) for x in read(E86/'inputs'/ds/'candidates.json')}
 records.append(dict(dataset=ds,fit_P_better_queries=len(positive),eligible_vote_events=len(events),unique_pairs=len(votes),eligible_sources=len(all_choices),selected_candidates=len(candidates),total_weight_votes=int(vv[:,2].sum()),overlap_E84=sum((x['slot'],x['shortcut_added'][0]) in old84 for x in candidates),overlap_E86=sum((x['slot'],x['shortcut_added'][0]) in old86 for x in candidates)))
 paths += [Path(native[k]) for k in ['queries_file','gt_file','row_ids','hub_ids']]+[Path(cfg['method'][k]) for k in ['W','mapping','tie_ids','graph_file']]+[E86/'results'/ds/'fit/compact_baseline.npz']+list((inp).glob('*'))
 for m in ['baseline','mode3P']:paths += [E66/'results'/ds/'fit'/(m+'_L128')/f for f,dt,w in FIELDS.values()]
 paths += list((E84/'results'/ds/'routes_fit').glob('*'))
 for x in read(E86/'reviews/base_graph_identity.json')['sources']:
  s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
dump(O/'reviews/proposal_verification.json',dict(status='PASS',records=records,scope='Complete P-vs-compact utility suggests targets; only actual one-edge NSG response may accept an edge. No new ANN yet.'))
dump(O/'config.locked.json',dict(training_NSG_cap=32768,per_dataset_training_NSG_cap=16384,training_HNSW_cap=5360512,aux_NSG=194304,aux_HNSW=193920,NSG_hard_cap=227072,HNSW_hard_cap=5554432,latest_training_launch=1789293300,latest_aux_launch=1789293720,query_hard_stop=1789294200,output_cap_MiB=96,free_min_GiB=6.55,threads=1,CPU=15))
dump(O/'bin/provenance.json',dict(compile_seconds=0,seconds=0,route_binary=identity(E86/'bin/routes.so'),NSG_binary=identity(C/'stage10_exact_triple_utility_v1/bin/inject.so'),evaluator=identity(E73/'bin/evaluate'),new_compilation=False))
paths += [O/'src'/s for s in ['common.py','native.py','routes.py','train.py','graph_reader.py','verify_training.py','propose.py']]+[O/'reviews/proposal_verification.json',O/'config.locked.json',O/'bin/provenance.json',E86/'bin/routes.so',C/'stage10_exact_triple_utility_v1/bin/inject.so',E73/'bin/evaluate']
freeze(O/'reviews/pretraining_freeze.json',[p for p in paths if p.is_file()]);dump(O/'logs/training_jobs.json',[]);dump(O/'logs/jobs.json',[]);dump(O/'state.json',dict(status='UTILITY_PROPOSALS_FROZEN_READY_TRAINING',NSG=0,HNSW=0,day_goal_complete=False));resources();print('E87_PROPOSALS_READY',records,flush=True)
