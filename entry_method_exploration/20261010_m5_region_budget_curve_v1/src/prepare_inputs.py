#!/usr/bin/env python3
"""Administrative copy of a frozen, already exposed E173 public window."""
import copy
import hashlib
import json
import os
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / '20261010_m5_residual_regions_v1'
E173 = ROOT.parent / '20261009_nsg_gt_m5_test_v1'

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def save(p, x):
    assert not p.exists(), f'preserve {p}'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False) + '\n')

def stat(p):
    s = Path(p).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]

def main():
    os.sched_setaffinity(0, {14})
    started = time.monotonic()
    protocol_sha = sha(ROOT / 'protocol.md')
    # Freeze the matrix before copying any already known GT words.
    save(ROOT / 'scope_lock.json', {'status': 'FROZEN_BEFORE_PUBLIC_WINDOW_COPY',
         'protocol_sha256': protocol_sha, 'datasets': ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1'],
         'role': 'public_test', 'n': 10000, 'source_window': [0, 10000],
         'methods': ['NSG', 'GT', 'M5', 'M5REG96'], 'K_values': [1, 100],
         'L': [200, 400, 800, 1000, 1200], 'timing_repeats': 3, 'threads': 1, 'cpu': 15,
         'points': 80, 'timed_batches': 240, 'comparisons': 200, 'mechanisms': 20,
         'TRAIN_increment_seconds': 0, 'created_unix': time.time()})
    old_pre = read(PARENT / 'reviews/data_preflight.json')
    old_exec = read(PARENT / 'execution_lock.json')
    registered = {}
    # Reuse prior complete SHA only with unchanged current stat. Record the
    # scope honestly: these old inputs are not all rehashed in this stage.
    for name, expected_stat in old_exec['input_stats'].items():
        assert stat(name) == expected_stat, f'prior registered input drift: {name}'
        previous = old_pre['registered_input_files'][name]
        registered[name] = {'path': name, 'sha256': previous['sha256'],
                            'bytes': expected_stat[2], 'identity_scope': 'prior complete E174 SHA plus current exact stat',
                            'prior_receipt': str(PARENT / 'reviews/data_preflight.json'),
                            'current_stat': expected_stat}
    inventory = {'status': 'PASS_FROZEN_ORIGINAL_M5_SUPPORT_INVENTORY', 'datasets': {},
                 'prior_inventory': str(PARENT / 'reviews/inventory.json'),
                 'no_new_training': True, 'scope': 'E175 public-window sweep; old supervision retained'}
    datasets = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
    derived = []
    for ds in datasets:
        original = read(E173 / 'jobs_v2' / f'{ds}.combined.json')
        job = read(PARENT / 'jobs' / f'confirm_a.{ds}.json')
        d = job['dimension']
        sources = [(original['queries'], original['query_sha256']), (original['GT'], original['GT_sha256'])]
        for name, expected in sources:
            before = stat(name)
            actual = sha(name)
            assert actual == expected and stat(name) == before, f'public source identity: {name}'
            registered[name] = {'path': name, 'sha256': actual, 'bytes': before[2],
                                'identity_scope': 'fresh complete E175 SHA', 'current_stat': before}
        qpath, gpath = map(Path, [original['queries'], original['GT']])
        assert qpath.stat().st_size % (4 * (d + 1)) == 0
        source_q = np.memmap(qpath, dtype='<i4', mode='r').reshape(-1, d + 1)
        assert len(source_q) >= 10000 and np.all(source_q[:10000, 0] == d)
        source_g = np.memmap(gpath, dtype='<i4', mode='r')
        width = int(source_g[0])
        assert width == 100 and source_g.size % (width + 1) == 0
        source_g = source_g.reshape(-1, width + 1)
        assert len(source_g) >= 10000 and np.all(source_g[:10000, 0] == width)
        qwords = np.array(source_q[:10000, 1:], dtype='<i4', order='C')
        gt = np.array(source_g[:10000, 1:], dtype='<i4', order='C')
        assert np.all(np.isfinite(qwords.view('<f4')))
        assert np.all((gt >= 0) & (gt < job['base_n']))
        assert all(len(set(row)) == 100 for row in gt)
        dst = ROOT / 'inputs' / ds
        dst.mkdir(parents=True, exist_ok=False)
        qp, gp, rp = dst / 'queries.f32', dst / 'gt.i32', dst / 'window_rows.i64'
        qwords.tofile(qp)
        gt.tofile(gp)
        np.arange(10000, dtype='<i8').tofile(rp)
        for name in [qp, gp, rp]:
            registered[str(name)] = {'path': str(name), 'sha256': sha(name), 'bytes': name.stat().st_size,
                                     'identity_scope': 'fresh derived window SHA', 'current_stat': stat(name)}
        old_m5 = next(m for m in job['methods'] if m['name'] == 'M5')
        reg = next(m for m in job['methods'] if m['name'] == 'M5REG96')
        gt_method = next(m for m in job['methods'] if m['name'] == 'GT')
        nsg = copy.deepcopy(gt_method)
        nsg['name'] = 'NSG'
        job.update(role='public_test', n=10000, queries=str(qp), query_format='raw', query_first=0,
                   query_sha256=registered[str(qp)]['sha256'], GT=str(gp), GT_format='raw', GT_dtype='<i4', GT_width=100,
                   GT_sha256=registered[str(gp)]['sha256'], rows=str(rp), rows_sha256=registered[str(rp)]['sha256'],
                   source_query_fvecs=str(qpath), source_query_sha256=original['query_sha256'],
                   source_GT_ivecs=str(gpath), source_GT_sha256=original['GT_sha256'],
                   source_window_first=0, source_window_n=10000, source_rows_scope='source-file window positions only',
                   L=[200, 400, 800, 1000, 1200], methods=[nsg, gt_method, old_m5, reg],
                   out=str(ROOT / 'results/public_test' / ds), no_training=True, audit_n=256)
        save(ROOT / 'jobs' / f'public_test.{ds}.json', job)
        old_inventory = read(PARENT / 'reviews/inventory.json')['datasets'][ds]
        inventory['datasets'][ds] = {k: old_inventory[k] for k in ['m5', 'compile_manifest']}
        derived.append({'dataset': ds, 'n': 10000, 'dimension': d, 'source_query_n': len(source_q),
                        'source_GT_n': len(source_g), 'GT_width': width, 'raw_query_words_equal_source': True,
                        'raw_GT_words_equal_source': True, 'rows_are_source_file_positions': True})
    assert sha(ROOT / 'protocol.md') == protocol_sha
    save(ROOT / 'reviews/inventory.json', inventory)
    save(ROOT / 'reviews/data_preflight.json', {'status': 'PASS_E175_SOURCE_IDENTITIES_AND_FIXED_WINDOW_COPY',
         'registered_input_files': registered, 'derived_windows': derived,
         'prior_complete_large_SHA_receipt': str(PARENT / 'reviews/data_preflight.json'),
         'administrative_access': 'reads existing exposed query and GT words; no new native responses, no new teacher',
         'protocol_sha256': protocol_sha, 'elapsed_seconds': time.monotonic() - started,
         'training_increment_seconds': 0, 'hash_cpu_affinity': [14]})
    jobs = {str(p): sha(p) for p in sorted((ROOT / 'jobs').glob('*.json'))}
    save(ROOT / 'parameter_lock.json', {'status': 'FROZEN_E175_80_POINT_PUBLIC_BUDGET_SWEEP',
         'protocol_sha256': protocol_sha, 'jobs': jobs, 'primary_method': 'M5REG96',
         'no_new_TRAIN': True, 'no_adaptive_cancel_or_selection': True, 'parameters_freeze_unix': time.time()})
    snapshots = {str(p): sha(p) for p in sorted((ROOT / 'source_before').glob('*.md'))}
    save(ROOT / 'source_before/manifest.json', {'root_documents': snapshots, 'scope': 'before E175 current markers'})
    print(json.dumps({'status': 'PASS_PREPARED', 'jobs': len(jobs), 'inputs': len(registered),
                      'elapsed_seconds': time.monotonic() - started}))

if __name__ == '__main__':
    main()
