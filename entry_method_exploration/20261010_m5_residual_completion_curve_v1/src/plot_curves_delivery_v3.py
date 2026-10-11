#!/usr/bin/env python3
"""E176 delivery layout v3 from exact audited saved fields; originals preserved.

Only RES12 budget labels are annotated. No fitting/interpolation, query, raw GT,
distance, bootstrap, training or metric change. Scalar display offsets move text
only; point coordinates and min/max endpoints remain saved values.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
LABELS = {'webvid2_5m_light_v1': 'WebVid2.5M', 'yandex_t2i_official10M_ip_v1': 'YandexT2I'}
BUDGETS = (200, 400, 800, 1000, 1200)
MAIN = ('NSG', 'GT', 'M5', 'M5REG96', 'M5RES12')
MECHANISM = ('M5', 'M5OPT', 'REGOPT96', 'WIDE12', 'M5RES12')
STYLES = {
    'NSG': ('#2563eb', 'o', '-', 'NSG', 5.5),
    'GT': ('#d68b00', 's', '-', 'GT10', 5.5),
    'M5': ('#dc2626', '*', '-', '原 M5', 11),
    'M5REG96': ('#7c3aed', 'D', '--', 'M5REG96', 5.5),
    'M5RES12': ('#047857', '^', '-', 'M5RES12', 7.5),
    'M5OPT': ('#c66e00', 'o', ':', 'M5OPT', 5.5),
    'REGOPT96': ('#7c3aed', 'D', '--', 'REGOPT96', 5.5),
    'WIDE12': ('#0891b2', 's', '-.', 'WIDE12', 5.5),
}
FIELDS = ('role', 'dataset', 'K', 'L', 'method', 'n', 'recall_pct', 'qps_median', 'qps_min', 'qps_max', 'qps_rounds', 'wall_seconds')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def stat4(path):
    s = Path(path).stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def sha(path):
    p = Path(path)
    require(p.stat().st_size <= 64 * 1024 * 1024, 'small files only, never giant input hash')
    before = stat4(p)
    value = hashlib.sha256(p.read_bytes()).hexdigest()
    require(stat4(p) == before, 'stable file during small hash')
    return value


def load(path):
    p = Path(path)
    require(p.stat().st_size <= 64 * 1024 * 1024, 'small saved metadata only')
    return json.loads(p.read_text())


def key(point):
    return point['dataset'], point['K'], point['L'], point['method']


def save_csv(path, rows):
    with path.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(FIELDS))
        w.writeheader()
        for row in rows:
            w.writerow({k: json.dumps(v) if isinstance(v, list) else v for k, v in row.items()})


def budget_labels(ax, curve):
    # Compute text-only leader positions in display pixels, never move data.
    ax.figure.canvas.draw()
    box = ax.get_window_extent()
    ordered = sorted(curve, key=lambda p: p['qps_median'])
    positions = []
    for p in ordered:
        px, py = ax.transData.transform((p['recall_pct'], p['qps_median']))
        positions.append([p, px, py, py + 8])
    gap = 20.0
    low, high = box.y0 + 17, box.y1 - 17
    for i in range(len(positions)):
        positions[i][3] = max(low, positions[i][3], positions[i-1][3] + gap if i else low)
    if positions[-1][3] > high:
        positions[-1][3] = high
        for i in range(len(positions)-2, -1, -1):
            positions[i][3] = min(positions[i][3], positions[i+1][3]-gap)
    for p, px, py, text_y in positions:
        ax.annotate('L' + str(p['L']), xy=(p['recall_pct'], p['qps_median']),
                    xycoords='data', xytext=(-15, text_y-py), textcoords='offset pixels',
                    ha='right', va='center', fontsize=8.5, color=STYLES['M5RES12'][0],
                    bbox=dict(boxstyle='round,pad=.18', facecolor='white', edgecolor='none', alpha=.88),
                    arrowprops=dict(arrowstyle='-', linewidth=.65, color=STYLES['M5RES12'][0], alpha=.75),
                    annotation_clip=False, zorder=30)


def draw(points, methods, stem, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.lines import Line2D
    from matplotlib.ticker import ScalarFormatter
    font = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    require(font.is_file(), 'existing local Chinese font required')
    font_manager.fontManager.addfont(str(font))
    name = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams.update({'font.family': name, 'font.size': 10, 'axes.unicode_minus': False, 'svg.fonttype': 'none'})
    fig, axes = plt.subplots(2, 2, figsize=(18, 11.8))
    fig.subplots_adjust(left=.095, right=.975, bottom=.155, top=.785, wspace=.28, hspace=.42)
    drawn, panels = [], []
    for dataset_row, dataset in enumerate(DATASETS):
        for k_column, K in enumerate((1, 100)):
            ax = axes[dataset_row, k_column]
            for method in methods:
                curve = [points[(dataset, K, L, method)] for L in BUDGETS]
                color, marker, linestyle, label, marker_size = STYLES[method]
                recall = [p['recall_pct'] for p in curve]
                qps = [p['qps_median'] for p in curve]
                lo = [p['qps_median']-p['qps_min'] for p in curve]
                hi = [p['qps_max']-p['qps_median'] for p in curve]
                ax.errorbar(recall, qps, yerr=[lo, hi], color=color, marker=marker,
                            linestyle=linestyle, linewidth=1.7 if method=='M5RES12' else 1.2,
                            markersize=marker_size, elinewidth=.8, capsize=2.8, alpha=.94,
                            zorder=12 if method=='M5RES12' else 5)
                drawn.extend({k:p[k] for k in FIELDS} for p in curve)
            # Titles/axes are set once per panel, independent of method/data vars.
            panel_title = f'{LABELS[dataset]} · Recall@{K}'
            xlabel, ylabel = f'Recall@{K} (%)', '完整 wall QPS'
            ax.set_title(panel_title, fontsize=13.5, pad=14)
            ax.set_xlabel(xlabel, fontsize=11, labelpad=9)
            ax.set_ylabel(ylabel, fontsize=11, labelpad=11)
            ax.grid(True, alpha=.2, linewidth=.7)
            ax.tick_params(axis='both', labelsize=9, pad=5)
            ax.margins(x=.18, y=.12)
            formatter = ScalarFormatter(useOffset=False)
            formatter.set_scientific(False)
            ax.yaxis.set_major_formatter(formatter)
            ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
            budget_labels(ax, [points[(dataset, K, L, 'M5RES12')] for L in BUDGETS])
            panels.append({'dataset':dataset, 'K':K, 'title':ax.get_title(),
                           'xlabel':ax.get_xlabel(), 'ylabel':ax.get_ylabel(),
                           'methods':list(methods), 'point_count':len(methods)*len(BUDGETS),
                           'annotated_method':'M5RES12', 'annotated_budgets':list(BUDGETS)})
            require(ax.get_title()==panel_title and ax.get_xlabel()==xlabel and ax.get_ylabel()==ylabel,
                    'panel title/axis labels retained')
    fig.suptitle(title, fontsize=18, y=.965)
    fig.text(.5, .914, '公开已曝光 10K · 原 raw-IP · 串行单线程 · QPS 中位数与三轮 [min,max]',
             ha='center', va='center', fontsize=11)
    handles = [Line2D([], [], color=STYLES[m][0], marker=STYLES[m][1], linestyle=STYLES[m][2],
                      markersize=STYLES[m][4], linewidth=1.5, label=STYLES[m][3]) for m in methods]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5,.885), ncol=5,
               frameon=False, fontsize=11, handlelength=2.7, columnspacing=2.0)
    fig.text(.5, .080, '所有方法均用 L=200/400/800/1000/1200；图中仅标注 M5RES12 的预算。微小变化的曲线可能重叠。',
             ha='center', va='center', fontsize=10)
    fig.text(.5, .050, '连线仅连接已测工作点以便阅读，无拟合或中间 L 性能承诺；该公开窗口不构成新的独立确认。',
             ha='center', va='center', fontsize=10)
    png, svg = stem.with_suffix('.png'), stem.with_suffix('.svg')
    fig.savefig(png, dpi=160)
    fig.savefig(svg)
    plt.close(fig)
    return drawn, panels, [png, svg]


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT/'analysis/final_v1/figures_delivery_v3')
    args = parser.parse_args()
    require(args.out.is_absolute() and args.out == ROOT/'analysis/final_v1/figures_delivery_v3'
            and not args.out.exists(), 'unique v3 output; preserve prior/partial artifacts')
    state = load(ROOT/'run_state.json')
    require(state.get('active') is None and len(state['completed'])==2
            and all(j['exit_code']==0 for j in state['completed']), 'both native jobs complete')
    audit_path = ROOT/'reviews/independent_result_audit/report.json'
    audit = load(audit_path)
    require(audit['status']=='PASS_E176_INDEPENDENT_DYNAMIC_INTEGER_WALL_TRACE_AUDIT'
            and audit['point_count']==160 and audit['formal_timed_batches']==480 and audit['comparison_count']==800,
            'actual all160/480/800 independent audit required')
    metrics = ROOT/'analysis/final_v1/metrics.json'
    binding = audit['source_sha256_and_stat4'][str(metrics)]
    require(binding['sha256']==sha(metrics) and binding['stat4']==stat4(metrics), 'exact audited metrics bytes')
    measured = load(metrics)
    require(measured['status']=='COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION', 'complete saved metrics')
    points = {key(p):p for p in measured['points']}
    expected = {(ds,K,L,m) for ds in DATASETS for K in (1,100) for L in BUDGETS for m in set(MAIN)|set(MECHANISM)}
    require(len(points)==len(measured['points'])==160 and set(points)==expected, 'same full160 original input matrix')
    for p in points.values():
        require(p['role']=='public_test' and p['n']==10000 and len(p['qps_rounds'])==len(p['wall_seconds'])==3
                and all(math.isfinite(p[k]) for k in ('recall_pct','qps_median','qps_min','qps_max'))
                and 0<=p['recall_pct']<=100 and 0<p['qps_min']<=p['qps_median']<=p['qps_max'], 'saved field domains')
    original_paths = [ROOT/'src/plot_curves_v2.py', ROOT/'src/write_report.py', ROOT/'analysis/final_v1/report.md',
                      ROOT/'reviews/plot_curves_execution.json', metrics, audit_path,
                      ROOT/'protocol.md', ROOT/'parameter_lock.json', ROOT/'execution_lock.json']
    original_dir = ROOT/'analysis/final_v1/figures'
    original_paths.extend(original_dir/f'{stem}.{ext}' for stem in ('recall_qps_budget_curves','mechanism_budget_curves') for ext in ('png','svg','csv'))
    protected = {str(p):{'stat4':stat4(p),'sha256':sha(p)} for p in original_paths}
    receipt_path = ROOT/'reviews/plot_curves_delivery_v3_execution.json'
    require(not receipt_path.exists(), 'unique actual v3 inner receipt')
    source_identity = {str(Path(__file__).resolve()):sha(__file__)}
    args.out.mkdir(parents=True)
    fields, panels, outputs = [], [], []
    for stem, methods, title in [('recall_qps_budget_curves', MAIN, 'E176 · 原方法与残差条件补全'),
                                  ('mechanism_budget_curves', MECHANISM, 'E176 · 原 M5、缓存与等在线预算补全')]:
        drawn, metadata, figures = draw(points, methods, args.out/stem, title)
        require(len(drawn)==100 and len(metadata)==4, 'all100 displayed points/four complete panels')
        for r in drawn:
            require(all(r[k]==points[key(r)][k] for k in FIELDS), 'every drawn coordinate/minmax/round exactly saved')
        csv_path = args.out/(stem+'.csv')
        save_csv(csv_path, drawn)
        fields.extend(dict(figure=stem,**r) for r in drawn)
        panels.extend(dict(figure=stem,**m) for m in metadata)
        outputs.extend(figures+[csv_path])
    require(len(fields)==200 and len({key(p) for p in fields})==160, 'two100 views, same160 unique saved points')
    for path,r in protected.items():
        require(stat4(path)==r['stat4'] and sha(path)==r['sha256'], 'all original frozen figures/report/metrics preserved')
    receipt = {'status':'PASS_E176_DELIVERY_V3_SAVED_FIELD_RENDER', 'metrics':str(metrics),
               'metrics_audited_sha256_and_stat4':binding, 'input_point_count':160, 'plotted_point_count':200,
               'figure_point_counts':{'recall_qps_budget_curves':100,'mechanism_budget_curves':100},
               'plotted_saved_fields':fields,'panels':panels,'saved_point_fields_exactly_equal':True,
               'source_sha256':source_identity,'protected_original_sha256_and_stat4':protected,
               'outputs':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs},
               'elapsed_seconds':time.monotonic()-started,
               'elapsed_scope':'renderer internal wall through drawing/exports/integrity checks, before own receipt serialization; external wrapper complete lifecycle separate and non-additive',
               'source_review_scope':'new layout source reviewed separately; actual audit binds all saved input fields; original frozen renderer not changed',
               'only_annotated_method':'M5RES12','only_annotated_budgets':list(BUDGETS),
               'axes':'x=saved Recall pct,y=saved complete-wall QPS median,yerr=saved min/max',
               'originals_preserved':True,'no_new_ANN_fit_bootstrap_GT_distance':True,
               'limits':['Five real measured L only; lines visual guides, no interpolation/fit.','Every method uses identical five L; tiny changes may overlap.','Text-only leader offsets do not move points or error endpoints.','Public historically exposed10K; no new confirmation or default change.']}
    with receipt_path.open('x') as f:
        json.dump(receipt,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps({'status':receipt['status'],'plotted_point_count':200,'output_dir':str(args.out),'receipt':str(receipt_path)}))


if __name__=='__main__':main()
