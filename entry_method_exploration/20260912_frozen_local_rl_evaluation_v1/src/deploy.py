from common import *
import copy

assert read(E47/'reviews/training_verification.json')['status']=='PASS'
assert not (O/'results/deployment_complete.json').exists()
def execute(name,c,out):
 resources();assert time.time()<QUERY_STOP-600;check(O/'reviews/prequery_freeze.json');cfg=O/'inputs/jobs'/f'{name}.json';assert not cfg.exists();dump(cfg,c)
 # Freeze every actual input/model before its first query, including newly exposed cal/audit.
 files=[cfg,O/'bin/evaluate',O/'src/deploy.py',O/'protocol.md']+[Path(c[k]) for k in ['queries_file','gt_file','row_ids']]
 for m in c['methods']:
  if m['family']!='nsg':files.extend(Path(m[k]) for k in ['W','mapping','tie_ids','graph_file'])
 freeze(O/'reviews'/f'{name}_before.json',files);reserve(name,c['real_call_cap']);t=time.time();rec=dict(pid=None,peak_RSS_KiB=0,peak_threads=0)
 with (O/'logs'/f'{name}.log').open('x') as log:
  proc=subprocess.Popen(['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(out)],env=env(),stdout=log,stderr=subprocess.STDOUT);rec['pid']=proc.pid
  try:
   while proc.poll() is None:
    try:
     a=dict(line.split(':',1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line)
     rec['peak_RSS_KiB']=max(rec['peak_RSS_KiB'],int(a.get('VmRSS','0 kB').split()[0]));rec['peak_threads']=max(rec['peak_threads'],int(a['Threads']))
    except FileNotFoundError:pass
    assert time.time()<QUERY_STOP and time.time()-t<600 and rec['peak_RSS_KiB']<32*(1<<20) and rec['peak_threads']<=1
    resources();dump(O/'logs/active_deployment.json',dict(name=name,started_at=t,**rec))
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   assert proc.returncode==0,'see '+str(log.name)
  except BaseException:
   if proc.poll() is None:proc.kill();proc.wait()
   dump(O/'logs/deployment_failure.json',dict(name=name,returncode=proc.returncode,**rec));raise
 result=read(out/'results.json');assert result['physical_graph_calls']==c['real_call_cap']
 finish(name,result['physical_graph_calls'],seconds=time.time()-t,**rec);print('DEPLOYMENT_COMPLETE',name,len(c['methods']),flush=True)
 return result
def models(ds):
 old=read(O/'inputs'/ds/'config.json');base=dict(old['original_policy'],model_name='baseline',graph_file=str(E37/'results'/ds/'baseline.hnsw'),W=old['P'],mapping=old['hub_ids'],tie_ids=old['hub_ids'])
 result=[base]
 for arm in ARMS:
  for seed in SEEDS:
   folder=E47/'models'/ds/f'{arm}_{seed}'/'selected';result.append(dict(base,model_name=f'{arm}_{seed}',W=str(folder/'W.f32'),graph_file=str(folder/'graph.hnsw')))
 return result
def configuration(ds,phase,methods,reps=0):
 old=read(O/'inputs'/ds/'config.json');dest=O/'inputs'/ds/phase;dest.mkdir()
 if phase=='fit_parity':
  src=old;rows=np.r_[np.arange(64),np.arange(4096,4160)];n=128
 else:src={k:str(E37/'inputs'/ds/phase/name) for k,name in [('queries_file','queries.f32'),('gt_file','gt.i64'),('row_ids','row_ids.i64')]};rows=np.arange(1024);n=1024
 source=[]
 for key,dt,width,name in [('queries_file',np.float32,old['dim'],'queries.f32'),('gt_file',np.int64,100,'gt.i64'),('row_ids',np.int64,1,'row_ids.i64')]:
  path=Path(src[key]);a=np.fromfile(path,dt).reshape(-1,width);a[rows].tofile(dest/name);source.append(identity(path))
 source_rows=np.fromfile(dest/'row_ids.i64',np.int64);assert len(np.unique(source_rows))==n
 if phase!='fit_parity':
  assert not np.intersect1d(source_rows,np.fromfile(old['row_ids'],np.int64)).size
 if phase=='audit':assert not np.intersect1d(source_rows,np.fromfile(O/'inputs'/ds/'cal/row_ids.i64',np.int64)).size
 dump(dest/'source.json',dict(files=source,historical=True,selected_rows=rows.tolist(),query_count=n))
 c=dict(dataset=ds,split='E49_historical_'+phase,num_queries=n,dim=old['dim'],gt_k=100,base_count=2505000 if ds==DS[0] else 10000000,index_path=old['index_path'],
  queries_file=str(dest/'queries.f32'),gt_file=str(dest/'gt.i64'),row_ids=str(dest/'row_ids.i64'),threads=1,query_cpu=15,dataset_order=DS.index(ds),timing_repeats=reps,
  methods=[dict(m,L=128,name=m['model_name']+'_L128',component_wall=False) for m in methods])
 c['real_call_cap']=len(methods)*((reps+2 if reps else 2)*n+16);return c
def point_data(out,m):
 p=out/m['name'];return dict(ids=np.fromfile(p/'ids.i32',np.int32).reshape(-1,10),distances=np.fromfile(p/'distances.f32',np.float32).reshape(-1,10),entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(-1,3),route_ndc=np.fromfile(p/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(p/'graph_ndc.u32',np.uint32))
for ds in DS:
 mm=models(ds);c=configuration(ds,'fit_parity',mm);out=O/'results'/('fit_parity_'+ds);result=execute('fit_parity_'+ds,c,out)
 for m in result['methods']:
  current=point_data(out,m)
  if m['model_name']=='baseline':prior=dict(np.load(E37/'results'/ds/'baseline.npz'));inds=np.r_[np.arange(64),np.arange(4096,4160)]
  else:
   folder=E47/'models'/ds/m['model_name'];step=read(folder/'model.json')['selected_step'];prior=dict(np.load(folder/'checkpoints'/f'{step:04}.npz'));inds=np.r_[np.arange(64),np.arange(4096,4160)]
  for k in current:assert np.array_equal(current[k].view(np.uint8),prior[k][inds].copy().view(np.uint8)),(ds,m['model_name'],k)
dump(O/'reviews/independent_fit_deployment.json',dict(status='PASS',queries=1280,methods=10,all_return_distance_entry_NDC_bits_equal=True))
for ds in DS:
 c=configuration(ds,'cal',models(ds));execute('cal_'+ds,c,O/'results'/('cal_'+ds))
selection={}
for ds in DS:
 out=O/'results'/('cal_'+ds);result=read(out/'results.json');gt=np.fromfile(O/'inputs'/ds/'cal/gt.i64',np.int64).reshape(1024,100)
 base=point_data(out,next(m for m in result['methods'] if m['model_name']=='baseline'));base['hits']=score(base['ids'],gt);scores=[]
 for m in result['methods']:
  if m['model_name']=='baseline':continue
  current=point_data(out,m);u=utility(current,base,gt);total=current['route_ndc'].astype(float)+current['graph_ndc']
  scores.append(dict(model=m['model_name'],mean_U=float(u.mean()),total_NDC=float(total.mean()),seed=int(m['model_name'].split('_')[-1])))
 selection[ds]={arm:max([x for x in scores if x['model'].startswith(arm+'_')],key=lambda x:(x['mean_U'],-x['total_NDC'],-x['seed'])) for arm in ARMS}
 dump(O/'results'/ds/'cal_selection_details.json',scores)
dump(O/'results/cal_selection.json',dict(selection=selection,rule='cal mean U then lower total NDC then smaller seed',audit_prepared=False))
freeze(O/'reviews/selection_before_audit.json',[O/'results/cal_selection.json']+[p for p in (E47/'models').rglob('*') if p.is_file() and '/selected/' in str(p)]+[O/'results'/('cal_'+ds)/'results.json' for ds in DS])
for ds in DS:
 c=configuration(ds,'audit',models(ds));execute('audit_'+ds,c,O/'results'/('audit_'+ds))
for ds in DS:
 c=read(O/'inputs/jobs'/('audit_'+ds+'.json'));c['split']='E49_historical_audit_frontier';c['timing_repeats']=5
 mm=models(ds);chosen=['baseline']+[selection[ds][arm]['model'] for arm in ARMS];mm=[m for m in mm if m['model_name'] in chosen]
 old=read(E34/'inputs'/ds/'config.json')
 for key in ['nsg','fast30k']:
  p=copy.deepcopy(next(m for m in old['methods'] if m['model_name']==key and m['L']==64));p['component_wall']=False;mm.insert(0,p)
 c['methods']=[dict(m,L=L,name=m['model_name']+f'_L{L}',component_wall=L==128) for L in LS for m in mm]
 c['real_call_cap']=sum(7*1024+16+(2048 if m['component_wall'] else 0) for m in c['methods'])
 execute('frontier_'+ds,c,O/'results'/('frontier_'+ds))
dump(O/'results/deployment_complete.json',dict(status='PASS',fit_points=10,cal_points=10,audit_points=10,frontier_points=50,wall_repeats=250,selection=selection))
dump(O/'state.json',dict(status='DEPLOYMENT_COMPLETE_ANALYSIS_PENDING',training_runs=0,optimizer_updates=0,default_replaced=False,validation_heldout_input_access=False))
