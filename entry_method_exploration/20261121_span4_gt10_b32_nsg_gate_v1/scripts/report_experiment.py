"""Render the measured curves and a report from the audited tables."""
from collections import Counter
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator

from run_experiment import DATASETS, MATRIX, N, ROOT, read, write
from score_experiment import B32, DATASET_NAMES, GATE, NSG, PRIMARY, SCALAR, TARGETS

LABEL = {NSG: "NSG 单入口 + SPAN4", B32: "GT10 + B32 + SPAN4", GATE: "GATE + SPAN4", SCALAR: "GATE 标量"}
STYLE = {NSG: ("#526981", "o"), B32: ("#007e73", "D"), GATE: ("#b25133", "^")}


def load(name):
    with (ROOT / "analysis" / (name + ".csv")).open(newline="") as handle:
        return list(csv.DictReader(handle))


def curve(points, k):
    regular = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    bold = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
    for font in (regular, bold):
        font_manager.fontManager.addfont(font)
    family = font_manager.FontProperties(fname=regular).get_name()
    plt.rcParams.update({"font.family": family, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for axis, ds in zip(axes.flat, DATASETS):
        for method in PRIMARY:
            group = [points[ds, k, l, method] for kk, l in MATRIX if kk == k]
            x, y = ([float(p[field]) for p in group] for field in ("recall_pct", "qps"))
            err = [[q - float(p["qps_min"]) for q, p in zip(y, group)],
                   [float(p["qps_max"]) - q for q, p in zip(y, group)]]
            color, marker = STYLE[method]
            axis.errorbar(x, y, yerr=err, color=color, marker=marker, markersize=5,
                          linewidth=1.7, capsize=2, label=LABEL[method])
        axis.set_title(DATASET_NAMES[ds], loc="left", weight="bold", fontsize=13)
        axis.set_xlabel(f"Recall@{k}（%）")
        axis.set_ylabel("端到端 QPS")
        axis.xaxis.set_major_locator(MaxNLocator(6))
        axis.ticklabel_format(style="plain", axis="x", useOffset=False)
        axis.set_axisbelow(True)
        axis.grid(color="#dfe7ef", linewidth=.65)
    fig.suptitle(f"四个数据集的 Recall@{k}–QPS", x=.085, y=.98, ha="left", fontsize=20, weight="bold")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(.075, .925), ncol=3, frameon=False)
    ls = " / ".join(str(l) for kk, l in MATRIX if kk == k)
    fig.text(.085, .020, f"每集 3,072 条，CPU15 单线程，每点两遍。L 为 {ls}。竖线表示两遍范围。",
             fontsize=9, color="#435269")
    fig.subplots_adjust(left=.086, right=.975, top=.82, bottom=.105, wspace=.27, hspace=.44)
    for ext in ("png", "svg"):
        fig.savefig(ROOT / f"analysis/recall_qps_k{k}.{ext}", dpi=180, facecolor="white")
    plt.close(fig)


def evaluate(points, pairs, targets, frontier):
    summary = {"same_l": {}, "highest_qps_at_target": {}, "gate_speedup_by_dataset": {}, "frontier": {}}
    for trial, ref in ((B32, NSG), (B32, GATE), (GATE, SCALAR)):
        rows = [r for r in pairs if (r["method"], r["baseline"]) == (trial, ref)]
        differences = [(float(r["recall_delta_pp"]), float(r["qps_delta_pct"])) for r in rows]
        summary["same_l"][f"{trial}/{ref}"] = {
            "pairs": len(rows), "recall_higher": sum(dr > 0 for dr, _ in differences),
            "qps_higher": sum(dq > 0 for _, dq in differences),
            "both_higher": sum(dr > 0 and dq > 0 for dr, dq in differences),
            "recall_delta_pp": [min(dr for dr, _ in differences), max(dr for dr, _ in differences)],
            "qps_delta_pct": [min(dq for _, dq in differences), max(dq for _, dq in differences)],
            "slower_repeat_above_reference_faster_repeat": sum(float(r["slow_new_vs_fast_old_pct"]) > 0 for r in rows)}
    for ds in DATASETS:
        fastest = Counter(r["method"] for r in targets if r["dataset"] == ds and r["fastest_span4"] == "True")
        summary["highest_qps_at_target"][ds] = {m: fastest[m] for m in PRIMARY}
        deltas = [float(r["qps_delta_pct"]) for r in pairs if
                  (r["dataset"], r["method"], r["baseline"]) == (ds, GATE, SCALAR)]
        assert len(deltas) == 14
        summary["gate_speedup_by_dataset"][ds] = [min(deltas), max(deltas)]
    for method in PRIMARY:
        active = [r for r in frontier if r["method"] == method]
        summary["frontier"][method] = {
            "points": len(active), "on_frontier": sum(r["on_frontier"] == "True" for r in active),
            "covered_by_other_method": sum(any(r[f"covered_by_{ref}"] == "True" for ref in PRIMARY if ref != method)
                                           for r in active)}
    summary["L200"] = [points[ds, k, 200, m] for ds in DATASETS for k in (1, 100) for m in PRIMARY]
    return summary


def recall_qps(p):
    return f"{float(p['recall_pct']):.3f}% / {float(p['qps']):,.1f}"


def fmt_range(pair, suffix="%"):
    return f"{pair[0]:+.2f}{suffix} 至 {pair[1]:+.2f}{suffix}"


def report(points, targets, stats):
    txt = ["# E213 四集 GT10+B32、NSG 与 GATE 同期实测", "",
        "COCO、Flickr30k、WebVid、Yandex first10M 各使用 3,072 条公开查询。真实 K1/K100 各 7 档 L，"
        "CPU15 实际单线程，每点两遍完整计时。三条 SPAN4 链路共 168 点、336 批。"
        "GATE 标量对照另有 56 点、112 批。QPS 为两遍 N/wall 的算术平均。", "",
        "E200 的 GATE 运行单位 query 的小 HNSW 路由，取三个真实入口后用原 raw query 搜索同一张 NSG 图。"
        "独立探针在四集、两种 K 的 L200 再现 GATE 主搜索调用 Faiss batch4，标量臂的调用为零。"
        "正式二进制未链接探针。GATE 两个后端的 56 组返回逐字节一致。", "",
        "## 同 L 结果", "",
        "| 对照 | Recall 更高 | QPS 更高 | 两项同时提高 | Recall 变化（百分点） | QPS 变化 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for trial, ref in ((B32, NSG), (B32, GATE), (GATE, SCALAR)):
        p = stats["same_l"][f"{trial}/{ref}"]
        n = p["pairs"]
        txt.append(f"| {LABEL[trial]} 相对 {LABEL[ref]} | {p['recall_higher']}/{n} | {p['qps_higher']}/{n} | "
                   f"{p['both_higher']}/{n} | {fmt_range(p['recall_delta_pp'], '')} | {fmt_range(p['qps_delta_pct'])} |")
    txt.extend(["", "以下为 L200 的实际召回与端到端 QPS。", "",
        "| 数据集 | K | NSG 单入口 | GT10 + B32 | GATE |", "| --- | ---: | ---: | ---: | ---: |"])
    for ds in DATASETS:
        for k in (1, 100):
            cells = " | ".join(recall_qps(points[ds, k, 200, arm]) for arm in PRIMARY)
            txt.append(f"| {DATASET_NAMES[ds]} | {k} | {cells} |")
    txt.extend(["", "![四集 Recall@1–QPS](analysis/recall_qps_k1.png)", "",
                "![四集 Recall@100–QPS](analysis/recall_qps_k100.png)", "",
        "## 最快的实测达标配置", "",
        "每格为 L / 实际 Recall / QPS。粗体为三条 SPAN4 链路中最快的达标点，破折号表示本次网格无达标点。", "",
        "| 数据集 | K | 目标 Recall | NSG 单入口 | GT10 + B32 | GATE |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    indexed = {(r["dataset"], int(r["K"]), int(r["target_pct"]), r["method"]): r for r in targets}
    for (ds, k), goals in TARGETS.items():
        for goal in goals:
            cells = []
            for method in PRIMARY:
                r = indexed[ds, k, goal, method]
                cell = f"L{r['L']} / {recall_qps(r)}" if r["L"] else "—"
                cells.append(f"**{cell}**" if r["fastest_span4"] == "True" else cell)
            txt.append(f"| {DATASET_NAMES[ds]} | {k} | {goal}% | " + " | ".join(cells) + " |")
    txt.extend(["", "三条链路各有 56 个点。在同数据集、同 K 的实测网格中，"
        "以下统计被其他链路同时达到或超过 Recall 与 QPS、且至少一项更高的点。", "",
        "| 链路 | 被其他链路覆盖 | 在实测前沿 |", "| --- | ---: | ---: |"])
    for arm in PRIMARY:
        counts = stats["frontier"][arm]
        txt.append(f"| {LABEL[arm]} | {counts['covered_by_other_method']}/56 | {counts['on_frontier']}/56 |")
    txt.extend(["", "## GATE 的后端差异", "",
        "| 数据集 | 同 K/L 的 GATE SPAN4 相对标量 QPS 变化 |", "| --- | ---: |"])
    for ds in DATASETS:
        txt.append(f"| {DATASET_NAMES[ds]} | {fmt_range(stats['gate_speedup_by_dataset'][ds])} |")
    gate = stats["same_l"][f"{GATE}/{SCALAR}"]
    txt.extend(["", f"56 个同配置对照中，{gate['slower_repeat_above_reference_faster_repeat']} 个的 SPAN4 慢遍"
        "仍比标量快遍更快。两遍范围只描述此次计时波动。", "",
        "## K100 低召回", "",
        f"L200 下每集 {N:,} 条。命中 0–9 个 GT 的查询计入下表。", "",
        "| 数据集 | NSG 单入口 | GT10 + B32 | GATE |", "| --- | ---: | ---: | ---: |"])
    for ds in DATASETS:
        counts = " | ".join(points[ds, 100, 200, m]["low_recall"] for m in PRIMARY)
        txt.append(f"| {DATASET_NAMES[ds]} | {counts} |")
    txt.extend(["", "## 核验与计量", "",
        "计时包含完整查询链路、六数组复制和正常销毁。载入、预热、GT 评分、核验、写盘在 wall 外。"
        "沿用冻结的画像和表，训练监督规模和离线成本沿 E200/E212 的合同。公共查询早已用于项目性能评测，"
        "门槛和前沿的结论限于本次实测窗口与预算点。", "",
        "NSG 与 GT10+B32 的 112 个实际包和 E212 逐字节一致，GATE 的 52 个可对齐实际包"
        "和 E200 的对应前缀一致。两套实现从正式的实际 ID 与 GT 重算全部 224 个召回点，核对 448 个正式 wall、"
        "同 L 比较、离散达标点和三条主链的有限前沿。", "",
        "[协议](protocol.md) · [逐点 CSV](analysis/points.csv) · [原始批次 CSV](analysis/rounds.csv) · "
        "[同 L 比较](analysis/same_l.csv) · [门槛](analysis/recall_thresholds.csv) · [前沿](analysis/frontier.csv) · "
        "[独立复算](reviews/independent_audit.json) · [封存](seal.json)"])
    return "\n".join(txt) + "\n"


def main():
    assert read(ROOT / "reviews/independent_audit.json")["status"] == "PASS_E213_STDLIB_AUDIT"
    points = {(r["dataset"], int(r["K"]), int(r["L"]), r["method"]): r for r in load("points")}
    pairs, targets, frontier = map(load, ("same_l", "recall_thresholds", "frontier"))
    stats = evaluate(points, pairs, targets, frontier)
    write(ROOT / "analysis/conclusions.json", stats)
    for k in (1, 100):
        curve(points, k)
    with (ROOT / "report.md").open("x") as out:
        out.write(report(points, targets, stats))


if __name__ == "__main__":
    main()
