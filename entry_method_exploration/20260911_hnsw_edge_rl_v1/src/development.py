from common import *
import copy

def verify(dest,c):
 result=read(dest/'results.json');n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100);row=np.fromfile(c['row_ids'],np.int64)
 assert np.array_equal(row,np.fromfile(dest/'row_ids.i64',np.int64))
 th=read(dest/'thread_contract.json');assert th['process_threads']==th['actual_openmp_threads']==1 and th['cpu']==15
 assert result['threads']==1 and result['GT_opened_after_all_raw_search'] and result['physical_graph_calls']==c['real_call_cap']
 allpoints=[]
 for m in result['methods']:
  p=dest/m['name'];ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,10);entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3);hits=score(ids,gt)
  assert (ids>=0).all() and (ids<c['base_count']).all() and (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
  assert (np.diff(entries,axis=1)>0).all() and np.isin(entries,np.fromfile(c['hub_ids'],np.int32)).all()
  assert np.array_equal(hits,np.fromfile(p/'hits.u8',np.uint8));found=(ids[:,:,None]==gt[:,None,:10]).any(1)
  assert np.array_equal((found*(1<<np.arange(10))).sum(1),np.fromfile(p/'hitmask.u16',np.uint16))
  rn=np.fromfile(p/'route_ndc.u32',np.uint32);gn=np.fromfile(p/'graph_ndc.u32',np.uint32)
  assert abs(hits.mean()/10-m['recall_at_10'])<1e-12 and int(hits.sum())==m['total_hits']
  assert abs(rn.mean()-m['mean_route_ndc'])<1e-10 and abs(gn.mean()-m['mean_graph_ndc'])<1e-10 and abs(rn.mean()+gn.mean()-m['mean_total_ndc'])<1e-10
  assert m['repeated_output_parity'] and m['original_kernel_parity_queries']==16
  reps=c['timing_repeats'];assert len(m['qps_runs'])==reps and len(m['end_to_end_seconds'])==reps
  if reps:assert np.allclose(m['qps_runs'],n/np.array(m['end_to_end_seconds']),rtol=1e-12) and m['qps']==np.median(m['qps_runs'])
  else:assert m['qps'] is None
  if m['model_name']=='baseline':
   if c['split'] in ['cal','audit']:
    old=E32/'results'/(c['split']+'_'+c['dataset'])/(policy(c['dataset'])['model_name']+'_L128')
   else:
    old=E30/'results'/('validation_'+c['dataset'])/(policy(c['dataset'])['model_name']+f"_L{m['L']}")
   for fn,typ in [('ids.i32',np.int32),('entry_ids.i32',np.int32),('hits.u8',np.uint8),('route_ndc.u32',np.uint32),('graph_ndc.u32',np.uint32)]:assert np.array_equal(np.fromfile(old/fn,typ),np.fromfile(p/fn,typ)),(old,fn)
  allpoints.append(dict(name=m['name'],query_outputs=n,all_GT_rescored=True,original_kernel_queries=16))
 dump(dest/'independent_verification.json',dict(status='PASS',points=allpoints,thread_contract=True,default_previous_results_recovered=True))
 return result

def run(ds,split,selected=None):
 source=E30/'inputs'/ds/split/'config.json';c=read(source);c['base_count']=read(E24/'inputs'/ds/'prepared.json')['base_rows']
 n=c['num_queries'];assert n==(2000 if split=='validation' else 1024)
 fit_rows=np.fromfile(read(O/'inputs'/ds/'config.json')['row_ids'],np.int64);current=np.fromfile(c['row_ids'],np.int64);assert not np.intersect1d(fit_rows,current).size
 methods=[];reps=5 if split=='validation' else 0
 seeds=[selected] if selected is not None else SEEDS
 for L in ([64,128,256,400,800] if reps else [128]):
  p=policy(ds);p.update(graph_file=str(O/'inputs'/ds/'base.hnsw'),model_name='baseline',name=f'baseline_L{L}',L=L,component_wall=False);methods.append(p)
  for seed in seeds:
   for family,filename in [('rl','graph.hnsw'),('random','random_graph.hnsw')]:
    m=policy(ds);m.update(graph_file=str(O/'models'/ds/str(seed)/'selected'/filename),model_name=f'{family}_{seed}',name=f'{family}_{seed}_L{L}',L=L,component_wall=False);methods.append(m)
 c.update(methods=methods,timing_repeats=reps,dataset_order=DS.index(ds),threads=1,query_cpu=15,protocol_sha256=sha(O/'protocol.md'))
 c['real_call_cap']=len(methods)*((reps+2)*n+16);dest=O/'results'/f'{split}_{ds}';cfg=O/'inputs'/ds/f'eval_{split}.json'
 assert not dest.exists() and not cfg.exists();resources();dump(cfg,c)
 freeze(O/'reviews'/f'frozen_{split}_{ds}.json',[cfg]+[Path(c[k]) for k in ['queries_file','gt_file','row_ids','hub_ids']]+[Path(m['graph_file']) for m in methods])
 scope=read(O/'reviews/access_scope.json');scope[split+'_hash']=True;scope[split+'_decoded']=True;dump(O/'reviews/access_scope.json',scope)
 name=f'{split}_{ds}';reserve(name,c['real_call_cap']);cmd=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)];started=time.time()
 used=sum(j.get('seconds',0) for j in read(O/'logs/jobs.json'))
 record=dict(argv=cmd,rss_peak_kib=0,process_threads_max=0)
 with (O/'logs'/f'{name}.log').open('x') as f:
  p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env());record['pid']=p.pid
  try:
   while p.poll() is None:
    assert time.time()-started<min(1200,3600-used),'query time cap';resources()
    status=Path('/proc')/str(p.pid)/'status'
    if status.exists():
     for line in status.read_text().splitlines():
      if line.startswith('VmRSS:'):record['rss_peak_kib']=max(record['rss_peak_kib'],int(line.split()[1]));assert record['rss_peak_kib']<40*(1<<20)
      if line.startswith('Threads:'):record['process_threads_max']=max(record['process_threads_max'],int(line.split()[1]))
    time.sleep(.5)
   assert p.returncode==0,'query failed; see '+name+'.log'
  except BaseException:
   if p.poll() is None:p.terminate();p.wait(timeout=5)
   jobs=read(O/'logs/jobs.json');j=next(x for x in jobs if x['name']==name);j.update(status='FAILED',actual_calls=None,actual_calls_unknown=True,seconds=time.time()-started,**record);dump(O/'logs/jobs.json',jobs);raise
 result=verify(dest,c);finish(name,result['physical_graph_calls'],**record);print('REAL_EVAL_PASS',ds,split,result['physical_graph_calls'],flush=True);return result

