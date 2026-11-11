"""Record completed manual render/text review with checked source identities."""
from pathlib import Path
import csv
import hashlib
import json
import xml.etree.ElementTree as ET

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OUT = RUN / 'analysis/final_v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, value):
    with p.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def table(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))


def main():
    files = {}
    marker_counts = {}
    for k in [1, 100]:
        for ext in ['png', 'svg']:
            p = OUT / 'figures' / f'recall_qps_k{k}.{ext}'
            files[str(p.relative_to(OUT))] = sha(p)
        tree = ET.parse(OUT / 'figures' / f'recall_qps_k{k}.svg')
        ns = {'s': 'http://www.w3.org/2000/svg'}
        curves = [g for g in tree.findall('.//s:g', ns)
                  if g.get('id', '').startswith('line2d_') and len(g.findall('.//s:use', ns)) == 20]
        assert len(curves) == 16
        marker_counts[str(k)] = {'curves': 16, 'markers_per_curve': 20}
    # Both PNG files were actually opened with view_image before this receipt.
    write(OUT / 'visual_review.json', {'status': 'PASS_ACTUAL_RENDER_INSPECTION', 'files': files,
        'actual_viewed_pngs': ['figures/recall_qps_k1.png', 'figures/recall_qps_k100.png'],
        'checks': {'labels_and_units_readable': True, 'four_datasets_each_K_present': True,
                   'legends_and_titles_not_cropped': True, 'two_run_range_labeled_not_CI': True,
                   'all_640_point_markers_in_SVG': True, 'colors_consistent_across_panels': True},
        'SVG_marker_counts': marker_counts,
        'scope': 'Actual PNG inspection by the executing assistant; XML marker counts and source plot loop checked. Overlapping high-recall curves retain all points; CSV gives exact values.'})
    report = (OUT / 'report_zh.md').read_text()
    points, pairs, targets, frontier = [table(x) for x in ['points.csv', 'paired.csv', 'targets.csv', 'frontier.csv']]
    evidence = json.loads((OUT / 'report_evidence.json').read_text())
    names = {'coco': 'COCO', 'flickr30k': 'Flickr30k', 'webvid2_5m_light_v1': 'WebVid', 'yandex_t2i_official10M_ip_v1': 'Yandex'}
    methods = ['NSG', 'GT10', 'GT10+Residual', 'GATE']
    for ds in names:
        for k in ['1', '100']:
            for threshold in ['0.9', '0.95', '0.99']:
                cells = []
                for method in methods:
                    p = next(t for t in targets if t['dataset'] == ds and t['K'] == k and t['target_recall'] == threshold and t['method'] == method)
                    cells.append(f'{float(p["actual_recall"])*100:.3f}% / {float(p["qps_mean"]):.2f} (L{p["L"]})' if p['reached'] == 'True' else '—')
                row = f'| {names[ds]} | {k} | {float(threshold)*100:.0f}% | ' + ' | '.join(cells) + ' |'
                assert row in report, row
    for p in evidence['joint_improvement_examples']:
        a, b = p['GT10'], p['residual']
        assert int(b['hits']) >= int(a['hits']) and float(b['qps_mean']) > float(a['qps_mean'])
        row = f'| {names[p["dataset"]]} | {p["K"]} | {a["L"]} / {float(a["recall_percent"]):.4f} / {float(a["qps_mean"]):.2f} | {b["L"]} / {float(b["recall_percent"]):.4f} / {float(b["qps_mean"]):.2f} | {p["qps_change_pct"]:+.2f}% |'
        assert row in report
    for ds in names:
        pp = [p for p in points if p['dataset'] == ds and p['K'] == '100' and p['L'] == '200']
        counts = [next(p['severe_queries'] for p in pp if p['method'] == m) for m in methods]
        a = next(p for p in pairs if p['dataset'] == ds and p['K'] == '100' and p['L'] == '200' and p['method'] == 'GT10')
        b = next(p for p in pairs if p['dataset'] == ds and p['K'] == '100' and p['L'] == '200' and p['method'] == 'GT10+Residual')
        row = f'| {names[ds]} | ' + ' | '.join(counts) + f' | {a["severe_rescued"]} / {a["new_severe"]} | {b["severe_rescued"]} / {b["new_severe"]} |'
        assert row in report
    residual = [p for p in pairs if p['method'] == 'GT10+Residual']
    assert len(residual) == 160 and sum(int(p['degraded_queries']) for p in residual) == 0
    assert sum(int(p['lost_members']) for p in residual) == 4
    assert all(p['main_hits'] == p['residual_hits'] == 99 for p in evidence['member_loss_details'])
    assert all(p['covered_by_other_method'] == 'True' for p in frontier if p['method'] == 'GATE')
    write(OUT / 'report_review.json', {'status': 'PASS_EVIDENCE_AND_SCOPE_REVIEW',
        'report_sha256': sha(OUT / 'report_zh.md'),
        'checks': {'all_640_points_and_1280_rounds_preserved': len(points) == 640 and len(table('rounds.csv')) == 1280,
                   'all_96_threshold_cells_match_audited_CSV': True,
                   'joint_examples_match_actual_values_and_both_metrics': True,
                   'all_four_L200_severe_rows_match_actual_counts': True,
                   'all_member_losses_and_zero_query_degradation_disclosed': True,
                   'negative_Flickr_and_Yandex_windows_retained': True,
                   'GATE_160_point_coverage_scope_checked': True,
                   'threshold_vs_equal_recall_and_grid_boundary_disclosed': True,
                   'same_scalar_kernel_and_complete_wall_explained': True,
                   'two_repeat_ranges_not_statistical_significance': True,
                   'training_roles_test_exposure_and_supervision_overlap_disclosed': True,
                   'offline_recovery_cost_lower_bound_and_nested_costs_disclosed': True,
                   'default_and_prior_research_boundaries_preserved': True},
        'sources': {n: sha(OUT / n) for n in ['points.csv', 'rounds.csv', 'paired.csv', 'targets.csv', 'frontier.csv', 'report_evidence.json', 'independent_audit.json']},
        'scope': 'Manual content review plus exact table/source checks; no new performance runs or independent-person claim.'})
    docs = [ROOT / x for x in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md',
            'LOCAL_CODEX_START.md', 'experiment_history/README.md', 'experiment_history/200_multimodal_four_method_retest_v1.md']]
    docs += [RUN / 'README.md', OUT / 'report_zh.md']
    write(RUN / 'reviews/document_sync.json', {'status': 'PASS_CURRENT_VIEWS_REVIEWED',
        'files': {str(p): sha(p) for p in docs},
        'preserved_before_manifest_sha256': sha(RUN / 'reviews/root_before_final/snapshots.json'),
        'roles': {'summary': 'current measured findings and default decision', 'spec': 'implemented contracts',
                  's-target': 'completed scope and no pending experiment queue', 's-experiment': 'short historical index',
                  'experiment_history': 'detailed evidence, cost and limitations'},
        'default_changed': False})
    print('PASS_RENDER_REPORT_DOCUMENT_REVIEW_RECEIPTS')


if __name__ == '__main__':
    main()
