#!/usr/bin/env python3
"""Train-only local cost-first atlas distilled from finite-beam utility probes."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


FIT_END = 1600
AUDIT_END = 2000
NEIGHBORS = 64
MIN_OBSERVATIONS = 4
COST_LIMIT = 0.005
COST_WEIGHT = 0.05
BOOTSTRAP_ROUNDS = 10000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_fvecs(path: Path, count: int) -> np.ndarray:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    raw = np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1)
    if len(raw) < count or not np.all(raw[:count, 0].copy().view(np.int32) == dim):
        raise ValueError(f"invalid or too-short fvecs: {path}")
    rows = np.asarray(raw[:count, 1:], dtype=np.float32).copy()
    rows /= np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)
    return rows


def bootstrap_ci(values: np.ndarray, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    means = np.empty(BOOTSTRAP_ROUNDS)
    for start in range(0, BOOTSTRAP_ROUNDS, 200):
        count = min(200, BOOTSTRAP_ROUNDS - start)
        sample = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start + count] = values[sample].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def weighted_mean_se(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    weights = weights / weights.sum()
    mean = float(weights @ values)
    effective_n = 1.0 / float(weights @ weights)
    variance = float(weights @ np.square(values - mean))
    return mean, float(np.sqrt(variance / max(effective_n, 1.0)))


def matrices(document: dict, search_l: int) -> dict[str, np.ndarray]:
    rows = [row for row in document["rows"] if row["search_L"] == search_l]
    candidate_count = int(document["candidate_count"])
    expected = AUDIT_END * candidate_count
    if len(rows) != expected:
        raise ValueError(f"expected {expected} rows for L={search_l}, got {len(rows)}")
    rows.sort(key=lambda row: (row["query_id"], row["geometry_rank"]))
    query_ids = np.asarray([row["query_id"] for row in rows]).reshape(AUDIT_END, candidate_count)
    ranks = np.asarray([row["geometry_rank"] for row in rows]).reshape(AUDIT_END, candidate_count)
    if not np.all(query_ids == np.arange(AUDIT_END)[:, None]) or not np.all(ranks == np.arange(candidate_count)):
        raise ValueError("query/rank layout does not match frozen [0,2000) top-8 protocol")
    result = {}
    for name, key, dtype in (
        ("entry", "entry_id", np.int32), ("recall", "recall_at_10", np.float64),
        ("ndc", "graph_ndc", np.float64), ("fast_ndc", "fast_top3_graph_ndc", np.float64),
    ):
        result[name] = np.asarray([row[key] for row in rows], dtype=dtype).reshape(AUDIT_END, candidate_count)
    result["utility"] = result["recall"] - COST_WEIGHT * result["ndc"] / np.maximum(result["fast_ndc"], 1.0)
    result["relative_ndc"] = result["ndc"] / result["ndc"][:, :1] - 1.0
    result["margin"] = result["utility"] - result["utility"][:, :1]
    return result


def evaluate(document: dict, queries: np.ndarray, search_l: int, seed: int) -> tuple[dict, np.ndarray]:
    data = matrices(document, search_l)
    similarities = queries[FIT_END:AUDIT_END] @ queries[:FIT_END].T
    neighbor_ids = np.argpartition(similarities, -NEIGHBORS, axis=1)[:, -NEIGHBORS:]
    ordered = np.take_along_axis(similarities, neighbor_ids, axis=1).argsort(axis=1)[:, ::-1]
    neighbor_ids = np.take_along_axis(neighbor_ids, ordered, axis=1)

    selected_ranks = np.zeros(AUDIT_END - FIT_END, dtype=np.int32)
    available_counts = np.zeros_like(selected_ranks)
    for local_query, query_id in enumerate(range(FIT_END, AUDIT_END)):
        best_score = 0.0
        neighbors = neighbor_ids[local_query]
        neighbor_similarity = similarities[local_query, neighbors]
        for rank, entry in enumerate(data["entry"][query_id]):
            hits = np.argwhere(data["entry"][neighbors] == entry)
            if len(hits) < MIN_OBSERVATIONS:
                continue
            neighbor_rows = neighbors[hits[:, 0]]
            neighbor_ranks = hits[:, 1]
            weights = np.maximum(neighbor_similarity[hits[:, 0]], 0.0)
            ndc_mean, ndc_se = weighted_mean_se(data["relative_ndc"][neighbor_rows, neighbor_ranks], weights)
            margin_mean, margin_se = weighted_mean_se(data["margin"][neighbor_rows, neighbor_ranks], weights)
            available_counts[local_query] += 1
            lower_margin = margin_mean - margin_se
            if ndc_mean + ndc_se <= COST_LIMIT and lower_margin > best_score:
                selected_ranks[local_query] = rank
                best_score = lower_margin

    audit_rows = np.arange(FIT_END, AUDIT_END)
    selected_recall = data["recall"][audit_rows, selected_ranks]
    selected_ndc = data["ndc"][audit_rows, selected_ranks]
    selected_utility = data["utility"][audit_rows, selected_ranks]
    baseline_recall = data["recall"][audit_rows, 0]
    baseline_ndc = data["ndc"][audit_rows, 0]
    baseline_utility = data["utility"][audit_rows, 0]
    utility_delta = selected_utility - baseline_utility
    recall_delta = selected_recall - baseline_recall
    ndc_relative = float(selected_ndc.mean() / baseline_ndc.mean() - 1.0)
    ci = bootstrap_ci(utility_delta, seed)
    reroute_fraction = float((selected_ranks != 0).mean())
    passed = (float(utility_delta.mean()) > 0 and ci[0] > 0
              and float(recall_delta.mean()) >= 0 and ndc_relative <= COST_LIMIT
              and reroute_fraction >= 0.01)
    report = {
        "search_L": search_l, "passed": bool(passed),
        "mean_utility_delta": float(utility_delta.mean()), "utility_delta_ci95": ci,
        "mean_recall_delta": float(recall_delta.mean()),
        "mean_graph_ndc_relative_delta": ndc_relative,
        "reroute_fraction": reroute_fraction,
        "mean_available_candidates": float(available_counts.mean()),
        "min_available_candidates": int(available_counts.min()),
    }
    routes = np.column_stack((audit_rows, selected_ranks, data["entry"][audit_rows, selected_ranks]))
    return report, routes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.trace.read_text())
    if document.get("status") != "complete" or document.get("split") != "drl_train":
        raise ValueError("requires a completed drl_train trace")
    if document.get("heldout_accessed") is not False or document.get("num_queries") != AUDIT_END:
        raise ValueError("input violates frozen train-only protocol")
    queries = read_fvecs(args.queries, AUDIT_END)
    args.output_dir.mkdir(parents=True, exist_ok=False)

    results = []
    route_files = {}
    for search_l in (64, 128):
        result, routes = evaluate(document, queries, search_l, 20260903 + search_l)
        path = args.output_dir / f"routes_train_audit_l{search_l}.npy"
        np.save(path, routes)
        route_files[str(search_l)] = {"path": str(path), "sha256": sha256(path)}
        results.append(result)

    model_path = args.output_dir / "atlas_fit.npz"
    packed = {"queries": queries[:FIT_END].astype(np.float32)}
    for search_l in (64, 128):
        data = matrices(document, search_l)
        for key in ("entry", "relative_ndc", "margin"):
            packed[f"l{search_l}_{key}"] = data[key][:FIT_END].astype(
                np.int32 if key == "entry" else np.float32)
    np.savez(model_path, **packed)
    all_pass = all(result["passed"] for result in results)
    report = {
        "schema_version": 1, "status": "complete", "dataset": document["dataset"],
        "split": "drl_train", "fit_rows": [0, FIT_END], "audit_rows": [FIT_END, AUDIT_END],
        "heldout_accessed": False, "validation_accessed": False,
        "method": "local cost-first reachability utility atlas",
        "frozen_parameters": {"neighbors": NEIGHBORS, "min_observations": MIN_OBSERVATIONS,
                              "cost_limit": COST_LIMIT, "confidence_margin_se": 1.0,
                              "cost_weight": COST_WEIGHT},
        "online_inputs": ["query vector", "Fast geometry top-8 IDs", "atlas_fit.npz"],
        "online_graph_probes": 0, "results": results,
        "train_internal_gate": "PASS" if all_pass else "FAIL",
        "sources": {"trace": str(args.trace), "trace_sha256": sha256(args.trace),
                    "queries": str(args.queries), "queries_sha256": sha256(args.queries)},
        "artifacts": {"atlas": str(model_path), "atlas_sha256": sha256(model_path),
                      "atlas_bytes": model_path.stat().st_size, "routes": route_files},
    }
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
