from common import *
import subprocess,shutil,signal
assert read(Path(LOCK['reference_E107'])/'complete.json')['status']=='COMPLETE'
assert not (RUN/'reviews/execution_started.json').exists(),'preserve previous execution'
deadline();protected_check();started=time.time();jobs=[]
dump(RUN/'reviews/execution_started.json',dict(created_unix=started,source=identity(Path(__file__)),protocol=identity(RUN/'protocol.md'),config=identity(RUN/'config.locked.json')))
def execute(argv,logname,timeout,kind,calls=0):
 deadline();assert LOCK['deadline_unix']-time.time()>timeout+5
 assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
 assert sum(j['reserved_calls'] for j in jobs)+calls<=LOCK['max_NSG_calls']
 assert read(TB/'state.json')['completed_NSG_calls']+LOCK['max_NSG_calls']<=read(TB/'config.locked.json')['resources']['max_NSG_calls']
 job=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout,reserved_calls=calls);jobs.append(job);dump(RUN/'reviews/jobs.json',jobs)
 with (RUN/'logs'/logname).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_DYNAMIC='FALSE'),start_new_session=True);job.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(RUN/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   job['timeout']=True
 job.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-job['started_unix']);dump(RUN/'reviews/jobs.json',jobs);assert p.returncode==0,job
 return job
try:
 old=Path(LOCK['reference_E107']);build=read(old/'reviews/jobs.json')[0]['argv'];argv=[x.replace(str(old),str(RUN)) for x in build]
 inherited=[]
 for p in (RUN/'src/common').rglob('*'):
  if p.is_file() and '__pycache__' not in str(p):assert sha(p)==sha(old/'src/common'/p.relative_to(RUN/'src/common'));inherited.append(identity(p))
 for n in ['kernels.hpp','search_core.hpp']:assert sha(RUN/'src'/n)==sha(old/'src'/n)
 dump(RUN/'reviews/build_source_lock.json',dict(files=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)],inherited_byte_parity=True))
 execute(argv,'build.log',120,'compile')
 configs=[]
 for order,(ds,c) in enumerate(LOCK['datasets'].items()):
  methods=[dict(name='GT10Default',W=c['default']['W'],ids=c['default']['ids'],graph=c['default']['graph'],new_graph=False),dict(name='GT10Rebuilt',W=c['default']['W'],ids=c['default']['ids'],graph=str(RUN/'models'/ds/'GT10Rebuilt.hnsw'),new_graph=True),dict(name='UnitHub',W=c['unit_W'],ids=c['default']['ids'],graph=str(RUN/'models'/ds/'UnitHub.hnsw'),new_graph=True)]
  meta=read(c['evaluation_manifest']);configs.append(dict(dataset=ds,dimension=c['dimension'],H=c['H'],base_n=c['base_n'],index=c['index'],base=meta['base'],queries=c['evaluation_queries'],GT=c['evaluation_GT'],source_rows=c['source_rows'],methods=methods,threads=1,dataset_order=order,reference=c['evaluation_reference'],reference_method=c['default']['name'],max_search_calls=LOCK['max_NSG_calls'],seconds_cap=LOCK['job_seconds_cap'],deadline_unix=LOCK['deadline_unix']))
 build_config=RUN/'reviews/build_graphs_config.json';dump(build_config,dict(configs=configs,M=16,efConstruction=200,graph_seed=LOCK['graph_seed']))
 execute(['taskset','-c','15',str(RUN/'bin/evaluate'),'build',str(build_config),str(RUN/'reviews/graphs_built.json')],'graphs.log',120,'graphs')
 assert read(RUN/'reviews/graphs_built.json')['new_graphs']==4
 model_files=[identity(p) for p in (RUN/'models').rglob('*.hnsw')];assert len(model_files)==4
 dump(RUN/'reviews/models_frozen.json',dict(created_unix=time.time(),files=model_files,configs=configs,query_payload_access=False))
 freeze=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[identity(RUN/n) for n in ['config.locked.json','protocol.md','bin/evaluate']]
 dump(RUN/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=freeze))
 for c in LOCK['datasets'].values():
  meta=read(c['evaluation_manifest']);assert sha(meta['base'])==meta['base_sha256'] and sha(c['evaluation_queries'])==meta['query_sha256'] and sha(c['evaluation_GT'])==meta['GT_sha256']
 dump(RUN/'reviews/inputs_validated.json',dict(created_unix=time.time(),base_query_GT_hash_revalidated=True,query_payload_after_model_freeze=True,exposure='E105 exposed development; no heldout access'))
 for smoke in [True,False]:
  for c in configs:
   points=[dict(K=k,L=128) for k in [1,100]] if smoke else [dict(K=int(k),L=L) for k,ls in LOCK['K_L'].items() for L in ls]
   current=dict(c,smoke=smoke,n=16 if smoke else 4096,points=points);calls=current['n']*3*len(points)*(4 if smoke else 5);current['expected_search_calls']=calls
   kind='smoke' if smoke else 'formal';cfg=RUN/'reviews'/(kind+'_'+c['dataset']+'.json');dump(cfg,current);out=RUN/('reviews' if smoke else 'results')/(kind+'_'+c['dataset'])
   dump(RUN/'state.json',dict(status='RUNNING_'+kind.upper(),dataset=c['dataset'],pending=['remaining matrix','paired quality and wall analysis']))
   job=execute(['taskset','-c','15',str(RUN/'bin/evaluate'),str(cfg),str(out)],kind+'_'+c['dataset']+'.log',LOCK['job_seconds_cap'],kind,calls)
   done=read(out/'complete.json');assert done['NSG_calls']==calls and done['threads']==1 and done['cpu']==15;job['complete']=done;dump(RUN/'reviews/jobs.json',jobs)
   assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<=LOCK['max_new_bytes']
   assert sum(p.stat().st_size for p in TB.rglob('*') if p.is_file())<=read(TB/'config.locked.json')['resources']['max_new_bytes']
   print(kind,c['dataset'],'completed',round(job['seconds'],2),flush=True)
  if smoke:dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',linked_E99_bits_and_NDC=True,default_E105_restored=True))
 protected_check()
 for r in freeze+model_files:assert sha(r['path'])==r['sha256'],r['path']
 calls=sum(j['reserved_calls'] for j in jobs);assert calls==LOCK['expected_NSG_calls']
 dump(RUN/'reviews/search_complete.json',dict(status='PASS',NSG_calls=calls,router_calls=sum(j['complete']['router_calls'] for j in jobs if j['reserved_calls']),seconds=time.time()-started,new_graphs=4,formal_points=54,formal_wall_rounds=162,new_GT=0,new_training=0))
 dump(RUN/'state.json',dict(status='ONLINE_MATRIX_COMPLETE',pending=['independent analysis','report','closeout']))
except Exception as e:
 dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect preserved error; do not blindly restart']));raise
