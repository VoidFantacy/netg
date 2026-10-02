"""Read-only session11 seal, terminal ledger and handoff inspection. No ANN or fitting."""
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
paths=[C/'reviews/session11_final_artifact_freeze.json']+[C/x/'reviews/final_artifact_freeze.json' for x in ['stage33_composed_repair_v1','stage34_final_selection_v1','stage35_final_comparison_v1']]+[C/'stage34_final_selection_v1/reviews/selection_artifact_freeze.json',C/'stage34_final_selection_v1/reviews/prescore_freeze.json',C/'stage35_final_comparison_v1/reviews/preselection_freeze.json',C/'stage35_final_comparison_v1/reviews/prequery_freeze.json']
for p in paths:
 for x in read(p)['files']:verify(x)
old=read(C/'candidate_inventory_v11.json');new=read(C/'candidate_inventory_v12.json')
assert len(new['candidates'])==77 and new['candidates'][:76]==old['candidates']
jobs=read(C/'session11_closeout/terminal_ledger.json')['jobs']
assert len(jobs)==4 and all(j['returncode']==0 and j['actual_tool_terminal_observed'] and j['threads']==1 and j['CPU']==15 for j in jobs)
assert all(a['completed_at']<=b['started_at'] for a,b in zip(jobs,jobs[1:]))
assert sum(j['actual_NSG'] for j in jobs)==781760 and sum(j['actual_HNSW'] for j in jobs)==640800
s=read(C/'state.json');assert s['session11_status']=='COMPLETE_SAFE_HANDOFF' and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions'] and not s['day_goal_complete']
assert not s['session11_final_feedback_used_for_training']
assert(s['total_new_NSG'],s['total_HNSW'],s['total_builds'],s['final_validation_QPS_points'])==(6854176,17820080,360,50)
free=shutil.disk_usage('/data').free;assert free-72*2**20>6.45*2**30
print(json.dumps(dict(status='PASS_SESSION11_READ_ONLY',epoch=time.time(),identity_records=checked,unique_files_hashed=len(cache),terminal_native_jobs=4,NSG=781760,HNSW=640800,ordinary_builds=0,vector_installs=1,new_final_QPS=50,final_wall_batches=250,free_GiB=free/2**30,E34_final_payload_access=True,final_feedback_to_training=False,day_goal_complete=False,next_action='Read handoff_session11 and latest supervisor notes; only report review/interpretation and21:00 delivery remain. No new queries or training.',process_scope='All owned tools terminal; supervisor independently checks host. Local /proc is isolated.'),indent=2))
