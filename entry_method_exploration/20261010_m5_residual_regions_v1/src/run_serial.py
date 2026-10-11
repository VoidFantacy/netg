#!/usr/bin/env python3
"""Frozen four-job run, no fitting and no response-driven branch."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           NUMEXPR_NUM_THREADS='1', OMP_DYNAMIC='FALSE')

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load(p):
    return json.loads(Path(p).read_text())

def write(p, x):
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(x, indent=2) + '\n')
    tmp.replace(p)

def start():
    lock = load(ROOT / 'execution_lock.json')
    for p, expected in lock['source_and_binary_sha256'].items():
        assert sha(p) == expected, f'execution source changed: {p}'
    assert load(ROOT / 'reviews/data_preflight.json')['status'].startswith('PASS'), 'data identity pending'
    assert load(ROOT / 'reviews/preexecution_acceptance.json')['status'].startswith('PASS'), 'acceptance pending'
    params = load(ROOT / 'parameter_lock.json')
    assert sha(ROOT / 'protocol.md') == params['protocol_sha256']
    state = {'status': 'RUNNING_FIXED_FOUR_JOBS_NO_NEW_TRAIN', 'started_unix': time.time(),
             'completed': [], 'planned_points': 112, 'planned_timed_batches': 336, 'training_increment_seconds': 0}
    write(ROOT / 'run_state.json', state)
    datasets = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
    for role in ['confirm_a', 'confirm_b']:
        for dataset in datasets:
            job = ROOT / 'jobs' / f'{role}.{dataset}.json'
            assert sha(job) == params['jobs'][str(job)], 'job changed'
            config = load(job)
            assert not Path(config['out']).exists(), 'preserve existing output'
            # Check all frozen data stats, including the hashed large inputs,
            # before/after each child. No heavy file hashing during performance.
            for p, before in lock['input_stats'].items():
                s = Path(p).stat()
                assert [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns] == before, f'input changed: {p}'
            logs = ROOT / 'logs'
            logs.mkdir(exist_ok=True)
            argv = [str(ROOT / 'bin/benchmark'), str(job)]
            started = time.monotonic()
            log = logs / f'{role}.{dataset}.log'
            assert not log.exists(), 'preserve log'
            with log.open('w') as f:
                proc = subprocess.Popen(argv, env=ENV, stdout=f, stderr=subprocess.STDOUT,
                                        preexec_fn=lambda: os.sched_setaffinity(0, {15}))
                max_threads = 0
                try:
                    state['active'] = {'role': role, 'dataset': dataset, 'pid': proc.pid, 'argv': argv}
                    write(ROOT / 'run_state.json', state)
                    while proc.poll() is None:
                        if time.monotonic() - started > 7200:
                            raise RuntimeError('frozen 7200s QUERY JOB cap exceeded; partial preserved')
                        try:
                            lines = Path(f'/proc/{proc.pid}/status').read_text().splitlines()
                            threads = int(next(s.split(':')[1] for s in lines if s.startswith('Threads:')))
                            max_threads = max(max_threads, threads)
                            assert threads == 1, 'actual native thread count changed'
                            assert os.sched_getaffinity(proc.pid) == {15}, 'actual CPU affinity changed'
                        except (FileNotFoundError, ProcessLookupError):
                            pass
                        time.sleep(.25)
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()
                        state['owned_child_cleanup'] = {'pid': proc.pid, 'returncode': proc.returncode,
                                                        'terminated_then_waited': True, 'partial_preserved': True}
                        state['active'] = None
                        try:
                            write(ROOT / 'run_state.json', state)
                        except BaseException as persistence_error:
                            # Child has already been waited for. Keep the
                            # original exception and a separate log receipt.
                            f.write('\nOWNED_CHILD_CLEANUP ' + json.dumps(state['owned_child_cleanup']) +
                                    ' persistence_error=' + repr(persistence_error) + '\n')
                            f.flush()
                code = proc.returncode
            receipt = {'role': role, 'dataset': dataset, 'argv': argv, 'exit_code': code,
                       'elapsed_seconds': time.monotonic() - started, 'max_threads_observed': max_threads,
                       'log': str(log), 'job_sha256': sha(job)}
            state['completed'].append(receipt)
            state['active'] = None
            write(ROOT / 'run_state.json', state)
            assert code == 0, f'native failure; preserve partial: {log}'
            assert load(Path(config['out']) / 'complete.json')['status'].startswith('PASS')
            for p, before in lock['input_stats'].items():
                s = Path(p).stat()
                assert [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns] == before, f'input changed after job: {p}'
    state['status'] = 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION'
    state['finished_unix'] = time.time()
    write(ROOT / 'run_state.json', state)
    print(json.dumps({'status': state['status'], 'jobs': len(state['completed'])}))

if __name__ == '__main__':
    try:
        start()
    except BaseException as e:
        p = ROOT / 'run_state.json'
        state = load(p) if p.exists() else {}
        state['status'] = 'FAILED_PARTIAL_PRESERVED'
        state['error'] = repr(e)
        write(p, state)
        raise
