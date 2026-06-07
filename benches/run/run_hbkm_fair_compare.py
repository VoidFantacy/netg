"""
Fair A/B comparison: ACO+W-DPC hubs vs HBKM hubs.

Design:
  - Same executable, same index, same queries, same machine, same time window.
  - Interleaved runs: W-DPC → HBKM → W-DPC → HBKM → ... (5 rounds each = 10 total)
  - Each C++ invocation does num_runs=1 internally; we average 5 invocations ourselves.
  - Eliminates thermal drift / background load bias.

Output:
  summary_tables/hbkm_fair_comparison.json   (raw data)
  summary_tables/hbkm_fair_comparison.csv    (for LaTeX)
  console summary
"""

import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)

# --- Config ---
DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
N_ROUNDS = 5          # 5 rounds per method (interleaved)
CPP_NUM_RUNS = 1      # Python-side 5 rounds is enough
COOLDOWN_SEC = 5      # sleep between runs to stabilize thermals
SEARCH_LS = "100,300,600,1200,1500"  # only L values we care about
TOP_K = 100           # recall@100

OUT_DIR = ROOT / "summary_tables"
OUT_DIR.mkdir(exist_ok=True)

# --- Find executable ---
def find_exe():
    for c in ["./build/test", "./build/benches/test"]:
        if os.path.exists(c):
            return c
    sys.exit("[fatal] no executable found")

EXE = find_exe()

# --- Hub paths ---
def hub_paths(ds, method):
    """Return (raw_hubs, trans_ids) for given method."""
    if method == "wdpc":
        return (f"drl/{ds}_results/raw_hubs.bin",
                f"drl/{ds}_results/transformed_hub_ids.bin")
    else:  # hbkm
        return (f"drl/{ds}_results/raw_hubs_hbkm.bin",
                f"drl/{ds}_results/transformed_hub_ids_hbkm.bin")


def run_once(ds, method, round_idx, tmp_dir):
    """Run C++ Task 2 once, return parsed performance list or None."""
    raw_hubs, trans_ids = hub_paths(ds, method)
    if not (os.path.exists(raw_hubs) and os.path.exists(trans_ids)):
        print(f"  [skip] missing files for {ds}/{method}")
        return None

    acpg_file = f"acpg/{ds}_index/acpg_nsg.json"
    if not os.path.exists(acpg_file):
        print(f"  [skip] missing acpg: {acpg_file}")
        return None

    report = f"{tmp_dir}/{ds}_{method}_r{round_idx}.json"
    cmd = [
        EXE,
        "--dataset", ds,
        "--acpg_file", acpg_file,
        "--fn_result", report,
        "--test_scope", "routing",
        "--num_runs", str(CPP_NUM_RUNS),
        "--R", "32",
        "--raw_hubs", raw_hubs,
        "--transformed_ids", trans_ids,
        "--search_Ls", SEARCH_LS,
        "--top_k", str(TOP_K),
    ]

    try:
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
        if proc.returncode != 0:
            print(f"  [error] {ds}/{method} round {round_idx}: rc={proc.returncode}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  [timeout] {ds}/{method} round {round_idx}")
        return None

    # Parse result
    with open(report) as f:
        data = json.load(f)
    for m in data.get("results", []):
        if "2. Raw HNSW" in m["method_name"]:
            return m["performance"]
    return None


def aggregate(runs):
    """Average QPS/recall across rounds for each L."""
    from collections import defaultdict
    by_L = defaultdict(lambda: {"qps_vals": [], "recall_vals": []})
    for perf in runs:
        for p in perf:
            L = p["search_L"]
            by_L[L]["qps_vals"].append(p["qps"])
            by_L[L]["recall_vals"].append(p["recall"])

    result = {}
    for L, v in sorted(by_L.items()):
        qps_vals = v["qps_vals"]
        rec_vals = v["recall_vals"]
        import numpy as np
        result[L] = {
            "qps_mean": float(np.mean(qps_vals)),
            "qps_std": float(np.std(qps_vals)),
            "recall_mean": float(np.mean(rec_vals)),
            "n_runs": len(qps_vals),
        }
    return result


def main():
    print(f"[Fair Compare] {N_ROUNDS} rounds x 2 methods, interleaved")
    print(f"[Fair Compare] executable: {EXE}")
    print(f"[Fair Compare] cpp_num_runs: {CPP_NUM_RUNS}, cooldown: {COOLDOWN_SEC}s")
    print(f"[Fair Compare] started: {datetime.datetime.now()}\n")

    tmp_dir = str(ROOT / "test_fair_tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    all_data = {}

    for ds in DATASETS:
        print(f"\n{'='*70}")
        print(f"  Dataset: {ds}")
        print(f"{'='*70}")

        wdpc_runs = []
        hbkm_runs = []

        for r in range(N_ROUNDS):
            # W-DPC first in odd rounds, HBKM first in even (further reduces bias)
            order = [("wdpc", wdpc_runs), ("hbkm", hbkm_runs)]
            if r % 2 == 1:
                order = order[::-1]

            for method, run_list in order:
                print(f"  Round {r+1}/{N_ROUNDS} — {method} ...", end=" ", flush=True)
                t0 = time.time()
                perf = run_once(ds, method, r, tmp_dir)
                elapsed = time.time() - t0
                if perf:
                    run_list.append(perf)
                    print(f"ok ({elapsed:.1f}s)")
                else:
                    print(f"FAILED ({elapsed:.1f}s)")
                time.sleep(COOLDOWN_SEC)

        # Aggregate
        if wdpc_runs and hbkm_runs:
            wdpc_agg = aggregate(wdpc_runs)
            hbkm_agg = aggregate(hbkm_runs)
            all_data[ds] = {"wdpc": wdpc_agg, "hbkm": hbkm_agg}

            # Print summary for this dataset
            print(f"\n  {'L':>6} | {'W-DPC QPS':>12} | {'HBKM QPS':>12} | {'Δ':>7} | {'W-DPC R':>8} | {'HBKM R':>8}")
            print(f"  {'-'*6}-+-{'-'*12}-+-{'-'*12}-+-{'-'*7}-+-{'-'*8}-+-{'-'*8}")
            for L in [100, 300, 600, 1200, 1500]:
                if L in wdpc_agg and L in hbkm_agg:
                    w = wdpc_agg[L]
                    h = hbkm_agg[L]
                    delta = (w["qps_mean"] - h["qps_mean"]) / h["qps_mean"] * 100
                    print(f"  {L:>6} | {w['qps_mean']:>7.1f}±{w['qps_std']:<4.1f} | {h['qps_mean']:>7.1f}±{h['qps_std']:<4.1f} | {delta:>+5.1f}% | {w['recall_mean']:>8.4f} | {h['recall_mean']:>8.4f}")
        else:
            print(f"  [!] insufficient data for {ds}")

    # Save raw JSON
    json_out = OUT_DIR / "hbkm_fair_comparison.json"
    with open(json_out, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\n[ok] wrote {json_out}")

    # Save CSV
    csv_out = OUT_DIR / "hbkm_fair_comparison.csv"
    with open(csv_out, "w") as f:
        f.write("dataset,method,L,qps_mean,qps_std,recall_mean,n_rounds\n")
        for ds, methods in all_data.items():
            for method, agg in methods.items():
                for L, v in sorted(agg.items()):
                    f.write(f"{ds},{method},{L},{v['qps_mean']:.2f},{v['qps_std']:.2f},{v['recall_mean']:.6f},{v['n_runs']}\n")
    print(f"[ok] wrote {csv_out}")

    print(f"\n[Fair Compare] finished: {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
