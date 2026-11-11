import json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
while not (R/'reviews/formal_complete.json').exists():time.sleep(2)
assert json.loads((R/'reviews/formal_complete.json').read_text())['status']=='PASS_FROZEN_FOUR_WINDOW_MATRIX'
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='1'
for name in ['analyze_v2','audit_stdlib','diagnose_shortlist','summarize']:
    start=time.perf_counter();log=R/'reviews'/f'{name}.log'
    with log.open('w') as f:
        p=subprocess.Popen([sys.executable,str(R/'scripts'/f'{name}.py')],stdout=f,stderr=subprocess.STDOUT)
        (R/'reviews/postprocess_active.json').write_text(json.dumps(dict(stage=name,pid=p.pid,log=str(log))))
        code=p.wait()
    receipt=dict(stage=name,returncode=code,seconds=time.perf_counter()-start,log=str(log))
    (R/'reviews'/f'{name}.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    assert code==0,receipt
    print('POSTPROCESSED',name,receipt['seconds'],flush=True)
(R/'reviews/postprocess_complete.json').write_text(json.dumps(dict(status='PASS_ANALYSIS_AUDIT_AND_TABLE_REPORT'))+'\n')
