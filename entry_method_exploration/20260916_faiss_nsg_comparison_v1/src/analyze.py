"""Read-only scoring and cost comparison; run after the benchmark exits."""
import pathlib,json,hashlib,csv,statistics,math,datetime
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent;B=D/'results/benchmark'
def read(p):return json.loads(p.read_text())
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def csvout(p,rows):
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
c=read(D/'config.json');done=read(B/'complete.json');assert done['status']=='PASS' and done['search_calls']==2000000 and done['wall_rounds']==120
assert read(D/'state.json')['status']=='MEASUREMENTS_COMPLETE';assert read(D/'reviews/post_run_identity.json')['status']=='PASS'
g=np.fromfile(c['gt'],dtype='<i4');width=int(g[0]);gt=g.reshape(-1,width+1);assert width>=100 and gt.shape[0]==c['n'] and np.all(gt[:,0]==width);gt=gt[:,1:]
timing=read(B/'timing_progress.json');assert len(timing)==120
for t in timing:assert t['cpu']==15 and t['threads']==1 and math.isclose(t['qps'],c['n']/t['seconds'],rel_tol=1e-12)
old=list(csv.DictReader((D.parent/'20260916_nsg_search_optimization_v1/results/metrics.csv').open()))
rows=[];raw=[]
for point in c['points']:
 K,L=point['K'],point['L']
 for v in c['variants']:
  p=B/f'{v}_K{K}_L{L}';pd=read(p/'complete.json');assert pd['status']=='PASS'
  ids=np.fromfile(p/'ids.i32',dtype='<i4').reshape(c['n'],K)
  assert np.all((ids>=0)&(ids<2505000))
  if K>1:assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
  hits=np.array([np.intersect1d(a,b,assume_unique=True).size for a,b in zip(ids,gt[:,:K])],dtype=np.int32);recall=float(hits.mean()/K)
  hits.tofile(p/'hits.i32')
  tr=sorted([x for x in timing if x['variant']==v and x['K']==K and x['L']==L],key=lambda x:x['repeat']);assert len(tr)==3 and [x['seconds'] for x in tr]==pd['seconds']
  qp=[x['qps'] for x in tr];wall=[x['seconds'] for x in tr];route=np.fromfile(p/'route_ndc.u64',dtype='<u8');graph=np.fromfile(p/'graph_ndc.u64',dtype='<u8');assert len(route)==len(graph)==c['n']
  for name,size in [('ids.i32',c['n']*K*4),('distances.f32',c['n']*K*4),('entry_ids.i32',c['n']*3*4),('route_ndc.u64',c['n']*8),('graph_ndc.u64',c['n']*8)]:
   file=p/name;assert file.stat().st_size==size;entry={'file':str(file.relative_to(D)),'sha256':sha(file),'bytes':size}
   if v!='Faiss-native':
    method='NSG' if v=='NSG-current' else 'HNSW' if v=='HNSW' else 'GT10-soft-t1'
    ref=pathlib.Path(c['reference_e99'])/f'{method}__{"reference" if method=="HNSW" else "optimized"}_K{K}_L{L}'/name
    assert sha(file)==sha(ref),str(file);entry['reference']=str(ref)
   raw.append(entry)
  if v!='Faiss-native':
   method='NSG' if v=='NSG-current' else 'HNSW' if v=='HNSW' else 'GT10-soft-t1'
   o=next(x for x in old if x['dataset']==c['dataset'] and x['method']==method and x['kernel']!='legacy' and int(x['K'])==K and int(x['L'])==L)
   assert abs(recall-float(o['recall']))<1e-12
  total=float(route.mean()+graph.mean());mean_ms=1000*statistics.mean(wall)/c['n']
  rows.append({'variant':v,'K':K,'L':L,'recall':recall,'qps_mean':statistics.mean(qp),'qps_min':min(qp),'qps_max':max(qp),'repeat_range_percent':100*(max(qp)-min(qp))/statistics.mean(qp),'qps_from_mean_wall':c['n']/statistics.mean(wall),'mean_ms':mean_ms,'route_ndc':float(route.mean()),'graph_ndc':float(graph.mean()),'total_ndc':total,'amortized_ns_per_ndc':1e6*mean_ms/total,'zero_hit_queries':int((hits==0).sum()),'qps_round1':qp[0],'qps_round2':qp[1],'qps_round3':qp[2]})
assert len(rows)==40 and len(raw)==200
pairs=[]
for x in rows:
 if not x['variant'].startswith('GT10-') or x['variant']=='GT10-current':continue
 for baseline in ['GT10-current','GT10-core']:
  if x['variant']==baseline:continue
  b=next(y for y in rows if y['variant']==baseline and (y['K'],y['L'])==(x['K'],x['L']))
  assert x['recall']==b['recall'] and x['total_ndc']==b['total_ndc']
  ratios=[x[f'qps_round{i}']/b[f'qps_round{i}'] for i in [1,2,3]]
  pairs.append({'variant':x['variant'],'baseline':baseline,'K':x['K'],'L':x['L'],'speedup_percent':100*(x['qps_mean']/b['qps_mean']-1),'paired_min_percent':100*(min(ratios)-1),'paired_max_percent':100*(max(ratios)-1),'conservative_repeat_separation_percent':100*(x['qps_min']/b['qps_max']-1),'identical_recall_and_ndc':True})
csvout(D/'results/metrics.csv',rows);csvout(D/'results/wall_rounds.csv',timing);csvout(D/'results/paired_speedup.csv',pairs);save(D/'reviews/raw_results.json',raw)
save(D/'results/summary.json',{'metrics':rows,'paired_speedups':pairs,'cost':done,'layout':read(B/'layout.json'),'scope':'Four fixed WebVid points; native Faiss search uses frozen project graph; no production replacement'})
save(D/'reviews/results_audit.json',{'status':'PASS','reviewed_at':datetime.datetime.now().astimezone().isoformat(),'points':40,'wall_rounds':120,'search_calls':2000000,'raw_files_verified':200,'e99_identical_files':180,'native_reference':'Native public API warm/plain/count bit parity plus range, uniqueness, order checks','recall_independently_recomputed':True,'same_graph_storage':True,'no_new_training_or_graph':True})
for row in rows:
 if row['K']==100 and row['L']==1250:print(json.dumps(row),flush=True)
