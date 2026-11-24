"""Score the first actual packet after all formal batches finish."""
import gzip
import math
from statistics import mean

from run_experiment import ARMS, DATASETS, E200, E212, MATRIX, N, ROOT, read, verify, write
from analyze import RAW, gt, packet, save
import numpy as np

NSG, B32, GATE, SCALAR = ARMS
PRIMARY = ARMS[:3]
PAIRS = ((B32, NSG), (B32, GATE), (GATE, NSG), (GATE, SCALAR))
DATASET_NAMES = dict(zip(DATASETS, ("COCO", "Flickr30k", "WebVid", "Yandex first10M")))
TARGETS = {(dataset, k): ((70, 80, 85, 90, 95, 99) if dataset == DATASETS[2] and k == 100 else (90, 95, 99))
           for dataset in DATASETS for k in (1, 100)}


def old_gate_bits(ds, k, l, widths):
    ref = E200 / "results" / ds / f"k{k}_run/k{k}/GATE_L{l}/raw"
    if k == 1 and l == 100:
        assert not ref.exists()
        return None
    expected = []
    for name, width in zip(RAW, widths):
        with gzip.open(ref / (name + ".gz"), "rb") as payload:
            expected.append(payload.read(width))
    return tuple(expected)


def score():
    phase = read(ROOT / "timing_complete.json")
    assert phase == {"status": "PASS_E213_TIMING_COMPLETE", "datasets": list(DATASETS),
                     "points": 224, "batches": 448, "query_calls": 1376256}
    for name in ("input_freeze.json", "bin/freeze.json"):
        verify(read(ROOT / name)["files"])
    eval_cfg = read(ROOT / "gt_eval.json")
    points, rounds, per_query = {}, [], {}
    anchor_e212 = anchor_e200 = gate_parity = 0
    for ds in DATASETS:
        path = ROOT / "data" / ds
        run = read(path / "complete.json")
        env = read(path / "environment.json")
        assert run == {"status": "PASS_E213_NATIVE", "dataset": ds, "points": 56, "batches": 112,
                       "gate_backend_parity_points": 14, "public_GT_read": False}
        assert (env["cpu"], env["threads"], env["dataset"]) == (15, 1, ds)
        truth = gt(eval_cfg[ds])
        assert truth.shape == (N, 100)
        assert np.min(truth) >= 0 and np.max(truth) < env["binding"]["N"]
        assert np.all(np.diff(np.sort(truth, axis=1), axis=1) > 0)
        dispatch = read(ROOT / "reviews" / f"{ds}.dispatch.json")
        assert (dispatch["status"], dispatch["dataset"]) == ("PASS_E213_DISPATCH", ds)
        assert {(r["K"], r["method"]) for r in dispatch["dispatch"]} == {
            (k, a) for k in (1, 100) for a in ARMS}
        for row in dispatch["dispatch"]:
            assert row["queries"] == 32 and row["L"] == 200
            assert (row["faiss_ip_batch4_calls"] > 0) == (row["method"] in PRIMARY)
        for ordinal, (k, l) in enumerate(MATRIX):
            group = path / f"K{k}_L{l}"
            state = {}
            for i, arm in enumerate(ARMS):
                cell = group / arm
                sha, ids, bits = packet(cell / "raw", k)
                assert np.min(ids) >= 0 and np.max(ids) < env["binding"]["N"]
                state[arm] = bits
                if arm in (NSG, B32):
                    old_method = "NSG" if arm == NSG else "GT10-new-B32"
                    old = E212 / "data" / ds / group.name / old_method / "raw"
                    assert bits == tuple((old / name).read_bytes() for name in RAW), (ds, k, l, arm)
                    anchor_e212 += 1
                if arm == GATE:
                    reference = old_gate_bits(ds, k, l, tuple(map(len, bits)))
                    if reference is not None:
                        assert bits == reference, (ds, k, l, arm)
                        anchor_e200 += 1
                backend = "scalar" if arm == SCALAR else "SPAN4"
                walls = []
                for rep in range(2):
                    row = read(cell / f"round{rep}.json")
                    assert (row["method"], row["backend"], row["K"], row["L"], row["n"],
                            row["rep"], row["cpu"], row["threads"], row["sha256"]) == (
                                arm, backend, k, l, N, rep, 15, 1, sha)
                    slot = (i - ordinal) % len(ARMS)
                    assert row["order"] == (slot + 1 if rep == 0 else 2 * len(ARMS) - slot)
                    wall = row["seconds"]
                    assert wall > 0 and math.isclose(N / wall, row["qps"], rel_tol=1e-13)
                    walls.append(wall)
                    rounds.append({"dataset": ds, **row})
                if k == 1:
                    counts = np.ravel(ids == truth[:, :1]).astype(np.uint8)
                else:
                    counts = (ids[:, :, None] == truth[:, None, :]).any(axis=2).sum(axis=1, dtype=np.uint8)
                hits = int(counts.sum())
                key = ds, k, l, arm
                per_query[key] = counts
                qps = [N / w for w in walls]
                points[key] = {"dataset": ds, "K": k, "L": l, "method": arm, "backend": backend,
                    "n": N, "hits": hits, "recall_pct": 100 * hits / (N*k), "qps": mean(qps),
                    "qps0": qps[0], "qps1": qps[1], "qps_min": min(qps), "qps_max": max(qps),
                    "wall_us": mean(walls) * 1e6 / N, "low_recall": int((counts < 10).sum()) if k == 100 else "",
                    "packet_sha256": sha}
            assert state[GATE] == state[SCALAR], (ds, k, l)
            gate_parity += 1
    assert (len(points), len(rounds), anchor_e212, anchor_e200, gate_parity) == (224, 448, 112, 52, 56)
    return points, rounds, per_query, {
        "status": "PASS_E213_PACKETS", "points": len(points), "batches": len(rounds),
        "gate_backend_bit_parity": gate_parity, "exact_E212_packets": anchor_e212,
        "exact_E200_gate_prefixes": anchor_e200, "gt_after_timing": True}


