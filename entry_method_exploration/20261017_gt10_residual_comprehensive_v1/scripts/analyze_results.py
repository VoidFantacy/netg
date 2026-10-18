#!/usr/bin/env python3
"""E183 retained-output analysis. No ANN traversal, training or vector scoring.

Input: configs/<dataset>.analysis.json; see --help. All timing jobs must already
be complete. The first actual timed packet is scored; rounds 2/3 must have native
full-packet bit-equivalence receipts. Query-paired bootstrap resamples the exact
empirical integer-difference distribution, never individual K100 members.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
REPS = 3000
SEED = 20261017
KS = (1, 100)
BANDS = (("0", 0, 0), ("1..10", 1, 10), ("11..50", 11, 50), ("51..90", 51, 90),
         ("91..99", 91, 99), ("100", 100, 100))
FREQUENCY_BANDS = (("0", 0, 0), ("1", 1, 1), ("2..5", 2, 5), ("6..20", 6, 20), ("21+", 21, 2**31-1))
LABELS = {"deep": "Deep", "deep1m": "Deep", "sift": "SIFT", "sift1m": "SIFT",
          "gist": "GIST", "gist1m": "GIST", "web": "WebVid", "webvid": "WebVid",
          "yandex": "Yandex", "coco": "COCO", "flickr": "Flickr30k", "flickr30k": "Flickr30k"}
LABELS.update({"deep10m_l2_v1": "Deep10M", "sift10m_bigann_l2_v1": "SIFT10M",
               "gist1m_l2_v1": "GIST1M", "webvid2_5m_light_v1": "WebVid",
               "yandex_t2i_official10M_ip_v1": "Yandex"})
DATASET_ORDER = ("deep10m_l2_v1", "sift10m_bigann_l2_v1", "gist1m_l2_v1", "webvid2_5m_light_v1",
                 "yandex_t2i_official10M_ip_v1", "coco", "flickr30k")
BOUNDARY_FIELDS = ("dataset", "K", "L", "method", "reference_method", "query_row",
                   "candidate_available_but_not_returned_GT_ids", "damaged_GT_ids", "reference_boundary_id",
                   "reference_boundary_native_distance", "actual_boundary_id", "actual_boundary_native_distance",
                   "numeric_cause_verified_by_analyzer")


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def save_json(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def save_csv(path, rows, empty_fields=None):
    if not rows and not empty_fields:
        return
    fields = list(rows[0]) if rows else list(empty_fields)
    require(all(list(row) == fields for row in rows), "CSV field identity: " + str(path))
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class Inputs:
    def __init__(self):
        self.identities = {}

    def remember(self, path, expected=None):
        path = Path(path).resolve()
        stat = path.stat()
        value = {"bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns, "sha256": sha(path)}
        after = path.stat()
        require((after.st_size, after.st_mtime_ns) == (stat.st_size, stat.st_mtime_ns), "input changed while hashing")
        require(expected is None or expected == value["sha256"], "input expected SHA: " + str(path))
        require(str(path) not in self.identities or self.identities[str(path)] == value, "input identity drift")
        self.identities[str(path)] = value
        return path

    def json(self, path):
        return json.loads(self.remember(path).read_text())

    def raw(self, path, dtype, shape):
        import numpy as np
        path = self.remember(path)
        require(path.stat().st_size == math.prod(shape) * np.dtype(dtype).itemsize, "raw shape: " + str(path))
        if math.prod(shape) == 0:
            return np.empty(shape, dtype=dtype)
        return np.memmap(path, mode="r", dtype=dtype, shape=shape)

    def unchanged(self):
        for path, old in self.identities.items():
            now = Path(path).stat()
            require((now.st_size, now.st_mtime_ns) == (old["bytes"], old["mtime_ns"]), "consumed input changed: " + path)


def validate_ids(ids, base_n):
    import numpy as np
    require(bool(((ids >= 0) & (ids < base_n)).all()), "ID domain")
    if ids.shape[1] > 1:
        ordered = np.sort(ids, axis=1)
        require(bool((ordered[:, 1:] > ordered[:, :-1]).all()), "unique IDs within query")


def load_gt(descriptor, inputs, n):
    """Support immutable raw/ivecs/ibin GT without assuming first dimension=100."""
    import numpy as np
    if isinstance(descriptor, str):
        descriptor = {"path": descriptor, "format": "raw_i64", "width": 100, "n": n}
    path = inputs.remember(descriptor["path"])
    fmt = descriptor.get("format", "raw_i64")
    width = int(descriptor.get("width", descriptor.get("k", 100)))
    total = int(descriptor.get("total_n", descriptor.get("n", n)))
    start = int(descriptor.get("row_start", 0))
    require(start >= 0 and start + n <= total and width >= 100, "GT prefix dimensions")
    if fmt == "ivecs":
        require(path.stat().st_size == total * (width + 1) * 4, "ivecs exact shape")
        raw = np.memmap(path, dtype="<i4", mode="r", shape=(total, width + 1))
        require(bool((raw[:, 0] == width).all()), "ivecs row headers")
        result = raw[start:start + n, 1:101]
    elif fmt == "ibin":
        with path.open("rb") as stream:
            header = struct.unpack("<2I", stream.read(8))
        require(header == (total, width) and path.stat().st_size == 8 + total * width * 4, "ibin shape/header")
        result = np.memmap(path, dtype="<i4", mode="r", offset=8, shape=(total, width))[start:start+n, :100]
    else:
        dtype = descriptor.get("dtype", {"raw_i64": "<i8", "raw_i32": "<i4", "raw": "<i8"}.get(fmt))
        require(dtype is not None, "supported GT format")
        require(path.stat().st_size == total * width * np.dtype(dtype).itemsize, "raw GT exact shape")
        result = np.memmap(path, dtype=dtype, mode="r", shape=(total, width))[start:start+n, :100]
    return result


def membership(ids, gt):
    """Output mask is on the GT-member axis, not returned-result rank axis."""
    import numpy as np
    require(ids.shape == gt.shape, "GT and response top-K shape")
    result = np.empty(gt.shape, dtype=np.bool_)
    for lo in range(0, len(gt), 256):
        hi = min(lo + 256, len(gt))
        result[lo:hi] = (ids[lo:hi, :, None] == gt[lo:hi, None, :]).any(axis=1)
    return result


def bootstrap_mean_ci(values, scale=1.0, key=""):
    """Equivalent to query bootstrap, with multinomial sufficient statistics."""
    import numpy as np
    values = np.asarray(values, dtype=np.int64)
    if not len(values):
        return None, None
    unique, counts = np.unique(values, return_counts=True)
    if len(unique) == 1:
        value = float(unique[0]) * scale
        return value, value
    local_seed = SEED ^ int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "little")
    rng = np.random.default_rng(local_seed)
    sampled = rng.multinomial(len(values), counts / counts.sum(), size=REPS)
    means = sampled @ unique / len(values) * scale
    return tuple(map(float, np.quantile(means, [.025, .975], method="linear")))


def wilson(success, total):
    if not total:
        return None, None
    z = 1.959963984540054
    p = success / total
    denom = 1 + z*z / total
    middle = (p + z*z/(2*total)) / denom
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denom
    return max(0.0, middle-half), min(1.0, middle+half)


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def compare_masks(ref, actual, key):
    import numpy as np
    n, k = ref.shape
    rescue = actual & ~ref
    damage = ref & ~actual
    nr, nd = int(rescue.sum()), int(damage.sum())
    old_hits = int(ref.sum())
    missing = n*k-old_hits
    delta = actual.sum(axis=1, dtype=np.int64) - ref.sum(axis=1, dtype=np.int64)
    reference_quality90 = ref.sum(axis=1) >= math.ceil(.9*k)
    actual_quality90 = actual.sum(axis=1) >= math.ceil(.9*k)
    low, high = bootstrap_mean_ci(delta, 100.0/k, key)
    wr = wilson(nr, missing) if k == 1 else (None, None)
    wd = wilson(nd, old_hits) if k == 1 else (None, None)
    return {"n": n, "reference_hits": old_hits, "hits": int(actual.sum()),
            "rescued_members": nr, "damaged_members": nd, "net_members": nr-nd,
            "persistent_missing_members": int((~ref & ~actual).sum()),
            "persistent_failed_queries": int((~ref.all(axis=1) & ~actual.all(axis=1)).sum()),
            "reference_missing_members": missing, "reference_correct_members": old_hits,
            "rescue_rate_on_missing": ratio(nr, missing), "damage_rate_on_correct": ratio(nd, old_hits),
            "rescue_rate_wilson95_low": wr[0], "rescue_rate_wilson95_high": wr[1],
            "damage_rate_wilson95_low": wd[0], "damage_rate_wilson95_high": wd[1],
            "rescued_queries": int(rescue.any(axis=1).sum()), "damaged_queries": int(damage.any(axis=1).sum()),
            "net_improved_queries": int((delta > 0).sum()), "net_worsened_queries": int((delta < 0).sum()),
            "unchanged_query_recall": int((delta == 0).sum()),
            "reference_full_success_queries": int(ref.all(axis=1).sum()),
            "reference_incomplete_queries": int((~ref.all(axis=1)).sum()),
            "actual_full_success_queries": int(actual.all(axis=1).sum()),
            "failed_queries_become_full_success": int((~ref.all(axis=1) & actual.all(axis=1)).sum()),
            "full_success_queries_become_failed": int((ref.all(axis=1) & ~actual.all(axis=1)).sum()),
            "reference_at_least_90pct_queries": int(reference_quality90.sum()),
            "reference_below_90pct_queries": int((~reference_quality90).sum()),
            "actual_at_least_90pct_queries": int(actual_quality90.sum()),
            "below_90pct_become_at_least_90pct_queries": int((~reference_quality90 & actual_quality90).sum()),
            "at_least_90pct_become_below_90pct_queries": int((reference_quality90 & ~actual_quality90).sum()),
            "recall_delta_pp": (100.0*(nr-nd)/(n*k)) if n else None,
            "recall_delta_pp_bootstrap95_low": low, "recall_delta_pp_bootstrap95_high": high}


def read_dataset(asset, inputs):
    import numpy as np
    cfg = inputs.json(asset["benchmark_config"])
    dataset, n, base_n = cfg["dataset"], cfg["queries"]["n"], cfg["base"]["n"]
    root = Path(cfg["output_dir"])
    complete = inputs.json(root / "complete.json")
    require(complete["status"] == "PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES", "formal native completion gate: " + dataset)
    require(complete["config"] == cfg and complete["formal_performance"] and
            complete["full_merge_oracle_passed"] and complete["threads"] == cfg["threads"] and
            complete["cpu"] == cfg["cpu"] and complete["evaluation_GT_read"] is False,
            "completed native configuration/oracle/timing binding")
    environment = inputs.json(root / "environment.json")
    require(environment["threads"] == 1 and environment["cpu"] == cfg["cpu"] and
            environment["metric_id"] == cfg["metric_id"], "actual formal environment")
    require(cfg["threads"] == 1 and cfg["timing_repeats"] == 3, "formal T1/three-round config")
    gt = load_gt(asset["eval_gt"], inputs, n)
    validate_ids(gt, base_n)
    methods = {m["name"]: m for m in cfg["methods"]}
    require(len(methods) == len(cfg["methods"]), "unique method names")
    grid = {(m, k, int(L)) for m in methods for k in KS for L in cfg["K_L"][str(k)]}
    points, timings, packets = [], [], {}
    for meta in complete["results"]:
        method, k, L = meta["method"], int(meta["K"]), int(meta["L"])
        key = (method, k, L)
        require(key in grid and key not in packets and meta["n"] == n, "complete result matrix uniqueness")
        result_dir = Path(meta["result_dir"])
        require(inputs.json(result_dir / "result.json") == meta, "result/complete metadata identity")
        rounds = meta["rounds"]
        require(len(rounds) == 3 and [r["round"] for r in rounds] == [0, 1, 2], "all three ordered timing rounds")
        require(all(r["first_round_bits_equal"] for r in rounds), "actual timed packet full-bit equivalence")
        require(all(r["packet_sha256"] == rounds[0]["packet_sha256"] for r in rounds), "timed packet SHA equality")
        require(meta.get("timed_output_retained") is True, "first actual timed output retained")
        require(meta["normal_output_destroyed_within_wall"] and meta["uniform_packet_copy_inside_wall"] and
                meta["full_merge_oracle_passed"] and meta["formal_performance"] and meta["counts_collected"] is False,
                "actual packet lifecycle/oracle/performance scope")
        raw = result_dir / "raw"
        ids = inputs.raw(raw / "ids.i32", "<i4", (n, k))
        distances = inputs.raw(raw / "distances.f32", "<f4", (n, k))
        entries = inputs.raw(raw / "entry_ids.i32", "<i4", (n, 3))
        profile = inputs.raw(raw / "profile_distances.f32", "<f4", (n, 3))
        # Native hashes two uint64 dimensions, these four saved vectors, then two
        # n-long uint64 zero layout vectors. They are placeholders, not NDC data.
        digest = hashlib.sha256(struct.pack("<2Q", n, k))
        for array in (ids, distances, entries, profile):
            digest.update(array.tobytes())
        digest.update(bytes(16*n))
        require(digest.hexdigest() == rounds[0]["packet_sha256"], "stored actual packet reproduces native full SHA")
        validate_ids(ids, base_n)
        require(bool(np.isfinite(distances).all() and np.isfinite(profile).all()), "finite response scores")
        require(k == 1 or bool((distances[:, 1:] >= distances[:, :-1]).all()), "ascending native distance order")
        if methods[method]["family"] != "NSG":
            validate_ids(entries, base_n)
        else:
            require(bool((entries[:, 0] == entries[0, 0]).all() and
                         (entries[:, 1:] == -1).all() and (profile.view("<u4") == 0).all()), "NSG fixed single entry")
            require(0 <= int(entries[0, 0]) < base_n, "NSG entry domain")
        mask = membership(ids, gt[:, :k])
        qps = []
        for rr in rounds:
            wall, speed = float(rr["wall_seconds"]), float(rr["qps"])
            require(wall > 0 and math.isfinite(wall) and math.isclose(speed, n/wall, rel_tol=1e-12), "complete-wall QPS")
            require(rr["threads"] == 1 and rr["cpu"] == cfg["cpu"] and rr["stored_round"] == 0 and
                    Path(rr["raw_dir"]).resolve() == raw.resolve(), "round environment and retained packet binding")
            qps.append(speed)
            timings.append({"dataset": dataset, "method": method, "K": k, "L": L, "round": rr["round"],
                            "n": n, "wall_seconds": wall, "qps": speed,
                            "measurement_order": rr["measurement_order"],
                            "actual_timed_packet_equals_stored_round0": 1, "packet_sha256": rr["packet_sha256"]})
        hits = int(mask.sum())
        p = {"dataset": dataset, "metric": "raw_IP" if cfg["metric_id"] == 0 else "L2",
             "method": method, "family": methods[method]["family"], "router": methods[method].get("router", ""),
             "K": k, "L": L, "n": n, "base_n": base_n, "hits": hits,
             "recall_pct": 100.0*hits/(n*k), "qps": float(np.median(qps)), "qps_min": min(qps), "qps_max": max(qps),
             "qps_round0": qps[0], "qps_round1": qps[1], "qps_round2": qps[2],
             "qps_range_pct_of_median": 100.0*(max(qps)-min(qps))/float(np.median(qps)),
             "timing_repeats": 3, "actual_packets_bit_equal": 1, "stored_round": 0, "result_dir": str(result_dir)}
        points.append(p)
        packets[key] = {"ids": ids, "distances": distances, "entries": entries, "profile": profile,
                        "mask": mask, "point": p, "qps": np.asarray(qps)}
    require(set(packets) == grid, "complete frozen method/K/L matrix")
    require(complete["points"] == len(grid) and complete["formal_batches"] == 3*len(grid) and
            complete["formal_queries"] == 3*len(grid)*n, "formal complete counts")
    for method, descriptor in methods.items():
        if descriptor["family"] == "POST":
            for k in KS:
                for L in cfg["K_L"][str(k)]:
                    a, b = packets[method, k, L], packets[descriptor["baseline"], k, L]
                    require(np.array_equal(a["entries"], b["entries"]) and
                            np.array_equal(a["profile"].view("<u4"), b["profile"].view("<u4")), "POST and own GT route identity")
    return cfg, complete, gt, points, timings, packets


def comparison_pairs(cfg):
    pairs = []
    for method in cfg["methods"]:
        if method["family"] == "GT10":
            pairs.append((method["name"], "NSG", "GT10_vs_NSG"))
        elif method["family"] == "POST":
            pairs.append((method["name"], method["baseline"], "residual_vs_own_GT10"))
    return pairs


def compare_dataset(cfg, packets):
    import numpy as np
    rows, bands, cascades = [], [], []
    ds = cfg["dataset"]
    for method, reference, kind in comparison_pairs(cfg):
        for k in KS:
            for L in cfg["K_L"][str(k)]:
                a, b = packets[method, k, L], packets[reference, k, L]
                prefix = {"dataset": ds, "K": k, "L": L, "method": method, "reference_method": reference, "comparison": kind}
                stats = compare_masks(b["mask"], a["mask"], f"{ds}/{method}/{reference}/{k}/{L}")
                paired = a["qps"] / b["qps"]
                speed_ratio = a["point"]["qps"] / b["point"]["qps"]
                rows.append({**prefix, **stats, "qps_ratio_of_medians": speed_ratio,
                             "qps_pct": 100*(speed_ratio-1), "qps_median_paired_ratio": float(np.median(paired)),
                             "paired_qps_ratio_min": float(paired.min()), "paired_qps_ratio_max": float(paired.max()),
                             "faster_rounds": int((paired > 1).sum()),
                             "strict_double_improvement_median": int(stats["net_members"] > 0 and speed_ratio > 1),
                             "qps_ranges_nonoverlap_faster": int(a["point"]["qps_min"] > b["point"]["qps_max"])})
                hits = b["mask"].sum(axis=1)
                for label, lo, hi in (BANDS if k == 100 else (("failure", 0, 0), ("success", 1, 1))):
                    selected = (hits >= lo) & (hits <= hi)
                    result = compare_masks(b["mask"][selected], a["mask"][selected], f"{ds}/{method}/{reference}/{k}/{L}/{label}")
                    bands.append({**prefix, "reference_hit_band": label, **result,
                                  "cohort_defined_by_reference_only": 1})
                if kind == "residual_vs_own_GT10":
                    nsg, gt, post = packets["NSG", k, L]["mask"], b["mask"], a["mask"]
                    lost = nsg & ~gt
                    old_missing = ~nsg & ~gt
                    gt_rescue = ~nsg & gt
                    cascades.append({**prefix, "n": len(nsg),
                                     "NSG_correct_GT10_lost_members": int(lost.sum()),
                                     "of_these_residual_restored_members": int((lost & post).sum()),
                                     "of_these_still_missing_members": int((lost & ~post).sum()),
                                     "both_NSG_GT10_missing_members": int(old_missing.sum()),
                                     "of_these_residual_restored_members_from_joint_failures": int((old_missing & post).sum()),
                                     "GT10_rescued_NSG_missing_members": int(gt_rescue.sum()),
                                     "of_these_residual_lost_again_members": int((gt_rescue & ~post).sum()),
                                     "NSG_full_GT10_failed_queries": int((nsg.all(axis=1) & ~gt.all(axis=1)).sum()),
                                     "of_these_residual_full_success_queries": int((nsg.all(axis=1) & ~gt.all(axis=1) & post.all(axis=1)).sum()),
                                     "GT10_lost_member_restore_rate": ratio(int((lost & post).sum()), int(lost.sum()))})
    return rows, bands, cascades


def branch_values(curve, recall, field="qps"):
    values = []
    for a, b in zip(curve, curve[1:]):
        x0, x1, y0, y1 = a["recall_pct"], b["recall_pct"], a[field], b[field]
        if min(x0, x1) <= recall <= max(x0, x1):
            if x0 == x1:
                values.extend((y0, y1))
            else:
                values.append(y0 + (recall-x0)/(x1-x0)*(y1-y0))
    if len(curve) == 1 and curve[0]["recall_pct"] == recall:
        values.append(curve[0][field])
    require(bool(values), "common-Recall value has measured segment support")
    return sorted(set(values))


def curves_and_cross_L(cfg, points):
    import numpy as np
    interpolation, summaries, discrete = [], [], []
    for method, reference, kind in comparison_pairs(cfg):
        for k in KS:
            a = sorted((p for p in points if p["K"] == k and p["method"] == method), key=lambda p: p["L"])
            b = sorted((p for p in points if p["K"] == k and p["method"] == reference), key=lambda p: p["L"])
            prefix = {"dataset": cfg["dataset"], "K": k, "method": method, "reference_method": reference, "comparison": kind}
            for pa in a:
                for pb in b:
                    if pa["L"] >= pb["L"]:
                        continue
                    discrete.append({**prefix, "L": pa["L"], "reference_L": pb["L"],
                                     "recall_delta_pp": pa["recall_pct"]-pb["recall_pct"],
                                     "qps_pct": 100*(pa["qps"]/pb["qps"]-1),
                                     "strict_double_improvement": int(pa["hits"] > pb["hits"] and pa["qps"] > pb["qps"]),
                                     "is_measured_discrete_pair": 1})
            lower = max(min(p["recall_pct"] for p in a), min(p["recall_pct"] for p in b))
            upper = min(max(p["recall_pct"] for p in a), max(p["recall_pct"] for p in b))
            summary = {**prefix, "common_recall_low_pct": lower, "common_recall_high_pct": upper,
                       "has_common_interval": lower <= upper, "qps_pct_min": None, "qps_pct_max": None,
                       "all_three_round_curves_min_qps_pct": None, "all_three_round_curves_max_qps_pct": None,
                       "all_branches_higher_on_shared_interval": False, "all_branches_lower_on_shared_interval": False,
                       "is_new_equal_recall_measurement": False}
            if lower <= upper:
                knots = {lower, upper, *(p["recall_pct"] for p in a+b if lower <= p["recall_pct"] <= upper)}
                grid = sorted(knots | set(map(float, np.linspace(lower, upper, 101))))
                rows = []
                for x in grid:
                    aa, bb = branch_values(a, x), branch_values(b, x)
                    rr = []
                    for round_id in range(3):
                        av, bv = branch_values(a, x, f"qps_round{round_id}"), branch_values(b, x, f"qps_round{round_id}")
                        rr.append((100*(min(av)/max(bv)-1), 100*(max(av)/min(bv)-1)))
                    rows.append({**prefix, "recall_pct": x, "method_qps_min": min(aa), "method_qps_max": max(aa),
                                 "reference_qps_min": min(bb), "reference_qps_max": max(bb),
                                 "qps_pct_min": 100*(min(aa)/max(bb)-1), "qps_pct_max": 100*(max(aa)/min(bb)-1),
                                 "round0_qps_pct_min": rr[0][0], "round0_qps_pct_max": rr[0][1],
                                 "round1_qps_pct_min": rr[1][0], "round1_qps_pct_max": rr[1][1],
                                 "round2_qps_pct_min": rr[2][0], "round2_qps_pct_max": rr[2][1],
                                 "method_branch_values": len(aa), "reference_branch_values": len(bb),
                                 "is_polyline_breakpoint": int(x in knots), "is_new_equal_recall_measurement": 0})
                bounds = [r for r in rows if r["is_polyline_breakpoint"]]
                summary.update(qps_pct_min=min(r["qps_pct_min"] for r in bounds), qps_pct_max=max(r["qps_pct_max"] for r in bounds),
                               all_three_round_curves_min_qps_pct=min(r[f"round{j}_qps_pct_min"] for r in bounds for j in range(3)),
                               all_three_round_curves_max_qps_pct=max(r[f"round{j}_qps_pct_max"] for r in bounds for j in range(3)))
                summary["all_branches_higher_on_shared_interval"] = summary["qps_pct_min"] > 0
                summary["all_branches_lower_on_shared_interval"] = summary["qps_pct_max"] < 0
                interpolation.extend(rows)
            summaries.append(summary)
    return interpolation, summaries, discrete


def read_table(path, inputs, labels, base_n):
    import numpy as np
    raw = inputs.remember(path).read_bytes()
    magic, version, H, capacity, hash_n, pairs, N, z1, z2 = struct.unpack_from("<8s8I", raw)
    require(magic == b"M5POST1\0" and version == 1 and N == base_n and H == len(labels) and z1 == z2 == 0, "posting header")
    require(len(raw) == 40+13*H+4*H*capacity+8*hash_n, "complete posting file size")
    require(np.array_equal(np.frombuffer(raw, "<i4", H, 40), labels), "posting hub IDs")
    sizes = np.frombuffer(raw, "u1", H, 40+4*H)
    words = np.frombuffer(raw, "<i4", H*capacity, 40+5*H).reshape(H, capacity)
    require(int(sizes.sum()) == pairs, "posting occupancy")
    rows = []
    for h in range(H):
        values = words[h, :sizes[h]]
        require(len(values) <= capacity and len(set(map(int, values))) == len(values), "posting row capacity/uniqueness")
        require(bool(((values >= 0) & (values < N)).all() and (words[h, sizes[h]:] == -1).all()), "posting row domain/padding")
        rows.append(set(map(int, values)))
    json_rows = Path(path).with_suffix(".rows.json")
    if json_rows.exists():
        stored = inputs.json(json_rows)
        require([set(map(int, row)) for row in stored] == rows, "table row JSON/binary sets")
    return rows, capacity, len(raw)


def source_masks(asset, cfg, router, gt, entries, labels, inputs):
    import numpy as np
    model = asset.get("models", {}).get(router)
    if not model:
        return None
    source_dir = Path(model["source_dir"])
    compiled = inputs.json(model["compile_manifest"])
    require(compiled["status"] == "PASS_NEW_K100_NESTED_TABLES" and compiled["name"] == router and
            compiled["teacher_K"] == 100 and compiled["teacher_L"] == 200 and
            compiled["all_test_or_eval_GT_access"] is False and compiled["independent_token_coverage_passed"],
            "TRAIN compiler scope and success")
    offsets = inputs.raw(source_dir / "hub_offsets.u64", "<u8", (len(labels)+1,))
    target_path = source_dir / "hub_targets.i32"
    targets = inputs.raw(target_path, "<i4", (target_path.stat().st_size//4,))
    global_path = source_dir / "global_ids.i32"
    global_ids = inputs.raw(global_path, "<i4", (global_path.stat().st_size//4,))
    token_path = source_dir / "token_targets.i32"
    token_targets = inputs.raw(token_path, "<i4", (token_path.stat().st_size//4,))
    token_queries = inputs.raw(source_dir / "token_queries.i32", "<i4", (len(token_targets),))
    require(len(token_targets) == compiled["tokens"] and bool(((token_queries >= 0) & (token_queries < compiled["residual_n"])).all()), "TRAIN token count/query domain")
    def target_frequency(values):
        targets, counts = np.unique(values, return_counts=True)
        result = np.zeros(gt.shape, dtype=np.int32)
        if len(targets):
            slots = np.searchsorted(targets, gt)
            safe = np.minimum(slots, len(targets)-1)
            found = (slots < len(targets)) & (targets[safe] == gt)
            result[found] = counts[safe[found]]
        return result
    residual_frequency = target_frequency(token_targets)
    require(int(offsets[0]) == 0 and int(offsets[-1]) == len(targets) and bool((offsets[1:] >= offsets[:-1]).all()), "uncapped source CSR")
    source_sets = [set(map(int, targets[int(offsets[h]):int(offsets[h+1])])) for h in range(len(labels))]
    union = set().union(*source_sets)
    require(union == set(map(int, global_ids)) and len(union) == len(global_ids), "global residual source identity")
    slot = {int(label): h for h, label in enumerate(labels)}
    routed = np.zeros(gt.shape, dtype=np.bool_)
    for i, (truth, route) in enumerate(zip(gt, entries)):
        row_sets = [source_sets[slot[int(e)]] for e in route]
        routed[i] = [any(int(t) in pool for pool in row_sets) for t in truth]
    global_mask = np.isin(gt, global_ids)
    require(bool((~routed | global_mask).all()), "route support subset of global TRAIN residual source")
    train_mask = None
    train_frequency = None
    if model.get("training_gt"):
        train_gt = load_gt(model["training_gt"], inputs, int(model["training_n"]))
        train_mask = np.isin(gt, np.unique(train_gt))
        train_frequency = target_frequency(train_gt)
        require(bool((~global_mask | train_mask).all()), "residual source subset of full TRAIN GT")
    return {"global": global_mask, "route": routed, "training": train_mask,
            "source_unique_targets": len(global_ids), "source_hub_target_edges": len(targets), "model": model,
            "source_sets": source_sets, "compiled": compiled,
            "residual_frequency": residual_frequency, "training_frequency": train_frequency}


def candidate_diagnostics(asset, cfg, gt, packets, inputs):
    import numpy as np
    diagnostics, models, boundary_cases, frequency_rows = [], [], [], []
    router_cfg = {r["name"]: r for r in cfg["routers"]}
    cache = {}
    for descriptor in cfg["methods"]:
        if descriptor["family"] != "POST":
            continue
        method, baseline, router = descriptor["name"], descriptor["baseline"], descriptor["router"]
        label_path = Path(router_cfg[router]["ids"])
        H = label_path.stat().st_size//4
        labels = inputs.raw(label_path, "<i4", (H,))
        require(len(set(map(int, labels))) == H, "unique profile hubs")
        slots = {int(label): i for i, label in enumerate(labels)}
        rows, cap, table_bytes = read_table(descriptor["table"], inputs, labels, cfg["base"]["n"])
        first = packets[baseline, 1, cfg["K_L"]["1"][0]]
        for k in KS:
            for L in cfg["K_L"][str(k)]:
                require(np.array_equal(first["entries"], packets[baseline, k, L]["entries"]), "routing independent of K/main L")
        if router not in cache:
            cache[router] = source_masks(asset, cfg, router, gt, first["entries"], labels, inputs)
        support = cache[router]
        unions = [set().union(*(rows[slots[int(e)]] for e in route)) for route in first["entries"]]
        selected = np.asarray([[int(t) in u for t in truth] for truth, u in zip(gt, unions)], dtype=np.bool_)
        if support:
            require(bool((~selected | support["route"]).all()), "selected table support subset of uncapped routed source")
        compiled_model = support["compiled"]["models"][f"JOINT{cap}"] if support else None
        models.append({"dataset": cfg["dataset"], "router": router, "method": method,
                       "base_n": cfg["base"]["n"], "H": H, "B": cap, "H_per_N": H/cfg["base"]["n"],
                       "HB_per_N": H*cap/cfg["base"]["n"], "effective_slots": sum(map(len, rows)),
                       "selected_unique_targets": len(set().union(*rows)), "table_file_bytes": table_bytes,
                       "source_unique_targets": support["source_unique_targets"] if support else None,
                       "source_hub_target_edges": support["source_hub_target_edges"] if support else None,
                       "training_n": support["model"].get("training_n") if support else None,
                       "training_rows_per_hub": support["model"].get("training_n", 0)/H if support else None,
                       "training_missing_tokens": support["compiled"]["tokens"] if support else None,
                       "training_covered_tokens": compiled_model["training_integer_coverage"] if compiled_model else None,
                       "training_in_sample_missing_coverage": ratio(compiled_model["training_integer_coverage"], support["compiled"]["tokens"]) if compiled_model else None,
                       "runtime_plus_stack_bytes_accounted_not_RSS": compiled_model["runtime_plus_stack_bytes"] if compiled_model else None,
                       "compiler_router_seconds_including_all_capacities": support["compiled"]["seconds"] if support else None,
                       "table": descriptor["table"]})
        for k in KS:
            for L in cfg["K_L"][str(k)]:
                actual, ref = packets[method, k, L], packets[baseline, k, L]
                missing = ~ref["mask"]
                rescued = actual["mask"] & missing
                damaged = ref["mask"] & ~actual["mask"]
                available = selected[:, :k] & missing
                unresolved = available & ~actual["mask"]
                nr, nd, nm = int(rescued.sum()), int(damaged.sum()), int(missing.sum())
                require(bool((~rescued | available).all()), "every rescued member available in selected candidates")
                nc = 0
                route_union = 0
                for old, new, union in zip(ref["ids"], actual["ids"], unions):
                    old = set(map(int, old))
                    require(set(map(int, new)).issubset(old | union), "post output subset of actual base output and routed table")
                    nc += len(union-old)
                    route_union += len(union)
                ns = int((support["global"][:, :k] & missing).sum()) if support else None
                nroute = int((support["route"][:, :k] & missing).sum()) if support else None
                ntrain = int((support["training"][:, :k] & missing).sum()) if support and support["training"] is not None else None
                nav = int(available.sum())
                if support:
                    for frequency_kind in ("residual", "training"):
                        frequency = support[frequency_kind+"_frequency"]
                        if frequency is None:
                            continue
                        for label, low, high in FREQUENCY_BANDS:
                            members = (frequency[:, :k] >= low) & (frequency[:, :k] <= high)
                            mm = missing & members
                            denominator = int(mm.sum())
                            rescue = int((rescued & members).sum())
                            damage = int((damaged & members).sum())
                            correct = int((ref["mask"] & members).sum())
                            frequency_rows.append({"dataset": cfg["dataset"], "K": k, "L": L, "method": method,
                                                   "reference_method": baseline, "frequency_kind": frequency_kind+"_query_count",
                                                   "training_target_query_frequency": label, "missing_members": denominator,
                                                   "correct_members": correct,
                                                   "missing_in_residual_source": int((mm & support["global"][:, :k]).sum()),
                                                   "missing_in_uncapped_routed_source": int((mm & support["route"][:, :k]).sum()),
                                                   "missing_in_selected_table": int((mm & selected[:, :k]).sum()),
                                                   "rescued_members": rescue, "damaged_members": damage,
                                                   "rescue_rate_on_missing": ratio(rescue, denominator), "damage_rate_on_correct": ratio(damage, correct)})
                for qi in np.flatnonzero(unresolved.any(axis=1) | damaged.any(axis=1)):
                    boundary_cases.append({"dataset": cfg["dataset"], "K": k, "L": L, "method": method,
                                           "reference_method": baseline, "query_row": int(qi),
                                           "candidate_available_but_not_returned_GT_ids": json.dumps(gt[qi, :k][unresolved[qi]].tolist()),
                                           "damaged_GT_ids": json.dumps(gt[qi, :k][damaged[qi]].tolist()),
                                           "reference_boundary_id": int(ref["ids"][qi, -1]),
                                           "reference_boundary_native_distance": float(ref["distances"][qi, -1]),
                                           "actual_boundary_id": int(actual["ids"][qi, -1]),
                                           "actual_boundary_native_distance": float(actual["distances"][qi, -1]),
                                           "numeric_cause_verified_by_analyzer": 0})
                diagnostics.append({"dataset": cfg["dataset"], "K": k, "L": L, "method": method, "reference_method": baseline,
                                    "n": len(gt), "H": H, "B": cap, "missing_members": nm,
                                    "missing_in_full_training_GT": ntrain, "missing_in_global_residual_source": ns,
                                    "missing_in_uncapped_routed_source": nroute, "missing_in_selected_routed_table": nav,
                                    "rescued_members": nr, "damaged_members": nd, "net_members": nr-nd,
                                    "unseen_by_residual_source": nm-ns if ns is not None else None,
                                    "source_present_but_route_missed": ns-nroute if ns is not None else None,
                                    "routed_source_present_but_capacity_missed": nroute-nav if nroute is not None else None,
                                    "candidate_present_but_not_rescued": nav-nr,
                                    "source_coverage_fraction": ratio(ns, nm) if ns is not None else None,
                                    "route_conditional_coverage_fraction": ratio(nroute, ns) if ns is not None else None,
                                    "capacity_conditional_coverage_fraction": ratio(nav, nroute) if nroute is not None else None,
                                    "selected_missing_coverage_fraction": ratio(nav, nm),
                                    "actual_candidates_outside_GT": nc, "route_union_candidates": route_union,
                                    "actual_candidates_per_query": nc/len(gt), "candidate_GT_fraction": ratio(nav, nc),
                                    "net_GT_per_scored_candidate": ratio(nr-nd, nc),
                                    "counts_reconstructed_after_timing": 1})
    return diagnostics, models, boundary_cases, frequency_rows


def plots(cfgs, points, deltas, diagnostics, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42, "svg.fonttype": "none"})
    figures = []
    for cfg in cfgs:
        dataset = cfg["dataset"]
        methods = [m["name"] for m in cfg["methods"]]
        colors = plt.get_cmap("tab10").colors
        fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), constrained_layout=True)
        for ax, k in zip(axes, KS):
            for j, method in enumerate(methods):
                curve = sorted((p for p in points if p["dataset"] == dataset and p["K"] == k and p["method"] == method), key=lambda p:p["L"])
                xs, ys = [p["recall_pct"] for p in curve], [p["qps"] for p in curve]
                err = [[p["qps"]-p["qps_min"] for p in curve], [p["qps_max"]-p["qps"] for p in curve]]
                ax.errorbar(xs, ys, yerr=err, color=colors[j%10], marker="os^DvP*X"[j%8], markersize=4,
                            capsize=2, linewidth=1.3, label=method)
            ax.set_title(f"Recall@{k}")
            ax.set_xlabel("Recall (%)")
            ax.set_ylabel("Complete-wall QPS (T1)")
            ax.grid(alpha=.25)
            ax.ticklabel_format(axis="y", style="plain", useOffset=False)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="outside lower center", ncol=min(len(methods), 4), fontsize=9, frameon=False)
        metric = "raw IP" if cfg["metric_id"] == 0 else "L2"
        fig.suptitle(f"E183 | {LABELS.get(dataset,dataset)} | {metric} | N={cfg['base']['n']:,}, queries={cfg['queries']['n']:,}\n"
                     "Markers: measured points; lines: descriptive connections; bars: 3-round min-max", fontsize=11)
        stem = "curves_"+dataset
        for ext in ("png", "svg", "pdf"):
            fig.savefig(out/f"{stem}.{ext}", dpi=190, bbox_inches="tight")
        plt.close(fig)
        figures.append({"path": str(out/f"{stem}.png"), "title": f"{LABELS.get(dataset,dataset)}：完整 Recall–QPS 曲线；三轮范围"})
    return figures


def fmt(value, digits=2, signed=False):
    if value is None:
        return "NA"
    return format(value, ("+" if signed else "")+f".{digits}f")


def review_evidence(inputs):
    """Read explicit review artifacts only; absent evidence stays absent."""
    paths = {
        "GT_sample": ROOT/"reviews/gt_sample_audit_exact_summary.json",
        "input_SHA": ROOT/"reviews/input_freeze.json",
        "source_review": ROOT/"reviews/independent_native_source_review_v2.json",
        "qualification_regression": ROOT/"reviews/qualification_regression.json",
        "independent_results": ROOT/"reviews/independent_results_audit.json",
        "boundaries": ROOT/"reviews/boundary_diagnostics.json",
        "costs": ROOT/"analysis/cost_ledger.json",
    }
    return {name: {"path": str(path), "record": inputs.json(path)} for name, path in paths.items() if path.exists()}


def evidence_paragraphs(evidence):
    lines = ["## 已完成的资格、独立核验与费用", ""]
    if "GT_sample" in evidence:
        r = evidence["GT_sample"]["record"]
        lines += [f"独立float64全库GT抽样审计共 {r['samples']} 个训练/测试实例：Top1身份一致 {r['top1_equal']}/{r['samples']}，"
                  f"Top100集合一致 {r['top100_set_equal']}/{r['samples']}。没有用容差接受成员集合差异。这里是固定样本抽审，不是全工作负载GT重新计算。", ""]
    if "input_SHA" in evidence:
        r = evidence["input_SHA"]["record"]
        lines += [f"训练前对 {len(r['files'])} 个已有真实输入/来源文件完成当前完整SHA绑定，耗时 {fmt(r['elapsed_seconds'])} 秒。新生成表、二进制及正式输入再由各阶段执行锁绑定；这项输入身份核对不等同于方法质量验证。", ""]
    labels = {"source_review": "独立源码及合成资格", "qualification_regression": "历史输出回归资格",
              "independent_results": "独立正式结果复算", "boundaries": "重复向量及数值边界诊断"}
    lines += ["| 核验 | 实际收据状态 |", "|---|---|"]
    for key, label in labels.items():
        record = evidence.get(key, {}).get("record")
        lines.append(f"| {label} | {record.get('status', '无status字段') if record is not None else '未提供收据；不声称已完成'} |")
    lines += ["", "源码审查只证明审过的实现条件；历史输出回归只覆盖它登记的预算与样本。实际计时整包、合并oracle、独立整数统计和GT抽审各有范围，不能相互替代。", ""]
    if "independent_results" in evidence:
        r = evidence["independent_results"]["record"]
        lines += [f"独立脚本未导入主分析器，使用逐查询整数集合复算 {r['points']} 个正式点、{r['formal_batches']} 轮时间身份、"
                  f"{r['same_L_pairs']} 组同L救损、{r['failure_strata']} 个失败分层及 {r['coverage_rows']} 条源/路由/容量分解，且独立重建全部训练遗漏源池。"
                  "Bootstrap区间与折线插值没有被该脚本独立重算；它也不重做真实数据的全部贪心选表顺序或再次执行原生图搜索。", ""]
    if "costs" in evidence:
        r = evidence["costs"]["record"]
        lines += ["以下为实际新阶段费用；每格是从launch到输出核验的阶段wall，已经包含其中原生子程序。继承图、画像和GT的完整冷启动费用没有重测，保留未知与历史原始账本。", "",
                  "| 数据 | 新teacher秒 | 新编表秒 | 资格秒 | 正式阶段秒 |", "|---|---:|---:|---:|---:|"]
        for ds, item in r["datasets"].items():
            stages = item["new_stages"]
            values = [fmt(stages[k]["launch_through_output_checks_seconds"]) for k in ("teacher", "compile", "qualification", "benchmark")]
            lines.append(f"| {LABELS.get(ds,ds)} | "+" | ".join(values)+" |")
        lines += ["", f"离线suite {fmt(r['offline_suite_seconds'])}秒、正式suite {fmt(r['formal_suite_seconds'])}秒是外层口径，不能再与上表阶段加总。"
                  f"输入完整SHA {fmt(r['input_full_SHA_seconds'])}秒、抽样GT审计 {fmt(r['sample_GT_audit_seconds'])}秒曾部分重叠，也不能把其和称为项目关键路径时长。"
                  "构建及保留的初次尝试、核验费用、嵌套关系详见原cost_ledger；未测精确峰值RSS，不以表文件大小替代。", ""]
    if "boundaries" in evidence:
        r = evidence["boundaries"]["record"]
        lines += [f"数值诊断完成 {r['boundary_query_point_rows']} 条查询工作点、{r['member_events']} 个成员事件，涉及 {r['unique_dataset_queries']} 条不同查询；"
                  f"其中需继续核查的成员事件为 {r['unresolved_member_events']}。同一query/target在多个L或方法重复出现不是独立证据。", "",
                  "| 边界分类 | 成员事件数 |", "|---|---:|"]
        for category, count in sorted(r["category_counts"].items()):
            lines.append(f"| {category} | {count} |")
        lines += ["", "数值诊断保持原正式GT与ID命中统计：完全相同向量的不同ID可证明几何并列；只有两侧原生分数都留存且与原float32坐标的精确有理数度量次序相反时，才能确认原生排序倒置。只有接近边界而缺少候选原生分数的实例，只能归为近并列迹象，不能宣称已证明原生tie或算法无损。精确几何次序与既有float32原生/GT计分合同分别保留，未定事件不被强行归因。", ""]
    lines += ["证据索引："]
    for name, value in evidence.items():
        lines.append(f"- {name}: {value['path']}")
    lines.append("")
    return lines


def finalize_report(source, out):
    """Text-only final delivery, preserving original numeric analysis and report."""
    source, out = source.resolve(), out.resolve()
    require(source.is_relative_to(ROOT/"analysis") and out.is_relative_to(ROOT/"analysis"), "campaign-local report delivery")
    require(source != out and (not out.exists() or not any(out.iterdir())), "new distinct delivery directory")
    started = time.monotonic()
    inputs = Inputs()
    inputs.remember(__file__)
    summary = inputs.json(source/"summary.json")
    receipt = inputs.json(source/"analysis_receipt.json")
    require(summary["status"] == receipt["status"] == "PASS_E183_RETAINED_OUTPUT_ANALYSIS", "successful original numeric analysis")
    report_path = inputs.remember(source/"report_zh.md")
    expected = receipt["outputs"][str(report_path)]
    require(inputs.identities[str(report_path)]["sha256"] == expected["sha256"], "preserved original report SHA")
    evidence = review_evidence(inputs)
    require("independent_results" in evidence and evidence["independent_results"]["record"]["status"].startswith("PASS"), "actual independent result audit must precede final delivery")
    require("costs" in evidence and evidence["costs"]["record"]["status"] == "PASS_ACTUAL_COST_LEDGER", "actual cost ledger must precede final delivery")
    if summary["boundary_cases"]:
        require("boundaries" in evidence and evidence["boundaries"]["record"]["status"] in
                ("PASS_BOUNDARY_DIAGNOSTICS_COMPLETED", "BOUNDARY_DIAGNOSTICS_COMPLETED_WITH_UNRESOLVED_CASES"),
                "completed boundary diagnostics must precede final delivery; unresolved causes stay disclosed")
    text = report_path.read_text()
    old = "独立结果审计和逐例数值诊断如另有文件，应与本报告一同阅读；本分析器本身不宣称独立人员审计完成。"
    text = text.replace(old, "独立正式结果复算已完成；实际收据与数值诊断的范围列在下节。统计作者与独立审计者分开。")
    text += "\n"+"\n".join(evidence_paragraphs(evidence))
    out.mkdir(parents=True, exist_ok=True)
    with (out/"report_zh.md").open("x", encoding="utf-8") as stream:
        stream.write(text)
    delivery = dict(summary)
    delivery.update(independent_result_audit_pending=False, numeric_analysis_source=str(source),
                    qualification_evidence=evidence, report_finalization_only=True)
    save_json(out/"summary.json", delivery)
    save_json(out/"evidence_receipts.json", evidence)
    inputs.unchanged()
    save_json(out/"report_finalization_receipt.json", {"status": "PASS_TEXT_ONLY_E183_FINAL_REPORT", "elapsed_seconds": time.monotonic()-started,
              "inputs": inputs.identities, "numeric_analysis_source": str(source), "numeric_analysis_recomputed": False,
              "original_report_preserved": True, "ANN_traversals": 0, "vector_scores_computed": 0,
              "outputs": {str(p): {"sha256": sha(p), "bytes": p.stat().st_size} for p in out.iterdir() if p.is_file()}})
    print(json.dumps({"status": "PASS_TEXT_ONLY_E183_FINAL_REPORT", "out": str(out)}), flush=True)


def report(summary, cfgs, points, deltas, strata, cascades, diagnostics, models, frequencies, out):
    lines = ["# GT10 与残差补全：七数据集及失败查询评估", "", "E183 · 2026-10-17 · 完整单线程计时 · 原始结果与统计可追溯", "",
             "## 先看结论与证据范围", "",
             f"本轮完成 {len(cfgs)} 个数据集、{len(points)} 个真实 K/L/方法工作点、{3*len(points)} 次完整计时。每点保存第一轮实际输出，后两轮由原生程序逐位核对整包一致；Recall 来自该实际计时输出。当前生产默认仍为 E99 GT10，本报告不自动变更默认。", "",
             "GT10 的贡献以同一图和主搜索核下的 GT10 对 NSG 衡量；残差的贡献以每个 GT10 家族自己的补全版本对其 GT10 衡量。hard/soft 各用自己的冻结训练残差表。残差指补算训练遗漏目标的候选表，不是向量量化误差。没有 NSG+残差这一额外组，因此本轮不声称识别完整 2×2 交互因果效应。", "",
             "曲线须在共同 Recall 区间内比较。线段插值只描述已测点的连接，不是新增等 Recall 测量；所有非单调分支均保留。每点 QPS 为三轮中位数，误差线为最小到最大值。三次计时反映本次运行间变化，不能据此保证换机器、换图或新查询仍有同样速度。", "",
             "下表先把非多模态 L2 数据与多模态 IP 数据分开读；每个格子概括完整共同区间，不是挑一个有利工作点。", "",
             "| 数据 / metric | 家族 | GT10对NSG：K1 / K100 | B32对GT10：K1 / K100 |", "|---|---|---|---|"]
    def curve_label(ds, method, k):
        r = next(r for r in summary["curve_summaries"] if r["dataset"] == ds and r["method"] == method and r["K"] == k)
        if not r["has_common_interval"]:
            return "无共同区间"
        if r["all_branches_higher_on_shared_interval"]:
            return "全段更高；三轮一致" if r["all_three_round_curves_min_qps_pct"] > 0 else "全段更高；三轮不全同向"
        if r["all_branches_lower_on_shared_interval"]:
            return "全段更低；三轮一致" if r["all_three_round_curves_max_qps_pct"] < 0 else "全段更低；三轮不全同向"
        return "交叉或相接"
    for cfg in sorted(cfgs, key=lambda c: (-c["metric_id"], c["dataset"])):
        for gtmethod in (m for m in cfg["methods"] if m["family"] == "GT10"):
            post = next(m for m in cfg["methods"] if m["family"] == "POST" and m["baseline"] == gtmethod["name"] and "32" in m["name"])
            ds = cfg["dataset"]
            lines.append(f"| {LABELS.get(ds,ds)} / {'L2' if cfg['metric_id'] else 'IP'} | {gtmethod['router']} | "
                         f"{curve_label(ds,gtmethod['name'],1)} / {curve_label(ds,gtmethod['name'],100)} | "
                         f"{curve_label(ds,post['name'],1)} / {curve_label(ds,post['name'],100)} |")
    lines += ["",
             "## 数据、距离与角色", "",
             "L2 数据集保持原欧氏目标；IP 数据集保持原始内积目标。训练画像内部的方向归一化不意味着改变 base/query 或测试目标。L2、cosine、raw-IP 的排序通常不同；没有把各数据集改成统一 cosine。COCO/Flickr 的 GT 是特征空间近邻，不是人工语义配对标签。", "",
             "| 数据 | metric | base N | 维度 | test query | 方法数 |", "|---|---|---:|---:|---:|---:|"]
    for c in cfgs:
        lines.append(f"| {LABELS.get(c['dataset'],c['dataset'])} | {'raw-IP' if c['metric_id']==0 else 'L2'} | {c['base']['n']:,} | {c['base']['d']} | {c['queries']['n']:,} | {len(c['methods'])} |")
    lines += ["", "训练角色关系保留各来源原合同：L2 与既有 Web/Yandex 的残差 TRAIN 可与原画像拟合来源共享，COCO/Flickr 的残差与画像训练角色则分开。两种设计均要求测试身份排除，不能把它们混称相同的训练角色控制。逐数据原文范围见 result_metadata.json 中 catalogue_entry.training_role_scope。"]
    lines += ["", "本轮核与本轮 NSG/GT10 对照配套；不得将绝对 QPS 与 E103 的 span+batch4 历史实现直接拼接。复用历史模型、图和已曝光测试源的身份见各数据配置与来源记录；重复计时不把已曝光数据变成新盲测。", "",
              "## 两个独立问题：GT10 与残差", "",
              "下表逐数据、逐 K 列出完整共同区间的折线 QPS 变化范围。正负混合意味着曲线交叉或分支重叠；同 L 更慢不自动否定共同 Recall 区间改善。表中范围来自点中位数曲线，不是置信区间。", "",
              "| 数据 / K | 对照 | 共同 Recall (%) | 折线 QPS 变化 (%) |", "|---|---|---|---|"]
    for r in summary["curve_summaries"]:
        interval = f"{fmt(r['common_recall_low_pct'])}–{fmt(r['common_recall_high_pct'])}" if r['has_common_interval'] else "无共同区间"
        lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['K']} | {r['method']} / {r['reference_method']} | {interval} | {fmt(r['qps_pct_min'],2,True)}～{fmt(r['qps_pct_max'],2,True)} |")
    lines += ["", "完整已测点另存 points.csv；跨 L 的真实离散比较另存 measured_cross_L.csv。二者与插值各自保留，不用离散点无双升否定整个折线，也不用折线证明未经测量的执行点。", "",
              "### 固定 L200 的实际 Recall 与 QPS", "",
              "下表格内为 Recall(%) / 完整单线程 QPS中位数；没有把不同L当成同预算。", "",
              "| 数据 | 方法 | K1：Recall / QPS | K100：Recall / QPS |", "|---|---|---:|---:|"]
    for cfg in cfgs:
        ds = cfg["dataset"]
        for method in (m["name"] for m in cfg["methods"]):
            a = next(p for p in points if p["dataset"] == ds and p["method"] == method and p["K"] == 1 and p["L"] == 200)
            b = next(p for p in points if p["dataset"] == ds and p["method"] == method and p["K"] == 100 and p["L"] == 200)
            lines.append(f"| {LABELS.get(ds,ds)} | {method} | {fmt(a['recall_pct'],4)} / {fmt(a['qps'])} | {fmt(b['recall_pct'],4)} / {fmt(b['qps'])} |")
    lines += ["",
              "## 失败查询怎样计数", "",
              "K1 失败指对应基线未返回指定 GT1。救回率 = 基线失败中被方法命中的查询数 / 基线失败数；损伤率 = 基线成功中被方法弄丢的查询数 / 基线成功数。两个分母不同，不能只报净增。K100 按真实 GT100 成员统计补回与丢失，并按对应基线命中数分为 0、1–10、11–50、51–90、91–99、100。零命中与低命中分开，100组单列以显式检查原来正确的查询是否受损；另报90/100和100/100两个预定质量门槛的正反转移。", "",
              "95% Recall 差区间按查询成对 bootstrap，K100 的100个成员作为一个查询簇共同重采样；固定3000次和seed20261017。K1 条件救回/损伤率另给 Wilson 95%区间。所有区间是描述性、未做多重比较校正；同一图片的多caption或其他查询相关性可能让独立查询假设偏乐观。分层由基线定义，但属于测试后的诊断，不训练门控或择优模型。", "",
              "### 固定 L200：先分清 GT10 自己带来的救回与损伤", "",
              "| 数据 / K | GT10 | 基线遗漏 | 补回 / 丢失 | ΔRecall pp [95%区间] | ΔQPS % |", "|---|---|---:|---:|---|---:|"]
    for r in deltas:
        if r["L"] == 200 and r["comparison"] == "GT10_vs_NSG":
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['K']} | {r['method']} | {r['reference_missing_members']} | {r['rescued_members']} / {r['damaged_members']} | {fmt(r['recall_delta_pp'],4,True)} [{fmt(r['recall_delta_pp_bootstrap95_low'],4)},{fmt(r['recall_delta_pp_bootstrap95_high'],4)}] | {fmt(r['qps_pct'],2,True)} |")
    lines += ["", "### 固定 L200：残差对各自 GT10 的增量", "",
              "| 数据 / K | 残差版本 | 基线遗漏 | 补回 / 丢失 | 救回率 / 损伤率 (%) | ΔQPS % |", "|---|---|---:|---:|---|---:|"]
    for r in deltas:
        if r["L"] == 200 and r["comparison"] == "residual_vs_own_GT10":
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['K']} | {r['method']} | {r['reference_missing_members']} | {r['rescued_members']} / {r['damaged_members']} | {fmt(None if r['rescue_rate_on_missing'] is None else 100*r['rescue_rate_on_missing'],3)} / {fmt(None if r['damage_rate_on_correct'] is None else 100*r['damage_rate_on_correct'],4)} | {fmt(r['qps_pct'],2,True)} |")
    lines += ["", "固定 L200 仅是事先指定的可比示例；完整宽 L 结果未被这个示例替代。same_L_deltas.csv 保存所有区间与分母，failure_strata.csv 保存每个难度层。", "",
              "### GT10 新增失败，残差能救回多少", "",
              "这里仅跟踪 NSG 原本命中、GT10 后遗漏的成员；与 NSG、GT10 都失败的成员分别计数。K100 的成员恢复不等于整条查询达到100/100。", "",
              "| 数据 / K | 残差版本，L200 | NSG正确→GT丢失 | 残差再救回 | 仍未恢复 |", "|---|---|---:|---:|---:|"]
    for r in cascades:
        if r["L"] == 200:
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['K']} | {r['method']} | {r['NSG_correct_GT10_lost_members']} | {r['of_these_residual_restored_members']} | {r['of_these_still_missing_members']} |")
    lines += ["", "### K100 难度分层（L200，B32版本）", "",
              "| 数据 / 方法 | 基线命中层 | 查询数 | 遗漏成员 | 补回 / 丢失 | 净改善 / 净变差查询 |", "|---|---|---:|---:|---:|---:|"]
    for r in strata:
        if r["K"] == 100 and r["L"] == 200 and "32" in r["method"]:
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['method']} | {r['reference_hit_band']} | {r['n']} | {r['reference_missing_members']} | {r['rescued_members']} / {r['damaged_members']} | {r['net_improved_queries']} / {r['net_worsened_queries']} |")
    lines += ["", "### K100 质量门槛转移（L200，B32版本）", "",
              "90门槛恢复指原命中少于90个、补全后至少90个；完整恢复指原少于100个、补全后100个。损伤列分别是相反方向，分母都保存在完整CSV中。", "",
              "| 数据 / 方法 | 90门槛恢复 / 损伤 | 100完整恢复 / 损伤 |", "|---|---:|---:|"]
    for r in deltas:
        if r["K"] == 100 and r["L"] == 200 and "32" in r["method"]:
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['method']} | {r['below_90pct_become_at_least_90pct_queries']} / {r['at_least_90pct_become_below_90pct_queries']} | {r['failed_queries_become_full_success']} / {r['full_success_queries_become_failed']} |")
    lines += ["", "## 从训练源到真实救回：覆盖漏在哪里", "",
              "固定测试遗漏集合后依次检查：是否在训练残差目标并集中；是否在当前查询路由到的三个 hub 未截断候选池中；是否被有限容量表保留；最后是否进入真实 topK。每一步都用同一批遗漏成员作计数，分别反映源支持、路由、容量和最终排序边界。这是观察性分解，不能单独证明修改该环节必有净 Recall–QPS 收益。", "",
              "| 数据 / B32方法 | L200/K100遗漏 | 源支持 | 三路由未截断 | 表保留 | 实际救回 | 实际补算/query |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in diagnostics:
        if r["K"] == 100 and r["L"] == 200 and r["B"] == 32:
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['method']} | {r['missing_members']} | {r['missing_in_global_residual_source']} | {r['missing_in_uncapped_routed_source']} | {r['missing_in_selected_routed_table']} | {r['rescued_members']} | {fmt(r['actual_candidates_per_query'])} |")
    lines += ["", "### 训练目标频次与修复（L200/K100，B32版本）", "",
              "全TRAIN GT频次是目标出现在多少条训练query的GT100中；残差频次是其中多少条query还漏掉该目标。两者分别保存，不能用残差高频代表全体目标高频。固定频次桶为0、1、2–5、6–20、21+。下表用残差频次，完整两类频次分层见target_frequency.csv。", "",
              "| 数据 / 方法 | 残差频次 | 测试遗漏 | 实际补回 / 损伤 | 遗漏救回率 (%) |", "|---|---|---:|---:|---:|"]
    for r in frequencies:
        if r["K"] == 100 and r["L"] == 200 and "32" in r["method"] and r["frequency_kind"] == "residual_query_count":
            lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['method']} | {r['training_target_query_frequency']} | {r['missing_members']} | {r['rescued_members']} / {r['damaged_members']} | {fmt(None if r['rescue_rate_on_missing'] is None else 100*r['rescue_rate_on_missing'],3)} |")
    lines += ["", "候选已存在却未按ID救回，可能涉及浮点边界或重复向量的不同ID；不能仅凭这个差额认定算法错误或没有几何救回。正式ID指标保留原GT定义，不临时换成宽松tie指标。未作高精度逐例验证的差额只能标为待分类；所有成员损伤也保留。", "",
              "## 容量、费用与计时差异", "",
              "H/N 反映入口密度，HB/N 反映候选表槽位密度。不同数据集的规模、图、维度、metric和训练密度共同变化，不能将差异单归因于是否多模态。固定B32意味着三路由最多96个未去重候选；实际补算须排除原返回和重复ID。", "",
              "| 数据 / 方法 | H | B | H/N (%) | HB/N | 文件 KiB | TRAIN/hub |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in models:
        lines.append(f"| {LABELS.get(r['dataset'],r['dataset'])} / {r['method']} | {r['H']} | {r['B']} | {fmt(100*r['H_per_N'],4)} | {fmt(r['HB_per_N'],4)} | {fmt(r['table_file_bytes']/1024)} | {fmt(r['training_rows_per_hub'])} |")
    lines += ["", "文件字节不是进程RSS。在线QPS包括正常批次分配、路由、主图搜索、残差补算、合并、统一输出保留与正常销毁；加载、训练和分析分账。外层任务耗时已经包含内部计时、预热与审计，不能重复相加。复用旧资产的历史训练费用不清零，缺失收据填未知而不是0。", "",
              "| 数据 | 原生外层秒 | 三轮正式wall合计秒（内含） | 最大单点三轮跨度/中位数 |", "|---|---:|---:|---:|"]
    for cfg in cfgs:
        ds = cfg["dataset"]
        c = summary["costs"][ds]
        lines.append(f"| {LABELS.get(ds,ds)} | {fmt(c['native_outer_seconds'])} | {fmt(c['formal_wall_seconds_nested'])} | {fmt(c['max_point_qps_range_pct'])}% |")
    lines += ["", "## 结论边界与可复核产物", "",
              "这轮回答的是冻结资产、固定容量和宽预算下的实际泛化表现与失败恢复。训练不读取测试遗漏，诊断结果不回流拟合；未增加数据依赖的在线选择器。三轮质量输出一致可验证实现确定性，但不能替代独立训练seed、独立主图、独立来源测试。原始ID统计、高精度tie诊断和因果解释应分开。", "",
              "points.csv 是完整测点；timings.csv 是三轮逐批时间；same_L_deltas.csv 是配对救损及区间；failure_strata.csv 是预定难度层；failure_cascade.csv 是新增失败再救回；candidate_coverage.csv 是源/路由/容量分解；curve_interpolation.csv 和 curve_summaries.json 是标记清楚的折线描述；measured_cross_L.csv 是真实跨预算点；capacity_models.csv 是容量与表成本；inputs_manifest.json 绑定本分析实际读取的输入。", "",
              "boundary_cases.csv 保留每条候选可用未救回及成员损伤的查询编号、GT ID和边界分数，不擅自认定为数值并列。独立结果审计和逐例数值诊断如另有文件，应与本报告一同阅读；本分析器本身不宣称独立人员审计完成。报告图在后附独立页面，每个数据集均保留 K1/K100 全预算与全部方法。", ""]
    with (out / "report_zh.md").open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, nargs="+", help="Analysis JSONs; default configs/*.analysis.json")
    parser.add_argument("--out", type=Path, default=ROOT / "analysis" / "final_v1")
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--finalize-report", type=Path, help="Text-only: source analysis directory; requires final independent audit/cost/boundary receipts")
    args = parser.parse_args()
    if args.finalize_report:
        finalize_report(args.finalize_report, args.out)
        return
    started = time.monotonic()
    order = {name: i for i, name in enumerate(DATASET_ORDER)}
    assets_paths = args.assets or sorted((ROOT / "configs").glob("*.analysis.json"),
                                         key=lambda p: order.get(p.name.removesuffix(".analysis.json"), len(order)))
    require(bool(assets_paths), "analysis asset mappings available")
    # Do not compete with timing: check ALL requested native jobs before imports/numerics.
    for path in assets_paths:
        asset = json.loads(path.read_text())
        cfg = json.loads(Path(asset["benchmark_config"]).read_text())
        complete = Path(cfg["output_dir"]) / "complete.json"
        require(complete.exists() and json.loads(complete.read_text())["status"] == "PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES", "all formal jobs must finish first")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = "1"
    available = os.sched_getaffinity(0)
    if 14 in available:
        os.sched_setaffinity(0, {14})
    out = args.out.resolve()
    require(out.is_relative_to(ROOT / "analysis"), "campaign-local analysis output")
    require(not out.exists() or not any(out.iterdir()), "preserve all previous analysis outputs; choose new --out")
    out.mkdir(parents=True, exist_ok=True)
    inputs = Inputs()
    inputs.remember(__file__)
    cfgs, metadata, points, timings, deltas, strata, cascades = [], {}, [], [], [], [], []
    diagnostics, models, boundary_cases, frequencies, interpolation, curves, discrete, costs = [], [], [], [], [], [], [], {}
    for path in assets_paths:
        asset = inputs.json(path)
        cfg, complete, gt, pp, tt, packets = read_dataset(asset, inputs)
        ds = cfg["dataset"]
        require(ds not in metadata, "unique dataset analysis mapping")
        cfgs.append(cfg)
        points.extend(pp)
        timings.extend(tt)
        dd, ss, cc = compare_dataset(cfg, packets)
        deltas.extend(dd)
        strata.extend(ss)
        cascades.extend(cc)
        cand, cap, boundary, freq = candidate_diagnostics(asset, cfg, gt, packets, inputs)
        diagnostics.extend(cand)
        models.extend(cap)
        boundary_cases.extend(boundary)
        frequencies.extend(freq)
        ii, cs, xx = curves_and_cross_L(cfg, pp)
        interpolation.extend(ii)
        curves.extend(cs)
        discrete.extend(xx)
        receipts = {str(p): inputs.json(p) for p in asset.get("cost_receipts", [])}
        costs[ds] = {"native_outer_seconds": complete.get("outer_seconds"),
                     "formal_wall_seconds_nested": sum(t["wall_seconds"] for t in tt),
                     "max_point_qps_range_pct": max(p["qps_range_pct_of_median"] for p in pp),
                     "provided_cost_receipts": receipts, "inherited_historical_costs_not_assumed_zero": True}
        source_manifest = inputs.json(asset["source_manifest"]) if asset.get("source_manifest") else None
        metadata[ds] = {"analysis_asset": asset, "config": cfg, "complete": complete, "source_manifest": source_manifest}
        print(json.dumps({"dataset": ds, "status": "ANALYZED", "points": len(pp), "elapsed_seconds": time.monotonic()-started}), flush=True)
        del packets
    summary = {"status": "PASS_E183_RETAINED_OUTPUT_ANALYSIS", "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "dataset_count": len(cfgs), "points": len(points), "formal_batches": len(timings),
               "same_L_comparisons": len(deltas), "boundary_cases": len(boundary_cases), "curve_summaries": curves, "costs": costs,
               "CI": {"method": "paired query bootstrap via integer-difference multinomial", "repetitions": REPS,
                      "seed": SEED, "level": .95, "multiple_comparison_adjustment": False,
                      "K1_conditional_rates": "Wilson interval; zero denominator -> null", "QPS_confidence_interval": "none; three-round range only"},
               "timed_packet_evidence": "Stored actual round0 packet; round1/2 native full-bit equality and SHA receipts. No later ANN replay replaces timed data.",
               "interpolation": "Descriptive ascending-L polyline only; all branches retained, no extrapolation. Extrema at union of recall knots; not measured equal-Recall comparison.",
               "new_ANN_traversals": 0, "new_vector_scores": 0, "default_changed": False,
               "independent_result_audit_pending": True}
    for filename, rows in (("points.csv", points), ("timings.csv", timings), ("same_L_deltas.csv", deltas),
                           ("failure_strata.csv", strata), ("failure_cascade.csv", cascades),
                           ("candidate_coverage.csv", diagnostics), ("capacity_models.csv", models), ("boundary_cases.csv", boundary_cases),
                           ("target_frequency.csv", frequencies),
                           ("curve_interpolation.csv", interpolation), ("measured_cross_L.csv", discrete)):
        save_csv(out/filename, rows, BOUNDARY_FIELDS if filename == "boundary_cases.csv" else None)
    save_json(out / "curve_summaries.json", curves)
    save_json(out / "cost_ledger.json", costs)
    save_json(out / "result_metadata.json", metadata)
    summary["figures"] = [] if args.skip_plots else plots(cfgs, points, deltas, diagnostics, out)
    report(summary, cfgs, points, deltas, strata, cascades, diagnostics, models, frequencies, out)
    save_json(out / "summary.json", summary)
    inputs.unchanged()
    save_json(out / "inputs_manifest.json", {"status": "PASS_CONSUMED_IDENTITIES", "inputs": inputs.identities,
              "scope": "Only consumed outputs/GT/tables/manifests hashed. No base/query/graph payload read by analyzer."})
    outputs = {str(p): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in out.iterdir() if p.is_file()}
    save_json(out / "analysis_receipt.json", {"status": summary["status"], "elapsed_seconds": time.monotonic()-started,
              "script_sha256": sha(__file__), "outputs": outputs, "ANN_traversals": 0, "vector_scores_computed": 0,
              "timed_measurements_added": 0, "independent_result_audit_pending": True})
    print(json.dumps({"status": summary["status"], "points": len(points), "out": str(out)}), flush=True)


if __name__ == "__main__":
    main()
