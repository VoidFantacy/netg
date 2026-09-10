#!/usr/bin/env python3
"""Resume only missing evaluations after verified process loss; preserve evidence."""
import hashlib
import json
import os
import shutil
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import run_models_eval as runner

OUT = Path(__file__).resolve().parents[1]
ATTEMPT = 'reboot_20260909T1210Z'
ARCHIVE = OUT / 'recovery' / ATTEMPT


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def verify_completed(root, split):
    path = root / 'results.json'
    if not path.exists():
        return False
    result = json.loads(path.read_text())
    if result['status'] != 'COMPLETE':
        return False
    n = 1024 if split in ['calibration_check', 'audit'] else 10000
    assert result['queries'] == n and len(result['methods']) == 28
    assert (root / 'row_ids.i64').stat().st_size == n * 8
    for method in result['methods']:
        assert method['plain_count_parity_queries'] == n
        assert len(method['timings']) == (0 if n == 1024 else 3)
        folder = root / method['name']
        assert (folder / 'hits.u8').stat().st_size == n
        assert (folder / 'graph_ndc.u32').stat().st_size == n * 4
        assert (folder / 'entry_ids.i32').stat().st_size == n * 3 * 4
    return True


def main():
    state = json.loads((OUT / 'state.json').read_text())
    assert state['status'] == 'MODELS_FROZEN_EVALUATION_RUNNING'
    assert state['model_fits'] == 12
    for pid in [state['controller_pid'], state['active_process'], 70087]:
        assert not Path(f'/proc/{pid}').exists(), f'previous process {pid} still exists'
    ready = json.loads((OUT / 'reviews/implementation_ready.json').read_text())
    for rel, expected in ready['execution_sha256'].items():
        assert sha(OUT / rel) == expected, rel
    prior_sources = json.loads((OUT / 'reviews/model_eval_execution_hashes.json').read_text())
    for rel, expected in prior_sources.items():
        assert sha(OUT / rel) == expected, rel
    frozen = json.loads((OUT / 'inputs/evaluation/validation/models_frozen_before_evaluation.json').read_text())
    for record in frozen['files']:
        assert sha(record['path']) == record['sha256'], record['path']
    assert json.loads((OUT / 'reviews/full_labels_verified.json').read_text())['status'] == 'PASS'
    assert not ARCHIVE.exists()
    ARCHIVE.mkdir(parents=True)
    for name in ['state.json', 'pipeline_supervisor.json']:
        shutil.copy2(OUT / name, ARCHIVE / name)
    manifest = {
        'status': 'RESUME_VERIFIED', 'attempt': ATTEMPT,
        'started_utc': datetime.now(timezone.utc).isoformat(),
        'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'controller_pid': os.getpid(), 'source_sha256': sha(__file__),
        'frozen_sources_and_models_verified': True,
        'frozen_model_files_checked': len(frozen['files']),
        'policy': 'Reuse complete labels and frozen models; preserve complete invocations; archive and rerun interrupted whole invocation with three fresh rotated timing rounds. No model reselection.',
        'completed_reused': [], 'incomplete_archived': [], 'newly_completed': [],
        'timing_scope_note': 'Validation WebVid builds 20260828/29 completed before reboot; all other formal invocations complete after reboot. Each build comparison uses methods timed together in the same invocation. Heldout all after reboot.',
    }
    dump(ARCHIVE / 'manifest.json', manifest)
    runner.state = state
    runner.state.update(controller_pid=os.getpid(), active_process=None,
                        recovery_attempt=ATTEMPT, active_stage='verified_resume',
                        next='Complete remaining frozen evaluations, then analysis and final review')
    runner.save()
    try:
        for split in ['calibration_check', 'audit', 'validation', 'heldout']:
            prep_path = OUT / 'inputs/evaluation' / split / 'complete.json'
            if not prep_path.exists():
                assert not prep_path.parent.exists(), 'partial preparation needs separate review'
                runner.command(f'{ATTEMPT}_prepare_{split}', [runner.PY, OUT / 'src/prepare_eval.py', '--split', split], threads=1)
            prep = json.loads(prep_path.read_text())
            assert prep['status'] == 'PREPARED'
            for config in prep['configs']:
                path = Path(config)
                root = OUT / 'results' / split / path.parent.name / path.stem
                stage = f'eval_{split}_{path.parent.name}_{path.stem}'
                if verify_completed(root, split):
                    manifest['completed_reused'].append(str(root.relative_to(OUT)))
                    dump(ARCHIVE / 'manifest.json', manifest)
                    continue
                if root.exists():
                    dest = ARCHIVE / 'interrupted_results' / split / path.parent.name / path.stem
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    root.rename(dest)
                    manifest['incomplete_archived'].append({'original': str(root), 'preserved': str(dest)})
                    dump(ARCHIVE / 'manifest.json', manifest)
                start = time.monotonic()
                runner.command(f'{ATTEMPT}_{stage}', [OUT / 'bin/benchmark', path, root])
                assert verify_completed(root, split)
                manifest['newly_completed'].append({'result': str(root), 'seconds': time.monotonic() - start})
                dump(ARCHIVE / 'manifest.json', manifest)
        runner.state.update(status='EVALUATION_COMPLETE_ANALYSIS_PENDING', active_stage=None, active_process=None)
        runner.save()
        os.environ['MPLCONFIGDIR'] = str(OUT / 'logs/matplotlib_cache')
        runner.command(f'{ATTEMPT}_analyze', [runner.PY, OUT / 'src/analyze.py'], threads=1)
        assert json.loads((OUT / 'results/analysis_v1/verification.json').read_text())['status'] == 'PASS'
        manifest.update(status='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING', completed_utc=datetime.now(timezone.utc).isoformat())
        dump(ARCHIVE / 'manifest.json', manifest)
        runner.state.update(status='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING', active_stage=None, active_process=None,
                            next='Review measured comparisons, interpretation and figures; synchronize history, spec, summary and next-stage handoff')
        runner.save()
        supervisor = json.loads((ARCHIVE / 'pipeline_supervisor.json').read_text())
        supervisor.update(status='SUPERSEDED_BY_VERIFIED_REBOOT_RESUME', active_process=None,
                          recovery_controller=os.getpid(), recovery_manifest=str(ARCHIVE / 'manifest.json'))
        dump(OUT / 'pipeline_supervisor.json', supervisor)
    except BaseException as error:
        if runner.child and runner.child.poll() is None:
            os.killpg(runner.child.pid, signal.SIGTERM)
            runner.child.wait()
        runner.state.update(status='RESUME_STOPPED_REQUIRES_INSPECTION', error=repr(error), active_process=None)
        runner.save()
        manifest.update(status='STOPPED_REQUIRES_INSPECTION', error=repr(error))
        dump(ARCHIVE / 'manifest.json', manifest)
        raise


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, runner.stop)
    signal.signal(signal.SIGINT, runner.stop)
    main()
