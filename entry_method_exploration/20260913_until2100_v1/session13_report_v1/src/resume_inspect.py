"""Read-only final delivery integrity. Does not start any analysis, browser or ANN."""
from pathlib import Path
import json,hashlib,shutil,time
O=Path(__file__).resolve().parents[1];C=O.parent
s=json.loads((O/'final_seal.json').read_text())
for x in s['files']:
    p=Path(x['path']);assert p.stat().st_size==x['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],str(p)
state=json.loads((C/'state.json').read_text())
assert not state['day_goal_complete']
assert state['session13_status']=='COMPLETE_REPORT_SAFE_HANDOFF'
assert not state['native_pids'] and not state['offline_pids'] and not state['pending_tool_sessions']
assert all(state[x]==0 for x in ['session13_NSG','session13_HNSW','session13_builds','session13_new_model_fits','session13_new_QPS'])
assert (state['total_new_NSG'],state['total_HNSW'],state['total_builds'],state['final_validation_QPS_points'])==(6854176,17820080,360,50)
assert hashlib.sha256((O/'report.html').read_bytes()).hexdigest()=='31108b1fdd477a6f56c3a0ca363ab22a5024182ca86ee13c358f9dbf475e529a'
free=shutil.disk_usage('/data').free
assert free-72*2**20>6.45*2**30
print(json.dumps(dict(status='PASS_SESSION13_DELIVERY_SEAL',files=len(s['files']),free_GiB=free/2**30,
    new_ANN=0,day_goal_complete=False,report=str(O/'report.md'),pdf=str(O/'report.pdf'),html=str(O/'report.html'),
    next_action='Read handoff_session13 and latest supervisor notes; complete day delivery. No pending experiment and no rerun required.',
    process_scope='No task launched by this inspector; original owned tools all terminal. Host CLI exit is checked separately by supervisor.'),ensure_ascii=False,indent=2))
