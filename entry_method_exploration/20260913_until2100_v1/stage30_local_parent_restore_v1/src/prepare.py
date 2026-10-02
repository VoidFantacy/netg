from common import *
import subprocess,csv
threads();resources();tick=time.monotonic()
paths=list((O/'src').glob('*'))+[O/'protocol.md',C/'session10_resource_protocol.json']
for ds in DS:
 inp=O/'inputs'/ds;inp.mkdir()
 cfg=read(E86/'inputs'/ds/'routes.json');nc=read(E86/'inputs'/ds/'native_training.json');nc['native_call_cap']=32768
 m=cfg['method'];d=cfg['dim'];w=np.fromfile(m['W'],np.float32).reshape(-1,d);mp=np.fromfile(m['mapping'],np.int32)
 original=np.fromfile(E73/'models'/ds/'original_slots.i32',np.int32);groups={int(h):np.flatnonzero(mp==h) for h in np.unique(mp)}
 oldP=next(x for x in read(E66/'inputs'/ds/'fit.json')['methods'] if x['model_name']=='baseline');P=np.fromfile(oldP['W'],np.float32).reshape(-1,d);ids=np.fromfile(oldP['mapping'],np.int32);lookup={int(h):j for j,h in enumerate(ids)}
 for h,slots in groups.items():
  assert len(slots) in [1,3] and original[slots[0]]%3==0
  assert w[slots[0]].tobytes()==P[lookup[h]].tobytes()
  if len(slots)==3:assert np.array_equal(original[slots],np.arange(original[slots[0]],original[slots[0]]+3))
 q=np.fromfile(nc['queries_file'],np.float32).reshape(20000,d);qprefix=np.fromfile(cfg['queries_file'],np.float32,count=20000*d).reshape(20000,d);assert q.tobytes()==qprefix.tobytes()
 gt=np.fromfile(nc['gt_file'],np.int64).reshape(20000,100);rows=np.fromfile(nc['row_ids'],np.int64);assert np.array_equal(rows,np.arange(10000,30000))
 p=raw(E66/'results'/ds/'fit/baseline_L128');b=dict(np.load(E86/'results'/ds/'fit/compact_baseline.npz'))
 for a in [p,b]:
  hh,mask=score(a['ids'],gt);assert np.array_equal(hh,a['hits']) and np.array_equal(mask,a['mask'])
 events=[];votes={};supports={};delta=p['hits'].astype(int)-b['hits'].astype(int)
 for i in np.flatnonzero(delta>0):
  selected={};seen=[]
  for slot in b['slots'][i]:
   h=int(mp[slot])
   if h not in selected:selected[h]=int(slot);seen.append(h)
  assert sorted(seen[:3])==b['entries'][i].tolist()
  for h in seen[:3]:
   slots=groups[h];slot=selected[h]
   if h in p['entries'][i] or len(slots)!=3 or slot==slots[0]:continue
   lift=float(np.dot(q[i].astype(float),w[slot].astype(float)-w[slots[0]].astype(float)))
   event=dict(fit_index=int(i),namespace='router_train',source_row=int(rows[i]),hub=h,parent_slot=int(slots[0]),winner_slot=slot,P_hits=int(p['hits'][i]),compact_hits=int(b['hits'][i]),weight=int(delta[i]),score_lift=lift,near_parent=bool(abs(lift)<=1e-5*max(1,float(np.linalg.norm(q[i].astype(float))))),P_entries=' '.join(map(str,p['entries'][i])),compact_entries=' '.join(map(str,b['entries'][i])))
   events.append(event);votes[h]=votes.get(h,0)+int(delta[i]);supports.setdefault(h,set()).add(int(i))
 candidates=[dict(hub=h,parent_slot=int(groups[h][0]),child_slots=list(map(int,groups[h][1:])),votes=votes[h],support=len(supports[h])) for h in sorted(votes,key=lambda h:(-votes[h],h)) if len(supports[h])>=2][:32]
 assert len({x['hub'] for x in candidates})==len(candidates)
 with (inp/'proposal_events.csv').open('x',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(events[0]));writer.writeheader();writer.writerows(events)
 dump(inp/'candidates.json',candidates);dump(inp/'eligible_groups.json',[dict(hub=h,parent_slot=int(s[0]),child_slots=list(map(int,s[1:]))) for h,s in groups.items() if len(s)==3])
 dump(inp/'routes.json',cfg);dump(inp/'native_training.json',nc)
 dump(inp/'proposals.json',dict(P_better_queries=int((delta>0).sum()),events=len(events),proposed_hubs=len(votes),candidates=len(candidates),selected_votes=sum(x['votes'] for x in candidates),action='two child rows copied from their original parent, fixed original topology',proposal_is_not_causal_credit=True))
 for source in [nc,cfg]:paths += [Path(source[k]) for k in ['queries_file','row_ids']]
 paths += [Path(nc['gt_file']),Path(m['W']),Path(m['mapping']),Path(m['tie_ids']),Path(m['graph_file']),Path(oldP['W']),Path(oldP['mapping']),E73/'models'/ds/'original_slots.i32',E86/'results'/ds/'fit/compact_baseline.npz']
 for name in ['baseline','mode3P']:paths += [E66/'results'/ds/'fit'/(name+'_L128')/f for f,dt,ww in FIELDS.values()]
for x in read(E73/'reviews/base_graph_identity.json')['sources']:
 st=Path(x['path']).stat();assert (st.st_size,st.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
shutil.copy2(E73/'reviews/base_graph_identity.json',O/'reviews/base_graph_identity.json')
dump(O/'config.locked.json',dict(training_NSG_cap=65536,per_dataset_training_NSG_cap=32768,training_HNSW_cap=2801024,aux_NSG=161920,aux_HNSW=161600,NSG_hard_cap=227456,HNSW_hard_cap=2962624,latest_training_launch=1789296000,latest_aux_launch=1789296900,query_hard_stop=1789297500,output_cap_MiB=128,free_min_GiB=6.45,threads=1,CPU=15))
args=read(E86/'bin/provenance.json')['argv'];args=[str(O/'src/routes.cpp') if x==str(E86/'src/routes.cpp') else str(O/'bin/routes.so') if x==str(E86/'bin/routes.so') else x for x in args]
paths += [Path(x) for x in args if Path(x).is_file()]+list((O/'inputs').rglob('*'))+[O/'config.locked.json',C/'stage10_exact_triple_utility_v1/bin/inject.so',E73/'bin/evaluate']
freeze(O/'reviews/precompile_freeze.json',[p for p in paths if p.is_file()]);compile_start=time.monotonic()
with (O/'logs/compile.log').open('x') as f:proc=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=180)
dump(O/'bin/provenance.json',dict(argv=args,returncode=proc.returncode,seconds=time.monotonic()-compile_start,binary=identity(O/'bin/routes.so') if proc.returncode==0 else None))
assert proc.returncode==0
dump(O/'logs/training_jobs.json',[]);dump(O/'logs/jobs.json',[])
dump(O/'results/preparation_cost.json',dict(operation_seconds=time.monotonic()-tick,new_NSG=0,new_HNSW=0,ordinary_builds=0,compile_seconds=read(O/'bin/provenance.json')['seconds']))
print('E89_PREPARED',[(ds,read(O/'inputs'/ds/'proposals.json')) for ds in DS],flush=True)
