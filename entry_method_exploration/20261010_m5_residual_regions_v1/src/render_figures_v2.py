#!/usr/bin/env python3
"""Post-result E174 presentation layout v2; original figures remain preserved.

本脚本只改展示：从已完成的 metrics.json 读取全部112个预计算点，保持
原图的颜色、Recall、QPS median/min/max和小L圆点/大L方点；不连线、不
jitter、不修改数据。取消逐点L文字，改用面板两行标题及更宽的留白。
这不是新实验、训练、质量门或报告结论；不打开GT、raw、向量、模型或图。
只写独立 figures_v2/{pilot,confirm}.{svg,png}，不改冻结renderer或首版图。
"""
import argparse
import json
import math
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
DS_NAME = dict(zip(DATASETS, ("WebVid", "Yandex")))
ROLES = ("confirm_a", "confirm_b")
ROLE_NAME = {"confirm_a": "pilot a", "confirm_b": "confirm b"}
PILOT = ("GT", "M5", "M5REG24", "M5REG96", "M5FIRST96", "MFDIRECT",
         "MFREG96", "GEODIRECT", "GEOREG96")
CONFIRM = ("GT", "M5", "M5REG96", "MFREG96", "GEOREG96")
L_VALUES = {DATASETS[0]: (800, 1000), DATASETS[1]: (1000, 1200)}
COLORS = {"GT": "#111827", "M5": "#64748b", "M5REG96": "#dc2626",
          "M5REG24": "#f97316", "M5FIRST96": "#a16207", "MFDIRECT": "#93c5fd",
          "MFREG96": "#2563eb", "GEODIRECT": "#d8b4fe", "GEOREG96": "#7e22ce"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def stat4(path):
    s = path.stat()
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def point_key(row):
    return row["role"], row["dataset"], int(row["K"]), int(row["L"]), row["method"]


def read_points(metrics):
    require(metrics.stat().st_size < 64 * 1024 * 1024,
            "presentation renderer refuses a large payload")
    measured = json.loads(metrics.read_text())
    require(measured["status"] == "COMPLETE_E174_FROZEN_112_POINT_EVALUATION",
            "requires the completed precomputed E174 evaluation")
    points = {point_key(p): p for p in measured["points"]}
    expected = {(r, d, k, l, m) for r in ROLES for d in DATASETS
                for k in (1, 100) for l in L_VALUES[d]
                for m in (PILOT if r == "confirm_a" else CONFIRM)}
    require(len(points) == len(measured["points"]) == 112 and set(points) == expected,
            "exact 112-point matrix must be represented, without duplicates")
    for p in points.values():
        require(p["n"] == 4096, "each point represents full n=4096")
        require(all(isinstance(p[f], (int, float)) and math.isfinite(p[f])
                    for f in ("recall_pct", "qps_median", "qps_min", "qps_max")),
                "plot coordinates must be already-computed finite values")
        require(0 <= p["recall_pct"] <= 100 and
                0 < p["qps_min"] <= p["qps_median"] <= p["qps_max"],
                "observed plot coordinates and QPS ranges must be valid")
        require(len(p["qps_rounds"]) == 3, "exactly three original QPS rounds")
    return points


def render(points, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import ScalarFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "svg.hashsalt": "E174-postresult-layout-v2"})
    out.mkdir(parents=True, exist_ok=False)
    panel_counts = []
    plotted = []
    artifacts = []
    for role, stem in (("confirm_a", "pilot"), ("confirm_b", "confirm")):
        methods = PILOT if role == "confirm_a" else CONFIRM
        fig, axes = plt.subplots(2, 2, figsize=(15, 10.5))
        # Explicit outer and inter-panel space protects all labels; no point
        # annotation can collide with another point or cross the right edge.
        fig.subplots_adjust(left=.12, right=.97, bottom=.19, top=.86,
                            wspace=.38, hspace=.50)
        for row, ds in enumerate(DATASETS):
            lower, upper = L_VALUES[ds]
            for col, K in enumerate((1, 100)):
                ax = axes[row, col]
                count = 0
                for method in methods:
                    for li, L in enumerate(L_VALUES[ds]):
                        key = (role, ds, K, L, method)
                        p = points[key]
                        x = p["qps_median"]
                        # Same unmodified fields and error-bar expressions as
                        # frozen render_report.py, without labels or lines.
                        ax.errorbar(x, p["recall_pct"],
                                    xerr=[[x - p["qps_min"]], [p["qps_max"] - x]],
                                    fmt="o" if li == 0 else "s", linestyle="none",
                                    color=COLORS[method],
                                    markersize=5.5 if method == "M5REG96" else 4,
                                    capsize=2, elinewidth=.8, alpha=.95)
                        plotted.append({"key": list(key),
                                        "recall_pct": p["recall_pct"],
                                        "qps_median": x,
                                        "qps_min": p["qps_min"],
                                        "qps_max": p["qps_max"],
                                        "marker": "o" if li == 0 else "s",
                                        "color": COLORS[method]})
                        count += 1
                ax.set_title(f"{DS_NAME[ds]} | Recall@{K} | n=4096\n"
                             f"lower L={lower}: circle   |   upper L={upper}: square",
                             fontsize=11, pad=13)
                ax.set_xlabel("Complete-wall QPS (3-round median and range)", labelpad=9)
                ax.set_ylabel(f"Recall@{K} (%)", labelpad=12)
                ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
                ax.ticklabel_format(axis="y", style="plain", useOffset=False)
                ax.margins(x=.08, y=.08)
                ax.grid(alpha=.2)
                panel_counts.append({"role": role, "dataset": ds,
                                     "K": K, "plotted_points": count})
        handles = [Line2D([], [], color=COLORS[m], marker="o", linestyle="none",
                          label=m) for m in methods]
        fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.545, .062),
                   ncol=5, fontsize=10, frameon=False,
                   columnspacing=2.0, handletextpad=.6, labelspacing=.9)
        fig.suptitle(f"E174 {ROLE_NAME[role]} | all frozen measured points",
                     fontsize=15, y=.97)
        fig.text(.545, .025,
                 "Bars: observed min-max QPS across 3 complete-wall rounds. "
                 "No connecting lines or interpolation.",
                 ha="center", fontsize=9, color="#475569")
        # A tight export bounding box is an additional guard against clipped
        # labels, not a change of the plotted coordinates or axis semantics.
        for suffix in ("svg", "png"):
            path = out / f"{stem}.{suffix}"
            kwargs = {"bbox_inches": "tight", "pad_inches": .25}
            if suffix == "svg":
                kwargs["metadata"] = {"Date": None, "Creator": "E174 presentation layout v2"}
            else:
                kwargs["dpi"] = 160
            fig.savefig(path, **kwargs)
            artifacts.append(str(path))
        plt.close(fig)
    require(len(plotted) == 112 and {tuple(p["key"]) for p in plotted} == set(points),
            "each and every precomputed point was plotted exactly once")
    return plotted, panel_counts, artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path,
                        default=ROOT / "analysis/final_v1/metrics.json")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "analysis/final_v1/figures_v2")
    args = parser.parse_args()
    started = time.perf_counter()
    metrics = args.metrics.resolve()
    out = args.out.resolve()
    require(out == (ROOT / "analysis/final_v1/figures_v2").resolve(),
            "only the separate figures_v2 directory may be written")
    before = stat4(metrics)
    points = read_points(metrics)
    plotted, panel_counts, artifacts = render(points, out)
    require(stat4(metrics) == before, "metrics must remain unchanged during presentation")
    print(json.dumps({
        "status": "PASS_POSTRESULT_PRESENTATION_LAYOUT_V2",
        "scope": "展示改版；原图保留；无新实验、训练、统计重采样或质量门",
        "metrics": str(metrics), "metrics_stat4": before,
        "input_point_count": len(points), "plotted_point_count": len(plotted),
        "role_point_counts": {r: sum(p["key"][0] == r for p in plotted) for r in ROLES},
        "panel_point_counts": panel_counts, "plotted_points": plotted,
        "artifacts": artifacts, "script_elapsed_seconds": time.perf_counter() - started,
        "colors_and_coordinates_preserved": True,
        "new_experiment": False, "new_TRAIN": False, "new_quality_gate": False,
        "new_GT_or_raw_read": False, "original_figures_preserved": True
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
