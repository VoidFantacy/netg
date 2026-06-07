#!/usr/bin/env python3
"""
Ridgeline (Joy) Plot — Per-Query Recall Distribution
仿照 Aumüller & Ceccarello 2019 的风格
"""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from scipy.stats import gaussian_kde
import os

INPUT_DIR  = "per_query_recall_results_r10"
OUTPUT_DIR = "per_query_recall_plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
DATASET_LABELS = {
    "deep10M": "Deep10M",
    "sift10M": "SIFT10M",
    "sift10M_skewed": "SIFT10M-Skew",
    "yandex_t2i": "Yandex T2I",
    "gist1M": "GIST1M",
}

# Search_L 从小到大，从下到上堆叠
RIDGE_LS = [64, 128, 200, 300, 400, 512, 800, 1024]


def kde_smooth(data, grid, bw=0.03):
    """KDE 平滑，处理离散 recall 值"""
    if len(data) == 0:
        return np.zeros_like(grid)
    # 加微小噪声打破离散性
    jittered = np.array(data) + np.random.normal(0, 0.008, len(data))
    jittered = np.clip(jittered, 0, 1)
    try:
        kde = gaussian_kde(jittered, bw_method=bw)
        density = kde(grid)
    except:
        density = np.zeros_like(grid)
    return density


def ridgeline_single_method(dataset, method_name, data, ax, color, title):
    """为一个方法画 ridgeline plot"""
    grid = np.linspace(-0.02, 1.02, 500)
    
    method_data = None
    for md in data["methods"]:
        if md["method"] == method_name:
            method_data = md
            break
    if method_data is None:
        return
    
    n_ridges = len(RIDGE_LS)
    spacing = 1.0  # 每层间距
    
    for i, target_L in enumerate(RIDGE_LS):
        for sr in method_data["search_results"]:
            if sr["search_L"] == target_L:
                recalls = np.array(sr["per_query_recalls"])
                density = kde_smooth(recalls, grid)
                # 归一化到合适高度
                if density.max() > 0:
                    density = density / density.max() * 0.85
                
                y_base = i * spacing
                
                # 填充
                ax.fill_between(grid, y_base, y_base + density,
                               color=to_rgba(color, 0.55),
                               edgecolor=to_rgba(color, 0.9),
                               linewidth=1.2, zorder=n_ridges - i)
                # 底线
                ax.plot(grid, y_base + density,
                       color=to_rgba(color, 0.95),
                       linewidth=1.0, zorder=n_ridges - i + 1)
                
                # 标注 mean recall
                mean_r = sr["mean_recall"]
                ax.text(1.06, y_base + 0.15, f'{mean_r:.3f}',
                       fontsize=7.5, va='center', color='#333333')
                break
    
    # Y 轴标签 = search_L
    ax.set_yticks([i * spacing + 0.15 for i in range(n_ridges)])
    ax.set_yticklabels([str(L) for L in RIDGE_LS], fontsize=8.5)
    ax.set_ylabel("Search_L", fontsize=11)
    ax.set_xlabel("Per-Query Recall@10", fontsize=11)
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(-0.3, n_ridges * spacing + 0.5)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    
    # 去掉上右边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)


