#!/usr/bin/env python3
"""Generate Fast-rank0-anchored routes from three independent target-basin builds."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


TOP_PER_SEED = 8
TOP_M = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(rows: np.ndarray) -> np.ndarray:
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)


def read_fvecs(path: Path, count: int) -> np.ndarray:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    raw = np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1)
    if len(raw) < count or not np.all(raw[:count, 0].copy().view(np.int32) == dim):
        raise ValueError(f"invalid query fvecs: {path}")
    return normalize(np.asarray(raw[:count, 1:], dtype=np.float32).copy())


def load_model(prototypes: Path, ids: Path, dim: int) -> tuple[np.ndarray, np.ndarray, dict[int, int]]:
    labels = np.fromfile(ids, dtype=np.int32)
    vectors = normalize(np.fromfile(prototypes, dtype=np.float32).reshape(len(labels), dim))
    if len(set(map(int, labels))) != len(labels):
        raise ValueError(f"duplicate IDs in {ids}")
    return vectors, labels, {int(label): i for i, label in enumerate(labels)}


def exact_top(query: np.ndarray, vectors: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    scores = query @ vectors.T
    local = np.argpartition(scores, -TOP_PER_SEED, axis=1)[:, -TOP_PER_SEED:]
    values = np.take_along_axis(scores, local, axis=1)
    order = np.argsort(-values, axis=1, kind="stable")
    local = np.take_along_axis(local, order, axis=1)
    return labels[local], np.take_along_axis(scores, local, axis=1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline-shortlist", type=Path, required=True)
    parser.add_argument("--expected-split", choices=("drl_train", "validation"), required=True)
    parser.add_argument("--seed28-prototypes", type=Path, required=True)
    parser.add_argument("--seed28-ids", type=Path, required=True)
    parser.add_argument("--seed29-prototypes", type=Path, required=True)
    parser.add_argument("--seed29-ids", type=Path, required=True)
    parser.add_argument("--seed30-prototypes", type=Path, required=True)
    parser.add_argument("--seed30-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    document = json.loads(args.baseline_shortlist.read_text())
    if document.get("split") != args.expected_split or document.get("utility_shortlist") != 32:
        raise ValueError("baseline shortlist split/schema mismatch")
    points = document["results"]
    baseline = np.asarray([row["candidate_entry_ids"] for row in points[0]["queries"]], dtype=np.int32)
    for point in points[1:]:
        current = np.asarray([row["candidate_entry_ids"] for row in point["queries"]], dtype=np.int32)
        if not np.array_equal(current, baseline):
            raise ValueError("baseline shortlist differs across operating points")
    queries = read_fvecs(args.queries, len(baseline))
    specs = [(args.seed28_prototypes, args.seed28_ids), (args.seed29_prototypes, args.seed29_ids),
             (args.seed30_prototypes, args.seed30_ids)]
    models = [load_model(p, i, queries.shape[1]) for p, i in specs]
    seed_top = [exact_top(queries, vectors, labels) for vectors, labels, _ in models[1:]]
    seed28_vectors, _, seed28_map = models[0]

    routes = np.empty((len(baseline), TOP_M), dtype=np.int32)
    routes[:, 0] = baseline[:, 0]
    for q in range(len(baseline)):
        candidates: dict[int, float] = {}
        for entry in baseline[q, :TOP_PER_SEED]:
            entry_int = int(entry)
            candidates[entry_int] = float(queries[q] @ seed28_vectors[seed28_map[entry_int]])
        for ids, scores in seed_top:
            for entry, score in zip(ids[q], scores[q]):
                candidates[int(entry)] = max(candidates.get(int(entry), -np.inf), float(score))
        candidates.pop(int(routes[q, 0]), None)
        selected = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[:2]
        routes[q, 1:] = [entry for entry, _ in selected]

    args.output_dir.mkdir(parents=True)
    route_path = args.output_dir / f"routes_{args.expected_split}_top3.i32"
    routes.tofile(route_path)
    baseline_top3 = baseline[:, :TOP_M]
    sources = {"queries": args.queries, "baseline_shortlist": args.baseline_shortlist}
    for seed, (prototypes, ids) in zip((28, 29, 30), specs):
        sources[f"seed{seed}_prototypes"] = prototypes
        sources[f"seed{seed}_ids"] = ids
    report = {
        "schema_version": 1, "status": "complete", "split": args.expected_split,
        "method": "Fast-rank0-anchored three-seed target-basin ensemble", "method_frozen": True,
        "heldout_accessed": False, "labels_used_for_routing": False, "online_graph_probes": 0,
        "rank0_preserved": bool(np.array_equal(routes[:, 0], baseline_top3[:, 0])),
        "route_top3_order_changed_fraction": float(np.any(routes != baseline_top3, axis=1).mean()),
        "route_top3_set_changed_fraction": float(np.mean([
            set(map(int, routes[i])) != set(map(int, baseline_top3[i])) for i in range(len(routes))])),
        "candidate_union_upper_bound": 24, "prototype_index_count": 3,
        "sources": {key: {"path": str(path), "sha256": sha256(path)} for key, path in sources.items()},
        "route": {"path": str(route_path), "sha256": sha256(route_path), "bytes": route_path.stat().st_size},
    }
    (args.output_dir / "route_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
