import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
os.environ['OMP_DYNAMIC']='FALSE';os.sched_setaffinity(0,{15})
import json,time,hashlib,subprocess,signal,shutil
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];TB=R.parents[1];ROOT=TB.parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
cfg=read(R/'config.locked.json');OLD=Path(cfg['previous_phase']);jobs=[];started=time.time()
assert not (R/'reviews/execution_started.json').exists()
def resources():
 assert time.time()<cfg['deadline_unix'];assert shutil.disk_usage(R).free>=cfg['min_free_gib']*2**30
 assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=cfg['max_new_bytes']
 assert sum(p.stat().st_size for root in [OLD,TB] for p in root.rglob('*') if p.is_file())<=cfg['max_combined_new_bytes']
def protect():
 for x in read(R/'reviews/protected_before.json')+read(R/'reviews/setup_freeze.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
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
 protect();resources();dump(R/'reviews/execution_started.json',dict(created_unix=started,config=ident(R/'config.locked.json'),development_globally_exposed=True,development_payload_read_by_this_runner=False))
 inputs=[]
 for ds,c in cfg['datasets'].items():
  for source,dest,width,isfloat in [(c['QGT_queries_source'],c['QGT_queries'],c['dimension'],True),(c['QGT_GT_source'],c['QGT_GT'],100,False)]:
   raw=np.fromfile(source,'<i4').reshape(5000,width+1);assert np.all(raw[:,0]==width);data=raw[:,1:].copy();data=data.view('<f4') if isfloat else data;data.tofile(dest);inputs.append(ident(dest))
  q=np.fromfile(c['QGT_queries'],'<f4');assert np.isfinite(q).all()
 dump(R/'reviews/QGT_inputs.json',dict(created_unix=time.time(),files=inputs,rows=5000,GT_width=100,source_headers_validated=True))
 argv=read(ROOT/'entry_method_exploration/20260920_gt10_conditional_mechanism_v1/reviews/build.json')['argv'];argv=[str(R/'src/design.cpp') if a.endswith('/src/evaluate.cpp') else str(R/'bin/design') if a.endswith('/bin/evaluate') else a for a in argv]
 execute(['taskset','-c','15']+argv,'compile',120,'compile.log')
 dump(R/'reviews/search_source_freeze.json',dict(created_unix=time.time(),files=[ident(R/p) for p in ['config.locked.json','protocol.md','research.md','src/design.cpp','src/run.py','bin/design']]+inputs))
 for ds,c in cfg['datasets'].items():
  current=dict(c,n=5000,queries=c['QGT_queries'],GT=c['QGT_GT'],deadline_unix=cfg['deadline_unix'],seconds_cap=cfg['job_seconds_cap']-10,max_nonzero=cfg['max_nonzero_per_dataset']);p=R/'reviews'/('select_'+ds+'.json');dump(p,current);out=R/'results'/('QGT_'+ds)
  dump(R/'state.json',dict(status='RUNNING_QGT_H_SELECTION',dataset=ds,pending=['remaining QGT','H freeze','development','analysis']))
  j=execute(['taskset','-c','15',str(R/'bin/design'),'select',str(p),str(out)],'select',900,'select_'+ds+'.log');j['complete']=read(out/'complete.json');dump(R/'reviews/jobs.json',jobs);assert j['complete']['NSG_calls']==0
  print('QGT complete',ds,j['complete']['all_base_sparse_nonzero'],round(j['seconds'],2),flush=True)
 hfiles=[ident(p) for p in (R/'results').glob('QGT_*/*/hub_ids.i32')];assert len(hfiles)==6
 dump(R/'reviews/hub_freeze.json',dict(created_unix=time.time(),files=hfiles,development_payload_read_by_this_runner=False,development_globally_exposed=True,QGT_only_selection=True))
 for ds,c in cfg['datasets'].items():
  current=dict(c,n=4096,queries=c['development_queries'],GT=c['development_GT'],deadline_unix=cfg['deadline_unix'],seconds_cap=290,methods=[dict(name=m,hub_ids=str(R/'results'/('QGT_'+ds)/m/'hub_ids.i32')) for m in cfg['methods']]);p=R/'reviews'/('evaluate_'+ds+'.json');dump(p,current);out=R/'results'/('development_'+ds)
  dump(R/'state.json',dict(status='RUNNING_DEVELOPMENT_LABEL_ASSESSMENT',dataset=ds,pending=['remaining development','independent information gate']))
  j=execute(['taskset','-c','15',str(R/'bin/design'),'evaluate',str(p),str(out)],'evaluate',300,'evaluate_'+ds+'.log');j['complete']=read(out/'complete.json');dump(R/'reviews/jobs.json',jobs);assert j['complete']['NSG_calls']==0
  print('Development labels complete',ds,round(j['seconds'],2),flush=True)
 protect()
 for x in read(R/'reviews/hub_freeze.json')['files']+read(R/'reviews/search_source_freeze.json')['files']:assert sha(x['path'])==x['sha256']
 dump(R/'reviews/label_complete.json',dict(status='PASS',seconds=time.time()-started,NSG_calls=0,ANN_calls=0,new_GT=0,new_graphs=0,new_training=0,graph_derived_labels=True,all_H_frozen_before_development=True))
 dump(R/'state.json',dict(status='LABELS_COMPLETE_PENDING_INDEPENDENT_GATE',pending=['independent membership validation','four paired intervals','information gate','report and closeout']))
except Exception as e:
 dump(R/'state.json',dict(status='STOP_EXECUTION_ERROR',error=repr(e),pending=['inspect and preserve cause before any mechanical repair']));raise