def ridgeline_overlay(dataset, data, ax):
    """NSG 和 NETG 叠加在同一张图上"""
    grid = np.linspace(-0.02, 1.02, 500)
    
    nsg_data = netg_data = None
    for md in data["methods"]:
        if md["method"] == "NSG_Medoid":
            nsg_data = md
        elif md["method"] == "NETG_AsymHNSW":
            netg_data = md
    
    if not nsg_data or not netg_data:
        return
    
    n_ridges = len(RIDGE_LS)
    spacing = 1.0
    
    for i, target_L in enumerate(RIDGE_LS):
        y_base = i * spacing
        
        # NSG
        for sr in nsg_data["search_results"]:
            if sr["search_L"] == target_L:
                recalls_nsg = np.array(sr["per_query_recalls"])
                density_nsg = kde_smooth(recalls_nsg, grid)
                if density_nsg.max() > 0:
                    density_nsg = density_nsg / density_nsg.max() * 0.82
                
                ax.fill_between(grid, y_base, y_base + density_nsg,
                               color=to_rgba('#d62728', 0.35),
                               edgecolor=to_rgba('#d62728', 0.7),
                               linewidth=1.0, zorder=n_ridges - i)
                mean_nsg = sr["mean_recall"]
                break
        
        # NETG
        for sr in netg_data["search_results"]:
            if sr["search_L"] == target_L:
                recalls_netg = np.array(sr["per_query_recalls"])
                density_netg = kde_smooth(recalls_netg, grid)
                if density_netg.max() > 0:
                    density_netg = density_netg / density_netg.max() * 0.82
                
                ax.fill_between(grid, y_base, y_base + density_netg,
                               color=to_rgba('#1f77b4', 0.35),
                               edgecolor=to_rgba('#1f77b4', 0.8),
                               linewidth=1.0, zorder=n_ridges - i + 1)
                mean_netg = sr["mean_recall"]
                break
        
        # 右侧标注 mean
        ax.text(1.06, y_base + 0.28, f'{mean_nsg:.3f}',
               fontsize=7, va='center', color='#d62728', fontweight='bold')
        ax.text(1.06, y_base + 0.05, f'{mean_netg:.3f}',
               fontsize=7, va='center', color='#1f77b4', fontweight='bold')
    
    ax.set_yticks([i * spacing + 0.15 for i in range(n_ridges)])
    ax.set_yticklabels([str(L) for L in RIDGE_LS], fontsize=8.5)
    ax.set_ylabel("Search_L", fontsize=11)
    ax.set_xlabel("Per-Query Recall@10", fontsize=11)
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(-0.3, n_ridges * spacing + 0.5)
    
    ds_label = DATASET_LABELS.get(dataset, dataset)
    ax.set_title(f"{ds_label}", fontsize=12, fontweight='bold', pad=8)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.5)
    ax.spines['bottom'].set_linewidth(0.5)
    
    # 图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=to_rgba('#d62728', 0.4), edgecolor='#d62728', label='NSG (Medoid)'),
        Patch(facecolor=to_rgba('#1f77b4', 0.4), edgecolor='#1f77b4', label='NETG (Ours)'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=8.5, framealpha=0.8)


