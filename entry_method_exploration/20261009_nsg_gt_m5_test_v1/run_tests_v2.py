from pathlib import Path
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta

OUT = Path(__file__).resolve().parent
receipt = json.loads((OUT / 'preparation_v2.json').read_text())
build = json.loads((OUT / 'src/build_v2.json').read_text())
binary = OUT / 'bin/benchmark_v2'
assert hashlib.sha256(binary.read_bytes()).hexdigest() == build['binary_sha256']
for job in receipt['jobs']:
    assert hashlib.sha256(Path(job['path']).read_bytes()).hexdigest() == job['sha256']
for filename, digest in build['source_sha256'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest
assert (OUT / 'data_preflight.json').is_file()
assert (OUT / 'source_review_v2.json').is_file()
review = json.loads((OUT / 'source_review_v2.json').read_text())
assert review['status'] == 'PASS', review
preflight = json.loads((OUT / 'data_preflight.json').read_text())
assert preflight['status'] == 'PASS_CURRENT_FULL_INPUT_SHA_AND_EXACT_TRAIN_TEST_BYTE_DISJOINTNESS' and not preflight['errors'], preflight['status']
for filename, record in preflight['current_complete_file_records'].items():
    actual = Path(filename).stat()
    observed = dict(device=actual.st_dev, inode=actual.st_ino, size=actual.st_size,
                    mtime_ns=actual.st_mtime_ns, mode=actual.st_mode)
    assert observed == record['stat5_after'], f'Input changed after hash: {filename}'
assert not (OUT / 'run_state_v2.json').exists(), 'Preserve prior invocation'
env = os.environ.copy()
for key in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    env[key] = '1'
env['OMP_DYNAMIC'] = 'FALSE'
env['MKL_DYNAMIC'] = 'FALSE'
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['MALLOC_ARENA_MAX'] = '1'
def stamp():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()
state = dict(status='RUNNING', started_at=stamp(), jobs=[], formal_total_batches=180,
             source_binary_sha256=build['binary_sha256'], no_training=True,
             driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
             protocol='protocol_v2.md', input_stats_still_match_preflight=True)
started = time.monotonic()
def save():
    state['elapsed_seconds'] = time.monotonic() - started
    state['updated_at'] = stamp()
    (OUT / 'run_state_v2.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
save()
for item in receipt['jobs']:
    job = json.loads(Path(item['path']).read_text())
    log_path = OUT / f'{job["dataset"]}.v2.native.log'
    entry = dict(dataset=job['dataset'], config=item['path'], log=str(log_path),
                 started_at=stamp(), status='RUNNING', thread_observations=0,
                 affinity='15', output=job['out'])
    state['jobs'].append(entry)
    with log_path.open('x') as log:
        process = subprocess.Popen(['taskset', '-c', '15', str(binary), item['path']],
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
        entry['pid'] = process.pid
        save()
        print(json.dumps(dict(event='START', dataset=job['dataset'], pid=process.pid, at=stamp())), flush=True)
        # Inspect affinity after taskset has exec'd the actual benchmark;
        # the forked child can briefly retain the parent's affinity first.
        exec_deadline = time.monotonic() + 5
        while process.poll() is None:
            try:
                if os.readlink(f'/proc/{process.pid}/exe') == str(binary):
                    break
            except FileNotFoundError:
                pass
            if time.monotonic() > exec_deadline:
                process.terminate()
                process.wait()
                entry['status'] = 'FAILED_EXEC_STARTUP'
                state['status'] = 'FAILED'
                save()
                raise RuntimeError('Benchmark exec startup did not complete')
            time.sleep(.05)
        while process.poll() is None:
            status_path = Path(f'/proc/{process.pid}/status')
            if status_path.exists():
                values = {}
                for line in status_path.read_text().splitlines():
                    key, _, value = line.partition(':')
                    if key in ('Threads', 'Cpus_allowed_list', 'VmRSS', 'State'):
                        values[key] = value.strip()
                if values.get('State', '').startswith('Z'):
                    break
                if values:
                    if values.get('Threads') != '1' or values.get('Cpus_allowed_list') != '15':
                        process.terminate()
                        process.wait()
                        entry['status'] = 'FAILED_THREAD_OR_CPU'
                        entry['last_process_status'] = values
                        state['status'] = 'FAILED'
                        save()
                        raise RuntimeError(values)
                    entry['thread_observations'] += 1
                    entry['last_process_status'] = values
            progress_path = Path(job['out']) / 'timing_progress.json'
            if progress_path.exists():
                try:
                    rounds = json.loads(progress_path.read_text())
                    entry['completed_timed_batches'] = len(rounds)
                    entry['last_timed_batch'] = rounds[-1] if rounds else None
                except json.JSONDecodeError:
                    pass
            save()
            time.sleep(5)
        exit_code = process.wait()
    entry['exit_code'] = exit_code
    entry['finished_at'] = stamp()
    entry['status'] = 'COMPLETED' if exit_code == 0 else 'FAILED'
    if exit_code:
        state['status'] = 'FAILED'
        save()
        print(log_path.read_text()[-4000:], flush=True)
        raise SystemExit(exit_code)
    completion = json.loads((Path(job['out']) / 'complete.json').read_text())
    assert completion['wall_rounds'] == 90
    entry['completed_timed_batches'] = completion['wall_rounds']
    entry['native_calls'] = completion['native_calls']
    entry['seconds_with_startup_and_audits'] = completion['seconds_with_startup_and_audits']
    save()
    print(json.dumps(dict(event='COMPLETE', dataset=job['dataset'], at=stamp(),
                         seconds=entry['seconds_with_startup_and_audits'])), flush=True)
state['status'] = 'NATIVE_COMPLETED_PENDING_EVALUATION'
state['finished_at'] = stamp()
save()
print(json.dumps(state, ensure_ascii=False), flush=True)
