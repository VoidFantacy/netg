from pathlib import Path
import runpy,json,hashlib
C=Path(__file__).resolve().parents[1];O=C/'session12_report_v1'
runpy.run_path(str(C/'src/resume_inspect_v11.py'))
for seal in ['final_seal.json','correction_seal.json']:
 for x in json.loads((O/seal).read_text())['files']:
  p=Path(x['path'])
  if seal=='final_seal.json' and p.name=='83_frozen_final_comparison.md':p=O/'history83_session12_addendum.md'
  assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],str(p)
s=json.loads((C/'state.json').read_text());assert not s['day_goal_complete'] and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions']
print('PASS_SESSION12_CORRECTED_SEALS; no pending experiments; day incomplete')
