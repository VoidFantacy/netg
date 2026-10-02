"""Preserve a zero-search compiler failure and copy omitted immutable headers."""
from common import *
import shutil

assert read(RUN/'state.json')['status'] == 'EXECUTION_ERROR'
jobs = read(RUN/'reviews/jobs.json')
assert len(jobs) == 1 and jobs[0]['reserved_calls'] == 0 and jobs[0]['exit_code'] == 1
dest = RUN/'reviews/failed_prebuild'
assert not dest.exists()
dest.mkdir()
for path in [RUN/'reviews/jobs.json', RUN/'reviews/execution_started.json', RUN/'state.json', RUN/'logs/build.log']:
    shutil.copy2(path,dest/path.name)
shutil.copytree(RUN/'src',dest/'src',ignore=shutil.ignore_patterns('__pycache__'))
headers = []
for path in (OLD/'src').rglob('*.h'):
    target = RUN/'src'/path.relative_to(OLD/'src')
    target.parent.mkdir(parents=True,exist_ok=True)
    assert not target.exists()
    shutil.copy2(path,target)
    assert sha(path) == sha(target)
    headers.append(identity(path))
assert headers
shutil.copy2(RUN/'src/run.py',RUN/'src/run_v2.py')
dump(RUN/'reviews/header_dependencies.json',dict(files=headers,source_bytes_unchanged=True,
    cause='prepare copied .cpp/.hpp but omitted the inherited .h dependency tree',
    failed_build_seconds=jobs[0]['seconds'],new_searches_before_repair=0,
    method_protocol_or_data_changed=False))
print('Preserved zero-search failure; copied',len(headers),'original headers')
