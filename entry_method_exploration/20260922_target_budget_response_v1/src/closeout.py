"""Check the stopped branch, snapshot handoff documents and seal this version."""
from common import RUN, ROOT, read, dump, identity, protected_check
from pathlib import Path
import os
import re
import shutil
import time
from urllib.parse import unquote

start = time.monotonic()
assert not (RUN/'seal.json').exists()
lock = read(RUN/'config.locked.json')
response = read(RUN/'analysis/response.json')
info = read(RUN/'analysis/information.json')
assert response['information_control_eligible'] and not info['pass_all']
for name in ['search_complete', 'independent_audit', 'statistics_audit', 'theory_checks']:
    assert read(RUN/'reviews'/f'{name}.json')['status'] == 'PASS'
jobs = read(RUN/'reviews/jobs_v2.json')
assert all(j['exit_code'] == 0 for j in jobs)
assert sum(j['reserved_calls'] for j in jobs) == lock['planned_NSG_calls']
assert sum(j['seconds'] for j in jobs if j['reserved_calls']) < lock['total_search_seconds_cap']
for job in jobs:
    path = Path('/proc')/str(job['pid'])/'cmdline'
    if path.exists():
        assert job['argv'][0].encode() not in path.read_bytes().split(b'\0'), job['pid']
protected_check()
for name in ['execution_started_v2.json', 'pre_response_information_design.json',
             'information_source_frozen.json', 'header_dependencies.json']:
    for item in read(RUN/'reviews'/name)['files']:
        assert identity(item['path']) == item, item['path']
assert identity(RUN/'bin/evaluate') == read(RUN/'reviews/binary.json')

docs = ['summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'AGENTS.md',
        'experiment_history/README.md', 'experiment_history/124_target_budget_response.md']
links = 0
for name in ['report.md', 'theory.md', 'literature_addendum.md']:
    path = RUN/name
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if '://' not in target and not target.startswith('#'):
            assert (path.parent/unquote(target.split('#')[0])).exists(), (path, target)
            links += 1
for name in docs:
    path = ROOT/name
    for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if RUN.name in target or '124_target_budget_response' in target:
            assert (path.parent/unquote(target.split('#')[0])).exists(), (path, target)
            links += 1
    out = RUN/'source_after'/name
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, out)
    assert path.read_bytes() == out.read_bytes()
for name in ['summary.md', 's-target.md']:
    assert 'STOP_TARGET_LOCAL_INFORMATION' in (ROOT/name).read_text().split('以下为')[0]
assert '测量尚未结束' not in (ROOT/'spec.md').read_text().split('2026-09-22 新增隔离')[0]

new_bytes = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
assert new_bytes < lock['max_new_bytes']
assert shutil.disk_usage(RUN).free > lock['min_free_gib']*(1<<30)
dump(RUN/'reviews/completion.json', dict(status='PASS', local_links_checked=links,
    snapshot_files=len(docs), bytes_before_seal=new_bytes, active_processes=[],
    protected_old_files=690, protected_original_headers=8, default_changed=False,
    completed_conditional_information_control=True, cheap_method_gate_passed=False,
    seconds=time.monotonic()-start))
dump(RUN/'state.json', dict(status='STOP_TARGET_LOCAL_INFORMATION', completed=True,
    active_processes=[], pending=[], default_changed=False, formal_QPS=False,
    response_gate_passed=True, information_gate_passed=False,
    conditional_cheap_method='not triggered: information gate failed',
    report='report.md', completed_unix=time.time()))
files = [p for p in RUN.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
sealed = [identity(p) for p in sorted(files)]
dump(RUN/'seal.json', dict(status='SEALED', created_unix=time.time(), files=sealed,
    excluded=['seal.json', '__pycache__'], scope='this version only; root docs preserved in source_after'))
for item in sealed:
    assert identity(item['path']) == item
print('COMPLETE', len(sealed), 'sealed files;', links, 'local links;', new_bytes, 'bytes', flush=True)
