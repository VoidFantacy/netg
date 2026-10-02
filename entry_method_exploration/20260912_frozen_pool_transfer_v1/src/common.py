from pathlib import Path
import os,sys,json,time,hashlib,shutil,csv,ast
import numpy as np
R=Path('/data/netg/ACSG');O=Path(__file__).resolve().parents[1]
E37=R/'entry_method_exploration/20260912_offline_profile_rl_v1'
E57=R/'entry_method_exploration/20260912_expanded_final_comparison_v1'
E58=R/'entry_method_exploration/20260912_accepted_action_conflicts_v1'
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def files(p):return sorted(x for x in p.rglob('*') if x.is_file())
def freeze(p,paths):
 assert not p.exists();dump(p,dict(files=[dict(path=str(x),bytes=x.stat().st_size,sha256=sha(x)) for x in sorted(set(map(Path,paths)))]))
def check(p):
 for x in read(p)['files']:assert sha(x['path'])==x['sha256'],x['path']
def start():
 assert os.sched_getaffinity(0)=={8}
 assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'])
 assert next(int(l.split(':')[1]) for l in Path('/proc/self/status').read_text().splitlines() if l.startswith('Threads:'))==1
 assert shutil.disk_usage(O).free>=7*(1<<30) and sum(p.stat().st_size for p in files(O))<32*(1<<20)
def table(name,rows):
 with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
