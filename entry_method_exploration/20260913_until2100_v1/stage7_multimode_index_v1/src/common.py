from pathlib import Path
import os,sys,json,time,hashlib,shutil,resource
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parents[1];C=O.parent;R=Path('/data/netg/ACSG');D=R/'entry_method_exploration'
E24=D/'20260910_gt_topk_profiles_v1';E33=D/'20260911_hnsw_edge_rl_v1';E37=D/'20260912_offline_profile_rl_v1'
E46=D/'20260912_exact_feedback_cache_v1';E60=C/'stage1_support_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];FIELDS=['ids','distances','entries','route_ndc','graph_ndc']
DTYPES=[np.int32,np.float32,np.int32,np.uint32,np.uint32]
LABELS=['baseline','zero_mass2','sham_mass2']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity(p):
    p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def save(p,**kw):
    p=Path(p);assert not p.exists(),p;p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**kw)
def equal(a,b):
    for k in FIELDS:assert a[k].shape==b[k].shape and a[k].dtype==b[k].dtype and a[k].tobytes()==b[k].tobytes(),k
def raw_digest(out):
    h=hashlib.sha256()
    for k in FIELDS:h.update(k.encode());h.update(out[k].tobytes())
    return h.hexdigest()
def threads(cpu=8):
    assert os.sched_getaffinity(0)=={cpu}
    for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:assert os.environ[k]=='1'
    assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
def resources():
    assert shutil.disk_usage('/data').free>=7*(1<<30)
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<128*(1<<20)
def check(p):
    for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def normalize(a):return a/np.maximum(np.linalg.norm(a,axis=1,keepdims=True),1e-12)
def ihits(ids,gt):return np.array([len(set(map(int,x))&set(map(int,g[:10]))) for x,g in zip(ids,gt)],np.uint8)
