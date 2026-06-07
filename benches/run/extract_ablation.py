"""
Extract ablation table from final_report.json files.

Generates:
- ablation_summary.csv  (machine-readable, fixed-L)
- ablation_table.tex    (LaTeX booktabs, fixed-L view)
- ablation_recall.tex   (LaTeX, fixed-recall view as supplementary)
- console summary

We report at fixed search depths L (matching paper Section 5.4) because
fixed-L is the operating point a deployment actually uses; fixed-recall
interpolation can mislead when ceiling recall differs slightly between
methods. Fixed-recall is provided as a supplementary view.

Method ordering follows the progressive ablation:
  0. Medoid              (NSG baseline)
  1. + ACO-Max           (single hub, ACO weight)
  2. + W-DPC (Raw HNSW)  (multi-hub, no projector)
  3. Full NETG           (multi-hub + neural folding)
"""

import json
from pathlib import Path

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]  # /mnt/lost+found/ACSG
TEST_DIR = ROOT / "test"

DATASETS = ["deep10M", "sift10M", "sift10M_skewed", "yandex_t2i", "gist1M"]

DATASET_DISPLAY = {
    "deep10M":        "Deep10M",
    "sift10M":        "SIFT10M",
    "sift10M_skewed": "SIFT10M-Skewed",
    "yandex_t2i":     "Yandex T2I",
    "gist1M":         "Gist1M",
}

METHOD_MAP = [
    ("0. Medoid",      "Medoid (NSG)"),
    ("1. ACO-Max",     "+ ACO-Max"),
    ("2. Raw HNSW",    "+ W-DPC (multi-hub)"),
    ("5. Asym-Neural", "Full NETG"),
]

# Fixed search depths to report. These are present in every JSON.
L_TARGETS = [100, 300, 600]

# Optional fixed-recall thresholds (supplementary view).
RECALL_TARGETS = [0.90, 0.95]

OUT_DIR = ROOT / "summary_tables"
OUT_DIR.mkdir(exist_ok=True)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def match_method(name: str):
    for prefix, label in METHOD_MAP:
        if name.startswith(prefix):
            return label
    return None


def at_fixed_L(perf, L_target):
    """Return (qps, std, recall) at the given search_L, or None."""
    for p in perf:
        if p["search_L"] == L_target:
            return p["qps"], p["qps_std"], p["recall"]
    return None


def at_fixed_recall(perf, target):
    """Linear interpolation in (recall, qps) space; None if not reached."""
    perf_sorted = sorted(perf, key=lambda p: p["search_L"])
    if max(p["recall"] for p in perf_sorted) < target:
        return None
    for i, p in enumerate(perf_sorted):
        if p["recall"] >= target:
            if i == 0:
                return p["qps"], p["qps_std"], p["search_L"]
            prev = perf_sorted[i - 1]
            r0, r1 = prev["recall"], p["recall"]
            w = 0.0 if abs(r1 - r0) < 1e-9 else (target - r0) / (r1 - r0)
            qps = prev["qps"] + w * (p["qps"] - prev["qps"])
            std = prev["qps_std"] + w * (p["qps_std"] - prev["qps_std"])
            L = prev["search_L"] + w * (p["search_L"] - prev["search_L"])
            return qps, std, L
    return None


# -----------------------------------------------------------------------------
# Extraction
# -----------------------------------------------------------------------------

def collect_fixed_L():
    """dict[(ds, label)][L] -> (qps, std, recall)."""
    table = {}
    for ds in DATASETS:
        path = TEST_DIR / f"{ds}_results" / f"{ds}_final_report.json"
        if not path.exists():
            print(f"[warn] missing {path}")
            continue
        with open(path) as f:
            data = json.load(f)
        for m in data["results"]:
            label = match_method(m["method_name"])
            if label is None:
                continue
            slot = {L: at_fixed_L(m["performance"], L) for L in L_TARGETS}
            table[(ds, label)] = slot
    return table


def collect_fixed_recall():
    table = {}
    for ds in DATASETS:
        path = TEST_DIR / f"{ds}_results" / f"{ds}_final_report.json"
        if not path.exists():
            continue
        with open(path) as f:
            data = json.load(f)
        for m in data["results"]:
            label = match_method(m["method_name"])
            if label is None:
                continue
            slot = {r: at_fixed_recall(m["performance"], r) for r in RECALL_TARGETS}
            table[(ds, label)] = slot
    return table


