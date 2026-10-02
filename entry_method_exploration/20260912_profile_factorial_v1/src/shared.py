from pathlib import Path
import os,sys,json,time,hashlib,shutil,resource,csv
import numpy as np
R=Path('/data/netg/ACSG')
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
E38=R/'entry_method_exploration/20260912_offline_profile_diagnosis_v1'
E39=R/'entry_method_exploration/20260912_fixed_profile_batch_diagnosis_v1'
E40=R/'entry_method_exploration/20260912_profile_payoff_attribution_v1'
O=Path(__file__).resolve().parents[1]
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];CELLS=['C','F','S','R']
FIELDS=['ids','distances','entries','route_ndc','graph_ndc']
sys.dont_write_bytecode=True
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def files(p):return sorted(x for x in p.rglob('*') if x.is_file())
def freeze(p,paths):
 assert not p.exists(),p
 dump(p,dict(files=[dict(path=str(x),bytes=x.stat().st_size,sha256=sha(x)) for x in sorted(set(paths))]))
def check(p):
 for f in read(p)['files']:assert sha(f['path'])==f['sha256'],f['path']
def save_np(p,**kw):
 assert not p.exists(),p
 p.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(p,**kw)
def equal(a,b):
 for k in FIELDS:
  assert a[k].shape==b[k].shape and a[k].dtype==b[k].dtype,k
  assert a[k].tobytes()==b[k].tobytes(),k
def resources():
 assert shutil.disk_usage(O).free>=10*(1<<30),'disk free <10GiB'
 assert sum(p.stat().st_size for p in files(O))<=64*(1<<20),'output >64MiB'
def threads(cpu):
 assert os.sched_getaffinity(0)=={cpu}
 for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:assert os.environ[key]=='1'
 n=next(int(line.split(':')[1]) for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('Threads:'))
 assert n==1
def cfg(ds):return read(O/'inputs'/ds/'config.json')
def case(ds):return next(x for x in read(O/'config.locked.json')['cases'] if x['dataset']==ds)
def score(ids,gt):return (ids[...,None]==gt[:,None,:10]).any(-2).sum(-1).astype(np.int16)
def writecsv(name,rows):
 assert rows and not (O/'results'/name).exists()
 with (O/'results'/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
