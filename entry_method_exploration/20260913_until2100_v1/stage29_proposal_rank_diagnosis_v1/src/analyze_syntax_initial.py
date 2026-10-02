from pathlib import Path
import os,json,csv,hashlib,time
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent;E=C/'stage28_utility_proposals_v1';DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def identity(p):
 p=Path(p);s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=h.hexdigest())
def scores(ids,gt):
 mask=np.zeros(len(ids),np.uint16)
 for j in range(10):mask|=np.any(ids==gt[:,j,None],axis=1).astype(np.uint16)<<j
 return np.array([int(x).bit_count() for x in mask]),mask
def writecsv(p,rows):
 with Path(p).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert os.sched_getaffinity(0)=={15}
assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'])
paths=[O/'protocol.md',Path(__file__),E/'reviews/final_artifact_freeze.json'];configs={}
for ds in DS:
 cfg=read(E/'inputs'/ds/'native_training.json');route=read(E/'inputs'/ds/'routes.json');configs[ds]=(cfg,route)
 paths += [E/'inputs'/ds/f for f in ['native_training.json','routes.json','proposals.npz','candidates.json']]
 paths += [Path(cfg[k]) for k in ['queries_file','gt_file','row_ids']]+[Path(route['method'][k]) for k in ['W','mapping','tie_ids']]
 paths += [p for p in (E/'results'/ds/'fit').glob('*.npz') if p.name=='compact_baseline.npz' or (p.name.startswith('edge_') and not p.name.endswith('_new.npz'))]+[E/'results'/ds/'fit/edge_statistics.json']
