"""One Mixed64 Recall–QPS curve per dataset, preserving each real timed point."""
import csv
from pathlib import Path

from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from drive import DATASETS, NAMES, ROOT

fonts = Path("/usr/share/fonts/opentype/noto")
regular = FontProperties(fname=fonts / "NotoSansCJK-Regular.ttc")
bold = FontProperties(fname=fonts / "NotoSansCJK-Bold.ttc")
ink, faded, color = "#142335", "#4f6171", "#137970"

with (ROOT / "analysis/points.csv").open() as file:
    rows = [p for p in csv.DictReader(file) if p["method"] == "Mixed64"]

for k in (1, 100):
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.75), facecolor="#f4f7f9")
    fig.subplots_adjust(left=.063, right=.976, top=.739, bottom=.164, wspace=.29)
    fig.text(.063, .907, f"新 B64（Mixed64）在经典 L2 数据上的 Recall@{k}–QPS",
             color=ink, fontproperties=bold, fontsize=21)
    fig.text(.063, .82, f"真实 K={k} · CPU15 单线程完整计时 · 每点两遍 QPS 取均值",
             color=faded, fontproperties=regular, fontsize=11)
    for ax, ds in zip(axs, DATASETS):
        panel = sorted((p for p in rows if p["dataset"] == ds and int(p["K"]) == k), key=lambda p: int(p["L"]))
        n = int(panel[0]["queries"])
        ax.set_title(f"{NAMES[ds]}  ·  {n:,} 条查询", loc="left", color=ink, fontproperties=bold,
                     fontsize=12, pad=9)
        ax.plot([float(p["qps"]) for p in panel], [float(p["recall_pct"]) for p in panel],
                color=color, marker="o", linewidth=1.8, markersize=4.6,
                markeredgecolor="white", markeredgewidth=.55, zorder=3)
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10, subs=(1, 2, 5)))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        ax.xaxis.set_minor_formatter(ticker.NullFormatter())
        ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
        ax.set_axisbelow(True)
        ax.grid(color="#dbe4ea", linewidth=.8)
        ax.tick_params(colors=faded, labelsize=9, length=0, pad=6)
        for spine in ax.spines.values():
            spine.set_color("#c4d4df")
        ax.set_xlabel("完整吞吐量（QPS，对数刻度）", color=ink, fontproperties=regular, fontsize=10, labelpad=6)
        ax.set_ylabel(f"Recall@{k}（%）", color=ink, fontproperties=regular, fontsize=10, labelpad=5)
        ax.margins(x=.085, y=.12)
        ax.set_ylim(top=min(100, ax.get_ylim()[1]))
    fig.savefig(ROOT / "analysis" / f"recall_qps_k{k}.png", dpi=175, facecolor=fig.get_facecolor())
    plt.close(fig)
