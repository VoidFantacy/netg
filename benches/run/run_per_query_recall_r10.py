#!/usr/bin/env python3
"""Per-Query Recall@10 Distribution Experiment"""
import subprocess, os, json, datetime

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
SEARCH_LS = "64,128,200,300,400,512,800,1024"
TOP_K = 10
EXECUTABLE = "./build/benches/bench_per_query_recall"
OUTPUT_DIR = "per_query_recall_results_r10"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("="*60)
print(f"Per-Query Recall@{TOP_K} Distribution Experiment")
print(f"Time: {datetime.datetime.now()}")
print("="*60)

for dataset in DATASETS:
    print(f"\n{'='*60}")
    print(f"Processing: {dataset}")
    print(f"{'='*60}")
    acpg_file = f"acpg/{dataset}_index/acpg_nsg.json"
    output_file = f"{OUTPUT_DIR}/{dataset}_per_query_recall_r10.json"
    trans_hubs = f"drl/{dataset}_results/transformed_hubs.bin"
    trans_ids = f"drl/{dataset}_results/transformed_hub_ids.bin"
    raw_hubs = f"drl/{dataset}_results/raw_hubs.bin"
    
    if not os.path.exists(acpg_file):
        print(f"  SKIP: {acpg_file} not found")
        continue
    
    cmd = [EXECUTABLE, "--dataset", dataset, "--acpg_file", acpg_file,
           "--output_file", output_file, "--search_L", SEARCH_LS, "--top_k", str(TOP_K)]
    if os.path.exists(trans_hubs): cmd.extend(["--transformed_hubs", trans_hubs])
    if os.path.exists(trans_ids): cmd.extend(["--transformed_ids", trans_ids])
    if os.path.exists(raw_hubs): cmd.extend(["--raw_hubs", raw_hubs])
    
    print(f"  CMD: {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    print(r.stdout[-3000:] if len(r.stdout) > 3000 else r.stdout)
    if r.returncode != 0:
        print(f"  FAILED: rc={r.returncode}")
        print(r.stderr[-500:] if r.stderr else "")

# Summary
print("\n\n" + "="*90)
print("SUMMARY TABLE")
print("="*90)

for target_L in [64, 128, 200, 512, 1024]:
    print(f"\n{'─'*90}")
    print(f"  Search_L = {target_L}, Recall@{TOP_K}")
    print(f"{'─'*90}")
    print(f"{'Dataset':<18} {'Method':<22} {'Mean':>6} {'P5':>6} {'P10':>6} {'<0.5%':>7} {'<0.8%':>7} {'<0.9%':>7} {'Perfect%':>9}")
    print(f"{'─'*90}")
    
    for ds in DATASETS:
        fp = f"{OUTPUT_DIR}/{ds}_per_query_recall_r10.json"
        if not os.path.exists(fp): continue
        with open(fp) as f:
            data = json.load(f)
        for md in data["methods"]:
            for sr in md["search_results"]:
                if sr["search_L"] == target_L:
                    print(f"{ds:<18} {md['method']:<22} {sr['mean_recall']:>6.4f} {sr['p5']:>6.3f} {sr['p10']:>6.3f} "
                          f"{sr['pct_below_50']:>6.1f}% {sr['pct_below_80']:>6.1f}% {sr['pct_below_90']:>6.1f}% {sr['pct_perfect']:>8.1f}%")
        print()

# Key findings
print("\n" + "="*90)
print("KEY FINDINGS: Geometric Myopia Reduction")
print("="*90)
for ds in DATASETS:
    fp = f"{OUTPUT_DIR}/{ds}_per_query_recall_r10.json"
    if not os.path.exists(fp): continue
    with open(fp) as f:
        data = json.load(f)
    
    nsg_data = netg_data = None
    for md in data["methods"]:
        if md["method"] == "NSG_Medoid": nsg_data = md
        elif md["method"] == "NETG_AsymHNSW": netg_data = md
    
    if not nsg_data or not netg_data: continue
    
    for sr_nsg, sr_netg in zip(nsg_data["search_results"], netg_data["search_results"]):
        L = sr_nsg["search_L"]
        if L not in [64, 128, 200, 512]: continue
        r80_nsg = sr_nsg["pct_below_80"]
        r80_netg = sr_netg["pct_below_80"]
        r50_nsg = sr_nsg["pct_below_50"]
        r50_netg = sr_netg["pct_below_50"]
        mean_diff = sr_netg["mean_recall"] - sr_nsg["mean_recall"]
        p5_diff = sr_netg["p5"] - sr_nsg["p5"]
        
        if r80_nsg - r80_netg > 0.3 or p5_diff > 0.01 or mean_diff > 0.005:
            print(f"\n  [{ds}, L={L}]")
            print(f"    Mean Recall: {sr_nsg['mean_recall']:.4f} → {sr_netg['mean_recall']:.4f} ({'+' if mean_diff>=0 else ''}{mean_diff:.4f})")
            print(f"    P5 (worst 5%): {sr_nsg['p5']:.3f} → {sr_netg['p5']:.3f} ({'+' if p5_diff>=0 else ''}{p5_diff:.3f})")
            print(f"    Queries <0.8: {r80_nsg:.1f}% → {r80_netg:.1f}% (↓{r80_nsg-r80_netg:.1f}%)")
            print(f"    Queries <0.5: {r50_nsg:.1f}% → {r50_netg:.1f}% (↓{r50_nsg-r50_netg:.1f}%)")

print("\n\nDONE!")
