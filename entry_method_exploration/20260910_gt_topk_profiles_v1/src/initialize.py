"""Read-only upstream verification, independent fit/cal copies and fit-only gap statistics.

No validation/held-out bytes, no search labels, no graph searches, no new profiles.
"""
import importlib.util
import os
import platform
import shutil
import subprocess
import time
import numpy as np
from common import DATASETS, E22, E23, ROOT, RUN, dump, identity, read, sha

started = time.monotonic()
assert not (RUN / 'source_before').exists(), 'refuse reinitialization'
for name in ['source_before', 'inputs', 'models', 'diagnostics', 'results', 'figures', 'logs', 'bin', 'reviews']:
    (RUN / name).mkdir(exist_ok=True)
docs = ['AGENTS.md', 'summary.md', 'spec.md', 's-target.md', 's-experiment.md', 'experiment_history/README.md',
        'experiment_history/04_utility_and_representation.md', 'experiment_history/05_probe_reroute.md',
        'experiment_history/08_fast_router_diagnosis.md', 'experiment_history/12_three_entry_rank_exploration.md']
for rel in docs:
    dest = RUN / 'source_before' / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / rel, dest)
(RUN / 'reviews/git_status_before.txt').write_text(subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True))
(RUN / 'reviews/git_diff_before.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT))
protected = {str((ROOT / p).resolve()): identity(ROOT / p) for p in docs}
for item in read(E22 / 'reviews/linked_sources_verified.json'):
    now = identity(item['path'])
    assert now['sha256'] == item['sha256'], item['path']
    protected[now['path']] = now
for name in ['legacy_reference.cpp', 'benchmark_with_nsg.cpp', 'evaluate.cpp']:
    src = E23 / 'src' / name
    shutil.copyfile(src, RUN / 'src' / name)
    protected[str(src)] = identity(src)
for rel in ['benches/run/build_fast_entry_variants.py',
            'entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/report.md',
            'entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/papers.md',
            'entry_method_exploration/20260910_ood_hubs_clustering_router_research_v1/local_evidence.json',
            'fast_router_diagnosis/20260908_v1/protocol.md',
            'fast_router_diagnosis/20260908_v1/analysis/v2/analysis.json',
            'entry_method_exploration/20260910_three_entry_rank_v1/protocol.md',
            'entry_method_exploration/20260910_three_entry_rank_v1/results/summary.json']:
    protected[str(ROOT / rel)] = identity(ROOT / rel)
spec = importlib.util.spec_from_file_location('reference_fast', ROOT / 'benches/run/build_fast_entry_variants.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
summaries = {}
for dataset in DATASETS:
    t = time.monotonic()
    upstream = read(E22 / 'inputs' / dataset / 'verified_sources.json')
    for key, item in upstream.items():
        now = identity(item['path'])
        assert now['sha256'] == item['sha256'], (dataset, key)
        protected[now['path']] = now
    q_all = mod.read_fvecs(__import__('pathlib').Path(upstream['query_train']['path']))
    gt_all = mod.read_ivecs(__import__('pathlib').Path(upstream['gt_train']['path']))
    base, d = mod.fvecs_memmap(__import__('pathlib').Path(upstream['base']['path']))
    assert q_all.shape == (30000, d) and gt_all.shape == (30000, 100)
    assert np.isfinite(q_all).all() and gt_all.min() >= 0 and gt_all.max() < len(base)
    assert np.all(np.diff(np.sort(gt_all, axis=1), axis=1) > 0), 'duplicate GT IDs'
    src = E23 / 'inputs' / dataset
    dest = RUN / 'inputs' / dataset; dest.mkdir()
    for split, rows in [('fit', np.arange(10000, 30000)), ('cal', np.arange(1024))]:
        old = read(src / split / 'config.json')
        assert old['gt_k'] == 100 and old['dim'] == d and old['num_queries'] == len(rows)
        part = dest / split; part.mkdir()
        for name, key, dtype, expected in [('queries.f32', 'queries_file', '<f4', q_all[rows]),
                                           ('gt.i64', 'gt_file', '<i8', gt_all[rows]),
                                           ('row_ids.i64', 'row_ids', '<i8', rows)]:
            a = np.fromfile(old[key], dtype=dtype)
            assert a.size == expected.size and np.array_equal(a.reshape(expected.shape), expected), (dataset, split, name)
            a.tofile(part / name)
            protected[old[key]] = identity(old[key])
        config = {**old, 'queries_file': str(part / 'queries.f32'), 'gt_file': str(part / 'gt.i64'),
                  'row_ids': str(part / 'row_ids.i64'), 'hub_ids': str(dest / 'hub_ids.i32')}
        dump(part / 'config.json', config)
    hubs = np.fromfile(src / 'hub_ids.i32', dtype='<i4')
    assert len(hubs) == (815 if dataset == DATASETS[0] else 821) and np.all(np.diff(hubs) > 0)
    fastdir = ROOT / f'fast_entry_variants/{dataset}_seed20260828'
    manifest = read(fastdir / 'manifest.json')
    assert manifest['variants']['qgt_cover']['seed'] == 20260828
    for key in ['qgt_cover', 'qgt_gt_basin_prototype']:
        item = manifest['variants'][key]
        for kind in ['ids', 'hubs']:
            path = ROOT / item[kind + '_file']
            info = identity(path)
            assert info['sha256'] == item[kind + '_sha256']
            protected[str(path)] = info
    raw_ids = np.fromfile(ROOT / manifest['variants']['qgt_cover']['ids_file'], dtype='<i4')
    raw = np.fromfile(ROOT / manifest['variants']['qgt_cover']['hubs_file'], dtype='<f4').reshape(len(hubs), d)
    assert np.array_equal(hubs, raw_ids) and np.array_equal(raw, base[hubs, 1:])
    hubs.tofile(dest / 'hub_ids.i32'); raw.tofile(dest / 'raw_hubs.f32')
    shutil.copyfile(src / 'P0.f32', dest / 'P0_reference.f32')
    for name in ['hub_ids.i32', 'P0.f32']:
        protected[str(src / name)] = identity(src / name)
    protected[str(fastdir / 'manifest.json')] = identity(fastdir / 'manifest.json')
    # Temperature scale is determined solely by every fit GT1 target and the fixed raw H.
    target = np.asarray(base[gt_all[10000:, 0], 1:], dtype='float32')
    tn, hn = mod.normalize(target), mod.normalize(raw)
    gaps, ties = [], 0
    for begin in range(0, 20000, 4096):
        scores = tn[begin:begin+4096] @ hn.T
        top = np.partition(scores, -2, axis=1)[:, -2:]
        gap = top.max(axis=1) - top.min(axis=1)
        gaps.extend(gap.astype('float64')); ties += int((gap == 0).sum())
    scale = max(float(np.median(gaps)), 1e-4)
    summaries[dataset] = {'dataset': dataset, 'dim': d, 'base_rows': len(base), 'H': len(hubs),
        'base_file': upstream['base']['path'], 'index_path': upstream['graph']['path'],
        'gap_definition': 'float32 cosine highest minus second-highest, all fit GT1 targets only',
        'gap_quantiles': np.quantile(gaps, [0, .1, .25, .5, .75, .9, 1]).tolist(),
        'top_ties': ties, 'temperature_scale': scale, 'temperatures': [scale/4, scale, scale*4],
        'source_fast_manifest': str(fastdir / 'manifest.json'), 'source_train': upstream,
        'seconds': time.monotonic()-t, 'GT_width': 100,
        'fit_rows': [10000, 30000], 'cal_rows': [0, 1024], 'audit_rows_deferred': [1024, 2048]}
    dump(dest / 'prepared.json', summaries[dataset])
    print(dataset, 'IDENTITY_PASS', 'temperatures', summaries[dataset]['temperatures'], flush=True)
dump(RUN / 'reviews/protected_before.json', list(protected.values()))
dump(RUN / 'inputs/preflight.json', {'status': 'PASS', 'datasets': summaries, 'seconds': time.monotonic()-started,
    'validation_opened': False, 'heldout_opened': False, 'single_or_triple_labels_opened': False,
    'cpu': platform.processor(), 'platform': platform.platform(), 'cpus': os.cpu_count(),
    'affinity': sorted(os.sched_getaffinity(0)), 'free_disk_bytes': shutil.disk_usage(ROOT).free})
dump(RUN / 'state.json', {'status': 'IDENTITY_VERIFIED_PROTOCOL_PENDING', 'new_real_search_calls': 0,
    'validation_opened': False, 'heldout_opened': False})
