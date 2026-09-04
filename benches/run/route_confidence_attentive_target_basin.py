#!/usr/bin/env python3
"""Generate confidence-attentive routes from three target-basin prototype views."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


TOP_PER_VIEW = 8
ALPHAS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)


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
    local = np.argpartition(scores, -TOP_PER_VIEW, axis=1)[:, -TOP_PER_VIEW:]
    values = np.take_along_axis(scores, local, axis=1)
    order = np.argsort(-values, axis=1, kind="stable")
    local = np.take_along_axis(local, order, axis=1)
    return labels[local], np.take_along_axis(scores, local, axis=1)


def alpha_tag(alpha: float) -> str:
    return str(alpha).replace("-", "m").replace(".", "p")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--baseline-shortlist", type=Path, required=True)
    parser.add_argument("--reference-routes", type=Path, required=True)
    parser.add_argument("--expected-split", choices=("drl_train", "validation"), required=True)
    for seed in (28, 29, 30):
        parser.add_argument(f"--seed{seed}-prototypes", type=Path, required=True)
        parser.add_argument(f"--seed{seed}-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--alphas", default=",".join(map(str, ALPHAS)))
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)
    alphas = tuple(float(value) for value in args.alphas.split(","))
    if args.expected_split == "validation" and len(alphas) != 1:
        raise ValueError("validation accepts exactly one train-selected alpha")

    document = json.loads(args.baseline_shortlist.read_text())
    if document.get("split") != args.expected_split or document.get("utility_shortlist") != 32:
        raise ValueError("baseline shortlist split/schema mismatch")
    points = document["results"]
    baseline = np.asarray([row["candidate_entry_ids"] for row in points[0]["queries"]], dtype=np.int32)
    for point in points[1:]:
        current = np.asarray([row["candidate_entry_ids"] for row in point["queries"]], dtype=np.int32)
        if not np.array_equal(current, baseline):
            raise ValueError("baseline shortlist differs across operating points")
    reference = np.fromfile(args.reference_routes, dtype=np.int32).reshape(-1, 3)
    if len(reference) != len(baseline):
        raise ValueError("reference route count mismatch")

    queries = read_fvecs(args.queries, len(baseline))
    specs = [(getattr(args, f"seed{seed}_prototypes"), getattr(args, f"seed{seed}_ids"))
             for seed in (28, 29, 30)]
    models = [load_model(p, i, queries.shape[1]) for p, i in specs]
    seed28_vectors, _, seed28_map = models[0]
    view_ids = [baseline[:, :TOP_PER_VIEW]]
    view_scores = [np.asarray([[queries[q] @ seed28_vectors[seed28_map[int(entry)]]
                               for entry in view_ids[0][q]] for q in range(len(queries))], dtype=np.float32)]
    for vectors, labels, _ in models[1:]:
        ids, scores = exact_top(queries, vectors, labels)
        view_ids.append(ids)
        view_scores.append(scores)
    margins = [scores[:, 0] - scores[:, 1] for scores in view_scores]

    args.output_dir.mkdir(parents=True)
    route_reports = {}
    for alpha in alphas:
        routes = np.empty((len(baseline), 3), dtype=np.int32)
        routes[:, 0] = baseline[:, 0]
        for q in range(len(baseline)):
            candidates: dict[int, float] = {}
            for ids, scores, margin in zip(view_ids, view_scores, margins):
                for entry, score in zip(ids[q], scores[q]):
                    adjusted = float(score + alpha * margin[q])
                    candidates[int(entry)] = max(candidates.get(int(entry), -np.inf), adjusted)
            candidates.pop(int(routes[q, 0]), None)
            selected = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[:2]
            routes[q, 1:] = [entry for entry, _ in selected]
        path = args.output_dir / f"routes_alpha_{alpha_tag(alpha)}.i32"
        routes.tofile(path)
        route_reports[str(alpha)] = {
            "path": str(path), "sha256": sha256(path),
            "reference_order_changed_fraction": float(np.any(routes != reference, axis=1).mean()),
            "reference_set_changed_fraction": float(np.mean([
                set(map(int, routes[i])) != set(map(int, reference[i])) for i in range(len(routes))])),
        }
        if alpha == 0.0 and not np.array_equal(routes, reference):
            raise RuntimeError("alpha=0 does not reproduce the frozen ensemble")

    sources = {"queries": args.queries, "baseline_shortlist": args.baseline_shortlist,
               "reference_routes": args.reference_routes}
    for seed, (prototypes, ids) in zip((28, 29, 30), specs):
        sources[f"seed{seed}_prototypes"] = prototypes
        sources[f"seed{seed}_ids"] = ids
    report = {
        "schema_version": 1, "status": "complete", "split": args.expected_split,
        "method": "confidence-attentive three-view target-basin ensemble",
        "heldout_accessed": False, "labels_used_for_routing": False, "online_graph_probes": 0,
        "top_per_view": TOP_PER_VIEW, "alphas": alphas, "routes": route_reports,
        "sources": {key: {"path": str(path), "sha256": sha256(path)} for key, path in sources.items()},
    }
    (args.output_dir / "route_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
