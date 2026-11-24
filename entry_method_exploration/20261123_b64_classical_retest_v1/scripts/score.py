"""Score both timed repeats against frozen exact L2 GT and compare measured points."""
import csv
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from pathlib import Path
import struct

import numpy as np

from drive import BATCHES, DATASETS, METHODS, POINTS, RAW, ROOT, config, digest, read, verify, write

ANALYSIS = ROOT / "analysis"


def csv_write(name, rows):
    assert rows
    with (ANALYSIS / f"{name}.csv").open("x") as out:
        writer = csv.DictWriter(out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def membership(ids, gt, base_n):
    ids = np.sort(ids, axis=1)
    assert ids.min() >= 0 and ids.max() < base_n
    assert (np.diff(ids, axis=1) > 0).all()
    offsets = np.arange(len(ids), dtype=np.int64)[:, None] * (1 << 32)
    flat = (ids + offsets).ravel()
    probe = gt + offsets
    hit = flat[np.minimum(np.searchsorted(flat, probe), len(flat) - 1)] == probe
    for j in np.linspace(0, len(ids) - 1, 24, dtype=int):
        assert set(gt[j][hit[j]]) == set(ids[j]) & set(gt[j])
    return hit


def score_point(folder, method, k, le, n, ds, ordinal, truth, base_n, repeats):
    parts = [(folder / "raw" / name).read_bytes() for name in RAW]
    assert tuple(map(len, parts)) == (4*n*k, 4*n*k, 12*n, 12*n)
    stamp = sha256(struct.pack("<QQ", n, k) + b"".join(parts) + bytes(n * 16)).hexdigest()
    qs, walls = [], []
    first = (METHODS.index(method) - ordinal) % len(METHODS)
    for rep, order in enumerate((first+1, 4-first)):
        datum = read(folder / f"round{rep}.json")
        assert (datum["method"], datum["n"], datum["K"], datum["L"], datum["rep"],
                datum["order"], datum["cpu"], datum["threads"], datum["sha256"]) == (
            method, n, k, le, rep, order, 15, 1, stamp
        )
        wall = datum["seconds"]
        assert wall > 0 and abs(n/wall - datum["qps"]) < 1e-8
        qs.append(datum["qps"])
        walls.append(wall)
        repeats.append(dict(dataset=ds, **datum))
    ids = np.frombuffer(parts[0], "<i4").reshape(n, k)
    hit = membership(ids, truth[:, :k], base_n)
    hits = int(hit.sum())
    low_recall = int((hit.sum(axis=1) < 10).sum()) if k == 100 else None
    work = np.fromfile(folder / "work.i8", "u1")
    assert work.shape == (256,) and (work <= (96 if method == "B32" else 192)).all()
    row = dict(dataset=ds, K=k, L=le, method=method, queries=n, hits=hits, recall_pct=100*hits/(n*k),
               qps=float(np.mean(qs)), qps0=qs[0], qps1=qs[1], mean_wall_us=1e6*float(np.mean(walls))/n,
               mean_exact_256=float(work.mean()), failures_under_10=low_recall,
               failure_pct=100*low_recall/n if low_recall is not None else None, packet_sha256=stamp)
    return row, hit, work, parts[2:]


def pct(a, b):
    return 100 * (a / b - 1)


def threshold(points, n, ds, k, levels):
    for level in levels:
        minimum = int((Decimal(str(level))*n*k/100).to_integral_value(rounding=ROUND_CEILING))
        row = dict(dataset=ds, K=k, target_pct=level, target_hits=minimum)
        best = {}
        for method in METHODS:
            best[method] = max((p for p in points if p["method"] == method and p["hits"] >= minimum),
                               key=lambda p: p["qps"], default=None)
            for field in ("L", "recall_pct", "qps", "qps0", "qps1"):
                row[f"{method}_{field}"] = best[method][field] if best[method] is not None else None
        b, x = (best[name] for name in METHODS)
        row["qps_delta_pct"] = pct(x["qps"], b["qps"]) if b and x else None
        row["slow_vs_fast_pct"] = pct(min(x["qps0"], x["qps1"]), max(b["qps0"], b["qps1"])) if b and x else None
        yield row


def evaluate():
    assert read(ROOT / "timing_complete.json") == dict(status="PASS_E252_TIMING", datasets=list(DATASETS),
                                                       points=POINTS, batches=BATCHES)
    verify(ROOT / "inputs.json")
    spec = read(ROOT / "configs/score.json")
    points, repeats, comparisons, targets, outcome = [], [], [], [], {}
    for ds in DATASETS:
        c = read(config(ds))
        root, n, base_n = Path(c["output_dir"]), c["eval_n"], c["base"]["n"]
        cert = read(root / "complete.json")
        npairs = sum(map(len, c["grids"].values()))
        assert (cert["binding"]["N"], cert["binding"]["metric_id"], cert["points"], cert["batches"],
                cert["qualified_queries"], cert["public_GT_read"]) == (
            base_n, 1, npairs*2, npairs*4, npairs*2*256, False
        )
        phys = np.fromfile(c["rows"], "<i4")
        assert phys.shape == (n,) and (np.diff(phys) > 0).all()
        g = spec["truth"][ds]
        assert g["format"] == "raw_i32" and g["k"] == 100 and not g.get("row_start")
        assert digest(g["path"]) == g["expected_sha256"]
        assert phys.min() >= 0 and phys.max() < g["n"]
        assert digest(g["ivecs"]) == g["ivecs_sha256"]
        dense = np.memmap(g["path"], "<i4", "r").reshape(g["n"], 100)
        packed = np.memmap(g["ivecs"], "<i4", "r").reshape(g["n"], 101)
        assert (packed[:, 0] == 100).all() and np.array_equal(packed[:, 1:], dense)
        truth = dense[phys]
        assert truth.min() >= 0 and truth.max() < base_n
        assert (np.diff(np.sort(truth, axis=1), axis=1) > 0).all()
        outcome[ds] = dict(n=n, peak_rss_kib=cert["peak_rss_kib"], scenes={})
        ordinal = 0
        for k in (1, 100):
            scene, same_l = [], []
            for le in c["grids"][str(k)]:
                folder = root / f"K{k}_L{le}"
                (b, hb, wb, rb), (x, hx, wx, rx) = [
                    score_point(folder / method, method, k, le, n, ds, ordinal, truth, base_n, repeats)
                    for method in METHODS
                ]
                assert rb == rx and (wx >= wb).all()
                rescued, lost = int((hx & ~hb).sum()), int((hb & ~hx).sum())
                assert x["hits"] - b["hits"] == rescued - lost
                scene.extend((b, x))
                low_recall = (hb.sum(axis=1) < 10) if k == 100 else None
                got = hx.sum(axis=1)
                improved = int((low_recall & (got > hb.sum(axis=1))).sum()) if k == 100 else None
                escaped = int((low_recall & (got >= 10)).sum()) if k == 100 else None
                same_l.append(dict(dataset=ds, K=k, L=le, rescued=rescued, lost=lost,
                                   B32_failures_improved=improved, B32_failures_escaped=escaped,
                                   recall_delta_pp=100*(rescued-lost)/(n*k),
                                   qps_delta_pct=pct(x["qps"], b["qps"]),
                                   extra_exact_256=x["mean_exact_256"]-b["mean_exact_256"]))
                ordinal += 1
            fixed = list(threshold(scene, n, ds, k, spec["targets"][ds][str(k)]))
            common = [row for row in fixed if row["qps_delta_pct"] is not None]
            delta = [row["recall_delta_pp"] for row in same_l]
            outcome[ds]["scenes"][str(k)] = dict(
                same_L_positive=sum(d > 0 for d in delta), same_L_tied=sum(d == 0 for d in delta),
                same_L_negative=sum(d < 0 for d in delta), same_L_total=len(delta),
                delta_pp=[min(delta), max(delta)],
                mean_added_exact_256=float(np.mean([row["extra_exact_256"] for row in same_l])),
                same_L_qps_delta_median=float(np.median([row["qps_delta_pct"] for row in same_l])),
                faster=sum(row["qps_delta_pct"] > 0 for row in common), common=len(common),
                slow_still_faster=sum(row["slow_vs_fast_pct"] > 0 for row in common),
                target_qps_delta_range=[min(row["qps_delta_pct"] for row in common),
                                        max(row["qps_delta_pct"] for row in common)] if common else None,
            )
            points.extend(scene)
            comparisons.extend(same_l)
            targets.extend(fixed)
    assert len(points) == POINTS and len(repeats) == BATCHES and len(comparisons) == POINTS//2
    for name, rows in (("points", points), ("rounds", repeats), ("same_L", comparisons), ("targets", targets)):
        csv_write(name, rows)
    write(ANALYSIS / "outcome.json", outcome)


if __name__ == "__main__":
    evaluate()
