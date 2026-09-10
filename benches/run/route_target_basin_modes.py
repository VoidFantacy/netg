#!/usr/bin/env python3
"""Route a frozen validation split with residual target-basin modes; labels are never read."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


SHORTLIST = 32
TOP_M = 3


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
        raise ValueError(f"invalid query fvecs: {path}")
    rows = np.asarray(raw[:count, 1:], dtype=np.float32).copy()
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--shortlist-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)

    document = json.loads(args.shortlist_json.read_text())
    if document.get("split") != "validation" or document.get("utility_shortlist") != SHORTLIST:
        raise ValueError("route-only stage accepts validation top-32 shortlist, never held-out")
    operating_points = document.get("results", [])
    if not operating_points:
        raise ValueError("empty shortlist artifact")
    candidates = np.asarray(
        [row["candidate_entry_ids"] for row in operating_points[0]["queries"]], dtype=np.int32)
    if candidates.shape != (document["num_queries"], SHORTLIST):
        raise ValueError("candidate shortlist shape mismatch")
    for point in operating_points[1:]:
        current = np.asarray([row["candidate_entry_ids"] for row in point["queries"]], dtype=np.int32)
        if not np.array_equal(current, candidates):
            raise ValueError("candidate shortlist differs across operating points")

    model = np.load(args.model)
    hub_ids = model["hub_ids"]
    primary = model["primary"]
    modes = model["modes"]
    weights = model["weights"]
    queries = read_fvecs(args.queries, len(candidates))
    if primary.shape != (len(hub_ids), queries.shape[1]) or modes.shape != (len(hub_ids), 2, queries.shape[1]):
        raise ValueError("model/query shape mismatch")
    id_to_local = {int(entry): local for local, entry in enumerate(hub_ids)}
    try:
        local_candidates = np.asarray([[id_to_local[int(entry)] for entry in row] for row in candidates], dtype=np.int32)
    except KeyError as error:
        raise ValueError(f"shortlist contains non-model hub: {error}") from error

    routes = np.empty((len(candidates), TOP_M), dtype=np.int32)
    for start in range(0, len(candidates), 512):
        end = min(start + 512, len(candidates))
        q = queries[start:end]
        local = local_candidates[start:end]
        primary_score = np.einsum("bd,bkd->bk", q, primary[local])
        mode_score = np.einsum("bd,bkmd->bkm", q, modes[local])
        mode_score += np.log(np.maximum(weights[local], 1e-12)) / queries.shape[1]
        score = np.maximum(primary_score, mode_score.max(axis=2))
        order = np.argsort(-score, axis=1, kind="stable")[:, :TOP_M]
        routes[start:end] = np.take_along_axis(candidates[start:end], order, axis=1)

    args.output_dir.mkdir(parents=True)
    route_path = args.output_dir / "routes_validation10k_top3.i32"
    routes.tofile(route_path)
    baseline = candidates[:, :TOP_M]
    report = {
        "schema_version": 1, "status": "complete", "split": "validation",
        "method_frozen": True, "heldout_accessed": False,
        "labels_used_for_routing": False, "online_graph_probes": 0,
        "route_top1_changed_fraction": float((routes[:, 0] != baseline[:, 0]).mean()),
        "route_top3_order_changed_fraction": float(np.any(routes != baseline, axis=1).mean()),
        "route_top3_set_changed_fraction": float(np.mean([
            set(map(int, routes[i])) != set(map(int, baseline[i])) for i in range(len(routes))])),
        "sources": {"model": {"path": str(args.model), "sha256": sha256(args.model)},
                    "queries": {"path": str(args.queries), "sha256": sha256(args.queries)},
                    "shortlist": {"path": str(args.shortlist_json), "sha256": sha256(args.shortlist_json)}},
        "route": {"path": str(route_path), "sha256": sha256(route_path), "bytes": route_path.stat().st_size},
    }
    (args.output_dir / "route_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
