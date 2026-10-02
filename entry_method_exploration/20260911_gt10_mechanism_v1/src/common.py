import csv
import hashlib
import json
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
VERSIONS = {24: ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1',
            25: ROOT/'entry_method_exploration/20260910_selective_profile_gate_v1',
            26: ROOT/'entry_method_exploration/20260910_profile_shrinkage_v1'}
DATASETS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
LS = [64,128,256,400,800]
SOURCES = {}

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def track(path):
    path=Path(path).resolve();key=str(path)
    assert 'heldout' not in key.lower() and 'held_out' not in key.lower()
    if key not in SOURCES:
        st=path.stat();SOURCES[key]={'path':key,'bytes':st.st_size,'mtime_ns':st.st_mtime_ns,'sha256':sha(path)}
    return path

def read(path): return json.loads(track(path).read_text())
def arr(path,dtype,shape=None):
    a=np.fromfile(track(path),dtype=dtype)
    return a.reshape(shape) if shape is not None else a

def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n')

def csv_write(path,rows):
    if not rows:return
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def norm(a):
    # E24 reference.normalize uses precisely this float32 expression.
    return a / np.maximum(np.linalg.norm(a,axis=1,keepdims=True),1e-12)

def desc(x):
    x=np.asarray(x,dtype='float64');x=x[np.isfinite(x)]
    if not len(x):return None
    return dict(zip(['min','p25','median','mean','p75','p90','max'],
                    map(float,[x.min(),np.quantile(x,.25),np.median(x),x.mean(),np.quantile(x,.75),np.quantile(x,.9),x.max()])))

def bootstrap(d):
    d=np.asarray(d);rng=np.random.default_rng(20260911);vals=[]
    for _ in range(40): vals.extend(d[rng.integers(0,len(d),(50,len(d)))].mean(1)*10)
    return np.quantile(vals,[.025,.975]).tolist()

def effect(h0,h1):
    d=h1.astype('int32')-h0.astype('int32')
    return {'n':len(d),'positive':int((d>0).sum()),'neutral':int((d==0).sum()),'negative':int((d<0).sum()),
            'gain_hits':int(d[d>0].sum()),'lost_hits':int(-d[d<0].sum()),'net_hits':int(d.sum()),
            'delta_recall_pp':float(10*d.mean()) if len(d) else None,
            'rescued':int(((h0==0)&(h1>0)).sum()),'new_zero':int(((h0>0)&(h1==0)).sum()),
            'failed0':int((h0==0).sum()),'failed1':int((h1==0).sum())}

def load_point(folder,m,n):
    p=folder/m['name'];out={}
    for key,name,dtype,shape in [('hits','hits.u8','u1',(n,)),('masks','hitmask.u16','<u2',(n,)),
           ('ids','ids.i32','<i4',(n,10)),('bits','distances.f32','<u4',(n,10)),
           ('entries','entry_ids.i32','<i4',(n,3)),('r','route_ndc.u32','<u4',(n,)),('g','graph_ndc.u32','<u4',(n,))]:
        out[key]=arr(p/name,dtype,shape)
    return out
