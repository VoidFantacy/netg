from common import *
import copy

assert not (O/"results/deployment_complete.json").exists()
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
    assert time.time()<QUERY_STOP and time.time()-t<1200 and rec['peak_RSS_KiB']<32*(1<<20) and rec['peak_threads']<=1
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
def point_data(out,m):
  p=out/m['name'];return dict(ids=np.fromfile(p/'ids.i32',np.int32).reshape(-1,10),distances=np.fromfile(p/'distances.f32',np.float32).reshape(-1,10),entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(-1,3),route_ndc=np.fromfile(p/'route_ndc.u32',np.uint32),graph_ndc=np.fromfile(p/'graph_ndc.u32',np.uint32))
def configuration(ds,phase,methods):
 old=read(O/'inputs'/ds/'config.json');dest=O/'inputs'/ds/phase;n={'fit_parity':128,'cal':1024,'validation':2000}[phase];reps=5 if phase=='validation' else 0
 c=dict(dataset=ds,split='E57_historical_'+phase,num_queries=n,dim=old['dim'],gt_k=100,base_count=2505000 if ds==DS[0] else 10000000,index_path=old['index_path'],
  queries_file=str(dest/'queries.f32'),gt_file=str(dest/'gt.i64'),row_ids=str(dest/'row_ids.i64'),threads=1,query_cpu=15,dataset_order=DS.index(ds),timing_repeats=reps,
  methods=[dict(m,L=L,name=m['model_name']+f'_L{L}',component_wall=False) for L in (LS if phase=='validation' else [128]) for m in methods])
 c['real_call_cap']=len(c['methods'])*((7 if reps else 2)*n+16);return c
pool=read(O/'inputs/candidate_pool.json')
for ds in DS:
 c=configuration(ds,'fit_parity',pool[ds]);out=O/'results'/('fit_parity_'+ds);result=execute('fit_parity_'+ds,c,out)
 for m in result['methods']:
  prior=dict(np.load(m['configuration']['prior_raw']));current=point_data(out,m);inds=np.r_[np.arange(64),np.arange(4096,4160)]
  for k in current:assert current[k].tobytes()==prior[k][inds].tobytes(),(ds,m['model_name'],k)
dump(O/'reviews/independent_fit_deployment.json',dict(status='PASS',queries=4864,methods=38,all_return_distance_entry_NDC_bits_equal=True))
for ds in DS:
 execute('cal_'+ds,configuration(ds,'cal',pool[ds]),O/'results'/('cal_'+ds))
selection={};matrices={}
for ds in DS:
 out=O/'results'/('cal_'+ds);result=read(out/'results.json');gt=np.fromfile(O/'inputs'/ds/'cal/gt.i64',np.int64).reshape(1024,100)
 base=point_data(out,next(m for m in result['methods'] if m['model_name']=='baseline'));base['hits']=score(base['ids'],gt);scores=[]
 for rank,m in enumerate(result['methods']):
  current=point_data(out,m);u=utility(current,base,gt);total=current['route_ndc'].astype(float)+current['graph_ndc'];dh=score(current['ids'],gt).astype(int)-base['hits']
  scores.append(dict(model=m['model_name'],mean_U=float(u.mean()),total_NDC=float(total.mean()),fixed_rank=rank,delta_recall_pp=float(dh.mean()*10),gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum())))
 best=lambda a:max(a,key=lambda x:(x['mean_U'],-x['total_NDC'],-x['fixed_rank']))
 selection[ds]=dict(best_all=best(scores),best_new=best(scores[1:]));dump(O/'results'/ds/'cal_selection_details.json',scores)
 old=read(E34/'inputs'/ds/'config.json');mm=[]
 for name in ['nsg','fast30k','gt10_hard']:
  mm.append(copy.deepcopy(next(m for m in old['methods'] if m['model_name']==name and m['L']==64)))
 if ds==DS[0]:mm.append(dict(pool[ds][0],model_name='baseline_soft'))
 chosen=next(m for m in pool[ds] if m['model_name']==selection[ds]['best_new']['model']);mm.append(dict(chosen,model_name='best_new',selected_source_name=chosen['model_name']))
 matrices[ds]=configuration(ds,'validation',mm)
dump(O/'results/cal_selection.json',dict(selection=selection,rule='cal mean U then lower total NDC then lower fixed pool index; default first',validation_measured=False))
dump(O/'inputs/final_matrix.json',matrices)
freeze(O/'reviews/selection_before_validation.json',[O/'results/cal_selection.json',O/'inputs/final_matrix.json']+[O/'results'/('cal_'+ds)/'results.json' for ds in DS]+[Path(m[k]) for ds in DS for m in matrices[ds]['methods'] if m['family']!='nsg' for k in ['W','graph_file','mapping','tie_ids']])
print('CAL_SELECTION',json.dumps(selection),flush=True)
sources={}
old_selection=read(E55/'results/cal_selection.json')['selection']
for ds in DS:
 changed=selection[ds]['best_new']['model']!=old_selection[ds]['best_new']['model']
 if changed:
  execute('validation_'+ds,matrices[ds],O/'results'/('validation_'+ds));folder=O/'results'/('validation_'+ds)
 else:
  folder=E55/'results'/('validation_'+ds)
  prior=read(folder/'config.json');chosen=next(m for m in prior['methods'] if m['model_name']=='best_new')
  assert chosen['selected_source_name']==selection[ds]['best_new']['model']
  assert [(m['name'],m['L']) for m in prior['methods']]==[(m['name'],m['L']) for m in matrices[ds]['methods']]
  assert all(sha(a[k])==sha(b[k]) for a,b in zip(prior['methods'],matrices[ds]['methods']) if a['family']!='nsg' for k in ['W','graph_file','mapping','tie_ids'])
 sources[ds]=dict(folder=str(folder),reused_E55=not changed,selection_model=selection[ds]['best_new']['model'],new_NSG=matrices[ds]['real_call_cap'] if changed else 0,wall_runs=25*5 if ds==DS[0] else 20*5)
dump(O/'results/final_sources.json',sources)
jobs=read(O/'logs/jobs.json');expected=88768+sum(x['new_NSG'] for x in sources.values());assert len(jobs)==4+sum(not x['reused_E55'] for x in sources.values()) and sum(x['actual'] for x in jobs)==expected
new_points=sum(25 if ds==DS[0] else 20 for ds in DS if not sources[ds]['reused_E55'])
dump(O/'results/deployment_complete.json',dict(status='PASS',fit_points=38,cal_points=38,final_points=45,new_final_points=new_points,NSG_calls=expected,wall_repeats_available=225,new_wall_repeats=new_points*5,selection=selection,final_sources=sources))
dump(O/'state.json',dict(status='EXPANDED_SELECTION_COMPLETE_ANALYSIS_PENDING',optimizer_updates=0,default_replaced=False,heldout_access=False))
