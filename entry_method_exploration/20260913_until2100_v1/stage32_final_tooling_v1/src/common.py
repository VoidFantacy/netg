from pathlib import Path
import os,sys,json,time,hashlib,shutil
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parents[1];C=O.parent;R=Path('/data/netg/ACSG');E73=C/'stage14_compact_modes_v1';E74=C/'stage15_compact_wall_v1';DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];LS=[64,128,256,400,800]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def check(p):
 for x in read(p)['files']:
  st=Path(x['path']).stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'] and sha(x['path'])==x['sha256'],x['path']
def freeze(p,paths):assert not Path(p).exists();dump(p,dict(epoch=time.time(),files=[identity(x) for x in sorted(set(map(Path,paths)))]))
def threads():
 assert os.sched_getaffinity(0)=={15}
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:assert os.environ[k]=='1'
 assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
def resources():
 p=read(C/'session10_resource_protocol_v3.json');used=sum(f.stat().st_size for q in p['stage_folders'] for f in Path(q).rglob('*') if f.is_file() and not f.is_symlink());assert used<192*2**20 and shutil.disk_usage('/data').free-(192*2**20-used)-72*2**20>6.45*2**30

def table(p,rows):
 import csv
 p=Path(p);assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',newline='') as f:
  if rows:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
