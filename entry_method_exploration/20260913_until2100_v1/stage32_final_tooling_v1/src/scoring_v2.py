from contracts_v2 import *
from graph_reader import inspect_serialized
from verify_slots_v2 import verify_slots
import itertools
FIELDS={'ids':('ids.i32',np.int32,10),'distances':('distances.f32',np.float32,10),'entries':('entry_ids.i32',np.int32,3),'graph_ndc':('graph_ndc.u32',np.uint32,1),'hits':('hits.u8',np.uint8,1),'mask':('hitmask.u16',np.uint16,1),'route_ndc':('route_ndc.u32',np.uint32,1)}
def raw(p):
 return {k:(lambda a:a.reshape(-1,w) if w>1 else a)(np.fromfile(Path(p)/f,dt)) for k,(f,dt,w) in FIELDS.items()}
def scores(a,gt,base_count):
 n=len(gt);assert gt.shape==(n,100) and a['ids'].shape==(n,10) and a['hits'].shape==a['mask'].shape==(n,)
 assert np.isfinite(a['distances']).all() and (a['ids']>=0).all() and (a['ids']<base_count).all();assert all(len(set(x.tolist()))==10 for x in a['ids']);assert all(len(set(x[:10].tolist()))==10 for x in gt)
 hits=np.array([len(set(x.tolist())&set(g[:10].tolist())) for x,g in zip(a['ids'],gt)],np.uint8);mask=np.zeros(n,np.uint16)
 for j in range(10):mask|=np.any(a['ids']==gt[:,j,None],axis=1).astype(np.uint16)<<j
 assert np.array_equal(hits,a['hits']) and np.array_equal(mask,a['mask']);return hits

