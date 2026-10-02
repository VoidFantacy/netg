from common import *
import csv,sys,ast
assert os.sched_getaffinity(0)=={8};resources();assert read(O/'results/deployment_complete.json')['status']=='PASS'
completion=read(O/'results/deployment_complete.json');sources=read(O/'results/final_sources.json')
def result_folder(ds,phase):return Path(sources[ds]['folder']) if phase=='validation' else O/'results'/f'{phase}_{ds}'
started=time.monotonic();points=[];timings=[];paired=[];queryrows=[];raw={};verified=[];selection=read(O/'results/cal_selection.json')['selection']
def load_point(folder,m,n):
 p=folder/m['name'];return dict(ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,10),distances=np.fromfile(p/'distances.f32',np.float32).reshape(n,10),entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3),route_ndc=np.fromfile(p/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(p/'graph_ndc.u32',np.uint32))
def bootstrap(delta):
 rng=np.random.default_rng(20260912);a=[]
 for _ in range(20):a.extend(delta[rng.integers(0,len(delta),size=(100,len(delta)))].mean(1))
 return np.percentile(a,[2.5,97.5]).tolist()
for ds in DS:
 for phase in ['fit_parity','cal','validation']:
  folder=result_folder(ds,phase);c=read(folder/'config.json');r=read(folder/'results.json');tc=read(folder/'thread_contract.json');n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)
  assert c['threads']==r['threads']==tc['process_threads']==tc['actual_openmp_threads']==1 and c['query_cpu']==15 and r['GT_opened_after_all_raw_search']
  assert np.fromfile(c['row_ids'],np.int64).tobytes()==np.fromfile(folder/'row_ids.i64',np.int64).tobytes()
  for m in r['methods']:
   a=load_point(folder,m,n);h=np.fromiter((len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(a['ids'],gt)),dtype=np.uint8,count=n)
   mask=np.array([sum(1<<j for j in range(10) if int(g[j]) in set(map(int,x))) for x,g in zip(a['ids'],gt)],np.uint16)
   assert h.tobytes()==np.fromfile(folder/m['name']/'hits.u8',np.uint8).tobytes() and mask.tobytes()==np.fromfile(folder/m['name']/'hitmask.u16',np.uint16).tobytes()
   assert abs(h.mean()/10-m['recall_at_10'])<1e-12 and int((h==0).sum())==m['failed_queries']
   assert np.isfinite(a['distances']).all() and ((a['ids']>=0)&(a['ids']<c['base_count'])).all()
   if m['family']!='nsg':assert all(len(set(map(int,x)))==3 for x in a['entries'])
   assert m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
   assert m['physical_graph_calls']==(7 if phase=='validation' else 2)*n+16
   for name,key in [('mean_route_ndc','route_ndc'),('mean_graph_ndc','graph_ndc')]:assert abs(m[name]-a[key].mean())<1e-10
   a.update(hits=h,mask=mask);raw[(ds,phase,m['model_name'],m['L'])]=a
   qq=np.array(m['qps_runs']) if phase=='validation' else np.array([])
   if phase=='validation':
    assert len(qq)==5 and np.max(np.abs(qq-n/np.array(m['end_to_end_seconds'])))<1e-10 and abs(float(np.median(qq))-m['qps'])<1e-10
    for j,(sec,qps) in enumerate(zip(m['end_to_end_seconds'],qq)):timings.append(dict(dataset=ds,model=m['model_name'],L=m['L'],repeat=j,seconds=sec,QPS=float(qps)))
   points.append(dict(dataset=ds,phase=phase,source_run='E55' if phase=='validation' and sources[ds]['reused_E55'] else 'E57',model=m['model_name'],L=m['L'],queries=n,recall_pct=float(h.mean()*10),failure_pct=float((h==0).mean()*100),failed_queries=int((h==0).sum()),
    QPS=float(np.median(qq)) if len(qq) else None,QPS_min=float(qq.min()) if len(qq) else None,QPS_max=float(qq.max()) if len(qq) else None,route_NDC=float(a['route_ndc'].mean()),graph_NDC=float(a['graph_ndc'].mean()),total_NDC=float(a['route_ndc'].mean()+a['graph_ndc'].mean())))
  verified.append(dict(dataset=ds,phase=phase,points=len(r['methods']),set_scored_rows=len(r['methods'])*n,original_kernel_rows=16*len(r['methods'])))
 # Original matched baseline calibration must still restore every field.
 old=E37/'results'/f'cal_{ds}'/'baseline_L128';b=raw[(ds,'cal','baseline',128)]
 for key,filename,dt in [('ids','ids.i32',np.int32),('distances','distances.f32',np.float32),('entries','entry_ids.i32',np.int32),('route_ndc','route_ndc.u32',np.uint32),('graph_ndc','graph_ndc.u32',np.uint32)]:assert b[key].tobytes()==np.fromfile(old/filename,dt).tobytes()
 # All 17 original calibration states restore E55, including counts and distances.
 for oldm in read(E55/'inputs/candidate_pool.json')[ds]:
  name=oldm['model_name'];prior=load_point(E55/'results'/f'cal_{ds}',dict(name=name+'_L128'),1024);now=raw[(ds,'cal',name,128)]
  for key in prior:assert prior[key].tobytes()==now[key].tobytes(),(ds,name,key)
 # Recompute selection independently from per-query set scores and frozen pool order.
 gt=np.fromfile(O/'inputs'/ds/'cal/gt.i64',np.int64).reshape(1024,100);scores=[]
 for rank,m in enumerate(read(O/'inputs/candidate_pool.json')[ds]):
  a=raw[(ds,'cal',m['model_name'],128)];dh=a['hits'].astype(int)-b['hits'];total=a['route_ndc'].astype(float)+a['graph_ndc'];den=b['route_ndc'].astype(float)+b['graph_ndc']
  u=dh-.1*((total-den)/den)-.1*((a['hits']==0).astype(int)-(b['hits']==0).astype(int))
  saved=next(x for x in read(O/'results'/ds/'cal_selection_details.json') if x['model']==m['model_name']);np.testing.assert_allclose(saved['mean_U'],u.mean(),atol=2e-15,rtol=0)
  assert saved['fixed_rank']==rank and saved['gain_hits']==int(np.maximum(dh,0).sum()) and saved['loss_hits']==int(np.maximum(-dh,0).sum());scores.append(saved)
 best=lambda a:max(a,key=lambda x:(x['mean_U'],-x['total_NDC'],-x['fixed_rank']))
 assert best(scores)==selection[ds]['best_all'] and best(scores[1:])==selection[ds]['best_new']
 pp=[p for p in points if p['dataset']==ds and p['phase']=='validation'];names=list(dict.fromkeys(p['model'] for p in pp));base_name='baseline_soft' if ds==DS[0] else 'gt10_hard'
 for name in names:
  graphs=[]
  for L in LS:
   a=raw[(ds,'validation',name,L)];assert a['entries'].tobytes()==raw[(ds,'validation',name,128)]['entries'].tobytes()
   if name!='nsg':graphs.append(sha(result_folder(ds,'validation')/f'{name}_L{L}.hnsw'))
  if graphs:assert len(set(graphs))==1
 for L in LS:
  a=raw[(ds,'validation','best_new',L)];ap=next(x for x in pp if x['model']=='best_new' and x['L']==L)
  for ref in [x for x in names if x!='best_new']:
   b=raw[(ds,'validation',ref,L)];bp=next(x for x in pp if x['model']==ref and x['L']==L);d=a['hits'].astype(int)-b['hits'];ci=bootstrap(d*10)
   rescue=int(((b['hits']==0)&(a['hits']>0)).sum());newfail=int(((b['hits']>0)&(a['hits']==0)).sum());assert rescue-newfail==bp['failed_queries']-ap['failed_queries']
   paired.append(dict(dataset=ds,L=L,model='best_new',reference=ref,delta_recall_pp=float(d.mean()*10),CI_low_pp=ci[0],CI_high_pp=ci[1],gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),helped_queries=int((d>0).sum()),harmed_queries=int((d<0).sum()),rescued_failures=rescue,new_failures=newfail,
    failure_delta_pp=ap['failure_pct']-bp['failure_pct'],QPS_change_pct=(ap['QPS']/bp['QPS']-1)*100,QPS_envelope_low_pct=(ap['QPS_min']/bp['QPS_max']-1)*100,QPS_envelope_high_pct=(ap['QPS_max']/bp['QPS_min']-1)*100))
  for name in names:
   aa=raw[(ds,'validation',name,L)];bb=raw[(ds,'validation',base_name,L)]
   for q in range(2000):queryrows.append(dict(dataset=ds,L=L,model=name,validation_local_row=q,hits=int(aa['hits'][q]),baseline_hits=int(bb['hits'][q]),route_NDC=int(aa['route_ndc'][q]),graph_NDC=int(aa['graph_ndc'][q])))
