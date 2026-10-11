#!/usr/bin/env python3
"""Acceptance using smoke words and administrative identity only; no GT decode."""
import hashlib
import json
import struct
import time
from pathlib import Path

P = Path(__file__).resolve().parents[1]

def sha(f):
    return hashlib.sha256(Path(f).read_bytes()).hexdigest()

def load(f):
    return json.loads(Path(f).read_text())

assert load(P / 'reviews/smoke_execution.json')['status'].startswith('PASS')
regression, smoke_points = [], []
for ds in ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']:
    c = load(P / 'jobs' / f'smoke.{ds}.json')
    base, old = Path(c['out']), P / 'smoke_original' / ds
    assert load(base / 'complete.json')['status'].startswith('PASS')
    assert load(old / 'complete.json')['status'].startswith('PASS')
    for K in c['K_values']:
        for L in c['L']:
            for m in c['methods']:
                pt = base / f'k{K}' / f'{m["name"]}_L{L}'
                r = load(pt / 'complete.json')
                assert r['full_plain_independent_replay_bits_equal']
                assert r['full_plain_independent_replay_n'] == 16
                assert r['linear_merge_audit_n'] == (0 if m['name'] == 'GT' else 16)
                assert r['plain_count_bits_equal'] and r['normal_output_release_before_stop']
                assert r['threads'] == 1 and r['cpu'] == 15
                if m['extra_cap']:
                    assert r['independent_region_linear_oracle']
                    b = (pt / 'raw/region_trace.i32').read_bytes()
                    assert len(b) == 16 * 128 * 4
                    for row in struct.iter_unpack('<128i', b):
                        C, X, S = row[8:8 + row[3]], row[32:32 + row[4]], row[:row[5]]
                        assert 0 <= row[3] <= 24 and 0 <= row[4] <= m['extra_cap'] and 0 <= row[5] <= 3
                        assert len(set(C)) == len(C) and len(set(X)) == len(X)
                        assert not set(C) & set(X) and set(S) <= set(C)
                elif m['name'] != 'GT':
                    assert r['region_zero_intervention'] and r['region_zero_intervention_n'] == 16
                smoke_points.append(dict(dataset=ds, K=K, L=L, method=m['name'], full_replay_n=16))
            for name in ['GT', 'M5']:
                a = base / f'k{K}' / f'{name}_L{L}' / 'raw'
                b = old / f'k{K}' / f'{name}_L{L}' / 'raw'
                for f in sorted(a.iterdir()):
                    assert f.read_bytes() == (b / f.name).read_bytes(), f'old binary regression: {f}'
                    regression.append(dict(dataset=ds, K=K, L=L, method=name, file=f.name, sha256=sha(f)))
for name in ['native_source_independent_review.json', 'analysis_runner_review.json']:
    r = load(P / 'reviews' / name)
    assert r['status'].startswith('PASS')
    for rel, value in r.get('reviewed_source', {}).items():
        assert sha(P / rel) == value['sha256'], f'reviewed source changed: {rel}'
rec = dict(status='PASS_PREEXECUTION_OLD_M5_WORD_REGRESSION_FULL_SMOKE_ORACLES_AND_STATIC_REVIEWS',
           completed_unix=time.time(),
           scope='16 pilot queries per dataset, all four KLs, no GT quality decode; not formal performance qualification',
           smoke_points=smoke_points, original_GT_M5_raw_file_bit_regression=regression,
           native_review_sha256=sha(P / 'reviews/native_source_independent_review.json'),
           analysis_runner_review_sha256=sha(P / 'reviews/analysis_runner_review.json'),
           build_sha256=sha(P / 'reviews/build.json'))
assert not (P / 'reviews/preexecution_acceptance.json').exists()
(P / 'reviews/preexecution_acceptance.json').write_text(json.dumps(rec, indent=2) + '\n')
pre, stats = load(P / 'reviews/data_preflight.json'), {}
for file, row in pre['registered_input_files'].items():
    s = Path(file).stat()
    v = [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]
    expected = row['stat5_after_complete_preflight']
    assert v == [expected[x] for x in ['device', 'inode', 'size', 'mtime_ns']], f'preflight changed: {file}'
    stats[file] = v
files = list((P / 'src').glob('*.hpp')) + list((P / 'src').glob('*.py'))
files += [P / 'src/benchmark.cpp', P / 'bin/benchmark', P / 'protocol.md', P / 'parameter_lock.json']
files += list((P / 'jobs').glob('confirm_*.json')) + list((P / 'reviews').glob('*review.json'))
files += [P / 'reviews/data_preflight.json', P / 'reviews/preexecution_acceptance.json']
lock = dict(status='FROZEN_AFTER_SMOKE_BEFORE_FORMAL_RESPONSES',
            source_and_binary_sha256={str(f): sha(f) for f in files}, input_stats=stats, no_new_TRAIN=True,
            inputs_sha_closure='reviews/data_preflight.json; full large SHA verified before performance, stat guards during serial jobs')
assert not (P / 'execution_lock.json').exists()
(P / 'execution_lock.json').write_text(json.dumps(lock, indent=2) + '\n')
print(json.dumps(dict(acceptance=rec['status'], smoke_points=len(smoke_points),
                      bit_regression_files=len(regression), frozen_inputs=len(stats),
                      frozen_sources=len(lock['source_and_binary_sha256']))))
