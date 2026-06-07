#!/usr/bin/env python3
"""
多阈值对比: 找出 NSG vs NETG 差异最显著的 threshold
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
THRESHOLDS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def load_data(dataset):
    fp = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
    with open(fp) as f:
        return json.load(f)


def compute_pct_below(recalls, threshold):
    return sum(1 for r in recalls if r < threshold) / len(recalls) * 100


def main():
    data = load_data("yandex_t2i")
    
    # 提取各方法数据
    methods = {}
    for md in data["methods"]:
        methods[md["method"]] = {}
        for sr in md["search_results"]:
            methods[md["method"]][sr["search_L"]] = sr["per_query_recalls"]
    
    # ====== 表格: 所有阈值 x 所有 Search_L ======
    print("=" * 110)
    print("Yandex T2I: NSG vs NETG failure rate at different thresholds")
    print("=" * 110)
    
    best_threshold = None
    best_max_diff = 0
    
    for thresh in THRESHOLDS:
        print(f"\n--- Threshold: Recall < {thresh} ---")
        print(f"{'L':<8}", end="")
        print(f"{'NSG':>8} {'NETG':>8} {'Raw':>8} {'Δ(abs)':>8} {'Δ(rel%)':>9}")
        
        max_rel_diff = 0
        for L in SEARCH_LS:
            nsg_pct = compute_pct_below(methods["NSG_Medoid"][L], thresh)
            netg_pct = compute_pct_below(methods["NETG_AsymHNSW"][L], thresh)
            raw_pct = compute_pct_below(methods["Raw_HNSW_Ablation"][L], thresh)
            
            abs_diff = nsg_pct - netg_pct
            rel_diff = (abs_diff / nsg_pct * 100) if nsg_pct > 0.5 else 0
            
            print(f"L={L:<5} {nsg_pct:>7.1f}% {netg_pct:>7.1f}% {raw_pct:>7.1f}% {abs_diff:>+7.1f}% {rel_diff:>+8.1f}%")
            
            if abs_diff > 0.3:
                max_rel_diff = max(max_rel_diff, rel_diff)
        
        if max_rel_diff > best_max_diff:
            best_max_diff = max_rel_diff
            best_threshold = thresh
    
    print(f"\n{'='*60}")
    print(f"🏆 Best relative difference at threshold: Recall < {best_threshold}")
    print(f"{'='*60}")
    
    # ====== 图1: 所有阈值的最大绝对差异 ======
    fig, axes = plt.subplots(3, 3, figsize=(18, 15))
    fig.suptitle("Yandex T2I: NSG vs NETG — Failure Rate at Different Thresholds",
                fontsize=15, fontweight='bold', y=1.0)
    
    for idx, thresh in enumerate(THRESHOLDS):
        ax = axes[idx // 3][idx % 3]
        
        nsg_vals = [compute_pct_below(methods["NSG_Medoid"][L], thresh) for L in SEARCH_LS]
        netg_vals = [compute_pct_below(methods["NETG_AsymHNSW"][L], thresh) for L in SEARCH_LS]
        raw_vals = [compute_pct_below(methods["Raw_HNSW_Ablation"][L], thresh) for L in SEARCH_LS]
        
        x = np.arange(len(SEARCH_LS))
        w = 0.28
        
        ax.bar(x - w, nsg_vals, w, label='NSG', color='#d62728', alpha=0.8)
        ax.bar(x, netg_vals, w, label='NETG', color='#1f77b4', alpha=0.8)
        ax.bar(x + w, raw_vals, w, label='Raw HNSW', color='#2ca02c', alpha=0.8)
        
        # 标注差异
        for i in range(len(SEARCH_LS)):
            if nsg_vals[i] > 0.5:
                rel = (nsg_vals[i] - netg_vals[i]) / nsg_vals[i] * 100
                if abs(rel) > 3:
                    y_pos = max(nsg_vals[i], netg_vals[i]) + max(nsg_vals) * 0.03
                    ax.text(x[i], y_pos, f'↓{rel:.0f}%', ha='center', fontsize=6.5,
                           fontweight='bold', color='#333',
                           bbox=dict(boxstyle='round,pad=0.15', facecolor='#ffffcc', alpha=0.7))
        
        ax.set_title(f"Recall < {thresh}", fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([str(L) for L in SEARCH_LS], fontsize=7.5, rotation=45)
        ax.set_ylabel("% Queries", fontsize=9)
        ax.legend(fontsize=7.5)
        ax.grid(True, alpha=0.2, axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/multi_threshold_bars.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"\n✅ {out}")
    plt.close()
    
    # ====== 图2: 哪个阈值差异最大？热力图 ======
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    
    diff_matrix = np.zeros((len(THRESHOLDS), len(SEARCH_LS)))
    for i, thresh in enumerate(THRESHOLDS):
        for j, L in enumerate(SEARCH_LS):
            nsg_pct = compute_pct_below(methods["NSG_Medoid"][L], thresh)
            netg_pct = compute_pct_below(methods["NETG_AsymHNSW"][L], thresh)
            rel_diff = ((nsg_pct - netg_pct) / nsg_pct * 100) if nsg_pct > 0.5 else 0
            diff_matrix[i][j] = rel_diff
    
    im = ax.imshow(diff_matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')
    ax.set_xticks(range(len(SEARCH_LS)))
    ax.set_xticklabels([str(L) for L in SEARCH_LS])
    ax.set_yticks(range(len(THRESHOLDS)))
    ax.set_yticklabels([f'< {t}' for t in THRESHOLDS])
    ax.set_xlabel("Search_L", fontsize=12)
    ax.set_ylabel("Recall Threshold", fontsize=12)
    ax.set_title("Relative Reduction (%) in Failed Queries: NSG → NETG\n(Darker = bigger improvement)", 
                fontsize=12, fontweight='bold')
    
    # 标注数值
    for i in range(len(THRESHOLDS)):
        for j in range(len(SEARCH_LS)):
            val = diff_matrix[i][j]
            color = 'white' if val > 15 else 'black'
            ax.text(j, i, f'{val:.0f}%', ha='center', va='center', fontsize=8, 
                   fontweight='bold', color=color)
    
    plt.colorbar(im, ax=ax, label='Relative Reduction %')
    plt.tight_layout()
    out = f"{OUTPUT_DIR}/threshold_heatmap.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"✅ {out}")
    plt.close()
    
    # ====== 图3: 选最优阈值画精品图 ======
    # 找绝对差异最大的阈值
    abs_diff_by_thresh = {}
    for thresh in THRESHOLDS:
        total_abs = 0
        for L in SEARCH_LS:
            nsg_pct = compute_pct_below(methods["NSG_Medoid"][L], thresh)
            netg_pct = compute_pct_below(methods["NETG_AsymHNSW"][L], thresh)
            total_abs += (nsg_pct - netg_pct)
        abs_diff_by_thresh[thresh] = total_abs
    
    print("\n--- Total absolute difference across all L ---")
    for thresh in THRESHOLDS:
        print(f"  Recall < {thresh}: total abs diff = {abs_diff_by_thresh[thresh]:.1f}%")
    
    best_abs = max(abs_diff_by_thresh, key=abs_diff_by_thresh.get)
    print(f"\n🏆 Best absolute diff threshold: Recall < {best_abs}")


if __name__ == "__main__":
    main()
