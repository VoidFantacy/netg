from common import *
import subprocess
deadline=time.time()+7200
while not(R/'formal_complete.json').exists():
 assert time.time()<deadline;time.sleep(5)
for name in ['analyze.py','plot.py','report.py']:
 log=R/'reviews'/f'post_{Path(name).stem}.log';assert not log.exists();t=time.perf_counter()
 with log.open('w')as f:p=subprocess.run([sys.executable,str(R/'scripts'/name)],cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
 dump(R/'reviews'/f'post_{Path(name).stem}.json',dict(returncode=p.returncode,seconds=time.perf_counter()-t,source_sha=sha(R/'scripts'/name)));assert p.returncode==0,log.read_text()[-7000:];print('POST_PASS',name,flush=True)
dump(R/'postprocess_complete.json',dict(status='PASS_ANALYSIS_REPORT',final_findings_pending=True))
