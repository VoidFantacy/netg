#!/usr/bin/env python3
"""Independent tiny arrays and guarded generated GT-prefix tests only."""
import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert digest(args.source) == args.source_sha
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('target_independent_subject', args.source)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    checks = []

    def check(name, ok):
        assert ok, name
        checks.append(name)

    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError, IndexError):
            checks.append(name)
        else:
            raise AssertionError('Expected rejection: ' + name)

    # Counter/sorted Python oracle does not reuse the implementation's matrix
    # counting or NumPy sorting. The cases cover ties and IDs above 63.
    rng = np.random.default_rng(2026090711)
    labels = rng.integers(0, 256, size=1024, dtype=np.uint16)
    gt = np.stack([rng.choice(600, size=10, replace=False) for _ in range(24)]).astype(np.int32)
    seen_nodes = np.arange(1024) % 3 == 0
    seen = seen_nodes[gt]
    metrics = d.oracle_metrics(labels, gt, seen)
    for q in range(len(gt)):
        leaf_counts = Counter(int(labels[u]) for u in gt[q])
        ordered = sorted(range(256), key=lambda r: (-leaf_counts[r], r))[:4]
        chosen = [i for i, u in enumerate(gt[q]) if int(labels[u]) in ordered]
        assert metrics['top4'][q].tolist() == ordered
        assert metrics['D'][q] == len(leaf_counts)
        assert metrics['covered'][q] == len(chosen)
        assert metrics['covered_seen'][q] == sum(bool(seen[q, i]) for i in chosen)
        assert metrics['covered_unseen'][q] == sum(not bool(seen[q, i]) for i in chosen)
        assert np.allclose(metrics['conditional_weights'][q],
                           [leaf_counts[r] / len(chosen) for r in ordered], rtol=0, atol=1e-15)
    check('24-row independent Counter oracle matches D/top4/coverage/subgroup contributions', True)

    trap_labels = np.array([200, 200, 100, 100, 0, 0, 1, 1, 2, 3], dtype=np.uint16)
    trap_gt = np.arange(10, dtype=np.int32)[None, :]
    trap_seen = np.array([[True] * 4 + [False] * 6])
    trap = d.oracle_metrics(trap_labels, trap_gt, trap_seen)
    check('Full-GT top4 is shared by support groups and does not independently rescue unseen leaves',
          trap['top4'].tolist() == [[0, 1, 100, 200]] and trap['D'].tolist() == [6] and
          trap['covered'].tolist() == [8] and trap['covered_seen'].tolist() == [4] and
          trap['covered_unseen'].tolist() == [4])
    one = d.oracle_metrics(np.full(10, 255, dtype=np.uint16), trap_gt, trap_seen)
    check('One occupied high-ID leaf retains globally ordered zero-mass ties',
          one['top4'].tolist() == [[255, 0, 1, 2]] and
          one['conditional_weights'].tolist() == [[1., 0., 0., 0.]])
    sm = d.metric_summary(trap, np.array([4]), np.array([True]))
    check('Absolute contributions and conditional slot ratios have different denominators',
          sm['mean_M4_absolute'] == .8 and sm['mean_M4_seen_contribution'] == .4 and
          sm['mean_M4_unseen_contribution'] == .4 and
          sm['seen_conditional_target_coverage'] == 1 and
          sm['unseen_conditional_target_coverage'] == 4 / 6)
    empty = d.metric_summary(trap, np.array([4]), np.array([False]))
    check('Empty groups are null and all exact D and coverage bins remain',
          empty['mean_M4_absolute'] is None and empty['unseen_conditional_target_coverage'] is None and
          len(empty['distinct_leaf_histogram']) == 10 and len(empty['covered_target_count_histogram']) == 11 and
          all(x['queries'] == 0 for x in empty['distinct_leaf_histogram']))

    # Fully valid repeated fit rows: each target occurs once in each fit row.
    initial = np.arange(20, dtype=np.uint16)
    first = initial.copy(); first[10] = 26
    final1 = initial.copy(); final1[0] = 1
    movement_labels = {'common_initial': initial, 'lambda0_pass1': first,
                       'lambda0_final': initial.copy(), 'lambda1_pass1': initial.copy(),
                       'lambda1_final': final1}
    frequency = np.array([2] * 10 + [0] * 10, dtype=np.uint32)
    pilot = np.array([[0, 1, 2, 3, 4, 10, 11, 12, 13, 14],
                      [5, 6, 7, 8, 9, 10, 15, 16, 17, 18]], dtype=np.int32)
    d.validate_gt10(pilot, 2, 20)
    with patch.object(d, 'NFIT', 2):
        pop = d.population_summary(movement_labels, frequency, pilot)
    any0 = pop['movements']['lambda0_any_pass_leaf_changed']
    check('Transient movement return counted in any-pass but absent from final difference',
          pop['movements']['lambda0_final_leaf_changed_from_initial']['unique_nodes']['all']['changed'] == 0 and
          any0['unique_nodes']['unseen']['changed'] == 1 and
          pop['movements']['lambda0_any_pass_coarse_changed']['unique_nodes']['unseen']['changed'] == 1)
    check('Repeated unseen target across queries uses separate node and slot denominators',
          any0['unique_nodes']['unseen'] == {'changed': 1, 'denominator': 10, 'rate': .1} and
          any0['pilot_target_slots']['unseen'] == {'changed': 2, 'denominator': 10, 'rate': .2})

    # A guarded generated ivecs file proves one exact prefix read and catches a
    # rank99 change despite metrics using ranks0..9 only.
    nq, nfit = 3, 2
    values = np.tile(np.arange(100, dtype='<i4'), (nq + nfit, 1))
    raw = np.column_stack((np.full(nq + nfit, 100, dtype='<i4'), values)).astype('<i4').tobytes()
    parent = args.output / 'generated_parent.ivecs'; parent.write_bytes(raw)
    audit = {'files': {'drl_train_gt_path': {'path': str(parent),
                'header': {'n': nq + nfit, 'd': 100, 'bytes': len(raw)}}},
             'pilot': {'row_range': [0, nq], 'n': nq,
                       'gt_values_sha256': hashlib.sha256(values[:nq].tobytes()).hexdigest()}}
    original_open = Path.open
    reads = []
    payload = raw

    class Guard(io.BytesIO):
        def read(self, size=-1):
            assert size == nq * 404 and self.tell() == 0, 'Unbounded or repeated parent read'
            reads.append(size)
            return super().read(size)

        def seek(self, *args):
            raise AssertionError('Unexpected parent seek')

    def guarded_open(path, *a, **kw):
        if path.resolve() == parent.resolve():
            return Guard(payload)
        return original_open(path, *a, **kw)

    with patch.object(d, 'NQ', nq), patch.object(d, 'NFIT', nfit), patch.object(Path, 'open', guarded_open):
        loaded, evidence = d.read_pilot_prefix(audit, nq, 200)
        check('Pilot loader makes one bounded first-three-record read without suffix or parent hash',
              reads == [nq * 404] and loaded.tolist() == [list(range(10))] * nq and
              evidence['fit_suffix_read'] is False and evidence['parent_file_rehashed'] is False)
        changed = bytearray(raw); changed[400:404] = (123).to_bytes(4, 'little'); payload = bytes(changed)
        reject('Rank99 tamper detected by full top100 values SHA', lambda: d.read_pilot_prefix(audit, nq, 200))
        changed = bytearray(raw); changed[404:408] = (99).to_bytes(4, 'little'); payload = bytes(changed)
        reject('Second-record header tamper detected', lambda: d.read_pilot_prefix(audit, nq, 200))
        payload = raw[:100]
        reject('Short physical prefix rejected', lambda: d.read_pilot_prefix(audit, nq, 200))
    reject('Duplicate GT IDs rejected', lambda: d.validate_gt10(np.zeros((1, 10), dtype=np.int32), 1, 200))
    reject('Negative GT ID rejected', lambda: d.validate_gt10(np.arange(-1, 9, dtype=np.int32)[None], 1, 200))
    reject('Unsigned GT contract rejected', lambda: d.validate_gt10(np.arange(10, dtype=np.uint32)[None], 1, 200))

    # Reconstruct hits from explicit IDs and use independent seen-slot masks.
    small_gt = gt[:3]
    small_seen = seen[:3]
    small_metrics = d.oracle_metrics(labels, small_gt, small_seen)
    rows = []
    for q, hit_count in enumerate([0, 5, 10]):
        ids = [int(u) for u in small_gt[q, :hit_count]] + list(range(800, 810 - hit_count))
        rows.append({'query_id': q, 'result_ids': ids, 'recall': hit_count / 10,
                     'regions': small_metrics['top4'][q].tolist(),
                     'weights': small_metrics['conditional_weights'][q].tolist(),
                     'fast_anchor_id': 900, 'shared_seed': 901, 'actual_entry_count': 14,
                     'entry_ids': [900] + list(range(910, 922)),
                     'routing_ndc': 3, 'graph_ndc': 100, 'total_ndc': 103,
                     'routing_mac': 6, 'graph_mac': 200, 'total_mac': 206,
                     'expanded': 20, 'rejected': 70, 'evicted_unexpanded': 10})
    batch = {'method': 'oracle_probability', 'round': 0, 'search_L': 64,
             'per_query': rows, 'mean_recall': .5}
    parsed, routes = d.parse_oracle_batch(batch, small_gt, small_seen, small_metrics, 1024)
    expected_seen = [sum(bool(x) for x in small_seen[q, :h]) for q, h in enumerate([0, 5, 10])]
    check('Saved result intersections reconstruct exact full and support-specific hits',
          parsed['hits'].tolist() == [0, 5, 10] and parsed['hits_seen'].tolist() == expected_seen and
          np.array_equal(parsed['hits_seen'] + parsed['hits_unseen'], parsed['hits']))
    for field, value in [('regions', [255, 1, 2, 3]), ('weights', [.1, .2, .3, .4]),
                         ('recall', .7), ('total_ndc', 111), ('expanded', -1), ('query_id', 8)]:
        bad = copy.deepcopy(batch); bad['per_query'][0][field] = value
        reject('Saved oracle integrity rejects altered ' + field,
               lambda bad=bad: d.parse_oracle_batch(bad, small_gt, small_seen, small_metrics, 1024))

    candidate = {k: v.copy() for k, v in parsed.items()}
    candidate['hits'] = np.array([1, 4, 10], dtype=np.int16)
    candidate['hits_seen'][0] += 0
    candidate['hits_unseen'][0] += 1
    # Remove one of q1's actual hits from the relevant support group.
    group = 'hits_seen' if small_seen[1, 0] else 'hits_unseen'
    candidate[group][1] -= 1
    candidate['graph_ndc'] += np.array([1, 2, 3])
    changes = d.search_delta(candidate, parsed, small_seen.sum(axis=1), np.ones(3, dtype=bool))
    check('Paired signs, candidate-reference orientation and additive support contributions',
          changes['query_improved'] == changes['query_harmed'] == changes['query_equal'] == 1 and
          changes['recall_delta_pp'] == 0 and
          abs(changes['seen_recall_contribution_delta_pp'] + changes['unseen_recall_contribution_delta_pp']) < 1e-12 and
          changes['mean_counter_deltas']['graph_ndc'] == 2)
    check('All ten fixed comparisons are explicit and original eight retained',
          len(d.CONTRASTS) == len({x[0] for x in d.CONTRASTS}) == 10 and
          d.CONTRASTS[-2:] == (
              ('structure_unified_under_frequency3', 'lambda1_frequency3', 'oracle_unified', 'lambda0_frequency3', 'oracle_unified'),
              ('structure_unified_under_greedy3', 'lambda1_greedy3', 'oracle_unified', 'lambda0_greedy3', 'oracle_unified')))
    check('Frozen subject source stable', digest(args.source) == args.source_sha)
    report = {'status': 'PASS', 'source': {'path': str(args.source), 'sha256': args.source_sha},
              'reviewer_script_sha256': digest(__file__), 'checks': checks, 'check_count': len(checks),
              'actual_data_read': False, 'ANN_calls': 0, 'new_confidence_intervals': False,
              'fixture_scope': 'Independent Python-Counter oracle, movement/support denominators, guarded generated physical prefix, GT-derived result hits and paired counters.'}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'check_count': len(checks), 'report': str(args.output / 'report.json')}))


if __name__ == '__main__':
    main()
