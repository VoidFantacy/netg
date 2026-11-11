from common import *
import subprocess
deadline=time.time()+7200
while not (R/'formal_complete.json').exists():
    assert time.time()<deadline,'formal matrix not complete within observer deadline'
    time.sleep(5)
for name in ['analyze.py','audit.py','source_chain.py','geometry.py','plot.py','report_v2.py']:
    p=R/'reviews'/f'post_{Path(name).stem}.log';assert not p.exists(),p
    t=time.perf_counter()
    with p.open('w') as f:run=subprocess.run([sys.executable,str(R/'scripts'/name)],cwd=REPO,stdout=f,stderr=subprocess.STDOUT)
    dump(R/'reviews'/f'post_{Path(name).stem}.json',dict(script=name,returncode=run.returncode,seconds=time.perf_counter()-t,source_sha=sha(R/'scripts'/name)))
    assert run.returncode==0,(name,p.read_text()[-6000:]);print('POST_PASS',name,round(time.perf_counter()-t,2),flush=True)
dump(R/'postprocess_complete.json',dict(status='PASS_ANALYSIS_SOURCE_GEOMETRY_AUDIT_REPORT',human_findings_and_document_sync_pending=True))
