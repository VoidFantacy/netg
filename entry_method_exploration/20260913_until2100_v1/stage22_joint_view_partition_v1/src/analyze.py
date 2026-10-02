from verify_candidates import *
import csv,struct
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
E73=C/'stage14_compact_modes_v1';E80=C/'stage21_hub_conditioned_targets_v1';tick=time.monotonic();points=[];paired=[];failures=[];gates={};level_records=[];retention=[];scored=recovered=candidate_rows=equal_triples=0
def graph_levels(path):
 data=Path(path).read_bytes();head=struct.unpack_from('<6QiI3QdQ',data);off,mx,n,size,label,coord,level,entry,M,M0,m,mult,ef=head;cursor=96+n*size;levels={};external=[]
 for i in range(n):
  ext=struct.unpack_from('<Q',data,96+i*size+label)[0];external.append(ext);nb=struct.unpack_from('<I',data,cursor)[0];cursor+=4;assert nb%68==0;levels[ext]=nb//68;cursor+=nb
 assert cursor==len(data) and levels[external[entry]]==level
 return levels,external[entry],level
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(c['row_ids'],np.int64);raw={}
 for m in c['methods']:
  name=m['model_name'];p=O/'results'/ds/'aux'/m['name'];a=load_raw(p,7952);raw[name]=a
  match=np.any(a['ids'][:,:,None]==gt[:,None,:10],axis=1);mask=(match*(1<<np.arange(10))).sum(1)
  assert np.array_equal(match.sum(1),a['hits']) and np.array_equal(mask,a['mask'])
  for ids,g,h in zip(a['ids'],gt,a['hits']):assert len(set(ids.tolist()))==10 and np.all((ids>=0)&(ids<c['base_count'])) and len(set(ids.tolist())&set(g[:10].tolist()))==h
  scored+=7952
  if name in ['baseline10','compact10']:
   old=load_raw(E73/'results'/ds/'aux'/m['name'],7952)
   for k in a:assert a[k].tobytes()==old[k].tobytes(),(ds,name,k)
   recovered+=7952
  if name=='conditional10':
   old=load_raw(E80/'results'/ds/'aux'/'conditional10_L128',7952)
   for k in a:assert a[k].tobytes()==old[k].tobytes(),(ds,name,k)
   recovered+=7952
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/m['name']/fn).read_bytes()
  candidate_rows+=verify_candidates(c,m,p,a,7952)
 for ref in ['baseline10','compact10']:
  a,b=raw['joint10'],raw[ref];ix=np.flatnonzero(np.all(a['entries']==b['entries'],axis=1));equal_triples+=len(ix)
  for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==b[k][ix].tobytes()
 # Query net-hit gain retention and total-loss migration, not GT-member counts.
 old_delta=raw['compact10']['hits'].astype(int)-raw['baseline10']['hits'].astype(int);og=np.maximum(old_delta,0);ol=np.maximum(-old_delta,0)
 for candidate in ['joint10','conditional10']:
  new_delta=raw[candidate]['hits'].astype(int)-raw['baseline10']['hits'].astype(int);ng=np.maximum(new_delta,0);nl=np.maximum(-new_delta,0);retained=np.minimum(og,ng);forgone=og-retained;gain_added=np.maximum(ng-og,0);loss_avoided=np.maximum(ol-nl,0);loss_added=np.maximum(nl-ol,0)
  assert np.array_equal(old_delta-forgone+gain_added+loss_avoided-loss_added,new_delta)
  retention.append(dict(dataset=ds,candidate=candidate,old_gain=int(og.sum()),retained_old_gain=int(retained.sum()),forgone_old_gain=int(forgone.sum()),new_gain=int(gain_added.sum()),old_loss=int(ol.sum()),avoided_old_loss=int(loss_avoided.sum()),new_or_amplified_loss=int(loss_added.sum()),new_total_loss=int(nl.sum()),net_delta_vs_compact=int((new_delta-old_delta).sum())))
 local={}
 for split,sl in [('all',slice(None)),('first_half',slice(0,3976)),('second_half',slice(3976,None))]:
  for name,a in raw.items():
   h=a['hits'][sl];points.append(dict(dataset=ds,model=name,split=split,n=len(h),total_hits=int(h.sum()),recall=float(h.mean()/10),failures=int((h==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for candidate in ['joint10','conditional10']:
   for ref in ['baseline10','compact10']+(['conditional10'] if candidate=='joint10' else []):
    a,b=raw[candidate],raw[ref];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
    gained=sum((int(x)&~int(y)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));lost=sum((int(y)&~int(x)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));assert gained-lost==int(delta.sum())
    r=dict(dataset=ds,candidate=candidate,reference=ref,split=split,n=len(ah),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=gained,member_lost=lost,route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100));paired.append(r);local[candidate,ref,split]=r
    if split=='all':
     print(r,flush=True)
     for i in np.flatnonzero(res|new):failures.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),candidate=candidate,reference=ref,transition='rescued' if res[i] else 'new_failure',reference_hits=int(bh[i]),candidate_hits=int(ah[i]),reference_entries=' '.join(map(str,b['entries'][i])),candidate_entries=' '.join(map(str,a['entries'][i]))))
 rules={}
 for ref in ['baseline10','compact10']:
  r=local['joint10',ref,'all'];rules[ref+'_hits']=r['net_hits']>0;rules[ref+'_halves']=all(local['joint10',ref,s]['net_hits']>=0 for s in ['first_half','second_half']);rules[ref+'_failures']=r['failure_change']<=0
 r=local['joint10','conditional10','all'];rules['conditional_hits']=r['net_hits']>=0;rules['conditional_halves']=all(local['joint10','conditional10',ss]['net_hits']>=0 for ss in ['first_half','second_half']);rules['conditional_failures']=r['failure_change']<=0
 gates[ds]=dict(passed=all(rules.values()),rules=rules)
