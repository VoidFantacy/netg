#!/usr/bin/env python3
"""
Ablation bar chart (replaces legacy xr.png).

Reads the authoritative test/yandex_t2i_results/yandex_t2i_final_report.json
and plots the 4-step progressive ablation at two search depths (L=150, 250):
    Base (Medoid) -> + ACO-Max -> + W-DPC (Multi-Hub) -> + Neural (Full NETG)

Two subplots:
    (a) Efficiency Improvement  (QPS)
    (b) Precision Improvement   (Recall@100)

Output: benches/run/xr.png (+ xr.pdf)
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # /mnt/lost+found/ACSG
REPORT = os.path.join(ROOT, "test", "yandex_t2i_results", "yandex_t2i_final_report.json")
OUT_DIR = SCRIPT_DIR

L_TARGETS = [150, 250]

# (json method_name, display label, bar color)
METHODS = [
    ("0. Medoid (Baseline)",                      "Base (Medoid)",   "#1f77b4"),
    ("1. ACO-Max (Global)",                       "+ ACO-Max",       "#ff7f0e"),
    ("2. Raw HNSW Routing (Ablation Baseline)",   "+ W-DPC (Multi)", "#2ca02c"),
    ("5. Asym-Neural HNSW Routing (0ms inference)", "+ Neural (NETG)", "#d62728"),
]
HATCHES = ["", "xx", "..", "//"]

# Font settings: sized for direct embedding at columnwidth (3.5 inch, IEEE single-column)
plt.rcParams.update({
    'font.size': 7,
    'axes.labelsize': 8,
    'axes.titlesize': 8,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'font.family': 'serif',
    'mathtext.fontset': 'dejavuserif',
})


def load_metric(report):
    """Return {method_name: {L: (qps, recall)}}."""
    out = {}
    for r in report["results"]:
        m = {}
        for p in r["performance"]:
            m[p["search_L"]] = (p["qps"], p["recall"])
        out[r["method_name"]] = m
    return out


def main():
    report = json.load(open(REPORT))
    data = load_metric(report)

    # Gather values: qps[L_idx][method_idx], recall[L_idx][method_idx]
    qps = {L: [] for L in L_TARGETS}
    rec = {L: [] for L in L_TARGETS}
    for L in L_TARGETS:
        for mname, _, _ in METHODS:
            q, r = data[mname][L]
            qps[L].append(q)
            rec[L].append(r)

    # figsize matches IEEE single-column width (3.5 inch); height trimmed to reduce whitespace
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 3.4))

    n_methods = len(METHODS)
    n_groups = len(L_TARGETS)
    group_w = 0.8
    bar_w = group_w / n_methods
    x_base = np.arange(n_groups)

    def draw(ax, values, ylabel, title, fmt, ylim=None):
        for mi, (_, label, color) in enumerate(METHODS):
            xs = x_base - group_w / 2 + bar_w * (mi + 0.5)
            heights = [values[L][mi] for L in L_TARGETS]
            bars = ax.bar(xs, heights, bar_w, label=label, color=color,
                          alpha=0.88, edgecolor="white", hatch=HATCHES[mi])
            for b, h in zip(bars, heights):
                ax.annotate(fmt(h), xy=(b.get_x() + b.get_width() / 2, h),
                            xytext=(0, 2), textcoords="offset points",
                            ha="center", va="bottom", fontsize=6, rotation=90)
        ax.set_xticks(x_base)
        ax.set_xticklabels([f"Search Depth L={L}" for L in L_TARGETS], fontsize=7)
        ax.set_ylabel(ylabel, fontsize=8)
        # subplot caption placed below the axes (IEEE caption-below convention)
        ax.text(0.5, -0.22, title, transform=ax.transAxes,
                ha="center", va="top", fontsize=8, fontweight="bold")
        ax.grid(True, alpha=0.25, axis="y")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if ylim:
            ax.set_ylim(*ylim)

    draw(ax1, qps, "Queries Per Second (QPS)", "(a) Efficiency Improvement",
         lambda h: f"{h:.1f}", ylim=(0, max(max(qps[L]) for L in L_TARGETS) * 1.22))
    # recall y-range tightened around the values for visibility
    rmin = min(min(rec[L]) for L in L_TARGETS)
    rmax = max(max(rec[L]) for L in L_TARGETS)
    pad_lo = (rmax - rmin) * 0.5 + 0.005
    pad_hi = (rmax - rmin) * 1.1 + 0.005
    draw(ax2, rec, "Recall@100", "(b) Precision Improvement",
         lambda h: f"{h:.4f}", ylim=(max(0, rmin - pad_lo), rmax + pad_hi))

    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=7,
               frameon=False, bbox_to_anchor=(0.5, 1.02))

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.subplots_adjust(hspace=0.5)
    out_pdf = os.path.join(OUT_DIR, "xr.pdf")
    out_png = os.path.join(OUT_DIR, "xr.png")
    plt.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()

    # Console summary for paper text
    print("Ablation values (Yandex T2I):")
    for L in L_TARGETS:
        print(f"  L={L}")
        for mi, (_, label, _) in enumerate(METHODS):
            print(f"    {label:18s} QPS={qps[L][mi]:8.1f}  Recall@100={rec[L][mi]:.4f}")
    print(f"\nSaved: {out_png}\n       {out_pdf}")


if __name__ == "__main__":
    main()
