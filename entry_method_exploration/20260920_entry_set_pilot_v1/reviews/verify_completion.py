"""Independent audit, run only after native measurement jobs terminate."""
from pathlib import Path
import json,hashlib,math,csv,time
import numpy as np
RUN=Path(__file__).resolve().parents[1];ROOT=RUN.parents[1]
def read(p):return json.loads(Path(p).read_text())
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
started=time.time();lock=read(RUN/'config.locked.json');state=read(RUN/'state.json');assert state['status']=='MEASUREMENTS_COMPLETE'
jobs=read(RUN/'reviews/jobs.json');assert all(j['exit_code']==0 for j in jobs)
for j in jobs:
 p=Path('/proc')/str(j['pid'])/'cmdline'
 assert not p.exists() or str(RUN).encode() not in p.read_bytes(),j['pid']
for f in read(RUN/'reviews/source_frozen.json')['files']:assert digest(f['path'])==f['sha256'],f['path']
for p,h in read(RUN/'reviews/protected_before.json').items():assert digest(p)==h,p
for f in read(RUN/'reviews/models_frozen.json')['files']:assert digest(f['path'])==f['sha256']
assert (RUN/'src/kernels.hpp').read_bytes()==(ROOT/'entry_method_exploration/20260920_entry_id_pilot_v1/src/kernels.hpp').read_bytes()

cost=[]
for j in jobs:
 cfg=read(j['argv'][-2]);done=read(Path(j['argv'][-1])/'complete.json');n=cfg['n']
 if cfg['mode']=='labels':
  parity=4*math.ceil(n/625);expected=n*5*(cfg['label_repeats']+1)+2*parity;router=n*2+n*5*(cfg['label_repeats']+1);features=3*n*(1+4*(cfg['label_repeats']+1))
 else:
  nm=len(cfg['methods']);npnt=len(cfg['points']);nf=sum(m.get('features',False) or 'tree' in m for m in cfg['methods']);parity=min(n,32)*nm*npnt
  expected=n*nm*npnt*(cfg['repeats']+2)+parity;router=2*n+n*nm*npnt*(cfg['repeats']+2);features=3*n+3*n*nf*npnt*(cfg['repeats']+2)
 assert done['search_calls']==expected and done['router_calls']==router and done['feature_distance_calls']==features
 assert done['linked_parity_queries']==parity and done['threads']==1
 cost.append(dict(kind=j['kind'],dataset=j['dataset'],search_calls=expected,router_calls=router,feature_distance_calls=features,seconds=j['seconds']))

