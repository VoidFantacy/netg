from workflow import *
ENV=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:ENV[k]='1'
ENV['OMP_DYNAMIC']='FALSE'
START=time.time();JOBS=[]
def check():
 assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
 for ds,c in LOCK['datasets'].items():
  s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
 for x in read(RUN/'reviews/source_frozen.json')['files']:assert sha(x['path'])==x['sha256']
def execute(cfg,out,kind):
 check();assert not out.exists();cp=RUN/'reviews'/f'config_{kind}_{cfg["dataset"]}.json';dump(cp,cfg);cmd=['taskset','-c','15',str(RUN/'bin/experiment'),str(cp),str(out)];j=dict(kind=kind,dataset=cfg['dataset'],argv=cmd,started_unix=time.time());JOBS.append(j);dump(RUN/'reviews/jobs.json',JOBS)
 with (RUN/'logs'/f'{kind}_{cfg["dataset"]}.log').open('x') as log:
  p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=ENV,start_new_session=True);j['pid']=p.pid;j['pgid']=os.getpgid(p.pid);dump(RUN/'reviews/jobs.json',JOBS)
  try:p.wait(timeout=max(1,LOCK['seconds_cap']-(time.time()-START)))
  except subprocess.TimeoutExpired:os.killpg(p.pid,9);p.wait();j['timeout']=True
 j.update(exit_code=p.returncode,seconds=time.time()-j['started_unix'],finished_unix=time.time());dump(RUN/'reviews/jobs.json',JOBS);assert p.returncode==0,(kind,cfg['dataset'],p.returncode)
 j['complete']=read(out/'complete.json');dump(RUN/'reviews/jobs.json',JOBS);assert sum(x.get('complete',{}).get('search_calls',0) for x in JOBS)<=LOCK['max_search_calls'];print('COMPLETE',kind,cfg['dataset'],round(j['seconds'],2),flush=True)
def main():
 assert not(RUN/'reviews/source_frozen.json').exists(),'one runner only; inspect any prior handle before continuation'
 files=[p for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[RUN/'bin/experiment',RUN/'config.locked.json',RUN/'protocol.md']
 dump(RUN/'reviews/source_frozen.json',dict(created_unix=time.time(),files=[ident(p) for p in files]))
 try:
  prepare()
  for ds in LOCK['datasets']:
   for role in ['proposal','fit']:execute(read(RUN/'inputs'/ds/role/'config.json'),RUN/'results'/ds/f'route_{role}',f'route_{role}')
  propose();dump(RUN/'state.json',dict(status='RUNNING_LABELS',started_unix=START,runner_pid=os.getpid()))
  for ds in LOCK['datasets']:execute(read(RUN/'inputs'/ds/'labels_config.json'),RUN/'results'/ds/'labels','labels')
  check();select();audit_inputs();dump(RUN/'state.json',dict(status='RUNNING_FROZEN_AUDIT',started_unix=START,runner_pid=os.getpid()))
  for ds in LOCK['datasets']:execute(read(RUN/'inputs'/ds/'audit/config.json'),RUN/'results'/ds/'audit','audit')
  from analyze import analyze
  analyze();check();dump(RUN/'reviews/execution_complete.json',dict(status='PASS',seconds=time.time()-START,search_calls=sum(x['complete']['search_calls'] for x in JOBS),router_only_calls=sum(x['complete'].get('router_calls',0) for x in JOBS),jobs=len(JOBS),new_gt=0,new_graphs=0))
  dump(RUN/'state.json',dict(status='MEASUREMENTS_COMPLETE',gate=read(RUN/'results/gate.json')['status'],pending=['independent completion audit','report and documents'],finished_unix=time.time()))
 except Exception as e:
  dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),jobs=JOBS,finished_unix=time.time()));raise
if __name__=='__main__':main()