# -----------------------------------------------------------------------------
# Output: CSV
# -----------------------------------------------------------------------------

def write_csv(tableL):
    out = OUT_DIR / "ablation_summary.csv"
    with open(out, "w") as f:
        header = ["dataset", "method"]
        for L in L_TARGETS:
            header += [f"qps@L{L}", f"std@L{L}", f"recall@L{L}"]
        f.write(",".join(header) + "\n")
        for ds in DATASETS:
            for _, label in METHOD_MAP:
                row = [DATASET_DISPLAY[ds], label]
                slot = tableL.get((ds, label), {})
                for L in L_TARGETS:
                    hit = slot.get(L)
                    if hit is None:
                        row += ["", "", ""]
                    else:
                        qps, std, rec = hit
                        row += [f"{qps:.1f}", f"{std:.1f}", f"{rec:.4f}"]
                f.write(",".join(row) + "\n")
    print(f"[ok] wrote {out}")


# -----------------------------------------------------------------------------
# Output: LaTeX (fixed-L main table)
# -----------------------------------------------------------------------------

def fmt_qps(hit):
    if hit is None:
        return "---"
    qps, std, _ = hit
    if qps >= 1000:
        return f"{qps:.0f}\\,{{\\scriptsize($\\pm${std:.0f})}}"
    else:
        return f"{qps:.1f}\\,{{\\scriptsize($\\pm${std:.1f})}}"


def write_latex_fixedL(tableL):
    out = OUT_DIR / "ablation_table.tex"
    with open(out, "w") as f:
        f.write("\\begin{table*}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Component-wise ablation across five benchmarks at fixed search depths $L \\in \\{100, 300, 600\\}$. "
                "QPS is reported as mean (over 10 runs) with standard deviation in parentheses. "
                "Each row adds one component on top of the previous, ending at the full NETG model. "
                "$\\Delta$ shows the QPS change of \\emph{Full NETG} relative to the Medoid baseline. "
                "Recall@100 at the same $L$ is shown in brackets.}\n")
        f.write("\\label{tab:ablation_full}\n")
        f.write("\\resizebox{\\textwidth}{!}{%\n")
        # 2 fixed cols + 2 cols per L
        f.write("\\begin{tabular}{ll" + "cc" * len(L_TARGETS) + "}\n")
        f.write("\\toprule\n")

        top = ["", ""]
        for L in L_TARGETS:
            top.append(f"\\multicolumn{{2}}{{c}}{{\\textbf{{$L={L}$}}}}")
        f.write(" & ".join(top) + " \\\\\n")
        cmid = " ".join(f"\\cmidrule(lr){{{3+2*i}-{4+2*i}}}" for i in range(len(L_TARGETS)))
        f.write(cmid + "\n")

        sub = ["\\textbf{Dataset}", "\\textbf{Method}"]
        for _ in L_TARGETS:
            sub += ["QPS", "Recall"]
        f.write(" & ".join(sub) + " \\\\\n")
        f.write("\\midrule\n")

        for ds in DATASETS:
            for i, (_, label) in enumerate(METHOD_MAP):
                row = []
                if i == 0:
                    row.append(f"\\multirow{{{len(METHOD_MAP)}}}{{*}}{{{DATASET_DISPLAY[ds]}}}")
                else:
                    row.append("")
                row.append(label)
                slot = tableL.get((ds, label), {})
                for L in L_TARGETS:
                    hit = slot.get(L)
                    if hit is None:
                        row += ["---", "---"]
                    else:
                        qps, std, rec = hit
                        row.append(fmt_qps(hit))
                        row.append(f"{rec:.3f}")
                f.write(" & ".join(row) + " \\\\\n")

            # Delta row: Full NETG vs Medoid (NSG)
            full = tableL.get((ds, "Full NETG"), {})
            base = tableL.get((ds, "Medoid (NSG)"), {})
            drow = ["", "\\quad$\\Delta$ vs Medoid"]
            for L in L_TARGETS:
                a = full.get(L); b = base.get(L)
                if a is None or b is None or b[0] <= 0:
                    drow += ["---", "---"]
                else:
                    pct = (a[0] - b[0]) / b[0] * 100
                    drec = a[2] - b[2]
                    sign = "+" if pct >= 0 else ""
                    drow.append(f"{sign}{pct:.1f}\\%")
                    drow.append(f"{drec:+.4f}")
            f.write(" & ".join(drow) + " \\\\\n")
            f.write("\\midrule\n")

        f.write("\\bottomrule\n")
        f.write("\\end{tabular}}\n")
        f.write("\\end{table*}\n")
    print(f"[ok] wrote {out}")


