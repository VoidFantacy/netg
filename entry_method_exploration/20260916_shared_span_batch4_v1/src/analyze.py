import csv,datetime,hashlib,json,math,pathlib,statistics
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvout(p,rows):
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
assert read(D/'state.json')['status']=='MEASUREMENTS_COMPLETE'
assert read(D/'reviews/post_run_identity.json')['status']=='PASS'
c=read(D/'configs/webvid2_5m_light_v1.json');B=D/'results'/c['dataset'];done=read(B/'complete.json');assert done['search_calls']==1800000 and done['wall_rounds']==108 and done['actual_batch4_count']
g=np.fromfile(c['gt'],dtype='<i4');width=int(g[0]);gt=g.reshape(-1,width+1);assert width>=100 and gt.shape[0]==c['n'] and np.all(gt[:,0]==width);gt=gt[:,1:]
times=read(B/'timing_progress.json');assert len(times)==108
for x in times:assert x['cpu']==15 and x['threads']==1 and math.isclose(x['qps'],c['n']/x['seconds'],rel_tol=1e-12)
old=list(csv.DictReader((D.parent/'20260916_nsg_search_optimization_v1/results/metrics.csv').open()))
rows=[];raw=[]
for pt in c['points']:
 K,L=pt['K'],pt['L']
 for v in c['variants']:
  method,kind=v['method'],v['kernel'];key=f'{method}__{kind}_K{K}_L{L}';p=B/key;pd=read(p/'complete.json');assert pd['status']=='PASS' and pd['output_bits_and_ndc_verified']
  if kind=='span-batch4':assert pd['actual_batch4_forwarded']
  ids=np.fromfile(p/'ids.i32',dtype='<i4').reshape(c['n'],K);dist=np.fromfile(p/'distances.f32',dtype='<f4').reshape(c['n'],K)
  assert np.all((ids>=0)&(ids<2505000)) and np.isfinite(dist).all()
  if K>1:assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0) and np.all(np.diff(dist,axis=1)>=0)
  hits=np.array([np.intersect1d(a,b,assume_unique=True).size for a,b in zip(ids,gt[:,:K])],dtype=np.int32);recall=float(hits.mean()/K);hits.tofile(p/'hits.i32')
  ref=pathlib.Path(c['reference_e99'])/f'{method}__{"reference" if method=="HNSW" else "optimized"}_K{K}_L{L}'
  for name,size in [('ids.i32',c['n']*K*4),('distances.f32',c['n']*K*4),('entry_ids.i32',c['n']*3*4),('route_ndc.u64',c['n']*8),('graph_ndc.u64',c['n']*8)]:
   assert (p/name).stat().st_size==size and sha(p/name)==sha(ref/name),(key,name)
   raw.append(dict(file=str((p/name).relative_to(D)),sha256=sha(p/name),reference=str(ref/name)))
  o=next(x for x in old if x['dataset']==c['dataset'] and x['method']==method and x['kernel']!='legacy' and int(x['K'])==K and int(x['L'])==L);assert abs(recall-float(o['recall']))<1e-12
  t=sorted([x for x in times if (x['method'],x['kernel'],x['K'],x['L'])==(method,kind,K,L)],key=lambda x:x['repeat']);assert len(t)==3 and [x['seconds'] for x in t]==pd['seconds']
  qp=[x['qps'] for x in t];wall=[x['seconds'] for x in t];route=np.fromfile(p/'route_ndc.u64',dtype='<u8');graph=np.fromfile(p/'graph_ndc.u64',dtype='<u8');assert len(route)==len(graph)==c['n']
  rows.append(dict(method=method,kernel=kind,K=K,L=L,recall=recall,qps_mean=statistics.mean(qp),qps_min=min(qp),qps_max=max(qp),repeat_range_percent=100*(max(qp)-min(qp))/statistics.mean(qp),qps_from_mean_wall=c['n']/statistics.mean(wall),mean_ms=1000*statistics.mean(wall)/c['n'],route_ndc=float(route.mean()),graph_ndc=float(graph.mean()),total_ndc=float(route.mean()+graph.mean()),zero_hit_queries=int((hits==0).sum()),**{f'qps_round{i+1}':qp[i] for i in range(3)}))
assert len(rows)==36 and len(raw)==180
def get(m,k,K,L):return next(x for x in rows if (x['method'],x['kernel'],x['K'],x['L'])==(m,k,K,L))
speed=[];methods=[]
for pt in c['points']:
 K,L=pt['K'],pt['L'];nsg=get('NSG','span-batch4',K,L)
 for m in [x['name'] for x in c['methods'] if x['name']!='HNSW']:
  a,b=get(m,'span-batch4',K,L),get(m,'current',K,L)
  assert a['recall']==b['recall'] and a['total_ndc']==b['total_ndc']
  speed.append(dict(method=m,K=K,L=L,speedup_percent=100*(a['qps_mean']/b['qps_mean']-1),conservative_repeat_separation_percent=100*(a['qps_min']/b['qps_max']-1),paired_min_percent=100*(min(a[f'qps_round{i}']/b[f'qps_round{i}'] for i in [1,2,3])-1),paired_max_percent=100*(max(a[f'qps_round{i}']/b[f'qps_round{i}'] for i in [1,2,3])-1),identical_recall_and_ndc=True))
  if m!='NSG':methods.append(dict(method=m,baseline='NSG',shared_kernel='span-batch4',K=K,L=L,recall_delta_pp=100*(a['recall']-nsg['recall']),qps_delta_percent=100*(a['qps_mean']/nsg['qps_mean']-1),candidate_min_vs_baseline_max_percent=100*(a['qps_min']/nsg['qps_max']-1),comparison='Same fixed L; not equal-recall frontier'))
compat=[];details=[];calls=0
for ds in read(D/'results/completed_datasets.json')[1:]:
 name=ds['dataset'];cfg=read(D/'configs'/f'{name}.json');p=D/'results'/name;progress=read(p/'progress.json');assert len(progress)==16 and all(x['actual_batch4'] for x in progress)
 totals={k:sum(x['checks'][k]['different_elements'] for x in progress) for k in ['ids','distance_bits','entries','route_ndc','graph_ndc']};calls+=ds['search_calls']
 compat.append(dict(dataset=name,status=ds['status'],configurations=16,search_calls=ds['search_calls'],mismatched_configurations=ds['mismatched_configurations'],**{k+'_different_elements':v for k,v in totals.items()}))
 for x in progress:
  if x['status']!='PASS':details.append(x)
assert calls==496000
csvout(D/'results/metrics.csv',rows);csvout(D/'results/wall_rounds.csv',times);csvout(D/'results/speedup.csv',speed);csvout(D/'results/shared_kernel_comparison.csv',methods);csvout(D/'results/compatibility.csv',compat)
save(D/'results/summary.json',dict(metrics=rows,speedups=speed,shared_kernel_comparisons=methods,compatibility=compat,mismatch_details=details,cost=read(D/'results/completed_datasets.json'),layout=read(B/'layout.json')))
save(D/'reviews/raw_results.json',raw)
save(D/'reviews/results_audit.json',dict(status='PASS',reviewed_at=datetime.datetime.now().astimezone().isoformat(),main_configurations=36,plain_rounds=108,real_search_calls=2296000,raw_files_verified=180,independent_gt_scoring=True,actual_batch4_count=True,compatibility_configurations=64,compatibility_status='PASS' if not details else 'COMPLETE_WITH_MISMATCH',production_changed=False))
print('Analysis complete; compatibility mismatches:',len(details))
