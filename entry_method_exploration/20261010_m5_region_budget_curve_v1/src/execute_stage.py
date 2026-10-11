#!/usr/bin/env python3
"""Administrative serial stage wrapper; scientific and renderer locks stay fixed."""
import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['evaluate', 'audit', 'plot', 'report'])
    stage = parser.parse_args().stage
    state = load(ROOT / 'run_state.json')
    assert state['status'] == 'NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION'
    assert state.get('active') is None and len(state['completed']) == 2
    assert all(x['exit_code'] == 0 for x in state['completed'])
    locks = [('execution_lock.json', 'source_and_binary_sha256'), ('auxiliary_lock.json', 'sha256'),
             ('delivery_source_lock.json', 'source_sha256'), ('delivery_source_precision_lock.json', 'source_sha256')]
    for filename, field in locks:
        for p, expected in load(ROOT / filename)[field].items():
            assert sha(p) == expected, f'frozen file changed: {p}'
    for p, expected in load(ROOT / 'execution_lock.json')['input_stats'].items():
        s = Path(p).stat()
        assert [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns] == expected, f'input changed: {p}'
    scripts = {'evaluate': ('evaluate.py', 'evaluation_execution.json'),
               'audit': ('independent_audit.py', 'independent_audit_execution.json'),
               'plot': ('plot_curves_v2.py', 'plot_curves_wrapper_execution.json'),
               'report': ('write_report_v2.py', 'report_wrapper_execution.json')}
    source, receipt_name = scripts[stage]
    receipt = ROOT / 'reviews' / receipt_name
    assert not receipt.exists(), 'preserve stage receipt'
    interpreter = ROOT.parents[1] / '.venv_cpu/bin/python' if stage in ('evaluate', 'plot') else Path('/usr/bin/python3')
    argv = [str(interpreter), str(ROOT / 'src' / source)]
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               NUMEXPR_NUM_THREADS='1', OMP_DYNAMIC='FALSE')
    before = time.monotonic()
    result = subprocess.run(argv, env=env, capture_output=True, text=True,
                            preexec_fn=lambda: os.sched_setaffinity(0, {14}))
    elapsed = time.monotonic() - before
    payload = {'status': 'PASS_E175_ACTUAL_STAGE_EXECUTION' if result.returncode == 0 else 'FAILED_STAGE_PARTIAL_PRESERVED',
               'stage': stage, 'argv': argv, 'exit_code': result.returncode, 'elapsed_seconds': elapsed,
               'elapsed_scope': 'whole subprocess lifetime, before receipt serialization',
               'source_sha256': sha(ROOT / 'src' / source), 'wrapper_sha256': sha(__file__),
               'stdout': result.stdout, 'stderr': result.stderr, 'CPU_affinity': [14],
               'training_increment_seconds': 0}
    receipt.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps(payload))
    assert result.returncode == 0, 'stage failed; preserve outputs and receipt'

if __name__ == '__main__':
    main()
