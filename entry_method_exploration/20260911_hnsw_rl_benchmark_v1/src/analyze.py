from common import *
import csv

def csvout(name,rows):
 if not rows:return
 with (O/'results'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def frontier(points):
 return sorted([p for p in points if not any(q['recall_pct']>=p['recall_pct'] and q['qps']>=p['qps'] and (q['recall_pct']>p['recall_pct'] or q['qps']>p['qps']) for q in points)],key=lambda p:p['recall_pct'])

assert read(O/'state.json')['status']=='EVALUATION_COMPLETE_ANALYSIS_PENDING'
assert not (O/'results/analysis.json').exists()
points=[];runs=[];paired=[];frontiers=[];interpolations=[];sources=set();regression=0;total=0
by_arrays={}
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');dest=O/'results'/ds;r=read(dest/'results.json');n=c['num_queries']
 gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(c['row_ids'],np.int64)
 assert np.array_equal(rows,np.fromfile(dest/'row_ids.i64',np.int64))
 th=read(dest/'thread_contract.json');assert th['process_threads']==th['actual_openmp_threads']==1 and th['cpu']==15
 assert r['physical_graph_calls']==c['real_call_cap'] and r['threads']==1 and r['GT_opened_after_all_raw_search'] and r['timing_repeats']==5
 old=read(E30/'results'/f'validation_{ds}'/'results.json');entry_reference={};graph_reference={}
 for m in r['methods']:
  method=m['model_name'];L=m['L'];p=dest/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,10)
  entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3);dist=np.fromfile(p/'distances.f32',np.float32).reshape(n,10)
  assert ((ids>=0)&(ids<c['base_count'])).all() and np.isfinite(dist).all() and (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
  found=(ids[:,:,None]==gt[:,None,:10]).any(1);hits=found.sum(1);masks=(found*(1<<np.arange(10))).sum(1)
  assert np.array_equal(hits,np.fromfile(p/'hits.u8',np.uint8)) and np.array_equal(masks,np.fromfile(p/'hitmask.u16',np.uint16))
  assert hits.sum()==m['total_hits'] and abs(hits.mean()/10-m['recall_at_10'])<1e-12
  assert int((hits==0).sum())==m['failed_queries'] and abs((hits==0).mean()-m['failure_rate'])<1e-12
  rn=np.fromfile(p/'route_ndc.u32',np.uint32);gn=np.fromfile(p/'graph_ndc.u32',np.uint32)
  assert rn.size==gn.size==n and abs(rn.mean()-m['mean_route_ndc'])<1e-10 and abs(gn.mean()-m['mean_graph_ndc'])<1e-10
  assert abs(rn.astype(float).mean()+gn.mean()-m['mean_total_ndc'])<1e-10
  if method=='nsg':assert (entries[:,0]==m['configuration']['fixed_entry']).all() and (entries[:,1:]==-1).all() and (rn==0).all()
  else:
   mapping=np.fromfile(m['configuration']['mapping'],np.int32);assert np.isin(entries,mapping).all() and (np.diff(np.sort(entries,axis=1),axis=1)>0).all()
   if method!='fast30k':assert (np.diff(entries,axis=1)>0).all()
   h=sha(dest/(m['name']+'.hnsw'));assert h==sha(m['configuration']['graph_file'])
   if method in graph_reference:assert h==graph_reference[method]
   graph_reference[method]=h
  if method in entry_reference:assert np.array_equal(entries,entry_reference[method])
  entry_reference[method]=entries
  q=np.array(m['qps_runs']);s=np.array(m['end_to_end_seconds']);assert q.size==s.size==5 and (s>0).all()
  assert np.allclose(q,n/s,rtol=1e-12) and m['qps']==np.median(q) and m['qps_min']==q.min() and m['qps_max']==q.max()
  assert m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
  if method!='rl':
   om=next(x for x in old['methods'] if x['model_name']==method and x['L']==L);op=E30/'results'/f'validation_{ds}'/om['name']
   for fn in ['ids.i32','distances.f32','entry_ids.i32','hits.u8','hitmask.u16','route_ndc.u32','graph_ndc.u32']:
    assert sha(op/fn)==sha(p/fn),(ds,method,L,fn);sources.add(op/fn)
   regression+=n
  point=dict(dataset=ds,method=method,label=LABELS[method],L=L,queries=n,recall_pct=float(hits.mean()*10),failed_queries=int((hits==0).sum()),failure_pct=float((hits==0).mean()*100),
   qps=float(m['qps']),qps_min=float(q.min()),qps_max=float(q.max()),route_ndc=float(rn.mean()),graph_ndc=float(gn.mean()),total_ndc=float(rn.mean()+gn.mean()),source=str(p))
  points.append(point);by_arrays[(ds,method,L)]=dict(hits=hits.astype(np.int16),entries=entries,qps=q,point=point)
  runs += [dict(dataset=ds,method=method,L=L,repeat=i+1,seconds=float(s[i]),qps=float(q[i])) for i in range(5)]
  total+=n
 rng=np.random.default_rng(20260915);bs=rng.integers(0,n,(2000,n))
 methods=[m['model_name'] for m in c['methods'] if m['L']==64]
 for L in LS:
  a=by_arrays[(ds,'rl',L)];ah=a['hits'];af=ah==0
  for method in methods:
   if method=='rl':continue
   b=by_arrays[(ds,method,L)];bh=b['hits'];bf=bh==0;delta=ah-bh;df=af.astype(np.int16)-bf
   rci=np.quantile(delta[bs].mean(1)*10,[.025,.975]);fci=np.quantile(df[bs].mean(1)*100,[.025,.975])
   speed=(a['qps']/b['qps']-1)*100;rescued=int((bf&~af).sum());new=int((~bf&af).sum())
   assert rescued-new==int(bf.sum()-af.sum())
   paired.append(dict(dataset=ds,baseline=method,L=L,recall_delta_pp=float(delta.mean()*10),recall_ci_low_pp=float(rci[0]),recall_ci_high_pp=float(rci[1]),
    qps_change_pct=float((a['point']['qps']/b['point']['qps']-1)*100),qps_paired_run_min_pct=float(speed.min()),qps_paired_run_max_pct=float(speed.max()),
    failure_delta_pp=float(df.mean()*100),failure_ci_low_pp=float(fci[0]),failure_ci_high_pp=float(fci[1]),
    baseline_failed=int(bf.sum()),rl_failed=int(af.sum()),rescued=rescued,newly_failed=new,still_failed=int((bf&af).sum()),
    gained_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),unchanged_queries=int((delta==0).sum()),
    route_ndc_change_pct=None if b['point']['route_ndc']==0 else float((a['point']['route_ndc']/b['point']['route_ndc']-1)*100),
    graph_ndc_change_pct=float((a['point']['graph_ndc']/b['point']['graph_ndc']-1)*100),total_ndc_change_pct=float((a['point']['total_ndc']/b['point']['total_ndc']-1)*100)))
 f_by={method:frontier([p for p in points if p['dataset']==ds and p['method']==method]) for method in methods}
 for method,f in f_by.items():
  frontiers.extend(dict(dataset=ds,method=method,L=p['L'],recall_pct=p['recall_pct'],qps=p['qps']) for p in f)
 for method in methods:
  if method=='rl':continue
  fa,fb=f_by['rl'],f_by[method];low=max(fa[0]['recall_pct'],fb[0]['recall_pct']);high=min(fa[-1]['recall_pct'],fb[-1]['recall_pct']);assert high>low
  def interp(f,method,x,rep=None):
   xs=[p['recall_pct'] for p in f];ys=[p['qps'] if rep is None else by_arrays[(ds,method,p['L'])]['qps'][rep] for p in f]
   return float(np.exp(np.interp(x,xs,np.log(ys))))
  for fraction in [.25,.5,.75]:
   target=low+fraction*(high-low);qa,qb=interp(fa,'rl',target),interp(fb,method,target)
   rr=[(interp(fa,'rl',target,i)/interp(fb,method,target,i)-1)*100 for i in range(5)]
   interpolations.append(dict(dataset=ds,baseline=method,overlap_low_recall_pct=low,overlap_high_recall_pct=high,overlap_fraction=fraction,
    target_recall_pct=target,rl_interpolated_qps=qa,baseline_interpolated_qps=qb,qps_change_pct=(qa/qb-1)*100,paired_run_min_pct=min(rr),paired_run_max_pct=max(rr),
    kind='descriptive log-QPS interpolation within measured nondominated overlap; not a new measurement'))
for name,data in [('points.csv',points),('qps_runs.csv',runs),('paired_changes.csv',paired),('frontier_points.csv',frontiers),('same_recall_interpolation.csv',interpolations)]:csvout(name,data)
dump(O/'results/analysis.json',dict(points=points,qps_runs=runs,paired=paired,frontiers=frontiers,same_recall_interpolation=interpolations))
freeze(O/'reviews/regression_sources.json',sources)
dump(O/'reviews/output_verification.json',dict(status='PASS',points=len(points),all_GT_rescored_query_outputs=total,old_baseline_bit_regression_outputs=regression,
 five_L_same_graph_and_entries=True,all_five_plain_walls_count_original_kernel_parity=True,failure_definition='hits == 0',paired_failure_identity=True,threads=1))
dump(O/'state.json',dict(status='ANALYSIS_COMPLETE_PLOTS_PENDING',points=45,wall_measurements=225,actual_NSG_calls=630720,optimizer_updates=0,heldout_access=False))
print('ANALYSIS_PASS',total,regression,flush=True)
for row in paired:
 if row['L']==128:print(json.dumps(row),flush=True)
