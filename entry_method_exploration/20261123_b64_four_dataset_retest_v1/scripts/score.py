"""Score exact GT by frozen physical query row after every full-wall run."""
import csv
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
from itertools import combinations
from pathlib import Path
import struct

import numpy as np

from drive import (BATCHES, COCO, DATASETS, E213, E229, E245, METHODS, N, POINTS, PRIMARY,
                   RAW, ROOT, config, digest, read, seal_files, sealed, verify, write)

PAIRS = tuple((METHODS[j], METHODS[i]) for i, j in combinations(range(len(METHODS)), 2))
ANALYSIS = ROOT / "analysis"


def csv_write(name, rows):
    assert rows
    with (ANALYSIS / f"{name}.csv").open("x") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def gt_rows(spec, rows, base_n):
    path = Path(spec["path"])
    assert spec["k"] == spec["width"] == 100 and digest(path) == spec["expected_sha256"]
    if spec["format"] == "raw_i64":
        found = np.memmap(path, "<i8", "r").reshape(spec["n"], 100)[rows]
    else:
        assert spec["format"] == "ivecs"
        packed = np.memmap(path, "<i4", "r").reshape(spec["n"], 101)[rows]
        assert (packed[:, 0] == 100).all()
        found = packed[:, 1:]
    assert found.shape == (N, 100) and found.min() >= 0 and found.max() < base_n
    assert (np.diff(np.sort(found, axis=1), axis=1) > 0).all()
    return found


def membership(ids, gt):
    offsets = np.arange(len(ids), dtype=np.int64)[:, None] * (1 << 32)
    keys = (np.sort(ids, axis=1) + offsets).ravel()
    probe = gt + offsets
    ix = np.minimum(np.searchsorted(keys, probe), len(keys) - 1)
    hit = keys[ix] == probe
    for j in np.linspace(0, len(ids) - 1, 64, dtype=int):
        expected = set(ids[j]) & set(gt[j])
        assert set(gt[j][hit[j]]) == expected
    return hit


def packet(p, k):
    parts = [(p / "raw" / f).read_bytes() for f in RAW]
    assert tuple(map(len, parts)) == (N * k * 4, N * k * 4, N * 3 * 4, N * 3 * 4)
    stamp = sha256(struct.pack("<QQ", N, k) + b"".join(parts) + bytes(N * 16)).hexdigest()
    return stamp, parts


def pct(value, baseline):
    return 100 * (value / baseline - 1)


def historical(ds, k, l, arm, parts, archives):
    if arm in ("B32", "B64-old"):
        source = E229
        name = "B64" if arm == "B64-old" else arm
        old = source / "data" / ds / f"K{k}_L{l}" / name / "raw"
    elif ds == COCO and k == 100:
        source = E245
        old = source / "data" / "confirmation" / f"K{k}_L{l}" / arm / "raw"
    else:
        return None
    if not old.exists():
        return None
    checks = {f: sealed(old / f, source, archives[source]).read_bytes() == b for f, b in zip(RAW, parts)}
    assert all(checks.values()), (ds, k, l, arm, checks)
    return dict(dataset=ds, K=k, L=l, method=arm, experiment=source.name, **checks)


def measure():
    verify(ROOT / "inputs.json")
    receipt = read(ROOT / "timing_complete.json")
    assert receipt == dict(status="PASS_E251_TIMING", datasets=list(DATASETS), points=POINTS, batches=BATCHES)
    gt_specs = read(E213 / "gt_eval.json")
    archives = {run: seal_files(run) for run in (E229, E245)}
    points, repeats, comparisons, parity = [], [], [], []
    for ds in DATASETS:
        c = read(config(ds))
        root = Path(c["output_dir"])
        cert = read(root / "complete.json")
        size = len(METHODS) * sum(map(len, c["grids"].values()))
        assert (cert["status"], cert["points"], cert["batches"], cert["qualified_queries"], cert["public_GT_read"]) == (
            "PASS_E251_FORMAL", size, 2 * size, size * 256, False
        )
        assert cert["binding"]["N"] == c["base"]["n"] and cert["binding"]["metric_id"] == 0
        assert cert["peak_rss_kib"] > 0
        phys = np.fromfile(c["rows"], "<i4")
        assert phys.shape == (N,) and (np.diff(phys) > 0).all()
        truth = gt_rows(gt_specs[ds], phys, c["base"]["n"])
        ordinal = 0
        for k in (1, 100):
            for le in c["grids"][str(k)]:
                route = None
                arms = {}
                for arm, method in enumerate(METHODS):
                    p = root / f"K{k}_L{le}" / method
                    stamp, parts = packet(p, k)
                    check = historical(ds, k, le, method, parts, archives)
                    if check:
                        parity.append(check)
                    if route is None:
                        route = parts[2:]
                    assert parts[2:] == route
                    batches = [read(p / f"round{rep}.json") for rep in range(2)]
                    slot = (arm - ordinal) % len(METHODS)
                    for rep, b in enumerate(batches):
                        pos = slot if rep == 0 else len(METHODS) - 1 - slot
                        order = 1 + rep * len(METHODS) + pos
                        assert (b["K"], b["L"], b["n"], b["rep"], b["order"], b["method"],
                                b["cpu"], b["threads"], b["sha256"]) == (
                            k, le, N, rep, order, method, 15, 1, stamp
                        )
                        assert b["seconds"] > 0 and abs(b["qps"] - N / b["seconds"]) < 1e-8
                        repeats.append(dict(dataset=ds, **b))
                    ids = np.frombuffer(parts[0], "<i4").reshape(N, k)
                    assert ids.min() >= 0 and ids.max() < c["base"]["n"]
                    hit = membership(ids, truth[:, :k])
                    n_hits = int(hit.sum())
                    work = np.fromfile(p / "work.i8", "u1")
                    assert work.shape == (256,) and (work <= (96 if method == "B32" else 192)).all()
                    q0, q1 = [b["qps"] for b in batches]
                    point = dict(dataset=ds, K=k, L=le, method=method, queries=N, hits=n_hits,
                                 recall_pct=100 * n_hits / (N * k), qps=(q0 + q1) / 2, qps0=q0, qps1=q1,
                                 wall_us=1e6 * np.mean([b["seconds"] for b in batches]) / N,
                                 mean_exact_256=float(work.mean()),
                                 failures_under_10=int((hit.sum(axis=1) < 10).sum()) if k == 100 else None,
                                 packet_sha256=stamp)
                    points.append(point)
                    arms[method] = (point, hit, work)
                for method, control in PAIRS:
                    a, ah, aw = arms[method]
                    b, bh, bw = arms[control]
                    if control == "B32":
                        assert (aw >= bw).all()
                    rescue = int((ah & ~bh).sum())
                    lost = int((bh & ~ah).sum())
                    assert rescue - lost == a["hits"] - b["hits"]
                    comparisons.append(dict(dataset=ds, K=k, L=le, method=method, control=control,
                                            rescued=rescue, lost=lost, recall_delta_pp=100 * (rescue - lost) / (N * k),
                                            qps_delta_pct=pct(a["qps"], b["qps"]),
                                            mean_added_exact_256=float(aw.mean() - bw.mean())))
                ordinal += 1
    assert len(points) == POINTS and len(repeats) == BATCHES
    assert sum(r["experiment"] == E229.name for r in parity) == 218
    for file, rows in (("points", points), ("rounds", repeats), ("same_L", comparisons), ("historical_parity", parity)):
        csv_write(file, rows)
    return points, comparisons


