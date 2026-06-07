#!/usr/bin/env python3
"""
Per-Query Recall Distribution Analysis
在所有数据集上运行 NSG (Medoid) vs NETG (Asym-Neural HNSW) 对比实验，
分析每个查询的 recall 分布，验证 NETG 解决了几何迷失问题。
"""

import subprocess
import os
import json
import numpy as np
import datetime

# ==========================================
# 配置
# ==========================================

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
SEARCH_LS = "64,128,200,300,400,512,800,1024"
TOP_K = 1  # Recall@1，最能体现 entry point 的影响

EXECUTABLE = "./build/benches/bench_per_query_recall"
OUTPUT_DIR = "per_query_recall_results"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def run_dataset(dataset):
    """运行单个数据集的 per-query recall 实验"""
    print(f"\n{'='*60}")
    print(f"📊 Processing: {dataset}")
    print(f"{'='*60}")

    acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
    output_file = f"{OUTPUT_DIR}/{dataset}_per_query_recall.json"
    
    trans_hubs = f"drl/{dataset}_results/transformed_hubs.bin"
    trans_ids = f"drl/{dataset}_results/transformed_hub_ids.bin"
    raw_hubs = f"drl/{dataset}_results/raw_hubs.bin"

    # 检查必要文件
    if not os.path.exists(acpg_file):
        print(f"  ❌ ACPG file not found: {acpg_file}")
        return None

    cmd = [
        EXECUTABLE,
        "--dataset", dataset,
        "--acpg_file", acpg_file,
        "--output_file", output_file,
        "--search_L", SEARCH_LS,
        "--top_k", str(TOP_K),
    ]

    if os.path.exists(trans_hubs):
        cmd.extend(["--transformed_hubs", trans_hubs])
    if os.path.exists(trans_ids):
        cmd.extend(["--transformed_ids", trans_ids])
    if os.path.exists(raw_hubs):
        cmd.extend(["--raw_hubs", raw_hubs])

    print(f"  Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
        if result.returncode != 0:
            print(f"  ❌ Failed with return code {result.returncode}")
            if result.stderr:
                print(f"  STDERR: {result.stderr[-500:]}")
            return None
        
        if os.path.exists(output_file):
            print(f"  ✅ Results saved: {output_file}")
            return output_file
        else:
            print(f"  ❌ Output file not generated")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"  ❌ Timeout (>1h)")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None


def generate_summary(result_files):
    """生成汇总表格"""
    print(f"\n\n{'='*80}")
    print("📋 SUMMARY: Per-Query Recall Distribution")
    print(f"{'='*80}")
    
    summary = {}
    
    for filepath in result_files:
        if filepath is None:
            continue
        with open(filepath) as f:
            data = json.load(f)
        
        dataset = data["dataset"]
        summary[dataset] = {}
        
        for method_data in data["methods"]:
            method = method_data["method"]
            summary[dataset][method] = {}
            
            for sr in method_data["search_results"]:
                L = sr["search_L"]
                summary[dataset][method][L] = {
                    "mean": sr["mean_recall"],
                    "p5": sr["p5"],
                    "p10": sr["p10"],
                    "p25": sr["p25"],
                    "median": sr["median"],
                    "pct_below_50": sr["pct_below_50"],
                    "pct_below_80": sr["pct_below_80"],
                    "pct_below_90": sr["pct_below_90"],
                    "pct_perfect": sr["pct_perfect"],
                }
    
    # 打印关键对比表格 (L=512 和 L=1024)
    for target_L in [512, 1024]:
        print(f"\n{'─'*80}")
        print(f"  Search_L = {target_L}, Recall@{TOP_K}")
        print(f"{'─'*80}")
        print(f"{'Dataset':<18} {'Method':<22} {'Mean':>6} {'P5':>6} {'P10':>6} {'<0.5%':>7} {'<0.8%':>7} {'<0.9%':>7} {'Perfect%':>9}")
        print(f"{'─'*80}")
        
        for dataset in DATASETS:
            if dataset not in summary:
                continue
            for method in ["NSG_Medoid", "NETG_AsymHNSW", "Raw_HNSW_Ablation"]:
                if method not in summary[dataset]:
                    continue
                if target_L not in summary[dataset][method]:
                    continue
                s = summary[dataset][method][target_L]
                print(f"{dataset:<18} {method:<22} {s['mean']:>6.4f} {s['p5']:>6.3f} {s['p10']:>6.3f} "
                      f"{s['pct_below_50']:>6.1f}% {s['pct_below_80']:>6.1f}% {s['pct_below_90']:>6.1f}% {s['pct_perfect']:>8.1f}%")
            print()
    
    # 打印关键结论：改善最大的数据集
    print(f"\n{'='*80}")
    print("🔑 KEY FINDINGS: Geometric Myopia Reduction")
    print(f"{'='*80}")
    
    for dataset in DATASETS:
        if dataset not in summary:
            continue
        if "NSG_Medoid" not in summary[dataset] or "NETG_AsymHNSW" not in summary[dataset]:
            continue
        
        for target_L in [512, 1024]:
            if target_L not in summary[dataset]["NSG_Medoid"] or target_L not in summary[dataset]["NETG_AsymHNSW"]:
                continue
            nsg = summary[dataset]["NSG_Medoid"][target_L]
            netg = summary[dataset]["NETG_AsymHNSW"][target_L]
            
            reduction_80 = nsg["pct_below_80"] - netg["pct_below_80"]
            reduction_50 = nsg["pct_below_50"] - netg["pct_below_50"]
            p5_improve = netg["p5"] - nsg["p5"]
            
            if reduction_80 > 0 or p5_improve > 0:
                print(f"  [{dataset}, L={target_L}]")
                print(f"    - Low-recall queries (<0.8): {nsg['pct_below_80']:.1f}% → {netg['pct_below_80']:.1f}% (↓{reduction_80:.1f}%)")
                print(f"    - Catastrophic queries (<0.5): {nsg['pct_below_50']:.1f}% → {netg['pct_below_50']:.1f}% (↓{reduction_50:.1f}%)")
                print(f"    - P5 (worst 5% queries): {nsg['p5']:.3f} → {netg['p5']:.3f} (↑{p5_improve:.3f})")
                print()
    
    # 保存汇总 JSON
    summary_file = f"{OUTPUT_DIR}/summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n✅ Summary saved to: {summary_file}")


def main():
    print("="*60)
    print("🚀 Per-Query Recall Distribution Experiment")
    print(f"   Time: {datetime.datetime.now()}")
    print(f"   Datasets: {DATASETS}")
    print(f"   Search_L: {SEARCH_LS}")
    print(f"   Top-K: {TOP_K}")
    print("="*60)
    
    if not os.path.exists(EXECUTABLE):
        print(f"❌ Executable not found: {EXECUTABLE}")
        return
    
    result_files = []
    for dataset in DATASETS:
        result_file = run_dataset(dataset)
        result_files.append(result_file)
    
    # 生成汇总
    generate_summary(result_files)
    
    print(f"\n🎉 All done! Results in: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
