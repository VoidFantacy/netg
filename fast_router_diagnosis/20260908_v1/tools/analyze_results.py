#!/usr/bin/env python3
"""Analyze completed Fast router diagnostic matrices; never run ANN or fit a model.

The 32 primary Recall comparisons, seed, bootstrap count and sample roles are
fixed by protocol.md. Outputs are new files in a new directory. Input arrays are
read-only and no original base, graph, validation or held-out data are opened.
Use --self-test for synthetic arithmetic checks that require no experiment data.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
BUDGETS = (64, 128)
BOOTSTRAPS = 10000
SEED = 20260908
FAMILY_SIZE = 32
K = 10
MASK_LIMIT = (1 << K) - 1
POPCOUNT = np.array([i.bit_count() for i in range(1 << K)], dtype=np.uint8)
PRIMARY_NAMES = (
    "exact1_minus_fast1",
    "exact3_minus_fast3",
    "all_h_single_oracle_minus_exact1",
    "all_h_single_oracle_minus_exact_c8_single_oracle",
    "gt1_basin_minus_exact1",
    "c8_unrestricted_triple_oracle_minus_anchor_triple_oracle",
    "c8_triple_oracle_minus_fast3",
    "nearest_fit_choice_minus_random_fit_choice",
)


def require(condition, message):
    if not bool(condition):
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def config_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def describe(values):
    arr = np.asarray(values, dtype=np.float64).ravel()
    finite = arr[np.isfinite(arr)]
    out = {"n": int(arr.size), "n_finite": int(finite.size),
           "n_undefined": int(arr.size - finite.size)}
    if not finite.size:
        return {**out, "mean": None, "min": None, "max": None,
                "std": None, "quantiles": {}}
    quantiles = (.0, .05, .25, .5, .75, .95, 1.)
    return {**out, "mean": float(finite.mean()), "min": float(finite.min()),
            "max": float(finite.max()), "std": float(finite.std()),
            "quantiles": {str(q): float(v) for q, v in
                          zip(quantiles, np.quantile(finite, quantiles))}}


def best_single(hit, ndc, base_ids):
    """Max hit count, then minimum NDC, then minimum REAL base ID."""
    hit = np.asarray(hit)
    ndc = np.asarray(ndc)
    best_hit = hit.max(axis=1)
    best_cost = np.where(hit == best_hit[:, None], ndc, np.inf).min(axis=1)
    eligible = (hit == best_hit[:, None]) & (ndc == best_cost[:, None])
    sentinel = np.iinfo(np.int64).max
    return np.where(eligible, np.asarray(base_ids)[None, :], sentinel).argmin(axis=1)


def best_variant(hit, ndc, columns):
    """Max hit count, then minimum NDC, then metadata column order."""
    columns = np.asarray(columns, dtype=np.int64)
    require(columns.size > 0, "empty variant family")
    h = np.asarray(hit)[:, columns]
    d = np.asarray(ndc)[:, columns]
    costs = np.where(h == h.max(axis=1, keepdims=True), d, np.inf)
    return columns[costs.argmin(axis=1)]


def gather(matrix, local_ids):
    return np.asarray(matrix)[np.arange(len(local_ids)), local_ids]


def optimal_set(hit, delta=0):
    hit = np.asarray(hit, dtype=np.int16)
    return hit >= hit.max(axis=1, keepdims=True) - delta


def set_transfer(target_hit, source_set):
    target = np.asarray(target_hit, dtype=np.float64) / K
    source_set = np.asarray(source_set, dtype=bool)
    counts = source_set.sum(axis=1)
    require(np.all(counts > 0), "source optimal set is empty")
    mean = (target * source_set).sum(axis=1) / counts
    best = np.where(source_set, target, -np.inf).max(axis=1)
    return mean, best


def bootstrap_group(values, rng, resamples=BOOTSTRAPS):
    """Paired row bootstrap, shared row draws for every column in this group."""
    values = np.asarray(values, dtype=np.float64)
    require(values.ndim == 2 and len(values) > 0, "invalid bootstrap matrix")
    require(np.isfinite(values).all(), "nonfinite primary comparison")
    n, columns = values.shape
    draws = np.empty((resamples, columns), dtype=np.float64)
    index_hash = hashlib.sha256()
    for start in range(0, resamples, 128):
        stop = min(start + 128, resamples)
        indices = rng.integers(0, n, size=(stop - start, n), dtype=np.int32)
        index_hash.update(indices.astype("<i4", copy=False).tobytes())
        draws[start:stop] = values[indices].mean(axis=1)
    quantiles = (0.025, 0.975, 0.05 / (2 * FAMILY_SIZE),
                 1 - 0.05 / (2 * FAMILY_SIZE))
    endpoints = np.quantile(draws, quantiles, axis=0, method="linear")
    rows = []
    for col in range(columns):
        rows.append({"n_queries": n, "mean_delta_recall": float(values[:, col].mean()),
                     "mean_delta_percentage_points": float(100 * values[:, col].mean()),
                     "ci95_recall": endpoints[:2, col].tolist(),
                     "ci95_bonferroni32_recall": endpoints[2:, col].tolist(),
                     "ci95_percentage_points": (100 * endpoints[:2, col]).tolist(),
                     "ci95_bonferroni32_percentage_points": (100 * endpoints[2:, col]).tolist(),
                     "positive_query_fraction": float(np.mean(values[:, col] > 0)),
                     "negative_query_fraction": float(np.mean(values[:, col] < 0)),
                     "zero_query_fraction": float(np.mean(values[:, col] == 0))})
    return rows, index_hash.hexdigest()


def row_spearman(a, b):
    # Average ranks make the many Recall ties explicit. Constant rows are undefined.
    from scipy.stats import rankdata
    ra = rankdata(np.asarray(a), axis=1, method="average")
    rb = rankdata(np.asarray(b), axis=1, method="average")
    ra -= ra.mean(axis=1, keepdims=True)
    rb -= rb.mean(axis=1, keepdims=True)
    denominator = np.linalg.norm(ra, axis=1) * np.linalg.norm(rb, axis=1)
    return np.divide((ra * rb).sum(axis=1), denominator,
                     out=np.full(len(ra), np.nan), where=denominator > 0)


def write_csv(path, rows):
    require(bool(rows), "no CSV rows")
    with Path(path).open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class Dataset:
    def __init__(self, prepared, result, expected_name):
        self.prepared = Path(prepared)
        self.result = Path(result)
        self.config = read_json(self.prepared / "runner_config.json")
        self.manifest = read_json(self.prepared / "sample_manifest.json")
        self.meta = read_json(self.result / "metadata.json")
        self.name = expected_name
        self.n = int(self.config["num_queries"])
        self.p = int(self.config["pilot_count"])
        self.h = int(self.config["hub_count"])
        self.gtk = int(self.config["gt_k"])
        self.d = int(self.config["dim"])
        self.identities = {}
        self.arrays = {}
        require(self.config["dataset"] == expected_name == self.manifest["dataset"],
                "dataset identity mismatch")
        require(self.meta["status"] == "COMPLETE", f"{expected_name}: runner not COMPLETE")
        require(self.p == 512 and 512 < self.n <= 768, "protocol sample count mismatch")
        require(self.h == (815 if expected_name == DATASETS[0] else 821), "unexpected hub count")
        require(tuple(self.meta["L"]) == BUDGETS == tuple(self.config["L"]), "budget mismatch")
        require(self.config["top_k"] == self.meta["K"] == K, "K mismatch")
        for key, value in (("num_queries", self.n), ("pilot_count", self.p),
                           ("hub_count", self.h), ("gt_k", self.gtk), ("dim", self.d)):
            require(self.meta[key] == value, f"metadata/config {key} mismatch")
        require(self.meta["index_ntotal"] == self.config["base_count"], "base count mismatch")
        require(self.meta["router"]["seed"] == 20260828, "main HNSW seed mismatch")
        require(self.meta["router"]["seed_control"] == 100, "control HNSW seed mismatch")
        require(self.meta["router"]["efSearch"] == 10, "efSearch mismatch")
        require(self.manifest["pilot_count"] == self.p and self.manifest["num_queries"] == self.n,
                "sample manifest dimensions mismatch")
        for path in (self.prepared / "runner_config.json", self.prepared / "sample_manifest.json",
                     self.result / "metadata.json"):
            self.identities[str(path)] = {"sha256": sha256(path), "bytes": path.stat().st_size}
        self.row_ids = self.read_result("row_ids.i64", "<i8", (self.n,))
        self.hubs = self.read_result("hub_ids.i32", "<i4", (self.h,))
        require(np.array_equal(self.row_ids, self.manifest["row_ids"]), "result row ID mismatch")
        require(len(np.unique(self.row_ids)) == self.n, "duplicate selected source rows")
        require(len(np.unique(self.hubs)) == self.h and np.all(self.hubs >= 0), "invalid hub IDs")
        require(np.all(self.hubs < self.config["base_count"]), "hub base ID out of range")
        require(np.all((self.row_ids[:self.p] >= 0) & (self.row_ids[:self.p] < 10000)),
                "pilot rows outside train pilot range")
        require(np.all((self.row_ids[self.p:] >= 10000) & (self.row_ids[self.p:] < 30000)),
                "auxiliary rows outside 20K fit range")
        self.gt = self.read_prepared("gt.i64", "<i8", (self.n, self.gtk))
        require(np.all(self.gt[:, :K] >= 0), "invalid GT10 ID")
        require(np.all(np.diff(np.sort(self.gt[:, :K], axis=1), axis=1) > 0), "duplicate GT10 ID")
        self.query = self.read_prepared("queries.f32", "<f4", (self.n, self.d))
        self.cos64 = self.read_prepared("prototype_cosine_f64.f64", "<f8", (self.n, self.h))
        self.raw_ip64 = self.read_prepared("raw_hub_ip_f64.f64", "<f8", (self.n, self.h))
        self.fit_counts = self.read_prepared("hub_fit_counts.i32", "<i4", (self.h,))
        self.concentration = self.read_prepared("hub_concentration.f64", "<f8", (self.h,))
        self.basin = self.read_result("basin_label_local.i32", "<i4", (self.n,))
        prepared_basin = self.read_prepared("basin_label_local.i32", "<i4", (self.n,))
        require(np.array_equal(self.basin, prepared_basin), "basin label mismatch")
        require(np.all((self.basin >= 0) & (self.basin < self.h)), "basin label out of range")
        self.exact = self.read_result("exact.rank_local.i32", "<i4", (self.n, self.h))
        self.exact_dist = self.read_result("exact.rank_distance.f32", "<f4", (self.n, self.h))
        require(np.all(np.sort(self.exact, axis=1) == np.arange(self.h)), "exact ranks not permutations")
        require(np.isfinite(self.exact_dist).all(), "nonfinite exact distances")
        require(np.all(np.diff(self.exact_dist, axis=1) >= 0), "exact ranks not distance sorted")
        tie = np.diff(self.exact_dist, axis=1) == 0
        require(np.all(~tie | (np.diff(self.hubs[self.exact], axis=1) > 0)), "exact tie rule mismatch")
        self.routes, self.route_dist, self.route_ndc = {}, {}, {}
        for source in ("fast", "seed100"):
            self.routes[source] = self.read_result(f"{source}.top8_local.i32", "<i4", (self.n, 8))
            self.route_dist[source] = self.read_result(f"{source}.top8_distance.f32", "<f4", (self.n, 8))
            self.route_ndc[source] = self.read_result(f"{source}.route_ndc.u32", "<u4", (self.n,))
            ranks = self.routes[source]
            require(np.all((ranks >= 0) & (ranks < self.h)), f"{source} local IDs out of range")
            require(np.all(np.diff(np.sort(ranks, axis=1), axis=1) > 0), f"{source} duplicate route IDs")
            require(np.isfinite(self.route_dist[source]).all(), f"{source} nonfinite distances")
            require(np.all(np.diff(self.route_dist[source], axis=1) >= 0), f"{source} distance order")
        self.score = np.empty((self.n, self.h), dtype=np.float64)
        np.put_along_axis(self.score, self.exact, 1.0 - self.exact_dist.astype(np.float64), axis=1)
        for source in self.routes:
            expected = 1.0 - np.take_along_axis(self.score, self.routes[source], axis=1)
            require(np.array_equal(expected.astype("<f4"), self.route_dist[source]),
                    f"{source} score differs from exact same distance function")
        self.variants = self.meta["variants"]
        self.v = len(self.variants)
        require(self.v == 91, "protocol requires all 91 variants including seed100")
        self.names = {v["name"]: int(v["column"]) for v in self.variants}
        require(len(self.names) == self.v, "duplicate variant names")
        require(sorted(self.names.values()) == list(range(self.v)), "variant columns not contiguous")
        self.entries = self.read_result("pilot.entry_local.i32", "<i4", (self.p, self.v, 3))
        source_routes = {**self.routes, "exact": self.exact}
        for v in self.variants:
            col, count = v["column"], v["entry_count"]
            require(1 <= count <= 3, "invalid variant entry count")
            expected = source_routes[v["route"]][:self.p, v["route_ranks"][:count]]
            require(np.array_equal(self.entries[:, col, :count], expected), f"variant {v['name']} entry mismatch")
            require(np.all(self.entries[:, col, count:] == -1), "entry padding mismatch")
        self.pair_cols = np.array([self.names[f"c8_pair_{i}_{j}"]
                                   for i, j in itertools.combinations(range(8), 2)])
        self.triple_cols = np.array([self.names[f"c8_triple_{i}_{j}_{k}"]
                                     for i, j, k in itertools.combinations(range(8), 3)])
        self.anchor_cols = np.array([v["column"] for v in self.variants
                                    if v["name"].startswith("c8_triple_") and 0 in v["route_ranks"]])
        self.without_anchor_cols = np.setdiff1d(self.triple_cols, self.anchor_cols)
        require(len(self.pair_cols) == 28 and len(self.triple_cols) == 56 and len(self.anchor_cols) == 21,
                "combination family mismatch")
        self.neighbors = self.manifest["neighbor_pairs"]
        require(len(self.neighbors) == 128, "requires predeclared 128 neighbor pairs")
        for i, pair in enumerate(self.neighbors):
            require(pair["pilot_local"] == i, "neighbor pilot order mismatch")
            require(pair["pilot_row"] == int(self.row_ids[i]), "neighbor pilot row mismatch")
            for source in ("nearest", "random"):
                local = int(pair[f"{source}_fit_local"])
                require(self.p <= local < self.n, "neighbor source is not an auxiliary fit row")
                require(pair[f"{source}_fit_row"] == int(self.row_ids[local]), "fit row/local mismatch")
                overlap = len(set(self.gt[i, :K]) & set(self.gt[local, :K]))
                require(overlap == pair[f"{source}_gt10_overlap"], "neighbor GT overlap mismatch")
        self.nearest = np.array([v["nearest_fit_local"] for v in self.neighbors], dtype=np.int64)
        self.random = np.array([v["random_fit_local"] for v in self.neighbors], dtype=np.int64)
        self.levels = {}

    def read_array(self, path, dtype, shape, expected_sha=None):
        path = Path(path)
        nbytes = math.prod(shape) * np.dtype(dtype).itemsize
        require(path.is_file() and path.stat().st_size == nbytes, f"missing/truncated array: {path}")
        digest = sha256(path)
        if expected_sha is not None:
            require(digest == expected_sha, f"SHA mismatch: {path}")
        self.identities[str(path)] = {"sha256": digest, "bytes": nbytes,
                                      "dtype": dtype, "shape": list(shape)}
        arr = np.memmap(path, mode="r", dtype=dtype, shape=shape)
        self.arrays[str(path)] = arr
        return arr

    def read_result(self, name, dtype, shape):
        return self.read_array(self.result / name, dtype, shape)

    def read_prepared(self, name, dtype, shape):
        spec = self.manifest["artifacts"][name]
        require(list(shape) == spec["shape"], f"manifest shape mismatch: {name}")
        require(np.dtype(dtype) == np.dtype(spec["dtype"]), f"manifest dtype mismatch: {name}")
        return self.read_array(self.prepared / name, dtype, shape, spec["sha256"])

    def load_level(self, budget):
        directory = self.result / f"L{budget}"
        complete = read_json(directory / "complete.json")
        require(complete["status"] == "COMPLETE" and complete["rows"] == self.n
                and complete["pilot_rows"] == self.p, "incomplete budget output")
        output = {"complete": complete}
        for family, rows, columns in (("all_single", self.n, self.h), ("pilot", self.p, self.v)):
            data = {}
            for field, suffix, dtype in (("hitcount", "u8", "<u1"), ("hitmask", "u16", "<u2"),
                                          ("ndc", "u32", "<u4"), ("ids", "i32", "<i4")):
                shape = (rows, columns, K) if field == "ids" else (rows, columns)
                spec = self.meta[family][field]
                require(spec["shape"] == list(shape) and np.dtype(spec["dtype"]) == np.dtype(dtype),
                        f"{family}/{field} metadata shape/dtype mismatch")
                data[field] = self.read_array(directory / f"{family}.{field}.{suffix}", dtype, shape)
            require(np.all(data["hitcount"] <= K) and np.all(data["hitmask"] <= MASK_LIMIT), "invalid hit data")
            require(np.array_equal(POPCOUNT[data["hitmask"]], data["hitcount"]), "hitcount/popcount mismatch")
            require(np.all(data["ndc"] > 0), "zero graph NDC for a valid entry")
            for start in range(0, rows, 16):
                stop = min(rows, start + 16)
                ids = np.asarray(data["ids"][start:stop])
                require(np.all((ids >= -1) & (ids < self.config["base_count"])), "returned base ID out of range")
                # Every GT bit is based on any of the 10 returned IDs. IDs are base IDs, not hub ordinals.
                hit = (ids[:, :, :, None] == self.gt[start:stop, None, None, :K]).any(axis=2)
                mask = (hit.astype(np.uint16) * (1 << np.arange(K, dtype=np.uint16))).sum(axis=2)
                require(np.array_equal(mask, data["hitmask"][start:stop]), "IDs/GT-derived hitmask mismatch")
            output[family] = data
        for source in ("fast", "exact"):
            local = self.routes[source][:self.p, 0] if source == "fast" else self.exact[:self.p, 0]
            col = self.names[f"{source}_top1"]
            for field in ("hitcount", "hitmask", "ndc", "ids"):
                require(np.array_equal(output["pilot"][field][:, col],
                                       output["all_single"][field][np.arange(self.p), local]),
                        f"cached {source} single result mismatch")
        for a, b in (("fast_top2", "c8_pair_0_1"), ("fast_top3", "c8_triple_0_1_2")):
            for field in ("hitcount", "hitmask", "ndc", "ids"):
                require(np.array_equal(output["pilot"][field][:, self.names[a]],
                                       output["pilot"][field][:, self.names[b]]), "duplicate action replay mismatch")
        output["representative"] = best_single(output["all_single"]["hitcount"],
                                              output["all_single"]["ndc"], self.hubs)
        self.levels[budget] = output
        return output


def method_summary(hit, ndc):
    return {"recall_at_10": describe(np.asarray(hit, dtype=np.float64) / K),
            "graph_ndc": describe(ndc)}


def coverage_summary(hit, shortlist):
    query = np.arange(len(shortlist))[:, None]
    h = np.asarray(hit)[:len(shortlist)]
    maximum = h.max(axis=1)
    best = h[query, shortlist].max(axis=1)
    return {"k": shortlist.shape[1], "best_single_recall": describe(best / K),
            "all_h_oracle_regret": describe((maximum.astype(float) - best) / K),
            "contains_A0_fraction": float(np.mean(best == maximum)),
            "contains_A1_fraction": float(np.mean(best.astype(int) >= maximum.astype(int) - 1))}


def router_diagnostics(data):
    out = {"interpretation": "Proxy-score approximation only; utility differences are reported separately.",
           "route_distance": "1 minus query-prototype inner product, same function for exact and HNSW",
           "exact_distance_margin_top1_top2": describe(data.exact_dist[:data.p, 1] - data.exact_dist[:data.p, 0]),
           "recorded_top8_route_ndc": {s: describe(x[:data.p]) for s, x in data.route_ndc.items()}}
    for source, rank in data.routes.items():
        details = {}
        for k in (1, 3, 8):
            expected = data.exact[:data.p, :k]
            actual = rank[:data.p, :k]
            overlap = (expected[:, :, None] == actual[:, None, :]).any(axis=2).sum(axis=1)
            details[str(k)] = {"exact_topk_set_recall": describe(overlap / k),
                                "ordered_list_equal_fraction": float(np.mean(np.all(expected == actual, axis=1))),
                                "set_equal_fraction": float(np.mean(overlap == k)),
                                "distance_list_equal_fraction": float(np.mean(np.all(
                                    data.exact_dist[:data.p, :k] == data.route_dist[source][:data.p, :k], axis=1))),
                                "distance_regret_at_rank_k": describe(
                                    data.route_dist[source][:data.p, k - 1].astype(float)
                                    - data.exact_dist[:data.p, k - 1])}
        out[source] = details
    order64 = np.lexsort((np.broadcast_to(data.hubs, (data.p, data.h)), -data.cos64[:data.p]), axis=1)
    out["float64_cosine_reference"] = {
        "top1_same_as_kernel_exact_fraction": float(np.mean(order64[:, 0] == data.exact[:data.p, 0])),
        "note": "Float64 cosine uses auxiliary normalization; rank differences are descriptive, not a search bug."}
    return out


def neighbor_diagnostics(data, level, budget):
    singles = level["all_single"]
    hit = np.asarray(singles["hitcount"])
    ndc = singles["ndc"]
    target = hit[:128]
    best = target.max(axis=1) / K
    reps = level["representative"]
    stats = {"n_target_queries": 128, "source_choice": "max Recall, then minimum source NDC, then real base ID",
             "target_best_is_oracle": True, "sources": {}}
    raw = {}
    for source, rows in (("nearest_fit", data.nearest), ("random_fit", data.random)):
        choice = reps[rows]
        values = target[np.arange(128), choice] / K
        costs = np.asarray(ndc)[np.arange(128), choice].astype(np.float64)
        summary = {"representative_recall": describe(values), "representative_graph_ndc": describe(costs),
                   "representative_regret": describe(best - values), "sets": {}}
        raw[source] = {"representative": values, "cost": costs, "choice": choice}
        for delta in (0, 1):
            source_set = optimal_set(hit[rows], delta)
            mean, optimistic = set_transfer(target, source_set)
            summary["sets"][f"A{delta}"] = {"source_size": describe(source_set.sum(axis=1)),
                 "target_mean_recall": describe(mean), "target_best_recall_oracle": describe(optimistic),
                 "target_mean_regret": describe(best - mean), "target_best_regret_oracle": describe(best - optimistic)}
            raw[source][f"A{delta}_mean"] = mean
            raw[source][f"A{delta}_best"] = optimistic
        stats["sources"][source] = summary
    similarities = np.array([x["nearest_query_cosine"] for x in data.neighbors])
    random_similarities = np.array([x["random_query_cosine"] for x in data.neighbors])
    overlaps = np.array([x["nearest_gt10_overlap"] for x in data.neighbors])
    require(np.isfinite(similarities).all() and np.isfinite(random_similarities).all(), "nonfinite neighbor similarity")
    stats["density"] = {"nearest_fit_reference_count": data.manifest["nearest_fit_reference_count"],
                         "nearest_cosine": describe(similarities), "random_cosine": describe(random_similarities),
                         "nearest_minus_random_cosine": describe(similarities - random_similarities),
                         "nearest_closer_fraction": float(np.mean(similarities > random_similarities)),
                         "unique_nearest_fit_rows": int(len(np.unique(data.nearest))),
                         "nearest_gt10_overlap": describe(overlaps),
                         "random_gt10_overlap": describe([x["random_gt10_overlap"] for x in data.neighbors])}
    # Descriptive feature-only strata; never used to select a model or hypothesis.
    strata = {"gt10_overlap_0": overlaps == 0, "gt10_overlap_1_to_4": (overlaps >= 1) & (overlaps <= 4),
              "gt10_overlap_5_to_9": (overlaps >= 5) & (overlaps <= 9), "gt10_overlap_10": overlaps == 10}
    sim_order = np.lexsort((data.row_ids[:128], similarities))
    for quartile, indices in enumerate(np.array_split(sim_order, 4), 1):
        mask = np.zeros(128, dtype=bool)
        mask[indices] = True
        strata[f"nearest_cosine_rank_quartile_{quartile}"] = mask
    stats["descriptive_strata"] = {}
    for label, mask in strata.items():
        stats["descriptive_strata"][label] = {"n": int(mask.sum()), "nearest_cosine": describe(similarities[mask]),
            "nearest_choice_recall": describe(raw["nearest_fit"]["representative"][mask]),
            "random_choice_recall": describe(raw["random_fit"]["representative"][mask]),
            "paired_recall_delta": describe((raw["nearest_fit"]["representative"] - raw["random_fit"]["representative"])[mask]),
            "nearest_A0_target_mean": describe(raw["nearest_fit"]["A0_mean"][mask]),
            "nearest_A0_target_best_oracle": describe(raw["nearest_fit"]["A0_best"][mask])}
    q = np.asarray(data.query[:data.p], dtype=np.float64)
    norms = np.linalg.norm(q, axis=1)
    require(np.all(norms > 0), "zero query norm in density diagnostic")
    q = q / norms[:, None]
    similarity = q[:128] @ q.T
    similarity[np.arange(128), np.arange(128)] = -np.inf
    # Same float64 cosine tie rule as the preparation stage: real source row ID.
    pilot_source = np.empty(128, dtype=np.int64)
    for i in range(128):
        eligible = np.flatnonzero(similarity[i] == similarity[i].max())
        pilot_source[i] = eligible[np.argmin(data.row_ids[eligible])]
    pmean, pbest = set_transfer(target, optimal_set(hit[pilot_source], 0))
    stats["pilot_only_density_control"] = {"n_reference_rows_excluding_self": data.p - 1,
        "cosine": describe(similarity[np.arange(128), pilot_source]),
        "A0_target_mean_recall": describe(pmean), "A0_target_best_recall_oracle": describe(pbest),
        "interpretation": "Compared on the same 128 targets; source labels come from the historical pilot."}
    rows = []
    for i in range(128):
        rows.append({"dataset": data.name, "L": budget, "pilot_local": i, "pilot_row": int(data.row_ids[i]),
            "nearest_fit_row": int(data.row_ids[data.nearest[i]]), "random_fit_row": int(data.row_ids[data.random[i]]),
            "nearest_cosine": float(similarities[i]), "random_cosine": float(random_similarities[i]),
            "nearest_gt10_overlap": int(overlaps[i]), "random_gt10_overlap": data.neighbors[i]["random_gt10_overlap"],
            "nearest_choice_base_id": int(data.hubs[raw["nearest_fit"]["choice"][i]]),
            "random_choice_base_id": int(data.hubs[raw["random_fit"]["choice"][i]]),
            **{f"{source}_{field}": float(raw[source][field][i]) for source in raw
               for field in ("representative", "cost", "A0_mean", "A0_best", "A1_mean", "A1_best")}})
    return stats, raw, rows


def analyze_level(data, budget):
    level = data.load_level(budget)
    singles, pilot = level["all_single"], level["pilot"]
    hit, ndc = np.asarray(singles["hitcount"]), np.asarray(singles["ndc"])
    phit, pndc = np.asarray(pilot["hitcount"]), np.asarray(pilot["ndc"])
    p, query = data.p, np.arange(data.p)
    maximum = hit[:p].max(axis=1).astype(np.int16)
    methods, selected = {}, {}
    for name in ("fast_top1", "fast_top2", "fast_top3", "exact_top1", "exact_top2", "exact_top3", "seed100_top3"):
        col = data.names[name]
        methods[name] = method_summary(phit[:, col], pndc[:, col])
        selected[name] = (phit[:, col].astype(np.int16), pndc[:, col].astype(np.float64))
    for name, local in (("gt1_basin", data.basin[:p]), ("all_h_single_oracle", level["representative"][:p])):
        h, d = hit[query, local].astype(np.int16), ndc[query, local].astype(np.float64)
        methods[name] = method_summary(h, d)
        selected[name] = (h, d)
    best_columns = {}
    for name, cols in (("c8_pair_oracle", data.pair_cols), ("c8_triple_oracle", data.triple_cols),
                       ("c8_anchor_triple_oracle", data.anchor_cols),
                       ("c8_without_anchor_triple_oracle", data.without_anchor_cols)):
        choice = best_variant(phit, pndc, cols)
        h, d = phit[query, choice].astype(np.int16), pndc[query, choice].astype(np.float64)
        methods[name] = method_summary(h, d)
        selected[name] = (h, d)
        best_columns[name] = choice
    coverage = {f"exact_top{k}": coverage_summary(hit, data.exact[:p, :k]) for k in (1, 3, 8, 32, 64)}
    coverage["fast_top8"] = coverage_summary(hit, data.routes["fast"][:p])
    coverage["seed100_top8"] = coverage_summary(hit, data.routes["seed100"][:p])
    exact8_hit = hit[query[:, None], data.exact[:p, :8]].max(axis=1).astype(np.int16)
    exact8_h = hit[query[:, None], data.exact[:p, :8]]
    exact8_d = ndc[query[:, None], data.exact[:p, :8]]
    exact8_best_ndc = np.where(exact8_h == exact8_hit[:, None], exact8_d, np.inf).min(axis=1)
    fast8_hit = hit[query[:, None], data.routes["fast"][:p]].max(axis=1).astype(np.int16)
    fast1 = selected["fast_top1"][0]
    basin = selected["gt1_basin"][0]
    exact1 = selected["exact_top1"][0]
    require(np.array_equal(maximum - fast1, (maximum - basin) + (basin - fast1)), "basin decomposition failed")
    require(np.array_equal(maximum - fast1, (maximum - fast8_hit) + (fast8_hit - fast1)), "C8 decomposition failed")
    ties, rank = {}, np.take_along_axis(hit[:p], data.exact[:p], axis=1)
    optimal_first_rank = np.argmax(rank == maximum[:, None], axis=1) + 1
    for delta in (0, 1):
        aset = optimal_set(hit[:p], delta)
        counts = aset.sum(axis=1)
        ties[f"A{delta}"] = {"size": describe(counts), "fraction_of_h": describe(counts / data.h),
             "uniform_random_entry_hit_probability": float(np.mean(counts / data.h)),
             "fast1_membership_fraction": float(np.mean(aset[query, data.routes["fast"][:p, 0]])),
             "exact1_membership_fraction": float(np.mean(aset[query, data.exact[:p, 0]])),
             "basin_membership_fraction": float(np.mean(aset[query, data.basin[:p]]))}
    a0 = optimal_set(hit[:p], 0)
    min_opt_cost = np.where(a0, ndc[:p], np.inf).min(axis=1)
    max_opt_cost = np.where(a0, ndc[:p], -np.inf).max(axis=1)
    median_opt_cost = np.nanmedian(np.where(a0, ndc[:p], np.nan), axis=1)
    ties["A0_graph_ndc"] = {"minimum": describe(min_opt_cost), "median": describe(median_opt_cost),
                            "maximum": describe(max_opt_cost)}
    fast1_optimal = fast1 == maximum
    ties["fast1_cost_ratio_when_recall_optimal"] = describe(
        selected["fast_top1"][1][fast1_optimal] / min_opt_cost[fast1_optimal])
    ties["zero_oracle_hit_queries"] = int(np.sum(maximum == 0))
    ties["maximum_hitcount_histogram"] = np.bincount(maximum, minlength=11).tolist()
    ties["oracle_saturation_strata"] = {}
    for label, mask in (("oracle_zero", maximum == 0), ("oracle_1_to_9", (maximum > 0) & (maximum < K)),
                        ("oracle_10_saturated", maximum == K)):
        ties["oracle_saturation_strata"][label] = {"n": int(mask.sum()),
            "A0_size": describe(a0.sum(axis=1)[mask]),
            "A1_size": describe(optimal_set(hit[:p], 1).sum(axis=1)[mask]),
            "fast1_regret": describe((maximum - fast1)[mask] / K),
            "exact1_regret": describe((maximum - exact1)[mask] / K)}
    ties["unique_representative_fast1_match_fraction"] = float(np.mean(
        level["representative"][:p] == data.routes["fast"][:p, 0]))
    spearman = row_spearman(data.score[:p], hit[:p])
    raw_spearman = row_spearman(data.raw_ip64[:p], hit[:p])
    image_alignment = {"prototype_score_vs_single_recall_spearman": describe(spearman),
                       "prototype_score_vs_negative_graph_ndc_spearman": describe(row_spearman(data.score[:p], -ndc[:p].astype(float))),
                       "raw_hub_ip_vs_single_recall_spearman": describe(raw_spearman),
                       "best_recall_entry_first_exact_rank_1_based": describe(optimal_first_rank),
                       "constant_recall_rows": int(np.sum(hit[:p].max(axis=1) == hit[:p].min(axis=1))),
                       "note": "Average ranks for ties; constant rows undefined; all correlations descriptive."}
    # All masks are relative to the same target GT10 within each row.
    combo_cols = np.r_[data.pair_cols, data.triple_cols]
    combo_entries = data.entries[:, combo_cols]
    per_entry_mask = singles["hitmask"][query[:, None, None], np.maximum(combo_entries, 0)]
    per_entry_mask = np.where(combo_entries >= 0, per_entry_mask, 0).astype(np.uint16)
    union = np.bitwise_or.reduce(per_entry_mask, axis=2)
    actual_mask = np.asarray(pilot["hitmask"][:, combo_cols])
    lost = POPCOUNT[union & (~actual_mask & MASK_LIMIT)]
    new = POPCOUNT[actual_mask & (~union & MASK_LIMIT)]
    require(np.array_equal(POPCOUNT[actual_mask].astype(int) - POPCOUNT[union].astype(int),
                           new.astype(int) - lost.astype(int)), "joint mask accounting failed")
    interaction = {"interpretation": "Independent single union is neither a same-cost action nor an upper bound.",
                   "unit_warning": "Actions within a query are correlated; no action-level significance tests.",
                   "families": {}}
    for name, locs in (("pairs", np.arange(28)), ("triples", np.arange(28, 84))):
        interaction["families"][name] = {"actions_per_query": int(len(locs)),
            "query_mean_lost_hits": describe(lost[:, locs].mean(axis=1)),
            "query_mean_new_hits": describe(new[:, locs].mean(axis=1)),
            "query_fraction_actions_with_lost": describe((lost[:, locs] > 0).mean(axis=1)),
            "query_fraction_actions_with_new": describe((new[:, locs] > 0).mean(axis=1)),
            "query_fraction_actions_exact_mask_equal": describe((union[:, locs] == actual_mask[:, locs]).mean(axis=1)),
            "query_mean_actual_minus_union_recall": describe((new[:, locs].astype(float) - lost[:, locs]).mean(axis=1) / K)}
    union_hit = POPCOUNT[union]
    per_entry_ndc = ndc[query[:, None, None], np.maximum(combo_entries, 0)]
    sum_cost = np.where(combo_entries >= 0, per_entry_ndc, 0).astype(np.float64).sum(axis=2)
    per_entry_hit = hit[query[:, None, None], np.maximum(combo_entries, 0)]
    sum_hit = np.where(combo_entries >= 0, per_entry_hit, 0).astype(np.int16).sum(axis=2)
    for proxy, proxy_hit in (("independent_union", union_hit), ("sum_single_hitcounts", sum_hit)):
        chosen_combo = best_variant(proxy_hit, sum_cost, np.arange(28, 84))
        actual_col = combo_cols[chosen_combo]
        ahit = phit[query, actual_col]
        interaction[f"{proxy}_selected_triple_actual"] = {
            **method_summary(ahit, pndc[query, actual_col]),
            "regret_to_true_c8_triple_oracle": describe((selected["c8_triple_oracle"][0] - ahit) / K),
            "tie_rule": "max proxy, min sum independent NDC, then metadata column"}
    neighbors, neighbor_raw, neighbor_rows = neighbor_diagnostics(data, level, budget)
    primary_pairs = (
        (selected["exact_top1"], selected["fast_top1"]),
        (selected["exact_top3"], selected["fast_top3"]),
        (selected["all_h_single_oracle"], selected["exact_top1"]),
        ((maximum, selected["all_h_single_oracle"][1]), (exact8_hit, exact8_best_ndc)),
        (selected["gt1_basin"], selected["exact_top1"]),
        (selected["c8_triple_oracle"], selected["c8_anchor_triple_oracle"]),
        (selected["c8_triple_oracle"], selected["fast_top3"]),
    )
    primary = []
    for name, (left, right) in zip(PRIMARY_NAMES[:7], primary_pairs):
        primary.append({"name": name, "dataset": data.name, "L": budget,
                        "values": (np.asarray(left[0], dtype=float) - right[0]) / K,
                        "graph_ndc_delta_descriptive": describe(np.asarray(left[1], dtype=float) - right[1])})
    primary.append({"name": PRIMARY_NAMES[7], "dataset": data.name, "L": budget,
        "values": neighbor_raw["nearest_fit"]["representative"] - neighbor_raw["random_fit"]["representative"],
        "graph_ndc_delta_descriptive": describe(neighbor_raw["nearest_fit"]["cost"] - neighbor_raw["random_fit"]["cost"])})
    decomp = {"all_h_minus_fast1": describe((maximum - fast1) / K),
              "all_h_minus_gt1_basin": describe((maximum - basin) / K),
              "gt1_basin_minus_fast1_signed": describe((basin - fast1) / K),
              "all_h_minus_fast_c8_single_best": describe((maximum - fast8_hit) / K),
              "fast_c8_single_best_minus_fast1": describe((fast8_hit - fast1) / K),
              "exact_c8_single_best_minus_fast_c8_single_best_signed": describe((exact8_hit - fast8_hit) / K),
              "fast1_equals_basin_label_fraction": float(np.mean(data.routes["fast"][:p, 0] == data.basin[:p])),
              "exact1_equals_basin_label_fraction": float(np.mean(data.exact[:p, 0] == data.basin[:p])),
              "basin_component_is_not_a_causal_percentage": True}
    fit_density = {"all_h_fit_counts": describe(data.fit_counts),
                   "all_h_concentration": describe(data.concentration),
                   "basin_fit_counts": describe(data.fit_counts[data.basin[:p]]),
                   "fast1_entry_fit_counts": describe(data.fit_counts[data.routes["fast"][:p, 0]]),
                   "oracle_representative_fit_counts": describe(data.fit_counts[level["representative"][:p]]),
                   "strata": {}}
    counts_at_basin = data.fit_counts[data.basin[:p]]
    for label, lower, upper in (("0", 0, 0), ("1_to_9", 1, 9), ("10_to_29", 10, 29),
                                ("30_to_99", 30, 99), ("100_plus", 100, np.inf)):
        mask = (counts_at_basin >= lower) & (counts_at_basin <= upper)
        fit_density["strata"][label] = {"n": int(mask.sum()), "basin_regret": describe((maximum - basin)[mask] / K),
           "exact1_regret": describe((maximum - exact1)[mask] / K), "prototype_recall_spearman": describe(spearman[mask])}
    per_query = []
    for i in range(p):
        per_query.append({"dataset": data.name, "L": budget, "pilot_local": i, "source_row_id": int(data.row_ids[i]),
            "A0_size": int(a0[i].sum()), "A1_size": int(optimal_set(hit[i:i+1], 1).sum()),
            "oracle_representative_base_id": int(data.hubs[level["representative"][i]]),
            "basin_base_id": int(data.hubs[data.basin[i]]), "fast1_base_id": int(data.hubs[data.routes["fast"][i, 0]]),
            "first_optimal_exact_rank": int(optimal_first_rank[i]),
            "prototype_recall_spearman": float(spearman[i]) if np.isfinite(spearman[i]) else "",
            "raw_ip_recall_spearman": float(raw_spearman[i]) if np.isfinite(raw_spearman[i]) else "",
            "exact_c8_single_best_recall": float(exact8_hit[i] / K), "fast_c8_single_best_recall": float(fast8_hit[i] / K),
            **{f"{name}_recall": float(value[0][i] / K) for name, value in selected.items()},
            **{f"{name}_graph_ndc": int(value[1][i]) for name, value in selected.items()},
            **{f"{name}_variant_column": int(col[i]) for name, col in best_columns.items()}})
    summary = {"L": budget, "methods": methods, "shortlist_coverage": coverage, "ties": ties,
               "proxy_and_raw_score_alignment": image_alignment, "basin_and_shortlist_decomposition": decomp,
               "combination_interaction": interaction, "neighbor_transfer": neighbors, "fit_density": fit_density,
               "instrumented_run_completion": level["complete"]}
    plot_values = {"A0": a0.sum(axis=1), "A1": optimal_set(hit[:p], 1).sum(axis=1)}
    return summary, primary, per_query, neighbor_rows, plot_values


def cross_budget(data):
    h64 = np.asarray(data.levels[64]["all_single"]["hitcount"][:data.p])
    h128 = np.asarray(data.levels[128]["all_single"]["hitcount"][:data.p])
    max64, max128 = h64.max(axis=1) / K, h128.max(axis=1) / K
    output = {"representative_same_fraction": float(np.mean(data.levels[64]["representative"][:data.p]
                                                            == data.levels[128]["representative"][:data.p])),
              "single_recall_vectors_spearman": describe(row_spearman(h64, h128)), "sets": {}}
    for delta in (0, 1):
        a, b = optimal_set(h64, delta), optimal_set(h128, delta)
        intersection, union = (a & b).sum(axis=1), (a | b).sum(axis=1)
        output["sets"][f"A{delta}"] = {"jaccard": describe(intersection / union),
             "intersection_size": describe(intersection), "nonempty_intersection_fraction": float(np.mean(intersection > 0))}
    for source, target, target_hit, maximum in ((64, 128, h128, max128), (128, 64, h64, max64)):
        source_level = data.levels[source]
        choice = source_level["representative"][:data.p]
        source_a0 = optimal_set(source_level["all_single"]["hitcount"][:data.p], 0)
        mean, best = set_transfer(target_hit, source_a0)
        output[f"L{source}_to_L{target}"] = {
            "representative_recall_regret": describe(maximum - target_hit[np.arange(data.p), choice] / K),
            "source_A0_target_mean_regret": describe(maximum - mean),
            "source_A0_target_best_regret_oracle": describe(maximum - best)}
    worst = np.maximum(max64[:, None] - h64 / K, max128[:, None] - h128 / K)
    output["best_common_entry_max_regret_oracle"] = describe(worst.min(axis=1))
    output["query_fraction_entries_with_lower_recall_at_L128"] = describe((h128 < h64).mean(axis=1))
    output["interpretation"] = "Budget-specific value transfer; ID changes alone do not establish prediction difficulty."
    return output


def plot_results(output, datasets, plot_values):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    paths = []
    colors = {64: "#2463a6", 128: "#d8662b"}
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    stages = ("fast_top1", "exact_top1", "gt1_basin", "exact_top8")
    labels = ("Fast1", "Exact1", "GT1 basin", "Exact C8 best")
    for axis, ds in zip(axes, datasets):
        for j, budget in enumerate(BUDGETS):
            lev = ds["budgets"][str(budget)]
            maximum = lev["methods"]["all_h_single_oracle"]["recall_at_10"]["mean"]
            recall = [lev["methods"][s]["recall_at_10"]["mean"] for s in stages[:3]]
            recall.append(lev["shortlist_coverage"]["exact_top8"]["best_single_recall"]["mean"])
            axis.bar(np.arange(4) + (j - .5) * .35, 100 * (maximum - np.array(recall)), .35,
                     label=f"L={budget}", color=colors[budget])
        axis.set_title(ds["dataset"].split("_")[0].title())
        axis.set_xticks(np.arange(4), labels, rotation=15)
        axis.legend()
    axes[0].set_ylabel("Recall@10 regret to all-H single oracle (pp)")
    fig.tight_layout()
    path = output / "recall_regret.png"; fig.savefig(path, dpi=170); plt.close(fig); paths.append(path.name)
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharey=True)
    for row, ds in enumerate(datasets):
        for col, budget in enumerate(BUDGETS):
            axis = axes[row, col]
            for key, color in (("A0", "#2463a6"), ("A1", "#d8662b")):
                values = np.sort(plot_values[ds["dataset"]][budget][key])
                axis.step(values, np.arange(1, len(values) + 1) / len(values), where="post", label=key, color=color)
            axis.set_title(f"{ds['dataset'].split('_')[0].title()}, L={budget}")
            axis.set_xlabel("Number of optimal / one-hit-near-optimal entries")
            axis.set_ylabel("Empirical cumulative fraction"); axis.legend()
    fig.tight_layout()
    path = output / "optimal_set_sizes.png"; fig.savefig(path, dpi=170); plt.close(fig); paths.append(path.name)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    for axis, ds in zip(axes, datasets):
        for j, budget in enumerate(BUDGETS):
            src = ds["budgets"][str(budget)]["neighbor_transfer"]["sources"]
            values = [src[s]["representative_recall"]["mean"] for s in ("random_fit", "nearest_fit")]
            values += [src["nearest_fit"]["sets"]["A0"][key]["mean"]
                       for key in ("target_mean_recall", "target_best_recall_oracle")]
            axis.bar(np.arange(4) + (j - .5) * .35, values, .35, label=f"L={budget}", color=colors[budget])
        axis.set_title(ds["dataset"].split("_")[0].title())
        axis.set_xticks(np.arange(4), ["Random choice", "Nearest choice", "Nearest A0 mean", "Nearest A0 best*"], rotation=20)
        axis.set_ylim(0, 1); axis.legend()
    axes[0].set_ylabel("Target Recall@10, 128 paired pilot queries")
    fig.text(.5, .005, "*Target-label oracle diagnostic, not a deployable choice", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, .04, 1, 1))
    path = output / "neighbor_transfer.png"; fig.savefig(path, dpi=170); plt.close(fig); paths.append(path.name)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for axis, ds in zip(axes, datasets):
        for j, key in enumerate(("query_mean_lost_hits", "query_mean_new_hits")):
            values = [ds["budgets"][str(b)]["combination_interaction"]["families"]["triples"][key]["mean"]
                      for b in BUDGETS]
            axis.bar(np.arange(2) + (j - .5) * .35, values, .35, label="Lost" if j == 0 else "New")
        axis.set_title(ds["dataset"].split("_")[0].title())
        axis.set_xticks(np.arange(2), ["L64", "L128"]); axis.legend()
    axes[0].set_ylabel("GT10 hits per triple: actual versus independent union")
    fig.tight_layout()
    path = output / "joint_mask_accounting.png"; fig.savefig(path, dpi=170); plt.close(fig); paths.append(path.name)
    return paths


def write_markdown(path, analysis):
    lines = ["# Fast 入口矩阵分析", "", "此文件为固定协议的离线诊断摘要；不发布 QPS 或部署收益。",
             "最优仅限当前 H、L 和目标；最近邻 A0 的目标最好值使用目标标签，属于 oracle。", "",
             "32 项主族均为 query 配对 Recall@10 差；普通 95% 与 Bonferroni32 区间来自 10,000 次 bootstrap。", "",
             "| 数据集 | L | 对比 | ΔRecall (pp) | 95% CI (pp) | 全族 95% CI (pp) |", "|---|---:|---|---:|---|---|"]
    for row in analysis["primary_comparisons"]:
        plain, adjusted = row["ci95_percentage_points"], row["ci95_bonferroni32_percentage_points"]
        lines.append(f"| {row['dataset'].split('_')[0]} | {row['L']} | {row['name']} | "
                     f"{row['mean_delta_percentage_points']:+.3f} | [{plain[0]:+.3f}, {plain[1]:+.3f}] | "
                     f"[{adjusted[0]:+.3f}, {adjusted[1]:+.3f}] |")
    lines += ["", "并列集合、短名单覆盖、GT1 basin 分解、真实组合、跨 L 迁移、Spearman、样本密度及 GT 交集分层见 [analysis.json](analysis.json)。",
              "逐 query 和邻近源映射见 CSV。相关性或当前近邻迁移失败均不证明一般不可学习。"]
    if analysis.get("plots"):
        lines += ["", *[f"![{name}]({name})" for name in analysis["plots"]]]
    Path(path).write_text("\n".join(lines) + "\n")


def self_test():
    # Unique-ID accuracy can be zero while the selected entry is recall-optimal.
    hit = np.array([[10, 10, 2], [7, 7, 7], [0, 0, 0]], dtype=np.uint8)
    ndc = np.array([[9, 9, 1], [4, 3, 3], [2, 2, 2]], dtype=np.uint32)
    base = np.array([50, 20, 30], dtype=np.int32)
    choice = best_single(hit, ndc, base)
    require(choice.tolist() == [1, 1, 1], "real-ID tie arithmetic")
    require(optimal_set(hit, 0).sum(axis=1).tolist() == [2, 3, 3], "optimal plateau arithmetic")
    require(optimal_set(np.array([[10, 9, 8]], dtype=np.uint8), 1).tolist() == [[True, True, False]], "one-hit tolerance")
    mean, best = set_transfer(np.array([[0, 10, 3]]), np.array([[True, True, False]]))
    require(mean[0] == .5 and best[0] == 1., "mean/oracle transfer distinction")
    left = np.array([[10, 10, 0]], dtype=np.int16)
    right = np.array([[0, 10, 10]], dtype=np.int16)
    require(np.logical_and(optimal_set(left), optimal_set(right)).sum() == 1, "cross-L shared solution")
    require(np.minimum(np.maximum(10 - left, 10 - right), 10).min() == 0, "shared-entry regret")
    union = np.array([0b0011], dtype=np.uint16)
    actual = np.array([0b0110], dtype=np.uint16)
    lost = POPCOUNT[union & (~actual & MASK_LIMIT)]
    new = POPCOUNT[actual & (~union & MASK_LIMIT)]
    require(lost[0] == new[0] == 1, "lost/new coexistence")
    require((POPCOUNT[actual].astype(int) - POPCOUNT[union].astype(int))[0]
            == (new.astype(int) - lost.astype(int))[0], "mask accounting")
    maximum, basin, fast = 10, 4, 7
    require(maximum - fast == (maximum - basin) + (basin - fast) and basin - fast < 0,
            "signed basin decomposition")
    stats, digest = bootstrap_group(np.tile([.1, -.2, 0.], (8, 1)), np.random.Generator(np.random.PCG64(SEED)), 1000)
    for result, expected in zip(stats, (.1, -.2, 0.)):
        require(np.allclose(result["ci95_bonferroni32_recall"], expected, atol=1e-15), "constant paired bootstrap")
    repeat, repeat_digest = bootstrap_group(np.tile([.1, -.2, 0.], (8, 1)), np.random.Generator(np.random.PCG64(SEED)), 1000)
    require(stats == repeat and digest == repeat_digest, "bootstrap reproducibility")
    rank = row_spearman(np.array([[1, 2, 3], [1, 2, 3]]), np.array([[0, 1, 1], [1, 1, 1]]))
    require(np.isclose(rank[0], np.sqrt(3) / 2) and np.isnan(rank[1]), "tied Spearman/constant row")
    print(json.dumps({"status": "PASS_SYNTHETIC_ARITHMETIC", "ann_search_calls": 0,
                      "checks": ["real-base-ID ties", "A0/A1", "set transfer", "cross-L shared entry",
                                 "joint lost/new", "signed basin decomposition", "paired bootstrap reproducibility",
                                 "tied Spearman and constant rows"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, help="prepared_v2 directory containing both dataset directories")
    parser.add_argument("--results-root", type=Path, help="main directory containing both completed dataset results")
    parser.add_argument("--output", type=Path, help="new output directory; existing directories are rejected")
    parser.add_argument("--plots", action="store_true", help="write four standalone Matplotlib PNG figures")
    parser.add_argument("--self-test", action="store_true", help="run synthetic arithmetic checks only")
    args = parser.parse_args()
    if args.self_test:
        require(not any((args.input_root, args.results_root, args.output)), "self-test does not accept experiment paths")
        self_test()
        return
    require(all((args.input_root, args.results_root, args.output)), "--input-root, --results-root and --output are required")
    input_root, result_root, output = args.input_root.resolve(), args.results_root.resolve(), args.output.resolve()
    require(input_root.name == "prepared_v2", "real analysis requires final prepared_v2 inputs")
    require(not output.exists(), "refusing to overwrite an existing analysis output")
    started = time.monotonic()
    all_summaries, all_comparisons, query_rows, neighbor_rows, plot_values = [], [], [], [], {}
    rng = np.random.Generator(np.random.PCG64(SEED))
    stream_hashes, consumed = {}, {}
    for name in DATASETS:
        print(f"READ_AND_VALIDATE {name}", flush=True)
        data = Dataset(input_root / name, result_root / name, name)
        ds_summary = {"dataset": name, "num_queries": data.n, "pilot_count": data.p, "hub_count": data.h,
                      "router_diagnostics": router_diagnostics(data), "budgets": {}}
        pending = []
        plot_values[name] = {}
        for budget in BUDGETS:
            print(f"ANALYZE {name} L{budget}", flush=True)
            summary, primary, rows, neighbors, plot = analyze_level(data, budget)
            ds_summary["budgets"][str(budget)] = summary
            pending.extend(primary); query_rows.extend(rows); neighbor_rows.extend(neighbors)
            plot_values[name][budget] = plot
        ds_summary["cross_budget"] = cross_budget(data)
        # Fixed stream order: dataset order above, then all 512-row contrasts, then 128-row contrasts.
        for n in (512, 128):
            group = [item for item in pending if len(item["values"]) == n]
            matrix = np.column_stack([item["values"] for item in group])
            intervals, stream_hash = bootstrap_group(matrix, rng)
            stream_hashes[f"{name}/n{n}"] = stream_hash
            for item, interval in zip(group, intervals):
                item.update(interval)
        for item in pending:
            item.pop("values")
            all_comparisons.append(item)
        ds_summary["validation"] = {"completed_status_checked": True, "input_manifest_sha_checked": True,
            "all_result_ids_to_gt10_masks_recomputed": True, "all_hitcount_popcounts_checked": True,
            "variant_entry_maps_and_duplicate_actions_checked": True, "no_original_base_or_graph_opened_by_analysis": True}
        ds_summary["instrumented_runner_wall_seconds"] = data.meta.get("instrumented_wall_seconds")
        all_summaries.append(ds_summary)
        consumed.update(data.identities)
    require(len(all_comparisons) == FAMILY_SIZE, "primary family incomplete")
    expected = {(d, b, name) for d in DATASETS for b in BUDGETS for name in PRIMARY_NAMES}
    require({(r["dataset"], r["L"], r["name"]) for r in all_comparisons} == expected, "primary family identities mismatch")
    output.mkdir(parents=True, exist_ok=False)
    analysis = {"schema_version": 1, "status": "COMPLETE", "created_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Offline instrumented diagnosis, no QPS/Pareto or deployed-method claim",
        "input_root": str(input_root), "results_root": str(result_root), "analysis_script_sha256": sha256(__file__),
        "protocol_sha256": sha256(Path(__file__).resolve().parents[1] / "protocol.md"),
        "statistics": {"unit": "target query", "bootstrap": "paired percentile, linear quantile",
             "resamples": BOOTSTRAPS, "generator": "numpy.random.PCG64", "seed": SEED,
             "family_size": FAMILY_SIZE, "ordinary_quantiles": [.025, .975],
             "bonferroni_quantiles": [.05 / 64, 1 - .05 / 64],
             "stream_order": "WebVid then Yandex; each dataset n512 then n128; within-group shared row draws",
             "draw_indices_sha256": stream_hashes, "numpy_version": np.__version__,
             "ndc_intervals": "NDC is descriptive; no extra significance family",
             "historical_pilot_only": True},
        "tie_rules": {"single": "max hits, min NDC, min real base ID", "combination": "max hits, min NDC, metadata column",
                      "A1": "one GT10 hit below optimum; 0.1 per-query Recall tolerance, not a negligible quality margin"},
        "primary_comparisons": all_comparisons, "datasets": all_summaries,
        "consumed_file_identities": consumed,
        "warnings": ["Finite candidate/beam oracles use labels and do not measure deployment cost.",
                     "Source-set target best uses target labels; it is an optimistic diagnostic.",
                     "Near-neighbor transfer or one selector failure cannot establish general unlearnability.",
                     "No original base/graph or raw validation/held-out file is opened by this script."]}
    write_csv(output / "per_query.csv", query_rows)
    write_csv(output / "neighbor_transfer.csv", neighbor_rows)
    analysis["plots"] = plot_results(output, all_summaries, plot_values) if args.plots else []
    analysis["analysis_wall_seconds"] = time.monotonic() - started
    (output / "analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    write_markdown(output / "analysis.md", analysis)
    artifacts = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in output.iterdir() if p.is_file()}
    (output / "completion.json").write_text(json.dumps({"status": "COMPLETE", "primary_comparisons": FAMILY_SIZE,
        "search_calls": 0, "model_fits": 0, "analysis_wall_seconds": analysis["analysis_wall_seconds"],
        "artifacts": artifacts}, indent=2) + "\n")
    print(f"COMPLETE {output} seconds={analysis['analysis_wall_seconds']:.3f}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(json.dumps({"status": "ANALYSIS_REJECTED", "error": str(exc)}), file=sys.stderr)
        sys.exit(2)
