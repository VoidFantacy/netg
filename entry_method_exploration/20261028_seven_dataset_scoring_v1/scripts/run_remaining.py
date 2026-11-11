"""Complete frozen controls, with audited byte-preserving storage between suites."""
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python'
def run(name,*args):
    print(json.dumps(dict(script=name,args=args)),flush=True)
    subprocess.run([str(PY),str(R/'scripts'/name),*args],cwd=REPO,check=True)
assert (R/'primary_complete.json').exists() and (R/'dense_freeze.json').exists()
for binding in ['postprocessing_binding.json','authorized_pdf_extension_binding.json','storage_archive_binding.json']:
    for x in json.loads((R/binding).read_text())['files']:
        assert hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
for ds in json.loads((R/'primary_complete.json').read_text())['datasets']:
    (R/'state.json').write_text(json.dumps(dict(status='ARCHIVING_COMPLETED_PRIMARY',dataset=ds,primary_points=448,primary_batches=1344,default_changed=False,no_PDF=False,PDF_authorized=True),indent=2)+'\n')
    run('packet_archive.py','archive','results',ds)
run('run_dense_archived.py')
run('run_archived_posthoc.py')
run('build_report.py')
run('compare_all_methods.py')
(R/'state.json').write_text(json.dumps(dict(status='READY_FOR_DETAILED_PDF_AND_FINAL_REVIEW',primary_points=448,primary_batches=1344,dense_complete=True,default_changed=False,no_PDF=False,PDF_authorized=True),indent=2)+'\n')
print('REPORT_READY_FOR_INTERPRETATION_PDF_AND_FINAL_VALIDATION',flush=True)
