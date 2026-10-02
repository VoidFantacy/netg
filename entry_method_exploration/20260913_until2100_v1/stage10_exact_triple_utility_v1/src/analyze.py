from common import *
import csv
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(j['status']=='COMPLETE' for j in jobs)
started=time.monotonic();points=[];paired=[];failures=[];gates={};verified=0
pop=np.array([i.bit_count() for i in range(1024)],np.int16)
def score(ids,gt):
 h=np.empty(len(ids),np.uint8);m=np.empty(len(ids),np.uint16)
 for i,(r,g) in enumerate(zip(ids,gt)):
  assert len(set(map(int,r)))==10
  found=set(map(int,r));mask=sum(1<<j for j,v in enumerate(g[:10]) if int(v) in found)
  h[i]=len(found&set(map(int,g[:10])));m[i]=mask;assert h[i]==int(mask).bit_count()
 return h,m
comparisons=[('exact_P','baseline'),('exact_mode','exact_P'),('exact_mode','baseline'),('exact_mode','mode3P'),('exact_mode','duplicate3P')]
for ds in DS:
 cfg=read(O/'inputs'/ds/'native.json');pro=read(O/'inputs'/ds/'provenance.json');gt=np.fromfile(pro['gt_file'],np.int64).reshape(7952,100)
 rt=dict(np.load(O/'inputs'/ds/'routes.npz'));raw={m:old_raw(ds,m) for m in MODELS};patch=dict(np.load(O/'results'/ds/'missing.npz'))
 base_replay=dict(np.load(O/'results'/ds/'baseline_replay.npz'));same(raw['baseline'],base_replay)
 for i,name in enumerate(['exact_P','exact_mode']):
  a={k:np.empty_like(raw['baseline'][k]) for k in ['ids','distances','graph_ndc']};a['entries']=rt['exact_entries'][i]
  for row in range(7952):
   mi=int(rt['source_method'][i,row]);j=int(rt['source_index'][i,row]);src=patch if mi==3 else raw[MODELS[mi]]
   if mi==3:assert int(patch['rows'][j])==row
   else:assert j==row
   assert np.array_equal(a['entries'][row],src['entries'][j])
   for k in ['ids','distances','graph_ndc']:a[k][row]=src[k][j]
  a['hits'],a['mask']=score(a['ids'],gt);verified+=7952
  save(O/'results'/ds/(name+'.npz'),source_rows=rt['source_rows'],source_method=rt['source_method'][i],source_index=rt['source_index'][i],**a);raw[name]=a
 for m in MODELS:
  h,mask=score(raw[m]['ids'],gt);assert np.array_equal(h,raw[m]['hits']) and np.array_equal(mask,raw[m]['mask']);verified+=7952
 for label in ['baseline_replay','missing']:
  a=dict(np.load(O/'results'/ds/(label+'.npz')));ref=dict(np.load(O/'results'/ds/(label+'_reference.npz')))
  same(ref,{k:a[k][:16] for k in ['ids','distances','graph_ndc']})
 local={}
 for split,sl in [('all',slice(0,7952)),('first_half',slice(0,3976)),('second_half',slice(3976,7952))]:
  n=sl.stop-sl.start
  for name,a in raw.items():
   points.append(dict(dataset=ds,model=name,split=split,n=n,total_hits=int(a['hits'][sl].sum()),recall=float(a['hits'][sl].mean()/10),failures=int((a['hits'][sl]==0).sum()),failure_rate=float((a['hits'][sl]==0).mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),QPS=None))
  for candidate,reference in comparisons:
   a=raw[candidate];b=raw[reference];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh
   mg=pop[(a['mask'][sl]&(~b['mask'][sl]))&1023];ml=pop[(b['mask'][sl]&(~a['mask'][sl]))&1023]
   rescued=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   rec=dict(dataset=ds,candidate=candidate,reference=reference,split=split,n=n,net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=int(mg.sum()),member_lost=int(ml.sum()),rescued=int(rescued.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-rescued.sum()),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100))
   assert rec['net_hits']==rec['member_gained']-rec['member_lost']==rec['positive_query_hits']-rec['negative_query_hits']
   paired.append(rec);local[(candidate,reference,split)]=rec
   if split=='all':
    for row in np.flatnonzero(rescued|new):
     failures.append(dict(dataset=ds,namespace=pro['namespace'],source_row=int(rt['source_rows'][row]),candidate=candidate,reference=reference,transition='rescued' if rescued[row] else 'new_failure',reference_hits=int(bh[row]),candidate_hits=int(ah[row]),reference_entries=' '.join(map(str,b['entries'][row])),candidate_entries=' '.join(map(str,a['entries'][row])),reference_ids=' '.join(map(str,b['ids'][row])),candidate_ids=' '.join(map(str,a['ids'][row])),gt10=' '.join(map(str,gt[row,:10]))))
 rules={}
 for reference in ['exact_P','baseline']:
  p=local[('exact_mode',reference,'all')]
  rules[reference+'_positive']=p['net_hits']>0
  rules[reference+'_halves']=all(local[('exact_mode',reference,s)]['net_hits']>=0 for s in ['first_half','second_half'])
  rules[reference+'_failure']=p['failure_change']<=0
  rules[reference+'_graph_cost']=p['graph_NDC_change_pct']<=1.0
 rules['mode_nonnegative']=local[('exact_mode','mode3P','all')]['net_hits']>=0
 gates[ds]=dict(passed=all(rules.values()),rules=rules,scope='historical auxiliary quality only; no QPS or utility oracle')
 for ref in ['exact_P','baseline','mode3P']:print(ds,ref,local[('exact_mode',ref,'all')],flush=True)
for name,data in [('points',points),('paired',paired),('failure_cases',failures)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'results/gate.json',dict(status='EXACT_TRIPLE_DIAGNOSIS_COMPLETE',datasets=gates,next_width_diagnosis_supported=any(x['passed'] for x in gates.values()),not_performance_GO=True))
cost=dict(NSG=sum(x['native']['NSG'] for x in jobs),HNSW=0,builds=0,logical_exact_outputs=31808,old_reused=28102,new_unique_keys=3535,new_logical_aliases=171,baseline_replay_NSG=31808,missing_plain_count_NSG=7070,reference_NSG=64,native_elapsed_seconds=sum(x['elapsed_seconds'] for x in jobs),load_seconds=sum(x['load_seconds'] for x in jobs),compile_seconds=read(O/'bin/build.json')['seconds'],analysis_seconds=time.monotonic()-started,QPS=None,QPS_reason='offline exact-entry injection and cache diagnostic, no full online router wall')
assert cost['NSG']==38942;dump(O/'results/cost.json',cost)
dump(O/'reviews/verification.json',dict(status='PASS',set_scored_outputs=verified,baseline_replay_rows=15904,original_kernel_parity_rows=64,cache_key_reconstruction_rows=31808,member_net_identities=30,actual_threads=[j['native']['actual_threads'] for j in jobs],invalid_batches=42,old_artifacts_unchanged=True))
dump(O/'state.json',dict(status='COMPLETE_EXACT_TRIPLE_UTILITY',NSG=38942,HNSW=0,builds=0,day_goal_complete=False))
