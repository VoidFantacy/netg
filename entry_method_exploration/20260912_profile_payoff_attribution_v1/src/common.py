from pathlib import Path
import os, json, time, csv, hashlib, shutil, resource, itertools
import numpy as np
R=Path('/data/netg/ACSG')
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
E38=R/'entry_method_exploration/20260912_offline_profile_diagnosis_v1'
E39=R/'entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1'
O=Path(__file__).resolve().parents[1]
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
LABELS=[f'action{i}' for i in range(8)]+['center']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def files(p):return sorted(q for q in p.rglob('*') if q.is_file())
def freeze(p,paths):
 assert not p.exists(),p
 dump(p,dict(files=[dict(path=str(x),bytes=x.stat().st_size,sha256=sha(x)) for x in sorted(set(paths))]))
def check(p):
 for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def writecsv(name,rows):
 assert rows and not (O/'results'/name).exists(),name
 with (O/'results'/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def save_np(p,**kw):
 assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**kw)
def score(ids,gt):return (ids[...,None]==gt[:,None,:10]).any(axis=-2).sum(-1).astype(np.int16)
def cos(a,b):
 den=np.linalg.norm(a)*np.linalg.norm(b)
 return float(a@b/den) if den else None
def best(x):
 value=np.max(x);return 8 if x[8]==value else int(np.flatnonzero(x==value)[0])
def contract():
 assert os.sched_getaffinity(0)=={8}
 for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:assert os.environ[key]=='1'
 n=next(int(x.split(':')[1]) for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:'))
 assert n==1
 assert shutil.disk_usage(O).free>=10*(1<<30)
 assert sum(p.stat().st_size for p in files(O))<=64*(1<<20)
 resource.setrlimit(resource.RLIMIT_AS,(4*(1<<30),4*(1<<30)))
def inputs(ds):
 c=read(E39/'inputs'/ds/'config.json');rows=np.load(E39/'inputs'/ds/'rows.npz')['rows']
 q=np.fromfile(c['queries_file'],np.float32).reshape(4096,c['dim'])[rows].astype(float)
 gt=np.fromfile(c['gt_file'],np.int64).reshape(4096,100)[rows]
 source=np.fromfile(c['row_ids'],np.int64)[rows]
 hubs=np.fromfile(c['hub_ids'],np.int32)
 return c,rows,q,gt,source,hubs
def load_context(ds,name):
 c,rows,q,gt,source,hubs=inputs(ds)
 raw=[dict(np.load(E39/'results'/ds/name/(label+'.npz'))) for label in LABELS]
 assert all(np.array_equal(x['rows'],rows) for x in raw)
 h=np.stack([score(x['ids'],gt) for x in raw])
 w=[np.fromfile(E39/'models'/ds/name/label/'W.f32',np.float32).reshape(c['hub_count'],c['dim']).astype(float) for label in LABELS]
 return c,rows,q,gt,source,hubs,raw,h,w
