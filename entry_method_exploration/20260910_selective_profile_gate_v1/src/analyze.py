"""Read-only analysis of frozen gates and independently measured curves."""
import csv
import math
import numpy as np
from common import RUN, DATASETS, FEATURES, LS, read, dump, check_lock, frozen_gate_check
from gate_stats import load_pair, ratios_stats, cross_L_stats
from verify_outputs import predict

LABELS = {'webvid2_5m_light_v1': 'WebVid', 'yandex_t2i_official10M_ip_v1': 'Yandex-IP'}
METHODS = ['nsg', 'fast30k', 'fast20k', 'e24', 'base_gate', 'dual_gate']
METHOD_LABELS = {'nsg': 'NSG', 'fast30k': 'Fast30K', 'fast20k': 'Fast20K', 'e24': 'E24',
                 'base_gate': 'BaseGate', 'dual_gate': 'DualGate'}


def weighted_auc(z, P, N):
    if P.sum() == 0 or N.sum() == 0:
        return None
    order = np.argsort(z, kind='stable')
    _, first = np.unique(z[order], return_index=True)
    positive = np.add.reduceat(P[order], first)
    negative = np.add.reduceat(N[order], first)
    negative_below = np.cumsum(negative) - negative
    return float(np.sum(positive * (negative_below + .5 * negative)) / (P.sum() * N.sum()))


def descriptive_bootstrap(h0, h1, choose):
    if h0.ndim == 1:
        h0, h1 = h0[:, None], h1[:, None]
    d = h1 - h0
    chosen = np.asarray(choose)[:, None]
    pos, neg = np.maximum(d, 0), np.maximum(-d, 0)
    rows = np.column_stack([
        ((d > 0) * chosen).sum(axis=1), (d > 0).sum(axis=1),
        ((d < 0) * ~chosen).sum(axis=1), (d < 0).sum(axis=1),
        (pos * chosen).sum(axis=1), pos.sum(axis=1),
        (neg * ~chosen).sum(axis=1), neg.sum(axis=1),
        (d * chosen).sum(axis=1), (d * (chosen - np.ones_like(chosen, dtype='int16'))).sum(axis=1),
    ]).astype(float)
    rng = np.random.Generator(np.random.PCG64(20260910))
    values = []
    for _ in range(20):
        selected_rows = rng.integers(0, len(d), size=(100, len(d)))
        totals = rows[selected_rows].sum(axis=1)
        ratios = []
        for a, b in [(0,1),(2,3),(4,5),(6,7)]:
            ratios.append(np.divide(totals[:, a], totals[:, b], out=np.full(100, np.nan), where=totals[:, b] > 0))
        values.append(np.column_stack([*ratios, totals[:, 8] * 10 / h0.size, totals[:, 9] * 10 / h0.size]))
    samples = np.vstack(values)
    intervals = {}
    for j, name in enumerate(['R','A','Rh','Ah','delta_recall_pp_vs_A0','delta_recall_pp_vs_A1']):
        defined = samples[np.isfinite(samples[:, j]), j]
        intervals[name] = {'low': float(np.quantile(defined, .025)) if len(defined) else None,
                           'high': float(np.quantile(defined, .975)) if len(defined) else None,
                           'defined_replicates': len(defined)}
    return {'seed': 20260910, 'replicates': 2000, 'unit': 'paired_query_all_L_kept_together',
            'interpretation': 'descriptive_unadjusted_percentile_95_not_a_selection_or_formal_GO_test',
            'intervals': intervals}


def signal_stats(h0, h1, z, choose, model):
    d = h1 - h0
    P = np.maximum(d, 0).sum(axis=1)
    N = np.maximum(-d, 0).sum(axis=1)
    net = d.sum(axis=1).astype(float)
    selected = int(choose.sum())
    fraction = selected / len(choose)
    mean_random = fraction * float(net.sum())
    variance_random = selected * (len(net) - selected) * float(net.var()) / max(len(net)-1, 1)
    observed = float(net[choose].sum())
    zero = ~(P + N > 0)
    return {'positive_hit_weight': int(P.sum()), 'negative_hit_weight': int(N.sum()),
            'weighted_AUC': weighted_auc(z, P, N),
            'event_AUC': weighted_auc(z, (d > 0).sum(axis=1), (d < 0).sum(axis=1)),
            'queries_with_any_label_weight': int((~zero).sum()),
            'zero_weight_queries': int(zero.sum()), 'zero_weight_queries_selected': int((zero & choose).sum()),
            'weighted_positive_prior': float(P.sum() / (P + N).sum()) if (P + N).sum() else None,
            'random_same_cardinality_expected_net_hits': mean_random,
            'observed_selected_net_hits': observed,
            'excess_net_hits_over_random_expectation': observed - mean_random,
            'random_same_cardinality_net_hits_standard_deviation': math.sqrt(variance_random),
            'random_expectation_is_posthoc_diagnostic_not_extra_gate': True,
            'minimum_distance_from_frozen_threshold': float(np.abs(z - model['threshold']).min())}


