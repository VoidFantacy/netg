#!/usr/bin/env python3
import os,json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def main():
 mode,ds=sys.argv[1:3];suffix='.'+mode if mode in ['profile','calibration'] else '';cfg=R/f'configs/{ds}{suffix}.json';c=json.loads(cfg.read_text())
 if mode=='qualification':
  c['queries']['n']=128;c['queries']['total_n']=10000;c['main_L']=[100,200,400];c['output_dir']=str(R/f'reviews/qualification_{ds}');cfg=R/f'configs/{ds}.qualification.json';cfg.write_text(json.dumps(c,indent=2)+'\n')
 env=os.environ.copy()
 for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
 def pin():os.sched_setaffinity(0,{15})
 t=time.perf_counter()
 with (R/f'reviews/{mode}_{ds}.log').open('x') as out:
  r=subprocess.run([str(R/'bin/cost_budget'),mode,str(cfg)],env=env,preexec_fn=pin,stdout=out,stderr=subprocess.STDOUT)
 receipt=dict(mode=mode,dataset=ds,returncode=r.returncode,seconds=time.perf_counter()-t)
 (R/f'reviews/{mode}_{ds}.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True);sys.exit(r.returncode)
if __name__=='__main__':main()
