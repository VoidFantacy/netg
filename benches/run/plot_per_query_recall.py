#!/usr/bin/env python3
"""
Per-Query Recall CDF Distribution Plot
生成 NSG vs NETG 的累积分布函数对比图，直观展示几何迷失的解决效果
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import os

# 配置
INPUT_DIR = "per_query_recall_results_r10"
OUTPUT_DIR = "per_query_recall_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
DATASET_LABELS = {
    "deep10M": "Deep10M (96-d)",
    "sift10M": "SIFT10M (128-d)", 
    "sift10M_skewed": "SIFT10M-Skewed (128-d)",
    "yandex_t2i": "Yandex T2I (200-d)",
    "gist1M": "GIST1M (960-d)"
}

METHOD_STYLES = {
    "NSG_Medoid": {"color": "#d62728", "linestyle": "-", "label": "NSG (Medoid)"},
    "NETG_AsymHNSW": {"color": "#1f77b4", "linestyle": "-", "label": "NETG (Ours)"},
    "Raw_HNSW_Ablation": {"color": "#2ca02c", "linestyle": "--", "label": "Raw HNSW (Ablation)"},
}

# 重点展示的 Search_L 值
HIGHLIGHT_LS = [64, 128, 200, 512]


def plot_cdf_single(dataset, search_L, data, ax):
    """在单个 axes 上画某个数据集某个 L 的 CDF 对比"""
    for method_data in data["methods"]:
        method = method_data["method"]
        if method not in METHOD_STYLES:
            continue
        style = METHOD_STYLES[method]
        
        for sr in method_data["search_results"]:
            if sr["search_L"] == search_L:
                recalls = np.array(sr["per_query_recalls"])
                sorted_recalls = np.sort(recalls)
                cdf = np.arange(1, len(sorted_recalls) + 1) / len(sorted_recalls)
                
                ax.plot(sorted_recalls, cdf, 
                       color=style["color"], 
                       linestyle=style["linestyle"],
                       linewidth=2.0,
                       label=f"{style['label']} (mean={sr['mean_recall']:.4f})")
                break
    
    ax.set_xlabel("Per-Query Recall@10", fontsize=11)
    ax.set_ylabel("CDF (Cumulative Fraction)", fontsize=11)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(0, 1.02)
    ax.axhline(y=0.05, color='gray', linestyle=':', alpha=0.5, linewidth=0.8)
    ax.axhline(y=0.10, color='gray', linestyle=':', alpha=0.5, linewidth=0.8)
    ax.axvline(x=0.5, color='orange', linestyle=':', alpha=0.6, linewidth=1.0)
    ax.axvline(x=0.8, color='red', linestyle=':', alpha=0.4, linewidth=1.0)
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{DATASET_LABELS.get(dataset, dataset)}, L={search_L}", fontsize=12, fontweight='bold')


def plot_zoomed_tail(dataset, search_L, data, ax):
    """放大低召回尾部区域 (recall < 0.8 的区域)"""
    for method_data in data["methods"]:
        method = method_data["method"]
        if method not in METHOD_STYLES:
            continue
        style = METHOD_STYLES[method]
        
        for sr in method_data["search_results"]:
            if sr["search_L"] == search_L:
                recalls = np.array(sr["per_query_recalls"])
                sorted_recalls = np.sort(recalls)
                cdf = np.arange(1, len(sorted_recalls) + 1) / len(sorted_recalls)
                
                # 只画 CDF < 0.35 的部分（尾部）
                mask = cdf <= 0.35
                if mask.sum() > 0:
                    ax.plot(sorted_recalls[mask], cdf[mask] * 100, 
                           color=style["color"], 
                           linestyle=style["linestyle"],
                           linewidth=2.5,
                           label=f"{style['label']} (<0.5: {sr['pct_below_50']:.1f}%, <0.8: {sr['pct_below_80']:.1f}%)")
                break
    
    ax.set_xlabel("Per-Query Recall@10", fontsize=11)
    ax.set_ylabel("% of Queries (Tail)", fontsize=11)
    ax.set_xlim(-0.05, 1.0)
    ax.axvline(x=0.5, color='orange', linestyle='--', alpha=0.7, linewidth=1.5, label='Recall=0.5 threshold')
    ax.axvline(x=0.8, color='red', linestyle='--', alpha=0.5, linewidth=1.5, label='Recall=0.8 threshold')
    ax.legend(fontsize=8.5, loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_title(f"{DATASET_LABELS.get(dataset, dataset)}, L={search_L} [Tail Zoom]", fontsize=11, fontweight='bold')


def main():
    print("="*60)
    print("Generating Per-Query Recall CDF Plots")
    print("="*60)
    
    # ===== Plot 1: Yandex T2I 全面展示 (主图) =====
    print("\n>>> Generating main figure: Yandex T2I...")
    fp = f"{INPUT_DIR}/yandex_t2i_per_query_recall_r10.json"
    if os.path.exists(fp):
        with open(fp) as f:
            data = json.load(f)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 11))
        fig.suptitle("Per-Query Recall@10 Distribution: Yandex T2I (200-d)\nNSG vs NETG — Geometric Myopia Analysis", 
                    fontsize=14, fontweight='bold', y=0.98)
        
        for idx, L in enumerate([64, 128, 200, 512]):
            ax = axes[idx // 2][idx % 2]
            plot_cdf_single("yandex_t2i", L, data, ax)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        out_path = f"{OUTPUT_DIR}/yandex_t2i_cdf_comparison.pdf"
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ Saved: {out_path}")
        plt.close()
        
        # Tail zoom for Yandex
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.suptitle("Low-Recall Tail Distribution (Geometric Myopia Queries): Yandex T2I", 
                    fontsize=13, fontweight='bold')
        plot_zoomed_tail("yandex_t2i", 64, data, axes[0])
        plot_zoomed_tail("yandex_t2i", 128, data, axes[1])
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        out_path = f"{OUTPUT_DIR}/yandex_t2i_tail_zoom.pdf"
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ Saved: {out_path}")
        plt.close()
    
    # ===== Plot 2: 所有数据集 L=64 对比 (综合图) =====
    print("\n>>> Generating all-datasets comparison (L=64)...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle("Per-Query Recall@10 CDF — All Datasets (Search_L=64)\nNSG (Medoid) vs NETG (Neural Routing)", 
                fontsize=14, fontweight='bold', y=0.98)
    
    for idx, dataset in enumerate(DATASETS):
        fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            data = json.load(f)
        
        row, col = idx // 3, idx % 3
        ax = axes[row][col]
        plot_cdf_single(dataset, 64, data, ax)
    
    # 隐藏空白子图
    if len(DATASETS) < 6:
        axes[1][2].set_visible(False)
    
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path = f"{OUTPUT_DIR}/all_datasets_cdf_L64.pdf"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ Saved: {out_path}")
    plt.close()
    
    # ===== Plot 3: 所有数据集 L=128 对比 =====
    print("\n>>> Generating all-datasets comparison (L=128)...")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11))
    fig.suptitle("Per-Query Recall@10 CDF — All Datasets (Search_L=128)\nNSG (Medoid) vs NETG (Neural Routing)", 
                fontsize=14, fontweight='bold', y=0.98)
    
    for idx, dataset in enumerate(DATASETS):
        fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
        if not os.path.exists(fp):
            continue
        with open(fp) as f:
            data = json.load(f)
        
        row, col = idx // 3, idx % 3
        ax = axes[row][col]
        plot_cdf_single(dataset, 128, data, ax)
    
    if len(DATASETS) < 6:
        axes[1][2].set_visible(False)
    
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    out_path = f"{OUTPUT_DIR}/all_datasets_cdf_L128.pdf"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ Saved: {out_path}")
    plt.close()
    
    # ===== Plot 4: 论文单图 - Yandex T2I L=128 精品图 =====
    print("\n>>> Generating paper-ready single figure (Yandex T2I, L=128)...")
    fp = f"{INPUT_DIR}/yandex_t2i_per_query_recall_r10.json"
    if os.path.exists(fp):
        with open(fp) as f:
            data = json.load(f)
        
        fig, ax = plt.subplots(1, 1, figsize=(7, 5))
        
        for method_data in data["methods"]:
            method = method_data["method"]
            if method not in METHOD_STYLES:
                continue
            style = METHOD_STYLES[method]
            
            for sr in method_data["search_results"]:
                if sr["search_L"] == 128:
                    recalls = np.array(sr["per_query_recalls"])
                    sorted_recalls = np.sort(recalls)
                    cdf = np.arange(1, len(sorted_recalls) + 1) / len(sorted_recalls)
                    
                    ax.plot(sorted_recalls, cdf * 100, 
                           color=style["color"], 
                           linestyle=style["linestyle"],
                           linewidth=2.5,
                           label=f"{style['label']}")
                    break
        
        # 标注关键区域
        ax.axvspan(0, 0.5, alpha=0.08, color='red', label='Catastrophic failure zone')
        ax.axvline(x=0.5, color='orange', linestyle='--', alpha=0.7, linewidth=1.5)
        ax.axvline(x=0.8, color='red', linestyle='--', alpha=0.5, linewidth=1.2)
        
        # 标注数值
        ax.annotate('NSG: 9.6% queries\nrecall < 0.5', 
                   xy=(0.35, 8.5), fontsize=9.5, color='#d62728', fontweight='bold')
        ax.annotate('NETG: 7.8% queries\nrecall < 0.5', 
                   xy=(0.35, 5.5), fontsize=9.5, color='#1f77b4', fontweight='bold')
        
        ax.set_xlabel("Per-Query Recall@10", fontsize=12)
        ax.set_ylabel("Cumulative % of Queries", fontsize=12)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, 102)
        ax.legend(fontsize=10, loc='lower right', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_title("Yandex T2I (200-d), Search_L=128, Recall@10", fontsize=12, fontweight='bold')
        
        plt.tight_layout()
        out_path = f"{OUTPUT_DIR}/paper_yandex_t2i_L128_cdf.pdf"
        plt.savefig(out_path, dpi=300, bbox_inches='tight')
        plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ Saved: {out_path}")
        plt.close()
    
    # ===== Plot 5: 柱状图 - 低召回查询占比对比 =====
    print("\n>>> Generating bar chart: low-recall query percentage...")
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    
    for plot_idx, (target_L, threshold) in enumerate([(64, 0.5), (128, 0.5)]):
        ax = axes[plot_idx]
        datasets_with_data = []
        nsg_vals = []
        netg_vals = []
        raw_vals = []
        
        for dataset in DATASETS:
            fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
            if not os.path.exists(fp):
                continue
            with open(fp) as f:
                d = json.load(f)
            
            for md in d["methods"]:
                for sr in md["search_results"]:
                    if sr["search_L"] == target_L:
                        val = sr["pct_below_50"] if threshold == 0.5 else sr["pct_below_80"]
                        if md["method"] == "NSG_Medoid":
                            nsg_vals.append(val)
                        elif md["method"] == "NETG_AsymHNSW":
                            netg_vals.append(val)
                        elif md["method"] == "Raw_HNSW_Ablation":
                            raw_vals.append(val)
                        break
            datasets_with_data.append(DATASET_LABELS.get(dataset, dataset).split(" (")[0])
        
        x = np.arange(len(datasets_with_data))
        width = 0.25
        
        bars1 = ax.bar(x - width, nsg_vals, width, label='NSG (Medoid)', color='#d62728', alpha=0.8)
        bars2 = ax.bar(x, netg_vals, width, label='NETG (Ours)', color='#1f77b4', alpha=0.8)
        bars3 = ax.bar(x + width, raw_vals, width, label='Raw HNSW', color='#2ca02c', alpha=0.8)
        
        ax.set_xlabel('Dataset', fontsize=11)
        ax.set_ylabel(f'% Queries with Recall < {threshold}', fontsize=11)
        ax.set_title(f'Catastrophic Query Rate (Search_L={target_L}, Recall@10 < {threshold})', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(datasets_with_data, rotation=15, ha='right', fontsize=9)
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 在柱子上标数值
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                h = bar.get_height()
                if h > 0.3:
                    ax.annotate(f'{h:.1f}%', xy=(bar.get_x() + bar.get_width()/2, h),
                              xytext=(0, 3), textcoords="offset points",
                              ha='center', va='bottom', fontsize=7.5)
    
    plt.tight_layout()
    out_path = f"{OUTPUT_DIR}/bar_catastrophic_queries.pdf"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_path.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ Saved: {out_path}")
    plt.close()
    
    print(f"\n{'='*60}")
    print(f"🎉 All plots generated in: {OUTPUT_DIR}/")
    print(f"{'='*60}")
    print("\nGenerated files:")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        size = os.path.getsize(f"{OUTPUT_DIR}/{f}")
        print(f"  {f} ({size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
