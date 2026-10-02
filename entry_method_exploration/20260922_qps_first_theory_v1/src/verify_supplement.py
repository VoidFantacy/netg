"""Verify historical wall scales and two additional theoretical counterexamples."""

import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 40
D = Decimal
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]


def main():
    path = ROOT / "entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/results/metrics.csv"
    with path.open(newline="") as stream:
        source = list(csv.DictReader(stream))
    references = json.loads((HERE / "results_v2/accounting.json").read_text())["historical_scales"]
    checked = []
    for ref in references:
        method = "GT10-soft-t1" if ref["dataset"].startswith("webvid") else "GT10-hard"
        rows = sorted([r for r in source if r["dataset"] == ref["dataset"]
                       and int(r["K"]) == ref["K"] and r["method"] == method], key=lambda r: int(r["L"]))
        assert len(rows) == 16
        times = []
        for row in rows:
            wall_time = sum(D(row[f"wall_round{i}"]) for i in (1, 2, 3)) * 1000000 / (3 * D(row["queries"]))
            inverse = D(1000000) / D(row["qps_from_mean_wall"])
            assert abs(wall_time - inverse) < D(".00000001")
            times.append(wall_time)
        target = D(str(ref["target"]))
        brackets = [i for i in range(len(rows) - 1) if D(rows[i]["recall"]) <= target <= D(rows[i + 1]["recall"])]
        assert bool(brackets) == ref["covered"]
        if brackets:
            assert len(brackets) == 1
            i = brackets[0]
            ra, rb = (D(rows[j]["recall"]) for j in (i, i + 1))
            weight = (target - ra) / (rb - ra)
            wall_time = times[i] * (1 - weight) + times[i + 1] * weight
            slope = (times[i + 1] - times[i]) / (100 * (rb - ra))
            assert abs(wall_time - D(str(ref["time_us"]))) < D(".00000001")
            assert abs(slope - D(str(ref["slope_us_per_pp"]))) < D(".00000001")
        checked.append({"dataset": ref["dataset"], "K": ref["K"], "target": ref["target"], "covered": bool(brackets)})
    baseline = 80 + 80
    spliced = 50 + 80
    actual = 50 + (80 + 50)
    assert spliced < baseline < actual
    same_state_value = max(D(0), (D(".1") + D("-.1")) / 2)
    full_state_value = (max(D(0), D(".1")) + max(D(0), D("-.1"))) / 2
    assert same_state_value == 0 and full_state_value == D(".05")
    result = {"status": "PASS", "historical_thresholds": checked,
              "historical_cost_basis": "Direct average of three recorded batch wall times divided by query count; no new timing",
              "cross_query_cache_counterexample": {"baseline_total_us": baseline, "invalid_spliced_prediction_us": spliced,
                                                      "actual_policy_total_us": actual},
              "same_route_state_opposite_gain_counterexample": {"coarse_state_value": str(same_state_value),
                                                                 "fine_state_value": str(full_state_value)},
              "new_searches": 0, "new_training": 0}
    with (HERE / "reviews/supplement_verification.json").open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "PASS", "historical_thresholds": len(checked), "additional_counterexamples": 2}))


if __name__ == "__main__":
    main()
