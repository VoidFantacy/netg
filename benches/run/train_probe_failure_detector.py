#!/usr/bin/env python3
"""Test whether GT-free early graph traces predict actionable entry reroutes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, roc_auc_score


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summary_features(values: np.ndarray) -> list[float]:
    return [float(values[0]), float(values[-1]), float(values.mean()),
            float(values.std()), float(values[-1] - values[0])]


def trace_features(path: Path, max_probe_l: int = 0) -> tuple[np.ndarray, np.ndarray, list[str], list[str], dict]:
    document = json.loads(path.read_text())
    if document.get("status") != "complete" or not document.get("probe_queries"):
        raise ValueError(f"incomplete probe trace: {path}")
    static_rows, trace_rows = [], []
    static_names = [f"router_distance_{i}" for i in range(8)]
    static_names += [f"router_gap_{i}_{i+1}" for i in range(7)]
    static_names += ["router_first", "router_last", "router_mean", "router_std", "router_range"]
    trace_names: list[str] = []

    probe_ls = [value for value in document["probe_Ls"] if max_probe_l <= 0 or value <= max_probe_l]
    if not probe_ls:
        raise ValueError("no probe L remains after max_probe_l filter")
    for L in probe_ls:
        trace_names += [f"L{L}_ndc"]
        trace_names += [f"L{L}_distance_{i}" for i in range(10)]
        trace_names += [f"L{L}_gap_{i}_{i+1}" for i in range(9)]
        trace_names += [f"L{L}_{name}" for name in ("first", "last", "mean", "std", "range")]
    for left, right in zip(probe_ls, probe_ls[1:]):
        trace_names += [f"L{left}_L{right}_result_overlap", f"L{left}_L{right}_top1_same",
                        f"L{left}_L{right}_best_delta", f"L{left}_L{right}_worst_delta",
                        f"L{left}_L{right}_ndc_delta"]

    for query in document["probe_queries"]:
        router = np.asarray(query["router_distances"], dtype=np.float32)
        static = list(map(float, router[:8]))
        static += list(map(float, np.diff(router[:8])))
        static += summary_features(router)
        probe_values: list[float] = []
        parsed = []
        for probe in query["probes"]:
            if probe["search_L"] not in probe_ls:
                continue
            distances = np.asarray(probe["result_distances"], dtype=np.float32)
            probe_values.append(float(probe["graph_ndc"]))
            probe_values += list(map(float, distances))
            probe_values += list(map(float, np.diff(distances)))
            probe_values += summary_features(distances)
            parsed.append((set(probe["result_ids"]), distances, float(probe["graph_ndc"])))
        for (ids_a, dist_a, ndc_a), (ids_b, dist_b, ndc_b) in zip(parsed, parsed[1:]):
            probe_values += [len(ids_a & ids_b) / max(len(ids_a | ids_b), 1),
                             float(dist_a[0] == dist_b[0]), float(dist_b[0] - dist_a[0]),
                             float(dist_b[-1] - dist_a[-1]), ndc_b - ndc_a]
        static_rows.append(static)
        trace_rows.append(static + probe_values)
    return (np.asarray(static_rows, dtype=np.float32), np.asarray(trace_rows, dtype=np.float32),
            static_names, static_names + trace_names, document)


def utility_targets(path: Path) -> tuple[np.ndarray, dict]:
    document = json.loads(path.read_text())
    rows = document["results"]
    recalls = np.stack([[q["candidate_recalls"] for q in row["queries"]] for row in rows])
    fast = np.stack([[q["fast_top3_recall"] for q in row["queries"]] for row in rows])
    candidate_mean = recalls.mean(axis=0)
    gain = candidate_mean.max(axis=1) - fast.mean(axis=0)
    return gain.astype(np.float32), document


def evaluate(scores: np.ndarray, labels: np.ndarray, gains: np.ndarray) -> dict:
    order = np.argsort(-scores)
    total_gain = float(np.maximum(gains, 0).sum())
    result = {
        "roc_auc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
    }
    for fraction in (0.05, 0.10, 0.20):
        count = max(1, int(len(scores) * fraction))
        chosen = order[:count]
        result[f"top_{int(fraction*100)}pct_positive_rate"] = float(labels[chosen].mean())
        result[f"top_{int(fraction*100)}pct_mean_oracle_gain"] = float(gains[chosen].mean())
        result[f"top_{int(fraction*100)}pct_total_gain_coverage"] = float(
            np.maximum(gains[chosen], 0).sum() / max(total_gain, 1e-12)
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-trace", type=Path, required=True)
    parser.add_argument("--validation-trace", type=Path, required=True)
    parser.add_argument("--train-utility", type=Path, required=True)
    parser.add_argument("--validation-utility", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--gain-threshold", type=float, default=0.1)
    parser.add_argument("--max-probe-L", type=int, default=0)
    args = parser.parse_args()

    train_static, train_trace, static_names, trace_names, train_trace_doc = trace_features(args.train_trace, args.max_probe_L)
    val_static, val_trace, _, _, val_trace_doc = trace_features(args.validation_trace, args.max_probe_L)
    train_gain, train_utility_doc = utility_targets(args.train_utility)
    val_gain, val_utility_doc = utility_targets(args.validation_utility)
    if train_trace_doc["split"] != "drl_train" or val_trace_doc["split"] != "validation":
        raise ValueError("trace split contract mismatch")
    if train_trace_doc["dataset"] != val_trace_doc["dataset"] or train_trace_doc["dataset"] != train_utility_doc["dataset"] or train_trace_doc["dataset"] != val_utility_doc["dataset"]:
        raise ValueError("dataset contract mismatch")
    if len(train_gain) != len(train_trace) or len(val_gain) != len(val_trace):
        raise ValueError("query alignment mismatch")
    train_labels = train_gain >= args.gain_threshold - 1e-7
    val_labels = val_gain >= args.gain_threshold - 1e-7
    seeds = [int(value) for value in args.seeds.split(",")]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    runs = []

    for seed in seeds:
        models = {}
        metrics = {}
        for name, x_train, x_val in (
            ("router_static", train_static, val_static),
            ("router_plus_probe_trace", train_trace, val_trace),
        ):
            model = HistGradientBoostingClassifier(
                learning_rate=0.05, max_iter=200, max_leaf_nodes=15,
                min_samples_leaf=40, l2_regularization=1.0, random_state=seed,
            )
            model.fit(x_train, train_labels)
            scores = model.predict_proba(x_val)[:, 1]
            metrics[name] = evaluate(scores, val_labels, val_gain)
            models[name] = model
            joblib.dump(model, args.output_dir / f"{name}_seed{seed}.joblib")
        runs.append({"seed": seed, "metrics": metrics})

    oracle_order = np.argsort(-val_gain)
    oracle_metrics = {}
    total_gain = float(np.maximum(val_gain, 0).sum())
    for fraction in (0.05, 0.10, 0.20):
        count = int(len(val_gain) * fraction)
        chosen = oracle_order[:count]
        oracle_metrics[f"top_{int(fraction*100)}pct_positive_rate"] = float(val_labels[chosen].mean())
        oracle_metrics[f"top_{int(fraction*100)}pct_mean_oracle_gain"] = float(val_gain[chosen].mean())
        oracle_metrics[f"top_{int(fraction*100)}pct_total_gain_coverage"] = float(
            np.maximum(val_gain[chosen], 0).sum() / max(total_gain, 1e-12)
        )

    report = {
        "schema_version": 1,
        "method": "GT-free early-probe actionable-reroute detection gate",
        "dataset": train_trace_doc["dataset"],
        "train_split": train_trace_doc["split"], "validation_split": val_trace_doc["split"],
        "train_queries": len(train_gain), "validation_queries": len(val_gain),
        "available_probe_Ls": train_trace_doc["probe_Ls"],
        "used_probe_Ls": [value for value in train_trace_doc["probe_Ls"] if args.max_probe_L <= 0 or value <= args.max_probe_L],
        "gain_threshold": args.gain_threshold,
        "train_positive_rate": float(train_labels.mean()),
        "validation_positive_rate": float(val_labels.mean()),
        "validation_mean_shortlist_oracle_gain": float(val_gain.mean()),
        "static_feature_count": len(static_names), "trace_feature_count": len(trace_names),
        "runs": runs, "validation_oracle_selection": oracle_metrics,
        "sources": {
            "train_trace": str(args.train_trace), "train_trace_sha256": sha256(args.train_trace),
            "validation_trace": str(args.validation_trace), "validation_trace_sha256": sha256(args.validation_trace),
            "train_utility": str(args.train_utility), "train_utility_sha256": sha256(args.train_utility),
            "validation_utility": str(args.validation_utility), "validation_utility_sha256": sha256(args.validation_utility),
        },
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
