"""Read-only derivation from sealed CSV summaries; no ANN, fitting or QPS run."""
import csv
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
E197 = ROOT / 'entry_method_exploration/20261101_residual_bottleneck_separation_v1'
INPUTS = [
    ROOT / p for p in ('AGENTS.md', 'LOCAL_CODEX_START.md', 'summary.md',
                       'spec.md', 's-target.md', 's-experiment.md')
] + [E197 / p for p in (
    'analysis/points.csv', 'analysis/bottlenecks.csv', 'analysis/comparisons.csv',
    'delivery_validation.json', 'protocol.md', 'findings_zh.md',
    'src/benchmark.cpp', 'src/formal.inc', 'src/model.inc')]
OLD173 = ROOT / 'entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/metrics.csv'
OLD191 = ROOT / 'entry_method_exploration/20261028_seven_dataset_scoring_v1/analysis/all_dense_points.csv'
INPUTS += [OLD173, OLD191]
NAMES = dict(zip(
    ('coco', 'flickr30k', 'webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1',
     'deep10m_l2_v1', 'sift10m_bigann_l2_v1', 'gist1m_l2_v1'),
    ('COCO', 'Flickr', 'WebVid', 'Yandex', 'Deep10M', 'SIFT10M', 'GIST')))


def fingerprint():
    return {str(p.relative_to(ROOT)): {
        'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()
    } for p in INPUTS}


def rows(path):
    with path.open(newline='') as f:
        return list(csv.DictReader(f))


def write_csv(name, data):
    with (OUT / name).open('w', newline='') as f:
        w = csv.DictWriter(f, list(data[0]))
        w.writeheader()
        w.writerows(data)


