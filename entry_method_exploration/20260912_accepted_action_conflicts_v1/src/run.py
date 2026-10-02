from shared import *
from native_factorial import Native
ds=sys.argv[1];assert ds in DS;threads(15);resources();check(O/'reviews/prequery_freeze.json');assert time.time()<1789219800
resource.setrlimit(resource.RLIMIT_AS,(32*(1<<30),32*(1<<30)))
ledger=O/'logs/jobs.json';jobs=read(ledger) if ledger.exists() else [];assert not any(x['dataset']==ds or x['status']=='RUNNING' for x in jobs)
assert sum(x['reserved'] for x in jobs)+30000<=60000
job=dict(dataset=ds,status='RUNNING',reserved=30000,pid=os.getpid(),started_at=time.time());jobs.append(job);dump(ledger,jobs)
c=read(O/'inputs'/ds/'config.json');P=np.fromfile(c['P'],np.float32).reshape(c['hub_count'],c['dim']);mapping=np.fromfile(c['hub_ids'],np.int32);gt=np.fromfile(c['gt_file'],np.int64).reshape(5120,100)
anchor=dict(np.load(E37/'results'/ds/'baseline.npz'));base={k:anchor[k][4096:] for k in FIELDS+['hits']};train_base={k:anchor[k][:4096] for k in FIELDS+['hits']};qrows=np.arange(4096,5120,dtype=np.int32)
started=time.monotonic();native=Native(c);normal_nsg=0;normal_states=0;parity_graphs=0;all_steps=[]
def set_graph(W,pure,expected):
 top=native.build(W)
 if pure:
  t=native.data(5,np.int32);native.build(P);assert native.install_topology(t)==top
 native.verify_vectors(P if pure else W);assert top==expected
def evaluate(parent,dest):
 global normal_nsg,normal_states
 assert time.time()<QUERY_STOP and time.monotonic()-started<360;resources()
 route=native.route(qrows);changed=np.flatnonzero((route['entries']!=parent['entries']).any(1)).astype(np.int32);patch=native.search_entries(qrows[changed],route['entries'][changed]);patch['hits']=score(patch['ids'],gt[qrows[changed]])
 out={k:parent[k].copy() for k in ['ids','distances','graph_ndc','hits']};out.update(route)
 for k in patch:out[k][changed]=patch[k]
 save(dest,changed_rows=changed,entries=route['entries'][changed],route_ndc=route['route_ndc'],parent_cache_sha=np.array(raw_digest(parent)),cache_sha=np.array(raw_digest(out)),**patch)
 normal_nsg+=len(changed);normal_states+=1;return out
def phase_delta(out,parent):
 dh=out['hits'].astype(int)-parent['hits'];return dict(gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),net_hits=int(dh.sum()),helped=int((dh>0).sum()),harmed=int((dh<0).sum()),
  rescued=int(((parent['hits']==0)&(out['hits']>0)).sum()),new_failures=int(((parent['hits']>0)&(out['hits']==0)).sum()))
