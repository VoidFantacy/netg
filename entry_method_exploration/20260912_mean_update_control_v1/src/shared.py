from pathlib import Path
import os,sys,json,time,hashlib,shutil,resource,csv
import numpy as np
R=Path('/data/netg/ACSG');O=Path(__file__).resolve().parents[1]
E44=R/'entry_method_exploration/20260912_local_sampling_diagnosis_v1'
E43=R/'entry_method_exploration/20260912_local_profile_rl_v1'
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
OLD=[R/'entry_method_exploration'/x for x in ['20260912_offline_profile_rl_v1','20260912_offline_profile_diagnosis_v1','20260912_fixed_profile_batch_diagnosis_v1','20260912_profile_payoff_attribution_v1','20260912_profile_factorial_v1','20260912_removed_profile_factorial_v1','20260912_local_profile_rl_v1','20260912_local_sampling_diagnosis_v1']]
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];ARMS=['rl','es'];SEEDS=[20260921,20260922]
STEPS=list(range(20,201,20));POP=8;BATCH=128;RANK=16;SIGMA=.3;CAP=170000;QUERY_STOP=1789213200
FIELDS=['ids','distances','entries','route_ndc','graph_ndc'];sys.dont_write_bytecode=True
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def files(p):return sorted(x for x in p.rglob('*') if x.is_file())
def freeze(p,paths):
 assert not p.exists();dump(p,dict(files=[dict(path=str(f),bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(set(paths))]))
def check(p):
 for f in read(p)['files']:assert sha(f['path'])==f['sha256'],f['path']
def save(p,**kw):
 assert not p.exists(),p
 p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**kw)
def resources():
 assert shutil.disk_usage(O).free>=9*(1<<30),'free disk <9GiB'
 assert sum(p.stat().st_size for p in files(O))<256*(1<<20),'E45 output >=256MiB'
def threads(cpu):
 assert os.sched_getaffinity(0)=={cpu}
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:assert os.environ[k]=='1'
 assert next(int(l.split(':')[1]) for l in Path('/proc/self/status').read_text().splitlines() if l.startswith('Threads:'))==1
def equal(a,b):
 for k in FIELDS:assert a[k].shape==b[k].shape and a[k].dtype==b[k].dtype and a[k].tobytes()==b[k].tobytes(),k
def score(ids,gt):return (ids[...,None]==gt[:,None,:10]).any(-2).sum(-1).astype(np.uint8)
def subset(a,rows):return {k:v[rows] for k,v in a.items()}
def utility(out,base,gt):
 h=score(out['ids'],gt).astype(float);h0=base['hits'].astype(float)
 total=out['route_ndc'].astype(float)+out['graph_ndc'];c0=base['route_ndc'].astype(float)+base['graph_ndc']
 return h-h0-.1*(total/c0-1)-.1*((h==0).astype(float)-(h0==0).astype(float))
def row_profile(p,b,s,z):
 if not np.any(z):return p.copy()
 y=p.astype(float)+(.25/4)*s*(np.tanh(z)@b.T)
 return (y/np.linalg.norm(y)).astype(np.float32)
def rate(step):return .003+.5*(.03-.003)*(1+np.cos(np.pi*(step-1)/(200-1)))
def update(mu,m,v,g,local_count,step):
 norm=float(np.linalg.norm(g));g=g/max(1.,norm);m=.9*m+.1*g;v=.999*v+.001*g*g
 mu=np.clip(mu+rate(step)*(m/(1-.9**local_count))/(np.sqrt(v/(1-.999**local_count))+1e-8),-2,2)
 return mu,m,v,norm
