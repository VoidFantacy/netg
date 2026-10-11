#!/usr/bin/env python3
"""Additional post-result E174 comparison plots from audited saved fields only.

Only connect the two measured L points of GT10/original M5/new M5REG96 within
each role. No intermediate-L performance, curve fit, jitter, new CI/statistical
resample, experiment, training or gate is implied. The incremental plot uses
16 saved comparisons directly; it does not derive changes from point medians.
Existing source, documents, locks, state, metrics, CSV and raw stay unchanged.
"""
import argparse
import csv
import json
import math
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
DS_NAME = dict(zip(DATASETS, ("WebVid", "Yandex")))
ROLES = ("confirm_a", "confirm_b")
ROLE_NAME = {"confirm_a": "pilot a", "confirm_b": "confirm b"}
METHODS = ("GT", "M5", "M5REG96")
METHOD_NAME = {"GT": "GT10", "M5": "Original M5", "M5REG96": "M5REG96 (new)"}
COLORS = {"GT": "#6b7280", "M5": "#2563eb", "M5REG96": "#dc2626"}
ROLE_COLORS = {"confirm_a": "#2563eb", "confirm_b": "#f97316"}
L_VALUES = {DATASETS[0]: (800, 1000), DATASETS[1]: (1000, 1200)}
POINT_FIELDS = ("role", "dataset", "K", "L", "method", "n", "recall_pct",
                "qps_median", "qps_min", "qps_max")
