"""Compare already measured fixed-L configurations meeting the Recall constraint."""

import csv
import json
from decimal import Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]


def main():
    path = ROOT / "entry_method_exploration/20260922_knn_three_point_timing_v1/metrics.csv"
    with path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    result = []
    for dataset in sorted({r["dataset"] for r in rows}):
        for k in (1, 100):
            choices = {}
            for method in ("DefaultGT10", "TargetKNN"):
                feasible = [r for r in rows if r["dataset"] == dataset and int(r["K"]) == k
                            and r["method"] == method and Decimal(r["recall"]) >= Decimal(".90")]
                best = max(feasible, key=lambda r: Decimal(r["qps_median"]))
                choices[method] = {"L": int(best["L"]), "recall": float(best["recall"]),
                                   "qps_median": float(best["qps_median"]),
                                   "time_us": float(Decimal(1000000) / Decimal(best["qps_median"]))}
            ratio = choices["TargetKNN"]["qps_median"] / choices["DefaultGT10"]["qps_median"]
            assert ratio < 1
            result.append({"dataset": dataset, "K": k, "methods": choices,
                           "qps_change_pct": 100 * (ratio - 1)})
    output = {"status": "PASS", "scope": "Descriptive selection among three recorded configurations only; no new L, timing or fitting",
              "constraint": "Each selected measured Recall >= .90; not equal exact Recall",
              "comparisons": result, "new_searches": 0, "new_training": 0}
    with (HERE / "results_v2/discrete_thresholds.json").open("x") as stream:
        json.dump(output, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
