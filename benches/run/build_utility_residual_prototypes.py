#!/usr/bin/env python3
"""Build closed-form prototypes from sparse continuous Recall/NDC utilities."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


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
    return np.asarray(raw[:count, 1:], dtype=np.float32).copy()


def normalize(rows: np.ndarray) -> np.ndarray:
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utility-json", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--base-prototypes", type=Path, required=True)
    parser.add_argument("--hub-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.25)
    parser.add_argument("--cost-weight", type=float, default=0.05)
    parser.add_argument("--tail-weight", type=float, default=1.0)
    args = parser.parse_args()

    document = json.loads(args.utility_json.read_text())
    if document.get("status") != "complete" or document.get("split") != "drl_train":
        raise ValueError("requires completed independent drl_train sparse utility")
    rows = document["results"]
    if not rows or any(row["top_k"] != 10 for row in rows):
        raise ValueError("first pilot requires Recall@10 utility rows")
    query_count = document["num_queries"]
    shortlist = document["utility_shortlist"]

    candidate_ids = np.asarray(
        [item["candidate_entry_ids"] for item in rows[0]["queries"]], dtype=np.int32
    )
    if candidate_ids.shape != (query_count, shortlist):
        raise ValueError("candidate matrix shape mismatch")
    recalls = []
    ndcs = []
    fast_recalls = []
    for row in rows:
        current_ids = np.asarray(
            [item["candidate_entry_ids"] for item in row["queries"]], dtype=np.int32
        )
        if not np.array_equal(current_ids, candidate_ids):
            raise ValueError("shortlist changed across utility operating points")
        recalls.append(np.asarray([item["candidate_recalls"] for item in row["queries"]], dtype=np.float32))
        ndcs.append(np.asarray([item["candidate_graph_ndcs"] for item in row["queries"]], dtype=np.float32))
        fast_recalls.append(np.asarray([item["fast_top3_recall"] for item in row["queries"]], dtype=np.float32))

    mean_recall = np.mean(recalls, axis=0)
    mean_ndc = np.mean(ndcs, axis=0)
    relative_ndc = mean_ndc / np.maximum(mean_ndc.mean(axis=1, keepdims=True), 1.0)
    utility = mean_recall - args.cost_weight * relative_ndc
    advantage = utility - utility.mean(axis=1, keepdims=True)
    hardness = 1.0 + args.tail_weight * (1.0 - np.mean(fast_recalls, axis=0))
    advantage *= hardness[:, None]

    hub_ids = np.fromfile(args.hub_ids, dtype=np.int32)
    base = np.fromfile(args.base_prototypes, dtype=np.float32).reshape(len(hub_ids), -1)
    base = normalize(base)
    queries = normalize(read_fvecs(args.queries, query_count))
    id_to_local = {int(value): index for index, value in enumerate(hub_ids)}
    local = np.empty_like(candidate_ids)
    for rank in range(shortlist):
        try:
            local[:, rank] = [id_to_local[int(value)] for value in candidate_ids[:, rank]]
        except KeyError as error:
            raise ValueError(f"shortlist contains non-current hub: {error}") from error

    residual_sum = np.zeros_like(base, dtype=np.float64)
    absolute_weight = np.zeros(len(hub_ids), dtype=np.float64)
    occurrences = np.zeros(len(hub_ids), dtype=np.int64)
    for rank in range(shortlist):
        indices = local[:, rank]
        weights = advantage[:, rank].astype(np.float64)
        np.add.at(residual_sum, indices, queries * weights[:, None])
        np.add.at(absolute_weight, indices, np.abs(weights))
        np.add.at(occurrences, indices, 1)

    residual = residual_sum / np.maximum(absolute_weight[:, None], 1e-12)
    prototypes = normalize(base + args.alpha * residual.astype(np.float32)).astype(np.float32)

    args.output_dir.mkdir(parents=True, exist_ok=False)
    prototype_path = args.output_dir / "utility_residual_prototypes.bin"
    ids_path = args.output_dir / "hub_ids.bin"
    prototypes.tofile(prototype_path)
    hub_ids.tofile(ids_path)
    manifest = {
        "schema_version": 1,
        "method": "closed-form signed query-centered Recall/NDC utility residual prototype",
        "dataset": document["dataset"],
        "train_split": document["split"],
        "train_queries": query_count,
        "utility_search_Ls": [row["search_L"] for row in rows],
        "utility_top_k": 10,
        "shortlist": shortlist,
        "alpha": args.alpha,
        "cost_weight": args.cost_weight,
        "tail_weight": args.tail_weight,
        "hub_count": len(hub_ids),
        "hubs_observed": int((occurrences > 0).sum()),
        "min_occurrences": int(occurrences.min()),
        "max_occurrences": int(occurrences.max()),
        "mean_abs_advantage": float(np.mean(np.abs(advantage))),
        "sources": {
            "utility_json": str(args.utility_json), "utility_sha256": sha256(args.utility_json),
            "queries": str(args.queries), "queries_sha256": sha256(args.queries),
            "base_prototypes": str(args.base_prototypes),
            "base_prototypes_sha256": sha256(args.base_prototypes),
            "hub_ids": str(args.hub_ids), "hub_ids_sha256": sha256(args.hub_ids),
        },
        "outputs": {
            "prototypes": str(prototype_path), "prototypes_sha256": sha256(prototype_path),
            "hub_ids": str(ids_path), "hub_ids_sha256": sha256(ids_path),
        },
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
