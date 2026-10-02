from verify_candidates import *
import csv,struct
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
E73=C/'stage14_compact_modes_v1';tick=time.monotonic();points=[];paired=[];failures=[];gates={};level_records=[];scored=recovered=candidate_rows=equal_triples=0
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
  if name!='preserved10':
   old=load_raw(E73/'results'/ds/'aux'/m['name'],7952)
   for k in a:assert a[k].tobytes()==old[k].tobytes(),(ds,name,k)
   recovered+=7952
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/m['name']/fn).read_bytes()
  candidate_rows+=verify_candidates(c,m,p,a,7952)
 for ref in ['baseline10','compact10']:
  a,b=raw['preserved10'],raw[ref];ix=np.flatnonzero(np.all(a['entries']==b['entries'],axis=1));equal_triples+=len(ix)
  for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==b[k][ix].tobytes()
 # Independent parser of serialized levels and original external-slot identities.
 config=read(O/'models'/ds/'build_config.json');keep=np.fromfile(config['original_slots'],np.int32);full,entry,top=graph_levels(config['source_graph']);new,newentry,newtop=graph_levels(O/'models'/ds/'graph.hnsw');old,oldentry,oldtop=graph_levels(E73/'models'/ds/'graph.hnsw')
 seq=read(O/'models'/ds/'random_stream.json')['source_levels'];assert [full[i] for i in range(len(full))]==seq
 assert len(new)==len(keep) and all(new[j]==full[int(k)] for j,k in enumerate(keep))
 level_records.append(dict(dataset=ds,retained_profiles=len(keep),source_full_entry=entry,ordinary_compact_entry=oldentry,ordinary_entry_original_slot=int(keep[oldentry]),preserved_compact_entry=newentry,preserved_entry_original_slot=int(keep[newentry]),ordinary_level_changes=sum(old[j]!=full[int(k)] for j,k in enumerate(keep)),preserved_level_changes=0,source_maxlevel=top,new_maxlevel=newtop,source_retained_hist=np.bincount([full[int(k)] for k in keep]).tolist(),ordinary_hist=np.bincount(list(old.values())).tolist(),preserved_hist=np.bincount(list(new.values())).tolist()))
 local={}
 for split,sl in [('all',slice(None)),('first_half',slice(0,3976)),('second_half',slice(3976,None))]:
  for name,a in raw.items():
   h=a['hits'][sl];points.append(dict(dataset=ds,model=name,split=split,n=len(h),total_hits=int(h.sum()),recall=float(h.mean()/10),failures=int((h==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for ref in ['baseline10','compact10']:
   a,b=raw['preserved10'],raw[ref];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   gained=sum((int(x)&~int(y)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));lost=sum((int(y)&~int(x)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));assert gained-lost==int(delta.sum())
   r=dict(dataset=ds,candidate='preserved10',reference=ref,split=split,n=len(ah),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=gained,member_lost=lost,route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100));paired.append(r);local[ref,split]=r
   if split=='all':
    print(r,flush=True)
    for i in np.flatnonzero(res|new):failures.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),reference=ref,transition='rescued' if res[i] else 'new_failure',reference_hits=int(bh[i]),candidate_hits=int(ah[i]),reference_entries=' '.join(map(str,b['entries'][i])),candidate_entries=' '.join(map(str,a['entries'][i]))))
 rules={}
 for ref in ['baseline10','compact10']:
  r=local[ref,'all'];rules[ref+'_hits']=r['net_hits']>0;rules[ref+'_halves']=all(local[ref,s]['net_hits']>=0 for s in ['first_half','second_half']);rules[ref+'_failures']=r['failure_change']<=0
 gates[ds]=dict(passed=all(rules.values()),rules=rules)
for name,data in [('points',points),('paired',paired),('failures',failures)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'results/levels.json',level_records);passed=any(x['passed'] for x in gates.values())
dump(O/'results/gate.json',dict(status='COMPLETE_PRESERVED_LEVEL_DEVELOPMENT',datasets=gates,wall_measurement_allowed=passed,selection_feedback='historical auxiliary training',old_gates_unchanged=True,not_performance_GO=True))
cost=dict(NSG=sum(j['actual_NSG'] for j in jobs),HNSW=96960,builds=2,synthetic_builds=4,synthetic_HNSW=512,source_graph_loads=12,count_graph_loads=12,native_job_seconds=sum(j['seconds'] for j in jobs),compile_seconds=read(O/'bin/provenance.json')['seconds'],micro_graph_build_seconds=sum(read(O/'models'/ds/'build.json')['build_seconds'] for ds in DS),analysis_seconds=time.monotonic()-tick,training_updates=0,new_GT=0,route_graph_wall=None,reason='no formal wall in E75; later wall allowed only by the frozen quality gate')
dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=scored+768,independent_scalar_rows=scored,old_recovered_rows=recovered,preflight_prefix_rows=768,candidate_rows=candidate_rows+512,original_kernel_parity_rows=192,same_triple_return_rows=equal_triples,graph_W_label_checked=True,all_retained_source_levels_preserved=True,actual_threads=[j['peak_threads'] for j in jobs]));check(O/'reviews/prequery_freeze.json');resources();dump(O/'state.json',dict(status='COMPLETE_PRESERVED_LEVEL_DEVELOPMENT',NSG=97152,HNSW=96960,builds=2,wall_allowed=passed,day_goal_complete=False));print('E75_ANALYZE_PASS',gates)
