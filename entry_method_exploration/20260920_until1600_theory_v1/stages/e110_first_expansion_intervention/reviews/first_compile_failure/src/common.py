import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import json,time,hashlib
from pathlib import Path
import numpy as np
RUN=Path(__file__).resolve().parents[1];TB=RUN.parents[1];ROOT=TB.parents[1]
def read(p):return json.loads(Path(p).read_text())
LOCK=read(RUN/'config.locked.json')
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(16<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,sha256=sha(p))
def protected_check():
 for r in read(RUN/'reviews/protected_before.json'):assert sha(r['path'])==r['sha256'],r['path']
 for c in LOCK['datasets'].values():
  s=Path(c['index']).stat();assert s.st_size==c['index_stat']['bytes'] and s.st_mtime_ns==c['index_stat']['mtime_ns']
def deadline():assert time.time()<LOCK['deadline_unix'],'15:50 search cutoff'
