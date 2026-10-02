from common import *
from verify_candidates import verify_candidates
import csv,itertools
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
tick=time.monotonic();points=[];pairs=[];retention=[];failure_rows=[];gates={};verified=0;recovered=0;candidate_rows=0;equal=0
def table(path,rows):
 assert rows
 with Path(path).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(c['row_ids'],np.int64);a={};methods={m['model_name']:m for m in c['methods']}
 for name,m in methods.items():
  p=O/'results'/ds/'aux'/m['name'];b=raw(p);a[name]=b;h,mask=score(b['ids'],gt);assert np.array_equal(h,b['hits']) and np.array_equal(mask,b['mask'])
  for ids,g,hh in zip(b['ids'],gt,h):assert len(set(ids.tolist()))==10 and min(ids)>=0 and max(ids)<c['base_count'] and len(set(ids.tolist())&set(g[:10].tolist()))==hh
  verified+=7952;candidate_rows+=verify_candidates(c,m,p,b,7952)
  pf=raw(O/'results'/ds/'preflight'/m['name'])
  for k in pf:assert b[k][:128].tobytes()==pf[k].tobytes()
  if name in ['baseline10','compact10','previous10']:
   source=E89/'results'/ds/'aux/restore10_L128' if name=='previous10' else E73/'results'/ds/'aux'/m['name'];r=raw(source)
   same(b,r,tuple(b));recovered+=7952
 for x,y in itertools.combinations(a,2):
  sameidx=np.flatnonzero(np.all(a[x]['entries']==a[y]['entries'],axis=1));equal+=len(sameidx)
  same({k:a[x][k][sameidx] for k in ['ids','distances','graph_ndc']},{k:a[y][k][sameidx] for k in ['ids','distances','graph_ndc']})
 local={}
 for split,sl in [('all',slice(None)),('support',slice(0,3976)),('accept',slice(3976,None)),('accept_half1',slice(3976,5964)),('accept_half2',slice(5964,None))]:
  for name,b in a.items():
   h=b['hits'][sl];points.append(dict(dataset=ds,model=name,split=split,n=len(h),total_hits=int(h.sum()),recall=float(h.mean()/10),failures=int((h==0).sum()),failure_rate=float((h==0).mean()),mean_route_NDC=float(b['route_ndc'][sl].mean()),mean_graph_NDC=float(b['graph_ndc'][sl].mean()),mean_total_NDC=float((b['route_ndc'][sl].astype(float)+b['graph_ndc'][sl]).mean())))
  for ca,ref in [('supported10','baseline10'),('supported10','compact10'),('supported10','previous10'),('supported10','random10'),('random10','baseline10'),('random10','compact10')]:
   x,y=a[ca],a[ref];xh=x['hits'][sl].astype(int);yh=y['hits'][sl].astype(int);delta=xh-yh;res=(xh>0)&(yh==0);new=(xh==0)&(yh>0);mg=sum((int(u)&~int(v)).bit_count() for u,v in zip(x['mask'][sl],y['mask'][sl]));ml=sum((int(v)&~int(u)).bit_count() for u,v in zip(x['mask'][sl],y['mask'][sl]));assert mg-ml==int(delta.sum())
   r=dict(dataset=ds,candidate=ca,reference=ref,split=split,n=len(xh),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=mg,member_lost=ml,route_NDC_change_pct=float((x['route_ndc'][sl].mean()/y['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((x['graph_ndc'][sl].mean()/y['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((x['route_ndc'][sl].astype(float)+x['graph_ndc'][sl]).mean()/(y['route_ndc'][sl].astype(float)+y['graph_ndc'][sl]).mean()-1)*100));pairs.append(r);local[ca,ref,split]=r
   if split=='accept':print('E90_PAIR',r,flush=True)
 old=a['compact10']['hits'].astype(int)-a['baseline10']['hits'];og=np.maximum(old,0);ol=np.maximum(-old,0)
 for name in ['supported10','random10','previous10']:
  cur=a[name]['hits'].astype(int)-a['baseline10']['hits'];ng=np.maximum(cur,0);nl=np.maximum(-cur,0);ret=np.minimum(og,ng);lost=og-ret;add=np.maximum(ng-og,0);avoid=np.maximum(ol-nl,0);damage=np.maximum(nl-ol,0);assert np.array_equal(old-lost+add+avoid-damage,cur)
  retention.append(dict(dataset=ds,candidate=name,old_gain=int(og.sum()),retained_old_gain=int(ret.sum()),forgone_old_gain=int(lost.sum()),new_gain=int(add.sum()),old_loss=int(ol.sum()),avoided_old_loss=int(avoid.sum()),new_or_amplified_loss=int(damage.sum()),new_total_loss=int(nl.sum()),net_delta_vs_compact=int((cur-old).sum())))
 zero=np.stack([b['hits']==0 for b in a.values()],axis=1)
 for i in np.flatnonzero(zero.any(1)):
  r=dict(dataset=ds,namespace='router_train',role='support_training' if i<3976 else 'historically_exposed_acceptance',source_row=int(rows[i]),changed_zero_status=bool(zero[i].any() and not zero[i].all()),GT10=' '.join(map(str,gt[i,:10])))
  for name,b in a.items():
   r[name+'_hits']=int(b['hits'][i]);r[name+'_entries']=' '.join(map(str,b['entries'][i]));r[name+'_returned']=' '.join(map(str,b['ids'][i]))
  failure_rows.append(r)
 rules={}
 for ref in ['baseline10','compact10','previous10','random10']:
  r=local['supported10',ref,'accept'];rules[ref+'_net']=r['net_hits']>0 if ref in ['baseline10','compact10'] else r['net_hits']>=0;rules[ref+'_halves']=all(local['supported10',ref,s]['net_hits']>=0 for s in ['accept_half1','accept_half2']);rules[ref+'_failures']=r['failure_change']<=0
  if ref in ['baseline10','compact10']:rules[ref+'_cost']=r['total_NDC_change_pct']<=1
 tr=[x for x in read(O/'results'/ds/'union_statistics.json') if x['model']=='supported10'];assert len(tr)==2
 rules['nonzero_update']=len(read(O/'models'/ds/'selected_actions.json'))>0
 for r in tr:rules['merged_training_'+r['role']]=r['net_hits']>0 and min(r['half_net_hits'])>=0 and r['failure_delta']<=0 and r['total_ndc_relative']<=.01
 for name in ['supported10','random10']:
  z=dict(np.load(O/'results'/ds/'support'/(name+'.npz')));same(z,{k:v[:3976] for k,v in a[name].items()},tuple(a[name]));recovered+=3976
 gates[ds]=dict(passed=bool(all(rules.values())),rules=rules)

table(O/'results/points.csv',points);table(O/'results/paired.csv',pairs);table(O/'results/failure_queries.csv',failure_rows);dump(O/'results/gain_retention.json',retention)
passed=any(x['passed'] for x in gates.values());dump(O/'results/gate.json',dict(status='COMPLETE_CROSS_SOURCE_PARENT_RESTORE',datasets=gates,wall_measurement_allowed=passed,selection_feedback='historically exposed auxiliary acceptance counts as training information',old_gates_unchanged=True,not_performance_GO=True))
tj=read(O/'logs/training_jobs.json');cost=dict(NSG=sum(j['actual_NSG'] for j in jobs+tj),training_NSG=sum(j['actual_NSG'] for j in tj),aux_NSG=sum(j['actual_NSG'] for j in jobs),HNSW=sum(j['actual_HNSW'] for j in tj)+161600,training_HNSW=sum(j['actual_HNSW'] for j in tj),aux_HNSW=161600,ordinary_builds=0,physical_graph_exports=sum(j['vector_exports'] for j in tj),nonzero_vector_installs=sum(2*int(j['accepted_actions']>0) for j in tj),zero_update_copies=sum(2*int(j['accepted_actions']==0) for j in tj),offline_utility_fits=2,gradient_updates=0,new_GT=0,compile_seconds=0,preparation_operation_seconds=read(O/'results/preparation_cost.json')['operation_seconds'],training_operation_seconds=sum(j['seconds'] for j in tj),aux_native_operation_seconds=sum(j['seconds'] for j in jobs),timing_scope='operations include load, count, cache verification, serialization and I/O; no QPS',inherited_GT_P_cost=None,inherited_cost_reason='Historical GT/P total cost unavailable; E86 compact fit cache generation inherited and separately charged in E86.',new_QPS_points=0,failures_union=len(failure_rows),failure_state_changes=sum(r['changed_zero_status'] for r in failure_rows),analysis_seconds=time.monotonic()-tick)
assert cost['NSG']<=227456 and cost['HNSW']<=616304;dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=verified+1280,independent_scalar_rows=verified,old_recovered_rows=recovered,preflight_prefix_rows=1280,candidate_rows=candidate_rows+1024,original_kernel_parity_rows=320,same_triple_return_rows=equal,actual_threads=[j['peak_threads'] for j in jobs],graph_identity_checked=True));dump(O/'state.json',dict(status='COMPLETE_CROSS_SOURCE_PARENT_RESTORE',NSG=cost['NSG'],HNSW=cost['HNSW'],wall_allowed=passed,day_goal_complete=False));check(O/'reviews/prequery_freeze.json');resources();print('E90_ANALYSIS_COMPLETE',gates,cost)
