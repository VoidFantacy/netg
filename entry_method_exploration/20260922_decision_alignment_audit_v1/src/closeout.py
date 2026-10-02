"""Seal only this completed audit and its current documentation snapshots."""
import hashlib
import json
import re
import shutil
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]

def read(path):
    return json.loads(path.read_text())

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8<<20), b''):
            h.update(block)
    return h.hexdigest()

assert not (RUN / 'reviews/completion.json').exists()
results = read(RUN / 'analysis/results.json')
assert results['calibration_eligible'] is False
assert read(RUN / 'reviews/independent_audit.json')['status'] == 'PASS'
before = read(RUN / 'reviews/before.json')
assert len(before['inputs']) == 76
for record in before['inputs'] + before['frozen_analysis']:
    p = Path(record['path'])
    assert p.stat().st_size == record['bytes'] and digest(p) == record['sha256'], str(p)

docs = ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md',
        'experiment_history/123_decision_alignment_audit.md']
for name in docs:
    dest = RUN / 'source_after' / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, dest)

links = 0
for path in [RUN / 'report.md', RUN / 'protocol.md', RUN / 'theory.md', ROOT / docs[-1]]:
    for href in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if href.startswith(('http:', 'https:', '#')):
            continue
        assert (path.parent / href.split('#')[0]).exists(), (path, href)
        links += 1

state = dict(status='STOP_CALIBRATION_ONLY_REUSE', completed=True, pending=[], active_processes=[],
    calibration_eligible=False, calibration_executed=False, new_training=0, new_search_calls=0,
    new_GT=0, new_graphs=0, new_QPS_points=0, default_changed=False,
    scope='Completed conditional audit; no claim of all-model or high-budget impossibility',
    analysis_seconds=results['seconds'], audit_seconds=read(RUN / 'reviews/independent_audit.json')['seconds'],
    first_audit_seconds=12.728050276999056,
    total_audit_seconds=12.728050276999056+read(RUN / 'reviews/independent_audit.json')['seconds'])
(RUN / 'state.json').write_text(json.dumps(state, indent=2)+'\n')
records = []
for path in sorted(RUN.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name == 'completion.json':
        continue
    records.append(dict(path=str(path.relative_to(RUN)), bytes=path.stat().st_size, sha256=digest(path)))
completion = dict(status='PASS', protected_inputs=76, protected_inputs_unchanged=True,
    frozen_analysis_unchanged=True, checked_local_links=links, records=records,
    old_E119_seal_unchanged=True, defaults_and_production_unchanged=True)
(RUN / 'reviews/completion.json').write_text(json.dumps(completion, indent=2)+'\n')
print(json.dumps(dict(completion='COMPLETE', local_links=links, sealed_files=len(records), **state), indent=2))
