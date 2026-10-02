from pathlib import Path
import os,sys,json,time,hashlib,shutil
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent;R=C.parents[1];E73=C/'stage14_compact_modes_v1';DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];N=3976
FIELDS={'ids':('ids.i32',np.int32,10),'distances':('distances.f32',np.float32,10),'entries':('entry_ids.i32',np.int32,3),'hits':('hits.u8',np.uint8,1),'mask':('hitmask.u16',np.uint16,1),'graph_ndc':('graph_ndc.u32',np.uint32,1),'route_ndc':('route_ndc.u32',np.uint32,1)}
def load_raw(p,n):
 a={}
 for k,(fn,dt,w) in FIELDS.items():
  v=np.fromfile(p/fn,dt);a[k]=v.reshape(n,w) if w>1 else v
 return a
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def identity(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=sha(p))
def freeze(p,paths):dump(p,dict(epoch=time.time(),files=[identity(x) for x in sorted(set(map(Path,paths)))]))
def check(p):
 for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def runtime():
 assert os.sched_getaffinity(0)=={15} and time.time()<1789290600
 assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'])
 assert next(int(x.split(':')[1]) for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:'))==1
 used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file() and not p.is_symlink());folders=[C/x for x in ['stage23_target_exact_utility_v1','stage24_sibling_links_v1','stage25_query_shortcuts_v1','stage26_query_gate_feasibility_v1']];total=sum(p.stat().st_size for f in folders for p in f.rglob('*') if p.is_file() and not p.is_symlink());assert used<12*2**20 and total<192*2**20 and shutil.disk_usage('/data').free-(12*2**20-used)-72*2**20>6.65*2**30
 return dict(stage_bytes=used,session_bytes=total,free_bytes=shutil.disk_usage('/data').free)
def features(q):
 q=q.astype(float);return q/np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-12)
