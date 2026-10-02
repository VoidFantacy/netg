from pathlib import Path
import hashlib,json,time,shutil
import numpy as np
R=Path('/data/netg/ACSG');E=R/'entry_method_exploration/20260912_offline_profile_rl_v1';O=R/'entry_method_exploration/20260912_offline_profile_diagnosis_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];ARMS=['rl','es'];SEEDS=[20260921,20260922]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def check(items):
 for x in items:
  p=Path(x['path']);s=p.stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and sha(p)==x['sha256'],p
def hit(ids,gt):return (ids[...,None]==gt[...,None,:10]).any(axis=-2).sum(-1).astype(np.int16)
def cosine(a,b):
 den=np.linalg.norm(a)*np.linalg.norm(b);return None if den<1e-20 else float(np.dot(a,b)/den)
def mat(arm,eps):return (eps-eps.mean(0)).T/(7*.3) if arm=='rl' else np.concatenate([eps[:4].T,-eps[:4].T],axis=1)/(8*.3)
def median(xs):
 x=[v for v in xs if v is not None and np.isfinite(v)];return float(np.median(x)) if x else None
