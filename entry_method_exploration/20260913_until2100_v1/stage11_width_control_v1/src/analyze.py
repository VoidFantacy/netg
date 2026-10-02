from common import *
import csv
threads();resources();check(O/'reviews/prequery_freeze.json');jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(x['status']=='COMPLETE' for x in jobs)
start=time.monotonic();points=[];paired=[];failures=[];rankstats=[];gates={};count=0;slotrows=0;models=[m+str(ef) for m in MODELS for ef in [10,30]]
comp=[('baseline30','baseline10'),('duplicate3P30','duplicate3P10'),('mode3P30','mode3P10'),('mode3P30','baseline10'),('mode3P30','baseline30'),('mode3P30','duplicate3P30'),('mode3P10','baseline10')]
pop=np.array([i.bit_count() for i in range(1024)],np.int16)
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');n=7952;d=c['dim'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);q=np.fromfile(c['queries_file'],np.float32).reshape(n,d)
 rows=np.fromfile(c['row_ids'],np.int64);ref=dict(np.load(E68/'results'/ds/'aux.npz'));assert np.array_equal(rows,ref['source_rows']);raw={};records=read(O/'results'/ds/'aux/results.json')['methods']
 for method in c['methods']:
  name=method['model_name'];base=name[:-2];ef=method['ef_search'];p=O/'results'/ds/'aux'/method['name'];a={}
  for k,(fn,dt,w) in FIELDS.items():a[k]=np.fromfile(p/fn,dt).reshape(n,w) if w>1 else np.fromfile(p/fn,dt)
  a['route_ndc']=np.fromfile(p/'route_ndc.u32',np.uint32)
  match=np.any(a['ids'][:,:,None]==gt[:,None,:10],axis=1);h=match.sum(1);mask=(match*(1<<np.arange(10))).sum(1)
  assert np.array_equal(h,a['hits']) and np.array_equal(mask,a['mask']);count+=n
  assert np.all(np.diff(a['entries'],axis=1)>0)
  if ef==10:
   old=old_raw(ds,base)
   for k in FIELDS:assert a[k].tobytes()==old[k].tobytes(),(name,k)
   assert a['route_ndc'].tobytes()==(E66/'results'/ds/'aux'/(base+'_L128')/'route_ndc.u32').read_bytes()
  for k,(fn,dt,w) in FIELDS.items():assert a[k][:128].tobytes()==(O/'results'/ds/'preflight'/method['name']/fn).read_bytes()
  exact=ref['exact_mode_hubs'] if base=='mode3P' else ref['exact_P_hubs'];agreement=np.sum(np.any(a['entries'][:,:,None]==exact[:,None,:],axis=2),axis=1)
  rankstats.append(dict(dataset=ds,model=name,n=n,exact_three_agreement=float((agreement==3).mean()),mean_overlap=float(agreement.mean()/3)))
  if method.get('multi_profile',False):
   slots=np.fromfile(p/'candidate_slots.i32',np.int32).reshape(n,7);dist=np.fromfile(p/'candidate_distances.f32',np.float32).reshape(n,7);W=np.fromfile(method['W'],np.float32).reshape(method['hub_count'],d);mapping=np.fromfile(method['mapping'],np.int32)
   for i in range(n):
    assert np.array_equal(np.lexsort((slots[i],dist[i])),np.arange(7));sel=[]
    for slot in slots[i]:
     h=int(mapping[slot])
     if h not in sel:sel.append(h)
    assert np.array_equal(sorted(sel[:3]),a['entries'][i]);slotrows+=1
   for b in range(0,n,128):
    vv=W[slots[b:b+128]].astype(float);calc=1-np.einsum('nkd,nd->nk',vv,q[b:b+128].astype(float));assert np.allclose(calc,dist[b:b+128],rtol=2e-5,atol=2e-5)
   if ef==10:
    for fn in ['candidate_slots.i32','candidate_distances.f32']:assert (p/fn).read_bytes()==(E66/'results'/ds/'aux'/(base+'_L128')/fn).read_bytes()
  raw[name]=a
 local={}
 for split,sl in [('all',slice(0,n)),('first_half',slice(0,3976)),('second_half',slice(3976,n))]:
  for name,a in raw.items():points.append(dict(dataset=ds,model=name,split=split,n=sl.stop-sl.start,total_hits=int(a['hits'][sl].sum()),recall=float(a['hits'][sl].mean()/10),failures=int((a['hits'][sl]==0).sum()),mean_route_NDC=float(a['route_ndc'][sl].mean()),mean_graph_NDC=float(a['graph_ndc'][sl].mean()),mean_total_NDC=float((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean())))
  for cand,reference in comp:
   a=raw[cand];b=raw[reference];ah=a['hits'][sl].astype(int);bh=b['hits'][sl].astype(int);delta=ah-bh;res=(bh==0)&(ah>0);new=(bh>0)&(ah==0)
   r=dict(dataset=ds,candidate=cand,reference=reference,split=split,n=len(delta),net_hits=int(delta.sum()),recall_delta_pp=float(delta.mean()*10),rescued=int(res.sum()),new_failures=int(new.sum()),failure_change=int(new.sum()-res.sum()),positive_query_hits=int(np.maximum(delta,0).sum()),negative_query_hits=int(np.maximum(-delta,0).sum()),member_gained=int(pop[(a['mask'][sl]&~b['mask'][sl])&1023].sum()),member_lost=int(pop[(b['mask'][sl]&~a['mask'][sl])&1023].sum()),route_NDC_change_pct=float((a['route_ndc'][sl].mean()/b['route_ndc'][sl].mean()-1)*100),graph_NDC_change_pct=float((a['graph_ndc'][sl].mean()/b['graph_ndc'][sl].mean()-1)*100),total_NDC_change_pct=float(((a['route_ndc'][sl]+a['graph_ndc'][sl]).mean()/(b['route_ndc'][sl]+b['graph_ndc'][sl]).mean()-1)*100))
   assert r['net_hits']==r['member_gained']-r['member_lost'];paired.append(r);local[(cand,reference,split)]=r
   if split=='all':
    for row in np.flatnonzero(res|new):failures.append(dict(dataset=ds,source_row=int(rows[row]),candidate=cand,reference=reference,transition='rescued' if res[row] else 'new_failure',reference_hits=int(bh[row]),candidate_hits=int(ah[row]),reference_entries=' '.join(map(str,b['entries'][row])),candidate_entries=' '.join(map(str,a['entries'][row]))))
 rules={}
 for reference in ['baseline10','baseline30']:
  a=local[('mode3P30',reference,'all')];rules[reference+'_positive']=a['net_hits']>0;rules[reference+'_halves']=all(local[('mode3P30',reference,s)]['net_hits']>=0 for s in ['first_half','second_half']);rules[reference+'_failures']=a['failure_change']<=0
 rules['mode10_nonnegative']=local[('mode3P30','mode3P10','all')]['net_hits']>=0;gates[ds]=dict(passed=all(rules.values()),rules=rules)
 for reference in ['baseline10','baseline30','mode3P10']:print(ds,reference,local[('mode3P30',reference,'all')],flush=True)
for name,a in [('points',points),('paired',paired),('failures',failures),('ranking',rankstats)]:
 with (O/'results'/(name+'.csv')).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(a[0]));w.writeheader();w.writerows(a)
