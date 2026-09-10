#!/usr/bin/env python3
"""Build only the independent P3 hierarchy executable into a new directory."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--sanitize', action='store_true')
    p.add_argument('--compiler', default='g++')
    a = p.parse_args()
    if time.time() >= dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp():
        raise RuntimeError('Research build closed at soft deadline')
    source = Path(__file__).with_name('partition_hierarchy.cpp').resolve()
    repo = source.parents[4]
    tools = repo/'hierarchical_target_search/20260907_v1/tools/local'
    a.output.mkdir(parents=True, exist_ok=False)
    a.output = a.output.resolve()
    source_sha = sha(source)
    (a.output/'source_snapshot.cpp').write_bytes(source.read_bytes())
    binary = a.output/'partition_hierarchy'
    flags = ['-O1', '-g', '-fsanitize=address,undefined', '-fno-omit-frame-pointer'] if a.sanitize else ['-O3']
    command = [a.compiler, *flags, '-std=c++17', '-fopenmp', '-Wall', '-Wextra',
               '-DP3_SOURCE_SHA256='+json.dumps(source_sha), '-I', str(tools/'include'),
               '-I', str(repo/'build/_deps/json-src/single_include'), str(source), '-L', str(tools/'lib'),
               '-Wl,-rpath,'+str(tools/'lib'), '-lmetis', '-lGKlib', '-lm', '-o', str(binary)]
    record = {'status': 'INCOMPLETE', 'command': command, 'source_file': str(source),
              'source_sha256': source_sha, 'sanitizer': a.sanitize,
              'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'real_graph_or_GT_accessed': False}
    (a.output/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    start = time.perf_counter()
    with (a.output/'build.stdout').open('x') as stdout, (a.output/'build.stderr').open('x') as stderr:
        process = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=180)
    record.update(exit_code=process.returncode, wall_seconds=time.perf_counter()-start)
    if process.returncode == 0:
        record.update(status='COMPILED', binary_file=str(binary), binary_sha256=sha(binary))
    else:
        record['status'] = 'FAILED_BUILD'
    (a.output/'build.json').write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2))
    raise SystemExit(process.returncode)


if __name__ == '__main__':
    main()
