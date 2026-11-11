"""Wait for serial primary suite; run its predeclared dense controls and report."""
import hashlib, json, os, subprocess, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
REPO=R.parents[1]
PY=REPO/'.venv_cpu/bin/python'
while not (R/'primary_complete.json').exists():
    time.sleep(15)
binding=json.loads((R/'postprocessing_binding.json').read_text())
for x in binding['files']:
    assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
for script in ['select_dense_controls.py','run_dense_all.py','posthoc_scoring.py','build_report.py']:
    print(json.dumps(dict(stage='POST_PRIMARY',script=script)),flush=True)
    subprocess.run([str(PY),str(R/'scripts'/script)],cwd=REPO,check=True)
print('REPORT_READY_FOR_REVIEW_AND_DOCUMENT_SYNC',flush=True)
