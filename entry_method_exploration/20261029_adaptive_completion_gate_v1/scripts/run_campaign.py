import os,sys,time,json,subprocess,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python';DS=['coco','deep10m_l2_v1','sift10m_bigann_l2_v1']
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def run(script,*args):subprocess.run([str(PY),str(R/'scripts'/script),*args],cwd=REPO,check=True)
def native(ds,mode):
 cfg=R/f'configs/{ds}.{"dev" if mode=="labels" else mode}.json';env=os.environ.copy()
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
 def pin():os.sched_setaffinity(0,{15})
 assert shutil.disk_usage('/data').free>.65*2**30 and shutil.disk_usage('/root').free>.7*2**30
 t=time.perf_counter();rss=0;threads=0
 with (R/f'reviews/{mode}_{ds}.log').open('x') as f:
  p=subprocess.Popen([str(R/'storage/benchmark'),mode,str(cfg)],cwd=REPO,env=env,preexec_fn=pin,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:
    v=dict(line.split(':',1) for line in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in line);threads=max(threads,int(v.get('Threads','0')));rss=max(rss,int(v.get('VmRSS','0 kB').split()[0])*1024)
   except FileNotFoundError:pass
   time.sleep(.25)
 rec=dict(dataset=ds,mode=mode,returncode=p.returncode,seconds=time.perf_counter()-t,max_observed_threads=threads,peak_rss=rss,affinity=[15]);dump(R/f'reviews/{mode}_{ds}.receipt.json',rec);print(json.dumps(rec),flush=True);assert p.returncode==0 and threads==1
if __name__=='__main__':
 run('diagnose.py')
 for ds in DS:
  dump(R/'state.json',dict(status='DEVELOPMENT_LABELS_AND_ACTION_COST',dataset=ds,default_changed=False));native(ds,'labels');run('fit.py',ds)
 frozen=[]
 for dd in ['src','configs','scripts']:
  frozen += [p for p in (R/dd).rglob('*') if p.is_file() and '__pycache__' not in str(p)]
 frozen += list((R/'storage/gates').rglob('*.json'))+list((R/'storage/oracle').rglob('*.u8'))+[R/'freeze.json',R/'protocol.md',R/'storage/benchmark']
 dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_QUALIFICATION_AND_FORMAL',files=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(frozen)]))
 for ds in DS:native(ds,'qualification');run('audit.py',ds,'qualification')
 dump(R/'reviews/qualification_complete.json',dict(status='PASS_36_QUALIFICATION_POINTS'))
 for ds in DS:
  dump(R/'state.json',dict(status='FROZEN_FORMAL_T1',dataset=ds,default_changed=False));native(ds,'formal');run('audit.py',ds,'formal')
 dump(R/'state.json',dict(status='FORMAL_COMPLETE_ANALYSIS_PENDING',default_changed=False));print('E193_FORMAL_COMPLETE',flush=True)