def frontier(pp):return sorted([p for p in pp if not any(q['recall_pct']>=p['recall_pct'] and q['QPS']>=p['QPS'] and (q['recall_pct']>p['recall_pct'] or q['QPS']>p['QPS']) for q in pp)],key=lambda x:x['recall_pct'])
frontiers=[]
for ds in DS:
 pp=[p for p in points if p['dataset']==ds and p['phase']=='validation'];new=frontier([p for p in pp if p['model']=='best_new'])
 for ref in sorted({p['model'] for p in pp}-{'best_new'}):
  base=frontier([p for p in pp if p['model']==ref])
  for bp in base[1:-1]:
   x=bp['recall_pct']
   if new[0]['recall_pct']<=x<=new[-1]['recall_pct']:
    q=float(np.exp(np.interp(x,[p['recall_pct'] for p in new],np.log([p['QPS'] for p in new]))));frontiers.append(dict(dataset=ds,reference=ref,recall_pct=x,reference_QPS=bp['QPS'],candidate_interpolated_QPS=q,change_pct=(q/bp['QPS']-1)*100,kind='descriptive common-domain log-QPS interpolation'))
def table(name,rows):
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for name,rr in [('all_points',points),('final_points',[p for p in points if p['phase']=='validation']),('paired_comparisons',paired),('timings',timings),('query_results',queryrows),('frontier_interpolation',frontiers)]:table(name,rr)
assert len(points)==121 and len(timings)==225 and sum(x['set_scored_rows'] for x in verified)==133776
dump(O/'results/analysis.json',dict(points=points,paired=paired,frontiers=frontiers,selection=selection));dump(O/'reviews/output_verification.json',dict(status='PASS',points=121,independent_set_scoring_rows=133776,available_original_kernel_parity_rows=1936,fit_bit_parity_rows=4864,old_baseline_cal_rows=2048,wall_repeats_available=225,new_wall_repeats=completion['new_wall_repeats'],new_NSG_calls=completion['NSG_calls'],final_sources=sources,full_five_L_entry_graph_consistency=True,independent_cal_selection=True,seconds=time.monotonic()-started,records=verified))
for name in ['prequery_freeze','upstream','protected','native_dependencies','selection_before_validation']:check(O/'reviews'/f'{name}.json')
jobs=read(O/'logs/jobs.json');assert len(jobs)==4+sum(not x['reused_E55'] for x in sources.values()) and all(x['status']=='COMPLETE' and x['actual']==x['reserved'] and x['peak_threads']==1 for x in jobs) and sum(x['actual'] for x in jobs)==completion['NSG_calls']
ordered=sorted(jobs,key=lambda x:x['started_at']);assert all(a['closed_at']<=b['started_at'] for a,b in zip(ordered,ordered[1:]))
for x in jobs:check(O/'reviews'/f'{x["name"]}_before.json')
dump(O/'reviews/contract_verification.json',dict(status='PASS',NSG_calls=completion['NSG_calls'],reserved_NSG=completion['NSG_calls'],serial_jobs=len(jobs),final_sources=sources,actual_threads=1,selection_frozen_before_validation=True,split_isolation=read(O/'reviews/split_isolation.json')['status'],heldout_access=False,optimizer_updates=0))
sys.path.insert(0,str(R/'entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
colors={'nsg':'#8b79a5','fast30k':'#318454','gt10_hard':'#c39a28','baseline_soft':'#333333','best_new':'#c7473f'}
labels={'nsg':'NSG','fast30k':'Fast30K','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft baseline','best_new':'Cal-selected candidate'}
def savefig(fig,name):
 fig.tight_layout()
 for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',dpi=180,bbox_inches='tight')
 plt.close(fig)
for name,xkey,xlabel in [('recall_qps','recall_pct','Recall@10 (%)'),('failure_qps','failure_pct','Zero-GT10-hit query rate (%)')]:
 fig,axes=plt.subplots(1,2,figsize=(12,4.8))
 for ax,ds,title in zip(axes,DS,['WebVid-2.5M','Yandex-IP 10M']):
  pp=[p for p in points if p['dataset']==ds and p['phase']=='validation']
  for model in dict.fromkeys(p['model'] for p in pp):
   a=sorted([p for p in pp if p['model']==model],key=lambda x:x['L']);q=np.array([p['QPS'] for p in a]);low=q-np.array([p['QPS_min'] for p in a]);high=np.array([p['QPS_max'] for p in a])-q
   ax.errorbar([p[xkey] for p in a],q,yerr=np.stack([low,high]),fmt='-o',capsize=2,markersize=4,color=colors[model],label=labels[model])
  ax.set(title=title,xlabel=xlabel,ylabel='QPS: median of 5 runs (range bars)');ax.grid(alpha=.2);ax.legend(fontsize=8)
 fig.suptitle('Historical validation2000 | Same machine, one thread, pure end-to-end wall');savefig(fig,name)
fig,axes=plt.subplots(3,2,figsize=(12,10))
for col,ds in enumerate(DS):
 pp=[p for p in points if p['dataset']==ds and p['phase']=='validation']
 for model in dict.fromkeys(p['model'] for p in pp):
  a=sorted([p for p in pp if p['model']==model],key=lambda x:x['L'])
  for row,(key,label) in enumerate([('recall_pct','Recall@10 (%)'),('QPS','QPS (median)'),('failure_pct','Zero-hit query rate (%)')]):
   axes[row,col].plot(LS,[p[key] for p in a],'-o',markersize=4,color=colors[model],label=labels[model]);axes[row,col].set(xlabel='NSG search L',ylabel=label);axes[row,col].grid(alpha=.2);axes[row,col].legend(fontsize=8)
 axes[0,col].set_title('WebVid-2.5M' if col==0 else 'Yandex-IP 10M')
fig.suptitle('All measured points; fixed cal-selected model for each dataset');savefig(fig,'three_metrics_by_L')
print('E57 OUTPUT AND CONTRACT VERIFICATION PASS',flush=True)
