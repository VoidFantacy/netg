from verify_candidates import *
import csv,struct
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
E73=C/'stage14_compact_modes_v1';tick=time.monotonic();points=[];paired=[];failures=[];gates={};level_records=[];retention=[];scored=recovered=candidate_rows=equal_triples=0
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
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/m['name']/fn).read_bytes()
  candidate_rows+=verify_candidates(c,m,p,a,7952)
 for ca,ref in [('sibling10','baseline10'),('sibling10','compact10'),('sibling10','neighbor10'),('neighbor10','baseline10'),('neighbor10','compact10')]:
  a,b=raw[ca],raw[ref];ix=np.flatnonzero(np.all(a['entries']==b['entries'],axis=1));equal_triples+=len(ix)
  for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==b[k][ix].tobytes()
 # Independent byte/adjacency verification of four installed graphs against source.
 names=['compact10','sibling10','neighbor10'];ms={m['model_name']:m for m in c['methods']};gl=[graph_levels(ms[x]['graph_file']) for x in names];assert all(x==gl[0] for x in gl)
 before=Path(ms['compact10']['graph_file']).read_bytes();hd=struct.unpack_from('<6QiI3QdQ',before);nn,size,label,coord=hd[2:6];plans={x['slot']:x for x in read(O/'models'/ds/'additions.json')};degs=[]
 for name,field in [('sibling10','sibling_added'),('neighbor10','neighbor_added')]:
  after=Path(ms[name]['graph_file']).read_bytes();restored=bytearray(after);degree=[]
  for i in range(nn):
   at=96+i*size;od=struct.unpack_from('<H',before,at)[0];nd=struct.unpack_from('<H',after,at)[0];degree.append(nd)
   oldids=list(struct.unpack_from('<'+'I'*od,before,at+4));newids=list(struct.unpack_from('<'+'I'*nd,after,at+4));added=plans[i][field] if i in plans else [];assert newids==oldids+added
   restored[at:at+2]=before[at:at+2];left=at+4+4*od;right=at+4+4*nd;restored[left:right]=before[left:right]
  assert bytes(restored)==before;degs.append(degree)
 assert degs[0]==degs[1]
 level_records.append(dict(dataset=ds,all_slot_levels_entry_identical=True,all_nonadjacency_bytes_exact=True,old_edges_preserved=True,pernode_degree_matched=True,entry_slot=int(gl[0][1]),maxlevel=int(gl[0][2])))
 # Query net-hit gain retention and total-loss migration, not GT-member counts.
 old_delta=raw['compact10']['hits'].astype(int)-raw['baseline10']['hits'].astype(int);og=np.maximum(old_delta,0);ol=np.maximum(-old_delta,0)
 for candidate in ['sibling10','neighbor10']:
  new_delta=raw[candidate]['hits'].astype(int)-raw['baseline10']['hits'].astype(int);ng=np.maximum(new_delta,0);nl=np.maximum(-new_delta,0);retained=np.minimum(og,ng);forgone=og-retained;gain_added=np.maximum(ng-og,0);loss_avoided=np.maximum(ol-nl,0);loss_added=np.maximum(nl-ol,0)
  assert np.array_equal(old_delta-forgone+gain_added+loss_avoided-loss_added,new_delta)
  retention.append(dict(dataset=ds,candidate=candidate,old_gain=int(og.sum()),retained_old_gain=int(retained.sum()),forgone_old_gain=int(forgone.sum()),new_gain=int(gain_added.sum()),old_loss=int(ol.sum()),avoided_old_loss=int(loss_avoided.sum()),new_or_amplified_loss=int(loss_added.sum()),new_total_loss=int(nl.sum()),net_delta_vs_compact=int((new_delta-old_delta).sum())))
 local={}
 for split,sl in [('all',slice(None)),('first_half',slice(0,3976)),('second_half',slice(3976,None))]:
  for name,a in raw.items():
   h=a['hits'][sl];points.append(dict(dataset=ds,model=name,split=split,n=len(h),total_hits=int(h.sum()),recall=float(h.mean()/10),failures=int((h==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for candidate in ['sibling10','neighbor10']:
   for ref in ['baseline10','compact10']+(['neighbor10'] if candidate=='sibling10' else []):
    a,b=raw[candidate],raw[ref];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
    gained=sum((int(x)&~int(y)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));lost=sum((int(y)&~int(x)).bit_count() for x,y in zip(a['mask'][sl],b['mask'][sl]));assert gained-lost==int(delta.sum())
    r=dict(dataset=ds,candidate=candidate,reference=ref,split=split,n=len(ah),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=gained,member_lost=lost,route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100));paired.append(r);local[candidate,ref,split]=r
    if split=='all':
     print(r,flush=True)
     for i in np.flatnonzero(res|new):failures.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),candidate=candidate,reference=ref,transition='rescued' if res[i] else 'new_failure',reference_hits=int(bh[i]),candidate_hits=int(ah[i]),reference_entries=' '.join(map(str,b['entries'][i])),candidate_entries=' '.join(map(str,a['entries'][i]))))
 rules={}
 for ref in ['baseline10','compact10']:
  r=local['sibling10',ref,'all'];rules[ref+'_hits']=r['net_hits']>0;rules[ref+'_halves']=all(local['sibling10',ref,s]['net_hits']>=0 for s in ['first_half','second_half']);rules[ref+'_failures']=r['failure_change']<=0
 r=local['sibling10','neighbor10','all'];rules['neighbor_hits']=r['net_hits']>=0;rules['neighbor_halves']=all(local['sibling10','neighbor10',ss]['net_hits']>=0 for ss in ['first_half','second_half']);rules['neighbor_failures']=r['failure_change']<=0
 gates[ds]=dict(passed=all(rules.values()),rules=rules)
