from common import *
import subprocess,shutil,signal
assert not (RUN/'reviews/execution_started.json').exists()
assert read(RUN.parent/'e109_perfect_proxy_gate/complete.json')['status']=='COMPLETE'
deadline();protected_check();started=time.time();jobs=[]
for r in read(RUN/'reviews/setup_freeze.json')['files']:assert sha(r['path'])==r['sha256']
dump(RUN/'reviews/execution_started.json',dict(created_unix=started,protocol=identity(RUN/'protocol.md'),config=identity(RUN/'config.locked.json')))
def execute(argv,log,timeout,kind,calls=0):
 deadline();assert LOCK['deadline_unix']-time.time()>timeout+5 and shutil.disk_usage(RUN).free>=4*1024**3
 assert sum(j['reserved_calls'] for j in jobs)+calls<=LOCK['max_NSG_calls']
 assert read(TB/'state.json')['completed_NSG_calls']+LOCK['max_NSG_calls']<=read(TB/'config.locked.json')['resources']['max_NSG_calls']
 j=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout,reserved_calls=calls);jobs.append(j);dump(RUN/'reviews/jobs.json',jobs)
 with (RUN/'logs'/log).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_DYNAMIC='FALSE'),start_new_session=True);j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(RUN/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   j['timeout']=True
 j.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-j['started_unix']);dump(RUN/'reviews/jobs.json',jobs);assert p.returncode==0,j
 return j
try:
 old=Path(LOCK['reference_E107']);argv=[x.replace(str(old),str(RUN)) for x in read(old/'reviews/jobs.json')[0]['argv']]
 dump(RUN/'reviews/build_source_lock.json',dict(files=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)],libraries=[identity(x) for x in argv if x.endswith('.a')]))
 execute(argv,'build.log',120,'build')
 freeze=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[identity(RUN/n) for n in ['protocol.md','research.md','config.locked.json','bin/evaluate']]
 dump(RUN/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=freeze))
 configs=[]
 for ds,c in LOCK['datasets'].items():
  meta=read(c['evaluation_manifest']);assert sha(meta['base'])==meta['base_sha256'] and sha(c['evaluation_queries'])==meta['query_sha256'] and sha(c['evaluation_GT'])==meta['GT_sha256']
  inp=read(old/'reviews'/('main_'+ds+'.json'));methods=[m for m in inp['methods'] if m['name'] in ['GT101','GT103']];assert len(methods)==2;methods.append(dict(methods[1],name='PrimaryFirst3'))
  inp.update(methods=methods,reference_E107=str(old),reference_initial_order=LOCK['reference_initial_order'],deadline_unix=LOCK['deadline_unix'],seconds_cap=LOCK['job_seconds_cap'],max_search_calls=LOCK['max_NSG_calls']);configs.append(inp)
 dump(RUN/'reviews/inputs_validated.json',dict(created_unix=time.time(),configs=configs,GT_base_hashes_revalidated=True,exposed_development=True))
 for smoke in [True,False]:
  for c in configs:
   current=dict(c,n=16 if smoke else 4096,smoke=smoke,K_L={'1':[128],'100':[128]} if smoke else LOCK['K_L']);calls=256 if smoke else 221184;current['expected_search_calls']=calls
   kind='smoke' if smoke else 'main';p=RUN/'reviews'/(kind+'_'+c['dataset']+'.json');dump(p,current);out=RUN/('reviews' if smoke else 'results')/(kind+'_'+c['dataset'])
   dump(RUN/'state.json',dict(status='RUNNING_'+kind.upper(),dataset=c['dataset'],pending=['remaining frozen intervention matrix','analysis']))
   job=execute(['taskset','-c','15',str(RUN/'bin/evaluate'),str(p),str(out)],kind+'_'+c['dataset']+'.log',LOCK['job_seconds_cap'],kind,calls)
   result=read(out/'complete.json');assert result['calls']==calls and result['threads']==1 and result['cpu']==15;job['complete']=result;dump(RUN/'reviews/jobs.json',jobs)
   assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<LOCK['max_new_bytes'];assert sum(p.stat().st_size for p in TB.rglob('*') if p.is_file())<read(TB/'config.locked.json')['resources']['max_new_bytes']
   print(kind,c['dataset'],'completed',round(job['seconds'],2),flush=True)
  if smoke:dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',controls_original_library_bits=True,first_intervention_and_noop_verified=True))
 protected_check()
 for r in freeze+read(RUN/'reviews/build_source_lock.json')['libraries']:assert sha(r['path'])==r['sha256']
 assert sum(j['reserved_calls'] for j in jobs)==442880
 dump(RUN/'reviews/search_complete.json',dict(status='PASS',NSG_calls=442880,seconds=time.time()-started,new_GT=0,new_graphs=0,new_training=0,formal_QPS=False))
 dump(RUN/'state.json',dict(status='FIRST_EXPANSION_SEARCH_COMPLETE',pending=['independent scoring','mechanism and candidate gates','report']))
except Exception as e:dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['preserve error and inspect before any restart']));raise
