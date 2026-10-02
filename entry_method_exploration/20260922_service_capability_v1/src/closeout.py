"""Seal the completed stop branch without rerunning training or graph search."""
from common import *
import re
import shutil
from PIL import Image


if __name__ == '__main__':
    start = time.monotonic()
    assert not (RUN / 'reviews/completion_audit.json').exists()
    lock = read(RUN / 'config.locked.json')
    training = read(RUN / 'reviews/training_complete.json')
    result = read(RUN / 'analysis/results.json')
    audit = read(RUN / 'reviews/independent_audit.json')
    assert training['status'] == 'COMPLETE'
    assert (training['fitted_primary'], training['fitted_GBDT_heads'], training['fitted_TabM']) == (32, 16, 8)
    assert result['status'] == 'STOP_CAPABILITY_PILOT'
    assert result['selected'] is None and result['strong_only'] == []
    assert not any(v['pass_all'] for v in result['gates'].values())
    assert not any(result['H1'].values()) and not any(result['H2_mean_contrast'].values())
    for name in ['preflight', 'asset_audit', 'label_return_audit', 'independent_audit']:
        assert read(RUN / f'reviews/{name}.json')['status'] == 'PASS'
    assert training['new_search_calls'] == result['new_search_calls'] == 0
    assert not read(RUN / 'reviews/source_audit.json')['query_payload_opened']

    frozen = read(RUN / 'reviews/pretraining_freeze.json')
    for item in frozen['files'] + [frozen['config'], frozen['protocol'], lock['research']]:
        assert identity(item['path']) == item
    inherited = read(RUN / 'reviews/source_identity.json')['files']
    for item in inherited:
        assert identity(item['path']) == item
    assert len(inherited) == audit['source_files_verified'] == 920
    for item in read(RUN / 'reviews/report_identity.json')['files']:
        assert identity(item['path']) == item

    model_count = 0
    prediction_count = 0
    for ds in lock['datasets']:
        all_outer = np.concatenate([r['outer'] for r in lock['roles'][ds]])
        assert np.array_equal(np.sort(all_outer), np.arange(4096))
        for fold, roles in enumerate(lock['roles'][ds]):
            src = RUN / 'models' / ds / f'fold_{fold}'
            dest = RUN / 'results' / ds / f'fold_{fold}'
            assert (src / 'representation.npz').is_file() and (dest / 'labels.npz').is_file()
            for name in lock['primary'] + lock['strong']:
                assert (src / name / 'training.json').is_file()
                files = ['K0.pickle', 'K1.pickle'] if name == 'GBDT' else ['model.pt']
                assert all((src / name / file).is_file() for file in files)
                model_count += 1
            for name in list(result['results'][ds]):
                if name != 'GT10':
                    pred = np.load(dest / f'{name}.npy', mmap_mode='r')
                    assert pred.shape[0] == 1024 and pred.shape[2] == 2
                    prediction_count += 1
        for name, stats in result['results'][ds].items():
            with np.load(RUN / 'analysis' / ds / f'{name}.npz') as saved:
                assert abs(saved['utility'].mean() - stats['mean_utility']) < 1e-9
                for k, K in enumerate(['1', '100']):
                    assert abs(saved['recall_delta'][:, k].mean() * 100 - stats['K'][K]['recall_delta_pp']) < 1e-8
                if name in lock['primary'] + lock['strong']:
                    assert saved['utility'].mean() < 0
    assert model_count == 48 and prediction_count == 72

    with Image.open(RUN / 'figures/oof_utility.png') as fig:
        pixels = np.asarray(fig.convert('RGB'))
        assert pixels.shape == (750, 1950, 3) and pixels.std() > 10
    docs = [RUN / name for name in ['decision.md', 'report.md', 'theory_bounds.md', 'prior_work_addendum.md', 'inference_cost.md']]
    history = ROOT / 'experiment_history/122_service_capability_pilot.md'
    docs.append(history)
    links = 0
    for path in docs:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' in target or target.startswith('#'):
                continue
            assert (path.parent / target.split('#')[0]).exists(), (path, target)
            links += 1
    root_docs = [ROOT / name for name in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md']]
    for path in root_docs:
        assert 'E119' in path.read_text()[:2000]
    assert all('STOP_CAPABILITY_PILOT' in p.read_text()[:3000] for p in root_docs[:4])

    active = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name) in [os.getpid(), os.getppid()]:
            continue
        try:
            command = (proc / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if RUN.name in command and '/src/' in command:
            active.append(dict(pid=int(proc.name), command=command))
    assert not active, active
    new_bytes = sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file())
    free_bytes = shutil.disk_usage(RUN).free
    assert new_bytes < lock['max_new_bytes'] and free_bytes >= lock['min_free_gib'] * (1 << 30)
    assert training['maxrss_gib'] < lock['max_rss_gib'] and training['seconds'] < lock['max_seconds']

    snapshot = RUN / 'source_after'
    snapshot.mkdir()
    for path in root_docs + [ROOT / 'AGENTS.md', history]:
        target = snapshot / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    requirements = [
        dict(requirement='theory, counterexamples and prior-work distinction', status='COMPLETE', evidence=['research.md', 'theory_bounds.md', 'prior_work_addendum.md']),
        dict(requirement='freeze roles, controls, costs and stop rules before fitting', status='COMPLETE', evidence=['config.locked.json', 'protocol.md', 'reviews/pretraining_freeze.json']),
        dict(requirement='complete all two-dataset query-out controls', status='COMPLETE', evidence=['reviews/training_complete.json', 'analysis/results.json', 'training.log']),
        dict(requirement='audit errors before attributing a negative result', status='COMPLETE_WITH_STATED_SCOPE', evidence=['reviews/preflight.json', 'reviews/independent_audit.json', 'reviews/label_return_audit.json']),
        dict(requirement='conditional native, fresh source and paid full-wall stage', status='NOT_TRIGGERED_BY_FROZEN_GATE', evidence=['analysis/results.json', 'decision.md']),
        dict(requirement='report all outcomes, costs, limits and stopping boundary', status='COMPLETE', evidence=['report.md', 'decision.md', 'figures/oof_utility.png']),
        dict(requirement='preserve source/default and synchronize role-separated documents', status='COMPLETE', evidence=['reviews/source_identity.json', 'source_after/']),
    ]
    dump(RUN / 'reviews/completion_audit.json', dict(status='PASS', branch='STOP_CAPABILITY_PILOT',
        requirements=requirements, source_files_verified=920, completed_model_runs=model_count,
        prediction_files=prediction_count, checked_local_links=links, active_experiment_processes=active,
        new_bytes=new_bytes, free_bytes=free_bytes, figure_nonblank=True,
        figure_visual_review='Inspected rendered PNG; labels, intervals, zero lines and both panels legible.',
        default_changed=False, new_search_calls=0, native_performance_measured=False,
        fresh_blind_test=False, seconds=time.monotonic() - start))
    dump(RUN / 'state.json', dict(status='STOP_CAPABILITY_PILOT', completed=True, default_changed=False,
        new_search_calls=0, selected=None, pending=[], active_processes=[],
        conditional_native_stage='NOT_TRIGGERED', completion_audit='reviews/completion_audit.json'))
    files = sorted(p for p in RUN.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    dump(RUN / 'reviews/final_identity.json', dict(files=[identity(p) for p in files],
        excludes=['reviews/final_identity.json', '__pycache__'], root_documents=[identity(p) for p in root_docs]))
    print('COMPLETION AUDIT PASS: STOP_CAPABILITY_PILOT', flush=True)
