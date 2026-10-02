"""Read frozen aggregate performance files; do not import search or training code."""

import csv
import hashlib
import json
import math
import shutil
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
TIMING = ROOT / "entry_method_exploration/20260922_knn_three_point_timing_v1"
E103 = ROOT / "entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1"
SOURCES = [TIMING / "metrics.csv", TIMING / "analysis.json", TIMING / "seal.json",
           E103 / "results/metrics.csv"]
DATASETS = {"webvid2_5m_light_v1": "WebVid", "yandex_t2i_official10M_ip_v1": "Yandex"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def lerp(x, xa, xb, ya, yb):
    assert xa < xb and xa <= x <= xb
    return ya + (yb - ya) * (x - xa) / (xb - xa)


def at_recall(rows, recall):
    rows = sorted(rows, key=lambda row: row["L"])
    if any(b["recall"] <= a["recall"] for a, b in zip(rows, rows[1:])):
        return {"covered": False, "reason": "non-strictly-monotone measured Recall curve"}
    for a, b in zip(rows, rows[1:]):
        if a["recall"] <= recall <= b["recall"]:
            return {"covered": True, "bracket_L": [a["L"], b["L"]],
                    "L": lerp(recall, a["recall"], b["recall"], a["L"], b["L"]),
                    "time_us": lerp(recall, a["recall"], b["recall"], a["time_us"], b["time_us"]),
                    "slope_us_per_pp": (b["time_us"] - a["time_us"]) / ((b["recall"] - a["recall"]) * 100)}
    return {"covered": False, "reason": "target not bracketed by measured points"}


def at_budget(rows, budget):
    rows = sorted(rows, key=lambda row: row["L"])
    for a, b in zip(rows, rows[1:]):
        if a["L"] <= budget <= b["L"]:
            return lerp(budget, a["L"], b["L"], a["time_us"], b["time_us"])
    raise ValueError("budget outside measured range")


def main():
    started = time.perf_counter()
    output = HERE / "results_v2"
    output.mkdir(exist_ok=False)
    before = HERE / "source_before"
    before.mkdir(exist_ok=True)
    for name in ["summary.md", "spec.md", "s-target.md", "s-experiment.md"]:
        if (before / name).exists():
            assert sha(ROOT / name) == sha(before / name)
        else:
            shutil.copy2(ROOT / name, before / name)
    identities = {str(path.relative_to(ROOT)): sha(path) for path in SOURCES}
    if (HERE / "inputs.locked.json").exists():
        assert json.loads((HERE / "inputs.locked.json").read_text()) == identities
    else:
        write_json(HERE / "inputs.locked.json", identities)
    with (TIMING / "metrics.csv").open(newline="") as stream:
        raw = list(csv.DictReader(stream))
    points = []
    for row in raw:
        qps = [float(row[f"qps_{r}"]) for r in (1, 2, 3)]
        assert math.isclose(statistics.median(qps), float(row["qps_median"]), rel_tol=1e-12)
        assert min(qps) == float(row["qps_min"]) and max(qps) == float(row["qps_max"])
        assert row["complete_query_wall"] == "True" and row["formal_evaluation"] == "False"
        points.append({"dataset": row["dataset"], "method": row["method"],
                       "K": int(row["K"]), "L": int(row["L"]), "recall": float(row["recall"]),
                       "time_us": 1e6 / statistics.median(qps),
                       "pooled_time_us": statistics.mean(1e6 / q for q in qps),
                       "repeat_times_us": [1e6 / q for q in qps]})
    assert len(points) == 24
    groups = {(dataset, k, method): sorted([p for p in points if p["dataset"] == dataset and p["K"] == k and p["method"] == method], key=lambda p: p["L"])
              for dataset in DATASETS for k in [1, 100] for method in ["DefaultGT10", "TargetKNN"]}
    comparisons, thresholds = [], []
    for dataset in DATASETS:
        for k in [1, 100]:
            baseline, candidate = (groups[dataset, k, m] for m in ["DefaultGT10", "TargetKNN"])
            for base, cand in zip(baseline, candidate):
                assert base["L"] == cand["L"]
                equivalent = at_recall(baseline, cand["recall"])
                credit = equivalent["time_us"] - base["time_us"] if equivalent["covered"] else None
                comparisons.append({"dataset": dataset, "K": k, "L": base["L"],
                                    "recall_delta_pp": 100 * (cand["recall"] - base["recall"]),
                                    "baseline_time_us": base["time_us"], "candidate_time_us": cand["time_us"],
                                    "full_same_L_penalty_us": cand["time_us"] - base["time_us"],
                                    "conditional_recall_credit_us": credit,
                                    "credit_scope": "baseline time-versus-Recall interpolation, not measured scorer cost",
                                    "credit_missing_reason": None if equivalent["covered"] else equivalent["reason"]})
            for target in [0.9, 0.95]:
                base, cand = at_recall(baseline, target), at_recall(candidate, target)
                result = {"dataset": dataset, "K": k, "target": target,
                          "baseline": base, "candidate": cand, "covered": base["covered"] and cand["covered"]}
                if result["covered"]:
                    base_at_cand = at_budget(baseline, cand["L"])
                    credit = base["time_us"] - base_at_cand
                    penalty = cand["time_us"] - base_at_cand
                    gap = cand["time_us"] - base["time_us"]
                    assert math.isclose(gap, penalty - credit, abs_tol=1e-10)
                    result.update({"baseline_at_candidate_budget_us": base_at_cand,
                                   "baseline_budget_credit_us": credit,
                                   "combined_same_L_penalty_us": penalty,
                                   "matched_gap_us": gap,
                                   "interpolated_qps_change_pct": 100 * (base["time_us"] / cand["time_us"] - 1),
                                   "conditional_charge_budget_for_5pct_qps_us": credit - base["time_us"] / 21,
                                   "conditional_zero_charge_gain_pct": 100 * (base["time_us"] / base_at_cand - 1),
                                   "required_current_latency_reduction_for_tie_pct": 100 * (1 - base["time_us"] / cand["time_us"])})
                thresholds.append(result)
    reference = json.loads((TIMING / "analysis.json").read_text())
    for row in reference["matched"]:
        if row["target_name"] != "R90":
            continue
        own = next(t for t in thresholds if (t["dataset"], t["K"], t["target"]) == (row["dataset"], row["K"], .9))
        assert math.isclose(own["interpolated_qps_change_pct"], row["interpolated_change_pct"], abs_tol=1e-10)
    with (E103 / "results/metrics.csv").open(newline="") as stream:
        historical = list(csv.DictReader(stream))
    scales = []
    for dataset in DATASETS:
        default = "GT10-soft-t1" if DATASETS[dataset] == "WebVid" else "GT10-hard"
        for k in [1, 100]:
            rows = [{"L": int(r["L"]), "recall": float(r["recall"]),
                     "time_us": 1e6 / float(r["qps_from_mean_wall"])} for r in historical
                    if (r["dataset"], int(r["K"]), r["method"]) == (dataset, k, default)]
            assert len(rows) == 16, (dataset, k, default, len(rows))
            for target in [.9, .95]:
                value = at_recall(rows, target)
                scales.append({"dataset": dataset, "K": k, "target": target,
                               "source": "E103 only; separate workload and timing session", **value})
    write_json(output / "accounting.json", {"points": points, "matched_L": comparisons,
                                           "thresholds": thresholds, "historical_scales": scales,
                                           "scope": "derived arithmetic; no new queries, models or component timings",
                                           "analysis_wall_seconds": time.perf_counter() - started,
                                           "created_utc": datetime.now(timezone.utc).isoformat()})
    with (output / "matched_L.csv").open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)
    lines = ["# Derived 90% cost accounting", "", "All times in microseconds/query. Coarse interpolation, not new measurement.", "",
             "| Dataset | K | Baseline time | Candidate time | Baseline budget credit | Combined same-L penalty | Matched excess | Conditional zero-charge gain | Charge budget for +5% QPS |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for t in thresholds:
        if t["covered"]:
            lines.append(f"| {DATASETS[t['dataset']]} | {t['K']} | {t['baseline']['time_us']:.3f} | {t['candidate']['time_us']:.3f} | {t['baseline_budget_credit_us']:.3f} | {t['combined_same_L_penalty_us']:.3f} | {t['matched_gap_us']:.3f} | {t['conditional_zero_charge_gain_pct']:.3f}% | {t['conditional_charge_budget_for_5pct_qps_us']:.3f} |")
    lines += ["", "Conditional zero-charge scenario assumes the candidate Recall curve and baseline same-L total cost. It is not measured and is not a general method upper bound.",
              "The combined penalty includes all pipeline differences. No component can be identified from this table.",
              "The +5% column is a sensitivity scenario, not a newly imposed user acceptance gate.",
              "No record125 curve covers 95%; historical scales are stored separately in accounting.json."]
    (output / "cost_table.md").write_text("\n".join(lines) + "\n")
    assert identities == {str(path.relative_to(ROOT)): sha(path) for path in SOURCES}
    print(json.dumps({"status": "PASS", "method_points": len(points), "matched_points": len(comparisons),
                      "covered_current_thresholds": sum(t["covered"] for t in thresholds),
                      "new_searches": 0, "new_training": 0}))


if __name__ == "__main__":
    main()
