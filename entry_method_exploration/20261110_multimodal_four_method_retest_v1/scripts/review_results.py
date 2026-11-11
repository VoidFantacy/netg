"""Derive report evidence from the audited full matrix; no new searches."""
from pathlib import Path
import csv
import gzip
import hashlib
import json
import numpy as np
from analyze import gt_for

RUN = Path(__file__).resolve().parents[1]
OUT = RUN / 'analysis/final_v1'


def read_table(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))


def array(point, name, dtype, shape):
    p = Path(point['point_dir']) / 'raw' / name
    with gzip.open(str(p) + '.gz', 'rb') as f:
        return np.frombuffer(f.read(), dtype).reshape(shape)


def main():
    assert json.loads((OUT / 'independent_audit.json').read_text())['status'] == 'PASS_INDEPENDENT_STDLIB_ALL_POINTS'
    points = read_table('points.csv')
    pairs = read_table('paired.csv')
    frontier = read_table('frontier.csv')
    targets = read_table('targets.csv')
    losses = []
    for pair in pairs:
        if pair['method'] != 'GT10+Residual' or not int(pair['lost_members']):
            continue
        match = [p for p in points if all(p[k] == pair[k] for k in ['dataset', 'K', 'L'])]
        a = next(p for p in match if p['method'] == 'GT10')
        b = next(p for p in match if p['method'] == 'GT10+Residual')
        n, k = int(a['n']), int(a['K'])
        ia = array(a, 'ids.i32', '<i4', (n, k))
        ib = array(b, 'ids.i32', '<i4', (n, k))
        da = array(a, 'distances.f32', '<f4', (n, k))
        db = array(b, 'distances.f32', '<f4', (n, k))
        gt = gt_for(pair['dataset'])[:, :k]
        counted = 0
        for i in range(n):
            g, sa, sb = set(map(int, gt[i])), set(map(int, ia[i])), set(map(int, ib[i]))
            lost = (sa & g) - (sb & g)
            if not lost:
                continue
            counted += len(lost)
            oldd = {int(x): float(y) for x, y in zip(ia[i], da[i])}
            newd = {int(x): float(y) for x, y in zip(ib[i], db[i])}
            losses.append({'dataset': pair['dataset'], 'K': k, 'L': int(pair['L']), 'query_row': i,
                'main_hits': len(sa & g), 'residual_hits': len(sb & g),
                'lost_correct': [{'id': x, 'main_distance': oldd[x]} for x in sorted(lost)],
                'new_final_ids': [{'id': x, 'distance': newd[x], 'in_GT': x in g} for x in sorted(sb - sa)],
                'main_boundary_distance': float(da[i, -1]), 'residual_boundary_distance': float(db[i, -1])})
        assert counted == int(pair['lost_members'])
    groups = []
    for ds in dict.fromkeys(p['dataset'] for p in points):
        for k in ['1', '100']:
            rows = [p for p in points if p['dataset'] == ds and p['K'] == k]
            pp = [p for p in pairs if p['dataset'] == ds and p['K'] == k and p['method'] == 'GT10+Residual']
            ff = [p for p in frontier if p['dataset'] == ds and p['K'] == k]
            groups.append({'dataset': ds, 'K': int(k),
                'residual_delta_pp_min': min(float(p['recall_delta_pp']) for p in pp),
                'residual_delta_pp_max': max(float(p['recall_delta_pp']) for p in pp),
                'residual_time_increase_pct_min': min(float(p['mean_time_increase_percent']) for p in pp),
                'residual_time_increase_pct_max': max(float(p['mean_time_increase_percent']) for p in pp),
                'residual_lost_member_events_across_L': sum(int(p['lost_members']) for p in pp),
                'other_method_covered_points': {m: sum(p['covered_by_other_method'] == 'True' for p in ff if p['method'] == m)
                    for m in ['NSG', 'GT10', 'GT10+Residual', 'GATE']},
                'L200': [{key: p[key] for key in ['method', 'recall_percent', 'qps_mean', 'mean_query_us', 'severe_queries']}
                         for p in rows if p['L'] == '200']})
    comparisons = []
    for b in targets:
        if b['method'] != 'GT10+Residual' or b['reached'] != 'True':
            continue
        a = next(p for p in targets if all(p[x] == b[x] for x in ['dataset', 'K', 'target_recall']) and p['method'] == 'GT10')
        if a['reached'] != 'True':
            continue
        comparisons.append({'dataset': b['dataset'], 'K': int(b['K']), 'target_recall': float(b['target_recall']),
            'GT10': a, 'residual': b, 'qps_change_pct': 100 * (float(b['qps_mean']) / float(a['qps_mean']) - 1),
            'two_run_ranges_disjoint_in_residual_favor': float(b['qps_min']) > float(a['qps_max'])})
    examples = []
    for ds, k, l in [('coco', '1', '200'), ('coco', '100', '200'),
                     ('flickr30k', '1', '80'), ('flickr30k', '100', '200'),
                     ('webvid2_5m_light_v1', '1', '640'), ('webvid2_5m_light_v1', '100', '960')]:
        b = next(p for p in points if p['dataset'] == ds and p['K'] == k and p['L'] == l and p['method'] == 'GT10+Residual')
        valid = [p for p in points if p['dataset'] == ds and p['K'] == k and p['method'] == 'GT10'
                 and int(p['hits']) <= int(b['hits']) and float(p['qps_mean']) < float(b['qps_mean'])]
        a = max(valid, key=lambda p: (int(p['hits']), float(p['qps_mean']))) if valid else None
        if a:
            examples.append({'dataset': ds, 'K': int(k), 'GT10': a, 'residual': b,
                'qps_change_pct': 100 * (float(b['qps_mean']) / float(a['qps_mean']) - 1),
                'two_run_ranges_disjoint_in_residual_favor': float(b['qps_min']) > float(a['qps_max'])})
    rounds = read_table('rounds.csv')
    costs = json.loads((RUN / 'reviews/formal_process_costs.json').read_text())
    result = {'status': 'PASS_REPORT_DERIVATIONS_FROM_AUDITED_DATA',
        'scope': 'Descriptive measured-grid comparisons, not statistical significance or global optimality; member losses retain original GT and actual float32 scores',
        'groups': groups, 'threshold_comparisons': comparisons, 'joint_improvement_examples': examples,
        'member_loss_details': losses, 'formal_wall_sum_seconds': sum(float(p['wall_seconds']) for p in rounds),
        'native_process_sum_seconds': sum(p['native_process_seconds'] for p in costs),
        'archive_seconds': sum(p['archive_seconds'] for p in costs),
        'source_sha256': {name: hashlib.sha256((OUT / name).read_bytes()).hexdigest()
                          for name in ['points.csv', 'rounds.csv', 'paired.csv', 'targets.csv', 'frontier.csv', 'independent_audit.json']}}
    with (OUT / 'report_evidence.json').open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({'groups': groups, 'member_loss_details': losses,
        'joint_examples': [{x: p[x] for x in ['dataset', 'K', 'qps_change_pct', 'two_run_ranges_disjoint_in_residual_favor']}
                          | {'GT10': [p['GT10'][x] for x in ['L', 'recall_percent', 'qps_mean']],
                             'residual': [p['residual'][x] for x in ['L', 'recall_percent', 'qps_mean']]}
                          for p in examples],
        'costs': {x: result[x] for x in ['formal_wall_sum_seconds', 'native_process_sum_seconds', 'archive_seconds']}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
