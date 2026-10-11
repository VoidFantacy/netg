#!/usr/bin/env python3
"""Render E175's 80 audited, precomputed points; no query or GT access.

Only the five measured L points of each method are connected. No fitting,
intermediate-L estimate, jitter, bootstrap, or replacement decision is made.
Matplotlib is imported only when main() runs after the independent audit.
"""
import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
DATASET_LABELS = {'webvid2_5m_light_v1': 'WebVid2.5M',
                  'yandex_t2i_official10M_ip_v1': 'YandexT2I'}
L_VALUES = (200, 400, 800, 1000, 1200)
METHODS = ('NSG', 'GT', 'M5', 'M5REG96')
STYLES = {'NSG': ('#2563eb', 'o', 'NSG', 6),
          'GT': ('#f59e0b', 's', 'GT10', 6),
          'M5': ('#dc2626', '*', '原 M5', 9),
          'M5REG96': ('#7c3aed', 'D', 'M5REG96', 6)}
NATIVE_THREADS = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                  'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def point_key(point):
    return point['dataset'], point['K'], point['L'], point['method']


def read_points(metrics):
    require(metrics.stat().st_size < 64 * 1024 * 1024, 'small precomputed metrics only')
    measured = read_json(metrics)
    require(measured['status'] == 'COMPLETE_E175_FROZEN_80_POINT_EVALUATION', 'completed E175 evaluation')
    points = measured['points']
    require(len(points) == 80, 'all 80 points')
    by_key = {}
    for point in points:
        key = point_key(point)
        require(key not in by_key, 'unique dataset/K/L/method point')
        require(point['role'] == 'public_test' and point['n'] == 10000, 'one already exposed public 10K role')
        require(all(math.isfinite(point[field]) for field in
                    ('recall_pct', 'qps_median', 'qps_min', 'qps_max')), 'finite saved plot fields')
        require(0 <= point['recall_pct'] <= 100
                and 0 < point['qps_min'] <= point['qps_median'] <= point['qps_max'], 'saved field domain')
        require(len(point['qps_rounds']) == 3
                and all(math.isfinite(x) and x > 0 for x in point['qps_rounds']), 'three saved wall-derived QPS values')
        by_key[key] = point
    expected = {(ds, K, L, name) for ds in DATASETS for K in (1, 100)
                for L in L_VALUES for name in METHODS}
    require(set(by_key) == expected, 'exact frozen 2 datasets x 2 K x 5 L x 4 methods')
    for ds in DATASETS:
        for K in (1, 100):
            require(sum(key[0] == ds and key[1] == K for key in by_key) == 20, 'all 20 points in each panel')
    return by_key


def protect_existing(audit):
    # Metadata checks never reopen the raw/GT/vector/model payloads.
    paths = set(audit['source_sha256_and_stat4'])
    preflight = read_json(ROOT / 'reviews/data_preflight.json')
    paths.update(preflight['registered_input_files'])
    paths.update(str(ROOT / name) for name in (
        'protocol.md', 'parameter_lock.json', 'execution_lock.json', 'auxiliary_lock.json',
        'run_state.json', 'reviews/data_preflight.json', 'reviews/inventory.json',
        'reviews/independent_result_audit/report.json', 'analysis/final_v1/metrics.json',
        'analysis/final_v1/points.csv', 'analysis/final_v1/comparisons.csv',
        'analysis/final_v1/mechanisms.csv'))
    for name in ('README.md', 'analysis/final_v1/report.md'):
        path = ROOT / name
        if path.exists():
            paths.add(str(path))
    return {path: stat4(path) for path in sorted(paths)}


