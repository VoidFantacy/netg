from pathlib import Path
import os,sys,json,time,hashlib,shutil,resource,csv
import numpy as np
R=Path('/data/netg/ACSG');O=Path(__file__).resolve().parents[1]
E43=R/'entry_method_exploration/20260912_local_profile_rl_v1'
E46=R/'entry_method_exploration/20260912_exact_feedback_cache_v1'
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
OLD=[R/'entry_method_exploration'/x for x in ['20260912_offline_profile_rl_v1','20260912_offline_profile_diagnosis_v1','20260912_fixed_profile_batch_diagnosis_v1','20260912_profile_payoff_attribution_v1','20260912_profile_factorial_v1','20260912_removed_profile_factorial_v1','20260912_local_profile_rl_v1','20260912_local_sampling_diagnosis_v1','20260912_mean_update_control_v1','20260912_exact_feedback_cache_v1']]
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];ARMS=['commit'];SEEDS=[20260921,20260922]
STEPS=200;POP=8;BATCH=128;RANK=16;SIGMA=.3;CAP=400000;TRAIN_STOP=1789220100
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
 assert shutil.disk_usage(O).free>=8*(1<<30),'free disk <8GiB'
 assert sum(p.stat().st_size for p in files(O))<256*(1<<20),'E52 output >=256MiB'
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
def rate(step):return .003+.5*(.03-.003)*(1+np.cos(np.pi*(step-1)/(STEPS-1)))
def gradient(arm,rewards,eps):
 if arm=='rl':return ((rewards-(rewards.sum()-rewards)/(POP-1))[:,None]*eps).mean(0)/SIGMA
 return ((rewards[:4]-rewards[4:])[:,None]*eps[:4]).mean(0)/(2*SIGMA)
def update(mu,m,v,g,local_count,step):
 norm=float(np.linalg.norm(g));g=g/max(1.,norm);m=.9*m+.1*g;v=.999*v+.001*g*g
 mu=np.clip(mu+rate(step)*(m/(1-.9**local_count))/(np.sqrt(v/(1-.999**local_count))+1e-8),-2,2)
 return mu,m,v,norm
def reserve(name,calls):
 p=O/'logs/jobs.json';jobs=read(p) if p.exists() else []
 builds=1803
 assert not any(x['name']==name for x in jobs),'existing job; no automatic retry'
 assert not any(x['status']=='RUNNING' for x in jobs),'another active/reserved job'
 assert sum(x['reserved'] for x in jobs)+calls<=CAP
 assert sum(x['reserved_builds'] for x in jobs)+builds<=15000
 jobs.append(dict(name=name,reserved=calls,reserved_builds=builds,status='RUNNING',pid=os.getpid(),started_at=time.time()));dump(p,jobs)
def finish(name,calls,**kw):
 p=O/'logs/jobs.json';jobs=read(p);j=next(x for x in jobs if x['name']==name)
 assert j['status']=='RUNNING' and calls<=j['reserved'];j.update(status='COMPLETE',actual=calls,completed_at=time.time(),**kw);dump(p,jobs)

def raw_digest(out):
 h=hashlib.sha256()
 for k in FIELDS:h.update(k.encode());h.update(np.ascontiguousarray(out[k]).tobytes())
 return h.hexdigest()
def fast_utility(out,base):
 h=out['hits'].astype(float);h0=base['hits'].astype(float);total=out['route_ndc'].astype(float)+out['graph_ndc'];t0=base['route_ndc'].astype(float)+base['graph_ndc']
 return h-h0-.1*(total/t0-1)-.1*((h==0).astype(float)-(h0==0).astype(float))

E47=R/"entry_method_exploration/20260912_full_feedback_profile_rl_v1"
E49=R/"entry_method_exploration/20260912_frozen_local_rl_evaluation_v1"
E51=R/"entry_method_exploration/20260912_update_direction_radius_v1"
LATEST_LAUNCH=1789218900
