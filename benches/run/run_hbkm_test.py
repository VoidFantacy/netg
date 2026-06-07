"""
Run the C++ benchmark with HBKM-mined hubs for the §5.4 hub-mining
ablation (Phase 1: raw HNSW Task 2 only — no projector retraining).

Pre-requisite:
  benches/run/hbkm.py has produced
    drl/{ds}_results/raw_hubs_hbkm.bin
    drl/{ds}_results/transformed_hub_ids_hbkm.bin

For each dataset we invoke `./build/test` (or `./build/benches/test`)
with `--test_scope routing` and *only* `--raw_hubs` set, so the
executable runs:
  Task 2: Raw HNSW Routing (Ablation Baseline)
and skips Task 5 (Asym-Neural) because we do not pass --transformed_hubs.

The report is written to `test_hbkm/{ds}_results/{ds}_final_report.json`
in the same JSON format as the main run, so `extract_ablation.py` can
ingest it later as an additional ablation row.
"""

import datetime
import os
import subprocess

# Single-thread the math libs to keep CPU-time vs wall-time clean
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
LOG_PATH = "test_hbkm.log"


def find_executable() -> str | None:
    for cand in ("./build/test", "./build/benches/test"):
        if os.path.exists(cand):
            return cand
    return None


def run_one(executable: str, dataset: str) -> bool:
    print(f"\n{'#'*60}\n[HBKM-Test] {dataset}\n{'#'*60}")

    raw_hubs_hbkm = f"drl/{dataset}_results/raw_hubs_hbkm.bin"
    ids_hbkm      = f"drl/{dataset}_results/transformed_hub_ids_hbkm.bin"
    if not (os.path.exists(raw_hubs_hbkm) and os.path.exists(ids_hbkm)):
        print(f"  [skip] missing HBKM outputs for {dataset}")
        print(f"          expected {raw_hubs_hbkm}")
        print(f"          expected {ids_hbkm}")
        print(f"          run: python3 benches/run/hbkm.py first")
        return False

    acpg_file  = f"acpg/{dataset}_index/acpg_nsg.json"
    if not os.path.exists(acpg_file):
        print(f"  [skip] missing acpg index: {acpg_file}")
        return False

    out_dir = f"test_hbkm/{dataset}_results"
    os.makedirs(out_dir, exist_ok=True)
    report = f"{out_dir}/{dataset}_final_report.json"

    cmd = [
        executable,
        "--dataset", dataset,
        "--acpg_file", acpg_file,
        "--fn_result", report,
        "--test_scope", "routing",
        "--num_runs", "10",
        "--R", "32",
        "--raw_hubs", raw_hubs_hbkm,
        "--transformed_ids", ids_hbkm,
        # NB: we deliberately do NOT pass --transformed_hubs so Task 5
        # does not run. Phase 1 is pure raw-hub mining comparison.
    ]
    print(f"  cmd: {' '.join(cmd)}")

    try:
        with open(LOG_PATH, "a", encoding="utf-8") as logf:
            logf.write(f"\n{'='*100}\n[HBKM-Test] {dataset}  {datetime.datetime.now()}\n")
            logf.write(" ".join(cmd) + "\n--- C++ Output ---\n")
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    bufsize=1)
            for line in proc.stdout:
                print(line, end="")
                logf.write(line)
            rc = proc.wait()
        if rc != 0:
            print(f"  [error] non-zero exit: {rc}")
            return False
        print(f"  [ok] report -> {report}")
        return True
    except FileNotFoundError as e:
        print(f"  [error] executable not found: {e}")
        return False


def main():
    exe = find_executable()
    if exe is None:
        print("[fatal] could not find ./build/test or ./build/benches/test")
        return
    print(f"[HBKM-Test] using executable {exe}")
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"HBKM ablation (Task 2 only) started {datetime.datetime.now()}\n")
    for ds in DATASETS:
        run_one(exe, ds)
    print("\n[HBKM-Test] done. Reports under test_hbkm/<ds>_results/.")


if __name__ == "__main__":
    main()
