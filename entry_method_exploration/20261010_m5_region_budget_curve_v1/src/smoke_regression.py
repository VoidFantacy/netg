#!/usr/bin/env python3
"""Finite n16 qualification; compare original E173 controls bit for bit."""
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E173 = ROOT.parent / '20261009_nsg_gt_m5_test_v1'
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
           NUMEXPR_NUM_THREADS='1', OMP_DYNAMIC='FALSE')

def load(p):
    return json.loads(p.read_text())

def save(p, x):
    assert not p.exists(), f'preserve {p}'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, indent=2) + '\n')

def main():
    started = time.monotonic()
    runs, checked = [], []
    for ds in ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']:
        formal = load(ROOT / 'jobs' / f'public_test.{ds}.json')
        for kind in ['new', 'original_E173']:
            job = dict(formal) if kind == 'new' else load(E173 / 'jobs_v2' / f'{ds}.combined.json')
            job.update(n=16, role='qualification_smoke', timing_repeats=1, warmup_batches=1, warmup_n=16,
                       threads=1, cpu=15, L=[200, 400, 800, 1000, 1200], K_values=[1, 100],
                       out=str(ROOT / 'smoke' / kind / ds))
            if kind == 'new': job['check_region_zero'] = True
            path = ROOT / 'smoke_jobs' / f'{kind}.{ds}.json'
            save(path, job)
            binary = ROOT / 'bin/benchmark' if kind == 'new' else E173 / 'bin/benchmark_v2'
            log = ROOT / 'logs' / f'smoke.{kind}.{ds}.log'
            assert not log.exists()
            before = time.monotonic()
            with log.open('w') as f:
                r = subprocess.run([str(binary), str(path)], env=ENV, stdout=f, stderr=subprocess.STDOUT,
                                   preexec_fn=lambda: os.sched_setaffinity(0, {15}), timeout=7200)
            receipt = {'kind': kind, 'dataset': ds, 'exit_code': r.returncode,
                       'elapsed_seconds': time.monotonic() - before, 'log': str(log),
                       'job_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                       'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest()}
            runs.append(receipt)
            assert r.returncode == 0, f'qualification failed, preserve partial: {log}'
            assert load(Path(job['out']) / 'complete.json')['status'].startswith('PASS')
        for K in [1, 100]:
            for L in [200, 400, 800, 1000, 1200]:
                for method in ['NSG', 'GT', 'M5']:
                    for filename in ['ids.i32', 'distances.f32', 'entry_ids.i32', 'profile_distances.f32',
                                     'graph_ndc.u64', 'route_ndc.u64', 'audit_query_ids.i32']:
                        suffix = Path(ds) / f'k{K}' / f'{method}_L{L}' / 'raw' / filename
                        new, old = ROOT / 'smoke/new' / suffix, ROOT / 'smoke/original_E173' / suffix
                        assert new.read_bytes() == old.read_bytes(), f'original control word regression: {suffix}'
                        checked.append(str(suffix))
    save(ROOT / 'reviews/smoke_regression.json', {'status': 'PASS_E175_N16_FIVE_L_FULL_ORACLES_AND_E173_WORD_REGRESSION',
         'runs': runs, 'new_points': 80, 'original_control_points': 60,
         'original_control_raw_files_bit_equal': len(checked), 'checked_files': checked,
         'elapsed_seconds': time.monotonic() - started, 'training_increment_seconds': 0,
         'scope': 'qualification only; n16, one wall round; not formal Recall/QPS evidence'})
    print(json.dumps({'status': 'PASS_QUALIFICATION', 'original_files': len(checked),
                      'elapsed_seconds': time.monotonic() - started}))

if __name__ == '__main__':
    main()
