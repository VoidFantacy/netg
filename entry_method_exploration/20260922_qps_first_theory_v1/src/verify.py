"""Independent Decimal accounting and finite synthetic decision checks."""

import csv
import hashlib
import itertools
import json
import random
import time
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 40
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
D = Decimal
MILLION = D(1000000)


def close(actual, expected):
    assert abs(actual - D(str(expected))) < D("0.00000001"), (actual, expected)


def weighted(x, xa, xb, ya, yb):
    assert xa <= x <= xb and xa < xb
    return ((xb - x) * ya + (x - xa) * yb) / (xb - xa)


def crossing(rows, target, times):
    for i in range(len(rows) - 1):
        a, b = rows[i:i + 2]
        if a["r"] <= target <= b["r"]:
            return (weighted(target, a["r"], b["r"], a["l"], b["l"]),
                    weighted(target, a["r"], b["r"], times[i], times[i + 1]))
    return None


def budget_time(rows, budget, times):
    for i in range(len(rows) - 1):
        a, b = rows[i:i + 2]
        if a["l"] <= budget <= b["l"]:
            return weighted(budget, a["l"], b["l"], times[i], times[i + 1])
    raise AssertionError("Uncovered budget")


def quantities(base, cand, bt, ct):
    lb, tb = crossing(base, D(".9"), bt)
    lc, tc = crossing(cand, D(".9"), ct)
    b_at_c = budget_time(base, lc, bt)
    return {"baseline_time_us": tb, "candidate_time_us": tc,
            "credit_us": tb - b_at_c, "combined_penalty_us": tc - b_at_c,
            "matched_excess_us": tc - tb,
            "zero_charge_gain_pct": 100 * (tb / b_at_c - 1),
            "charge_budget_for_5pct_us": tb - b_at_c - tb / 21,
            "qps_change_pct": 100 * (tb / tc - 1)}


def synthetic_checks():
    checks = []

    def check(name, condition, evidence):
        assert condition, (name, evidence)
        checks.append({"name": name, "status": "PASS", "evidence": evidence})

    check("recall_improves_but_matched_recall_slower", 115 > 105,
          {"baseline": [[.90, 100], [.91, 105]], "candidate": [.91, 115]})
    perfect_before_fee = (80 + 100) / 2
    check("perfect_action_prediction_still_too_expensive", perfect_before_fee + 15 > 100,
          {"default_us": 100, "perfect_choice_us": perfect_before_fee,
           "scorer_us": 15, "complete_candidate_us": perfect_before_fee + 15})
    truth, prediction = [D(".01")] + [D(0)] * 998 + [D("-.10")], [D(".01")] + [D(0)] * 998 + [D(".02")]
    mse = sum((a - b) ** 2 for a, b in zip(truth, prediction)) / len(truth)
    regret = max(truth) - truth[max(range(len(prediction)), key=prediction.__getitem__)]
    check("small_average_mse_large_selection_regret", mse == D(".0000144") and regret == D(".11"),
          {"actions": 1000, "mse": str(mse), "regret": str(regret)})
    check("monotone_recall_does_not_preserve_action_preference", .82 > .80 and .899 < .90 and .899 > .82,
          {"default_low_target": [.80, .90], "alternative_low_target": [.82, .899]})
    check("all_fallback_still_pays_gate", 0 * (20 - 5) - 2 == -2,
          {"upgrade_fraction": 0, "gate_us": 2, "net_saving_us": -2})
    check("xor_information_complementarity", .5 - .1 - .1 > 0,
          {"single_bit_value": 0, "both_bit_value": .5, "each_bit_cost": .1,
           "note": "Predict XOR of two independent fair bits; either single bit leaves Bayes error .5."})
    gain = D(".9") * D(".001") - D(".1") * D(".1")
    check("high_win_probability_negative_expected_gain", gain == D("-.0091"),
          {"win_probability": .9, "expected_gain": str(gain)})
    mean_time_delta = (99 * -1 + 200) / 100
    mean_relative_delta = (99 * -.01 + .02) / 100
    check("mean_relative_time_wrong_objective", mean_time_delta > 0 and mean_relative_delta < 0,
          {"mean_time_delta_us": mean_time_delta, "mean_relative_delta": mean_relative_delta})
    lower_mu = (D(2) - D(1)) / (D(".90") - D(".89"))
    upper_mu = (D("2.1") - D(2)) / (D(".91") - D(".90"))
    check("single_lagrange_weight_misses_discrete_optimum", lower_mu > upper_mu,
          {"mu_lower_bound": str(lower_mu), "mu_upper_bound": str(upper_mu)})
    check("mean_inverse_is_not_throughput", (1 / 1 + 1 / 9) / 2 != 2 / (1 + 9),
          {"latencies": [1, 9], "mean_inverse": (1 / 1 + 1 / 9) / 2,
           "complete_throughput": 2 / 10})

    rng = random.Random(220926)
    bound_trials = 5000
    for _ in range(bound_trials):
        n = rng.randrange(2, 12)
        eps, delta = rng.random(), rng.random()
        low = [rng.uniform(-3, 3) for _ in range(n)]
        target = [v + rng.uniform(-delta, delta) for v in low]
        pred = [v + rng.uniform(-eps, eps) for v in low]
        selected = max(range(n), key=pred.__getitem__)
        assert max(low) - low[selected] <= 2 * eps + 1e-12
        assert max(target) - target[selected] <= 2 * (eps + delta) + 1e-12
        ordered = sorted(low, reverse=True)
        if ordered[0] - ordered[1] > 2 * eps:
            assert low[selected] == ordered[0]
    check("uniform_error_margin_and_budget_bounds", True, {"finite_trials": bound_trials})

    voi_trials = 1000
    for _ in range(voi_trials):
        losses = [[D(rng.randrange(1000)) / 100 for _ in range(4)] for _ in range(8)]
        prior = min(sum(row[a] for row in losses) / 8 for a in range(4))
        after = sum(min(sum(losses[q][a] for q in cell) / len(cell) for a in range(4))
                    * D(len(cell)) / 8 for cell in ([0, 1, 2, 3], [4, 5, 6, 7]))
        perfect = sum(min(row) for row in losses) / 8
        assert D(0) <= prior - after <= prior - perfect
    check("nonnegative_voi_bounded_by_perfect_information", True, {"finite_trials": voi_trials})
    return checks


