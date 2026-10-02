"""Read-only incremental session7 check; no ANN, NumPy, final-query decoding, or old bulk replay."""
from pathlib import Path
import hashlib,json,shutil,time,os
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
checked=0
# E79/E80 source/model/raw/final already independently accepted by supervisor107/108/111..113.
# This resume checks their sealed manifest anchors saved in session7 closeout, and new E81 payload.
for p in [C/'stage22_joint_view_partition_v1/reviews/final_artifact_freeze.json',C/'reviews/session7_final_artifact_freeze.json']:
 for r in read(p)['files']:assert sha(r['path'])==r['sha256'],r['path'];checked+=1
old=read(C/'candidate_inventory_v7.json');new=read(C/'candidate_inventory_v8.json');assert new['candidates'][:50]==old['candidates'] and len(new['candidates'])==52
for candidate in new['candidates'][50:]:
 for k in ['W','graph','mapping','tie_ids','evaluator','development_configuration','protocol']:
  r=candidate[k];assert sha(r['path'])==r['sha256'];checked+=1
jobs=[]
for stage in ['stage20_target_space_modes_v1','stage21_hub_conditioned_targets_v1','stage22_joint_view_partition_v1']:
 jj=read(C/stage/'logs/jobs.json');assert len(jj)==4 and all(j['status']=='COMPLETE' and j['returncode']==0 for j in jj);jobs+=jj
state=read(C/'state.json');assert state['session7_status']=='COMPLETE_SAFE_HANDOFF' and not state['native_pids'] and state['offline_tool_status']=='TERMINAL_EXIT0';assert not state['day_goal_complete']
free=shutil.disk_usage('/data').free;assert free>=6.8*(1<<30)+68*(1<<20)
print(json.dumps(dict(status='PASS_SESSION7_INCREMENTAL_READ_ONLY_RESUME',epoch=time.time(),checked_identity_records=checked,free_GiB=free/(1<<30),session7_NSG=sum(j['actual_NSG'] for j in jobs),terminal_native_jobs=len(jobs),process_scope='Each exec has an isolated PID namespace. Original tool terminal ledger and within-run child checks establish session-owned completion; supervisor performs host-wide process check.',next_action='Read handoff_session7 and next_stage_design_session7; do not rerun completed E79/E80/E81. Final E34 remains pending.',campaign_state=state),ensure_ascii=False,indent=2))