def paired(ds,split):
 dest=O/'results'/f'{split}_{ds}';result=read(dest/'results.json');n=result['queries'];base=dest/'baseline_L128'
 bh=np.fromfile(base/'hits.u8',np.uint8).astype(float);bc=np.fromfile(base/'route_ndc.u32',np.uint32).astype(float)+np.fromfile(base/'graph_ndc.u32',np.uint32);rows=[]
 rng=np.random.default_rng(20260914);bootstrap=rng.integers(0,n,(2000,n))
 for m in result['methods']:
  if m['model_name']=='baseline':continue
  p=dest/m['name'];hits=np.fromfile(p/'hits.u8',np.uint8).astype(float);rn=np.fromfile(p/'route_ndc.u32',np.uint32);gn=np.fromfile(p/'graph_ndc.u32',np.uint32);cost=rn.astype(float)+gn
  delta=hits-bh;r=delta-.1*(cost/bc-1);ci=np.quantile(delta[bootstrap].mean(1)*10,[.025,.975])
  rows.append(dict(dataset=ds,split=split,method=m['model_name'],recall_pct=float(hits.mean()*10),baseline_recall_pct=float(bh.mean()*10),delta_pp=float(delta.mean()*10),ci95_pp=ci.tolist(),
   route_ndc=float(rn.mean()),graph_ndc=float(gn.mean()),total_ndc=float(cost.mean()),total_change_pct=float((cost.mean()/bc.mean()-1)*100),reward=float(r.mean()),
   gained_queries=int((delta>0).sum()),lost_queries=int((delta<0).sum()),entry_changed_queries=int((np.fromfile(p/'entry_ids.i32',np.int32).reshape(n,3)!=np.fromfile(base/'entry_ids.i32',np.int32).reshape(n,3)).any(1).sum())))
 return rows

