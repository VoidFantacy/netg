"""Read-only session10 inspection. No ANN, fit, or final payload read."""
from pathlib import Path
import json,hashlib,shutil,time
C=Path(__file__).resolve().parents[1];cache={};checked=0
def read(p):return json.loads(Path(p).read_text())
def verify(x):
 global checked
 p=Path(x['path']);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8<<20),b''):h.update(b)
  cache[key]=h.hexdigest()
 assert s.st_size==x['bytes'] and cache[key]==x['sha256'],str(p)
 if 'mtime_ns' in x:assert s.st_mtime_ns==x['mtime_ns'],str(p)
 checked+=1
for path in [C/'reviews/session10_final_artifact_freeze.json']+[C/x/'reviews/final_artifact_freeze.json' for x in ['stage30_local_parent_restore_v1','stage31_cross_source_restore_v1','stage32_final_tooling_v1']]+[C/'stage30_local_parent_restore_v1/supplement_training_v1/final_freeze.json',C/'session10_report/input_freeze_v2.json']:
 for x in read(path)['files']:verify(x)
old=read(C/'candidate_inventory_v10.json');new=read(C/'candidate_inventory_v11.json');assert new['candidates'][:68]==old['candidates'] and len(new['candidates'])==76
for m in new['candidates'][68:]:
 for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol','gate','cost']:verify(m[k])
assert sum(m['selectable_for_final'] for m in new['candidates'][68:])==3
jobs=read(C/'session10_closeout/terminal_ledger.json')['jobs'];assert len(jobs)==12 and all(j['returncode']==0 and j['actual_tool_terminal_observed'] and j['threads']==1 and j['CPU']==15 for j in jobs);assert all(a['completed_at']<=b['started_at'] for a,b in zip(jobs,jobs[1:]));assert sum(j['actual_NSG'] for j in jobs)==346556 and sum(j['actual_HNSW'] for j in jobs)==3578928
s=read(C/'state.json');assert s['session10_status']=='COMPLETE_SAFE_HANDOFF' and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions'] and not s['day_goal_complete'];assert(s['total_new_NSG'],s['total_HNSW'],s['total_builds'],s['final_validation_QPS_points'])==(6072416,17179280,360,0)
free=shutil.disk_usage('/data').free;assert free-72*2**20>6.45*2**30
print(json.dumps(dict(status='PASS_SESSION10_READ_ONLY',epoch=time.time(),identity_records=checked,unique_files_hashed=len(cache),terminal_native_jobs=12,NSG=346556,HNSW=3578928,ordinary_builds=0,new_QPS=0,free_GiB=free/2**30,E34_final_payload_access=False,next_action='Read handoff_session10 and latest supervisor notes. E89-E91 complete; actual final selection, protocol, matrix preparation and native execution remain pending.',process_scope='Owned tools all terminal; supervisor independently checks host. Local /proc is isolated.'),indent=2))