def fastest(rows, min_hits):
    return max((r for r in rows if r["hits"] >= min_hits), key=lambda r: r["qps"], default=None)


def targets(ds, k, method, control, a, b, levels):
    for level in levels:
        needed = int((Decimal(str(level)) * N * k / 100).to_integral_value(rounding=ROUND_CEILING))
        r, s = fastest(a, needed), fastest(b, needed)
        row = dict(dataset=ds, K=k, target_pct=level, target_hits=needed, method=method, control=control)
        for name, point in (("a", r), ("b", s)):
            row.update({f"{name}_{key}": point[key] if point else None for key in ("L", "recall_pct", "qps", "qps0", "qps1")})
        row["qps_delta_pct"] = pct(r["qps"], s["qps"]) if r and s else None
        row["slow_vs_fast_pct"] = pct(min(r["qps0"], r["qps1"]), max(s["qps0"], s["qps1"])) if r and s else None
        yield row


def matched(ds, k, method, control, a, b):
    unique = sorted({p["hits"] for p in b})
    exact = [max(p["qps"] for p in b if p["hits"] == hits) for hits in unique]
    for curr in a:
        limit = curr["hits"]
        prior = fastest(b, limit)
        interp = float(np.interp(limit, unique, exact)) if unique[0] <= limit <= unique[-1] else None
        dominated = any(p["hits"] >= limit and p["qps"] >= curr["qps"]
                        and (p["hits"] > limit or p["qps"] > curr["qps"]) for p in b)
        yield dict(dataset=ds, K=k, method=method, control=control, L=curr["L"], recall_pct=curr["recall_pct"],
                   qps=curr["qps"], control_L=prior["L"] if prior else None, control_qps=prior["qps"] if prior else None,
                   qps_delta_pct=pct(curr["qps"], prior["qps"]) if prior else None,
                   line_delta_pct=pct(curr["qps"], interp) if interp is not None else None, dominated=dominated)


def evaluate(points, comparisons):
    result, all_targets, all_matches = {}, [], []
    for ds in DATASETS:
        levels = read(ROOT / "configs" / f"{ds}.targets.json")
        result[ds] = {}
        for k in (1, 100):
            scene = result[ds][str(k)] = {}
            for method, control in PAIRS:
                a, b = ([p for p in points if (p["dataset"], p["K"], p["method"]) == (ds, k, name)]
                        for name in (method, control))
                fixed = list(targets(ds, k, method, control, a, b, levels[str(k)]))
                each = list(matched(ds, k, method, control, a, b))
                common = [p for p in fixed if p["qps_delta_pct"] is not None]
                line = [p["line_delta_pct"] for p in each if p["line_delta_pct"] is not None]
                sub = [p for p in comparisons
                       if (p["dataset"], p["K"], p["method"], p["control"]) == (ds, k, method, control)]
                pp = [p["recall_delta_pp"] for p in sub]
                scene[f"{method}/{control}"] = dict(
                    targets=len(common), goals_faster=sum(p["qps_delta_pct"] > 0 for p in common),
                    goals_slow_faster=sum(p["slow_vs_fast_pct"] > 0 for p in common),
                    same_L_wins=sum(p > 0 for p in pp), same_L_count=len(pp),
                    same_L_recall_range_pp=[min(pp), max(pp)],
                    same_L_median_qps_delta=float(np.median([p["qps_delta_pct"] for p in sub])),
                    interp_count=len(line), interp_faster=sum(p > 0 for p in line),
                    interp_median_delta=float(np.median(line)) if line else None,
                    dominated=sum(p["dominated"] for p in each),
                    primary=next(p for p in fixed if p["target_pct"] == PRIMARY[ds, k]),
                )
                all_targets.extend(fixed)
                all_matches.extend(each)
    csv_write("targets", all_targets)
    csv_write("matched", all_matches)
    write(ANALYSIS / "outcome.json", result)


if __name__ == "__main__":
    evaluate(*measure())
