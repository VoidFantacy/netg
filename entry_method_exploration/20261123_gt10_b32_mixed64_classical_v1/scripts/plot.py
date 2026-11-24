"""Plot the three full-wall curves for each real K on the fixed L2 datasets."""
import csv
from pathlib import Path

from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D

from drive import DATASETS, NAMES, ROOT

fonts = Path("/usr/share/fonts/opentype/noto")
regular = FontProperties(fname=fonts / "NotoSansCJK-Regular.ttc")
bold = FontProperties(fname=fonts / "NotoSansCJK-Bold.ttc")
legend_font = FontProperties(fname=regular.get_file(), size=11)
ink, faded = "#172535", "#4f6171"
style = {
    "GT10": dict(label="GT10", color="#263f54", marker="o", linestyle="--", linewidth=1.8),
    "B32": dict(label="GT10+B32", color="#1c67a5", marker="s", linestyle="-.", linewidth=1.7),
    "Mixed64": dict(label="GT10+新 B64", color="#b14e24", marker="^", linestyle="-", linewidth=1.7),
}

with (ROOT / "analysis/points.csv").open() as file:
    rows = list(csv.DictReader(file))

for k in (1, 100):
    fig, axes = plt.subplots(1, 3, figsize=(14.4, 5.15), facecolor="#f4f7f9")
    fig.subplots_adjust(left=.065, right=.978, top=.735, bottom=.157, wspace=.29)
    fig.text(.065, .915, f"三套经典 L2 数据的 Recall@{k}–QPS 对比",
             color=ink, fontproperties=bold, fontsize=22)
    fig.text(.065, .833, f"真 K={k} · CPU15 单线程 · 每点两次完整计时取 QPS 均值",
             color=faded, fontproperties=regular, fontsize=11)
    fig.legend(handles=[Line2D([], [], **line) for line in style.values()], loc="upper right",
               bbox_to_anchor=(.981,.882), ncol=3, frameon=False, prop=legend_font, handlelength=2.7, columnspacing=1.1)
    for ax, ds in zip(axes, DATASETS):
        data = [p for p in rows if p["dataset"] == ds and int(p["K"]) == k]
        n = int(data[0]["queries"])
        ax.set_title(f"{NAMES[ds]}  ·  {n:,} 条查询", loc="left", color=ink, fontproperties=bold,
                     fontsize=12, pad=9)
        # Stagger only the visible markers to keep very close curves legible.
        for i, (arm, line) in enumerate(style.items()):
            panel = sorted((p for p in data if p["method"] == arm), key=lambda p: int(p["L"]))
            ax.plot([float(p["qps"]) for p in panel], [float(p["recall_pct"]) for p in panel], **line,
                    markevery=(i, 3), markersize=4.9, markeredgecolor="white", markeredgewidth=.57, zorder=5-i)
        ax.set_xscale("log")
        ax.xaxis.set_major_locator(ticker.LogLocator(base=10, subs=(1, 2, 5)))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        ax.xaxis.set_minor_formatter(ticker.NullFormatter())
        ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
        ax.set_axisbelow(True)
        ax.grid(color="#d9e3ea", linewidth=.8)
        ax.tick_params(colors=faded, labelsize=9, length=0, pad=6)
        for spine in ax.spines.values():
            spine.set_color("#c4d4df")
        ax.set_xlabel("完整吞吐量（QPS，对数刻度）", color=ink, fontproperties=regular, fontsize=10, labelpad=6)
        ax.set_ylabel(f"Recall@{k}（%）", color=ink, fontproperties=regular, fontsize=10, labelpad=5)
        ax.margins(x=.08, y=.10)
        ax.set_ylim(top=min(100, ax.get_ylim()[1]))
    fig.savefig(ROOT / "analysis" / f"recall_qps_k{k}.png", dpi=190, facecolor=fig.get_facecolor())
    plt.close(fig)