dump(O/'results/gate.json',dict(status='COMPLETE_WIDTH_QUALITY_CONTROL',datasets=gates,full_development_wall_supported=any(x['passed'] for x in gates.values()),old_E66_gate_unchanged=True,not_performance_GO=True))
dump(O/'results/cost.json',dict(NSG=sum(x['actual_NSG'] for x in jobs),HNSW=193920,builds=0,source_graph_loads=24,count_graph_loads=24,native_job_seconds=sum(x['seconds'] for x in jobs),compile_seconds=read(O/'bin/provenance.json')['seconds'],analysis_seconds=time.monotonic()-start,route_graph_wall=None,reason='not separately timed; no QPS diagnostic'))
dump(O/'reviews/verification.json',dict(status='PASS',set_scored_rows=count+1536,full_aux_set_rows=count,full_ef10_recovered_rows=47712,preflight_recovered_rows=768,slot_rows=slotrows,preflight_to_aux_rows=1536,original_kernel_parity_rows=384,source_graphs_referenced=True,graph_copies=0,threads_actual=[j['peak_threads'] for j in jobs]))
check(O/'reviews/prequery_freeze.json');dump(O/'state.json',dict(status='COMPLETE_WIDTH_CONTROL',NSG=194304,HNSW=193920,builds=0,day_goal_complete=False));resources()
