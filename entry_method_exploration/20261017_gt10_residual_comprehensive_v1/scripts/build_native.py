#!/usr/bin/env python3
"""Build E183 native tools only; no TRAIN, GT, or measured ANN is executed."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def build(name):
    started = time.monotonic()
    target = ROOT / 'bin' / name
    receipt = ROOT / 'bin' / ('build_' + name + '.json')
    log = ROOT / 'bin' / ('build_' + name + '.log')
    if any(p.exists() for p in (target, receipt, log)):
        raise RuntimeError('Preserve previous build artifacts: ' + name)
    libs = [Path('/root/acsg-e172-storage-v2/campaign/common/acsg_current.o'),
            REPO / 'build/ACSG/libACSG.a', REPO / 'build/MRNN_Descent/libmrnndescent.a',
            REPO / 'build/faiss/faiss/libfaiss.a']
    old = REPO / 'entry_method_exploration/20261015_m5_k100_capacity_v1/src'
    source = ROOT / 'src' / (name + '.cpp')
    sources = [source, ROOT / 'src/residual_tools.cpp', Path(__file__).resolve(),
               *sorted(old.glob('*.hpp')), *sorted((REPO / 'benches/hnswlib').glob('*.h')),
               REPO / 'ACSG/ACSG.h', REPO / 'ACSG/IndexACSG.h', *libs]
    identities = {str(p): sha(p) for p in sources}
    argv = ['g++', '-O3', '-march=native', '-std=c++17', '-fopenmp', '-rdynamic',
            f'-I{REPO}', f'-I{REPO}/benches', f'-I{REPO}/faiss',
            f'-I{REPO}/build/_deps/json-src/single_include', str(source),
            *map(str, libs), '-lopenblas', '-lz', '-ldl', '-lcrypto', '-o', str(target)]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1',
               MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
    compile_start = time.monotonic()
    failure = None
    with log.open('x') as stream:
        child = subprocess.Popen(argv, cwd=REPO, env=env, stdout=stream,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = child.wait(timeout=600)
        except BaseException as error:
            failure = repr(error)
            os.killpg(child.pid, signal.SIGTERM)
            try:
                code = child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait()
    compile_wall = time.monotonic() - compile_start
    changed = [path for path, expected in identities.items() if sha(path) != expected]
    record = dict(status='PASS_E183_NATIVE_BUILD' if code == 0 and not changed and failure is None else 'FAIL_E183_NATIVE_BUILD',
                  target=name, argv=argv, exit_code=code, failure=failure,
                  input_sha256=identities, changed_inputs=changed,
                  binary=str(target), binary_sha256=sha(target) if target.exists() else None,
                  compile_subprocess_seconds=compile_wall, elapsed_seconds=time.monotonic() - started,
                  cost_scope='elapsed includes input/output hashing and compile subprocess; do not add nested compile again',
                  scientific_binary_executed=False, log=str(log))
    with receipt.open('x') as stream:
        json.dump(record, stream, indent=2)
        stream.write('\n')
    print(json.dumps({k: record[k] for k in ('status', 'target', 'exit_code', 'elapsed_seconds', 'log')}), flush=True)
    if record['status'] != 'PASS_E183_NATIVE_BUILD':
        raise RuntimeError('Build failed; preserve artifacts: ' + str(log))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=('all', 'residual_tools', 'benchmark'), default='all')
    args = parser.parse_args()
    os.sched_setaffinity(0, {14})
    (ROOT / 'bin').mkdir(exist_ok=True)
    for name in ('residual_tools', 'benchmark') if args.target == 'all' else (args.target,):
        build(name)

if __name__ == '__main__':
    main()
