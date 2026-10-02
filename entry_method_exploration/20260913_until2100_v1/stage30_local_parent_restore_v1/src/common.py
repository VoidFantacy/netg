from pathlib import Path
import os,sys,json,time,hashlib,shutil
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parents[1];C=O.parent;R=Path('/data/netg/ACSG')
E66=C/'stage7_multimode_index_v1';E73=C/'stage14_compact_modes_v1';E84=C/'stage25_query_shortcuts_v1'
E86=C/'stage27_edge_utility_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,paths):
 assert not Path(p).exists();dump(p,dict(epoch=time.time(),files=[identity(x) for x in sorted(set(map(Path,paths)))]))
def check(p):
 for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def resources():
 used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file() and not p.is_symlink());free=shutil.disk_usage('/data').free
 rp=read(C/'session10_resource_protocol.json');folders=list(map(Path,rp['stage_folders']))
 total=sum(p.stat().st_size for f in folders for p in f.rglob('*') if p.is_file() and not p.is_symlink())
 assert used<128*2**20 and total<192*2**20,(used,total)
 assert free-(192*2**20-total)-72*2**20>6.45*2**30,(used,total,free)
def threads():
 assert os.sched_getaffinity(0)=={15}
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:assert os.environ[k]=='1'
 assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
def save(p,**x):
 p=Path(p);assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**x)
def same(a,b,fields=('ids','distances','graph_ndc')):
 for k in fields:assert a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes(),k
FIELDS={'ids':('ids.i32',np.int32,10),'distances':('distances.f32',np.float32,10),'entries':('entry_ids.i32',np.int32,3),'graph_ndc':('graph_ndc.u32',np.uint32,1),'hits':('hits.u8',np.uint8,1),'mask':('hitmask.u16',np.uint16,1),'route_ndc':('route_ndc.u32',np.uint32,1)}
def raw(p,n=None):
 out={}
 for k,(f,dt,w) in FIELDS.items():
  a=np.fromfile(Path(p)/f,dt,count=-1 if n is None else n*w);out[k]=a.reshape(-1,w) if w>1 else a
 return out
def score(ids,gt):
 mask=np.zeros(len(ids),np.uint16)
 for j in range(10):mask|=np.any(ids==gt[:,j,None],axis=1).astype(np.uint16)<<j
 return np.array([int(x).bit_count() for x in mask],np.uint8),mask
