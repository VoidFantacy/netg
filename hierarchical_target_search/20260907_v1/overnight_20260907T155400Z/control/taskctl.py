#!/usr/bin/env python3
"""Session-scoped CPU job control; every child group has a verifiable token."""
import argparse
import datetime as dt
import fcntl
import json
import os
import resource
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def stamp(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()

def write(path, obj):
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(obj, indent=2) + '\n')
    tmp.replace(path)

def proc(pid):
    try:
        p = Path('/proc') / str(pid)
        stat = (p/'stat').read_text().rsplit(')', 1)[1].split()
        env = (p/'environ').read_bytes().split(b'\0')
        return {'pid': int(pid), 'pgid': int(stat[2]), 'start_ticks': int(stat[19]),
                'state': stat[0], 'token': next((x.split(b'=', 1)[1].decode() for x in env
                       if x.startswith(b'ACSG_OVERNIGHT_JOB_TOKEN=')), None),
                'rss_kib': int(stat[21]) * os.sysconf('SC_PAGE_SIZE') // 1024}
    except (OSError, ValueError, IndexError):
        return None

def members(job):
    found = []
    for p in Path('/proc').iterdir():
        if p.name.isdecimal():
            x = proc(p.name)
            if x and x['pgid'] == job.get('pgid') and x['state'] != 'Z':
                found.append(x)
    return found

def terminate(job, sig):
    live = members(job)
    if not live:
        return {'at': now(), 'signal': sig, 'result': 'ALREADY_STOPPED'}
    if any(x['token'] != job['token'] for x in live):
        return {'at': now(), 'signal': sig, 'result': 'REFUSED_IDENTITY_MISMATCH', 'members': live}
    leader = next((x for x in live if x['pid'] == job['pid']), None)
    if leader and leader['start_ticks'] != job['start_ticks']:
        return {'at': now(), 'signal': sig, 'result': 'REFUSED_START_MISMATCH'}
    try:
        os.killpg(job['pgid'], sig)
        return {'at': now(), 'signal': sig, 'result': 'SENT', 'members': live}
    except ProcessLookupError:
        return {'at': now(), 'signal': sig, 'result': 'ALREADY_STOPPED'}

def config(control):
    return json.loads((control/'config.json').read_text())

def artifact_bytes(cfg):
    total = 0
    for parent, dirs, files in os.walk(cfg['run_dir'], followlinks=False):
        for name in files:
            try:
                total += (Path(parent)/name).lstat().st_size
            except FileNotFoundError:
                pass
    return total

def allowed(control, cfg, expected):
    t = time.time()
    if (control/'CLOSED.json').exists() or t >= stamp(cfg['soft_stop_utc']):
        raise RuntimeError('Research launch closed by deadline protection')
    if t >= stamp(cfg['no_long_job_utc']) and t + expected >= stamp(cfg['soft_stop_utc']):
        raise RuntimeError('Estimated job crosses cutoff; launch refused')
    if shutil.disk_usage(cfg['project_root']).free < cfg['min_free_disk_bytes']:
        raise RuntimeError('Less than required disk reserve')
    if artifact_bytes(cfg) >= cfg['artifact_limit_bytes']:
        raise RuntimeError('New artifact budget exhausted')

def supervise(control, spec_path):
    cfg = config(control)
    job = json.loads(spec_path.read_text())
    lock = None
    child = None
    try:
        allowed(control, cfg, job['expected_seconds'])
        if job['heavy']:
            lock = (control/'heavy.lock').open('a')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            avail = next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
            if avail < job['min_ram_gib'] * 1024**3:
                raise RuntimeError('Insufficient RAM for declared job requirement')
        env = dict(os.environ, CUDA_VISIBLE_DEVICES='', ACSG_OVERNIGHT_JOB_TOKEN=job['token'])
        env.setdefault('OMP_NUM_THREADS', '16')
        env.setdefault('OPENBLAS_NUM_THREADS', '1')
        env.setdefault('MKL_NUM_THREADS', '1')
        with open(job['log'], 'xb', buffering=0) as log:
            child = subprocess.Popen(job['command'], cwd=cfg['project_root'], env=env,
                                     stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            info = proc(child.pid)
            if info is None:
                raise RuntimeError('Child identity unavailable immediately after launch')
            job.update(status='RUNNING', started_utc=now(), supervisor_pid=os.getpid(),
                       pid=child.pid, pgid=info['pgid'], start_ticks=info['start_ticks'], peak_rss_kib=0)
            write(spec_path, job)
            started = time.monotonic()
            term_at = None
            while child.poll() is None:
                live = members(job)
                job['peak_rss_kib'] = max(job['peak_rss_kib'], sum(x['rss_kib'] for x in live))
                job['last_observed_utc'] = now()
                reason = None
                if time.time() >= stamp(cfg['soft_stop_utc']) or (control/'CLOSED.json').exists():
                    reason = 'DEADLINE'
                elif time.monotonic() - started >= job['timeout_seconds']:
                    reason = 'JOB_TIMEOUT'
                elif shutil.disk_usage(cfg['project_root']).free < cfg['min_free_disk_bytes']:
                    reason = 'DISK_RESERVE'
                if reason and term_at is None:
                    job['stop_reason'] = reason
                    job.setdefault('signals', []).append(terminate(job, signal.SIGTERM))
                    term_at = time.monotonic()
                if term_at is not None and time.monotonic() - term_at >= 10:
                    job.setdefault('signals', []).append(terminate(job, signal.SIGKILL))
                write(spec_path, job)
                time.sleep(2)
            job.update(returncode=child.wait(), ended_utc=now(), elapsed_seconds=time.monotonic()-started)
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            job.update(child_user_cpu_seconds=usage.ru_utime, child_system_cpu_seconds=usage.ru_stime, rusage_maxrss_kib=usage.ru_maxrss, disk_free_bytes_at_end=shutil.disk_usage(cfg['project_root']).free)
            job['status'] = 'COMPLETE' if job['returncode'] == 0 and not job.get('stop_reason') else 'INCOMPLETE' if job.get('stop_reason') else 'FAILED'
    except Exception as e:
        job.update(status='LAUNCH_FAILED', error=str(e), ended_utc=now())
        if child is not None and child.poll() is None:
            info = proc(child.pid)
            if info and info['token'] == job['token']:
                os.killpg(info['pgid'], signal.SIGTERM)
    finally:
        write(spec_path, job)
        if lock:
            lock.close()

def watchdog(control):
    cfg = config(control)
    events = []
    last_resource_check = 0.0
    resource_state = {}
    lock = (control/'watchdog.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    write(control/'watchdog_identity.json', {'pid': os.getpid(), 'proc': proc(os.getpid()), 'started_utc': now(), 'config': cfg})
    while True:
        t = time.time()
        if t-last_resource_check >= 15:
            resource_state = {'artifact_bytes':artifact_bytes(cfg),'disk_free_bytes':shutil.disk_usage(cfg['project_root']).free,'checked_utc':now()}
            last_resource_check = t
        budget_stop = resource_state['artifact_bytes'] >= cfg['artifact_limit_bytes'] or resource_state['disk_free_bytes'] < cfg['min_free_disk_bytes']
        closing = t >= stamp(cfg['soft_stop_utc']) or budget_stop or (control/'CLOSED.json').exists()
        if closing and not (control/'CLOSED.json').exists():
            write(control/'CLOSED.json', {'at': now(), 'reason': 'RESOURCE_LIMIT' if budget_stop else 'SOFT_DEADLINE', 'research_complete': False})
        active = []
        for path in sorted((control/'jobs').glob('*.json')):
            job = json.loads(path.read_text())
            if job.get('pgid'):
                live = members(job)
                if live:
                    active.append({'name': job['name'], 'members': live})
                    if closing:
                        sig = signal.SIGKILL if t >= stamp(cfg['soft_stop_utc'])+15 else signal.SIGTERM
                        events.append({'name': job['name'], **terminate(job, sig)})
        write(control/'watchdog_status.json', {'at': now(), 'status': 'CLOSING' if closing else 'ARMED', 'active': active, 'signals': events, 'resources':resource_state})
        if t >= stamp(cfg['deadline_utc']):
            write(control/'stop_verification.json', {'at': now(), 'deadline_utc': cfg['deadline_utc'],
                'all_registered_research_processes_stopped': not active,
                'active': active, 'signals': events, 'research_goal_complete': False})
            return
        time.sleep(min(5, max(.05, stamp(cfg['deadline_utc'])-time.time())))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control', type=Path, default=HERE)
    sub = parser.add_subparsers(dest='action', required=True)
    launch = sub.add_parser('launch')
    launch.add_argument('--name', required=True)
    launch.add_argument('--heavy', action='store_true')
    launch.add_argument('--expected-seconds', type=float, default=120)
    launch.add_argument('--timeout-seconds', type=float, default=3600)
    launch.add_argument('--min-ram-gib', type=float, default=4)
    launch.add_argument('command', nargs=argparse.REMAINDER)
    run = sub.add_parser('supervise'); run.add_argument('spec', type=Path)
    sub.add_parser('watchdog')
    sub.add_parser('status')
    args = parser.parse_args()
    control = args.control.resolve()
    (control/'jobs').mkdir(exist_ok=True)
    cfg = config(control)
    if args.action == 'launch':
        allowed(control, cfg, args.expected_seconds)
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command or '/' in args.name or args.name in ('.', '..'):
            raise RuntimeError('Invalid name/command')
        job = {'name': args.name, 'status': 'QUEUED', 'created_utc': now(), 'token': str(uuid.uuid4()),
               'command': command, 'heavy': args.heavy, 'expected_seconds': args.expected_seconds,
               'timeout_seconds': args.timeout_seconds, 'min_ram_gib': args.min_ram_gib,
               'log': str(Path(cfg['run_dir'])/'logs'/(args.name+'.log'))}
        path = control/'jobs'/(args.name+'.json')
        with path.open('x') as f:
            json.dump(job, f, indent=2)
        with (control/(args.name+'.supervisor.log')).open('xb') as log:
            p = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--control', str(control), 'supervise', str(path)],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        print(json.dumps({'supervisor_pid': p.pid, 'job_file': str(path), 'log': job['log']}))
    elif args.action == 'supervise':
        supervise(control, args.spec)
    elif args.action == 'watchdog':
        watchdog(control)
    else:
        for p in sorted((control/'jobs').glob('*.json')):
            j = json.loads(p.read_text())
            print(json.dumps({k:j.get(k) for k in ('name','status','pid','pgid','started_utc','elapsed_seconds','peak_rss_kib','returncode','stop_reason')}))

if __name__ == '__main__':
    main()