def validation_arrays(ds):
    folder = RUN / 'results' / ds
    assert read(folder / 'independent_verification.json')['status'] == 'PASS'
    x = np.fromfile(folder / 'features.f64', dtype='<f8').reshape(2000, 13)
    data = {}
    for kind in METHODS:
        data[kind] = {L: {'hits': np.fromfile(folder / f'{kind}_L{L}/hits.u8', dtype='u1').astype('int16'),
                         'entries': np.fromfile(folder / f'{kind}_L{L}/entry_ids.i32', dtype='<i4').reshape(2000, 3),
                         'graph_ndc': np.fromfile(folder / f'{kind}_L{L}/graph_ndc.u32', dtype='<u4'),
                         'route_ndc': np.fromfile(folder / f'{kind}_L{L}/route_ndc.u32', dtype='<u4')}
                      for L in LS}
    return folder, x, data


def split_analysis(ds, selections, stage, x, h0, h1):
    result = {'queries': len(x), 'cross_L': cross_L_stats(h0, h1), 'gates': {},
              'A1_control': ratios_stats(h0, h1, np.ones(len(x), bool))}
    strata = {}
    for kind in ['base_gate','dual_gate']:
        model = read(RUN / 'models' / ds / f'{kind}.json')
        z, choose = predict(x, model)
        result['gates'][kind] = {'pooled_L64_L128': ratios_stats(h0, h1, choose),
                                'per_L': {str(L): ratios_stats(h0[:, j], h1[:, j], choose) for j,L in enumerate([64,128])},
                                'signal': signal_stats(h0, h1, z, choose, model),
                                'bootstrap': descriptive_bootstrap(h0, h1, choose)}
        by_feature = {}
        for j, feature in enumerate(FEATURES):
            bounds = selections[ds]['feature_quartile_boundaries_fit_only'][feature]
            bins = np.searchsorted(bounds, x[:, j], side='right')
            by_feature[feature] = {'fit_boundaries': bounds, 'bins': []}
            for b in range(4):
                keep = bins == b
                by_feature[feature]['bins'].append({'bin': b, 'queries': int(keep.sum()),
                    'stats': ratios_stats(h0[keep], h1[keep], choose[keep]) if keep.any() else None})
        strata[kind] = by_feature
    dump(RUN / 'results' / 'mechanism' / ds / f'{stage}_feature_strata.json', strata)
    return result


def compare_point(ds, m, ref, data):
    kind, other, L = m['kind'], ref['kind'], m['L']
    hits = data[kind][L]['hits']; baseline = data[other][L]['hits']
    diff = hits - baseline
    qps_ratios = np.asarray(m['qps_runs']) / ref['qps_runs']
    n = len(hits)
    interval = descriptive_bootstrap(baseline, hits, np.ones(n, bool))['intervals']['delta_recall_pp_vs_A0']
    return {'dataset': ds, 'method': kind, 'reference': other, 'L': L,
            'recall': m['recall_at_10'], 'reference_recall': ref['recall_at_10'],
            'delta_recall_pp': float(diff.mean() * 10), 'delta_recall_pp_95': interval,
            'qps_median': m['qps'], 'reference_qps_median': ref['qps'],
            'qps_percent_change_medians': 100 * (m['qps']/ref['qps'] - 1),
            'qps_percent_change_by_repeat': (100*(qps_ratios-1)).tolist(),
            'recall_strictly_better': bool(diff.sum() > 0),
            'same_L_recall_and_median_qps_strictly_better': bool(diff.sum() > 0 and m['qps'] > ref['qps']),
            'same_L_recall_better_qps_better_all_three_repeats': bool(diff.sum() > 0 and np.all(qps_ratios > 1)),
            'improved_queries': int((diff > 0).sum()), 'harmed_queries': int((diff < 0).sum()),
            'same_hits_queries': int((diff == 0).sum()), 'positive_hits': int(np.maximum(diff,0).sum()),
            'negative_hits': int(np.maximum(-diff,0).sum()), 'net_hits': int(diff.sum()),
            'zero_hit_rescues': int(((baseline == 0) & (hits > 0)).sum()),
            'new_zero_hit_failures': int(((baseline > 0) & (hits == 0)).sum()),
            'mean_graph_ndc_difference': float(data[kind][L]['graph_ndc'].mean()-data[other][L]['graph_ndc'].mean()),
            'mean_total_ndc_difference': float((data[kind][L]['graph_ndc']+data[kind][L]['route_ndc']).mean() -
                                             (data[other][L]['graph_ndc']+data[other][L]['route_ndc']).mean())}


