import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='1'
import csv,hashlib,json,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
OLD=R.parent/'20261028_seven_dataset_scoring_v1'
E194=R.parent/'20261030_residual_optimization_stability_v1'
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1','deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1']
LS=[100,128,160,200,256,320,400,512,640,800,1000]
NAV=['ONEHOP96','DIST96','DIST384','NOVEL96','NOVEL384','REP384']
sys.path.insert(0,str(OLD/'scripts'))
from io_data import view,gt
def read(p):return json.loads(Path(p).read_text())
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p,full=True):
    p=Path(p);s=p.stat();v=dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,inode=s.st_ino)
    if full:v['sha256']=sha(p)
    return v
def csvwrite(p,rows):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
