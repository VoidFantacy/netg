#!/usr/bin/env python3
"""
放大差异的可视化方案:
1. 失败率折线图: % queries with recall < threshold vs Search_L
2. 尾部放大 CDF
3. 差值柱状图
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import os

INPUT_DIR  = "per_query_recall_results_r10"
OUTPUT_DIR = "per_query_recall_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
DATASET_LABELS = {
    "deep10M": "Deep10M (96-d)",
    "sift10M": "SIFT10M (128-d)",
    "sift10M_skewed": "SIFT10M-Skew (128-d)",
    "yandex_t2i": "Yandex T2I (200-d)",
    "gist1M": "GIST1M (960-d)",
}

SEARCH_LS = [64, 128, 200, 300, 400, 512, 800, 1024]


def load_data(dataset):
    fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
    if not os.path.exists(fp):
        return None
    with open(fp) as f:
        return json.load(f)


def get_method_stats(data, method_name):
    """提取某方法在所有 Search_L 下的统计数据"""
    for md in data["methods"]:
        if md["method"] == method_name:
            stats = {}
            for sr in md["search_results"]:
                L = sr["search_L"]
                stats[L] = sr
            return stats
    return None


def plot1_failure_rate_lines():
    """图1: 失败率折线图 — 最直观展示差异"""
    print(">>> [1] Failure rate line chart...")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle("Geometric Myopia: Query Failure Rate vs Search Budget",
                fontsize=14, fontweight='bold', y=1.02)
    
    # 只画 Yandex T2I (效果最好) 和 GIST1M
    for ax_idx, (dataset, threshold) in enumerate([
        ("yandex_t2i", 0.5),
        ("yandex_t2i", 0.8),
    ]):
        ax = axes[ax_idx]
        data = load_data(dataset)
        if data is None:
            continue
        
        methods = [
            ("NSG_Medoid", "#d62728", "s", "-", "NSG (Medoid)"),
            ("NETG_AsymHNSW", "#1f77b4", "o", "-", "NETG (Ours)"),
            ("Raw_HNSW_Ablation", "#2ca02c", "^", "--", "Raw HNSW (Ablation)"),
        ]
        
        for method_name, color, marker, ls, label in methods:
            stats = get_method_stats(data, method_name)
            if stats is None:
                continue
            
            Ls = []
            fail_rates = []
            for L in SEARCH_LS:
                if L in stats:
                    Ls.append(L)
                    if threshold == 0.5:
                        fail_rates.append(stats[L]["pct_below_50"])
                    else:
                        fail_rates.append(stats[L]["pct_below_80"])
            
            ax.plot(Ls, fail_rates, color=color, marker=marker, markersize=7,
                   linewidth=2.2, linestyle=ls, label=label, zorder=3)
        
        ax.set_xlabel("Search_L (Search Budget)", fontsize=11)
        ax.set_ylabel(f"% Queries with Recall@10 < {threshold}", fontsize=11)
        ds_label = DATASET_LABELS.get(dataset, dataset)
        ax.set_title(f"{ds_label} — Recall < {threshold}", fontsize=12, fontweight='bold')
        ax.legend(fontsize=9.5, loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(SEARCH_LS)
        ax.set_xticklabels([str(L) for L in SEARCH_LS], rotation=45, fontsize=8.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 填充差异区域
        nsg_stats = get_method_stats(data, "NSG_Medoid")
        netg_stats = get_method_stats(data, "NETG_AsymHNSW")
        if nsg_stats and netg_stats:
            nsg_vals = []
            netg_vals = []
            valid_Ls = []
            for L in SEARCH_LS:
                if L in nsg_stats and L in netg_stats:
                    valid_Ls.append(L)
                    key = "pct_below_50" if threshold == 0.5 else "pct_below_80"
                    nsg_vals.append(nsg_stats[L][key])
                    netg_vals.append(netg_stats[L][key])
            
            ax.fill_between(valid_Ls, nsg_vals, netg_vals,
                          alpha=0.15, color='#1f77b4', label='_nolegend_')
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/failure_rate_lines_yandex.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()


def plot2_reduction_bars():
    """图2: 差值柱状图 — 直接展示 NETG 的改善量"""
    print(">>> [2] Reduction bar chart...")
    
    data = load_data("yandex_t2i")
    if data is None:
        return
    
    nsg = get_method_stats(data, "NSG_Medoid")
    netg = get_method_stats(data, "NETG_AsymHNSW")
    raw = get_method_stats(data, "Raw_HNSW_Ablation")
    
    if not nsg or not netg:
        return
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle("Yandex T2I (200-d): Reduction in Failed Queries by NETG",
                fontsize=13, fontweight='bold', y=1.01)
    
    for ax_idx, (threshold, key, title) in enumerate([
        (0.5, "pct_below_50", "Catastrophic Failures (Recall < 0.5)"),
        (0.8, "pct_below_80", "Low-Recall Queries (Recall < 0.8)"),
    ]):
        ax = axes[ax_idx]
        
        nsg_vals = [nsg[L][key] for L in SEARCH_LS]
        netg_vals = [netg[L][key] for L in SEARCH_LS]
        
        x = np.arange(len(SEARCH_LS))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, nsg_vals, width, label='NSG (Medoid)',
                       color='#d62728', alpha=0.8, edgecolor='white', linewidth=0.5)
        bars2 = ax.bar(x + width/2, netg_vals, width, label='NETG (Ours)',
                       color='#1f77b4', alpha=0.8, edgecolor='white', linewidth=0.5)
        
        # 在柱子上方标注数值
        for bar in bars1:
            h = bar.get_height()
            if h > 0.5:
                ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                          xytext=(0, 3), textcoords="offset points",
                          ha='center', va='bottom', fontsize=7.5, fontweight='bold',
                          color='#d62728')
        for bar in bars2:
            h = bar.get_height()
            if h > 0.5:
                ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                          xytext=(0, 3), textcoords="offset points",
                          ha='center', va='bottom', fontsize=7.5, fontweight='bold',
                          color='#1f77b4')
        
        # 标注相对改善
        for i, L in enumerate(SEARCH_LS):
            if nsg_vals[i] > 0.5:
                reduction_pct = (nsg_vals[i] - netg_vals[i]) / nsg_vals[i] * 100
                if reduction_pct > 3:
                    y_pos = max(nsg_vals[i], netg_vals[i]) + 1.5
                    ax.annotate(f'↓{reduction_pct:.0f}%',
                              xy=(x[i], y_pos),
                              ha='center', fontsize=7.5, color='#333',
                              fontweight='bold',
                              bbox=dict(boxstyle='round,pad=0.2',
                                       facecolor='#ffffcc', alpha=0.8))
        
        ax.set_xlabel("Search_L", fontsize=11)
        ax.set_ylabel(f"% of Queries with Recall < {threshold}", fontsize=11)
        ax.set_title(title, fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([str(L) for L in SEARCH_LS], fontsize=9)
        ax.legend(fontsize=10, loc='upper right')
        ax.grid(True, alpha=0.2, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/reduction_bars_yandex.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()


def plot3_tail_cdf_zoom():
    """图3: 尾部 CDF 放大图 — 只看 recall < 0.8 的区域"""
    print(">>> [3] Tail CDF zoom...")
    
    data = load_data("yandex_t2i")
    if data is None:
        return
    
    fig, axes = plt.subplots(1, 4, figsize=(20, 4.5))
    fig.suptitle("Yandex T2I — CDF Tail Zoom (Low-Recall Region Only)",
                fontsize=13, fontweight='bold', y=1.03)
    
    target_Ls = [64, 128, 200, 512]
    
    for ax_idx, target_L in enumerate(target_Ls):
        ax = axes[ax_idx]
        
        for md in data["methods"]:
            method = md["method"]
            if method == "Raw_HNSW_Ablation":
                color, ls, lw = '#2ca02c', '--', 1.5
            elif method == "NETG_AsymHNSW":
                color, ls, lw = '#1f77b4', '-', 2.5
            elif method == "NSG_Medoid":
                color, ls, lw = '#d62728', '-', 2.5
            else:
                continue
            
            label_map = {"NSG_Medoid": "NSG", "NETG_AsymHNSW": "NETG", "Raw_HNSW_Ablation": "Raw HNSW"}
            
            for sr in md["search_results"]:
                if sr["search_L"] == target_L:
                    recalls = np.array(sr["per_query_recalls"])
                    sorted_r = np.sort(recalls)
                    cdf = np.arange(1, len(sorted_r)+1) / len(sorted_r) * 100
                    
                    # 只画 CDF <= 30% 的部分
                    mask = cdf <= 35
                    ax.plot(sorted_r[mask], cdf[mask],
                           color=color, linestyle=ls, linewidth=lw,
                           label=f'{label_map[method]} (<0.5: {sr["pct_below_50"]:.1f}%)')
                    break
        
        ax.axvline(x=0.5, color='orange', linestyle=':', alpha=0.7, linewidth=1.5)
        ax.set_xlabel("Per-Query Recall@10", fontsize=10)
        if ax_idx == 0:
            ax.set_ylabel("Cumulative % of Queries", fontsize=10)
        ax.set_title(f"L = {target_L}", fontsize=11, fontweight='bold')
        ax.legend(fontsize=8, loc='lower right')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-0.05, 1.0)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/tail_cdf_zoom_yandex.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()


def plot4_paper_combo():
    """图4: 论文组合图 — 上面失败率折线 + 下面柱状图"""
    print(">>> [4] Paper combo figure...")
    
    data = load_data("yandex_t2i")
    if data is None:
        return
    
    nsg = get_method_stats(data, "NSG_Medoid")
    netg = get_method_stats(data, "NETG_AsymHNSW")
    raw = get_method_stats(data, "Raw_HNSW_Ablation")
    
    if not nsg or not netg:
        return
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8), height_ratios=[1, 1])
    fig.suptitle("Yandex T2I (200-d): Geometric Myopia Analysis",
                fontsize=14, fontweight='bold', y=0.98)
    
    # 上图: 失败率折线 (< 0.5)
    for method_name, color, marker, ls, label in [
        ("NSG_Medoid", "#d62728", "s", "-", "NSG (Medoid)"),
        ("NETG_AsymHNSW", "#1f77b4", "o", "-", "NETG (Ours)"),
        ("Raw_HNSW_Ablation", "#2ca02c", "^", "--", "Raw HNSW (No Folding)"),
    ]:
        stats = get_method_stats(data, method_name)
        if stats is None:
            continue
        Ls = [L for L in SEARCH_LS if L in stats]
        vals = [stats[L]["pct_below_50"] for L in Ls]
        ax1.plot(Ls, vals, color=color, marker=marker, markersize=8,
                linewidth=2.5, linestyle=ls, label=label, zorder=3)
    
    # 填充 NSG-NETG 差异
    nsg_v = [nsg[L]["pct_below_50"] for L in SEARCH_LS]
    netg_v = [netg[L]["pct_below_50"] for L in SEARCH_LS]
    ax1.fill_between(SEARCH_LS, nsg_v, netg_v, alpha=0.2, color='#1f77b4')
    
    ax1.set_xlabel("Search_L", fontsize=11)
    ax1.set_ylabel("% Queries with Recall@10 < 0.5", fontsize=11)
    ax1.set_title("(a) Catastrophic Failure Rate (Recall < 0.5)", fontsize=11, fontweight='bold')
    ax1.legend(fontsize=9.5, loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(SEARCH_LS)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # 标注关键差异
    L128_nsg = nsg[128]["pct_below_50"]
    L128_netg = netg[128]["pct_below_50"]
    reduction = (L128_nsg - L128_netg) / L128_nsg * 100
    ax1.annotate(f'↓{reduction:.0f}% relative\nreduction',
                xy=(128, (L128_nsg + L128_netg)/2),
                xytext=(250, L128_nsg + 2),
                fontsize=9, fontweight='bold', color='#1f77b4',
                arrowprops=dict(arrowstyle='->', color='#1f77b4', lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))
    
    # 下图: Mean Recall 对比
    nsg_mean = [nsg[L]["mean_recall"] for L in SEARCH_LS]
    netg_mean = [netg[L]["mean_recall"] for L in SEARCH_LS]
    raw_mean = [raw[L]["mean_recall"] for L in SEARCH_LS] if raw else None
    
    ax2.plot(SEARCH_LS, nsg_mean, color='#d62728', marker='s', markersize=8,
            linewidth=2.5, label='NSG (Medoid)', zorder=3)
    ax2.plot(SEARCH_LS, netg_mean, color='#1f77b4', marker='o', markersize=8,
            linewidth=2.5, label='NETG (Ours)', zorder=3)
    if raw_mean:
        ax2.plot(SEARCH_LS, raw_mean, color='#2ca02c', marker='^', markersize=7,
                linewidth=2, linestyle='--', label='Raw HNSW (No Folding)', zorder=3)
    
    ax2.fill_between(SEARCH_LS, nsg_mean, netg_mean, alpha=0.2, color='#1f77b4')
    
    ax2.set_xlabel("Search_L", fontsize=11)
    ax2.set_ylabel("Mean Recall@10", fontsize=11)
    ax2.set_title("(b) Mean Recall@10", fontsize=11, fontweight='bold')
    ax2.legend(fontsize=9.5, loc='lower right')
    ax2.grid(True, alpha=0.3)
    ax2.set_xticks(SEARCH_LS)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = f"{OUTPUT_DIR}/paper_combo_yandex.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()


def plot5_all_datasets_failure():
    """图5: 所有数据集的失败率折线图"""
    print(">>> [5] All datasets failure rate...")
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle("Query Failure Rate (Recall@10 < 0.5) Across All Datasets",
                fontsize=14, fontweight='bold', y=0.99)
    
    for idx, dataset in enumerate(DATASETS):
        data = load_data(dataset)
        if data is None:
            continue
        
        row, col = idx // 3, idx % 3
        ax = axes[row][col]
        
        for method_name, color, marker, ls, label in [
            ("NSG_Medoid", "#d62728", "s", "-", "NSG"),
            ("NETG_AsymHNSW", "#1f77b4", "o", "-", "NETG"),
            ("Raw_HNSW_Ablation", "#2ca02c", "^", "--", "Raw HNSW"),
        ]:
            stats = get_method_stats(data, method_name)
            if stats is None:
                continue
            Ls = [L for L in SEARCH_LS if L in stats]
            vals = [stats[L]["pct_below_50"] for L in Ls]
            ax.plot(Ls, vals, color=color, marker=marker, markersize=6,
                   linewidth=2, linestyle=ls, label=label, zorder=3)
        
        ds_label = DATASET_LABELS.get(dataset, dataset)
        ax.set_title(ds_label, fontsize=11, fontweight='bold')
        ax.set_xlabel("Search_L", fontsize=9)
        ax.set_ylabel("% Fail (Recall < 0.5)", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(SEARCH_LS)
        ax.set_xticklabels([str(L) for L in SEARCH_LS], fontsize=7, rotation=45)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    if len(DATASETS) < 6:
        axes[1][2].set_visible(False)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = f"{OUTPUT_DIR}/all_datasets_failure_rate.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()


if __name__ == "__main__":
    print("="*60)
    print("Generating Enhanced Visualizations")
    print("="*60)
    
    plot1_failure_rate_lines()
    plot2_reduction_bars()
    plot3_tail_cdf_zoom()
    plot4_paper_combo()
    plot5_all_datasets_failure()
    
    print(f"\n🎉 Done! All plots in: {OUTPUT_DIR}/")
