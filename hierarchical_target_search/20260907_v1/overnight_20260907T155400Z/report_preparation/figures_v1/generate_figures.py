#!/usr/bin/env python3
"""Export fixed P2/P3 summary figures; no new inference or experiment.

Only the two completed, SHA-bound analysis JSON files are data inputs.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import platform
import struct
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator
import numpy as np

RUN = Path(__file__).resolve().parents[2]
EXPECTED_HASHES = {
    'p2': 'e73a8d8c16a5bebb2404596b63d621b1780b1aab0f9eb29efce5281edfc04c1f',
    'p3': '63da6a71425b0dbd6e186db1c608a564b9847c58168b6b56059a9ed2d2f901ae',
}
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
DATASET_NAMES = {'webvid2_5m_light_v1': 'WebVid-2.5M', 'yandex_t2i_official10M_ip_v1': 'Yandex-10M'}
METHODS = (
    ('fast', 'Fast (m=3)', '#25313b', 'o', '-', 7.5, '#25313b'),
    ('geom_unified', 'Geometric: unified pool', '#0072b2', '^', '-', 8.5, '#0072b2'),
    ('geom_uniform', 'Geometric: uniform pools', '#009e73', 's', '-', 10.5, 'white'),
    ('geom_probability', 'Geometric: probability pools', '#cc79a7', '+', '-', 11.5, '#cc79a7'),
    ('oracle_unified', 'Oracle: unified (diagnostic)', '#e69f00', 'D', '--', 8.5, 'white'),
    ('oracle_probability', 'Oracle: probability (diagnostic)', '#7553a3', 'X', '--', 9.5, 'white'),
)
DPI = 300


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': digest(path), 'bytes': path.stat().st_size}


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def inputs(stage, path):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_HASHES[stage], 'Frozen input hash differs: ' + stage)
    obj = json.loads(raw)
    require(obj['status'] == 'COMPLETE' and [d['dataset'] for d in obj['datasets']] == list(DATASETS),
            'Both complete fixed datasets required')
    return obj


def export(fig, out, stem):
    outputs = []
    for ext in ('svg', 'png'):
        path = out / f'{stem}.{ext}'
        require(not path.exists(), 'Refuse to overwrite export: ' + str(path))
        kwargs = {'format': ext, 'facecolor': 'white'}
        if ext == 'png':
            kwargs['dpi'] = DPI
            kwargs['metadata'] = {'Software': 'Matplotlib; frozen ACSG P2/P3 summary export',
                                  'Description': '10K development pilot; oracle diagnostic only; no formal performance gain established.'}
        else:
            kwargs['metadata'] = {'Creator': 'Matplotlib; ACSG frozen-summary report preparation',
                                  'Description': 'Scientific figure from existing completed summaries; no new confidence intervals or experiments.'}
        fig.savefig(path, **kwargs)
        record = ref(path)
        if ext == 'png':
            header = path.read_bytes()[:24]
            require(header[:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG export')
            record['pixel_dimensions'] = list(struct.unpack('>II', header[16:24]))
            record['dpi'] = DPI
        else:
            record['format'] = 'standalone vector SVG; text preserved as text'
        outputs.append(record)
    plt.close(fig)
    return outputs


def p2_figure(data, out):
    fig, axes = plt.subplots(1, 2, figsize=(14, 7.5), sharey=True)
    fig.subplots_adjust(left=.07, right=.985, top=.80, bottom=.30, wspace=.13)
    fig.suptitle('P2 | Recall and throughput on the development pilot', x=.07, y=.97, ha='left', fontsize=19, weight='bold')
    fig.text(.07, .915, '10,000 queries per dataset  |  K=10  |  16 CPU threads  |  QPS: mean of five pure-wall rounds', fontsize=11.8, color='#4b5563')
    points = []
    handles = []
    for ax, dataset in zip(axes, DATASETS):
        ds = next(d for d in data['datasets'] if d['dataset'] == dataset)
        require(ds['audit_status'] == 'PASS' and len(ds['measurements']) == 12, 'Incomplete P2 measurement table')
        for order, (method, label, color, marker, style, size, face) in enumerate(METHODS):
            rows = sorted((m for m in ds['measurements'] if m['method'] == method), key=lambda m: m['L'])
            require([m['L'] for m in rows] == [64, 128] and all(m['num_queries'] == 10000 for m in rows), 'Missing P2 method/L')
            require(rows[0]['recall'] < rows[1]['recall'] and rows[0]['qps_mean_of_five'] > rows[1]['qps_mean_of_five'],
                    'Endpoint L annotation is inconsistent with observed data')
            for m in rows:
                require(m['oracle_diagnostic_only'] == method.startswith('oracle') and len(m['qps_rounds']) == 5,
                        'Oracle flag or five-round QPS source differs')
                require(abs(sum(m['qps_rounds']) / 5 - m['qps_mean_of_five']) < 1e-8, 'Stored mean QPS differs from five rounds')
                points.append({'dataset': dataset, 'method': method, 'L': m['L'], 'recall_fraction': m['recall'],
                               'mean_of_five_QPS': m['qps_mean_of_five'], 'oracle_diagnostic_only': m['oracle_diagnostic_only']})
            ax.plot([m['recall'] * 100 for m in rows], [m['qps_mean_of_five'] / 1000 for m in rows],
                    color=color, linestyle=style, linewidth=1.9, marker=marker, markersize=size,
                    markerfacecolor=face, markeredgecolor=color, markeredgewidth=1.6,
                    zorder=8 if method == 'fast' else 3 + order)
            if ax is axes[0]:
                handles.append(Line2D([0], [0], color=color, linestyle=style, linewidth=1.9,
                                      marker=marker, markersize=size - 1, markerfacecolor=face,
                                      markeredgecolor=color, markeredgewidth=1.4, label=label))
        ax.set_title(DATASET_NAMES[dataset], loc='left', fontsize=15, weight='bold', pad=12)
        ax.set_xlabel('Recall@10 (%)', labelpad=8)
        ax.set_ylim(0, 35)
        ax.yaxis.set_major_locator(MultipleLocator(5))
        ax.xaxis.set_major_locator(MultipleLocator(5))
        ax.set_xlim((56, 84) if dataset == DATASETS[0] else (72, 96))
        ax.grid(axis='both', color='#d8dee5', alpha=.7, linewidth=.7)
        ax.set_axisbelow(True)
        ax.text(.02, .04, 'Higher-QPS endpoint: L64\nLower-QPS endpoint: L128', transform=ax.transAxes,
                fontsize=10.1, color='#586271', va='bottom', bbox={'facecolor': 'white', 'edgecolor': 'none', 'alpha': .85, 'pad': 3})
        for edge in ('top', 'right'):
            ax.spines[edge].set_visible(False)
    axes[0].set_ylabel('Throughput (thousand queries/s)', labelpad=8)
    fig.legend(handles=handles, ncol=3, loc='lower center', bbox_to_anchor=(.53, .15), frameon=False,
               columnspacing=2.2, handlelength=2.8, handletextpad=.8, fontsize=11)
    fig.text(.07, .105, 'Lines connect the two measured settings only. WebVid uniform/probability points nearly overlap; no coordinates are shifted.',
             fontsize=10.1, color='#4b5563')
    fig.text(.07, .065, 'Oracle uses true target regions: diagnostic only, not a deployment method. Cross-model wall comparisons are descriptive.',
             fontsize=10.1, color='#4b5563')
    fig.text(.07, .025, 'No new timing interval, matched-cost interpolation, or formal performance-gain claim is made.',
             fontsize=10.1, color='#4b5563')
    return export(fig, out, 'p2_recall_qps'), points


def p3_figure(data, out):
    rows = []
    for dataset in DATASETS:
        ds = next(d for d in data['datasets'] if d['dataset'] == dataset)
        for l in (64, 128):
            found = [c for c in ds['fixed_comparisons'] if c['L'] == l and c['contrast'] == 'structure_under_greedy3']
            require(len(found) == 1, 'Missing fixed primary structure contrast')
            rows.append({'group': 'primary_structure', **found[0]})
    for dataset in DATASETS:
        ds = next(d for d in data['datasets'] if d['dataset'] == dataset)
        for lam in (0, 1):
            for l in (64, 128):
                found = [c for c in ds['fixed_comparisons'] if c['L'] == l and c['contrast'] == f'portals_under_lambda{lam}']
                require(len(found) == 1, 'Missing fixed portal contrast')
                rows.append({'group': 'portal_selection', 'lambda': lam, **found[0]})
    require(len(rows) == 12 and data['primary_search_condition']['all_four_lower_bounds_positive'] is False,
            'Expected failed four-cell primary condition and eight portal contrasts')
    for row in rows:
        low, high = row['paired_query_bootstrap95_pp']
        require(math.isfinite(low) and math.isfinite(high) and low <= row['recall_delta_pp'] <= high and
                row['oracle_diagnostic_only'] is True and row['candidate_method'] == row['reference_method'] == 'oracle_probability',
                'Wrong CI or oracle diagnostic scope')
    fig, ax = plt.subplots(figsize=(14, 8.8))
    fig.subplots_adjust(left=.265, right=.745, top=.80, bottom=.24)
    fig.suptitle('P3 | Structure and portal effects on oracle search', x=.055, y=.97, ha='left', fontsize=19, weight='bold')
    fig.text(.055, .924, 'Existing paired-query 95% intervals  |  10K development pilot  |  K=10  |  16 CPU threads', fontsize=11.8, color='#4b5563')
    positions = [13, 12, 11, 10, 8, 7, 6, 5, 4, 3, 2, 1]
    labels = []
    colors = {DATASETS[0]: '#21618c', DATASETS[1]: '#bc6c25'}
    for row, y in zip(rows, positions):
        x = row['recall_delta_pp']; low, high = row['paired_query_bootstrap95_pp']
        color = colors[row['dataset']]
        ax.hlines(y, low, high, color=color, linewidth=2.2)
        ax.vlines([low, high], y - .11, y + .11, color=color, linewidth=1.5)
        ax.plot(x, y, marker='D' if row['group'] == 'primary_structure' else 'o', markersize=7.5,
                color=color, markeredgecolor='white', markeredgewidth=.65, zorder=5)
        short = 'WebVid' if row['dataset'] == DATASETS[0] else 'Yandex'
        labels.append(f'{short}  |  L{row["L"]}' if row['group'] == 'primary_structure' else f'{short}  |  λ{row["lambda"]}  |  L{row["L"]}')
        ax.text(1.045, y, f'{x:+.3f}  [{low:+.3f}, {high:+.3f}]', transform=ax.get_yaxis_transform(),
                va='center', fontsize=10.8, color='#293744', family='DejaVu Sans Mono')
    ax.set_yticks(positions, labels, fontsize=11.5)
    ax.tick_params(axis='y', length=0, pad=13)
    ax.set_ylim(.35, 13.7)
    ax.set_xlim(-1.18, .40)
    ax.xaxis.set_major_locator(MultipleLocator(.2))
    ax.axvline(0, color='#465365', linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    ax.grid(axis='x', linewidth=.7, color='#e0e5eb')
    ax.set_axisbelow(True)
    ax.set_xlabel('Recall@10 difference (percentage points)', labelpad=10)
    for edge in ('top', 'right', 'left'):
        ax.spines[edge].set_visible(False)
    ax.text(-.40, 14.12, 'PRIMARY: λ1 − λ0 under greedy3', transform=ax.get_yaxis_transform(),
            fontsize=12, weight='bold', color='#25313b', clip_on=False)
    ax.text(-.40, 9.16, 'PORTALS: greedy3 − frequency3', transform=ax.get_yaxis_transform(),
            fontsize=12, weight='bold', color='#25313b', clip_on=False)
    ax.text(1.045, 14.12, 'Δ Recall pp  [ordinary 95% CI]', transform=ax.get_yaxis_transform(),
            fontsize=10.9, weight='bold', color='#25313b', clip_on=False)
    ax.axhline(9.13, color='#d3dbe4', linewidth=.8, xmin=0, xmax=1)
    fig.text(.055, .137, 'Positive favors λ1 (primary) or greedy3 (portals). The plotted endpoints are the exact existing, unadjusted ordinary 95% intervals.',
             fontsize=10.4, color='#4b5563')
    fig.text(.055, .096, 'Oracle uses true target regions: diagnostic only, not deployable. P3 search gate: NOPASS; no formal performance gain established.',
             fontsize=10.4, color='#4b5563')
    fig.text(.055, .055, 'Cross-model wall comparisons are descriptive; this figure displays Recall only. No new confidence interval or subgroup selection.',
             fontsize=10.4, color='#4b5563')
    points = [{k: r[k] for k in ('group', 'dataset', 'L', 'contrast', 'candidate_model', 'reference_model',
                                'recall_delta_pp', 'paired_query_bootstrap95_pp', 'interval_scope')} for r in rows]
    return export(fig, out, 'p3_fixed_contrasts'), points


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--p2-analysis', type=Path, default=RUN / 'p2/analysis_v1/analysis.json')
    p.add_argument('--p3-analysis', type=Path, default=RUN / 'p3/analysis_v1/analysis.json')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    require(not (a.output / 'input_hash_manifest.json').exists(), 'This output directory was already completed')
    for name in ('p2_recall_qps', 'p3_fixed_contrasts'):
        require(not any((a.output / f'{name}.{ext}').exists() for ext in ('png', 'svg')), 'Existing figure export must be preserved')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11.5, 'axes.labelsize': 12.2,
                         'axes.edgecolor': '#687383', 'axes.linewidth': .8, 'xtick.color': '#465365',
                         'ytick.color': '#465365', 'svg.fonttype': 'none', 'svg.hashsalt': 'acsg-report-figures-v1'})
    p2 = inputs('p2', a.p2_analysis)
    p3 = inputs('p3', a.p3_analysis)
    files2, points2 = p2_figure(p2, a.output)
    files3, points3 = p3_figure(p3, a.output)
    record = {'schema_version': 1, 'status': 'COMPLETE', 'scope': 'REPORT_EXPORT_FROM_EXISTING_SUMMARIES_ONLY',
              'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv,
              'source': ref(__file__), 'inputs': {'p2': ref(a.p2_analysis), 'p3': ref(a.p3_analysis)},
              'outputs': files2 + files3, 'plotted_P2_points': points2, 'plotted_P3_contrasts': points3,
              'environment': {'python': platform.python_version(), 'executable': sys.executable,
                              'matplotlib': matplotlib.__version__, 'numpy': np.__version__, 'backend': matplotlib.get_backend()},
              'dimensions_inches': {'p2_recall_qps': [14, 7.5], 'p3_fixed_contrasts': [14, 8.8]},
              'PNG_dpi': DPI, 'reads_raw_GT_count_model_query_base_graph': False,
              'new_numerical_experiment': False, 'new_confidence_intervals': False,
              'new_interpolated_performance_points': False, 'formal_performance_gain_claim': False,
              'limits': ['P2 displays all six methods at exactly both fixed L values; connecting segments are visual guides only.',
                         'P2 QPS is the saved arithmetic mean of five pure-wall rounds, without a new timing uncertainty estimate.',
                         'P3 displays all four primary structure and all eight portal comparisons. CI endpoints are copied exactly; table text is rounded to 0.001 pp.',
                         '10K development pilot is neither validation nor held-out confirmation. Oracle is diagnostic only and not a deployable method.',
                         'Cross-model wall comparisons are descriptive. Neither plot implies matched-cost interpolation or formal performance improvement.',
                         'Near-overlapping P2 points retain their true coordinates; different marker shapes and outlines indicate both methods.']}
    write_new(a.output / 'input_hash_manifest.json', record)
    print(json.dumps({'status': 'COMPLETE', 'outputs': record['outputs'], 'manifest': ref(a.output / 'input_hash_manifest.json')}))


if __name__ == '__main__':
    main()
