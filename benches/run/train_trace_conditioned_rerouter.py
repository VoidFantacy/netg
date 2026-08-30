#!/usr/bin/env python3
"""Train and evaluate a trace-conditioned alternate-entry utility reranker."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_probe_failure_detector import trace_features  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_budget(path: Path) -> tuple[dict, list[dict]]:
    document = json.loads(path.read_text())
    if document.get("status") != "complete" or not document.get("budget_pairs"):
        raise ValueError(f"incomplete budget reroute data: {path}")
    return document, document["budget_pairs"]


def router_matrices(trace_document: dict) -> tuple[np.ndarray, np.ndarray]:
    ids = np.asarray([q["router_entry_ids"] for q in trace_document["probe_queries"]], dtype=np.int32)
    distances = np.asarray([q["router_distances"] for q in trace_document["probe_queries"]], dtype=np.float32)
    return ids, distances


def fvecs_memmap(path: Path) -> tuple[np.memmap, int]:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    size = path.stat().st_size
    rows = size // ((dim + 1) * 4)
    return np.memmap(path, mode="r", dtype=np.float32, shape=(rows, dim + 1)), dim


def frontier_affinity_features(
    base: np.memmap, candidate_ids: np.ndarray, trace_document: dict,
    probe_l: int, batch_size: int = 128,
) -> np.ndarray:
    probe_ids = np.asarray([
        next(p["result_ids"] for p in query["probes"] if p["search_L"] == probe_l)
        for query in trace_document["probe_queries"]
    ], dtype=np.int64)
    n, shortlist = candidate_ids.shape
    output = np.empty((n, shortlist, 7), dtype=np.float32)
    for start in range(0, n, batch_size):
        end = min(n, start + batch_size)
        candidate_vectors = np.asarray(base[candidate_ids[start:end], 1:], dtype=np.float32)
        frontier_vectors = np.asarray(base[probe_ids[start:end], 1:], dtype=np.float32)
        similarities = np.einsum("bsd,btd->bst", candidate_vectors, frontier_vectors, optimize=True)
        output[start:end, :, 0] = similarities[:, :, 0]
        output[start:end, :, 1] = similarities.max(axis=2)
        output[start:end, :, 2] = similarities.mean(axis=2)
        output[start:end, :, 3] = similarities.min(axis=2)
        output[start:end, :, 4] = similarities.std(axis=2)
        output[start:end, :, 5] = similarities.max(axis=2) - similarities.mean(axis=2)
        output[start:end, :, 6] = (candidate_ids[start:end, :, None] == probe_ids[start:end, None, :]).any(axis=2)
    return output


def pair_arrays(pair: dict) -> dict[str, np.ndarray]:
    queries = pair["queries"]
    arrays = {
        "ids": np.asarray([q["candidate_entry_ids"] for q in queries], dtype=np.int32),
        "recalls": np.asarray([q["candidate_merged_recalls"] for q in queries], dtype=np.float32),
        "ndcs": np.asarray([q["candidate_total_graph_ndcs"] for q in queries], dtype=np.float32),
        "baseline_recall": np.asarray([q["baseline_recall"] for q in queries], dtype=np.float32),
        "baseline_ndc": np.asarray([q["baseline_graph_ndc"] for q in queries], dtype=np.float32),
        "restart_recall": np.asarray([q["restart_merged_recall"] for q in queries], dtype=np.float32),
        "restart_ndc": np.asarray([q["restart_total_graph_ndc"] for q in queries], dtype=np.float32),
    }
    topology_rows = [q.get("candidate_topology_features") for q in queries]
    if any(row is not None for row in topology_rows):
        if not all(row is not None for row in topology_rows):
            raise ValueError("candidate topology features are only partially present")
        topology = np.asarray(topology_rows, dtype=np.float32)
        expected = (*arrays["ids"].shape, 7)
        if topology.shape != expected:
            raise ValueError(f"candidate topology shape {topology.shape} != {expected}")
        arrays["topology"] = topology
    return arrays


def global_entry_stats(ids: np.ndarray, utility: np.ndarray, gain: np.ndarray, ndc_ratio: np.ndarray) -> dict[int, tuple[float, float, float, float]]:
    flat_ids = ids.ravel()
    flat_u = utility.ravel()
    flat_gain = gain.ravel()
    flat_ndc = ndc_ratio.ravel()
    stats = {}
    for entry in np.unique(flat_ids):
        mask = flat_ids == entry
        stats[int(entry)] = (float(flat_u[mask].mean()), float(flat_gain[mask].mean()),
                             float(flat_ndc[mask].mean()), float(np.log1p(mask.sum())))
    return stats


def candidate_features(
    trace: np.ndarray, candidate_ids: np.ndarray, router_distances: np.ndarray,
    stats: dict[int, tuple[float, float, float, float]], include_trace: bool,
    candidate_extra: np.ndarray | None = None,
) -> np.ndarray:
    n, shortlist = candidate_ids.shape
    ranks = np.broadcast_to(np.arange(shortlist, dtype=np.float32) / max(shortlist - 1, 1), (n, shortlist))
    gaps = router_distances - router_distances[:, :1]
    global_values = np.empty((n, shortlist, 4), dtype=np.float32)
    fallback = (0.0, 0.0, 1.0, 0.0)
    for rank in range(shortlist):
        global_values[:, rank] = [stats.get(int(entry), fallback) for entry in candidate_ids[:, rank]]
    parts = [ranks[..., None], router_distances[..., None], gaps[..., None], global_values]
    if candidate_extra is not None:
        parts.append(candidate_extra)
    local = np.concatenate(parts, axis=2)
    flat_local = local.reshape(n * shortlist, -1)
    if not include_trace:
        return flat_local
    return np.concatenate([np.repeat(trace, shortlist, axis=0), flat_local], axis=1)


def policy_metrics(
    risk_scores: np.ndarray, chosen_index: np.ndarray, arrays: dict[str, np.ndarray], fractions: list[float]
) -> dict:
    n = len(risk_scores)
    q_idx = np.arange(n)
    chosen_recall = arrays["recalls"][q_idx, chosen_index]
    chosen_ndc = arrays["ndcs"][q_idx, chosen_index]
    order = np.argsort(-risk_scores)
    baseline_r = float(arrays["baseline_recall"].mean())
    baseline_n = float(arrays["baseline_ndc"].mean())
    result = {
        "baseline_recall": baseline_r, "baseline_graph_ndc": baseline_n,
        "restart_recall": float(arrays["restart_recall"].mean()),
        "restart_total_graph_ndc": float(arrays["restart_ndc"].mean()),
        "chosen_candidate_mean_recall": float(chosen_recall.mean()),
        "chosen_candidate_mean_ndc": float(chosen_ndc.mean()),
    }
    for fraction in fractions:
        count = int(n * fraction)
        selected = order[:count]
        recall = arrays["restart_recall"].copy()
        ndc = arrays["restart_ndc"].copy()
        recall[selected] = chosen_recall[selected]
        ndc[selected] = chosen_ndc[selected]
        prefix = f"top_{int(fraction * 100)}pct"
        result[prefix] = {
            "recall": float(recall.mean()),
            "recall_delta_pp_vs_baseline": float((recall.mean() - baseline_r) * 100),
            "total_graph_ndc": float(ndc.mean()),
            "ndc_delta_pct_vs_baseline": float((ndc.mean() / baseline_n - 1) * 100),
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-budget", type=Path, required=True)
    parser.add_argument("--validation-budget", type=Path, required=True)
    parser.add_argument("--train-trace", type=Path, required=True)
    parser.add_argument("--validation-trace", type=Path, required=True)
    parser.add_argument("--risk-model", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cost-weight", type=float, default=0.05)
    parser.add_argument("--max-probe-L", type=int, default=0)
    args = parser.parse_args()

    train_doc, train_pairs = load_budget(args.train_budget)
    val_doc, val_pairs = load_budget(args.validation_budget)
    train_static, train_trace, _, _, train_trace_doc = trace_features(args.train_trace, args.max_probe_L)
    val_static, val_trace, _, _, val_trace_doc = trace_features(args.validation_trace, args.max_probe_L)
    if train_doc["dataset"] != val_doc["dataset"] or train_doc["dataset"] != train_trace_doc["dataset"] or train_doc["dataset"] != val_trace_doc["dataset"]:
        raise ValueError("dataset mismatch")
    train_router_ids, train_router_distances = router_matrices(train_trace_doc)
    val_router_ids, val_router_distances = router_matrices(val_trace_doc)
    risk_model = joblib.load(args.risk_model)
    risk_scores = risk_model.predict_proba(val_trace)[:, 1]
    base, base_dim = fvecs_memmap(args.base)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    pair_reports = []

    for train_pair, val_pair in zip(train_pairs, val_pairs):
        if (train_pair["target_L"], train_pair["reroute_L"]) != (val_pair["target_L"], val_pair["reroute_L"]):
            raise ValueError("budget pair mismatch")
        train = pair_arrays(train_pair)
        val = pair_arrays(val_pair)
        if not np.array_equal(train["ids"], train_router_ids) or not np.array_equal(val["ids"], val_router_ids):
            raise ValueError("budget candidates differ from online router top-32")
        train_ndc_ratio = train["ndcs"] / np.maximum(train["baseline_ndc"][:, None], 1.0)
        train_utility = train["recalls"] - args.cost_weight * train_ndc_ratio
        train_gain = train["recalls"] - train["restart_recall"][:, None]
        stats = global_entry_stats(train["ids"], train_utility, train_gain, train_ndc_ratio)
        sample_weight = 1.0 + 2.0 * np.maximum(train_gain, 0.0)
        target = train_utility.ravel()
        train_frontier = frontier_affinity_features(base, train["ids"], train_trace_doc, train_doc["probe_L"])
        val_frontier = frontier_affinity_features(base, val["ids"], val_trace_doc, val_doc["probe_L"])
        if "topology" not in train or "topology" not in val:
            raise ValueError("topology-aware gate requires candidate_topology_features")
        train_frontier_topology = np.concatenate([train_frontier, train["topology"]], axis=2)
        val_frontier_topology = np.concatenate([val_frontier, val["topology"]], axis=2)

        models = {}
        predictions = {}
        for name, include_trace, train_extra, val_extra in (
            ("candidate_static", False, None, None),
            ("trace_conditioned", True, None, None),
            ("frontier_conditioned", True, train_frontier, val_frontier),
            ("topology_conditioned", True, train["topology"], val["topology"]),
            ("frontier_topology_conditioned", True, train_frontier_topology, val_frontier_topology),
        ):
            x_train = candidate_features(train_trace, train["ids"], train_router_distances, stats, include_trace, train_extra)
            x_val = candidate_features(val_trace, val["ids"], val_router_distances, stats, include_trace, val_extra)
            model = HistGradientBoostingRegressor(
                learning_rate=0.05, max_iter=200, max_leaf_nodes=31,
                min_samples_leaf=80, l2_regularization=1.0,
            )
            model.fit(x_train, target, sample_weight=sample_weight.ravel())
            scores = model.predict(x_val).reshape(val["ids"].shape)
            predictions[name] = np.argmax(scores, axis=1)
            model_path = args.output_dir / f"{name}_targetL{train_pair['target_L']}.joblib"
            joblib.dump(model, model_path)
            models[name] = {"path": str(model_path), "sha256": sha256(model_path)}

        val_ndc_ratio = val["ndcs"] / np.maximum(val["baseline_ndc"][:, None], 1.0)
        val_utility = val["recalls"] - args.cost_weight * val_ndc_ratio
        oracle_index = np.argmax(val_utility, axis=1)
        report = {
            "target_L": train_pair["target_L"], "reroute_L": train_pair["reroute_L"],
            "models": models,
            "candidate_static": policy_metrics(risk_scores, predictions["candidate_static"], val, [0.1, 0.2, 0.3, 0.5]),
            "trace_conditioned": policy_metrics(risk_scores, predictions["trace_conditioned"], val, [0.1, 0.2, 0.3, 0.5]),
            "frontier_conditioned": policy_metrics(risk_scores, predictions["frontier_conditioned"], val, [0.1, 0.2, 0.3, 0.5]),
            "topology_conditioned": policy_metrics(risk_scores, predictions["topology_conditioned"], val, [0.1, 0.2, 0.3, 0.5]),
            "frontier_topology_conditioned": policy_metrics(risk_scores, predictions["frontier_topology_conditioned"], val, [0.1, 0.2, 0.3, 0.5]),
            "alternate_oracle": policy_metrics(risk_scores, oracle_index, val, [0.1, 0.2, 0.3, 0.5]),
            "predicted_routes": {},
        }
        for name, indices in predictions.items():
            routes = val["ids"][np.arange(len(indices)), indices].astype(np.int32)
            route_path = args.output_dir / f"routes_{name}_targetL{train_pair['target_L']}.bin"
            routes.tofile(route_path)
            report["predicted_routes"][name] = {"path": str(route_path), "sha256": sha256(route_path)}
        pair_reports.append(report)

    final_report = {
        "schema_version": 2,
        "method": "trace-conditioned topology-aware merged-utility alternate-entry ranking",
        "dataset": train_doc["dataset"], "train_split": train_doc["split"],
        "validation_split": val_doc["split"], "train_queries": train_doc["num_queries"],
        "validation_queries": val_doc["num_queries"], "probe_L": train_doc["probe_L"],
        "shortlist": 32, "cost_weight": args.cost_weight, "max_probe_L": args.max_probe_L,
        "candidate_topology_feature_dim": 7,
        "base": str(args.base), "base_sha256": sha256(args.base), "base_dim": base_dim,
        "risk_model": str(args.risk_model), "risk_model_sha256": sha256(args.risk_model),
        "budget_pairs": pair_reports,
        "sources": {
            "train_budget": str(args.train_budget), "train_budget_sha256": sha256(args.train_budget),
            "validation_budget": str(args.validation_budget), "validation_budget_sha256": sha256(args.validation_budget),
            "train_trace": str(args.train_trace), "train_trace_sha256": sha256(args.train_trace),
            "validation_trace": str(args.validation_trace), "validation_trace_sha256": sha256(args.validation_trace),
        },
    }
    (args.output_dir / "report.json").write_text(json.dumps(final_report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(final_report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