def main():
    print("=" * 60)
    print("Generating Ridgeline Plots (Aumüller-style)")
    print("=" * 60)
    
    # ===== Plot 1: Yandex T2I — NSG vs NETG 左右对比 =====
    print("\n>>> [1] Yandex T2I side-by-side...")
    fp = f"{INPUT_DIR}/yandex_t2i_per_query_recall_r10.json"
    if os.path.exists(fp):
        with open(fp) as f:
            data = json.load(f)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), sharey=True)
        fig.suptitle("Per-Query Recall@10 Distribution — Yandex T2I (200-d)",
                    fontsize=14, fontweight='bold', y=0.99)
        
        ridgeline_single_method("yandex_t2i", "NSG_Medoid", data, ax1,
                               color='#d62728', title="NSG (Medoid)")
        ridgeline_single_method("yandex_t2i", "NETG_AsymHNSW", data, ax2,
                               color='#1f77b4', title="NETG (Ours)")
        ax2.set_ylabel("")
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        out = f"{OUTPUT_DIR}/ridgeline_yandex_t2i_sidebyside.pdf"
        plt.savefig(out, dpi=300, bbox_inches='tight')
        plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ {out}")
        plt.close()
    
    # ===== Plot 2: Yandex T2I — 叠加图 =====
    print("\n>>> [2] Yandex T2I overlay...")
    if os.path.exists(fp):
        fig, ax = plt.subplots(1, 1, figsize=(7, 7))
        ridgeline_overlay("yandex_t2i", data, ax)
        fig.suptitle("Per-Query Recall@10 Distribution — Yandex T2I (200-d)",
                    fontsize=13, fontweight='bold', y=1.01)
        plt.tight_layout()
        out = f"{OUTPUT_DIR}/ridgeline_yandex_t2i_overlay.pdf"
        plt.savefig(out, dpi=300, bbox_inches='tight')
        plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ {out}")
        plt.close()
    
    # ===== Plot 3: 所有数据集 叠加图 2x3 =====
    print("\n>>> [3] All datasets overlay grid...")
    fig, axes = plt.subplots(2, 3, figsize=(19, 13))
    fig.suptitle("Per-Query Recall@10 Distribution — NSG vs NETG",
                fontsize=15, fontweight='bold', y=0.99)
    
    for idx, dataset in enumerate(DATASETS):
        fp_ds = f"{INPUT_DIR}/{dataset}_per_query_recall_r10.json"
        if not os.path.exists(fp_ds):
            continue
        with open(fp_ds) as f:
            ds_data = json.load(f)
        
        row, col = idx // 3, idx % 3
        ridgeline_overlay(dataset, ds_data, axes[row][col])
    
    if len(DATASETS) < 6:
        axes[1][2].set_visible(False)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = f"{OUTPUT_DIR}/ridgeline_all_datasets.pdf"
    plt.savefig(out, dpi=300, bbox_inches='tight')
    plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
    print(f"  ✅ {out}")
    plt.close()
    
    # ===== Plot 4: 论文精品图 — Yandex T2I 单方法 (类似原论文风格) =====
    print("\n>>> [4] Paper-ready single figure (Yandex T2I, NSG only to show problem)...")
    fp = f"{INPUT_DIR}/yandex_t2i_per_query_recall_r10.json"
    if os.path.exists(fp):
        with open(fp) as f:
            data = json.load(f)
        
        fig, ax = plt.subplots(1, 1, figsize=(6.5, 6.5))
        
        grid = np.linspace(-0.02, 1.02, 500)
        n_ridges = len(RIDGE_LS)
        spacing = 1.0
        cmap = plt.cm.viridis_r
        
        nsg_data = None
        for md in data["methods"]:
            if md["method"] == "NSG_Medoid":
                nsg_data = md
                break
        
        if nsg_data:
            for i, target_L in enumerate(RIDGE_LS):
                for sr in nsg_data["search_results"]:
                    if sr["search_L"] == target_L:
                        recalls = np.array(sr["per_query_recalls"])
                        density = kde_smooth(recalls, grid, bw=0.035)
                        if density.max() > 0:
                            density = density / density.max() * 0.85
                        
                        y_base = i * spacing
                        c = cmap(i / (n_ridges - 1) * 0.8 + 0.1)
                        
                        ax.fill_between(grid, y_base, y_base + density,
                                       color=to_rgba(c, 0.6),
                                       edgecolor=to_rgba(c, 0.95),
                                       linewidth=1.2, zorder=n_ridges - i)
                        ax.plot(grid, y_base + density,
                               color=to_rgba(c, 0.95),
                               linewidth=0.8, zorder=n_ridges - i + 1)
                        
                        mean_r = sr["mean_recall"]
                        pct_low = sr["pct_below_50"]
                        ax.text(1.06, y_base + 0.15, f'{mean_r:.3f}',
                               fontsize=7.5, va='center', color='#333')
                        if pct_low > 1.0:
                            ax.text(-0.08, y_base + 0.15, f'{pct_low:.0f}%',
                                   fontsize=7, va='center', color='#d62728',
                                   fontweight='bold')
                        break
        
        ax.set_yticks([i * spacing + 0.15 for i in range(n_ridges)])
        ax.set_yticklabels([str(L) for L in RIDGE_LS], fontsize=9)
        ax.set_ylabel("Search_L", fontsize=12)
        ax.set_xlabel("Per-Query Recall@10", fontsize=12)
        ax.set_xlim(-0.12, 1.08)
        ax.set_ylim(-0.3, n_ridges * spacing + 0.5)
        ax.set_title("NSG — Yandex T2I (200-d)\nRecall distribution per Search_L",
                    fontsize=12, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 标注说明
        ax.text(-0.08, -0.6, '% fail', fontsize=7, color='#d62728',
               fontweight='bold', ha='center')
        ax.text(1.06, -0.6, 'mean', fontsize=7, color='#333',
               ha='center')
        
        plt.tight_layout()
        out = f"{OUTPUT_DIR}/ridgeline_paper_nsg_yandex.pdf"
        plt.savefig(out, dpi=300, bbox_inches='tight')
        plt.savefig(out.replace('.pdf', '.png'), dpi=200, bbox_inches='tight')
        print(f"  ✅ {out}")
        plt.close()
    
    print(f"\n{'='*60}")
    print(f"🎉 All ridgeline plots saved to: {OUTPUT_DIR}/")
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if 'ridgeline' in f:
            sz = os.path.getsize(f"{OUTPUT_DIR}/{f}")
            print(f"  {f} ({sz/1024:.1f} KB)")


if __name__ == "__main__":
    main()
