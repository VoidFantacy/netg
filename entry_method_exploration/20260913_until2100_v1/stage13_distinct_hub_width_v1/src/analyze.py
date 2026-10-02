from verify_candidates import *
import csv
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(x['status']=='COMPLETE' for x in jobs)
start=time.monotonic();points=[];paired=[];failures=[];rankstats=[];gates={};count=0;candidate_rows=0;recovered=0;equal_exact=0
comp=[('mode3PD10','baseline10'),('mode3PD10','mode3P10'),('mode3PD10','mode3P30'),('mode3PD10','duplicate3PD10'),('duplicate3PD10','duplicate3P10'),('duplicate3PD10','baseline10'),('baselineD10','baseline10'),('mode3P10','baseline10')]
pop=np.array([i.bit_count() for i in range(1024)],np.int16)
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');n=7952;gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);rows=np.fromfile(c['row_ids'],np.int64)
 ref=dict(np.load(E68/'results'/ds/'aux.npz'));assert np.array_equal(rows,ref['source_rows']);raw={}
 for m in c['methods']:
  name=m['model_name'];base=name.removesuffix('D10').removesuffix('10');p=O/'results'/ds/'aux'/m['name'];a=load_raw(p,n)
  match=np.any(a['ids'][:,:,None]==gt[:,None,:10],axis=1);h=match.sum(1);mask=(match*(1<<np.arange(10))).sum(1)
  assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask']);count+=n
  assert np.all(np.diff(a['entries'],axis=1)>0)
  if not m['distinct_hub_width'] or name=='baselineD10':
   old=old_raw(ds,base)
   for k in FIELDS:assert a[k].tobytes()==old[k].tobytes(),(name,k)
   assert a['route_ndc'].tobytes()==(E66/'results'/ds/'aux'/(base+'_L128')/'route_ndc.u32').read_bytes();recovered+=n
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/m['name']/fn).read_bytes()
  candidate_rows+=verify_candidates(c,m,p,a,n)
  exact=ref['exact_mode_hubs'] if base=='mode3P' else ref['exact_P_hubs'];agreement=np.sum(np.any(a['entries'][:,:,None]==exact[:,None,:],axis=2),axis=1)
  r=dict(dataset=ds,model=name,n=n,exact_three_agreement=float((agreement==3).mean()),mean_overlap=float(agreement.mean()/3),mean_candidate_slots=None,min_candidate_slots=None,max_candidate_slots=None)
  if m['distinct_hub_width']:
   sizes=np.fromfile(p/'distinct_size.u32',np.uint32);r.update(mean_candidate_slots=float(sizes.mean()),min_candidate_slots=int(sizes.min()),max_candidate_slots=int(sizes.max()))
  rankstats.append(r);raw[name]=a
  er=dict(np.load(C/'stage10_exact_triple_utility_v1/results'/ds/('exact_mode.npz' if base=='mode3P' else 'exact_P.npz')))
  ix=np.flatnonzero(np.all(a['entries']==er['entries'],axis=1));equal_exact+=len(ix)
  for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==er[k][ix].tobytes()
 old=C/'stage11_width_control_v1';oc=read(old/'inputs'/ds/'aux.json')
 for k in ['queries_file','gt_file','row_ids','index_path']:assert c[k]==oc[k]
 raw['mode3P30']=load_raw(old/'results'/ds/'aux/mode3P30_L128',n)
 local={}
 for split,sl in [('all',slice(0,n)),('first_half',slice(0,3976)),('second_half',slice(3976,n))]:
  for name,a in raw.items():points.append(dict(dataset=ds,model=name,split=split,n=sl.stop-sl.start,source='E70_quality_reference_only' if name=='mode3P30' else 'E72_current',total_hits=int(a['hits'][sl].sum()),recall=float(a['hits'][sl].mean()/10),failures=int((a['hits'][sl]==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for cand,reference in comp:
   a=raw[cand];b=raw[reference];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   r=dict(dataset=ds,candidate=cand,reference=reference,split=split,n=len(delta),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=int(pop[(a['mask'][sl]&~b['mask'][sl])&1023].sum()),member_lost=int(pop[(b['mask'][sl]&~a['mask'][sl])&1023].sum()),route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100))
   assert r['net_hits']==r['member_gained']-r['member_lost'];paired.append(r);local[(cand,reference,split)]=r
   if split=='all':
    for row in np.flatnonzero(res|new):failures.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[row]),candidate=cand,reference=reference,transition='rescued' if res[row] else 'new_failure',reference_hits=int(bh[row]),candidate_hits=int(ah[row]),reference_entries=' '.join(map(str,b['entries'][row])),candidate_entries=' '.join(map(str,a['entries'][row]))))
 rules={}
 for reference in ['baseline10','mode3P10','mode3P30']:
  a=local[('mode3PD10',reference,'all')];rules[reference+'_hits']=a['net_hits']>0 if reference=='baseline10' else a['net_hits']>=0
  rules[reference+'_halves']=all(local[('mode3PD10',reference,s)]['net_hits']>=0 for s in ['first_half','second_half']);rules[reference+'_failures']=a['failure_change']<=0
 rules['route_cheaper_than_mode30']=local[('mode3PD10','mode3P30','all')]['route_NDC_change_pct']<0
 gates[ds]=dict(passed=all(rules.values()),rules=rules)
 for reference in ['baseline10','mode3P10','mode3P30']:print(ds,reference,local[('mode3PD10',reference,'all')],flush=True)
for name,a in [('points',points),('paired',paired),('failures',failures),('ranking',rankstats)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
dump(O/'results/gate.json',dict(status='COMPLETE_DISTINCT_QUALITY_CONTROL',datasets=gates,full_development_wall_supported=any(x['passed'] for x in gates.values()),old_E66_E70_gates_unchanged=True,not_performance_GO=True))
dump(O/'results/cost.json',dict(NSG=sum(x['actual_NSG'] for x in jobs),HNSW=193920,builds=0,source_graph_loads=24,count_graph_loads=24,native_job_seconds=sum(x['seconds'] for x in jobs),compile_seconds=read(O/'bin/provenance.json')['seconds'],analysis_seconds=time.monotonic()-start,synthetic=read(O/'reviews/synthetic.json'),route_graph_wall=None,reason='not separately timed; no QPS diagnostic'))
dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=count+1536,full_aux_set_rows=count,full_old_and_singleton_recovered_rows=recovered,distinct_candidate_rows=candidate_rows+768,preflight_to_aux_rows=1536,original_kernel_parity_rows=384,E69_same_triple_return_rows=equal_exact,source_graphs_referenced=True,graph_copies=0,threads_actual=[j['peak_threads'] for j in jobs]))
check(O/'reviews/prequery_freeze.json');dump(O/'state.json',dict(status='COMPLETE_DISTINCT_HUB_CONTROL',NSG=194304,HNSW=193920,builds=0,day_goal_complete=False));resources()
