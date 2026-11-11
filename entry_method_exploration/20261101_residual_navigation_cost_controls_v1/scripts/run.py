from common import *
import subprocess,shutil
for x in read(R/'formal_freeze.json')['files']:assert sha(x['path'])==x['sha256'],x['path']
done=[]
for ds in DS:
 for w in ['A','B']:
  assert shutil.disk_usage('/data').free>200<<20,'data reserve';cp=R/'configs'/f'{ds}.{w}.json';t=time.perf_counter();log=R/'reviews'/f'{ds}.{w}.log';assert not log.exists()
  with log.open('w')as f:p=subprocess.run(['taskset','-c','15',str(R/'storage/benchmark'),str(cp)],cwd=REPO,stdout=f,stderr=subprocess.STDOUT,timeout=7200)
  dump(R/'reviews'/f'{ds}.{w}.receipt.json',dict(returncode=p.returncode,seconds=time.perf_counter()-t,config=str(cp)));assert p.returncode==0,log.read_text()[-5000:]
  d=read(Path(read(cp)['output_dir'])/'complete.json');done.append({k:d[k]for k in ['dataset','window','points','batches','seconds']});dump(R/'state.json',dict(status='RUNNING_FROZEN_COST_CONTROLS',completed=done,default_changed=False));print(ds,w,'PASS',d['points'],round(d['seconds'],2),flush=True)
expected=read(R/'selection_freeze.json');assert sum(x['points']for x in done)==expected['formal_points'];dump(R/'formal_complete.json',dict(status='PASS_E196_ALL_FROZEN_POINTS',completed=done,points=expected['formal_points'],batches=expected['formal_batches']));dump(R/'state.json',dict(status='NATIVE_COMPLETE_ANALYSIS_PENDING',default_changed=False,points=expected['formal_points'],batches=expected['formal_batches']))
