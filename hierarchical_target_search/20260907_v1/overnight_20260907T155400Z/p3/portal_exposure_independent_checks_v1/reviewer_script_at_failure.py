#!/usr/bin/env python3
"""Independent, generated small fixtures only; never loads production rows."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--source', type=Path, required=True)
    cli.add_argument('--source-sha', required=True)
    cli.add_argument('--output', type=Path, required=True)
    args = cli.parse_args()
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest(args.source) == args.source_sha
    args.output.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location('portal_independent_subject', args.source)
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    passed = []

    def check(name, condition):
        assert condition, name
        passed.append(name)

    def rejects(name, callback):
        try:
            callback()
        except (ValueError, KeyError, IndexError):
            passed.append(name)
        else:
            raise AssertionError('Expected integrity rejection: ' + name)

    # These rows have an explicitly known synthetic GT. Recall is computed
    # independently from IDs, not edited independently of the returned set.
    gt = set([0, 1, 2, 3, 4, 20, 21, 22, 23, 24])
    frequency = np.arange(100, 868, dtype=np.int32).reshape(256, 3)
    greedy = frequency.copy()
    greedy[4] = greedy[4][::-1]
    for q in (2, 3, 4):
        greedy[q * 4, 0] = 2000 + q
    proxy = [{'eligible_target_support': 10, 'greedy_minus_frequency_hits': 0}
             for _ in range(256)]
    patterns = [([2, -3, 1, 0], [10, 20, 5, 8]),
                ([-1, 0, 0, 0], [10, 10, 10, 10]),
                ([1, 0, 0, 0], [10, 10, 10, 10]),
                ([1, 0, 0, 0], [10, 10, 10, 0]),
                ([-1, 0, 0, 0], [10, 10, 10, 0]),
                ([0, 0, 0, 0], [10, 10, 10, 10])]
    for q, (deltas, supports) in enumerate(patterns):
        for j, (delta, support) in enumerate(zip(deltas, supports)):
            proxy[q * 4 + j] = {'eligible_target_support': support,
                                'greedy_minus_frequency_hits': delta}

    def make_row(q, portals):
        regions = list(range(q * 4, q * 4 + 4))
        return {'query_id': q, 'shared_seed': 4000, 'fast_anchor_id': 4001,
                'actual_entry_count': 14,
                'entry_ids': [4001] + [int(x) for r in regions for x in portals[r]],
                'regions': regions,
                'weights': [.4, .3, .3, 0.] if q == 4 else [.4, .3, .2, .1],
                'result_ids': list(range(10)), 'recall': .5,
                'routing_ndc': 3, 'graph_ndc': 100, 'total_ndc': 103,
                'routing_mac': 6, 'graph_mac': 200, 'total_mac': 206,
                'expanded': 20, 'rejected': 70, 'evicted_unexpanded': 10}

    reference = [make_row(q, frequency) for q in range(6)]
    candidate = [make_row(q, greedy) for q in range(6)]
    candidate[1]['result_ids'][0:2] = [1, 0]
    candidate[2]['result_ids'][-1] = 31
    candidate[3]['result_ids'][-1] = 20
    candidate[4]['result_ids'][4] = 30
    for q, graph_delta in [(2, 3), (3, 4), (4, -5)]:
        candidate[q]['graph_ndc'] += graph_delta
        candidate[q]['total_ndc'] += graph_delta
        candidate[q]['graph_mac'] += 2 * graph_delta
        candidate[q]['total_mac'] += 2 * graph_delta
    candidate[3]['expanded'] += 2
    candidate[4]['expanded'] -= 1
    for row in reference + candidate:
        row['recall'] = len(set(row['result_ids']) & gt) / 10

    p3, p2 = subject.helpers()
    for rows, portals in [(reference, frequency), (candidate, greedy)]:
        for row in rows:
            p3.check_route(row, 'oracle_probability', portals, 5000, 4000)
    check('Independent six-query fixture has valid oracle route shapes and GT-derived Recall',
          [r['recall'] for r in candidate] == [.5, .5, .5, .6, .4, .5])

    paired = subject.pair_rows(reference, candidate, proxy)
    check('Three actual entry classes include shared seed first',
          [r['route_class'] for r in paired] ==
          [subject.ROUTE_CLASSES[i] for i in [0, 1, 2, 2, 2, 0]] and
          subject.actual_order(reference[0])[0] == 4000)
    check('Same returned set, changed order, changed set and equal Recall remain distinct',
          [r['result_set_equal'] for r in paired] == [True, True, False, False, False, True] and
          [r['result_order_equal'] for r in paired] == [True, False, False, False, False, True] and
          [r['delta_recall_pp'] for r in paired] == [0, 0, 0, 10, -10, 0])
    check('Zero raw sum and positive weighted score are independently reported',
          paired[0]['sum_proxy_delta_sign'] == 'zero' and
          paired[0]['weighted_proxy_score_sign'] == 'positive' and
          abs(paired[0]['weighted_proxy_score'] - .075) < 1e-15)
    check('Positive-weight unsupported leaf is null without renormalization',
          paired[3]['weighted_proxy_score'] is None and
          paired[3]['weighted_proxy_score_sign'] == 'undefined' and
          paired[3]['missing_support_weight'] == .1)
    check('Zero-weight unsupported leaf does not erase supported score',
          paired[4]['weighted_proxy_score'] == -.04 and
          paired[4]['missing_support_weight'] == 0 and
          paired[4]['leaf_proxy_ratios'][3] is None)

    summary = subject.summarize_cell(paired)
    overall = summary['overall']
    check('Correct paired signs and means with complete counts',
          overall['query_count'] == 6 and overall['recall_wins'] == 1 and
          overall['recall_losses'] == 1 and overall['recall_equal'] == 4 and
          overall['mean_delta_recall_pp'] == 0 and
          abs(overall['mean_graph_ndc_delta'] - 1 / 3) < 1e-15 and
          abs(overall['mean_expanded_delta'] - 1 / 6) < 1e-15)
    check('Result equality cannot be inferred from equal Recall',
          overall['equal_recall_but_changed_result_order'] == 2 and
          overall['equal_recall_but_changed_result_set'] == 1)
    check('Every fixed grouping retains empty bins and exhausts the six queries',
          [len(summary[k]) for k in ['by_route_class', 'by_sum_proxy_delta_sign',
                                    'by_weighted_proxy_score_sign',
                                    'by_route_and_sum_delta_sign',
                                    'by_route_and_weighted_score_sign']] == [3, 3, 4, 9, 12] and
          all(sum(g['query_count'] for g in v) == 6 for k, v in summary.items()
              if isinstance(v, list)) and
          any(g['query_count'] == 0 and g['mean_delta_recall_pp'] is None
              for g in summary['by_route_and_sum_delta_sign']))

    for field, value in [('result_ids', [1, 0] + list(range(2, 10))),
                         ('recall', .6)] + [(f, 999) for f in subject.METRICS]:
        bad = copy.deepcopy(candidate)
        bad[0][field] = value
        rejects('Identical full route rejects changed ' + field,
                lambda bad=bad: subject.pair_rows(reference, bad, proxy))
    bad = copy.deepcopy(candidate)
    bad[1]['recall'] = .6
    rejects('Same returned set with a different route still rejects changed Recall',
            lambda: subject.pair_rows(reference, bad, proxy))
    for field, value in [('regions', [255, 1, 2, 3]), ('weights', [.3, .4, .2, .1]),
                         ('shared_seed', 4999), ('fast_anchor_id', 4998),
                         ('actual_entry_count', 13)]:
        bad = copy.deepcopy(candidate)
        bad[0][field] = value
        rejects('Hidden full-route field cannot drift: ' + field,
                lambda bad=bad: subject.pair_rows(reference, bad, proxy))
    bad = copy.deepcopy(candidate)
    bad[0]['query_id'] = 5
    rejects('Paired query order mismatch', lambda: subject.pair_rows(reference, bad, proxy))
    rejects('Paired query length mismatch', lambda: subject.pair_rows(reference, candidate[:-1], proxy))

    for row in paired:
        row.update(structure_lambda=0, search_L=64)
    saved = subject.save_rows(args.output / 'independent.per_query.npz', paired)
    with np.load(saved['file']['path'], allow_pickle=False) as arrays:
        check('Compact arrays preserve null and integer exact deltas',
              arrays['delta_recall_pp'].tolist() == [0, 0, 0, 10, -10, 0] and
              np.isnan(arrays['weighted_proxy_score'][3]) and
              np.isnan(arrays['leaf_proxy_ratios'][4, 3]) and
              not np.isnan(arrays['weighted_proxy_score'][4]))
    generated = args.output / 'generated.json'
    generated.write_text('{"generated_only":true}\n')
    desc = subject.binding(generated)
    check('Generated saved-file exact hash read',
          subject.read_bound(desc, root=args.output) == {'generated_only': True})
    rejects('Generated saved-file digest tamper',
            lambda: subject.read_bound({**desc, 'sha256': '0' * 64}, root=args.output))
    rejects('Generated saved-file boundary escape',
            lambda: subject.read_bound(desc, root=args.output / 'closed'))
    check('Frozen source stable after synthetic execution', digest(args.source) == args.source_sha)
    result = {'status': 'PASS', 'source': {'path': str(args.source), 'sha256': args.source_sha},
              'reviewer_script_sha256': digest(Path(__file__)), 'checks': passed,
              'check_count': len(passed), 'queries': 6,
              'source_fixture_is_independent_of_implementation_selftest': True,
              'actual_data_read': False, 'ANN_calls': 0, 'new_confidence_intervals': False,
              'per_query': saved}
    (args.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'check_count': len(passed),
                      'report': str(args.output / 'report.json')}))


if __name__ == '__main__':
    main()
