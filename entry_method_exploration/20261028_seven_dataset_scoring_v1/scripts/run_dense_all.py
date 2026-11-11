import json,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python';t=time.perf_counter();freeze=json.loads((R/'dense_freeze.json').read_text());completed=[]
for d in freeze['decisions']:
 ds=d['dataset']
 if not d['positive_points']:continue
 assert shutil.disk_usage('/').free>.7*2**30
 (R/'state.json').write_text(json.dumps(dict(status='RUNNING_DENSE_CONTROLS',dataset=ds,primary_points=448,primary_batches=1344,candidate_changed=False,default_changed=False,no_PDF=True),indent=2)+'\n')
 for name,args in [('run_native.py',['dense',ds]),('analyze_dense.py',[ds,'dense_controls']),('audit_dense_results.py',[ds]),('compress_dense_traces.py',[ds])]:subprocess.run([str(PY),str(R/'scripts'/name),*args],cwd=REPO,check=True)
 completed.append(ds);print(json.dumps(dict(dataset=ds,phase='DENSE_CONTROL_COMPLETE')),flush=True)
(R/'dense_complete.json').write_text(json.dumps(dict(status='DENSE_STAGE_COMPLETE',datasets=completed,seconds=time.perf_counter()-t),indent=2)+'\n')
