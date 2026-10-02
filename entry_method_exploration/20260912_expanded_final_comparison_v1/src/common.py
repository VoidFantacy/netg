from pathlib import Path
import os, json, hashlib, shutil, time, subprocess
import numpy as np

R=Path('/data/netg/ACSG'); O=Path(__file__).resolve().parents[1]
E24=R/'entry_method_exploration/20260910_gt_topk_profiles_v1'
E33=R/'entry_method_exploration/20260911_hnsw_edge_rl_v1'
E34=R/'entry_method_exploration/20260911_hnsw_rl_benchmark_v1'
E36=R/'entry_method_exploration/20260911_query_swap_policy_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
ARMS=['rl','es']; SEEDS=[20260921,20260922]; LS=[64,128,256,400,800]
RANK=16; SIGMA=.3; STEPS=200; POP=8; BATCH=128; CAP=750000

def read(p): return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,files):
 assert not Path(p).exists(),p
 dump(p,dict(files=[identity(f) for f in sorted(set(map(Path,files)))],time=time.time()))
def check(p,hashes=True):
 for x in read(p)['files']:
  f=Path(x['path']);s=f.stat();assert s.st_size==x['bytes'] and ('mtime_ns' not in x or s.st_mtime_ns==x['mtime_ns']),f
  if hashes:assert sha(f)==x['sha256'],f
def env():
 e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');return e
def resources():
 assert shutil.disk_usage(O).free>=7*(1<<30),'free disk <7GiB'
 assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<=384*(1<<20),'artifact cap'
def reserve(name,calls):
 p=O/'logs/jobs.json';jobs=read(p) if p.exists() else []
 assert sum(j['reserved'] for j in jobs)+calls<=CAP
 assert not any(j['name']==name for j in jobs),name
 jobs.append(dict(name=name,reserved=calls,status='RUNNING',started_at=time.time(),pid=os.getpid()));dump(p,jobs)
def finish(name,calls,**kw):
 p=O/'logs/jobs.json';jobs=read(p);j=next(j for j in jobs if j['name']==name)
 assert j['status']=='RUNNING' and calls<=j['reserved'];j.update(status='COMPLETE',actual=calls,closed_at=time.time(),**kw);dump(p,jobs)
def score(ids,gt):
 return (ids[...,None]==gt[:,:10][:,None,:]).any(axis=1).sum(axis=1).astype(np.uint8)
def utility(out,base,gt):
 h=score(out['ids'],gt).astype(float);h0=base['hits'].astype(float)
 total=out['route_ndc'].astype(float)+out['graph_ndc'];c0=base['route_ndc'].astype(float)+base['graph_ndc']
 return h-h0-.1*(total/c0-1)-.1*((h==0).astype(float)-(h0==0).astype(float))
def subset(a,rows):return {k:v[rows] for k,v in a.items()}
def profiles(p,b,x):
 if not np.any(x):return p.astype(np.float32,copy=True)
 y=p.astype(float)+.25*((p.astype(float)@b)@(np.tanh(x.reshape(RANK,RANK))/4.))@b.T
 return (y/np.linalg.norm(y,axis=1,keepdims=True)).astype(np.float32)
def rate(step):return .003+.5*(.03-.003)*(1+np.cos(np.pi*(step-1)/(STEPS-1)))
def gradient(arm,rewards,eps):
 if arm=='rl':
  baseline=(rewards.sum()-rewards)/(POP-1)
  return ((rewards-baseline)[:,None]*eps).mean(0)/SIGMA
 return ((rewards[:POP//2]-rewards[POP//2:])[:,None]*eps[:POP//2]).mean(0)/(2*SIGMA)
def update(mu,m,v,g,step):
 norm=np.linalg.norm(g);g=g/max(1.,norm);m=.9*m+.1*g;v=.999*v+.001*g*g
 mu=np.clip(mu+rate(step)*(m/(1-.9**step))/(np.sqrt(v/(1-.999**step))+1e-8),-2,2)
 return mu,m,v,float(norm)

E37=R/"entry_method_exploration/20260912_offline_profile_rl_v1"
E47=R/"entry_method_exploration/20260912_full_feedback_profile_rl_v1"
E48=R/"entry_method_exploration/20260912_score_topology_factorial_v1"
QUERY_STOP=1789220400

E52=R/"entry_method_exploration/20260912_direct_candidate_commit_v1"
E53=R/"entry_method_exploration/20260912_feedback_step_rl_v1"
E54=R/"entry_method_exploration/20260912_learned_model_factorial_v1"

E55=R/"entry_method_exploration/20260912_final_method_comparison_v1"
E56=R/"entry_method_exploration/20260912_construction_only_rl_v1"