for name,data in [('points',points),('paired',paired),('failures',failures)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'results/gain_retention.json',retention);passed=any(x['passed'] for x in gates.values())
dump(O/'results/gate.json',dict(status='COMPLETE_JOINT_VIEW_PARTITION',datasets=gates,wall_measurement_allowed=passed,selection_feedback='historical auxiliary training',old_gates_unchanged=True,not_performance_GO=True))
offline=read(O/'results/offline.json');builds=read(O/'results/builds.json')
cost=dict(NSG=sum(j['actual_NSG'] for j in jobs),HNSW=129280,builds=2,synthetic_builds=0,synthetic_HNSW=0,source_graph_loads=16,count_graph_loads=16,native_job_seconds=sum(j['seconds'] for j in jobs),compile_seconds=0,micro_graph_build_seconds=sum(x['build_seconds'] for x in builds),build_process_seconds=sum(x['seconds'] for x in builds),offline_total_seconds=sum(x['seconds'] for x in offline['datasets']),rank_reconstruction_seconds=sum(x['rank_reconstruction_seconds'] for x in offline['datasets']),analysis_seconds=time.monotonic()-tick,offline_fits=2,training_updates=0,new_GT=0,inherited_GT_cost=None,inherited_GT_reason='historical exact GT/P cost not remeasured',route_graph_wall=None,reason='no formal wall in E81; later wall allowed only by the frozen quality gate')
dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=scored+1024,independent_scalar_rows=scored,old_recovered_rows=recovered,preflight_prefix_rows=1024,candidate_rows=candidate_rows+768,original_kernel_parity_rows=256,same_triple_return_rows=equal_triples,graph_W_label_checked=True,new_graphs_independently_parsed=2,actual_threads=[j['peak_threads'] for j in jobs]));check(O/'reviews/prequery_freeze.json');resources();dump(O/'state.json',dict(status='COMPLETE_JOINT_VIEW_PARTITION',NSG=129536,HNSW=129280,builds=2,wall_allowed=passed,day_goal_complete=False));print('E81_ANALYZE_PASS',gates)
