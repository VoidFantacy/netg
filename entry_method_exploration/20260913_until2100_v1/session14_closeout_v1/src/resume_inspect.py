"""Read-only report integrity and handoff check; never invokes research or browser."""
from pathlib import Path
import hashlib
import json
import shutil

O = Path(__file__).resolve().parents[1]
C = O.parent
seal = json.loads((O / 'final_seal.json').read_text())
for row in seal['files']:
    p = Path(row['path'])
    assert p.stat().st_size == row['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'], str(p)
manifest = json.loads((O / 'delivery_manifest.json').read_text())
for row in manifest['files']:
    p = Path(row['path'])
    assert p.stat().st_size == row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'], str(p)
state = json.loads((C / 'state.json').read_text())
assert state['session14_status'] == 'COMPLETE_DELIVERY_SAFE_HANDOFF'
assert not state['day_goal_complete']
assert not any(state[k] for k in ['native_pids', 'offline_pids', 'pending_tool_sessions', 'session14_pending_tasks'])
assert all(state[k] == 0 for k in ['session14_NSG', 'session14_HNSW', 'session14_builds', 'session14_new_model_fits', 'session14_new_GT', 'session14_new_QPS'])
assert (state['total_new_NSG'], state['total_HNSW'], state['total_builds'], state['final_validation_QPS_points']) == (6854176, 17820080, 360, 50)
free = shutil.disk_usage('/data').free
assert free - 72 * 2**20 > 6.45 * 2**30
print(json.dumps(dict(status='PASS_SESSION14_DELIVERY_READY', seal_records=len(seal['files']),
    delivery_files=len(manifest['files']), free_GiB=free/2**30, new_ANN=0, day_goal_complete=False,
    delivery=str(O / 'delivery.md'), handoff=str(C / 'handoff_session14.md'),
    next_action='Supervisor final day delivery before21:00; no research tasks to restore. Host CLI exit verified separately.'), ensure_ascii=False, indent=2))
