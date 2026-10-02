from common import *
import subprocess,signal
from train import train
from analyze import analyze

ENV=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:ENV[k]='1'
ENV['OMP_DYNAMIC']='FALSE'
START=time.time();JOBS=[];RESOURCES=[]
def check():
 assert shutil.disk_usage(RUN).free>=LOCK['min_free_gib']*1024**3
 for c in LOCK['datasets'].values():
  st=Path(c['index']).stat();assert st.st_size==c['index_stat']['bytes'] and st.st_mtime_ns==c['index_stat']['mtime_ns']
 for x in read(RUN/'reviews/source_frozen.json')['files']:assert sha(x['path'])==x['sha256']
def execute(cfg,out,kind):
 check();assert not out.exists();cp=RUN/'reviews'/f'config_{kind}_{cfg["dataset"]}.json';dump(cp,cfg);argv=['taskset','-c','15',str(RUN/'bin/experiment'),str(cp),str(out)]
 j=dict(kind=kind,dataset=cfg['dataset'],argv=argv,started_unix=time.time());JOBS.append(j);dump(RUN/'reviews/jobs.json',JOBS)
 with (RUN/'logs'/f'{kind}_{cfg["dataset"]}.log').open('x') as log:
  p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=ENV,start_new_session=True);j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(RUN/'reviews/jobs.json',JOBS)
  try:
   while p.poll() is None:
    try:p.wait(timeout=5)
    except subprocess.TimeoutExpired:
     status=Path(f'/proc/{p.pid}/status').read_text();data={a:b.strip() for a,b in (line.split(':',1) for line in status.splitlines() if ':' in line)}
     rss=int(data.get('VmRSS','0 kB').split()[0])*1024;threads=int(data['Threads']);free=shutil.disk_usage(RUN).free
     RESOURCES.append(dict(unix=time.time(),pid=p.pid,kind=kind,rss=rss,threads=threads,free_bytes=free));dump(RUN/'reviews/resources.json',RESOURCES)
     assert rss<=LOCK['maxrss_gib']*1024**3 and threads==1 and free>=LOCK['min_free_gib']*1024**3
     assert time.time()-j['started_unix']<LOCK['job_seconds_cap'] and time.time()-START<LOCK['seconds_cap']
  except BaseException:
   if p.poll() is None:
    os.killpg(p.pid,signal.SIGTERM)
    try:p.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   raise
 j.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-j['started_unix']);dump(RUN/'reviews/jobs.json',JOBS);assert p.returncode==0,(kind,cfg['dataset'],p.returncode)
 j['complete']=read(out/'complete.json');dump(RUN/'reviews/jobs.json',JOBS);assert sum(v.get('complete',{}).get('search_calls',0) for v in JOBS)<=LOCK['max_search_calls'];assert sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())<=LOCK['max_new_bytes']
 print('COMPLETE',kind,cfg['dataset'],round(j['seconds'],2),flush=True)
def main():
 assert not(RUN/'reviews/execution_started.json').exists(),'one runner; inspect existing handle before continuation'
 os.sched_setaffinity(0,{15});dump(RUN/'reviews/execution_started.json',dict(unix=START,pid=os.getpid(),objective='user authorized four-action entry-only pilot'))
 files=[p for p in (RUN/'src').rglob('*') if p.is_file() and '__pycache__' not in str(p)]+[RUN/'bin/experiment',RUN/'config.locked.json',RUN/'protocol.md'];dump(RUN/'reviews/source_frozen.json',dict(created_unix=time.time(),files=[ident(p) for p in files]))
 try:
  prepare('fit')
  for ds,c in LOCK['datasets'].items():
   cfg=read(RUN/'inputs'/ds/'fit/config.json');d=c['dimension'];p=RUN/'inputs'/ds/'smoke';p.mkdir();np.fromfile(cfg['queries'],np.float32).reshape(-1,d)[:64].tofile(p/'queries.f32');np.fromfile(cfg['route_reference'],np.int32).reshape(-1,3)[:64].tofile(p/'routes.i32')
   cfg.update(n=64,queries=str(p/'queries.f32'),route_reference=str(p/'routes.i32'))
   execute(cfg,RUN/'results'/ds/'smoke','smoke')
  dump(RUN/'reviews/smoke_gate.json',dict(status='PASS',datasets=2,original_router_membership=True,original_main_search_bit_parity=True))
  dump(RUN/'state.json',dict(status='RUNNING_FIT_LABELS',runner_pid=os.getpid(),pending=['fit labels','train and freeze','accept','report']))
  for ds in LOCK['datasets']:execute(read(RUN/'inputs'/ds/'fit/config.json'),RUN/'results'/ds/'labels','labels')
  check();train();check();prepare('accept');dump(RUN/'state.json',dict(status='RUNNING_FROZEN_ACCEPTANCE',runner_pid=os.getpid(),pending=['acceptance','analysis','report']))
  for ds in LOCK['datasets']:execute(read(RUN/'inputs'/ds/'accept/config.json'),RUN/'results'/ds/'accept','accept')
  analyze();check()
  if read(RUN/'results/gate.json')['full_curve_required']:
   for ds in LOCK['datasets']:
    cfg=read(RUN/'inputs'/ds/'accept/config.json');fixed=read(RUN/'models'/ds/'models.json')['fixed_best_method'];cfg['methods']=[m for m in cfg['methods'] if m['name'] in ['GT10',fixed,'CostTree']];cfg['points']=[dict(K=K,L=L) for K in [1,100] for L in [64,256,400,800] if L>=K];execute(cfg,RUN/'results'/ds/'curve','curve')
   analyze('curve');check()
  dump(RUN/'reviews/execution_complete.json',dict(status='PASS',seconds=time.time()-START,search_calls=sum(j['complete']['search_calls'] for j in JOBS),router_calls=sum(j['complete']['router_calls'] for j in JOBS),feature_distance_calls=sum(j['complete']['feature_distance_calls'] for j in JOBS),jobs=len(JOBS),new_gt=0,new_graphs=0))
  dump(RUN/'state.json',dict(status='MEASUREMENTS_COMPLETE',gate=read(RUN/'results/gate.json')['status'],pending=['independent completion audit','report and documentation'],active_processes=[],finished_unix=time.time()))
 except BaseException as err:
  dump(RUN/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(err),jobs=JOBS,finished_unix=time.time()));raise
if __name__=='__main__':main()