assert not (O/'reviews/preanalysis_freeze.json').exists()
dump(O/'reviews/preanalysis_freeze.json',dict(epoch=time.time(),files=[identity(p) for p in sorted(set(paths))]))
t=time.perf_counter();summaries=[];all_events=[];all_edges=[];score_rows=0
for ds in DS:
 cfg,route=configs[ds];m=route['method'];d=route['dim'];q=np.fromfile(cfg['queries_file'],np.float32).reshape(20000,d);gt=np.fromfile(cfg['gt_file'],np.int64).reshape(20000,100)
 W=np.fromfile(m['W'],np.float32).reshape(-1,d).astype(float);mapping=np.fromfile(m['mapping'],np.int32);tie=np.fromfile(m['tie_ids'],np.int32)
 b=dict(np.load(E/'results'/ds/'fit/compact_baseline.npz'));p=dict(np.load(E/'inputs'/ds/'proposals.npz'));cs=read(E/'inputs'/ds/'candidates.json');stats=read(E/'results'/ds/'fit/edge_statistics.json')
 h,mask=scores(b['ids'],gt);assert np.array_equal(h,b['hits']) and np.array_equal(mask,b['mask']);score_rows+=20000
 candidates={(x['slot'],x['shortcut_added'][0]):j for j,x in enumerate(cs)};responses={}
 for j,x in enumerate(cs):
  a=dict(np.load(E/'results'/ds/'fit'/('edge_%03d.npz'%j)));h,mask=scores(a['ids'],gt[a['rows']]);assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask']);score_rows+=len(h)
  support=set(int(e[0]) for e in p['events'] if (int(e[1]),int(e[2]))==(x['slot'],x['shortcut_added'][0]));assert len(support)==x['query_support']
  delta=a['hits'].astype(int)-b['hits'][a['rows']].astype(int);inside=np.array([int(i) in support for i in a['rows']],bool)
  assert len(a['rows'])==stats[j]['changed_triples'] and int(delta.sum())==stats[j]['net_hits']
  assert np.all(np.any(a['entries']!=b['entries'][a['rows']],axis=1))
  rec=dict(dataset=ds,candidate=j,source=x['slot'],target=x['shortcut_added'][0],support_queries=len(support),accepted=stats[j]['accepted'],changed_triples=len(a['rows']),net_hits=int(delta.sum()),support_net_hits=int(delta[inside].sum()),outside_support_net_hits=int(delta[~inside].sum()),support_gain_query_events=int(np.count_nonzero(delta[inside]>0)),outside_gain_query_events=int(np.count_nonzero(delta[~inside]>0)),support_harm_query_events=int(np.count_nonzero(delta[inside]<0)),outside_harm_query_events=int(np.count_nonzero(delta[~inside]<0)))
  all_edges.append(rec);responses[j]=(a,{int(v):k for k,v in enumerate(a['rows'])},{int(v):k for k,v in enumerate(a['route_changed_rows'])})
 for ei,(row,s,target,weight,ph,ch) in enumerate(p['events']):
  row,s,target,weight,ph,ch=map(int,(row,s,target,weight,ph,ch));assert ph-ch==weight>0 and target>=0
  slots=list(map(int,b['slots'][row]));qq=q[row].astype(float);unique=list(dict.fromkeys(slots+[target]));values={j:float(np.dot(W[j],qq)) for j in unique};rank=sorted(unique,key=lambda j:(-values[j],int(tie[j]),j));rank2=list(np.asarray(unique)[np.lexsort((np.asarray(unique),tie[unique],-np.array([values[j] for j in unique]))]);assert rank==rank2
  hs=[]
  for j in rank:
   if int(mapping[j]) not in hs:hs.append(int(mapping[j]))
  old_hubs=[];boundary=None
  for j in slots:
   if int(mapping[j]) not in old_hubs:
    old_hubs.append(int(mapping[j]))
    if len(old_hubs)==3:boundary=j;break
  assert boundary is not None and int(mapping[target]) not in b['entries'][row]
  gap=values[target]-values[boundary];eps=1e-5*max(1,float(np.linalg.norm(qq)));candidate=candidates.get((s,target));measured=candidate is not None
  rec=dict(dataset=ds,event=ei,fit_local_row=row,source_row=int(b['source_rows'][row]),source=s,target=target,target_hub=int(mapping[target]),proposal_weight=weight,P_hits=ph,compact_hits=ch,measured_candidate=candidate if measured else '',accepted_edge=bool(stats[candidate]['accepted']) if measured else '',target_already_in_seven=target in slots,fixed_set_target_hub_top3=int(mapping[target]) in hs[:3],target_score=values[target],third_hub_slot=boundary,third_hub_score=values[boundary],score_gap=gap,near_boundary=abs(gap)<=eps,actual_target_returned='',actual_target_hub_selected='',actual_triple_changed='',actual_net_hits='')
  if measured:
   a,ix,rx=responses[candidate];k=ix.get(row);rk=rx.get(row);newslots=slots if rk is None else a['slots'][rk];newentries=b['entries'][row] if k is None else a['entries'][k];dh=0 if k is None else int(a['hits'][k])-int(b['hits'][row])
   rec.update(actual_target_returned=target in newslots,actual_target_hub_selected=int(mapping[target]) in newentries,actual_triple_changed=k is not None,actual_net_hits=dh)
  all_events.append(rec)
 ev=[r for r in all_events if r['dataset']==ds];me=[r for r in ev if r['measured_candidate']!=''];edges=[r for r in all_edges if r['dataset']==ds]
 summaries.append(dict(dataset=ds,all_proposal_events=len(ev),measured_support_events=len(me),unmeasured_events=len(ev)-len(me),measured_unique_queries=len({r['fit_local_row'] for r in me}),target_already_in_seven=sum(r['target_already_in_seven'] for r in me),fixed_set_eligible=sum(r['fixed_set_target_hub_top3'] for r in me),near_boundary=sum(r['near_boundary'] for r in me),actual_target_returned=sum(r['actual_target_returned'] for r in me),actual_target_selected=sum(r['actual_target_hub_selected'] for r in me),actual_changed_triple=sum(r['actual_triple_changed'] for r in me),actual_support_gain_events=sum(r['actual_net_hits']>0 for r in me),actual_support_harm_events=sum(r['actual_net_hits']<0 for r in me),actual_support_net_hits=sum(r['actual_net_hits'] for r in me),all_fit_edge_net_hits=sum(r['net_hits'] for r in edges),outside_support_net_hits=sum(r['outside_support_net_hits'] for r in edges),outside_gain_query_edge_events=sum(r['outside_gain_query_events'] for r in edges),outside_harm_query_edge_events=sum(r['outside_harm_query_events'] for r in edges)))
writecsv(O/'results/events.csv',all_events);writecsv(O/'results/edges.csv',all_edges)
dump(O/'results/summary.json',dict(status='PASS',records=summaries,independently_scored_rows=score_rows,analysis_seconds=time.perf_counter()-t,NSG=0,HNSW=0,GT=0,fits=0,QPS=0,scope='Training descriptive diagnosis; events may share query and effects are independent edge interventions, never additive method gains. Unmeasured response cells blank.'))
dump(O/'state.json',dict(status='COMPLETE_CACHED_PROPOSAL_RANK_DIAGNOSIS',NSG=0,HNSW=0,GT=0,builds=0,fits=0,QPS=0,day_goal_complete=False))
print('E88_PASS',summaries)
