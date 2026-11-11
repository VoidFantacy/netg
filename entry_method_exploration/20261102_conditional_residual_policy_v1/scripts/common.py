import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import csv,gzip,hashlib,json,subprocess,sys,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
OLD=R.parent/'20261101_residual_bottleneck_separation_v1'
DS=['coco','webvid2_5m_light_v1']
STATES=[(100,100),(100,200),(100,400),(1,200)]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def csvwrite(p,rows):
    with open(p,'w') as f:
        w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
def budget():
    s=os.statvfs('/data');assert s.f_bfree*s.f_frsize>10*2**30,'persistent free-space floor'
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<2*2**30,'2GiB new evidence cap'
def run(argv,log):
    budget();start=time.perf_counter()
    with open(log,'w') as f:
        p=subprocess.Popen(argv,cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
        dump(R/'live_process.json',dict(pid=p.pid,argv=argv,log=str(log),start_unix=time.time()))
        code=p.wait()
    rec=dict(argv=argv,returncode=code,seconds=time.perf_counter()-start,log=str(log))
    dump(str(log)+'.receipt.json',rec)
    assert code==0,rec
    return rec
