from verify_candidates import *
import csv
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
tick=time.monotonic();points=[];paired=[];failures=[];rankstats=[];gates={};scored=recovered=candidate_rows=equal_exact=0
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(c['row_ids'],np.int64);rank=dict(np.load(E68/'results'/ds/'aux.npz'));assert np.array_equal(rows,rank['source_rows']);raw={}
 for m in c['methods']:
  name=m['model_name'];p=O/'results'/ds/'aux'/m['name'];a=load_raw(p,7952);raw[name]=a
  match=np.any(a['ids'][:,:,None]==gt[:,None,:10],axis=1);mask=(match*(1<<np.arange(10))).sum(1)
  assert np.array_equal(match.sum(1),a['hits']) and np.array_equal(mask,a['mask'])
  # Second independent scalar set scoring, legitimate ID and duplicate-output checks.
  for ids,g,h in zip(a['ids'],gt,a['hits']):
   assert len(set(ids.tolist()))==10 and np.all((ids>=0)&(ids<c['base_count'])) and len(set(ids.tolist())&set(g[:10].tolist()))==h
  scored+=7952
  if name!='compact10':
   base={'baseline10':'baseline','mode10':'mode3P'}[name];old=old_raw(ds,base)
   for k in FIELDS:assert a[k].tobytes()==old[k].tobytes(),(name,k)
   assert a['route_ndc'].tobytes()==(E66/'results'/ds/'aux'/(base+'_L128')/'route_ndc.u32').read_bytes();recovered+=7952
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/m['name']/fn).read_bytes()
  candidate_rows+=verify_candidates(c,m,p,a,7952)
  key='exact_P_hubs' if name=='baseline10' else 'exact_mode_hubs';agree=np.sum(np.any(a['entries'][:,:,None]==rank[key][:,None,:],axis=2),axis=1)
  rankstats.append(dict(dataset=ds,model=name,exact_agreement=float((agree==3).mean()),mean_overlap=float(agree.mean()/3)))
  er=dict(np.load(C/'stage10_exact_triple_utility_v1/results'/ds/('exact_P.npz' if name=='baseline10' else 'exact_mode.npz')));ix=np.flatnonzero(np.all(er['entries']==a['entries'],axis=1));equal_exact+=len(ix)
  for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==er[k][ix].tobytes()
 # Reconstruct full source bank from kept rows independently, including source real IDs.
 m=next(x for x in c['methods'] if x['model_name']=='compact10');folder=O/'models'/ds;meta=read(folder/'manifest.json');src=meta['source'];keep=np.fromfile(folder/'original_slots.i32',np.int32);o2n=np.fromfile(folder/'old_to_compact.i32',np.int32)
 W=np.fromfile(m['W'],np.float32).reshape(-1,c['dim']);oldW=np.fromfile(src['W'],np.float32).reshape(-1,c['dim']);ids=np.fromfile(m['mapping'],np.int32);oldids=np.fromfile(src['mapping'],np.int32)
 assert W.tobytes()==oldW[keep].tobytes() and W[o2n].tobytes()==oldW.tobytes() and ids[o2n].tobytes()==oldids.tobytes()
 assert all(1<=x<=3 for x in np.unique(ids,return_counts=True)[1]);local={}
 for split,sl in [('all',slice(None)),('first_half',slice(0,3976)),('second_half',slice(3976,None))]:
  for name,a in raw.items():
   h=a['hits'][sl];points.append(dict(dataset=ds,model=name,split=split,n=len(h),total_hits=int(h.sum()),recall=float(h.mean()/10),failures=int((h==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for ref in ['baseline10','mode10']:
   a=raw['compact10'];b=raw[ref];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   gained=sum((int(x)&~int(y)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));lost=sum((int(y)&~int(x)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));assert gained-lost==int(delta.sum())
   r=dict(dataset=ds,candidate='compact10',reference=ref,split=split,n=len(ah),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=gained,member_lost=lost,route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100));paired.append(r);local[ref,split]=r
   if split=='all':
    print(r,flush=True)
    for i in np.flatnonzero(res|new):failures.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),reference=ref,transition='rescued' if res[i] else 'new_failure',reference_hits=int(bh[i]),candidate_hits=int(ah[i]),reference_entries=' '.join(map(str,b['entries'][i])),candidate_entries=' '.join(map(str,a['entries'][i]))))
 rules={}
 for ref in ['baseline10','mode10']:
  r=local[ref,'all'];rules[ref+'_hits']=r['net_hits']>0 if ref=='baseline10' else r['net_hits']>=0;rules[ref+'_halves']=all(local[ref,s]['net_hits']>=0 for s in ['first_half','second_half']);rules[ref+'_failures']=r['failure_change']<=0
 gates[ds]=dict(passed=all(rules.values()),rules=rules)
for name,data in [('points',points),('paired',paired),('failures',failures),('ranking',rankstats)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'results/gate.json',dict(status='COMPLETE_COMPACT_DEVELOPMENT',datasets=gates,wall_measurement_authorized_by_protocol=True,selection_feedback='historical auxiliary training',old_gates_unchanged=True,not_performance_GO=True))
cost=dict(NSG=sum(j['actual_NSG'] for j in jobs),HNSW=96960,builds=2,source_graph_loads=12,count_graph_loads=12,native_job_seconds=sum(j['seconds'] for j in jobs),compile_seconds=read(O/'bin/provenance.json')['seconds'],compaction_seconds=sum(x['preparation_seconds'] for x in read(O/'results/compaction.json')['datasets']),micro_graph_build_seconds=sum(read(O/'models'/ds/'build.json')['build_seconds'] for ds in DS),analysis_seconds=time.monotonic()-tick,training_updates=0,new_GT=0,route_graph_wall=None,reason='no formal wall in E73; E74 will measure full online cost')
dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=scored+768,independent_scalar_rows=scored,old_recovered_rows=recovered,preflight_prefix_rows=768,candidate_rows=candidate_rows+512,original_kernel_parity_rows=192,exact_same_triple_return_rows=equal_exact,graph_W_label_checked=True,complete_score_set_byte_invariance=True,actual_threads=[j['peak_threads'] for j in jobs]));check(O/'reviews/prequery_freeze.json');resources();dump(O/'state.json',dict(status='COMPLETE_COMPACT_MODE_DEVELOPMENT',NSG=97152,HNSW=96960,builds=2,day_goal_complete=False));print('E73_ANALYZE_PASS',gates)