try:
 for rec in [x for x in read(O/'inputs/contexts.json') if x['dataset']==ds]:
  src=Path(rec['source']);dest=O/'results'/ds/rec['key'];dest.mkdir(parents=True);(dest/'monitor_patches').mkdir();(dest/'checkpoints').mkdir();(dest/'parity').mkdir()
  W=P.copy();train={k:v.copy() for k,v in train_base.items()};meta=read(src/'checkpoints.json');curve=read(src/'training_curve.json');top=meta[0]['topology_sha'];set_graph(W,rec['construction_only'],top)
  mon=evaluate(base,dest/'monitor_patches/0000.npz');equal(mon,base);td=[];md=[];steps=[];seen_accepts=0
  for step in range(201):
   if step%20==0:
    cp=dict(np.load(src/'checkpoints'/f'{step:04}.npz'));assert digest(W)==digest(cp['W']);equal(train,{k:cp[k][:4096] for k in FIELDS});equal(mon,{k:cp[k][4096:] for k in FIELDS})
    assert np.array_equal(train['hits'],cp['hits'][:4096]) and np.array_equal(mon['hits'],cp['hits'][4096:]);save(dest/'checkpoints'/f'{step:04}.npz',**{k:mon[k] for k in FIELDS+['hits']})
   if step in rec['parity_steps']:
    folder=dest/'parity'/f'{step:04}';folder.mkdir();native.save(folder/'graph.hnsw');native.verify(folder/'graph.hnsw',qrows[:16])
    parity={k:native.data(j,[np.int32,np.float32,np.int32,np.uint32,np.uint32][j]).reshape((-1,10) if j<2 else ((-1,3) if j==2 else (-1,))) for j,k in enumerate(FIELDS)}
    equal(parity,{k:mon[k][:16] for k in FIELDS});save(folder/'raw.npz',**parity);dump(folder/'identity.json',dict(topology_sha=top,W_sha=digest(P if rec['construction_only'] else W),graph_sha=sha(folder/'graph.hnsw')));parity_graphs+=1
   if step==200:break
   assert time.time()<QUERY_STOP and time.monotonic()-started<360
   st=step+1;t=np.load(src/'trajectory'/f'{st:04}.npz');slot=int(t['slot']);choice=int(t['choice']);assert W[slot].tobytes()==t['current_row'].tobytes() and top==str(t['current_topology_sha']) and raw_digest(train)==str(t['current_cache_sha'])
   before_train=train;before_mon=mon;W[slot]=t['next_row'];iscommit=rec['stage']=='E52';prefix='commit' if iscommit else 'accepted';top=str(t[prefix+'_topology_sha']);assert digest(W)==str(t[prefix+'_W_sha'])
   if choice>=0:
    seen_accepts+=1;branch=f'a{choice}_' if iscommit else f'd{choice}_';changed=t[branch+'rows'];train={k:v.copy() for k,v in train.items()}
    for k in ['ids','distances','entries','graph_ndc','hits']:train[k][changed]=t[branch+k]
    train['route_ndc']=t['route_ndc' if iscommit else 'd_route_ndc'][choice];assert np.array_equal(score(train['ids'][changed],gt[changed]),train['hits'][changed])
    set_graph(W,rec['construction_only'],top);mon=evaluate(mon,dest/'monitor_patches'/f'{st:04}.npz')
   else:assert np.array_equal(t['next_row'],t['current_row'])
   assert raw_digest(train)==str(t[prefix+'_cache_sha']);tr=phase_delta(train,before_train);mo=phase_delta(mon,before_mon);td.append(train['hits'].astype(np.int8)-before_train['hits'].astype(np.int8));md.append(mon['hits'].astype(np.int8)-before_mon['hits'].astype(np.int8))
   cpref='commit' if iscommit else 'accepted'
   for key in ['gain_hits','loss_hits','net_hits']:assert tr[key]==curve[step][cpref+'_'+key]
   row=dict(dataset=ds,stage=rec['stage'],seed=rec['seed'],step=st,slot=slot,hub_id=int(mapping[slot]),choice=choice,accepted=choice>=0,selected_delta_J=float(t['selected_delta_J']),
    train_cache_sha=raw_digest(train),monitor_cache_sha=raw_digest(mon),topology_sha=top,construction_W_sha=digest(W),score_W_sha=digest(P if rec['construction_only'] else W),
    **{'train_'+k:v for k,v in tr.items()},**{'monitor_'+k:v for k,v in mo.items()})
   steps.append(row);all_steps.append(row);t.close()
  assert seen_accepts==rec['accepted'];td=np.stack(td);md=np.stack(md);assert np.array_equal(td.sum(0),train['hits'].astype(int)-train_base['hits']) and np.array_equal(md.sum(0),mon['hits'].astype(int)-base['hits'])
  save(dest/'effects.npz',train_delta_hits=td,monitor_delta_hits=md);dump(dest/'steps.json',steps);dump(dest/'complete.json',dict(status='PASS',accepted=seen_accepts,steps=200,selected_step=rec['selected_step']))
  print('RUN_COMPLETE',ds,rec['key'],seen_accepts,native.stats(),flush=True)
 budget=next(x for x in read(O/'config.locked.json')['budgets'] if x['dataset']==ds);stats=native.stats();assert stats['NSG_calls']==normal_nsg+budget['parity_NSG'] and stats['HNSW_calls']==budget['HNSW'] and stats['builds']==budget['builds'] and native.installation_count()==budget['installations']
 assert normal_states==budget['normal_states'] and parity_graphs==budget['parity_graphs'] and len(all_steps)==1200 and stats['actual_threads']==1
 result=dict(status='PASS',dataset=ds,normal_new_NSG=normal_nsg,normal_states=normal_states,parity_graphs=parity_graphs,steps=1200,seconds=time.monotonic()-started,**stats)
 dump(O/'results'/ds/'query_complete.json',result);job.update(status='COMPLETE',actual=stats['NSG_calls'],completed_at=time.time());dump(ledger,jobs);print('DATASET_COMPLETE',json.dumps(result),flush=True)
finally:native.close()