def frontier(points, field='qps'):
    return [p['name'] for p in points if not any(
        q['recall_at_10'] >= p['recall_at_10'] and q[field] >= p[field] and
        (q['recall_at_10'] > p['recall_at_10'] or q[field] > p[field]) for q in points if q is not p)]


def main():
    check_lock(); frozen_gate_check()
    assert read(RUN / 'reviews/validation_verification.json')['status'] == 'PASS'
    selections = read(RUN / 'models/selections.json')
    report = {'status': 'ANALYSIS_COMPLETE', 'datasets': {}, 'comparisons': [],
              'historical_validation': True, 'formal_performance_GO': False}
    for ds in DATASETS:
        r = {'primary_frozen_on_cal': selections[ds]['primary'], 'splits': {}, 'validation_gates': {}}
        for stage in ['fit','cal','audit']:
            _, x, h0, h1 = load_pair(ds, stage)
            r['splits'][stage] = split_analysis(ds, selections, stage, x, h0, h1)
        folder, x, data = validation_arrays(ds)
        h0 = np.column_stack([data['fast20k'][L]['hits'] for L in [64,128]])
        h1 = np.column_stack([data['e24'][L]['hits'] for L in [64,128]])
        r['splits']['validation'] = split_analysis(ds, selections, 'validation', x, h0, h1)
        points = read(folder / 'results.json')['methods']
        r['measured_points'] = points
        for kind in ['base_gate','dual_gate']:
            model = read(RUN / 'models' / ds / f'{kind}.json')
            z, choose = predict(x, model)
            per_L = {}
            for L in LS:
                b, a = data['fast20k'][L]['hits'], data['e24'][L]['hits']
                assert np.array_equal(np.where(choose, a, b), data[kind][L]['hits'])
                per_L[str(L)] = {'stats': ratios_stats(b,a,choose), 'bootstrap': descriptive_bootstrap(b,a,choose)}
            b = np.column_stack([data['fast20k'][L]['hits'] for L in LS])
            a = np.column_stack([data['e24'][L]['hits'] for L in LS])
            r['validation_gates'][kind] = {'per_L': per_L,
                'all_five_L_extrapolation_descriptive_only': ratios_stats(b,a,choose),
                'cross_five_L': cross_L_stats(b,a)}
            same_entries = np.all(data['fast20k'][64]['entries'] == data['e24'][64]['entries'],axis=1)
            r['validation_gates'][kind]['entry_mechanism'] = {
                'A0_A1_identical_entry_sets': int(same_entries.sum()),
                'gate_selected_A1_but_same_entry_sets': int((choose & same_entries).sum()),
                'gate_actual_entry_changes_vs_A0': int((choose & ~same_entries).sum()),
                'A1_changes_reverted_by_gate': int((~choose & ~same_entries).sum())}
        for kind in ['e24','base_gate','dual_gate','fast30k']:
            for other in (['fast20k','e24','nsg','fast30k'] if kind in ['base_gate','dual_gate'] else ['fast20k','nsg']):
                if kind == other: continue
                for L in LS:
                    m = next(p for p in points if p['kind'] == kind and p['L'] == L)
                    ref = next(p for p in points if p['kind'] == other and p['L'] == L)
                    report['comparisons'].append(compare_point(ds,m,ref,data))
        r['frontier_among_all_six_methods_30_measured_points'] = frontier(points)
        r['frontier_by_repeat'] = []
        for repeat in range(3):
            current = [{**p, 'qps_repeat': p['qps_runs'][repeat]} for p in points]
            r['frontier_by_repeat'].append(frontier(current, 'qps_repeat'))
        report['datasets'][ds] = r
        print(ds, 'ANALYZED', r['primary_frozen_on_cal'], flush=True)
    dump(RUN / 'results/analysis.json', report)
    flat = [{k:v for k,v in row.items() if not isinstance(v,(dict,list))} for row in report['comparisons']]
    with (RUN / 'results/comparisons.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    frozen_gate_check()
    print('ANALYSIS_ALL_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
