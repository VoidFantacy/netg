"""Same frozen dense matrix and audits; archive own packets between datasets."""
import json,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python';t=time.perf_counter()
freeze=json.loads((R/'dense_freeze.json').read_text());capacity=json.loads((R/'reviews/storage_preflight.json').read_text());sizes={x['dataset']:x for x in capacity['datasets']};completed=[]
for d in freeze['decisions']:
    ds=d['dataset']
    if not d['positive_points']:continue
    x=sizes[ds];required=max(x['actual_raw_packet_bytes']+x['trace_uncompressed_bytes'],2*x['actual_raw_packet_bytes']+x['trace_gzip_bytes_predicted'])+x['access_bytes']+x['metadata_allowance_bytes']
    assert shutil.disk_usage('/').free>required+.7*2**30,(ds,required,shutil.disk_usage('/').free)
    (R/'state.json').write_text(json.dumps(dict(status='RUNNING_DENSE_CONTROLS',dataset=ds,primary_points=448,primary_batches=1344,candidate_changed=False,default_changed=False,no_PDF=False,PDF_authorized=True,packet_storage='verified lossless solid archive after each completed audit'),indent=2)+'\n')
    for name,args in [('run_native.py',['dense',ds]),('analyze_dense.py',[ds,'dense_controls']),('audit_dense_results.py',[ds]),('compress_dense_traces.py',[ds]),('packet_archive.py',['archive','dense_controls',ds])]:
        subprocess.run([str(PY),str(R/'scripts'/name),*args],cwd=REPO,check=True)
    completed.append(ds);print(json.dumps(dict(dataset=ds,phase='DENSE_CONTROL_COMPLETE_AND_LOSSLESS_ARCHIVED')),flush=True)
(R/'dense_complete.json').write_text(json.dumps(dict(status='DENSE_STAGE_COMPLETE',datasets=completed,seconds=time.perf_counter()-t,packet_archive_time_in_suite=True,scientific_matrix_unchanged=True),indent=2)+'\n')
print('ALL_DENSE_COMPLETE',flush=True)
