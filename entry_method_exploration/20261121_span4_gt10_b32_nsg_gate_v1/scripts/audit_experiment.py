"""Recompute quality with stdlib sets and redo the paired and threshold calculations."""
import csv
from math import isclose
from pathlib import Path

from run_experiment import ARMS, DATASETS, MATRIX, N, ROOT, read, write
from audit import language_neutral_array, load_truth
from score_experiment import PAIRS, PRIMARY, TARGETS


def load(name):
    with (ROOT / "analysis" / (name + ".csv")).open(newline="") as handle:
        return list(csv.DictReader(handle))


def check(value, expected):
    assert isclose(float(value), expected, abs_tol=1e-11, rel_tol=1e-11), (value, expected)


def main():
    report = read(ROOT / "reviews/output_audit.json")
    assert report["status"] == "PASS_E213_PACKETS"
    point_rows, pair_rows, target_rows, frontier_rows = map(load, ("points", "same_l", "recall_thresholds", "frontier"))
    assert (len(point_rows), len(pair_rows), len(target_rows), len(frontier_rows)) == (224, 224, 108, 168)
    cfg = read(ROOT / "gt_eval.json")
    points = {(r["dataset"], int(r["K"]), int(r["L"]), r["method"]): r for r in point_rows}
    scores = {}
    hits = {}
    for ds in DATASETS:
        truth100, truth1 = load_truth(Path(cfg[ds]["path"]), cfg[ds]["format"])
        for k, l in MATRIX:
            for arm in ARMS:
                key = ds, k, l, arm
                p = points[key]
                cell = ROOT / "data" / ds / f"K{k}_L{l}" / arm
                ids = language_neutral_array(cell/"raw/ids.i32", "i")
                assert len(ids) == N*k
                if k == 1:
                    counts = [int(a == b) for a, b in zip(ids, truth1)]
                else:
                    counts = [sum(i in t for i in ids[q*100:(q+1)*100]) for q, t in enumerate(truth100)]
                    assert int(p["low_recall"]) == sum(h < 10 for h in counts)
                hits[key] = counts
                total = sum(counts)
                assert int(p["hits"]) == total
                check(p["recall_pct"], total * 100 / (N*k))
                times = [read(cell / f"round{rep}.json")["seconds"] for rep in range(2)]
                qps = tuple(N / time for time in times)
                check(p["qps0"], qps[0])
                check(p["qps1"], qps[1])
                check(p["qps"], (qps[0] + qps[1]) / 2)
                scores[key] = (total, (qps[0] + qps[1]) / 2, min(qps), max(qps), sum(times)*1e6/(2*N))
    for row in pair_rows:
        ds, k, l = row["dataset"], int(row["K"]), int(row["L"])
        assert (row["method"], row["baseline"]) in PAIRS
        a, b = ((ds, k, l, m) for m in (row["baseline"], row["method"]))
        x, y = scores[a], scores[b]
        check(row["recall_delta_pp"], (y[0] - x[0]) * 100 / (N*k))
        check(row["qps_delta_pct"], 100 * (y[1] / x[1] - 1))
        check(row["slow_new_vs_fast_old_pct"], 100 * (y[2] / x[3] - 1))
        check(row["saved_us_per_query"], x[4] - y[4])
        xy = list(zip(hits[a], hits[b]))
        for field, expected in (("better_queries", sum(b > a for a, b in xy)),
                                ("worse_queries", sum(b < a for a, b in xy))):
            assert int(row[field]) == expected
        if k == 100:
            assert int(row["escaped_low"]) == sum(a < 10 <= b for a, b in xy)
            assert int(row["entered_low"]) == sum(b < 10 <= a for a, b in xy)
    for row in target_rows:
        ds, k, goal, arm = row["dataset"], int(row["K"]), int(row["target_pct"]), row["method"]
        assert goal in TARGETS[ds, k]
        peers = [(s[1], s[0], -l, m) for (d, kk, l, m), s in scores.items()
                 if (d, kk) == (ds, k) and 100*s[0] >= goal*N*k]
        eligible = [p for p in peers if p[3] == arm]
        if eligible:
            qps, total, negative_l, _ = max(eligible)
            check(row["qps"], qps)
            check(row["recall_pct"], total*100/(N*k))
            assert int(row["L"]) == -negative_l
            fastest = arm in PRIMARY and qps == max(p[0] for p in peers if p[3] in PRIMARY)
            assert (row["fastest_span4"] == "True") == fastest
        else:
            assert not row["L"] and not row["qps"] and row["fastest_span4"] == "False"
    for row in frontier_rows:
        ds, k, l, arm = row["dataset"], int(row["K"]), int(row["L"]), row["method"]
        total, qps, *_ = scores[ds, k, l, arm]
        dominators = {m for (d, kk, _, m), s in scores.items()
                      if d == ds and kk == k and m in PRIMARY and s[0] >= total and s[1] >= qps
                      and (s[0] > total or s[1] > qps)}
        assert (row["on_frontier"] == "True") == (not dominators)
        for other in PRIMARY:
            assert (row[f"covered_by_{other}"] == "True") == (other in dominators)
    write(ROOT / "reviews/independent_audit.json", {"status": "PASS_E213_STDLIB_AUDIT",
          "recall_points": len(points), "batch_walls": 2*len(scores), "paired_rows": len(pair_rows),
          "threshold_rows": len(target_rows), "frontier_rows": len(frontier_rows)})


if __name__ == "__main__":
    main()
