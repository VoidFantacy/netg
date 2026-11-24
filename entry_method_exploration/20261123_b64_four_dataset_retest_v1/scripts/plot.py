"""Render the three requested methods on four aligned dataset panels."""
import csv
from pathlib import Path

from matplotlib import pyplot as plt, ticker
from matplotlib.font_manager import FontProperties

from drive import DATASETS, NAMES, ROOT

fonts = Path("/usr/share/fonts/opentype/noto")
regular = FontProperties(fname=fonts / "NotoSansCJK-Regular.ttc")
bold = FontProperties(fname=fonts / "NotoSansCJK-Bold.ttc")
legend_font = FontProperties(fname=regular.get_file(), size=10)
ink, faded = "#162a41", "#536b81"
palette = (
    ("B32", "B32", "#146b85", "o"),
    ("B64-old", "老 B64", "#b54936", "D"),
    ("Mixed64", "新 B64", "#247256", "^"),
)

with (ROOT / "analysis/points.csv").open() as file:
    rows = list(csv.DictReader(file))

for k in (1, 100):
    fig, axs = plt.subplots(2, 2, figsize=(13.2, 8.3), facecolor="#f4f7fa")
    fig.subplots_adjust(left=.082, right=.965, top=.815, bottom=.09, hspace=.47, wspace=.25)
    fig.text(.082, .947, f"四集 Recall@{k}–QPS 同期复测", color=ink, fontproperties=bold, fontsize=24)
    fig.text(.082, .894, f"真实 K{k} · 每集 3,072 条查询 · CPU15 单线程完整计时 · 每点两遍均值",
             color=faded, fontproperties=regular, fontsize=11)
    fig.legend([plt.Line2D([], [], marker=marker, color=color, linewidth=2, markersize=6)
                for _, _, color, marker in palette], [label for _, label, _, _ in palette],
               loc="upper right", bbox_to_anchor=(.971,.897), ncol=3, frameon=False,
               labelcolor=ink, prop=legend_font, columnspacing=1.15, handlelength=2.1)
    for ax, ds in zip(axs.flat, DATASETS):
        ax.set_title(NAMES[ds], loc="left", color=ink, fontproperties=bold, fontsize=14, pad=7)
        panel = [p for p in rows if p["dataset"] == ds and int(p["K"]) == k]
        ax.set_axisbelow(True)
        ax.grid(color="#dce6ee", linewidth=.9)
        ax.tick_params(colors=faded, labelsize=9, length=0, pad=6)
        for side in ax.spines.values():
            side.set_color("#cdd9e5")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(5))
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("{x:,.0f}"))
        ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
        rec = [float(p["recall_pct"]) for p in panel]
        fmt = "{x:.2f}" if max(rec) - min(rec) < 5 else "{x:.1f}"
        ax.yaxis.set_major_formatter(ticker.StrMethodFormatter(fmt))
        for arm, label, color, marker in palette:
            data = sorted((p for p in panel if p["method"] == arm), key=lambda p: int(p["L"]))
            ax.plot([float(p["qps"]) for p in data], [float(p["recall_pct"]) for p in data],
                    label=label, color=color, marker=marker, linewidth=1.8,
                    markersize=4.6, markeredgecolor="white", markeredgewidth=.55, zorder=3)
        ax.set_xlabel("完整吞吐量（QPS）", color=ink, fontproperties=regular, fontsize=10, labelpad=6)
        ax.set_ylabel(f"Recall@{k}（%）", color=ink, fontproperties=regular, fontsize=10, labelpad=5)
        ax.margins(x=.055, y=.075)
    fig.savefig(ROOT / "analysis" / f"recall_qps_k{k}.png", dpi=185, facecolor=fig.get_facecolor())
    plt.close(fig)
