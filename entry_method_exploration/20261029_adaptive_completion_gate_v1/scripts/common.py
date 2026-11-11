import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[name] = '1'
import csv,hashlib,json,sys
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
OLD=R.parent/'20261028_seven_dataset_scoring_v1'
DS=['deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1','coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
ANCHORS=['coco','deep10m_l2_v1','sift10m_bigann_l2_v1']
LABEL=dict(zip(DS,['Deep10M','SIFT10M','GIST1M','COCO','Flickr30k','WebVid','Yandex10M']))
sys.path.insert(0,str(OLD/'scripts'))
from io_data import gt,view
from packet_archive import read_bytes
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def arr(p,dtype):
 p=Path(p)
 return np.fromfile(p,dtype) if p.exists() else np.frombuffer(read_bytes(p),dtype=dtype).copy()
def csvwrite(p,rows):
 with Path(p).open('w') as f:
  w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def mask(ids,g,K):
 out=np.empty((len(g),K),bool)
 for lo in range(0,len(g),128):out[lo:lo+128]=(g[lo:lo+128,:K,None]==ids[lo:lo+128,None,:]).any(2)
 return out