if __name__=='__main__':
 assert read(O/'reviews/training_independent_verification.json')['status']=='PASS'
 check_freeze(O/'reviews/models_after_training.json');check_freeze(O/'reviews/initial_graphs.json')
 freeze(O/'reviews/deployment_implementation.json',[O/'src/development.py',O/'bin/evaluate',O/'src/evaluate.cpp',O/'src/benchmark_with_nsg.cpp',O/'src/legacy_reference.cpp'])
 selection={};allrows=[]
 for ds in DS:
  run(ds,'cal');cal=paired(ds,'cal');allrows+=cal;eligible=[r for r in cal if r['method'].startswith('rl_')]
  chosen=max(eligible,key=lambda r:(r['reward'],-int(r['method'].split('_')[1])));selection[ds]=int(chosen['method'].split('_')[1])
 dump(O/'results/cal_selection.json',dict(selection=selection,rule='maximum paired cal reward; smaller seed tie',audit_used=False))
 freeze(O/'reviews/selection_after_cal.json',[O/'results/cal_selection.json']+[O/'results'/f'cal_{ds}'/'results.json' for ds in DS])
 for ds in DS:
  run(ds,'audit');allrows+=paired(ds,'audit')
 dump(O/'results/development_paired.json',allrows);checks=[]
 for ds in DS:
  seed=selection[ds];rs=[r for r in allrows if r['dataset']==ds and r['method']==f'rl_{seed}'];random=[r for r in allrows if r['dataset']==ds and r['method']==f'random_{seed}']
  assert len(rs)==len(random)==2
  quality_cost=[]
  for r in rs:
   A=r['delta_pp']>=.05-1e-12 and r['total_change_pct']<=1+1e-12;B=r['delta_pp']>=-.02-1e-12 and r['total_change_pct']<=-1+1e-12
   quality_cost.append(dict(split=r['split'],path_A=A,path_B=B,pass_gate=A or B))
  beats_random=sum(r['reward'] for r in rs)>sum(r['reward'] for r in random)
  checks.append(dict(dataset=ds,seed=seed,quality_cost=quality_cost,combined_reward_beats_random=beats_random,pass_gate=all(r['pass_gate'] for r in quality_cost) and beats_random))
 passed=all(x['pass_gate'] for x in checks);gate=dict(status='PASS_CONDITIONAL_PERFORMANCE' if passed else 'STOP_DEVELOPMENT_GATE',checks=checks)
 dump(O/'results/development_gate.json',gate)
 if passed:
  for ds in DS:run(ds,'validation',selection[ds])
  status='COMPLETE_WITH_EXPLORATORY_PERFORMANCE'
 else:status='COMPLETE_DEVELOPMENT_STOP'
 dump(O/'state.json',dict(status=status,training_runs=4,optimizer_updates=2400,development_gate=gate['status'],QPS_points=30 if passed else 0,
  NSG_calls=sum(j.get('actual_calls',0) for j in read(O/'logs/jobs.json')),heldout_access=False))
 print('DEVELOPMENT_COMPLETE',gate,flush=True)
