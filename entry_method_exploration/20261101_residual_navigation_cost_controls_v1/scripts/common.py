import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
import csv,hashlib,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];OLD=R.parent/'20261101_residual_navigation_diagnosis_v1'
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,sha256=sha(p))
def csvwrite(p,rows):
 with Path(p).open('w')as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