def draw(points, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.lines import Line2D
    from matplotlib.ticker import ScalarFormatter

    # Same local CJK font used by E173's plot_results.py; no font download.
    font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    require(font_path.is_file(), 'local Noto Sans CJK font required for complete Chinese labels')
    font_manager.fontManager.addfont(str(font_path))
    font_name = font_manager.FontProperties(fname=str(font_path)).get_name()
    plt.rcParams.update({'font.family': font_name, 'font.size': 10,
                         'axes.unicode_minus': False, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 2, figsize=(16, 10.5))
    fig.subplots_adjust(left=.095, right=.975, bottom=.14, top=.815,
                        wspace=.26, hspace=.43)
    plotted_keys = []
    plotted_fields = []
    for row, ds in enumerate(DATASETS):
        for col, K in enumerate((1, 100)):
            ax = axes[row, col]
            for name in METHODS:
                curve = [points[(ds, K, L, name)] for L in L_VALUES]
                # Coordinates use saved values directly; subtraction below
                # only expresses the saved min/max endpoints as error lengths.
                recall = [point['recall_pct'] for point in curve]
                qps = [point['qps_median'] for point in curve]
                lower = [point['qps_median'] - point['qps_min'] for point in curve]
                upper = [point['qps_max'] - point['qps_median'] for point in curve]
                color, marker, label, size = STYLES[name]
                ax.errorbar(recall, qps, yerr=[lower, upper], color=color,
                            marker=marker, markersize=size, linewidth=1.35,
                            elinewidth=.9, capsize=3, capthick=.9, alpha=.95,
                            label=label, zorder=3 if name == 'M5REG96' else 2)
                if name == 'M5REG96':
                    for i, point in enumerate(curve):
                        ax.annotate(f'L={point["L"]}',
                                    xy=(point['recall_pct'], point['qps_median']),
                                    xytext=(7, 8 if i % 2 == 0 else -15),
                                    textcoords='offset points', fontsize=8.5,
                                    color=color, annotation_clip=False)
                for point in curve:
                    plotted_keys.append(point_key(point))
                    plotted_fields.append({key: point[key] for key in
                        ('role', 'dataset', 'K', 'L', 'method', 'n', 'recall_pct',
                         'qps_median', 'qps_min', 'qps_max')})
            anchor = 'GT10-soft-t1' if row == 0 else 'GT10-hard'
            ax.set_title(f'{DATASET_LABELS[ds]} · Recall@{K} · {anchor}', fontsize=11.5, pad=13)
            ax.set_xlabel(f'Recall@{K} (%)', fontsize=11, labelpad=9)
            ax.set_ylabel('完整单线程 QPS', fontsize=11, labelpad=10)
            ax.grid(True, color='#dbe3ec', linewidth=.65, alpha=.8)
            ax.margins(x=.11, y=.15)
            formatter = ScalarFormatter(useOffset=False)
            formatter.set_scientific(False)
            ax.yaxis.set_major_formatter(formatter)
            ax.tick_params(axis='both', labelsize=9)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
    require(len(plotted_keys) == 80 and set(plotted_keys) == set(points), 'all 80 stored points plotted once')
    # Check every recorded source field by identity, without new statistics.
    require(all(record == {key: points[point_key(record)][key] for key in record}
                for record in plotted_fields), 'all plotted fields exactly equal saved fields')
    handles = [Line2D([], [], color=STYLES[name][0], marker=STYLES[name][1],
                      markersize=STYLES[name][3], linewidth=1.35, label=STYLES[name][2])
               for name in METHODS]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.535, .88),
               ncol=4, frameon=False, fontsize=11, columnspacing=3, handlelength=2.5)
    fig.suptitle('M5 区域扩展与原方法：Recall–QPS 预算曲线', fontsize=17, y=.97)
    fig.text(.535, .915, '四种方法在本轮同条件重跑；真实 K=1 / 100；单线程 CPU15',
             ha='center', fontsize=10.5, color='#475569')
    fig.text(.535, .075,
             '两集公共测试前 10,000 查询；L = 200 / 400 / 800 / 1000 / 1200；四种方法使用相同主搜索 L。\n'
             'QPS 为三轮完整计时的中位数，误差线为最小值–最大值；紫色数字标注 M5REG96 的 L。',
             ha='center', va='center', fontsize=10, color='#475569', linespacing=1.7)
    fig.text(.535, .025, '越右上越好；线段连接实测点。公共测试窗口此前已曝光，本轮用于预算曲线比较。',
             ha='center', va='center', fontsize=9.5, color='#475569')
    out.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'svg'):
        fig.savefig(out / f'recall_qps_budget_curves.{extension}', dpi=160,
                    bbox_inches='tight', pad_inches=.25)
    plt.close(fig)
    return plotted_fields, str(font_path), font_name


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument('--metrics', type=Path, default=ROOT / 'analysis/final_v1/metrics.json')
    parser.add_argument('--out', type=Path, default=ROOT / 'analysis/final_v1/figures')
    args = parser.parse_args()
    os.sched_setaffinity(0, {14})
    require(all(os.environ.get(name) == '1' for name in NATIVE_THREADS), 'plot execution uses env1')
    metrics, out = args.metrics.resolve(), args.out.resolve()
    receipt = ROOT / 'reviews/plot_curves_execution.json'
    outputs = [out / f'recall_qps_budget_curves.{ext}' for ext in ('png', 'svg')]
    require(not receipt.exists() and all(not path.exists() for path in outputs), 'preserve plot receipt and figures')
    audit = read_json(ROOT / 'reviews/independent_result_audit/report.json')
    require(audit['status'] == 'PASS_INDEPENDENT_80_POINT_INTEGER_WALL_TRACE_AUDIT', 'independent result audit must finish first')
    binding = audit['source_sha256_and_stat4'].get(str(metrics))
    require(binding is not None and binding['stat4'] == stat4(metrics), 'selected metrics are the actually audited file')
    protected = protect_existing(audit)
    protected[str(metrics)] = stat4(metrics)
    points = read_points(metrics)
    fields, font_path, font_name = draw(points, out)
    require(all(stat4(path) == before for path, before in protected.items()), 'all existing protected files unchanged')
    result = {'status': 'PASS_E175_80_POINT_PRECOMPUTED_BUDGET_CURVES',
              'source': str(Path(__file__).resolve()), 'source_sha256': sha(__file__),
              'metrics': str(metrics), 'metrics_audited_sha256_and_stat4': binding,
              'plotted_point_count': len(fields), 'panels': 4, 'points_per_panel': 20,
              'saved_point_fields_exactly_equal': True, 'plotted_point_fields': fields,
              'x_field': 'recall_pct', 'y_field': 'qps_median',
              'y_range_fields': ['qps_min', 'qps_max'], 'L': list(L_VALUES),
              'curve_connection': 'measured L points only, in ascending L; no fitting, smoothing or jitter',
              'font_path': font_path, 'font_family': font_name,
              'outputs': {str(path): {'sha256': sha(path), 'stat4': stat4(path)} for path in outputs},
              'protected_existing_file_count': len(protected),
              'protected_existing_stat4_unchanged': protected,
              'CPU_affinity': sorted(os.sched_getaffinity(0)),
              'thread_env': {name: os.environ[name] for name in NATIVE_THREADS},
              'TRAIN_increment_seconds': 0,
              'scope': 'presentation of audited precomputed points only; no query, GT, fit, bootstrap or new quality gate'}
    result['elapsed_seconds'] = time.monotonic() - started
    receipt.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'status': result['status'], 'points': len(fields),
                      'elapsed_seconds': result['elapsed_seconds'], 'outputs': [str(path) for path in outputs]}))


if __name__ == '__main__':
    main()
