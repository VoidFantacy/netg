from pathlib import Path
import os,json,hashlib,shutil,time,subprocess,itertools
import numpy as np
R=Path('/data/netg/ACSG');O=R/'entry_method_exploration/20260911_query_swap_policy_v1'
E35=R/'entry_method_exploration/20260911_hnsw_selection_probe_v1';E34=R/'entry_method_exploration/20260911_hnsw_rl_benchmark_v1';E33=R/'entry_method_exploration/20260911_hnsw_edge_rl_v1';E24=R/'entry_method_exploration/20260910_gt_topk_profiles_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];SEEDS=[20260917,20260918];ARMS=['rl','exact'];TRIP=np.array(list(itertools.combinations(range(8),3)),np.int64)
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,files):
 assert not Path(p).exists(),p
 dump(p,dict(time=time.time(),files=[identity(f) for f in sorted(set(map(Path,files)))]))
def check(p,hashes=True):
 for x in read(p)['files']:
  f=Path(x['path']);s=f.stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'],f
  if hashes:assert sha(f)==x['sha256'],f
def env():
 e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');return e
def resources():
 assert shutil.disk_usage(O).free>=10*(1<<30)
 assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<=384*(1<<20)
def reserve(name,cap):
 path=O/'logs/jobs.json';jobs=read(path) if path.exists() else [];assert not any(x['name']==name for x in jobs)
 assert sum(x['reserved'] for x in jobs)+cap<=300000
 jobs.append(dict(name=name,reserved=cap,status='RUNNING',started_at=time.time()));dump(path,jobs)
def finish(name,actual,**kw):
 jobs=read(O/'logs/jobs.json');j=next(x for x in jobs if x['name']==name);assert j['status']=='RUNNING' and actual<=j['reserved'];j.update(status='COMPLETE',actual=actual,closed_at=time.time(),**kw);dump(O/'logs/jobs.json',jobs)
def run_job(name,cfg,out,cap):
 resources();reserve(name,cap);t=time.time();peak=0;nt=0
 with (O/'logs'/(name+'.log')).open('x') as f:
  p=subprocess.Popen([str(O/'bin/runner'),str(cfg),str(out)],env=env(),stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:
    a=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line);peak=max(peak,int(a.get('VmRSS','0 kB').split()[0]));nt=max(nt,int(a['Threads']))
   except FileNotFoundError:pass
   if time.time()-t>1200 or peak>40*(1<<20) or nt>1:p.kill();p.wait();raise RuntimeError('resource stop '+name)
   time.sleep(.1)
 assert p.returncode==0,name+' see log'
 done=read(out/'complete.json');finish(name,done['NSG_calls'],seconds=time.time()-t,peak_RSS_KiB=peak,peak_threads=nt,HNSW_calls=done['HNSW_calls']);print('JOB_COMPLETE',name,time.time()-t,flush=True)
def successors():
 index={tuple(x):i for i,x in enumerate(TRIP)};rows=[]
 for i,s in enumerate(TRIP):
  row=[i]
  for a in s:
   for b in range(8):
    if b not in s:row.append(index[tuple(sorted((set(s)-{a})|{b}))])
  rows.append(row)
 return np.array(rows,np.int64)
NEXT=successors();PRIOR=-.25*(TRIP.sum(axis=1)-3)
def score(ids,gt):
 g=gt[:,:10].reshape((len(gt),)+(1,)*(ids.ndim-1)+(10,));return (ids[...,None]==g).any(axis=-1).sum(axis=-1).astype(np.uint8)