DELTA_FIELDS = ("role", "dataset", "K", "L", "method", "reference_L", "reference",
                "paired_qps_change_pct", "recall_delta_pp")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stat4(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def load(path):
    require(path.stat().st_size <= 64 * 1024 * 1024, "refuse large payload: " + str(path))
    return json.loads(path.read_text())


def point_key(p):
    return p["role"], p["dataset"], p["K"], p["L"], p["method"]


def comparison_key(c):
    return (*point_key(c), c["reference_L"], c["reference"])


def protect_existing(audit, preflight):
    # Metadata only for all previously audited payloads and 109 registered
    # inputs; vector/GT/raw/index bytes are never opened or rehashed here.
    paths = set(audit["source_sha256_and_stat4"])
    paths.update(preflight["registered_input_files"])
    paths.update(str(ROOT / p) for p in (
        "README.md", "run_state.json", "protocol.md", "parameter_lock.json",
        "execution_lock.json", "auxiliary_lock.json", "analysis_schema.md",
        "m5_relationship.md", "theory_interpretation.md", "src/render_report.py",
        "src/render_figures_v2.py", "analysis/final_v1/report.md",
        "analysis/final_v1/metrics.json", "analysis/final_v1/points.csv",
        "analysis/final_v1/comparisons.csv", "analysis/final_v1/mechanisms.csv",
        "analysis/final_v1/figures/pilot.svg", "analysis/final_v1/figures/pilot.png",
        "analysis/final_v1/figures/confirm.svg", "analysis/final_v1/figures/confirm.png",
        "analysis/final_v1/figures_v2/pilot.svg", "analysis/final_v1/figures_v2/pilot.png",
        "analysis/final_v1/figures_v2/confirm.svg", "analysis/final_v1/figures_v2/confirm.png",
        "source_before/closing_documents/report.renderer_v1.md",
        "reviews/data_preflight.json", "reviews/independent_result_audit/report.json",
        "reviews/completion_requirements.md", "reviews/completion_audit.md",
        "reviews/completion_audit.json"))
    # Delivery review may be produced only after these new figures exist.
    # Protect it if already present, without inventing a circular prerequisite.
    paths.update(str(ROOT / p) for p in (
        "reviews/final_delivery_independent_review.md",
        "reviews/final_delivery_independent_review.json") if (ROOT / p).exists())
    repo = ROOT.parents[1]
    paths.update(str(repo / p) for p in (
        "AGENTS.md", "summary.md", "spec.md", "s-target.md", "s-experiment.md",
        "experiment_history/174_m5_residual_regions.md"))
    return {p: stat4(Path(p)) for p in sorted(paths)}


def select_saved(measured):
    require(measured["status"] == "COMPLETE_E174_FROZEN_112_POINT_EVALUATION",
            "requires completed precomputed evaluation")
    all_points = {point_key(p): p for p in measured["points"]}
    require(len(all_points) == len(measured["points"]) == 112,
            "the input is the complete 112-point matrix")
    expected = {(r, d, k, l, m) for r in ROLES for d in DATASETS
                for k in (1, 100) for l in L_VALUES[d] for m in METHODS}
    points = {k: all_points[k] for k in sorted(expected)}
    require(len(points) == 48, "48 saved main points")
    for p in points.values():
        require(p["n"] == 4096 and all(math.isfinite(p[f]) for f in
                ("recall_pct", "qps_median", "qps_min", "qps_max")) and
                0 < p["qps_min"] <= p["qps_median"] <= p["qps_max"],
                "valid already-stored point coordinates")
    expected_deltas = {(r, d, k, l, "M5REG96", l, "M5")
                       for r in ROLES for d in DATASETS for k in (1, 100)
                       for l in L_VALUES[d]}
    delta_rows = [c for c in measured["comparisons"] if comparison_key(c) in expected_deltas]
    deltas = {comparison_key(c): c for c in delta_rows}
    require(len(deltas) == len(delta_rows) == 16 and set(deltas) == expected_deltas,
            "exact 16 saved same-L comparisons against original M5")
    require(all(math.isfinite(c[f]) for c in deltas.values()
                for f in ("paired_qps_change_pct", "recall_delta_pp")),
            "valid already-stored comparison coordinates")
    return points, deltas


def write_csv(path, fields, rows):
    with path.open("x", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({name: row[name] for name in fields} for row in rows)


def setup_panel(ax, ds, K, increment=False):
    from matplotlib.ticker import ScalarFormatter
    lo, hi = L_VALUES[ds]
    ax.set_title(f"{DS_NAME[ds]} | Recall@{K} | n=4096 per point\n"
                 f"lower L={lo}: circle   |   upper L={hi}: square", fontsize=11, pad=13)
    ax.set_xlabel("Saved paired-round QPS change vs M5 (%)" if increment else
                  "Complete-wall QPS (3-round median and range)", labelpad=9)
    ax.set_ylabel("Recall change vs M5 (percentage points)" if increment else
                  f"Recall@{K} (%)", labelpad=12)
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax.ticklabel_format(axis="y", style="plain", useOffset=False)
    ax.margins(x=.10, y=.10)
    ax.grid(alpha=.2)


def save_figure(fig, out, stem):
    paths = []
    for suffix in ("svg", "png"):
        path = out / f"{stem}.{suffix}"
        kwargs = {"bbox_inches": "tight", "pad_inches": .25}
        if suffix == "svg":
            kwargs["metadata"] = {"Date": None, "Creator": "E174 measured comparison curves v1"}
        else:
            kwargs["dpi"] = 160
        fig.savefig(path, **kwargs)
        paths.append(str(path))
    return paths


def render(points, deltas, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "E174-measured-comparison-curves-v1"})
    plotted_points, plotted_deltas, artifacts = [], [], []
    for role, stem in (("confirm_a", "pilot"), ("confirm_b", "confirm")):
        fig, axes = plt.subplots(2, 2, figsize=(15, 10.5))
        fig.subplots_adjust(left=.12, right=.97, bottom=.19, top=.86,
                            wspace=.38, hspace=.50)
        for row, ds in enumerate(DATASETS):
            for col, K in enumerate((1, 100)):
                ax = axes[row, col]
                for method in METHODS:
                    pair = [points[(role, ds, K, L, method)] for L in L_VALUES[ds]]
                    # Segment joins only these two actually measured endpoints.
                    ax.plot([p["qps_median"] for p in pair],
                            [p["recall_pct"] for p in pair],
                            color=COLORS[method], linewidth=1.25, alpha=.70)
                    for li, p in enumerate(pair):
                        x = p["qps_median"]
                        ax.errorbar(x, p["recall_pct"],
                                    xerr=[[x - p["qps_min"]], [p["qps_max"] - x]],
                                    fmt="o" if li == 0 else "s", linestyle="none",
                                    color=COLORS[method], markersize=6 if method=="M5REG96" else 5,
                                    capsize=3, elinewidth=1, alpha=.95)
                        plotted_points.append({f: p[f] for f in POINT_FIELDS})
                setup_panel(ax, ds, K)
        handles = [Line2D([], [], color=COLORS[m], marker="o", linewidth=1.25,
                          label=METHOD_NAME[m]) for m in METHODS]
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.545, .085),
                   ncol=3, fontsize=11, frameon=False, columnspacing=3)
        fig.suptitle(f"E174 {ROLE_NAME[role]} | matched GT10, original M5 and new M5REG96",
                     fontsize=15, y=.97)
        fig.text(.545, .033,
                 "Connecting measured points only; no intermediate-L performance implied.\n"
                 "Bars: observed min-max QPS over 3 complete-wall rounds. "
                 "No curve fit or jitter.", ha="center", fontsize=9, color="#475569")
        artifacts.extend(save_figure(fig, out, stem))
        plt.close(fig)
    fig, axes = plt.subplots(2, 2, figsize=(15, 10.5))
    fig.subplots_adjust(left=.12, right=.97, bottom=.19, top=.86,
                        wspace=.38, hspace=.50)
    for row, ds in enumerate(DATASETS):
        for col, K in enumerate((1, 100)):
            ax = axes[row, col]
            ax.axhline(0, color="#64748b", linewidth=.9, alpha=.7)
            ax.axvline(0, color="#64748b", linewidth=.9, alpha=.7)
            for role in ROLES:
                for li, L in enumerate(L_VALUES[ds]):
                    c = deltas[(role, ds, K, L, "M5REG96", L, "M5")]
                    ax.plot(c["paired_qps_change_pct"], c["recall_delta_pp"],
                            marker="o" if li == 0 else "s", linestyle="none",
                            color=ROLE_COLORS[role], markersize=7)
                    plotted_deltas.append({f: c[f] for f in DELTA_FIELDS})
            setup_panel(ax, ds, K, increment=True)
    handles = [Line2D([], [], color=ROLE_COLORS[r], marker="o", linestyle="none",
                      label=ROLE_NAME[r]) for r in ROLES]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.545, .085),
               ncol=2, fontsize=11, frameon=False, columnspacing=3)
    fig.suptitle("E174 M5REG96 incremental change vs original M5 | same L",
                 fontsize=15, y=.97)
    fig.text(.545, .033,
             "16 saved comparisons; zero axes denote original M5. No new ratio or CI calculation.\n"
             "QPS change: saved median paired-round change; not the ratio of plotted QPS medians.",
             ha="center", fontsize=9, color="#475569")
    artifacts.extend(save_figure(fig, out, "increment_vs_m5"))
    plt.close(fig)
    require(len(plotted_points)==48 and {point_key(p) for p in plotted_points}==set(points),
            "all 48 main points plotted once")
    require(len(plotted_deltas)==16 and {comparison_key(c) for c in plotted_deltas}==set(deltas),
            "all 16 saved primary comparisons plotted once")
    return plotted_points, plotted_deltas, artifacts


