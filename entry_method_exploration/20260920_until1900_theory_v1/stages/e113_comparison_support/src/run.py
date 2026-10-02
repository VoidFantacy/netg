import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
os.environ['OMP_DYNAMIC']='FALSE';os.sched_setaffinity(0,{15})
import json,time,hashlib,subprocess,signal,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];TB=R.parents[1];ROOT=TB.parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
cfg=read(R/'config.locked.json');OLD=Path(cfg['previous_phase']);jobs=[];started=time.time();assert not (R/'reviews/execution_started.json').exists()
def resources():
 assert time.time()<cfg['deadline_unix'] and shutil.disk_usage(R).free>=cfg['min_free_gib']*2**30
 assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=cfg['max_stage_bytes']
 assert sum(p.stat().st_size for root in [OLD,TB] for p in root.rglob('*') if p.is_file())<=cfg['max_combined_bytes']
def protect():
 for x in read(R/'reviews/protected_before.json')+read(R/'reviews/setup_freeze.json')['files']+read(R/'reviews/input_sources.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
 for c in cfg['datasets'].values():s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
def execute(argv,kind,timeout,log):
 resources();assert time.time()+timeout+5<cfg['deadline_unix'];j=dict(argv=argv,kind=kind,started_unix=time.time(),timeout_seconds=timeout);jobs.append(j);dump(R/'reviews/jobs.json',jobs)
 with (R/'logs'/log).open('x') as f:
  p=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,start_new_session=True);j.update(pid=p.pid,pgid=os.getpgid(p.pid));dump(R/'reviews/jobs.json',jobs)
  try:p.wait(timeout=timeout)
  except subprocess.TimeoutExpired:
   assert os.getpgid(p.pid)==p.pid;os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=3)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
   j['timed_out']=True
 j.update(exit_code=p.returncode,finished_unix=time.time(),seconds=time.time()-j['started_unix']);dump(R/'reviews/jobs.json',jobs);assert p.returncode==0,j
 resources();return j
try:
 protect();resources();dump(R/'reviews/execution_started.json',dict(created_unix=started,config=ident(R/'config.locked.json'),data_roles='Existing fit only; no cal or development payload'))
 argv=read(ROOT/'entry_method_exploration/20260920_gt10_conditional_mechanism_v1/reviews/build.json')['argv'];argv=[str(R/'src/evaluate.cpp') if a.endswith('/src/evaluate.cpp') else str(R/'bin/evaluate') if a.endswith('/bin/evaluate') else a for a in argv];execute(['taskset','-c','15']+argv,'compile',120,'compile.log')
 dump(R/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=read(R/'reviews/setup_freeze.json')['files']+[ident(R/'bin/evaluate')]))
 completed=0
 for ds,c in cfg['datasets'].items():
  p=R/'reviews'/(ds+'.json');dump(p,c);dump(R/'state.json',dict(status='RUNNING_FIT_COMPARISONS',dataset=ds,completed_NSG_calls=completed,pending=['remaining dataset','independent support analysis']))
  out=R/'results'/ds;j=execute(['taskset','-c','15',str(R/'bin/evaluate'),str(p),str(out)],'fit_trace',900,ds+'.log');done=read(out/'complete.json');j['complete']=done;dump(R/'reviews/jobs.json',jobs);completed+=done['NSG_calls'];assert completed<=cfg['max_NSG_calls'];print(ds,'complete',done['unique_query_action_pairs'],'pairs',round(j['seconds'],2),'seconds',flush=True)
 assert completed==cfg['expected_NSG_calls'];protect();dump(R/'reviews/trace_complete.json',dict(status='PASS',seconds=time.time()-started,NSG_calls=completed,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,all_historical_outputs_restored=True,all_K1_K100_pair_sets_identical=True))
 state=read(TB/'state.json');state['completed_NSG_calls']+=completed;state['active_stage_reserved_NSG_calls']=0;dump(TB/'state.json',state);dump(R/'state.json',dict(status='TRACES_COMPLETE_PENDING_INFORMATION_GATE',completed_NSG_calls=completed,pending=['shared support analysis','report and closeout']))
except Exception as e:
 dump(R/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['preserve cause and exact call counts before any repair']));raise