def same_l(points, per_query):
    for ds in DATASETS:
        for k, l in MATRIX:
            for method, baseline in PAIRS:
                a, b = (points[ds, k, l, x] for x in (baseline, method))
                x, y = (per_query[ds, k, l, m] for m in (baseline, method))
                yield {"dataset": ds, "K": k, "L": l, "baseline": baseline, "method": method,
                    "baseline_recall_pct": a["recall_pct"], "recall_pct": b["recall_pct"],
                    "recall_delta_pp": 100 * (b["hits"] - a["hits"]) / (N*k),
                    "baseline_qps": a["qps"], "qps": b["qps"], "qps_delta_pct": 100 * (b["qps"]/a["qps"] - 1),
                    "slow_new_vs_fast_old_pct": 100 * (b["qps_min"]/a["qps_max"] - 1),
                    "saved_us_per_query": a["wall_us"] - b["wall_us"],
                    "better_queries": int(np.count_nonzero(y > x)), "worse_queries": int(np.count_nonzero(y < x)),
                    "low_before": a["low_recall"], "low_after": b["low_recall"],
                    "escaped_low": int(np.count_nonzero((x < 10) & (y >= 10))) if k == 100 else "",
                    "entered_low": int(np.count_nonzero((x >= 10) & (y < 10))) if k == 100 else ""}


def thresholds(points):
    for (ds, k), targets in TARGETS.items():
        pool = [p for p in points.values() if (p["dataset"], p["K"]) == (ds, k)]
        for goal in targets:
            best = {arm: max((p for p in pool if p["method"] == arm and p["hits"] * 100 >= goal*N*k),
                             key=lambda p: (p["qps"], p["hits"], -p["L"]), default=None) for arm in ARMS}
            fastest = max((best[a]["qps"] for a in PRIMARY if best[a] is not None), default=None)
            for arm, point in best.items():
                yield {"dataset": ds, "K": k, "target_pct": goal, "method": arm,
                    **{key: point[key] if point else "" for key in ("L", "recall_pct", "qps", "qps_min", "qps_max")},
                    "fastest_span4": bool(point and arm in PRIMARY and point["qps"] == fastest)}


def frontier(points):
    for ds, k in TARGETS:
        pool = [p for p in points.values() if (p["dataset"], p["K"]) == (ds, k) and p["method"] in PRIMARY]
        for p in pool:
            cover = [q for q in pool if q["hits"] >= p["hits"] and q["qps"] >= p["qps"]
                     and (q["hits"] > p["hits"] or q["qps"] > p["qps"])]
            yield {**{key: p[key] for key in ("dataset", "K", "L", "method", "recall_pct", "qps")},
                   "on_frontier": not cover, **{f"covered_by_{a}": any(q["method"] == a for q in cover) for a in PRIMARY}}


def main():
    points, rounds, per_query, audit = score()
    tables = {"points": list(points.values()), "rounds": rounds, "same_l": list(same_l(points, per_query)),
              "recall_thresholds": list(thresholds(points)), "frontier": list(frontier(points))}
    for name, rows in tables.items():
        save(ROOT / "analysis" / (name + ".csv"), rows)
    write(ROOT / "reviews/output_audit.json", audit)


if __name__ == "__main__":
    main()
