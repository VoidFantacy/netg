"""Keep the authorized E97 pipeline running independently of the chat session.

Existing workers are observed without interruption. Resume only when all of
them have gone away; preserve real FAILED states for later human inspection.
The frozen experiment sources, models, budgets and evaluation stay unchanged.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
PY = ROOT / '.venv_cpu/bin/python'
ALLOWED_CPUS = os.sched_getaffinity(0)
os.sched_setaffinity(0, {min(ALLOWED_CPUS)})
NAMES = {
    'run_after_preparation.py', 'pipeline.py', 'freeze_models.py',
    'prepare_data.py', 'preflight.py', 'analyze.py', 'train_gate.py',
    'prepare.py', 'build_profiles.py', 'reuse_ip.py',
    'labels', 'evaluate', 'build_nsg', 'build_hnsw',
}
TARGETS = {RUN / folder / name for folder in ('src', 'bin') for name in NAMES}


def write_status(status, **fields):
    out = dict(status=status, unix=time.time(), supervisor_pid=os.getpid(), **fields)
    p = RUN / 'ops/background_status.json'
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(out, indent=2) + '\n')
    tmp.replace(p)


def workers():
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            argv = (proc / 'cmdline').read_bytes().split(b'\0')
            cwd = (proc / 'cwd').resolve()
            for arg in argv[:4]:
                if not arg:
                    continue
                p = Path(os.fsdecode(arg))
                if not p.is_absolute():
                    p = cwd / p
                if p.resolve() in TARGETS:
                    found.append(int(proc.name))
                    break
        except (OSError, RuntimeError):
            continue
    return found


def restore_worker_affinity():
    os.sched_setaffinity(0, ALLOWED_CPUS)


def main():
    with (RUN / 'ops/background.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        resumes = []
        while True:
            state = json.loads((RUN / 'state.json').read_text())
            status = state['status']
            if status in ('COMPLETE', 'PLOTS_READY_PENDING_VISUAL_CHECK'):
                write_status(status, resumes=resumes, note='Measurements and automatic plots completed; manual review can happen later.')
                print(status, flush=True)
                return
            if status == 'FAILED':
                write_status('NEEDS_REVIEW', experiment_state=state, resumes=resumes)
                raise RuntimeError('The experiment reported FAILED; preserve its evidence and do not retry blindly.')
            live = workers()
            if live:
                write_status('MONITORING_ACTIVE_PIPELINE', active_worker_pids=live, experiment_stage=state.get('stage'), resumes=resumes)
                time.sleep(20)
                continue
            if not (RUN / 'preparation.complete.json').exists():
                write_status('NEEDS_REVIEW', experiment_state=state, resumes=resumes)
                raise RuntimeError('Preparation not complete; unexpected state for this post-preparation service.')
            attempt = len(resumes) + 1
            logfile = RUN / 'logs' / f'background_resume_{time.time_ns()}.log'
            rec = dict(attempt=attempt, resumed_unix=time.time(), previous_state=state, log=str(logfile))
            resumes.append(rec)
            (RUN / 'ops/resumes.json').write_text(json.dumps(resumes, indent=2) + '\n')
            env = os.environ.copy()
            env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', PYTHONUNBUFFERED='1')
            with logfile.open('w') as out, open(os.devnull, 'rb') as inp:
                p = subprocess.Popen([str(PY), str(RUN / 'src/run_after_preparation.py')],
                                     cwd=ROOT, stdin=inp, stdout=out, stderr=subprocess.STDOUT,
                                     env=env, preexec_fn=restore_worker_affinity)
                write_status('RESUMED_PIPELINE', driver_pid=p.pid, resumes=resumes)
                code = p.wait()
            rec['exit_code'] = code
            (RUN / 'ops/resumes.json').write_text(json.dumps(resumes, indent=2) + '\n')
            if code:
                write_status('NEEDS_REVIEW', resumes=resumes)
                raise RuntimeError(f'Resumed pipeline exited {code}; inspect {logfile}')


if __name__ == '__main__':
    main()
