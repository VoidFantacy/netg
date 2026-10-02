"""Read-only session8 incremental integrity check, no ANN or final input access."""
from pathlib import Path
import json,hashlib,shutil,time
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
cache={};records=0
def verify(r):
 global records
 p=Path(r['path']);s=p.stat();key=(str(p),s.st_size,s.st_mtime_ns)
 if key not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
  cache[key]=h.hexdigest()
 assert s.st_size==r['bytes'] and cache[key]==r['sha256'],str(p);records+=1
# E82/E83/E84 payloads independently reviewed by supervisor126/128..136.
# Verify their manifest anchors in the final session seal; do not re-run numerical proofs.
for seal in [C/'reviews/session8_final_artifact_freeze.json',C/'stage26_query_gate_feasibility_v1/reviews/final_artifact_freeze.json']:
 for r in read(seal)['files']:verify(r)
old=read(C/'candidate_inventory_v8.json');new=read(C/'candidate_inventory_v9.json');assert new['candidates'][:52]==old['candidates'] and len(new['candidates'])==60
for m in new['candidates'][52:]:
 for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol']:verify(m[k])
assert not new['offline_E85']['selectable_for_final']
for r in new['offline_E85']['models']:verify(r)
ns=0;terminal=0
for stage in ['stage23_target_exact_utility_v1','stage24_sibling_links_v1','stage25_query_shortcuts_v1']:
 jobs=read(C/stage/'logs/jobs.json');assert all(j['status']=='COMPLETE' for j in jobs);terminal+=len(jobs)
 if stage.startswith('stage23'):
  ns+=sum(j['native']['NSG'] for j in jobs);assert all(j['native']['actual_threads']==1 for j in jobs)
 else:
  assert all(j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jobs);ns+=sum(j['actual_NSG'] for j in jobs)
assert ns==266834 and terminal==10
s=read(C/'state.json');assert s['session8_status']=='COMPLETE_SAFE_HANDOFF' and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions'] and not s['day_goal_complete'];assert s['session8_NSG']==ns and s['session8_HNSW']==339072 and s['total_new_NSG']==5360806 and s['total_HNSW']==5843808
free=shutil.disk_usage('/data').free;assert free>=6.65*2**30+72*2**20
print(json.dumps(dict(status='PASS_SESSION8_INCREMENTAL_READ_ONLY',epoch=time.time(),checked_identity_records=records,unique_files_hashed=len(cache),terminal_NSG_jobs=terminal,NSG=ns,HNSW=339072,free_GiB=free/2**30,E34_final_access=False,next_action='Read handoff_session8 and supervisor notes; completed E82-E85 must not rerun. Day final comparison remains pending.',process_scope='Actual tool terminal ledgers establish session-owned completion. Supervisor performs separate host-wide check; isolated /proc cannot prove host absence.'),indent=2))
