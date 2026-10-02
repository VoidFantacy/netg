from pathlib import Path
import os,sys,json,time,hashlib,shutil,resource,csv
import numpy as np
R=Path('/data/netg/ACSG');O=Path(__file__).resolve().parents[1]
E47=R/'entry_method_exploration/20260912_full_feedback_profile_rl_v1'
E46=R/'entry_method_exploration/20260912_exact_feedback_cache_v1'
E45=R/'entry_method_exploration/20260912_mean_update_control_v1'
E44=R/'entry_method_exploration/20260912_local_sampling_diagnosis_v1'
E43=R/'entry_method_exploration/20260912_local_profile_rl_v1'
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
OLD=[R/'entry_method_exploration'/x for x in ['20260912_offline_profile_rl_v1','20260912_offline_profile_diagnosis_v1','20260912_fixed_profile_batch_diagnosis_v1','20260912_profile_payoff_attribution_v1','20260912_profile_factorial_v1','20260912_removed_profile_factorial_v1','20260912_local_profile_rl_v1','20260912_local_sampling_diagnosis_v1','20260912_mean_update_control_v1','20260912_exact_feedback_cache_v1','20260912_full_feedback_profile_rl_v1']]
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];ARMS=['rl','es'];SEEDS=[20260921,20260922]
STEPS=list(range(20,201,20));POP=8;BATCH=128;RANK=16;SIGMA=.3;CAP=60000;QUERY_STOP=1789213200
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
 assert shutil.disk_usage(O).free>=8.5*(1<<30),'free disk <8.5GiB'
 assert sum(p.stat().st_size for p in files(O))<256*(1<<20),'E51 output >=256MiB'
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

E49=R/"entry_method_exploration/20260912_frozen_local_rl_evaluation_v1"
E48=R/"entry_method_exploration/20260912_score_topology_factorial_v1"
def raw_digest(out):
 h=hashlib.sha256()
 for k in FIELDS:h.update(k.encode());h.update(np.ascontiguousarray(out[k]).tobytes())
 return h.hexdigest()

E50=R/"entry_method_exploration/20260912_candidate_commit_diagnosis_v1"
QUERY_STOP=1789220400
LATEST_LAUNCH=1789218900
CAP=40000
def row_profile(p,b,s,z):
 if not np.any(z):return p.copy()
 y=p.astype(float)+.0625*s*(np.tanh(z)@b.T)
 return (y/np.linalg.norm(y)).astype(np.float32)
