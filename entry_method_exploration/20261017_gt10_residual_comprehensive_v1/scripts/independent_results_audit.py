#!/usr/bin/env python3
"""Independent E183 integer-set and retained-packet audit; never runs ANN.

Does not import the main analyzer or native implementation. Rebuilds TRAIN
omission source pools from GT and actual teacher outputs, parses posting tables,
scores all formal outputs with Python integer sets, and compares published CSVs.
Full floating-point distance/oracle execution remains the native qualification
and GT audit's separate evidence; bootstrap/interpolation are outside this audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
FREQUENCY_LABELS = ('0', '1', '2..5', '6..20', '21+')
FREQUENCY_FIELDS = ('missing_members', 'correct_members', 'missing_in_residual_source',
                    'missing_in_uncapped_routed_source', 'missing_in_selected_table',
                    'rescued_members', 'damaged_members')


def insist(condition, description):
    if not condition:
        raise AssertionError(description)


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


class Reader:
    def __init__(self):
        self.files = {}

    def register(self, path):
        p = Path(path).resolve()
        s = p.stat()
        if str(p) not in self.files:
            self.files[str(p)] = dict(bytes=s.st_size, mtime_ns=s.st_mtime_ns, sha256=file_sha(p))
        old = self.files[str(p)]
        insist((s.st_size, s.st_mtime_ns) == (old['bytes'], old['mtime_ns']), 'changed input: ' + str(p))
        return p

    def json(self, path):
        return json.loads(self.register(path).read_text())

    def array(self, path, dtype, shape):
        import numpy as np
        p = self.register(path)
        insist(p.stat().st_size == math.prod(shape) * np.dtype(dtype).itemsize, 'array shape: ' + str(p))
        return np.memmap(p, dtype=dtype, mode='r', shape=shape)

    def finish(self):
        for path, old in self.files.items():
            s = Path(path).stat()
            insist((s.st_size, s.st_mtime_ns) == (old['bytes'], old['mtime_ns']), 'post-read identity drift')


def truth(spec, reader):
    """Independent on-disk GT reader, retaining original exact-ID convention."""
    n, start = int(spec['n']), int(spec.get('row_start', 0))
    total, width = int(spec.get('total_n', n)), int(spec.get('k', spec.get('width', 100)))
    insist(width == 100 and 0 <= start <= total - n, 'GT role/window')
    fmt = spec['format']
    if fmt == 'ivecs':
        a = reader.array(spec['path'], '<i4', (total, 101))
        insist(all(int(x) == 100 for x in a[:, 0]), 'GT ivecs headers')
        return a[start:start + n, 1:]
    insist(fmt in ('raw_i32', 'raw_i64'), 'GT supported frozen format')
    return reader.array(spec['path'], '<i8' if fmt == 'raw_i64' else '<i4', (total, 100))[start:start + n]


def id_sets(array, N, label):
    out = []
    for row in array:
        s = set(row.tolist())
        insist(len(s) == len(row) and all(0 <= v < N for v in s), label + ' unique domain IDs')
        out.append(s)
    return out


def read_table(path, reader, N, expected_ids):
    """Parse every table byte independently of native Posting and analyzer."""
    import numpy as np
    data = reader.register(path).read_bytes()
    magic, ver, H, B, slots, pairs, base_n, reserved1, reserved2 = struct.unpack_from('<8s8I', data)
    insist(magic == b'M5POST1\0' and ver == 1 and base_n == N and B in (8, 16, 32), 'table header')
    insist(slots >= H * 2 and slots & (slots - 1) == 0, 'table hash capacity')
    pos = 40
    def take(dtype, count):
        nonlocal pos
        size = np.dtype(dtype).itemsize * count
        insist(pos + size <= len(data), 'bounded table region')
        a = np.frombuffer(data, dtype=dtype, count=count, offset=pos)
        pos += size
        return a
    labels = take('<i4', H).tolist()
    counts = take('u1', H).tolist()
    flat = take('<i4', H * B).reshape(H, B)
    keys, values = take('<i4', slots).tolist(), take('<i4', slots).tolist()
    sorted_labels, sorted_rows = take('<i4', H).tolist(), take('<i4', H).tolist()
    insist(pos == len(data) and labels == list(map(int, expected_ids)), 'table exact byte/ordered hub binding')
    insist(sorted_labels == sorted(labels) and [labels[i] for i in sorted_rows] == sorted_labels,
           'table sorted fallback')
    occupied = {key: value for key, value in zip(keys, values) if key != -1}
    insist(len(occupied) == H and sum(key != -1 for key in keys) == H
           and all(occupied[label] == i for i, label in enumerate(labels)), 'table complete hash map')
    insist(all(value == -1 for key, value in zip(keys, values) if key == -1), 'table empty hash pairs')
    rows = []
    for i, count in enumerate(counts):
        values_row = flat[i, :count].tolist()
        insist(0 <= count <= B and len(set(values_row)) == count and all(0 <= v < N for v in values_row), 'table legal rows')
        insist(all(int(x) == -1 for x in flat[i, count:]), 'table padding')
        rows.append(values_row)
    insist(sum(counts) == pairs, 'table pair total')
    return rows, B


def audit_training(entry, reader):
    """Rebuild all tokens and all untruncated source pools, no main analyzer."""
    import numpy as np
    cfg = reader.json(ROOT / 'configs' / (entry['dataset'] + '.compile.json'))
    gt = truth(cfg['train_gt'], reader)
    n, N = len(gt), entry['base']['n']
    truths = id_sets(gt, N, 'TRAIN GT')
    training_frequency = Counter()
    for row in truths:
        training_frequency.update(row)
    insist(sum(training_frequency.values()) == n * 100, 'full TRAIN query-target memberships')
    models, receipts = {}, []
    for teacher in cfg['teachers']:
        name = teacher['name']
        td = Path(teacher['teacher_dir'])
        receipt = reader.json(td / 'complete.json')
        insist(receipt['status'] == 'PASS_TRAIN_TEACHER' and receipt['n'] == n
               and receipt['K'] == 100 and receipt['L'] == 200
               and receipt['any_GT_read'] is False and receipt['test_queries_read'] is False, 'TRAIN receipt')
        ids = reader.array(teacher['ids'], '<i4', (entry['H'],)).tolist()
        slots = {label: i for i, label in enumerate(ids)}
        response_ids = reader.array(td / 'raw/ids.i32', '<i4', (n, 100))
        returned = id_sets(response_ids, N, 'TRAIN outputs')
        routes = reader.array(td / 'raw/entry_ids.i32', '<i4', (n, 3))
        response_distances = reader.array(td / 'raw/distances.f32', '<f4', (n, 100))
        profile_distances = reader.array(td / 'raw/profile_distances.f32', '<f4', (n, 3))
        packet_digest = hashlib.sha256(struct.pack('<QQ', n, 100))
        for values in (response_ids, response_distances, routes, profile_distances):
            packet_digest.update(values.tobytes())
        packet_digest.update(b'\0' * (16 * n))
        insist(packet_digest.hexdigest() == receipt['packet_sha256'], 'TRAIN raw packet SHA matches actual teacher')
        root = Path(cfg['output_dir']) / name
        meta = reader.json(root / 'compile_manifest.json')
        insist(meta['status'] == 'PASS_NEW_K100_NESTED_TABLES' and meta['residual_n'] == n
               and meta['train_gt'] == cfg['train_gt'] and meta['all_test_or_eval_GT_access'] is False, 'compile provenance')
        token_n = meta['tokens']
        tq = reader.array(root / 'source/token_queries.i32', '<i4', (token_n,))
        tt = reader.array(root / 'source/token_targets.i32', '<i4', (token_n,))
        missing, hub_pools, global_pool, cursor = [], [set() for _ in ids], set(), 0
        residual_frequency = Counter()
        for qi, (g, r, route) in enumerate(zip(truths, returned, routes)):
            absent = g - r
            missing.append(absent)
            residual_frequency.update(absent)
            expected = sorted(absent)
            stop = cursor + len(expected)
            insist(tt[cursor:stop].tolist() == expected and all(int(v) == qi for v in tq[cursor:stop]), 'TRAIN exact omission tokens')
            cursor = stop
            hubs = route.tolist()
            insist(len(set(hubs)) == 3 and all(h in slots for h in hubs), 'TRAIN three valid routes')
            for hub in hubs:
                hub_pools[slots[hub]].update(absent)
            global_pool.update(absent)
        insist(cursor == token_n, 'complete TRAIN token consumption')
        insist(sum(residual_frequency.values()) == token_n
               and all(count <= training_frequency[target] for target, count in residual_frequency.items()),
               'independent residual query-target frequency bounded by full TRAIN frequency')
        global_file = reader.array(root / 'source/global_ids.i32', '<i4', (meta['global_source_unique_targets'],))
        insist(global_file.tolist() == sorted(global_pool), 'full residual global source reconstructed')
        offsets = reader.array(root / 'source/hub_offsets.u64', '<u8', (len(ids) + 1,))
        edges = meta['candidate_key_target_edges']
        targets = reader.array(root / 'source/hub_targets.i32', '<i4', (edges,))
        insist(int(offsets[0]) == 0 and int(offsets[-1]) == edges, 'source edge endpoints')
        for i, pool in enumerate(hub_pools):
            lo, hi = int(offsets[i]), int(offsets[i + 1])
            insist(0 <= lo <= hi <= edges and targets[lo:hi].tolist() == sorted(pool), 'full hub residual source reconstructed')
        tables, previous, coverages = {}, None, {}
        for cap in (8, 16, 32):
            md = meta['models']['JOINT' + str(cap)]
            rows, actual_cap = read_table(md['binary'], reader, N, ids)
            insist(actual_cap == cap and reader.json(md['rows_file']) == rows, 'binary/JSON row identity')
            insist(all(set(row) <= pool for row, pool in zip(rows, hub_pools)), 'selected targets have TRAIN support')
            if previous is not None:
                insist(all(row[:len(old)] == old for row, old in zip(rows, previous)), 'B8->16->32 ordered prefix')
            sets = list(map(set, rows))
            count = sum(len(absent & set.union(*(sets[slots[int(h)]] for h in route))) for absent, route in zip(missing, routes))
            insist(count == md['training_integer_coverage'], 'independent full TRAIN coverage')
            coverages[str(cap)] = count
            tables[cap] = sets
            previous = rows
        models[name] = dict(ids=ids, slots=slots, global_pool=global_pool, hub_pools=hub_pools, tables=tables,
                            frequency_maps={'training_query_count': training_frequency,
                                            'residual_query_count': residual_frequency})
        receipts.append(dict(dataset=entry['dataset'], router=name, queries=n, tokens=token_n,
                             global_targets=len(global_pool), hub_target_edges=edges,
                             full_source_reconstructed=True, integer_training_coverage=coverages,
                             full_training_query_target_memberships=sum(training_frequency.values()),
                             residual_query_target_memberships=sum(residual_frequency.values()),
                             query_frequency_reconstructed_from_unique_per_query_sets=True,
                             actual_greedy_selection_sequence_recomputed=False))
    return models, receipts


def pair_counts(reference, actual, k):
    """Integer set differences; not GT-axis broadcast masks used by analyzer."""
    n = len(reference)
    old_hits = sum(map(len, reference))
    hits = sum(map(len, actual))
    rescue = [len(b - a) for a, b in zip(reference, actual)]
    damage = [len(a - b) for a, b in zip(reference, actual)]
    delta = [len(b) - len(a) for a, b in zip(reference, actual)]
    threshold = (9 * k + 9) // 10
    result = dict(n=n, reference_hits=old_hits, hits=hits, rescued_members=sum(rescue),
                  damaged_members=sum(damage), net_members=hits - old_hits,
                  reference_missing_members=n * k - old_hits, reference_correct_members=old_hits,
                  rescued_queries=sum(v > 0 for v in rescue), damaged_queries=sum(v > 0 for v in damage),
                  net_improved_queries=sum(v > 0 for v in delta), net_worsened_queries=sum(v < 0 for v in delta),
                  unchanged_query_recall=sum(v == 0 for v in delta),
                  reference_full_success_queries=sum(len(s) == k for s in reference),
                  actual_full_success_queries=sum(len(s) == k for s in actual),
                  failed_queries_become_full_success=sum(len(a) < k and len(b) == k for a, b in zip(reference, actual)),
                  full_success_queries_become_failed=sum(len(a) == k and len(b) < k for a, b in zip(reference, actual)),
                  reference_at_least_90pct_queries=sum(len(s) >= threshold for s in reference),
                  actual_at_least_90pct_queries=sum(len(s) >= threshold for s in actual),
                  below_90pct_become_at_least_90pct_queries=sum(len(a) < threshold <= len(b) for a, b in zip(reference, actual)),
                  at_least_90pct_become_below_90pct_queries=sum(len(b) < threshold <= len(a) for a, b in zip(reference, actual)))
    insist(result['net_members'] == result['rescued_members'] - result['damaged_members'], 'integer net identity')
    return result


def cascade_counts(truths, nsg, gt, post, k):
    """Three-stage GT membership changes, directly from per-query ID sets."""
    insist(len(truths) == len(nsg) == len(gt) == len(post), 'cascade cohort identity')
    result = dict(n=len(truths), NSG_correct_GT10_lost_members=0,
                  of_these_residual_restored_members=0, of_these_still_missing_members=0,
                  both_NSG_GT10_missing_members=0,
                  of_these_residual_restored_members_from_joint_failures=0,
                  GT10_rescued_NSG_missing_members=0, of_these_residual_lost_again_members=0,
                  NSG_full_GT10_failed_queries=0, of_these_residual_full_success_queries=0)
    for correct, initial, prior, final in zip(truths, nsg, gt, post):
        lost = initial - prior
        jointly_missing = correct - (initial | prior)
        gained = prior - initial
        result['NSG_correct_GT10_lost_members'] += len(lost)
        result['of_these_residual_restored_members'] += len(lost & final)
        result['of_these_still_missing_members'] += len(lost - final)
        result['both_NSG_GT10_missing_members'] += len(jointly_missing)
        result['of_these_residual_restored_members_from_joint_failures'] += len(jointly_missing & final)
        result['GT10_rescued_NSG_missing_members'] += len(gained)
        result['of_these_residual_lost_again_members'] += len(gained - final)
        new_failed = len(initial) == k and len(prior) < k
        result['NSG_full_GT10_failed_queries'] += int(new_failed)
        result['of_these_residual_full_success_queries'] += int(new_failed and len(final) == k)
    insist(result['NSG_correct_GT10_lost_members'] == result['of_these_residual_restored_members']
           + result['of_these_still_missing_members'], 'cascade lost-member partition')
    return result


def frequency_label(count):
    insist(isinstance(count, int) and count >= 0, 'nonnegative integer TRAIN query frequency')
    if count < 2:
        return str(count)
    if count <= 5:
        return '2..5'
    if count <= 20:
        return '6..20'
    return '21+'


def new_frequency_counts():
    return {(kind, label): dict.fromkeys(FREQUENCY_FIELDS, 0)
            for kind in ('residual_query_count', 'training_query_count') for label in FREQUENCY_LABELS}


def accumulate_frequency_counts(result, correct, prior, final, routed, selected, support):
    """Count individual GT IDs; frequency comes from independent TRAIN Counters."""
    for target in correct:
        missing = target not in prior
        for kind, counts in support['frequency_maps'].items():
            row = result[kind, frequency_label(counts.get(target, 0))]
            row['missing_members' if missing else 'correct_members'] += 1
            if missing:
                row['missing_in_residual_source'] += int(target in support['global_pool'])
                row['missing_in_uncapped_routed_source'] += int(target in routed)
                row['missing_in_selected_table'] += int(target in selected)
                row['rescued_members'] += int(target in final)
            else:
                row['damaged_members'] += int(target not in final)


def assert_ratio(numerator, denominator, published, field, label):
    if not denominator:
        insist(published[field] == '', label + '/' + field + '/undefined denominator')
    else:
        insist(math.isclose(float(published[field]), numerator / denominator, rel_tol=1e-12, abs_tol=1e-12),
               label + '/' + field)


def audit_packet(meta, cfg, reader):
    import numpy as np
    n, k, N = meta['n'], meta['K'], cfg['base']['n']
    insist(n == cfg['queries']['n'] and meta['metric_id'] == cfg['metric_id']
           and meta['threads'] == 1 and meta['cpu'] == 15, 'point actual task/environment identity')
    point = Path(meta['result_dir'])
    insist(reader.json(point / 'result.json') == meta, 'point and complete metadata equality')
    insist(meta['status'] == 'PASS_E183_POINT' and meta['timed_output_retained']
           and meta['normal_output_destroyed_within_wall'] and meta['uniform_packet_copy_inside_wall']
           and meta['full_merge_oracle_passed'] and meta['formal_performance']
           and meta['counts_collected'] is False and meta['NDC'] is None, 'formal point assertions')
    shapes = [('ids.i32', '<i4', (n, k)), ('distances.f32', '<f4', (n, k)),
              ('entry_ids.i32', '<i4', (n, 3)), ('profile_distances.f32', '<f4', (n, 3))]
    arrays = [reader.array(point / 'raw' / f, d, s) for f, d, s in shapes]
    digest = hashlib.sha256(struct.pack('<QQ', n, k))
    for a in arrays:
        digest.update(a.tobytes(order='C'))
    digest.update(b'\0' * (n * 8))
    digest.update(b'\0' * (n * 8))
    outputs = id_sets(arrays[0], N, 'formal output')
    insist(np.isfinite(arrays[1]).all() and np.isfinite(arrays[3]).all(), 'finite actual native scores')
    insist(k == 1 or np.all(arrays[1][:, 1:] >= arrays[1][:, :-1]), 'ascending distance packet')
    if meta['family'] == 'NSG':
        insist(np.all(arrays[2][:, 1:] == -1) and np.all(arrays[3].view('<u4') == 0), 'NSG unused slots')
    else:
        id_sets(arrays[2], N, 'router entry')
    rounds, qps = meta['rounds'], []
    insist(len(rounds) == 3, 'three actual timings')
    for i, rr in enumerate(rounds):
        insist(reader.json(point / ('round' + str(i) + '.json')) == rr, 'round standalone identity')
        insist(rr['round'] == i and rr['threads'] == 1 and rr['cpu'] == 15
               and rr['stored_round'] == 0 and rr['first_round_bits_equal']
               and rr['packet_sha256'] == digest.hexdigest(), 'actual round native SHA and environment')
        wall = float(rr['wall_seconds'])
        insist(wall > 0 and math.isfinite(wall) and math.isclose(rr['qps'], n / wall, rel_tol=1e-12), 'wall-derived QPS')
        qps.append(n / wall)
    insist(math.isclose(meta['qps'], statistics.median(qps), rel_tol=1e-12), 'median QPS')
    insist(math.isclose(meta['wall_seconds'], statistics.median([r['wall_seconds'] for r in rounds]), rel_tol=1e-12), 'median wall')
    return dict(output=outputs, arrays=arrays, qps=qps, digest=digest.hexdigest())


def csv_rows(path, keys, reader):
    with reader.register(path).open(newline='') as f:
        rows = list(csv.DictReader(f))
    result = {tuple(r[k] for k in keys): r for r in rows}
    insist(len(result) == len(rows), 'unique published CSV keys')
    return result


def assert_int_fields(actual, published, label):
    for key, value in actual.items():
        if isinstance(value, int):
            insist(key in published and int(published[key]) == value, label + '/' + key)


def selftest():
    stats = pair_counts([{1, 2}, set(), {3}], [{2, 4}, {1}, {3}], 2)
    insist(stats['rescued_members'] == 2 and stats['damaged_members'] == 1
           and stats['net_members'] == 1 and stats['net_improved_queries'] == 1, 'handwritten set fixture')
    empty = pair_counts([], [], 100)
    insist(empty['n'] == empty['net_members'] == 0, 'empty stratum fixture')
    insist(hashlib.sha256(struct.pack('<QQ', 1, 1) + b'\0' * 48).hexdigest()
           != hashlib.sha256(struct.pack('<QQ', 1, 100) + b'\0' * 48).hexdigest(), 'packet shape distinction')
    cascade = cascade_counts([{1, 2}, {3, 4}, {5, 6}], [{1, 2}, set(), {5}],
                             [{1}, {3}, {6}], [{1, 2}, {4}, {5, 6}], 2)
    insist(cascade == dict(n=3, NSG_correct_GT10_lost_members=2,
                          of_these_residual_restored_members=2, of_these_still_missing_members=0,
                          both_NSG_GT10_missing_members=1,
                          of_these_residual_restored_members_from_joint_failures=1,
                          GT10_rescued_NSG_missing_members=2, of_these_residual_lost_again_members=1,
                          NSG_full_GT10_failed_queries=1, of_these_residual_full_success_queries=1),
           'handwritten three-stage cascade fixture')
    insist([frequency_label(v) for v in (0, 1, 2, 5, 6, 20, 21, 16000)]
           == ['0', '1', '2..5', '2..5', '6..20', '6..20', '21+', '21+'], 'frequency boundaries')
    freq = new_frequency_counts()
    accumulate_frequency_counts(freq, {10, 20, 30, 40}, {10, 20}, {20, 30}, {30}, {10, 30},
                                {'global_pool': {20, 30, 40},
                                 'frequency_maps': {'training_query_count': {10: 1, 20: 5, 30: 21, 40: 6},
                                                    'residual_query_count': {20: 1, 30: 6, 40: 2}}})
    expected = new_frequency_counts()
    for kind, lost_band, correct_band, rescued_band, missed_band in (
            ('training_query_count', '1', '2..5', '21+', '6..20'),
            ('residual_query_count', '0', '1', '6..20', '2..5')):
        expected[kind, lost_band].update(correct_members=1, damaged_members=1)
        expected[kind, correct_band].update(correct_members=1)
        expected[kind, rescued_band].update(missing_members=1, missing_in_residual_source=1,
                                            missing_in_uncapped_routed_source=1, missing_in_selected_table=1,
                                            rescued_members=1)
        expected[kind, missed_band].update(missing_members=1, missing_in_residual_source=1)
    insist(freq == expected, 'handwritten independent frequency-axis membership fixture')
    return {'status': 'PASS_INDEPENDENT_AUDIT_HANDWRITTEN_FIXTURES', 'scientific_data_read': False}


def audit(analysis, output):
    started = time.monotonic()
    reader = Reader()
    catalogue = reader.json(ROOT / 'reviews/dataset_catalogue.json')
    insist(len(catalogue['datasets']) == 7 and catalogue['expected_points'] == 645
           and catalogue['expected_formal_batches'] == 1935, 'frozen seven-dataset matrix')
    for entry in catalogue['datasets'].values():
        cfg = reader.json(entry['benchmark_config'])
        done = reader.json(Path(cfg['output_dir']) / 'complete.json')
        insist(done['status'] == 'PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES', 'all formal runs complete before audit')
    # Heavy numerical/file analysis begins only after every formal run has ended.
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    if 14 in os.sched_getaffinity(0):
        os.sched_setaffinity(0, {14})
    insist(reader.json(analysis / 'summary.json')['status'] == 'PASS_E183_RETAINED_OUTPUT_ANALYSIS', 'published analysis complete')
    point_csv = csv_rows(analysis / 'points.csv', ['dataset', 'method', 'K', 'L'], reader)
    pair_csv = csv_rows(analysis / 'same_L_deltas.csv', ['dataset', 'method', 'K', 'L'], reader)
    strata_csv = csv_rows(analysis / 'failure_strata.csv', ['dataset', 'method', 'K', 'L', 'reference_hit_band'], reader)
    coverage_csv = csv_rows(analysis / 'candidate_coverage.csv', ['dataset', 'method', 'K', 'L'], reader)
    cascade_csv = csv_rows(analysis / 'failure_cascade.csv', ['dataset', 'method', 'K', 'L'], reader)
    frequency_csv = csv_rows(analysis / 'target_frequency.csv',
                             ['dataset', 'method', 'K', 'L', 'frequency_kind', 'training_target_query_frequency'], reader)
    point_records, pair_records, source_records, coverage_records = [], [], [], []
    cascade_records, frequency_records = [], []
    total_rounds, stratum_count = 0, 0
    for ds, entry in catalogue['datasets'].items():
        cfg = reader.json(entry['benchmark_config'])
        complete = reader.json(Path(cfg['output_dir']) / 'complete.json')
        n, N = cfg['queries']['n'], cfg['base']['n']
        insist(complete['config'] == cfg and complete['formal_performance'] and complete['threads'] == 1
               and complete['cpu'] == 15 and complete['evaluation_GT_read'] is False, 'native complete configuration')
        gt = truth(entry['test_gt'], reader)
        truths100 = id_sets(gt, N, 'eval GT')
        truths1 = [{int(row[0])} for row in gt]
        models, source = audit_training(entry, reader)
        source_records.extend(source)
        descriptors = {m['name']: m for m in cfg['methods']}
        points = {(p['method'], p['K'], p['L']): p for p in complete['results']}
        expected = {(m, k, int(L)) for m in descriptors for k in (1, 100) for L in cfg['K_L'][str(k)]}
        insist(set(points) == expected and len(points) == len(complete['results']) == complete['points'], 'exact native point matrix')
        insist(complete['formal_batches'] == 3 * len(points) and complete['formal_queries'] == 3 * len(points) * n,
               'complete formal accounting')
        orders = [r['measurement_order'] for p in complete['results'] for r in p['rounds']]
        insist(sorted(orders) == list(range(1, 3 * len(points) + 1)), 'unique complete execution order')
        for k in (1, 100):
            truths = truths1 if k == 1 else truths100
            for L in cfg['K_L'][str(k)]:
                packets = {}
                for method in descriptors:
                    packet = audit_packet(points[(method, k, L)], cfg, reader)
                    packet['hits'] = [truth_set & returned for truth_set, returned in zip(truths, packet['output'])]
                    hits = sum(map(len, packet['hits']))
                    record = dict(dataset=ds, method=method, K=k, L=L, n=n, hits=hits,
                                  recall_pct=100 * hits / (n * k), qps=statistics.median(packet['qps']), packet_sha256=packet['digest'])
                    key = ds, method, str(k), str(L)
                    pub = point_csv[key]
                    insist(int(pub['hits']) == hits and int(pub['n']) == n, 'published point integer Recall')
                    for f in ('recall_pct', 'qps'):
                        insist(math.isclose(float(pub[f]), record[f], rel_tol=1e-12, abs_tol=1e-12), 'published point ' + f)
                    packets[method] = packet
                    point_records.append(record)
                    total_rounds += 3
                for method, spec in descriptors.items():
                    if spec['family'] == 'NSG':
                        continue
                    baseline = 'NSG' if spec['family'] == 'GT10' else spec['baseline']
                    old, new = packets[baseline], packets[method]
                    stats = pair_counts(old['hits'], new['hits'], k)
                    key = ds, method, str(k), str(L)
                    assert_int_fields(stats, pair_csv[key], 'same-L integer pair')
                    pair_records.append(dict(dataset=ds, method=method, reference_method=baseline, K=k, L=L, **stats))
                    bands = [('failure', 0, 0), ('success', 1, 1)] if k == 1 else [
                        ('0', 0, 0), ('1..10', 1, 10), ('11..50', 11, 50),
                        ('51..90', 51, 90), ('91..99', 91, 99), ('100', 100, 100)]
                    for band, lo, hi in bands:
                        indices = [i for i, s in enumerate(old['hits']) if lo <= len(s) <= hi]
                        sub = pair_counts([old['hits'][i] for i in indices], [new['hits'][i] for i in indices], k)
                        assert_int_fields(sub, strata_csv[key + (band,)], 'reference-defined stratum')
                        stratum_count += 1
                    if spec['family'] != 'POST':
                        continue
                    cascade = cascade_counts(truths, packets['NSG']['hits'], old['hits'], new['hits'], k)
                    published_cascade = cascade_csv[key]
                    insist(published_cascade['reference_method'] == baseline
                           and published_cascade['comparison'] == 'residual_vs_own_GT10', 'cascade reference identity')
                    assert_int_fields(cascade, published_cascade, 'independent failure cascade')
                    assert_ratio(cascade['of_these_residual_restored_members'], cascade['NSG_correct_GT10_lost_members'],
                                 published_cascade, 'GT10_lost_member_restore_rate', 'cascade rate')
                    cascade_records.append(dict(dataset=ds, method=method, reference_method=baseline, K=k, L=L, **cascade))
                    insist(old['arrays'][2].tobytes() == new['arrays'][2].tobytes()
                           and old['arrays'][3].tobytes() == new['arrays'][3].tobytes(), 'POST exact own-GT route/profile words')
                    support = models[spec['router']]
                    cap = 32 if '32' in method else 8
                    rows = support['tables'][cap]
                    coverage = dict(missing_members=0, missing_in_full_training_GT=0, missing_in_global_residual_source=0,
                                    missing_in_uncapped_routed_source=0, missing_in_selected_routed_table=0,
                                    rescued_members=stats['rescued_members'], damaged_members=stats['damaged_members'],
                                    net_members=stats['net_members'], actual_candidates_outside_GT=0, route_union_candidates=0)
                    frequencies = new_frequency_counts()
                    for i, (correct, prior, final, route) in enumerate(zip(truths, old['hits'], new['hits'], old['arrays'][2])):
                        row_ids = [support['slots'][int(h)] for h in route]
                        selected = set.union(*(rows[j] for j in row_ids))
                        missing = correct - prior
                        routed = {v for v in missing if any(v in support['hub_pools'][j] for j in row_ids)}
                        available = missing & selected
                        rescued = final - prior
                        insist(rescued <= available, 'all actual rescued GT in table union')
                        insist(new['output'][i] <= old['output'][i] | selected, 'POST cannot invent candidates')
                        coverage['missing_members'] += len(missing)
                        coverage['missing_in_full_training_GT'] += sum(v in support['frequency_maps']['training_query_count']
                                                                       for v in missing)
                        coverage['missing_in_global_residual_source'] += len(missing & support['global_pool'])
                        coverage['missing_in_uncapped_routed_source'] += len(routed)
                        coverage['missing_in_selected_routed_table'] += len(available)
                        coverage['actual_candidates_outside_GT'] += len(selected - old['output'][i])
                        coverage['route_union_candidates'] += len(selected)
                        accumulate_frequency_counts(frequencies, correct, prior, final, routed, selected, support)
                    a, b, c, d = [coverage[f] for f in ('missing_members', 'missing_in_global_residual_source',
                                                        'missing_in_uncapped_routed_source', 'missing_in_selected_routed_table')]
                    insist(a >= b >= c >= d >= coverage['rescued_members'], 'source-route-capacity-actual nesting')
                    coverage.update(unseen_by_residual_source=a-b, source_present_but_route_missed=b-c,
                                    routed_source_present_but_capacity_missed=c-d,
                                    candidate_present_but_not_rescued=d-coverage['rescued_members'])
                    assert_int_fields(coverage, coverage_csv[key], 'independent source/route/capacity decomposition')
                    coverage_records.append(dict(dataset=ds, method=method, K=k, L=L, **coverage))
                    for kind in ('residual_query_count', 'training_query_count'):
                        totals = Counter()
                        for band in FREQUENCY_LABELS:
                            row = frequencies[kind, band]
                            pub = frequency_csv[key + (kind, band)]
                            insist(pub['reference_method'] == baseline, 'frequency reference identity')
                            assert_int_fields(row, pub, 'independent TRAIN target-frequency bucket')
                            assert_ratio(row['rescued_members'], row['missing_members'], pub,
                                         'rescue_rate_on_missing', 'frequency rescue rate')
                            assert_ratio(row['damaged_members'], row['correct_members'], pub,
                                         'damage_rate_on_correct', 'frequency damage rate')
                            insist(row['missing_members'] >= row['missing_in_residual_source']
                                   >= row['missing_in_uncapped_routed_source'] >= row['missing_in_selected_table']
                                   >= row['rescued_members'] and row['correct_members'] >= row['damaged_members'],
                                   'frequency source-route-capacity nesting')
                            totals.update(row)
                            frequency_records.append(dict(dataset=ds, method=method, reference_method=baseline, K=k, L=L,
                                                          frequency_kind=kind, training_target_query_frequency=band, **row))
                        insist(totals['missing_members'] + totals['correct_members'] == n * k
                               and totals['missing_members'] == coverage['missing_members']
                               and totals['correct_members'] == stats['reference_correct_members']
                               and totals['missing_in_residual_source'] == coverage['missing_in_global_residual_source']
                               and totals['missing_in_uncapped_routed_source'] == coverage['missing_in_uncapped_routed_source']
                               and totals['missing_in_selected_table'] == coverage['missing_in_selected_routed_table']
                               and totals['rescued_members'] == stats['rescued_members']
                               and totals['damaged_members'] == stats['damaged_members'], 'frequency buckets partition all GT members')
                del packets
        print(json.dumps(dict(dataset=ds, status='INDEPENDENT_DATASET_PASS', points=len(points), elapsed_seconds=time.monotonic()-started)), flush=True)
    insist(len(point_records) == len(point_csv) == 645 and total_rounds == 1935, '645 points and1935 timings')
    insist(len(pair_records) == len(pair_csv) and len(coverage_records) == len(coverage_csv)
           and stratum_count == len(strata_csv) and len(cascade_records) == len(cascade_csv)
           and len(frequency_records) == len(frequency_csv) == 10 * len(coverage_records),
           'all published comparison/decomposition/frequency/cascade rows audited')
    reader.register(__file__)
    reader.finish()
    result = dict(status='PASS_INDEPENDENT_E183_INTEGER_RESULTS_AUDIT', points=645, formal_batches=1935,
                  same_L_pairs=len(pair_records), source_models=len(source_records), coverage_rows=len(coverage_records),
                  failure_strata=stratum_count, whole_train_source_reconstructed=True,
                  failure_cascade_rows=len(cascade_records), target_frequency_rows=len(frequency_records),
                  train_target_query_frequency_reconstructed=True,
                  main_analyzer_imported=False, integer_algorithm='Python exact sets and set differences per query',
                  packet_hash_algorithm='native shape + four retained arrays + two exact zero NDC layout buffers',
                  seconds=time.monotonic()-started, generated_unix=time.time(), source_training_audits=source_records,
                  point_results=point_records, paired_results=pair_records, source_coverage_results=coverage_records,
                  failure_cascade_results=cascade_records, target_frequency_results=frequency_records,
                  consumed_identities=reader.files, new_ANN=0, new_vector_distance_scores=0, new_timing_runs=0,
                  limits=['Native full scalar merge oracle was source-reviewed; not re-executed by this script.',
                          'Bootstrap confidence intervals and curve interpolation not independently recalculated.',
                          'Greedy actual-data selection sequence not recomputed; source membership, table binary/JSON and full token coverage verified.',
                          'Later timed rounds rely on native bit-parity and full packet hashes; only actual round0 raw retained.'])
    with output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=result['status'], output=str(output), points=645, seconds=result['seconds'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, default=ROOT / 'analysis/final_v1')
    parser.add_argument('--out', type=Path, default=ROOT / 'reviews/independent_results_audit.json')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest()))
        return
    insist(not args.out.exists(), 'preserve previous independent audit')
    audit(args.analysis.resolve(), args.out.resolve())


if __name__ == '__main__':
    main()
