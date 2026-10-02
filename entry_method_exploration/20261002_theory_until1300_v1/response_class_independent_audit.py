"""Independent stdlib-only read of old E166 return IDs/hits/NDC.

No query/base/GT vectors, scoring, native code, graph or training is opened.
The main script uses NumPy; this audit uses struct/zipfile/Counter/set/Fraction.
"""
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time
import zipfile


OUT = Path(__file__).resolve().parent
OLD = OUT.parent / '20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1'
METHODS = ('Default3', 'DefaultRank1', 'TargetBank1')
POINTS = {
    'webvid2_5m_light_v1': ((1, 800), (1, 1000), (1, 1250), (100, 1120), (100, 1250), (100, 1400)),
    'yandex_t2i_official10M_ip_v1': ((1, 96), (1, 128), (1, 160), (100, 200), (100, 256), (100, 320)),
}
PAIRS = ((0, 1), (0, 2), (1, 2))


def identity(path):
    p = Path(path)
    return {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def read_json(path):
    return json.loads(Path(path).read_text())


def integer_stream(path, code, n):
    raw = Path(path).read_bytes()
    unit = struct.calcsize('<' + code)
    assert len(raw) == n * unit, (str(path), len(raw), n * unit)
    return tuple(value[0] for value in struct.iter_unpack('<' + code, raw))


def old_saved_hits(path, n):
    # Open only the saved hits member; no other NPZ arrays are extracted/read.
    with zipfile.ZipFile(path) as archive:
        raw = archive.read('hits.npy')
    assert raw[:6] == b'\x93NUMPY'
    version = tuple(raw[6:8])
    if version == (1, 0):
        header_start, length = 10, struct.unpack('<H', raw[8:10])[0]
    elif version in ((2, 0), (3, 0)):
        header_start, length = 12, struct.unpack('<I', raw[8:12])[0]
    else:
        raise ValueError('Unsupported saved NPY version')
    header = ast.literal_eval(raw[header_start:header_start + length].decode('latin1'))
    assert header == {'descr': '<i4', 'fortran_order': False, 'shape': (n, 6, 3)}, header
    data = raw[header_start + length:]
    assert len(data) == n * 6 * 3 * 4
    return tuple(value[0] for value in struct.iter_unpack('<i', data))


def percentile(histogram, n, probability):
    # Rational interpolation; compared with main NumPy linear quantile at 1e-9.
    at = Fraction(n - 1) * probability
    lower = at.numerator // at.denominator
    upper = math.ceil(at)
    positions, cumulative = {}, 0
    for value, count in sorted(histogram.items()):
        for position in (lower, upper):
            if cumulative <= position < cumulative + count:
                positions[position] = value
        cumulative += count
    return float(positions[lower] + (at - lower) * (positions[upper] - positions[lower]))


def compare(actual, expected, prefix=''):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (prefix, set(actual) ^ set(expected))
        return sum(compare(actual[key], expected[key], prefix + '/' + key) for key in expected)
    if isinstance(expected, float):
        assert abs(actual - expected) <= 1e-9, (prefix, actual, expected)
    else:
        assert actual == expected, (prefix, actual, expected)
    return 1


def main():
    started = time.perf_counter()
    os.sched_setaffinity(0, {0})
    assert os.sched_getaffinity(0) == {0}
    status = Path('/proc/self/status').read_text()
    threads = int(next(line.split()[1] for line in status.splitlines() if line.startswith('Threads:')))
    assert threads == 1
    manifest_path = OUT / 'response_class_input_identity.json'
    main_result_path = OUT / 'response_class_check.json'
    control_paths = (manifest_path, main_result_path, Path(__file__).resolve())
    controls_before = {str(p): identity(p) for p in control_paths}
    manifest = read_json(manifest_path)
    expected_identity = manifest['files']
    assert manifest['input_identity_before_after_equal'] is True
    assert len(expected_identity) == 114
    for path, expected in expected_identity.items():
        assert identity(path) == expected, ('main identity differs before read', path)
    root_result = read_json(main_result_path)
    config = read_json(OLD / 'config.locked.json')
    old_analysis = read_json(OLD / 'results/analysis.json')
    assert config['methods'] == list(METHODS)
    fields_compared, pair_units, query_pairs = 0, 0, 0
    totals = Counter()
    focused = []
    for dataset, frozen_points in POINTS.items():
        cfg = config['datasets'][dataset]
        n, base_n = cfg['n'], cfg['base_n']
        assert n == 4096 and cfg['methods'] == list(METHODS)
        assert tuple((p['K'], p['L']) for p in cfg['points']) == frozen_points
        hits = old_saved_hits(OLD / 'results' / dataset / 'score_arrays.npz', n)
        expected_rows = root_result['datasets'][dataset]
        assert len(expected_rows) == 18
        for pi, (k, width) in enumerate(frozen_points):
            outputs, graph_counts, route_counts, point_hits = [], [], [], []
            for mi, method in enumerate(METHODS):
                loc = OLD / 'results' / dataset / f'k{k}_L{width}' / method
                ids = integer_stream(loc / 'ids.i32', 'i', n * k)
                rows = tuple(ids[q * k:(q + 1) * k] for q in range(n))
                assert all(len(set(row)) == k and all(0 <= item < base_n for item in row) for row in rows)
                graph = integer_stream(loc / 'graph_ndc.u64', 'Q', n)
                route = integer_stream(loc / 'route_ndc.u64', 'Q', n)
                h = tuple(hits[(q * 6 + pi) * 3 + mi] for q in range(n))
                assert all(0 <= item <= k for item in h)
                measured = old_analysis['datasets'][dataset]['points'][f'k{k}_L{width}']['methods'][method]
                assert sum(h) == measured['hits']
                assert abs(float(Fraction(sum(graph), n)) - measured['graph_NDC']) < 1e-9
                assert abs(float(Fraction(sum(route), n)) - measured['route_NDC']) < 1e-9
                outputs.append(rows)
                graph_counts.append(graph)
                route_counts.append(route)
                point_hits.append(h)
            for pair_index, (left, right) in enumerate(PAIRS):
                counts, histogram = Counter(), Counter()
                sum_delta = 0
                for q in range(n):
                    a, b = outputs[left][q], outputs[right][q]
                    aset, bset = set(a), set(b)
                    same_order, same_set = a == b, aset == bset
                    equal_hits = point_hits[left][q] == point_hits[right][q]
                    replaced = len(aset - bset)
                    assert replaced == len(bset - aset)
                    assert (replaced == 0) == same_set
                    assert not same_order or same_set
                    assert not same_set or equal_hits
                    delta = point_hits[right][q] - point_hits[left][q]
                    assert abs(delta) <= replaced
                    sum_delta += delta
                    histogram[replaced] += 1
                    same_graph = graph_counts[left][q] == graph_counts[right][q]
                    same_total = graph_counts[left][q] + route_counts[left][q] == graph_counts[right][q] + route_counts[right][q]
                    counts['same_ordered_return_n'] += same_order
                    counts['same_return_set_n'] += same_set
                    counts['same_saved_hit_count_n'] += equal_hits
                    counts['same_hit_count_but_different_return_set_n'] += equal_hits and not same_set
                    counts['same_return_set_same_graphNDC_n'] += same_set and same_graph
                    counts['same_return_set_different_graphNDC_n'] += same_set and not same_graph
                    counts['same_return_set_same_totalNDC_n'] += same_set and same_total
                    counts['same_return_set_different_totalNDC_n'] += same_set and not same_total
                mean_replaced = Fraction(sum(value * count for value, count in histogram.items()), n)
                row = {'K': k, 'L': width, 'left': METHODS[left], 'right': METHODS[right], 'n': n,
                       **dict(counts),
                       'same_return_set_pct': float(Fraction(counts['same_return_set_n'] * 100, n)),
                       'replaced_output_members': {'mean': float(mean_replaced), 'max': max(histogram),
                                                  'p50': percentile(histogram, n, Fraction(1, 2)),
                                                  'p90': percentile(histogram, n, Fraction(9, 10)),
                                                  'p99': percentile(histogram, n, Fraction(99, 100))},
                       'mean_symmetric_difference_recall_bound_pp': float(mean_replaced * 100 / k),
                       'old_right_minus_left_recall_pp': float(Fraction(sum_delta * 100, n * k)),
                       'same_set_implies_same_saved_hits': True,
                       'saved_hit_difference_within_symmetric_difference_bound': True}
                fields_compared += compare(row, expected_rows[pi * 3 + pair_index], dataset)
                pair_units += 1
                query_pairs += n
                totals.update(counts)
                if left == 0 and right == 2 and (dataset, k, width) in (
                        ('webvid2_5m_light_v1', 1, 1000), ('yandex_t2i_official10M_ip_v1', 100, 256)):
                    focused.append({'dataset': dataset, **row})
    assert pair_units == 36 and root_result['pair_point_units'] == 36 and root_result['input_files'] == 114
    for path, before in expected_identity.items():
        assert identity(path) == before, ('main input changed after read', path)
    for path, before in controls_before.items():
        assert identity(path) == before, ('audit control changed after read', path)
    result = {
        'status': 'PASS_INDEPENDENT_STDLIB_OLD_RESPONSE_CLASS_AUDIT',
        'implementation': 'struct/zipfile/ast/Counter/set/Fraction; no NumPy or main-script import',
        'cpu_affinity': [0], 'actual_process_threads': threads,
        'main_pair_point_units': pair_units, 'query_pair_checks': query_pairs,
        'all_main_fields_compared': fields_compared, 'numeric_tolerance': 1e-9,
        'main_input_files_verified_before_after': len(expected_identity),
        'main_identity_manifest_reused_and_all_hashes_verified': True,
        'main_and_audit_control_identities_before_after_equal': True,
        'control_identities': controls_before,
        'aggregate_pair_query_counts': dict(totals), 'focused_old_cells': focused,
        'new_vector_scores': 0, 'new_ANN_NSG_GT_calls': 0,
        'query_base_GT_vectors_opened': False, 'new_models_graphs': 0,
        'seconds_for_readonly_audit_only': time.perf_counter() - started,
        'interpretation': 'Saved terminal K-ID equivalence only; not live-pool convergence, trace, cross-query or wall equivalence.'}
    target = OUT / 'response_class_independent_audit.json'
    with target.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps({key: result[key] for key in (
        'status', 'main_pair_point_units', 'query_pair_checks', 'all_main_fields_compared',
        'main_input_files_verified_before_after', 'new_vector_scores', 'new_ANN_NSG_GT_calls')}))


if __name__ == '__main__':
    main()
