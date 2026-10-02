from common import *
import subprocess,shutil,signal
assert not (RUN/'reviews/execution_started.json').exists(),'preserve previous run'
deadline();protected_check();started=time.time()
dump(RUN/'reviews/execution_started.json',dict(created_unix=started,protocol=identity(RUN/'protocol.md'),research=identity(RUN/'research.md'),config=identity(RUN/'config.locked.json')))
jobs=[]
def execute(argv,logname,timeout,kind,calls=0):
 deadline();assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
 remaining=LOCK['deadline_unix']-time.time();assert remaining>timeout+5,'not enough time for bounded job'
 assert sum(j['reserved_calls'] for j in jobs)+calls<=LOCK['max_NSG_calls']
 job=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout,reserved_calls=calls);jobs.append(job);dump(RUN/'reviews/jobs.json',jobs)
 with (RUN/'logs'/logname).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_DYNAMIC='FALSE'),start_new_session=True);job.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(RUN/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   job['timeout']=True
 job.update(exit_code=p.returncode,seconds=time.time()-job['started_unix'],finished_unix=time.time());dump(RUN/'reviews/jobs.json',jobs);assert p.returncode==0,job
 return job
try:
 old=Path(LOCK['reference_E106']);build=read(old/'reviews/build.json')['argv'];argv=[x.replace(str(old),str(RUN)) for x in build]
 dump(RUN/'reviews/build_source_lock.json',dict(files=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]))
 execute(argv,'build.log',120,'build')
 execute(['taskset','-c','15',str(RUN/'bin/evaluate'),'counterexample',str(RUN/'reviews/counterexample.json')],'counterexample.log',20,'synthetic',0)
 assert read(RUN/'reviews/counterexample.json')['status']=='PASS'
 methods=LOCK['methods'];models=[]
 for ds,c in LOCK['datasets'].items():
  raw=np.fromfile(Path(c['fit_input'])/'raw_hubs.f32','<f4').reshape(c['H'],c['dimension']);unit=raw/np.linalg.norm(raw,axis=1,keepdims=True)
  p=RUN/'models'/(ds+'.UnitHub.W.f32');unit.astype('<f4').tofile(p);models.append(identity(p))
  for m in methods[ds]:
   if m.get('normalize_W'):m.update(W=str(p),normalize_W=False)
 dump(RUN/'reviews/frozen_models.json',dict(created_unix=time.time(),files=models,methods=methods,evaluation_payload_access=False))
 freeze=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[identity(RUN/n) for n in ['config.locked.json','research.md','protocol.md','bin/evaluate']]
 dump(RUN/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=freeze))
 configs=[]
 for ds,c in LOCK['datasets'].items():
  meta=read(c['evaluation_manifest']);assert sha(meta['base'])==meta['base_sha256'] and sha(c['evaluation_queries'])==meta['query_sha256'] and sha(c['evaluation_GT'])==meta['GT_sha256']
  configs.append(dict(dataset=ds,dimension=c['dimension'],H=c['H'],n=4096,queries=c['evaluation_queries'],GT=c['evaluation_GT'],rows=c['source_rows'],hub_ids=str(Path(c['fit_input'])/'hub_ids.i32'),index=c['index'],base_n=c['base_n'],base=meta['base'],threads=1,methods=methods[ds],reference=c['evaluation_reference'],reference_method=c['default']['name'],reference_E106=str(old),E106_family='Soft' if ds.startswith('webvid') else 'Hard',deadline_unix=LOCK['deadline_unix'],seconds_cap=LOCK['job_seconds_cap'],max_search_calls=LOCK['max_NSG_calls']))
 dump(RUN/'reviews/inputs_validated.json',dict(created_unix=time.time(),configs=configs,GT_base_hashes_revalidated=True,exposure='E105 exposed development, no new blind data'))
 for smoke in [True,False]:
  for c in configs:
   current=dict(c,n=16 if smoke else 4096,smoke=smoke,K_L={'1':[128],'100':[128]} if smoke else LOCK['K_L'])
   calls=current['n']*len(current['methods'])*sum(len(v) for v in current['K_L'].values())*(3 if smoke else 2);current['expected_search_calls']=calls
   kind='smoke' if smoke else 'main';path=RUN/'reviews'/(kind+'_'+c['dataset']+'.json');dump(path,current);out=RUN/('reviews' if smoke else 'results')/(kind+'_'+c['dataset'])
   dump(RUN/'state.json',dict(status='RUNNING_'+kind.upper(),dataset=c['dataset'],pending=['remaining searches','analysis']))
   job=execute(['taskset','-c','15',str(RUN/'bin/evaluate'),str(path),str(out)],kind+'_'+c['dataset']+'.log',LOCK['job_seconds_cap'],kind,calls)
   result=read(out/'complete.json');assert result['calls']==calls and result['threads']==1 and result['cpu']==15;job['complete']=result;dump(RUN/'reviews/jobs.json',jobs)
   assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<=LOCK['max_new_bytes']
   print(kind,c['dataset'],'completed',round(job['seconds'],2),flush=True)
  if smoke:dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',legacy_kernel_bit_parity=True))
 protected_check()
 for r in freeze+models:assert sha(r['path'])==r['sha256'],r['path']
 assert sum(j['reserved_calls'] for j in jobs)==LOCK['expected_NSG_calls']
 dump(RUN/'reviews/search_complete.json',dict(status='PASS',calls=LOCK['expected_NSG_calls'],synthetic_calls=2,seconds=time.time()-started,search_job_seconds=sum(j['seconds'] for j in jobs if j['reserved_calls']),formal_QPS=False))
 dump(RUN/'state.json',dict(status='FACTORIAL_SEARCH_COMPLETE',pending=['independent analysis','theory interpretation','next-method decision']))
except Exception as e:
 dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect preserved error; do not blindly restart']))
 raise
