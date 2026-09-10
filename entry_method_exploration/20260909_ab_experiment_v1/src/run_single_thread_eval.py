#!/usr/bin/env python3
"""All frozen queries and methods evaluated again under the user thread contract."""
import hashlib
import json
import os
import shutil
import signal
import time
from pathlib import Path

import run_models_eval as runner

OUT = Path(__file__).resolve().parents[1]
EVAL = OUT / 'single_thread_v1'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def main():
    state = json.loads((OUT / 'state.json').read_text())
    assert state['status'] == 'RESUME_STOPPED_REQUIRES_INSPECTION'
    assert state['model_fits'] == 12
    previous = Path(f"/proc/{state['controller_pid']}/stat")
    if previous.exists():
        assert previous.read_text().split(') ', 1)[1].split()[0] == 'Z', 'old controller has not exited'
    assert json.loads((OUT / 'reviews/single_thread_acceptance.json').read_text())['status'] == 'PASS'
    ready = json.loads((OUT / 'reviews/implementation_ready.json').read_text())
    for rel, expected in ready['execution_sha256'].items():
        assert sha(OUT / rel) == expected, rel
    frozen = json.loads((OUT / 'inputs/evaluation/validation/models_frozen_before_evaluation.json').read_text())
    for record in frozen['files']:
        assert sha(record['path']) == record['sha256'], record['path']
    assert not EVAL.exists()
    EVAL.mkdir()
    (EVAL / 'inputs').mkdir()
    (EVAL / 'results').mkdir()
    shutil.copy2(OUT / 'state.json', EVAL / 'state_before.json')
    sources = [OUT / 'src/run_single_thread_eval.py', OUT / 'src/benchmark_single_thread.cpp',
               OUT / 'src/analyze_single_thread.py', OUT / 'bin/benchmark_single_thread',
               OUT / 'evaluation_single_thread_amendment.md']
    manifest = {'status': 'SINGLE_THREAD_EVALUATION_RUNNING', 'threads': 1,
                'controller_pid': os.getpid(), 'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'execution_sha256': {str(p.relative_to(OUT)): sha(p) for p in sources},
                'model_files_verified': len(frozen['files']), 'models_retrained': False,
                'old_16_thread_results_used': False, 'completed': []}
    dump(EVAL / 'manifest.json', manifest)
    runner.state = state
    runner.state.update(status='SINGLE_THREAD_EVALUATION_RUNNING', controller_pid=os.getpid(),
                        active_stage='single_thread_prepared', active_process=None,
                        evaluation_threads=1, offline_training_threads=16,
                        superseded_timing='Original 16-thread results preserved and excluded from final comparison',
                        next='Finish every frozen method and query split at one thread, then verify/analyze and close out')
    runner.state.pop('error', None)
    runner.save()
    for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS']:
        os.environ[name] = '1'
    os.environ['OMP_DYNAMIC'] = 'FALSE'
    os.environ['MPLCONFIGDIR'] = str(OUT / 'logs/matplotlib_cache')
    try:
        for split in ['calibration_check', 'audit', 'validation', 'heldout']:
            prep_path = OUT / 'inputs/evaluation' / split / 'complete.json'
            if not prep_path.exists():
                assert not prep_path.parent.exists(), 'partial preparation requires review'
                runner.command(f'st1_prepare_{split}', [runner.PY, OUT / 'src/prepare_eval.py', '--split', split], threads=1)
            prep = json.loads(prep_path.read_text())
            assert prep['status'] == 'PREPARED'
            for config_path in prep['configs']:
                original = Path(config_path)
                config = json.loads(original.read_text())
                assert config['threads'] == 16
                config['threads'] = 1
                config['thread_amendment'] = str(OUT / 'evaluation_single_thread_amendment.md')
                destination = EVAL / 'inputs' / split / original.parent.name / original.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                dump(destination, config)
                assert json.loads(destination.read_text())['threads'] == 1
                result_root = EVAL / 'results' / split / original.parent.name / original.stem
                stage = f'st1_eval_{split}_{original.parent.name}_{original.stem}'
                start = time.monotonic()
                runner.command(stage, [OUT / 'bin/benchmark_single_thread', destination, result_root], threads=1)
                result = json.loads((result_root / 'results.json').read_text())
                contract = json.loads((result_root / 'thread_contract.json').read_text())
                assert result['status'] == 'COMPLETE' and result['threads'] == 1
                assert contract['status'] == 'PASS' and contract['observed_openmp_threads'] == 1
                assert len(result['methods']) == 28
                manifest['completed'].append({'result': str(result_root), 'seconds': time.monotonic() - start, 'threads': 1})
                dump(EVAL / 'manifest.json', manifest)
        runner.state.update(status='SINGLE_THREAD_EVALUATION_COMPLETE_ANALYSIS_PENDING', active_stage=None, active_process=None)
        runner.save()
        runner.command('st1_analyze', [runner.PY, OUT / 'src/analyze_single_thread.py'], threads=1)
        review = json.loads((EVAL / 'results/analysis_v1/verification.json').read_text())
        assert review['status'] == 'PASS' and review['evaluation_threads'] == 1
        manifest.update(status='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING')
        dump(EVAL / 'manifest.json', manifest)
        runner.state.update(status='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING', active_stage=None, active_process=None,
                            next='Review single-thread measured metrics, figures and all artifacts; synchronize history/spec/summary/next-stage handoff')
        runner.save()
    except BaseException as error:
        if runner.child and runner.child.poll() is None:
            os.killpg(runner.child.pid, signal.SIGTERM)
            runner.child.wait()
        runner.state.update(status='SINGLE_THREAD_STOPPED_REQUIRES_INSPECTION', error=repr(error), active_process=None)
        runner.save()
        manifest.update(status='STOPPED_REQUIRES_INSPECTION', error=repr(error))
        dump(EVAL / 'manifest.json', manifest)
        raise


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, runner.stop)
    signal.signal(signal.SIGINT, runner.stop)
    main()
