"""Hourly, lightweight E97 observation and same-session Codex completion review."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OPS = RUN / 'ops'
TIMER = 'acsg-e97-hourly-check.timer'


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def record(value):
    write_json(OPS / 'hourly_status.json', value)
    with (OPS / 'hourly_checks.jsonl').open('a') as out:
        out.write(json.dumps(value, ensure_ascii=False) + '\n')
    print(json.dumps(value, ensure_ascii=False), flush=True)


def process_args(pid):
    try:
        return Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except OSError:
        return []


def live_workers():
    workers = []
    source_prefix = str(RUN / 'src').encode() + b'/'
    binary_prefix = str(RUN / 'bin').encode() + b'/'
    for proc in Path('/proc').iterdir():
        if proc.name.isdigit():
            args = process_args(proc.name)
            if any(arg.startswith(source_prefix) or arg.startswith(binary_prefix) for arg in args):
                workers.append(int(proc.name))
    return workers


def observe():
    state = read_json(RUN / 'state.json')
    snapshot = dict(checked_beijing=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
                    checked_unix=time.time(), experiment_status=state.get('status'),
                    stage=state.get('stage'), state_pid=state.get('pid'),
                    target_points=800, target_wall_rounds=2400)
    points = rounds = 0
    by_dataset = {}
    invalid = []
    # Exactly one method/budget below dataset/K; skip aggregate K complete.json.
    for path in (RUN / 'results').glob('*/*/*/complete.json'):
        item = read_json(path)
        if (item.get('status') != 'PASS' or item.get('threads') != 1
                or item.get('cpu') != 15 or item.get('K') not in (1, 100)
                or len(item.get('seconds', [])) != 3
                or not item.get('plain_count_bit_parity')
                or not item.get('warmup_bit_parity')):
            invalid.append(str(path.relative_to(RUN)))
            continue
        points += 1
        rounds += len(item['seconds'])
        ds = path.relative_to(RUN / 'results').parts[0]
        by_dataset[ds] = by_dataset.get(ds, 0) + 1
    snapshot.update(completed_points=points, completed_wall_rounds=rounds,
                    points_by_dataset=by_dataset, invalid_completions=invalid,
                    live_pipeline_pids=live_workers())
    pid = state.get('pid')
    if pid and process_args(pid):
        stat = Path(f'/proc/{pid}/status')
        if stat.exists():
            snapshot['process'] = {k: v.strip() for line in stat.read_text().splitlines()
                                   if ':' in line for k, v in [line.split(':', 1)]
                                   if k in ('Threads', 'Cpus_allowed_list', 'VmRSS')}
    return snapshot


def thread_idle(rollout):
    """Avoid concurrent writers to the current IDE conversation."""
    lifecycle = None
    try:
        with Path(rollout).open() as src:
            for line in src:
                if not any(token in line for token in ('task_started', 'task_complete', 'task_interrupted', 'turn_aborted')):
                    continue
                item = json.loads(line)
                if item.get('type') == 'event_msg':
                    kind = item.get('payload', {}).get('type')
                    if kind in ('task_started', 'task_complete', 'task_interrupted', 'turn_aborted'):
                        lifecycle = kind
    except (OSError, ValueError):
        return False
    return lifecycle in ('task_complete', 'task_interrupted', 'turn_aborted')


def finished():
    return (read_json(RUN / 'state.json').get('status') == 'COMPLETE'
            and read_json(RUN / 'complete.json').get('status') == 'COMPLETE'
            and read_json(RUN / 'reviews/raw_results_verified.json').get('status') == 'PASS'
            and read_json(RUN / 'reviews/figures_visual_check.json').get('status') == 'PASS'
            and read_json(OPS / 'analysis_done.json').get('status') == 'PASS')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--observe-only', action='store_true')
    args = parser.parse_args()
    os.sched_setaffinity(0, {0})
    lock = (OPS / 'hourly.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('Another hourly check/review is still running.', flush=True)
        return
    config = read_json(OPS / 'hourly_config.json')
    not_before = config.get('inspect_not_before_unix', 0)
    if not args.observe_only and time.time() < not_before:
        print('Inspection deferred until ' + datetime.fromtimestamp(
            not_before, ZoneInfo('Asia/Shanghai')).isoformat()
            + '; no experiment files or workers inspected.', flush=True)
        return
    snapshot = observe()
    if args.observe_only:
        snapshot['action'] = 'OBSERVE_ONLY'
        record(snapshot)
        return
    if finished():
        snapshot['action'] = 'COMPLETE_TIMER_STOPPED'
        record(snapshot)
        subprocess.run(['systemctl', 'disable', '--now', TIMER], check=True)
        return
    status = snapshot['experiment_status']
    terminal = status in ('PLOTS_READY_PENDING_VISUAL_CHECK', 'COMPLETE', 'FAILED', 'NEEDS_REVIEW')
    if snapshot['live_pipeline_pids']:
        snapshot['action'] = 'WAIT_PIPELINE'
        record(snapshot)
        return
    # Missing workers for a running state also deserve inspection, not a blind restart.
    if not terminal and status and status.startswith('RUNNING'):
        terminal = True
    if not terminal:
        snapshot['action'] = 'WAIT_PIPELINE_STATE'
        record(snapshot)
        return
    if not thread_idle(config['rollout_path']):
        snapshot['action'] = 'DEFER_ACTIVE_CONVERSATION'
        record(snapshot)
        return
    run_id = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d_%H%M%S')
    output = RUN / 'logs' / f'hourly_codex_{run_id}.jsonl'
    message = OPS / f'hourly_result_{run_id}.md'
    command = [config['codex_binary'], '-C', str(ROOT), '-a', 'never',
               '-s', 'danger-full-access', 'exec', 'resume', '--json',
               '--output-last-message', str(message), config['thread_id'], '-']
    snapshot.update(action='RESUMING_SAME_CONVERSATION', codex_log=str(output),
                    result_message=str(message), thread_id=config['thread_id'])
    record(snapshot)
    env = os.environ.copy()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        env[name] = '1'
    prompt = (OPS / 'hourly_review_prompt.md').read_text()
    with output.open('w') as log:
        result = subprocess.run(command, input=prompt, text=True, stdout=log,
                                stderr=subprocess.STDOUT, cwd=ROOT, env=env)
    snapshot.update(action='CODEX_REVIEW_RETURNED', codex_exit_code=result.returncode,
                    returned_unix=time.time(), complete=finished())
    record(snapshot)
    if finished():
        subprocess.run(['systemctl', 'disable', '--now', TIMER], check=True)


if __name__ == '__main__':
    main()
