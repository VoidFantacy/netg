"""Frozen old-result diagnosis: no query/base vectors, GT or native search."""
from itertools import combinations
from pathlib import Path
import hashlib
import json
import time

import numpy as np


ROOT = Path('/data/netg/ACSG')
OLD = ROOT / 'entry_method_exploration/20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1'
OUT = Path(__file__).resolve().parent
METHODS = ['Default3', 'DefaultRank1', 'TargetBank1']
POINTS = {'webvid2_5m_light_v1': [(1, 800), (1, 1000), (1, 1250), (100, 1120), (100, 1250), (100, 1400)],
          'yandex_t2i_official10M_ip_v1': [(1, 96), (1, 128), (1, 160), (100, 200), (100, 256), (100, 320)]}
READS = {}


def identity(path):
    path = Path(path)
    return {'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def consume(path):
    path = Path(path)
    before = identity(path)
    if str(path) in READS:
        assert before == READS[str(path)]
    else:
        READS[str(path)] = before
    return path


def read_json(path):
    return json.loads(consume(path).read_text())


def read_ints(path, dtype, shape):
    path = consume(path)
    expected = int(np.prod(shape)) * np.dtype(dtype).itemsize
    assert path.stat().st_size == expected, (str(path), expected)
    return np.fromfile(path, dtype=dtype).reshape(shape)


def count(mask):
    return int(np.count_nonzero(mask))


def write_new(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')


def main():
    started = time.perf_counter()
    protocol = consume(OUT / 'response_equivalence_protocol.md')
    script = consume(Path(__file__))
    config = read_json(OLD / 'config.locked.json')
    analysis = read_json(OLD / 'results/analysis.json')
    assert config['methods'] == METHODS
    result = {}
    total_rows = 0
    for dataset, frozen_points in POINTS.items():
        cfg = config['datasets'][dataset]
        n, base_n = cfg['n'], cfg['base_n']
        assert n == 4096 and cfg['methods'] == METHODS
        assert [(p['K'], p['L']) for p in cfg['points']] == frozen_points
        with np.load(consume(OLD / 'results' / dataset / 'score_arrays.npz'), allow_pickle=False) as archive:
            hits = archive['hits'].copy()
        assert hits.shape == (n, 6, 3) and np.issubdtype(hits.dtype, np.integer)
        dataset_rows = []
        for pi, (k, width) in enumerate(frozen_points):
            old_point = analysis['datasets'][dataset]['points'][f'k{k}_L{width}']['methods']
            outputs, graph_counts, route_counts = [], [], []
            for mi, method in enumerate(METHODS):
                loc = OLD / 'results' / dataset / f'k{k}_L{width}' / method
                ids = read_ints(loc / 'ids.i32', '<i4', (n, k))
                ordered = np.sort(ids, axis=1)
                assert ((ids >= 0) & (ids < base_n)).all()
                assert k == 1 or (ordered[:, 1:] > ordered[:, :-1]).all()
                h = hits[:, pi, mi]
                assert ((h >= 0) & (h <= k)).all()
                graph = read_ints(loc / 'graph_ndc.u64', '<u8', (n,))
                route = read_ints(loc / 'route_ndc.u64', '<u8', (n,))
                assert int(h.sum()) == old_point[method]['hits']
                assert abs(float(graph.mean()) - old_point[method]['graph_NDC']) < 1e-9
                assert abs(float(route.mean()) - old_point[method]['route_NDC']) < 1e-9
                outputs.append(ids)
                graph_counts.append(graph)
                route_counts.append(route)
            for left, right in combinations(range(3), 2):
                a, b = outputs[left], outputs[right]
                same_order = (a == b).all(axis=1)
                same_set = (np.sort(a, axis=1) == np.sort(b, axis=1)).all(axis=1)
                equal_hits = hits[:, pi, left] == hits[:, pi, right]
                assert equal_hits[same_set].all()
                replaced = np.fromiter((len(set(x.tolist()) - set(y.tolist())) for x, y in zip(a, b)), dtype=np.int32, count=n)
                reverse_replaced = np.fromiter((len(set(y.tolist()) - set(x.tolist())) for x, y in zip(a, b)), dtype=np.int32, count=n)
                assert np.array_equal(replaced, reverse_replaced)
                assert np.array_equal(replaced == 0, same_set)
                hit_delta = hits[:, pi, right].astype(np.int64) - hits[:, pi, left].astype(np.int64)
                assert (np.abs(hit_delta) <= replaced).all()
                same_graph = graph_counts[left] == graph_counts[right]
                total_left = graph_counts[left] + route_counts[left]
                total_right = graph_counts[right] + route_counts[right]
                same_total = total_left == total_right
                row = {'K': k, 'L': width, 'left': METHODS[left], 'right': METHODS[right], 'n': n,
                       'same_ordered_return_n': count(same_order),
                       'same_return_set_n': count(same_set), 'same_return_set_pct': float(same_set.mean() * 100),
                       'same_saved_hit_count_n': count(equal_hits),
                       'same_hit_count_but_different_return_set_n': count(equal_hits & ~same_set),
                       'same_return_set_same_graphNDC_n': count(same_set & same_graph),
                       'same_return_set_different_graphNDC_n': count(same_set & ~same_graph),
                       'same_return_set_same_totalNDC_n': count(same_set & same_total),
                       'same_return_set_different_totalNDC_n': count(same_set & ~same_total),
                       'replaced_output_members': {'mean': float(replaced.mean()), 'max': int(replaced.max()),
                                                   'p50': float(np.quantile(replaced, .5)), 'p90': float(np.quantile(replaced, .9)),
                                                   'p99': float(np.quantile(replaced, .99))},
                       'mean_symmetric_difference_recall_bound_pp': float(replaced.mean() * 100 / k),
                       'old_right_minus_left_recall_pp': float(hit_delta.mean() * 100 / k),
                       'same_set_implies_same_saved_hits': True,
                       'saved_hit_difference_within_symmetric_difference_bound': True}
                dataset_rows.append(row)
                total_rows += 1
        result[dataset] = dataset_rows
    assert total_rows == 36
    for path, before in READS.items():
        assert identity(path) == before, ('source changed', path)
    elapsed = time.perf_counter() - started
    write_new(OUT / 'response_class_input_identity.json',
              {'input_identity_before_after_equal': True, 'files': READS})
    write_new(OUT / 'response_class_check.json',
              {'status': 'FROZEN_OLD_RETURN_RESPONSE_CLASS_DIAGNOSTIC_COMPLETE',
               'protocol_sha256': READS[str(protocol)]['sha256'],
               'script_sha256': READS[str(script)]['sha256'],
               'datasets': result, 'pair_point_units': total_rows,
               'input_files': len(READS), 'seconds': elapsed,
               'new_vector_scores': 0, 'new_ANN_NSG_GT_calls': 0,
               'query_base_GT_vectors_opened': False, 'new_models_graphs': 0,
               'interpretation': 'Same terminal K-ID sets; not live-pool identity/coalescence, cross-query labels or wall equivalence.'})
    print(json.dumps({'status': 'FROZEN_OLD_RETURN_RESPONSE_CLASS_DIAGNOSTIC_COMPLETE',
                      'pair_point_units': total_rows, 'input_files': len(READS),
                      'seconds': elapsed, 'new_vector_scores': 0, 'new_ANN_NSG_GT_calls': 0}))


if __name__ == '__main__':
    main()