def analyze_dataset(c,out,roles):
 budget=validate_config(c);out=Path(out);result=read(out/'results.json');n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);q=np.fromfile(c['queries_file'],np.float32).reshape(n,c['dim']);rows=np.fromfile(c['row_ids'],np.int64);assert rows.shape==(n,) and len(np.unique(rows))==n;assert (out/'row_ids.i64').read_bytes()==rows.tobytes()
 tc=read(out/'thread_contract.json');assert tc['process_threads']==tc['actual_openmp_threads']==1 and tc['cpu']==15;assert result['timing_repeats']==5 and result['GT_opened_after_all_raw_search'] and result['physical_graph_calls']==budget['NSG'];assert result['status']=='COMPLETE';ms=c['methods'];assert [m['name'] for m in result['methods']]==[m['name'] for m in ms]
 order=[]
 for rep in range(5):
  for ordinal,L in enumerate(LS):
   a=[m['name'] for m in ms if m['L']==L];offset=(c['dataset_order']+rep+ordinal)%len(a);order.extend((name,rep,L) for name in a[offset:]+a[:offset])
 progress=read(out/'timing_progress.json');assert [(x['name'],x['repeat'],x['L']) for x in progress]==order
 points=[];timings=[];cache={};modelbytes={};graphs=0;scored=0;samekeys=0;load=countload=wall=0.
 for configured,m in zip(ms,result['methods']):
  assert m['configuration']==configured;name=m['model_name'];L=m['L'];a=raw(out/m['name']);h=scores(a,gt,c['base_count']);scored+=n;cache[name,L]=a
  assert m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16 and m['repeated_output_parity'] and m['physical_graph_calls']==7*n+16;assert int(h.sum())==m['total_hits'] and int((h==0).sum())==m['failed_queries'];secs=np.asarray(m['end_to_end_seconds']);assert secs.shape==(5,) and (secs>0).all();qps=n/secs;np.testing.assert_allclose(qps,m['qps_runs'],rtol=1e-13,atol=0);assert float(np.median(qps))==m['qps']
  events=[e for e in progress if e['name']==m['name']];assert len(events)==5
  for j,e in enumerate(events):assert e['repeat']==j and abs(e['seconds']-secs[j])<1e-12
  np.testing.assert_allclose([a['route_ndc'].mean(),a['graph_ndc'].mean()],[m['mean_route_ndc'],m['mean_graph_ndc']],rtol=0,atol=1e-10)
  if configured['family']=='nsg':assert (a['route_ndc']==0).all() and (a['entries'][:,0]==configured['fixed_entry']).all()
  else:
   mapping=np.fromfile(configured['mapping'],np.int32);W=np.fromfile(configured['W'],np.float32).reshape(len(mapping),c['dim']);inspect_serialized(configured['graph_file'],W,np.arange(len(W)) if configured.get('slot_labels') else mapping);graphs+=1;assert np.isin(a['entries'],mapping).all() and all(len(set(x.tolist()))==3 for x in a['entries']);fingerprint=(sha(configured['graph_file']),a['entries'].tobytes(),a['route_ndc'].tobytes())
   if name in modelbytes:assert modelbytes[name]==fingerprint
   modelbytes[name]=fingerprint
   if configured.get('multi_profile'):verify_slots(out/m['name'],mapping,W,q,a['entries'],(sha(configured['graph_file']),configured.get('ef_search',10)))
  load+=m['policy_build_seconds'];countload+=m['count_policy_load_seconds'];wall+=float(secs.sum());points.append(dict(dataset=c['dataset'],model=name,L=L,queries=n,recall_pct=float(h.mean()*10),failure_count=int((h==0).sum()),failure_rate_pct=float((h==0).mean()*100),QPS=float(np.median(qps)),QPS_min=float(qps.min()),QPS_max=float(qps.max()),mean_route_NDC=float(a['route_ndc'].mean()),mean_graph_NDC=float(a['graph_ndc'].mean())))
  for j,(s,rate) in enumerate(zip(secs,qps)):timings.append(dict(dataset=c['dataset'],model=name,L=L,repeat=j,seconds=float(s),QPS=float(rate)))
 pair=[];failure=[]
 for L in LS:
  names=[m['model_name'] for m in ms if m['L']==L]
  for x,y in itertools.combinations(names,2):
   a,b=cache[x,L],cache[y,L];ix=np.flatnonzero(np.all(a['entries']==b['entries'],axis=1));samekeys+=len(ix)
   for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==b[k][ix].tobytes()
  for i in range(n):
   if any(cache[name,L]['hits'][i]==0 for name in names):
    status=[bool(cache[name,L]['hits'][i]==0) for name in names]
    for name in names:
     a=cache[name,L];failure.append(dict(dataset=c['dataset'],namespace=c.get('source_namespace',c['split']),source_row=int(rows[i]),L=L,model=name,hits=int(a['hits'][i]),failed=bool(a['hits'][i]==0),changed_zero_status=len(set(status))>1,GT10=' '.join(map(str,gt[i,:10])),entries=' '.join(map(str,a['entries'][i])),returned=' '.join(map(str,a['ids'][i])),distances=' '.join(map(str,a['distances'][i]))))
  for candidate in sorted(set(roles.values())):
   a=cache[candidate,L];pa=next(p for p in points if p['model']==candidate and p['L']==L)
   for ref in names:
    if ref==candidate:continue
    b=cache[ref,L];pb=next(p for p in points if p['model']==ref and p['L']==L);d=a['hits'].astype(int)-b['hits'];mg=sum((int(u)&~int(v)).bit_count() for u,v in zip(a['mask'],b['mask']));ml=sum((int(v)&~int(u)).bit_count() for u,v in zip(a['mask'],b['mask']));assert mg-ml==int(d.sum())
    pair.append(dict(dataset=c['dataset'],L=L,candidate=candidate,reference=ref,net_hits=int(d.sum()),delta_recall_pp=float(d.mean()*10),gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),member_gained=mg,member_lost=ml,rescued=int(((a['hits']>0)&(b['hits']==0)).sum()),new_failures=int(((a['hits']==0)&(b['hits']>0)).sum()),QPS_change_pct=(pa['QPS']/pb['QPS']-1)*100,all_range_low_pct=(pa['QPS_min']/pb['QPS_max']-1)*100,all_range_high_pct=(pa['QPS_max']/pb['QPS_min']-1)*100))
 return dict(points=points,timings=timings,paired=pair,failures=failure,verification=dict(set_mask_rows=scored,physical_graphs=graphs,original_kernel_rows=16*len(ms),same_triple_rows=samekeys,wall_batches=5*len(ms),source_load_seconds=load,count_load_seconds=countload,pure_wall_seconds=wall),budget=budget)
