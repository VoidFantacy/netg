"""
Extract a focused HBKM vs ACO+W-DPC hub-mining comparison from the
Phase-1 ablation runs.

Inputs:
  test/{ds}_results/{ds}_final_report.json       (W-DPC Task 2)
  test_hbkm/{ds}_results/{ds}_final_report.json  (HBKM   Task 2)

Outputs (under summary_tables/):
  hbkm_vs_wdpc.csv        machine-readable
  hbkm_vs_wdpc.tex        LaTeX booktabs (5 datasets x {L=100, 300, 600})
  console summary

Each row is:
  Dataset | hub-miner | (QPS, std, recall) at L in {100, 300, 600}
A `Delta` row reports W-DPC vs HBKM relative QPS gain at fixed L.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEST_WDPC = ROOT / "test"
TEST_HBKM = ROOT / "test_hbkm"
OUT_DIR   = ROOT / "summary_tables"
OUT_DIR.mkdir(exist_ok=True)

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]
DATASET_DISPLAY = {
    "deep10M": "Deep10M",
    "sift10M": "SIFT10M",
    "sift10M_skewed": "SIFT10M-Skewed",
    "yandex_t2i": "Yandex T2I",
    "gist1M": "Gist1M",
}

L_TARGETS = [100, 300, 600]

# Task 2 in test.cpp is: "2. Raw HNSW Routing (Ablation Baseline)"
TASK2_PREFIX = "2. Raw HNSW"


def at_L(perf, L):
    for p in perf:
        if p["search_L"] == L:
            return p["qps"], p["qps_std"], p["recall"]
    return None


def load_task2(report_path: Path):
    if not report_path.exists():
        return None
    with open(report_path) as f:
        data = json.load(f)
    for m in data.get("results", []):
        if m["method_name"].startswith(TASK2_PREFIX):
            return {L: at_L(m["performance"], L) for L in L_TARGETS}
    return None


def collect():
    rows = {}  # rows[ds] = {"wdpc": slot, "hbkm": slot}
    for ds in DATASETS:
        wdpc = load_task2(TEST_WDPC / f"{ds}_results" / f"{ds}_final_report.json")
        hbkm = load_task2(TEST_HBKM / f"{ds}_results" / f"{ds}_final_report.json")
        rows[ds] = {"wdpc": wdpc, "hbkm": hbkm}
        if wdpc is None:
            print(f"  [warn] missing W-DPC Task 2 for {ds}")
        if hbkm is None:
            print(f"  [warn] missing HBKM  Task 2 for {ds}")
    return rows


def write_csv(rows):
    out = OUT_DIR / "hbkm_vs_wdpc.csv"
    with open(out, "w") as f:
        header = ["dataset", "miner"]
        for L in L_TARGETS:
            header += [f"qps@L{L}", f"std@L{L}", f"recall@L{L}"]
        f.write(",".join(header) + "\n")
        for ds in DATASETS:
            for label, key in (("HBKM", "hbkm"), ("ACO+W-DPC", "wdpc")):
                row = [DATASET_DISPLAY[ds], label]
                slot = rows[ds][key]
                for L in L_TARGETS:
                    if slot is None or slot.get(L) is None:
                        row += ["", "", ""]
                    else:
                        q, s, r = slot[L]
                        row += [f"{q:.1f}", f"{s:.1f}", f"{r:.4f}"]
                f.write(",".join(row) + "\n")
    print(f"[ok] wrote {out}")


def fmt_qps(hit):
    if hit is None:
        return "---"
    q, s, _ = hit
    if q >= 1000:
        return f"{q:.0f}\\,{{\\scriptsize($\\pm${s:.0f})}}"
    return f"{q:.1f}\\,{{\\scriptsize($\\pm${s:.1f})}}"


def write_latex(rows):
    out = OUT_DIR / "hbkm_vs_wdpc.tex"
    n_L = len(L_TARGETS)
    with open(out, "w") as f:
        f.write("\\begin{table}[t]\n\\centering\n")
        f.write("\\caption{Hub-mining ablation: HBKM (own implementation, "
                "matched hub count, no projector) vs ACO+W-DPC (no projector). "
                "Both methods route through identical raw HNSW search; the "
                "only difference is the hub set fed to it. "
                "$\\Delta$ shows relative QPS gain of ACO+W-DPC over HBKM.}\n")
        f.write("\\label{tab:hbkm_ablation}\n")
        f.write("\\resizebox{\\columnwidth}{!}{%\n")
        f.write("\\begin{tabular}{ll" + "cc" * n_L + "}\n\\toprule\n")
        top = ["", ""]
        for L in L_TARGETS:
            top.append(f"\\multicolumn{{2}}{{c}}{{\\textbf{{$L={L}$}}}}")
        f.write(" & ".join(top) + " \\\\\n")
        cmid = " ".join(f"\\cmidrule(lr){{{3+2*i}-{4+2*i}}}" for i in range(n_L))
        f.write(cmid + "\n")
        sub = ["\\textbf{Dataset}", "\\textbf{Miner}"]
        for _ in L_TARGETS:
            sub += ["QPS", "Recall"]
        f.write(" & ".join(sub) + " \\\\\n\\midrule\n")
        for ds in DATASETS:
            for i, (label, key) in enumerate((("HBKM", "hbkm"),
                                              ("ACO+W-DPC", "wdpc"))):
                row = []
                if i == 0:
                    row.append(f"\\multirow{{3}}{{*}}{{{DATASET_DISPLAY[ds]}}}")
                else:
                    row.append("")
                row.append(label)
                slot = rows[ds][key]
                for L in L_TARGETS:
                    hit = slot.get(L) if slot else None
                    if hit is None:
                        row += ["---", "---"]
                    else:
                        row.append(fmt_qps(hit))
                        row.append(f"{hit[2]:.3f}")
                f.write(" & ".join(row) + " \\\\\n")
            # Delta row
            wdpc = rows[ds]["wdpc"]; hbkm = rows[ds]["hbkm"]
            drow = ["", "\\quad$\\Delta$ vs HBKM"]
            for L in L_TARGETS:
                a = wdpc.get(L) if wdpc else None
                b = hbkm.get(L) if hbkm else None
                if a is None or b is None or b[0] <= 0:
                    drow += ["---", "---"]
                else:
                    pct = (a[0] - b[0]) / b[0] * 100
                    drec = a[2] - b[2]
                    sign = "+" if pct >= 0 else ""
                    drow.append(f"{sign}{pct:.1f}\\%")
                    drow.append(f"{drec:+.4f}")
            f.write(" & ".join(drow) + " \\\\\n\\midrule\n")
        f.write("\\bottomrule\n\\end{tabular}}\n\\end{table}\n")
    print(f"[ok] wrote {out}")


def print_summary(rows):
    print("\n" + "=" * 100)
    print(f"{'Dataset':<18} {'Miner':<12}", end="")
    for L in L_TARGETS:
        print(f"{'L='+str(L):>26}", end="")
    print()
    print("=" * 100)
    for ds in DATASETS:
        for label, key in (("HBKM", "hbkm"), ("W-DPC", "wdpc")):
            slot = rows[ds][key]
            print(f"{DATASET_DISPLAY[ds]:<18} {label:<12}", end="")
            for L in L_TARGETS:
                hit = slot.get(L) if slot else None
                if hit is None:
                    print(f"{'---':>26}", end="")
                else:
                    print(f"{hit[0]:>9.1f} \u00b1{hit[1]:<5.1f} R={hit[2]:.3f}", end="")
            print()
        wdpc = rows[ds]["wdpc"]; hbkm = rows[ds]["hbkm"]
        deltas = []
        for L in L_TARGETS:
            a = wdpc.get(L) if wdpc else None
            b = hbkm.get(L) if hbkm else None
            if a and b and b[0] > 0:
                deltas.append(f"L={L}: {(a[0]-b[0])/b[0]*100:+.1f}%")
            else:
                deltas.append(f"L={L}: ---")
        print(f"  -> W-DPC vs HBKM: " + " | ".join(deltas))
        print("-" * 100)


def main():
    rows = collect()
    write_csv(rows)
    write_latex(rows)
    print_summary(rows)


if __name__ == "__main__":
    main()
