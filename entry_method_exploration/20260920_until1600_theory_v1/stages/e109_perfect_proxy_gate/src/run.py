from common import *
import subprocess,shutil,signal,sys
wait=Path(LOCK['wait_for_E108']);assert read(wait)['status']=='PASS' and read(wait.parents[1]/'complete.json')['status']=='COMPLETE','finish E108 first'
assert not (RUN/'reviews/execution_started.json').exists()
deadline();protected_check();started=time.time();jobs=[]
before=[]
for n in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 p=RUN/'source_before'/n;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();shutil.copy2(ROOT/n,p);before.append(identity(p))
dump(RUN/'reviews/execution_started.json',dict(created_unix=started,protocol=identity(RUN/'protocol.md'),config=identity(RUN/'config.locked.json'),source_before=before))
def execute(argv,logname,timeout,kind,calls=0):
 deadline();assert LOCK['deadline_unix']-time.time()>timeout+5 and shutil.disk_usage(RUN).free>=4*1024**3
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
 execute(['taskset','-c','15',sys.executable,str(RUN/'src/prepare.py')],'prepare.log',300,'prepare')
 old=Path(LOCK['reference_E107']);build=read(old/'reviews/jobs.json')[0]['argv'];argv=[x.replace(str(old),str(RUN)) for x in build]
 for n in ['kernels.hpp','search_core.hpp']:assert sha(RUN/'src'/n)==sha(old/'src'/n)
 dump(RUN/'reviews/build_source_lock.json',dict(files=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)],libraries=[identity(Path(x)) for x in argv if x.endswith('.a')]))
 execute(argv,'build.log',120,'compile')
 inputs=read(RUN/'reviews/inputs_prepared.json');assert inputs['status']=='PASS'
 freeze=[identity(p) for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[identity(RUN/n) for n in ['protocol.md','config.locked.json','bin/evaluate']]
 for r in inputs['datasets']:freeze.extend(r['files'])
 dump(RUN/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=freeze))
 for smoke in [True,False]:
  for r in inputs['datasets']:
   c=dict(r['config'],smoke=smoke,n=16 if smoke else LOCK['n']);calls=c['n']*4*2*(3 if smoke else 2);c['expected_search_calls']=calls
   kind='smoke' if smoke else 'main';cfg=RUN/'reviews'/(kind+'_'+c['dataset']+'.json');dump(cfg,c);out=RUN/('reviews' if smoke else 'results')/(kind+'_'+c['dataset'])
   dump(RUN/'state.json',dict(status='RUNNING_'+kind.upper(),dataset=c['dataset'],pending=['remaining fit proxy matrix','information gate analysis']))
   job=execute(['taskset','-c','15',str(RUN/'bin/evaluate'),str(cfg),str(out)],kind+'_'+c['dataset']+'.log',300,kind,calls)
   result=read(out/'complete.json');assert result['NSG_calls']==calls and result['threads']==1 and result['cpu']==15;job['complete']=result;dump(RUN/'reviews/jobs.json',jobs)
   assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<=LOCK['max_new_bytes'];assert sum(p.stat().st_size for p in TB.rglob('*') if p.is_file())<=read(TB/'config.locked.json')['resources']['max_new_bytes']
   print(kind,c['dataset'],'complete',round(job['seconds'],2),flush=True)
  if smoke:dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',all_four_routes_original_kernel_bits_and_NDC=True))
 protected_check()
 for r in freeze+read(RUN/'reviews/pre_fit_lock.json')['files']+read(RUN/'reviews/build_source_lock.json')['libraries']:assert sha(r['path'])==r['sha256'],r['path']
 calls=sum(j['reserved_calls'] for j in jobs);assert calls==LOCK['expected_NSG_calls']
 dump(RUN/'reviews/search_complete.json',dict(status='PASS',NSG_calls=calls,seconds=time.time()-started,new_GT=0,new_training=0,new_graphs=0,new_formal_QPS=False,privileged_fit_only=True))
 dump(RUN/'state.json',dict(status='PROXY_SEARCH_COMPLETE',pending=['independent analysis','prelocked information gate','report']))
except Exception as e:
 dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect preserved error; no blind restart']));raise
