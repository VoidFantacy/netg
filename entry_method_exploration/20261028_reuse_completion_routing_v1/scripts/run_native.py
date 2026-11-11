import os,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
mode,ds=sys.argv[1:3];suffix='.'+mode if mode in ['qualification','calibration'] else '';cfg=R/f'configs/{ds}{suffix}.json';env=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
def pin():os.sched_setaffinity(0,{15})
t=time.perf_counter();peak=0;maxthreads=0
with (R/f'reviews/{mode}_{ds}.log').open('x') as out:
 p=subprocess.Popen([str(R/'bin/reuse'),mode,str(cfg)],env=env,preexec_fn=pin,stdout=out,stderr=subprocess.STDOUT)
 while p.poll() is None:
  try:
   lines=Path(f'/proc/{p.pid}/status').read_text().splitlines();val={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in lines if ':' in s};peak=max(peak,int(val.get('VmRSS','0 kB').split()[0])*1024);maxthreads=max(maxthreads,int(val.get('Threads','0')))
  except FileNotFoundError:pass
  time.sleep(.25)
rc=p.returncode;v=dict(mode=mode,dataset=ds,returncode=rc,seconds=time.perf_counter()-t,peak_sampled_rss_bytes=peak,max_observed_threads=maxthreads,rss_sampling_seconds=.25)
(R/f'reviews/{mode}_{ds}.receipt.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True);sys.exit(rc)
