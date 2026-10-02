"""Read-only readiness check. Does not import NumPy/native or run ANN."""
from pathlib import Path
import hashlib,json,shutil,time,re,os
C=Path(__file__).resolve().parents[1];R=C.parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
checked=0
for stage in ['stage1_support_v1','stage2_missing_targets_v1','stage3_missing_factorial_v1']:
    for row in read(C/stage/'reviews/final_artifact_freeze.json')['files']:
        assert sha(row['path'])==row['sha256'],row['path'];checked+=1
    assert all(x['status']=='COMPLETE' for x in read(C/stage/'logs/jobs.json'))
for row in read(C/'candidate_inventory.json')['candidates']:
    for key in ['W','graph','mapping']:assert sha(row[key]['path'])==row[key]['sha256'];checked+=1
assert shutil.disk_usage('/data').free>=7*(1<<30)
processes=[]
for p in Path('/proc').glob('[0-9]*/cmdline'):
    try:cmd=p.read_bytes().replace(b'\0',b' ').decode(errors='replace')
    except (OSError,ProcessLookupError):continue
    if 'entry_method_exploration/' in cmd and re.search(r'/src/(run|train|deploy|prepare)\.py(?:\s|$)',cmd) and 'python' in cmd and not re.search(r'(^|/)(bash|sh) ',cmd):processes.append(dict(pid=int(p.parent.name),cmd=cmd))
assert not processes,processes
print(json.dumps(dict(status='PASS_READ_ONLY_RESUME',epoch=time.time(),checked_files=checked,free_GiB=shutil.disk_usage('/data').free/(1<<30),active_native_or_training=processes,
    campaign_state=read(C/'state.json'),next_design=str(C/'next_stage_design.md'),scope='Historical development data; no new ANN/QPS/GT; next method remains unimplemented; user day authorization persists'),indent=2))