metrics=read(RUN/'results/metrics.json');paired=read(RUN/'results/paired.json');model_summary=[];feature_checks=[];assets=[]
for ds,c in lock['datasets'].items():
 d=c['dimension'];doc=read(RUN/'models'/ds/'models.json');freeze=read(RUN/'reviews/models_frozen.json')['created_unix'];assert all(j['started_unix']>freeze for j in jobs if j['kind']=='accept')
 fit=RUN/'inputs'/ds/'fit';accept=RUN/'inputs'/ds/'accept'
 assert not set(read(fit/'query_hashes.json'))&set(read(accept/'query_hashes.json'))
 for role in ['fit','accept']:
  inp=RUN/'inputs'/ds/role;lo,hi=lock[role+'_positions'];n=hi-lo
  rows=np.fromfile(inp/'row_ids.i64',np.int64);assert np.array_equal(rows,np.arange(10000+lo,10000+hi))
  manifest=read(inp/'manifest.json')
  for f in manifest['files']+manifest['assets']:assert digest(f['path'])==f['sha256'];assets.append(f)
  q=np.fromfile(inp/'queries.f32',np.float32).reshape(n,d);gt=np.fromfile(inp/'gt.i64',np.int64).reshape(n,100)
  source=c['fit_source'];sq=np.memmap(source['queries_file'],np.float32,mode='r',shape=(20000,d))[lo:hi];sg=np.memmap(source['gt_file'],np.int64,mode='r',shape=(20000,100))[lo:hi]
  assert q.tobytes()==sq.tobytes() and gt.tobytes()==sg.tobytes();assert all(len(set(g))==100 for g in gt)
  p=RUN/'results'/ds/('labels' if role=='fit' else 'accept');X=np.fromfile(p/'features.f64',np.float64).reshape(n,6);s=np.fromfile(p/'profile_scores.f32',np.float32).reshape(n,3).astype(float);b=np.fromfile(p/'base_scores.f32',np.float32).reshape(n,3).astype(float);E=np.fromfile(p/'ranked_entries.i32',np.int32).reshape(n,3)
  assert np.all(s[:,:2]>=s[:,1:]);ps=np.sqrt((s*s).sum(1))+1e-12;bs=np.sqrt((b*b).sum(1))+1e-12;best=np.array([sorted(range(3),key=lambda j:(-v[j],ids[j]))[0] for v,ids in zip(b,E)])
  actual=np.column_stack(((s[:,0]-s[:,1])/ps,(s[:,1]-s[:,2])/ps,(b[:,0]-b[:,1])/bs,(b[:,0]-b[:,2])/bs,(b[:,1]-b[:,2])/bs,best));assert np.allclose(X,actual,rtol=1e-13,atol=1e-13)
  # Independently compare deterministic sampled feature scores with original vectors.
  base=np.memmap(c['base'],np.float32,mode='r',shape=(c['base_n'],d+1));ids=np.fromfile(c['anchor']['ids'],np.int32);W=np.fromfile(c['anchor']['W'],np.float32).reshape(-1,d);slot={int(e):i for i,e in enumerate(ids)}
  for i in np.linspace(0,n-1,32,dtype=int):
   query=q[i].astype(float)
   for j,e in enumerate(E[i]):
    bv=np.asarray(base[e,1:],float);wv=W[slot[int(e)]].astype(float)
    for observed,vec in [(b[i,j],bv),(s[i,j],wv)]:
     tol=8*np.finfo(np.float32).eps*(d*np.abs(query*vec).sum()+1)
     assert abs(observed-query@vec)<=tol
  feature_checks.append(dict(dataset=ds,role=role,all_feature_rows=n,independent_vector_pairs=192))
  for m in doc['methods']:
   if 'tree' not in m:continue
   nodes=m['tree'];choices=[];leaf=[]
   for x in X:
    j=0;depth=0
    while nodes[j]['feature']>=0:
     f=nodes[j]['feature'];j=nodes[j]['left'] if x[f]<=nodes[j]['threshold'] else nodes[j]['right'];depth+=1;assert depth<=2
    choices.append(nodes[j]['action']);leaf.append(j)
   choices=np.array(choices);leaf=np.array(leaf)
   if role=='fit':
    assert np.array_equal(choices,np.fromfile(RUN/'models'/ds/f'{m["name"]}.fit_actions.i32',np.int32))
    H=np.fromfile(RUN/'models'/ds/'fit_hits.i16',np.int16).reshape(n,4,2).astype(float);H[:,:,1]/=100;delta=H-H[:,:1];dt=np.fromfile(RUN/'models'/ds/'fit_delta_time.f64',np.float64).reshape(n,4);utility=delta.mean(2)
    if m['name']!='RecallTree':utility=utility-lock['cost_weight']*dt/doc['fit_baseline_seconds']
    if m['name']=='ShuffledTree':utility=utility[np.fromfile(RUN/'models'/ds/'shuffle.i32',np.int32)]
    for j in set(leaf):
     ix=leaf==j;node=nodes[j];assert ix.sum()>=lock['min_leaf'];assert np.argmax(utility[ix].sum(0))==node['action'];assert node['support']==ix.sum()
     assert np.allclose(node['estimates']['delta_recall'],delta[ix].mean(0)) and np.allclose(node['estimates']['delta_seconds'],dt[ix].mean(0))
   else:
    for K in [1,100]:assert np.array_equal(choices,np.fromfile(p/f'{m["name"]}_K{K}_L128/actions.i32',np.int32))
   model_summary.append(dict(dataset=ds,role=role,method=m['name'],actions=np.bincount(choices,minlength=4).tolist(),leaves=len(set(leaf))))
  if role=='fit':
   T=np.fromfile(p/'seconds.f64',np.float64).reshape(n,5,4);assert np.isfinite(T).all() and np.all(T>0)
   schedule=read(p/'timing_schedule.json');assert len(schedule)==math.ceil(n/256)*5*4
   for rep in range(4):
    for lo2 in range(0,n,256):
     a=[r['variant'] for r in schedule if r['rep']==rep and r['block_start']==lo2];assert a==[(z+rep+lo2//256)%5 for z in range(5)]
  else:
   truths=[set(g.tolist()) for g in gt];one=gt[:,0];allh={}
   for K in [1,100]:
    for m in doc['methods']:
     f=p/f'{m["name"]}_K{K}_L128';I=np.fromfile(f/'ids.i32',np.int32).reshape(n,K);h=np.array([int(a[0]==t) for a,t in zip(I,one)]) if K==1 else np.array([sum(int(e) in t for e in a) for a,t in zip(I,truths)])
     row=next(v for v in metrics if v['dataset']==ds and v['method']==m['name'] and v['K']==K);assert abs(row['recall_pct']-100*h.sum()/(n*K))<1e-10;assert row['zero_hit_queries']==int((h==0).sum());times=read(f/'complete.json')['seconds'];assert len(times)==3 and abs(row['qps']-n/np.mean(times))<1e-8;allh[m['name'],K]=h
   for v in paired:
    if v['dataset']!=ds:continue
    k=v['K'];a=allh[v['method'],k];b=allh[v['reference'],k];assert v['net_hits']==int((a-b).sum());assert v['rescued_zero']==int(((b==0)&(a>0)).sum()) and v['new_zero']==int(((b>0)&(a==0)).sum())
   oracle={}
   for K in [1,100]:
    mat=np.column_stack([allh[nm,K] for nm in ['GT10','Single1','Single2','Single3']]);best=mat.max(1);basehit=mat[:,0];oracle[str(K)]=dict(oracle_recall_pct=float(100*best.mean()/K),gain_vs_GT10_pp=float(100*(best-basehit).mean()/K),gain_vs_best_fixed_pp=float(100*(best.mean()-mat.mean(0).max())/K),nonconstant_queries=int(np.any(mat!=mat[:,:1],axis=1).sum()))
   dump(RUN/'results'/f'{ds}.action_oracle.json',oracle)
totals={k:sum(r[k] for r in cost) for k in ['search_calls','router_calls','feature_distance_calls']};record=read(RUN/'reviews/execution_complete.json')
for k,v in totals.items():assert record[k]==v
assert totals['search_calls']<=lock['max_search_calls']
dump(RUN/'reviews/cost_ledger.json',dict(jobs=cost,totals=totals,controller_seconds=record['seconds'],compile_seconds=sum(read(RUN/'reviews'/x)['seconds'] for x in ['build.json','build_v2.json']),model_training_seconds=read(RUN/'reviews/models_frozen.json')['training_seconds'],max_observed_rss_bytes=max(v['rss'] for v in read(RUN/'reviews/resources.json')),new_gt=0,new_graph=0,policy_tree_fits=6))
dump(RUN/'reviews/independent_numeric_audit.json',dict(status='PASS',seconds=time.time()-started,features=feature_checks,models=model_summary,input_files_checked=len(assets),native_calls_independently_counted=totals,all_source_model_and_protected_hashes_unchanged=True,acceptance_returns_independently_rescored=True,no_active_native_processes=True))
print(json.dumps(dict(status='PASS',totals=totals,model_summary=model_summary),ensure_ascii=False,indent=2))