for name,data in [('points',points),('paired',paired),('failures',failures)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
dump(O/'results/levels.json',level_records);dump(O/'results/gain_retention.json',retention);passed=any(x['passed'] for x in gates.values())
dump(O/'results/gate.json',dict(status='COMPLETE_SIBLING_LINKS',datasets=gates,wall_measurement_allowed=passed,selection_feedback='historical auxiliary training',old_gates_unchanged=True,not_performance_GO=True))
cost=dict(NSG=sum(j['actual_NSG'] for j in jobs),HNSW=129280,builds=0,synthetic_builds=0,synthetic_HNSW=0,edge_installs=4,source_graph_loads=16,count_graph_loads=16,native_job_seconds=sum(j['seconds'] for j in jobs),compile_seconds=read(O/'bin/provenance.json')['compile_seconds'],micro_graph_build_seconds=0,edge_install_seconds=None,edge_install_seconds_reason='all four installs completed before metadata error, elapsed not persisted',profile_construction_seconds=0,first_failed_prepare_seconds=None,resume_preparation_seconds=read(O/'results/construction.json')['preparation_seconds'],analysis_seconds=time.monotonic()-tick,training_updates=0,new_GT=0,route_graph_wall=None,reason='no formal wall in E83; source W unchanged, edges installed offline; later wall gate independent')
dump(O/'results/cost.json',cost);dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=scored+1024,independent_scalar_rows=scored,old_recovered_rows=recovered,preflight_prefix_rows=1024,candidate_rows=candidate_rows+768,original_kernel_parity_rows=256,same_triple_return_rows=equal_triples,graph_W_label_checked=True,all_nonadjacency_bytes_and_old_prefix_verified=True,actual_threads=[j['peak_threads'] for j in jobs]));check(O/'reviews/prequery_freeze.json');resources();dump(O/'state.json',dict(status='COMPLETE_SIBLING_LINKS',NSG=129536,HNSW=129280,builds=0,wall_allowed=passed,day_goal_complete=False));print('E83_ANALYZE_PASS',gates)