# -----------------------------------------------------------------------------
# Output: LaTeX (fixed-recall supplementary table)
# -----------------------------------------------------------------------------

def fmt_qps_R(hit):
    if hit is None:
        return "---"
    qps, std, L = hit
    if qps >= 1000:
        return f"{qps:.0f} ({{\\scriptsize $\\pm${std:.0f}, $L${L:.0f}}})"
    return f"{qps:.1f} ({{\\scriptsize $\\pm${std:.1f}, $L${L:.0f}}})"


def write_latex_fixedR(tableR):
    out = OUT_DIR / "ablation_recall.tex"
    with open(out, "w") as f:
        f.write("\\begin{table}[t]\n")
        f.write("\\centering\n")
        f.write("\\caption{Supplementary ablation at fixed Recall@100 thresholds. "
                "Each cell shows QPS and the search depth $L$ required to reach the target recall. "
                "``---'' means the threshold is not reachable within the maximum budget.}\n")
        f.write("\\label{tab:ablation_recall}\n")
        f.write("\\resizebox{\\columnwidth}{!}{%\n")
        f.write("\\begin{tabular}{ll" + "c" * len(RECALL_TARGETS) + "}\n")
        f.write("\\toprule\n")
        cols = ["\\textbf{Dataset}", "\\textbf{Method}"]
        for r in RECALL_TARGETS:
            cols.append(f"\\textbf{{R={r:.2f}}}")
        f.write(" & ".join(cols) + " \\\\\n")
        f.write("\\midrule\n")
        for ds in DATASETS:
            for i, (_, label) in enumerate(METHOD_MAP):
                row = []
                if i == 0:
                    row.append(f"\\multirow{{{len(METHOD_MAP)}}}{{*}}{{{DATASET_DISPLAY[ds]}}}")
                else:
                    row.append("")
                row.append(label)
                slot = tableR.get((ds, label), {})
                for r in RECALL_TARGETS:
                    row.append(fmt_qps_R(slot.get(r)))
                f.write(" & ".join(row) + " \\\\\n")
            f.write("\\midrule\n")
        f.write("\\bottomrule\n")
        f.write("\\end{tabular}}\n")
        f.write("\\end{table}\n")
    print(f"[ok] wrote {out}")


# -----------------------------------------------------------------------------
# Console summary
# -----------------------------------------------------------------------------

def print_summary(tableL):
    print("\n" + "=" * 110)
    print(f"{'Dataset':<18} {'Method':<22}", end="")
    for L in L_TARGETS:
        print(f"{'L='+str(L):>30}", end="")
    print()
    print("=" * 110)
    for ds in DATASETS:
        for _, label in METHOD_MAP:
            slot = tableL.get((ds, label), {})
            print(f"{DATASET_DISPLAY[ds]:<18} {label:<22}", end="")
            for L in L_TARGETS:
                hit = slot.get(L)
                if hit is None:
                    print(f"{'---':>30}", end="")
                else:
                    qps, std, rec = hit
                    print(f"{qps:>10.1f} \u00b1{std:<6.1f} R={rec:.3f}", end="")
            print()
        full = tableL.get((ds, "Full NETG"), {})
        base = tableL.get((ds, "Medoid (NSG)"), {})
        deltas = []
        for L in L_TARGETS:
            a = full.get(L); b = base.get(L)
            if a and b and b[0] > 0:
                deltas.append(f"L={L}: {(a[0]-b[0])/b[0]*100:+.1f}%")
            else:
                deltas.append(f"L={L}: ---")
        print(f"  -> Full NETG vs Medoid: " + " | ".join(deltas))
        print("-" * 110)


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main():
    tableL = collect_fixed_L()
    tableR = collect_fixed_recall()
    write_csv(tableL)
    write_latex_fixedL(tableL)
    write_latex_fixedR(tableR)
    print_summary(tableL)


if __name__ == "__main__":
    main()

