import json,sys,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];PY=REPO/'.venv_cpu/bin/python'
order=['deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1','coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
def run(name,*args):
 p=subprocess.run([str(PY),str(R/'scripts'/name),*args],cwd=REPO);assert p.returncode==0,(name,args,p.returncode)
assert (R/'freeze.json').exists();allstart=time.perf_counter()
for ds in order:
 assert shutil.disk_usage('/').free>.7*2**30
 (R/'state.json').write_text(json.dumps(dict(status='RUNNING_PRIMARY',dataset=ds,completed_datasets=[x for x in order if (R/f'analysis/{x}/summary.json').exists()],planned_primary_points=448,no_PDF=True,default_changed=False),indent=2)+'\n')
 run('run_native.py','formal',ds)
 run('analyze.py',ds)
 run('audit_results.py',ds)
 run('compress_traces.py',ds)
 print(json.dumps(dict(dataset=ds,phase='PRIMARY_DATASET_COMPLETED_AND_AUDITED',elapsed_seconds=time.perf_counter()-allstart)),flush=True)
(R/'primary_complete.json').write_text(json.dumps(dict(status='PRIMARY_MATRIX_COMPLETE',datasets=order,points=448,batches=1344,seconds=time.perf_counter()-allstart),indent=2)+'\n');print('ALL_PRIMARY_COMPLETE',flush=True)