def write_readme(out, metrics_binding):
    text = f"""# E174：新区域扩展与原方法的同条件曲线

本目录是用户在结果完成后新增的展示需求，只读取已独审的预计算metrics字段；没有新实验、训练、GT、统计重采样或策略门。现有report、README、history、科学源/锁、metrics/CSV/raw与首版图均未修改。

- [pilot图](pilot.png)（[SVG](pilot.svg)）：confirm_a，每点4096query，24个已存点。
- [confirm图](confirm.png)（[SVG](confirm.svg)）：confirm_b，每点4096query，24个已存点。
- [相对原M5的独立增量](increment_vs_m5.png)（[SVG](increment_vs_m5.svg)）：16条已存same-L比较，每panel是a/b×两L共4点。
- [48点字段摘录](points48.csv)、[16比较字段摘录](saved_comparisons16.csv)、[原最终报告](../report.md)、[独立结果审计](../../../reviews/independent_result_audit/report.json)、[本次绘图执行收据](../../../reviews/comparison_curves_execution.json)。

GT图例写作GT10（WebVid为GT10-soft-t1，Yandex为GT10-hard）；蓝色原M5，红色新M5REG96。这里的“之前方法”都是在本轮同角色、同K/L、同计时条件下重跑的matched对照，未拼接E173旧公共test 10K角色。pilot与confirm分别展示，不合并两角色。

每张主图为WebVid/Yandex×K1/K100四panel；WebVid仅L800/1000，Yandex仅L1000/1200。圆为小L，方为大L，线段只连接同方法的两档真实实测点：**Connecting measured points only; no intermediate-L performance implied.** 没有jitter、曲线拟合、中间L性能、预算插值或新Recall区间。主图横坐标使用原`qps_median`，横误差条是原`qps_min`/`qps_max`三轮范围；纵坐标是原`recall_pct`。

差值图直接使用已有`comparisons.paired_qps_change_pct`和`recall_delta_pp`。ΔQPS是三轮按序速度比的中位数变化，**不能理解为主曲线两个QPS中位数的比**；ΔRecall单位为百分点。蓝色pilot a、橙色confirm b，零轴为原M5参照，圆/方仍对应各dataset的小/大L。没有重新计算ratio、CI或门。

本轮已报告的主M5REG96/原M5同L16点是14点Recall增、2点平，配对QPS中位变化全部下降；差值图让小质量增量及其速度代价更容易看清。WebVid K1确认b跨L有观测双升，但pilot a对应Recall差为负，且b原M5在同一小L已具备对大L GT的观测双升；整个跨档速度优势不能归给区域扩展。原协议主双升门与更严格报告门均0：停止本冻结区域版，保留原M5研究与GT10默认，具体值和归因见原报告。

图只展示已测离散点及保存的描述量，不是总体/同时显著性检验。仅连接两端也不证明中间曲线、单调性或其它budget收益。表外候选/救回不直接证明跨模态泛化；NDC仅固定256query，与full4096返回/trace范围分开。各审计范围、CI未独立重生、监控partial-speed与callback UNRESOLVED限制继续以原报告/历史说明为准。

实际metrics身份来自独审登记：SHA256 `{metrics_binding['sha256']}`，stat4 `{metrics_binding['stat4']}`。本脚本要求当前metrics的绝对路径与stat4匹配该登记，复用已审SHA，不重新hashGT、raw、base、图或模型。执行前后对所有1193个独审登记文件、109项原注册输入的并集及当前交付文档/旧图做metadata保全检查，具体覆盖范围与费用以执行收据为准；不把metadata检查扩大为重新全内容hash。
"""
    (out / "README.md").write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=ROOT / "analysis/final_v1/metrics.json")
    args = parser.parse_args()
    started = time.perf_counter()
    metrics = args.metrics.resolve()
    audit = load(ROOT / "reviews/independent_result_audit/report.json")
    require(audit["status"]=="PASS_INDEPENDENT_112_POINT_INTEGER_WALL_TRACE_AUDIT",
            "existing independent audit must pass")
    binding = audit["source_sha256_and_stat4"].get(str(metrics))
    require(binding is not None and binding["stat4"]==stat4(metrics),
            "selected metrics must be the actually audited registered file")
    preflight = load(ROOT / "reviews/data_preflight.json")
    protected = protect_existing(audit, preflight)
    measured = load(metrics)
    points, deltas = select_saved(measured)
    out = ROOT / "analysis/final_v1/comparison_curves_v1"
    out.mkdir(exist_ok=False)
    plotted_points, plotted_deltas, artifacts = render(points, deltas, out)
    write_csv(out / "points48.csv", POINT_FIELDS, plotted_points)
    write_csv(out / "saved_comparisons16.csv", DELTA_FIELDS, plotted_deltas)
    write_readme(out, binding)
    require(all(stat4(Path(p))==s for p,s in protected.items()),
            "all existing registered files/current documents must remain unchanged")
    print(json.dumps({
        "status":"PASS_POSTRESULT_MEASURED_COMPARISON_CURVES_V1",
        "scope":"Additional presentation only; no new experiment, training, statistics or gate",
        "metrics":str(metrics), "metrics_audited_sha256_and_stat4":binding,
        "input_matrix_points":112, "main_points":48, "saved_primary_comparisons":16,
        "plotted_points":plotted_points, "plotted_comparisons":plotted_deltas,
        "protected_registered_and_current_stat4_unchanged":protected,
        "audited_registered_file_count":len(audit["source_sha256_and_stat4"]),
        "preflight_registered_input_count":len(preflight["registered_input_files"]),
        "artifacts":artifacts+[str(out/p) for p in
                              ("points48.csv","saved_comparisons16.csv","README.md")],
        "script_elapsed_seconds":time.perf_counter()-started,
        "no_intermediate_L_performance_implied":True,
        "new_GT_or_raw_read":False, "new_TRAIN":False,
        "new_statistical_resample_or_quality_gate":False
    },ensure_ascii=False))


if __name__=="__main__":
    main()
