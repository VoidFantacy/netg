from pathlib import Path
import runpy,json,hashlib
C=Path(__file__).resolve().parents[1]
runpy.run_path(str(C/'src/resume_inspect_v11.py'))
f=json.loads((C/'session12_report_v1/final_seal.json').read_text())
for x in f['files']:
 p=Path(x['path']);assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],str(p)
s=json.loads((C/'state.json').read_text());assert not s['day_goal_complete'] and not s['native_pids'] and not s['offline_pids'] and not s['pending_tool_sessions']
print('PASS_SESSION12_REPORT_SEAL',len(f['files']),'day_goal_complete=false; no new experiments')
