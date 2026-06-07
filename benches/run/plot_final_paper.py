#!/usr/bin/env python3
"""
精品图 — 使用 Recall < 0.1 阈值（相对改善最大: 40%）
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

INPUT_DIR  = "per_query_recall_results_r10"
OUTPUT_DIR = "per_query_recall_plots"

SEARCH_LS = [64, 128, 200, 300, 400, 512, 800, 1024]
THRESHOLD = 0.1  # 灾难性失败定义

# Unified font scheme (shared across all paper figures, IEEE single-column 3.5 inch)
plt.rcParams.update({
    'font.size': 7,
    'axes.labelsize': 8,
    'axes.titlesize': 8,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 6.5,
    'font.family': 'serif',
    'mathtext.fontset': 'dejavuserif',
})


def load_data(dataset):
    fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
    with open(fp) as f:
        return json.load(f)


def compute_pct_below(recalls, threshold):
    return sum(1 for r in recalls if r < threshold) / len(recalls) * 100


def main():
    data = load_data("yandex_t2i")
    
    methods = {}
    for md in data["methods"]:
        methods[md["method"]] = {}
        for sr in md["search_results"]:
            methods[md["method"]][sr["search_L"]] = sr["per_query_recalls"]
    
    nsg_fail = [compute_pct_below(methods["NSG_Medoid"][L], THRESHOLD) for L in SEARCH_LS]
    netg_fail = [compute_pct_below(methods["NETG_AsymHNSW"][L], THRESHOLD) for L in SEARCH_LS]
    raw_fail = [compute_pct_below(methods["Raw_HNSW_Ablation"][L], THRESHOLD) for L in SEARCH_LS]
    
    nsg_mean = [np.mean(methods["NSG_Medoid"][L]) for L in SEARCH_LS]
    netg_mean = [np.mean(methods["NETG_AsymHNSW"][L]) for L in SEARCH_LS]
    raw_mean = [np.mean(methods["Raw_HNSW_Ablation"][L]) for L in SEARCH_LS]
    
    # ====== 图1: 组合图 (上: 失败率, 下: mean recall) — 单栏竖排压缩高度 ======
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 3.9), height_ratios=[1, 1])

    # 离散搜索预算 -> 等距索引 (避免线性轴下 64/128/200 挤成一团)
    xi = np.arange(len(SEARCH_LS))

    # (a) 灾难性失败率
    ax1.plot(xi, nsg_fail, color='#d62728', marker='s', markersize=4,
            linewidth=1.5, label='NSG (Medoid)', zorder=3)
    ax1.plot(xi, raw_fail, color='#2ca02c', marker='^', markersize=4,
            linewidth=1.2, linestyle='--', label='Raw HNSW (No Projection)', zorder=3)
    ax1.plot(xi, netg_fail, color='#1f77b4', marker='o', markersize=4,
            linewidth=1.5, label='NETG (Ours)', zorder=3)

    ax1.fill_between(xi, nsg_fail, netg_fail, alpha=0.2, color='#1f77b4')

    # 标注关键点 (跳过 L=64, 由黄框单独标注, 避免重叠)
    for i, L in enumerate(SEARCH_LS):
        if i == 0:
            continue
        if nsg_fail[i] > 1.0:
            rel = (nsg_fail[i] - netg_fail[i]) / nsg_fail[i] * 100
            if rel > 30:
                ax1.annotate(f'↓{rel:.0f}%',
                           xy=(xi[i], (nsg_fail[i] + netg_fail[i])/2),
                           xytext=(xi[i] + 0.15, (nsg_fail[i] + netg_fail[i])/2 + 0.45),
                           fontsize=6, fontweight='bold', color='#1f77b4',
                           ha='left')

    # L=64 特别标注 (放到中部空白区: legend 下方 + 低值曲线上方; 箭头指向 L=64)
    ax1.annotate('↓40% relative\nreduction',
                xy=(0, (nsg_fail[0] + netg_fail[0])/2),
                xytext=(4.7, 3.4),
                fontsize=6.5, fontweight='bold', color='#1f77b4',
                ha='center',
                arrowprops=dict(arrowstyle='->', color='#1f77b4', lw=1.0),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow',
                          edgecolor='#1f77b4', alpha=0.95))

    ax1.set_ylim(0, max(nsg_fail) * 1.25)
    ax1.set_xlabel("Search_L (Beam Pool Size)")
    ax1.set_ylabel("Tail-Failure Rate (%)")
    ax1.text(0.5, -0.30, "(a) Tail-Query Failure Rate (Recall@10 < 0.1)",
             transform=ax1.transAxes, ha='center', va='top',
             fontsize=8, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(xi)
    ax1.set_xticklabels(SEARCH_LS)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)

    # (b) Mean Recall
    ax2.plot(xi, nsg_mean, color='#d62728', marker='s', markersize=4,
            linewidth=1.5, label='NSG (Medoid)', zorder=3)
    ax2.plot(xi, raw_mean, color='#2ca02c', marker='^', markersize=4,
            linewidth=1.2, linestyle='--', label='Raw HNSW (No Projection)', zorder=3)
    ax2.plot(xi, netg_mean, color='#1f77b4', marker='o', markersize=4,
            linewidth=1.5, label='NETG (Ours)', zorder=3)

    ax2.fill_between(xi, nsg_mean, netg_mean, alpha=0.2, color='#1f77b4')

    ax2.set_xlabel("Search_L (Beam Pool Size)")
    ax2.set_ylabel("Mean Recall@10")
    ax2.text(0.5, -0.30, "(b) Mean Recall@10",
             transform=ax2.transAxes, ha='center', va='top',
             fontsize=8, fontweight='bold')
    ax2.legend(loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(xi)
    ax2.set_xticklabels(SEARCH_LS)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout(rect=[0, 0, 1, 1])
    plt.subplots_adjust(hspace=0.62)
    out = f"{OUTPUT_DIR}/paper_combo_threshold01.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    print(f"✅ {out}")
    plt.close()
    
    # ====== 图2: 柱状图 (Recall < 0.1) ======
    fig, ax = plt.subplots(1, 1, figsize=(9, 5.5))
    
    x = np.arange(len(SEARCH_LS))
    w = 0.25
    
    bars1 = ax.bar(x - w, nsg_fail, w, label='NSG (Medoid)', color='#d62728', alpha=0.85, edgecolor='white')
    bars2 = ax.bar(x, netg_fail, w, label='NETG (Ours)', color='#1f77b4', alpha=0.85, edgecolor='white')
    bars3 = ax.bar(x + w, raw_fail, w, label='Raw HNSW (No Folding)', color='#2ca02c', alpha=0.85, edgecolor='white')
    
    # 标注数值和相对改善
    for i in range(len(SEARCH_LS)):
        # NSG 数值
        ax.annotate(f'{nsg_fail[i]:.1f}%', xy=(x[i] - w, nsg_fail[i]),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#d62728')
        # NETG 数值
        ax.annotate(f'{netg_fail[i]:.1f}%', xy=(x[i], netg_fail[i]),
                   xytext=(0, 3), textcoords="offset points",
                   ha='center', va='bottom', fontsize=7.5, fontweight='bold', color='#1f77b4')
        
        # 相对改善
        if nsg_fail[i] > 0.5:
            rel = (nsg_fail[i] - netg_fail[i]) / nsg_fail[i] * 100
            y_top = max(nsg_fail[i], netg_fail[i], raw_fail[i]) + 0.8
            ax.annotate(f'↓{rel:.0f}%', xy=(x[i], y_top),
                       ha='center', fontsize=8, fontweight='bold', color='#333',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffcc', alpha=0.8))
    
    ax.set_xlabel("Search_L", fontsize=12)
    ax.set_ylabel("% of Queries with Recall@10 < 0.1\n(Catastrophic Failure)", fontsize=11)
    ax.set_title("Yandex T2I (200-d): Catastrophic Query Reduction by NETG",
                fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([str(L) for L in SEARCH_LS], fontsize=10)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(True, alpha=0.2, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/paper_bars_threshold01.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"✅ {out}")
    plt.close()
    
    # ====== 图3: 多数据集对比 (Recall < 0.1) ======
    fig, ax = plt.subplots(1, 1, figsize=(10, 5.5))
    
    datasets = ["deep10M", "sift10M", "yandex_t2i", "gist1M"]
    ds_labels = ["Deep10M", "SIFT10M", "Yandex T2I", "GIST1M"]
    target_L = 64  # 最能体现差异的 L
    
    nsg_all = []
    netg_all = []
    raw_all = []
    valid_labels = []
    
    for ds in datasets:
        try:
            d = load_data(ds)
        except:
            continue
        
        ms = {}
        for md in d["methods"]:
            ms[md["method"]] = {}
            for sr in md["search_results"]:
                ms[md["method"]][sr["search_L"]] = sr["per_query_recalls"]
        
        nsg_all.append(compute_pct_below(ms["NSG_Medoid"][target_L], THRESHOLD))
        netg_all.append(compute_pct_below(ms["NETG_AsymHNSW"][target_L], THRESHOLD))
        raw_all.append(compute_pct_below(ms["Raw_HNSW_Ablation"][target_L], THRESHOLD))
        valid_labels.append(ds_labels[datasets.index(ds)])
    
    x = np.arange(len(valid_labels))
    w = 0.25
    
    bars1 = ax.bar(x - w, nsg_all, w, label='NSG (Medoid)', color='#d62728', alpha=0.85)
    bars2 = ax.bar(x, netg_all, w, label='NETG (Ours)', color='#1f77b4', alpha=0.85)
    bars3 = ax.bar(x + w, raw_all, w, label='Raw HNSW', color='#2ca02c', alpha=0.85)
    
    for i in range(len(valid_labels)):
        if nsg_all[i] > 0.3:
            rel = (nsg_all[i] - netg_all[i]) / nsg_all[i] * 100
            y_top = max(nsg_all[i], netg_all[i], raw_all[i]) + 0.3
            ax.annotate(f'↓{rel:.0f}%', xy=(x[i], y_top),
                       ha='center', fontsize=9, fontweight='bold', color='#333',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='#ffffcc', alpha=0.8))
    
    ax.set_xlabel("Dataset", fontsize=12)
    ax.set_ylabel("% Queries with Recall@10 < 0.1", fontsize=11)
    ax.set_title(f"Catastrophic Failure Rate Across Datasets (Search_L={target_L})",
                fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(valid_labels, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.2, axis='y')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/paper_bars_all_datasets_threshold01.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"✅ {out}")
    plt.close()
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
