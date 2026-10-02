from pathlib import Path
import os,json,hashlib,time,shutil,subprocess
import numpy as np
R=Path('/data/netg/ACSG')
O=R/'entry_method_exploration/20260911_hnsw_selection_probe_v1'
D=R/'fast_router_diagnosis/20260908_v1'
E33=R/'entry_method_exploration/20260911_hnsw_edge_rl_v1'
E34=R/'entry_method_exploration/20260911_hnsw_rl_benchmark_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
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
 dump(p,dict(time=time.time(),files=[identity(x) for x in sorted(set(map(Path,files)))]))
def check(p):
 for x in read(p)['files']:
  f=Path(x['path']);s=f.stat();assert s.st_size==x['bytes'] and s.st_mtime_ns==x['mtime_ns'] and sha(f)==x['sha256'],f
def env():
 e=os.environ.copy();e.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1');return e
def score(ids,gt):return (ids[...,None]==gt[:,None,:10]).any(axis=-1).sum(axis=-1).astype(np.uint8)