def main():
    before = fingerprint()
    points = rows(E197 / 'analysis/points.csv')
    receipt = json.loads((E197 / 'delivery_validation.json').read_text())
    assert len(points) == receipt['formal_points'] == 9434
    assert receipt['status'] == 'PASS_E197_FULL_LOCAL_DELIVERY'
    keys = [(x['dataset'], x['window'], x['K'], x['L'], x['method']) for x in points]
    assert len(keys) == len(set(keys))
    for x in points:
        expected = 100 * int(x['hits']) / (int(x['K']) * int(x['n']))
        assert math.isclose(float(x['recall_pct']), expected, abs_tol=1e-10)
        assert math.isclose(float(x['mean_us']), 1e6 / float(x['qps']), abs_tol=1e-7)

    derived = []
    for dataset in NAMES:
        for window in ('A', 'B'):
            domain = [x for x in points if x['dataset'] == dataset
                      and x['window'] == window and x['K'] == '100']
            idx = {(x['method'], int(x['L'])): x for x in domain}
            model, dist, base = (idx[m, 200] for m in ('MODEL-FULL', 'DIST1-FULL', 'OPT-B32'))
            controls = [x for x in domain if x['method'] in ('GT10', 'OPT-B32', 'REUSE-SQ')
                        and int(x['hits']) >= int(model['hits'])]
            control = max(controls, key=lambda x: float(x['qps']))
            t = lambda x: 1e6 / float(x['qps'])
            derived.append(dict(
                dataset=dataset, window=window, K=100, L=200,
                model_recall_pct=float(model['recall_pct']), model_qps=float(model['qps']),
                distance_recall_pct=float(dist['recall_pct']), distance_qps=float(dist['qps']),
                direct_recall_pct=float(base['recall_pct']), direct_qps=float(base['qps']),
                model_us=t(model), distance_us=t(dist), direct_us=t(base),
                control_method=control['method'], control_L=int(control['L']),
                control_recall_pct=float(control['recall_pct']), control_qps=float(control['qps']),
                quality_threshold_us=t(control),
                extra_budget_above_direct_us=t(control)-t(base),
                current_model_time_reduction_to_tie_pct=100*(1-t(control)/t(model)),
                distance_pipeline_above_model_quality_threshold=t(dist)>t(control),
                model_gain_over_distance_pp=float(model['recall_pct'])-float(dist['recall_pct']),
                interpretation='descriptive finite-grid quality threshold; not causal timing or new performance',
            ))
    write_csv('cost_envelopes.csv', derived)
    headroom = []
    for x in rows(E197 / 'analysis/bottlenecks.csv'):
        if x['K'] != '100' or x['bank'] != 'FULL':
            continue
        n, oracle = int(x['queries']), int(x['C_full_gain'])
        headroom.append(dict(
            dataset=x['dataset'], queries=n, K=100, L=200, bank='FULL',
            teacher_gain_pp=oracle/n,
            model_gain_pp=int(x['model_gain'])/n,
            distance_gain_pp=int(x['distance_single_gain'])/n,
            distance_top6_teacher_retention_pct=100*int(x['C_top6_gain'])/oracle,
            model_teacher_retention_pct=100*int(x['model_gain'])/oracle,
            shared_pool_additional_teacher_pp=(int(x['shared_pool_gain'])-oracle)/n,
            interpretation='GT-privileged finite-pool opportunity, no selector cost or learnability guarantee',
        ))
    assert len(derived) == 14 and len(headroom) == 7
    write_csv('headroom.csv', headroom)

    history = []
    for source, data, method, L, ref_method, ref_L, qcol in (
        (OLD173, 'webvid2_5m_light_v1', 'M5', 800, 'GT', 1000, 'qps_median'),
        (OLD191, 'coco', 'REUSE-SQ', 400, 'GT10', 693, 'qps'),
    ):
        tab = {(x['dataset'], x['K'], x['method'], int(x['L'])): x for x in rows(source)}
        a, b = (tab[data, '1', m, l] for m, l in ((method, L), (ref_method, ref_L)))
        history.append(dict(dataset=data, K=1, method=method, L=L,
                            recall_pct=a['recall_pct'], qps=a[qcol],
                            reference=ref_method, reference_L=ref_L,
                            reference_recall_pct=b['recall_pct'], reference_qps=b[qcol],
                            qps_gain_pct=100*(float(a[qcol])/float(b[qcol])-1),
                            source=str(source.relative_to(ROOT))))
    write_csv('historical_examples.csv', history)

    table = ['| 数据 | 模型兑现教师 | 距离前6保留教师 | 当前质量的追加费用空间（两窗，μs） | 当前模型完整耗时须下降 |',
             '| --- | --- | --- | --- | --- |']
    for h in headroom:
        a = [x for x in derived if x['dataset'] == h['dataset']]
        ranges = []
        for key in ('extra_budget_above_direct_us', 'current_model_time_reduction_to_tie_pct'):
            values = [x[key] for x in a]
            ranges.append(f'{min(values):.1f}–{max(values):.1f}')
        table.append(f"| {NAMES[h['dataset']]} | {h['model_teacher_retention_pct']:.1f}% | "
                     f"{h['distance_top6_teacher_retention_pct']:.1f}% | {ranges[0]} | {ranges[1]}% |")
    (OUT / 'tables.md').write_text('\n'.join(table)+'\n')
    assert before == fingerprint(), 'Source changed during read-only derivation'
    (OUT / 'source_manifest.json').write_text(json.dumps(before, indent=2, ensure_ascii=False)+'\n')
    result = dict(status='PASS_READ_ONLY_DERIVATION', source_points=len(points),
                  derived_cost_rows=len(derived), derived_headroom_rows=len(headroom),
                  historical_examples=len(history),
                  distance_above_model_quality_threshold=sum(x['distance_pipeline_above_model_quality_threshold'] for x in derived),
                  input_hashes_unchanged=True, new_ANN=False, new_training=False,
                  new_QPS=False, new_GT=False, default_changed=False,
                  limitation='CSV summary arithmetic verified, not a new audit of all raw packets')
    (OUT / 'reanalysis_validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
