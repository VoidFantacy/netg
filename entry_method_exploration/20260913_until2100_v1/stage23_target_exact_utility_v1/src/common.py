from pathlib import Path
import os,sys,json,time,hashlib,shutil,csv
sys.dont_write_bytecode=True
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent;R=Path('/data/netg/ACSG')
E69=C/'stage10_exact_triple_utility_v1';E73=C/'stage14_compact_modes_v1';E79=C/'stage20_target_space_modes_v1';E80=C/'stage21_hub_conditioned_targets_v1';E81=C/'stage22_joint_view_partition_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];BANKS=['target10','conditional10','joint10'];MODELS=['baseline10','compact10',*BANKS,'exact_P','exact_mode']
FIELDS={'ids':('ids.i32',np.int32,10),'distances':('distances.f32',np.float32,10),'entries':('entry_ids.i32',np.int32,3),'graph_ndc':('graph_ndc.u32',np.uint32,1),'hits':('hits.u8',np.uint8,1),'mask':('hitmask.u16',np.uint16,1)}
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
def freeze(p,paths):dump(p,dict(epoch=time.time(),files=[identity(x) for x in sorted(set(map(Path,paths)))]))
def check(p):
 for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def resources():
 free=shutil.disk_usage('/data').free;used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file() and not p.is_symlink())
 assert used<32*2**20;assert free-(32*2**20-used)-72*2**20>6.65*2**30
 return dict(free_GiB=free/2**30,new_bytes=used)
def threads():
 assert os.sched_getaffinity(0)=={15}
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:assert os.environ[k]=='1'
 assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
def source(ds,m):
 if m.startswith('exact_'):return E69/'results'/ds/(m+'.npz')
 stage=E79 if m=='target10' else E81
 return stage/'results'/ds/'aux'/(m+'_L128')
def old_raw(ds,m):
 p=source(ds,m)
 if p.suffix=='.npz':return {k:a for k,a in dict(np.load(p)).items() if k in FIELDS}
 out={}
 for k,(name,dt,width) in FIELDS.items():
  a=np.fromfile(p/name,dt);out[k]=a.reshape(-1,width) if width>1 else a
 return out
def same(a,b,fields=('ids','distances','graph_ndc')):
 for k in fields:assert a[k].dtype==b[k].dtype and a[k].shape==b[k].shape and a[k].tobytes()==b[k].tobytes(),k
def save(p,**x):
 p=Path(p);assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**x)
def table(p,data):
 with Path(p).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
def score(ids,gt):
 h=[];ms=[]
 for r,g in zip(ids,gt):
  found=set(map(int,r));assert len(found)==10
  mask=sum(1<<j for j,v in enumerate(g[:10]) if int(v) in found);h.append(len(found&set(map(int,g[:10]))));ms.append(mask);assert h[-1]==mask.bit_count()
 return np.array(h,np.uint8),np.array(ms,np.uint16)