def main():
    started = time.perf_counter()
    output = HERE / "reviews"
    output.mkdir(exist_ok=False)
    locked = json.loads((HERE / "inputs.locked.json").read_text())
    for name, digest in locked.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest
    metrics = ROOT / "entry_method_exploration/20260922_knn_three_point_timing_v1/metrics.csv"
    with metrics.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    own = {}
    for row in rows:
        qps = [D(row[f"qps_{i}"]) for i in (1, 2, 3)]
        assert sorted(qps)[1] == D(row["qps_median"])
        point = {"r": D(row["recall"]), "l": D(row["L"]),
                 "t": MILLION / sorted(qps)[1], "samples": [MILLION / q for q in qps]}
        own[row["dataset"], int(row["K"]), row["method"], int(row["L"])] = point
    derived = json.loads((HERE / "results_v2/accounting.json").read_text())
    assert len(rows) == len(derived["points"]) == 24
    for row in derived["points"]:
        point = own[row["dataset"], row["K"], row["method"], row["L"]]
        close(point["t"], row["time_us"])
        close(sum(point["samples"]) / 3, row["pooled_time_us"])
    for row in derived["matched_L"]:
        b = own[row["dataset"], row["K"], "DefaultGT10", row["L"]]
        c = own[row["dataset"], row["K"], "TargetKNN", row["L"]]
        close(c["t"] - b["t"], row["full_same_L_penalty_us"])
        close(100 * (c["r"] - b["r"]), row["recall_delta_pp"])
    envelopes = []
    for row in derived["thresholds"]:
        dataset, k = row["dataset"], row["K"]
        base, cand = [sorted([v for key, v in own.items() if key[:3] == (dataset, k, method)], key=lambda p: p["l"])
                      for method in ("DefaultGT10", "TargetKNN")]
        if row["target"] == .95:
            assert crossing(base, D(".95"), [p["t"] for p in base]) is None
            assert crossing(cand, D(".95"), [p["t"] for p in cand]) is None
            continue
        values = quantities(base, cand, [p["t"] for p in base], [p["t"] for p in cand])
        mapping = {"credit_us": "baseline_budget_credit_us", "combined_penalty_us": "combined_same_L_penalty_us",
                   "matched_excess_us": "matched_gap_us", "zero_charge_gain_pct": "conditional_zero_charge_gain_pct",
                   "charge_budget_for_5pct_us": "conditional_charge_budget_for_5pct_qps_us",
                   "qps_change_pct": "interpolated_qps_change_pct"}
        for key, other in mapping.items():
            close(values[key], row[other])
        combinations = [quantities(base, cand, times[:3], times[3:])
                        for times in itertools.product(*(p["samples"] for p in base + cand))]
        assert len(combinations) == 729
        envelope = {key: [float(min(v[key] for v in combinations)), float(max(v[key] for v in combinations))]
                    for key in values}
        assert envelope["matched_excess_us"][0] > 0
        assert envelope["charge_budget_for_5pct_us"][1] < 0
        envelopes.append({"dataset": dataset, "K": k, "combinations": len(combinations), "range": envelope})
    checks = synthetic_checks()
    result = {"status": "PASS", "implementation": "Independent Decimal barycentric interpolation; no analyze.py import",
              "verified_points": 24, "verified_matched_L": 12, "verified_current_thresholds": 4,
              "old_input_hashes_verified": len(locked), "sensitivity_envelopes": envelopes,
              "sensitivity_scope": "Exhaustive recorded-sample combinations, not confidence intervals or new timing",
              "synthetic_checks": checks, "synthetic_scope": "Arithmetic only, no ANN or training",
              "new_searches": 0, "new_training": 0, "analysis_wall_seconds": time.perf_counter() - started}
    with (output / "independent_verification.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: result[key] for key in ["status", "verified_points", "verified_matched_L", "verified_current_thresholds", "analysis_wall_seconds"]}))


if __name__ == "__main__":
    main()
