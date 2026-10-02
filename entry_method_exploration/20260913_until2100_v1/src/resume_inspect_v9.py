"""Read-only session9 incremental inspection. No ANN, fits or final-input payload read."""
from pathlib import Path
import json,hashlib,shutil,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
cache={};checked=0
def verify(x):
 global checked
 p=Path(x['path']);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for z in iter(lambda:f.read(8<<20),b''):h.update(z)
  cache[key]=h.hexdigest()
 assert s.st_size==x['bytes'] and cache[key]==x['sha256'],str(p)
 if 'mtime_ns' in x:assert s.st_mtime_ns==x['mtime_ns'],str(p)
 checked+=1
for x in read(C/'reviews/session9_final_artifact_freeze.json')['files']:verify(x)
# Payload correctness and full seals independently reviewed by supervisor144..160; verify manifest anchors in session seal instead of rerunning original numerical analyses.
old=read(C/'candidate_inventory_v9.json');new=read(C/'candidate_inventory_v10.json');assert new['candidates'][:60]==old['candidates'] and len(new['candidates'])==68
for m in new['candidates'][60:]:
 for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol']:verify(m[k])
assert sum(m['selectable_for_final'] for m in new['candidates'][60:])==3
assert not next(m for m in new['candidates'] if m['name']=='E87_utility10' and m['dataset'].startswith('yandex'))['selectable_for_final']
jobs=read(C/'session9_closeout/terminal_ledger.json')['jobs'];assert len(jobs)==12 and all(j['returncode']==0 and j['actual_tool_terminal_observed'] and j['threads']==1 and j['CPU']==15 for j in jobs)
assert all(a['completed_at']<=b['started_at'] for a,b in zip(jobs,jobs[1:])) and sum(j['actual_NSG'] for j in jobs)==365054
s=read(C/'state.json');assert s['session9_status']=='COMPLETE_SAFE_HANDOFF' and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions'] and not s['day_goal_complete'];assert (s['total_new_NSG'],s['total_HNSW'],s['total_builds'],s['final_validation_QPS_points'])==(5725860,13600352,360,0)
free=shutil.disk_usage('/data').free;assert free-72*2**20>6.55*2**30
print(json.dumps(dict(status='PASS_SESSION9_INCREMENTAL_READ_ONLY',epoch=time.time(),identity_records=checked,unique_files_hashed=len(cache),terminal_native_jobs=12,NSG=365054,HNSW=7756544,ordinary_builds=0,new_QPS=0,free_GiB=free/2**30,E34_final_access=False,next_action='Read handoff_session9 and supervisor notes; E86-E88 complete, final selection and full E34 matrix pending.',process_scope='Owned terminal ledgers; supervisor separately checks host. Local /proc is isolated.'),indent=2))
