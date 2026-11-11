"""Sequential frozen formal measurement; no concurrent numerical work."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python';ANCHORS=['coco','deep10m_l2_v1','sift10m_bigann_l2_v1']
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def run(script,*args):
 subprocess.run([str(PY),str(R/'scripts'/script),*args],cwd=REPO,check=True)
def native(ds,qualify=False):
 mode='qualification' if qualify else 'formal';cfg=R/f'configs/{ds}{".qualification" if qualify else ""}.json';env=os.environ.copy()
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
 def pin():os.sched_setaffinity(0,{15})
 t=time.perf_counter();peak=0;threads=0
 with (R/f'reviews/{mode}_{ds}.log').open('x') as f:
  p=subprocess.Popen([str(R/'storage/benchmark'),mode,str(cfg)],cwd=REPO,env=env,preexec_fn=pin,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:
    vals={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in s};peak=max(peak,int(vals.get('VmRSS','0 kB').split()[0])*1024);threads=max(threads,int(vals.get('Threads','0')))
   except FileNotFoundError:pass
   time.sleep(.25)
 v=dict(dataset=ds,mode=mode,returncode=p.returncode,seconds=time.perf_counter()-t,max_observed_threads=threads,peak_sampled_rss_bytes=peak,affinity=[15],sampling_seconds=.25);dump(R/f'reviews/{mode}_{ds}.receipt.json',v);print(json.dumps(v),flush=True);assert p.returncode==0 and threads==1
def main():
 freeze=json.loads((R/'freeze.json').read_text())
 for x in freeze['files']:assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
 for ds in ANCHORS:
  dump(R/'state.json',dict(status='QUALIFICATION',dataset=ds,default_changed=False));native(ds,True);run('audit_native.py',ds,'qualification')
 dump(R/'reviews/qualification_complete.json',dict(status='PASS_ALL_36_QUALIFICATION_POINTS',points=36))
 for ds in ANCHORS:
  assert shutil.disk_usage('/root').free>1.4*2**30
  dump(R/'state.json',dict(status='RUNNING_FROZEN_FORMAL',dataset=ds,formal_points=39,formal_batches=117,default_changed=False));native(ds);run('analyze_native.py',ds);run('audit_native.py',ds)
 dump(R/'formal_complete.json',dict(status='PASS_ALL_FROZEN_FORMAL_POINTS',points=39,batches=117,datasets=ANCHORS))
 dump(R/'state.json',dict(status='FORMAL_COMPLETE_DIAGNOSTICS_NEXT',default_changed=False));run('diagnose.py');run('audit_diagnostics.py')
 dump(R/'state.json',dict(status='READY_FOR_PROOF_INTERPRETATION_AND_DOCUMENTATION',formal_points=39,formal_batches=117,default_changed=False));print('E192_READY_FOR_INTERPRETATION',flush=True)
if __name__=='__main__':main()
