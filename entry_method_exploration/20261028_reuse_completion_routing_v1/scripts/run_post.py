import json,os,subprocess,sys,time,hashlib,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for role in ['results','calibration']:
 for ds in ['coco','deep10m_l2_v1']:assert (R/role/ds/'complete.json').exists()
steps=[['analyze.py','calibration'],['analyze.py','formal'],['trace_audit.py','calibration'],['trace_audit.py','formal'],['audit_calibration.py'],['audit_results.py'],['audit_scores.py'],['role_and_model_audit.py'],['audit_comparisons.py']]
env=os.environ.copy()
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:env[k]='1'
binding=dict(status='POSTPROCESSING_CODE_BOUND_BEFORE_QUALITY_READ',timestamp=datetime.datetime.now().isoformat(),files=[dict(path=str(R/'scripts'/name),sha256=hashlib.sha256((R/'scripts'/name).read_bytes()).hexdigest()) for name in sorted({s[0] for s in steps})]);(R/'reviews/postprocessing_binding.json').write_text(json.dumps(binding,indent=2)+'\n')
for i,step in enumerate(steps):
 t=time.perf_counter()
 with (R/f'reviews/post_{i}_{step[0]}.log').open('x') as log:p=subprocess.run([sys.executable,str(R/'scripts'/step[0]),*step[1:]],env=env,stdout=log,stderr=subprocess.STDOUT)
 v=dict(step=step,returncode=p.returncode,seconds=time.perf_counter()-t);(R/f'reviews/post_{i}.receipt.json').write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v),flush=True)
 if p.returncode:raise SystemExit(p.returncode)
