#!/usr/bin/env python3
"""Build two residual spherical modes per frozen Fast GT basin and emit train routes."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


FIT_START = 10000
FIT_END = 30000
MIN_MODE_SAMPLES = 8
MODE_COUNT = 2
SHORTLIST = 32
TOP_M = 3


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(rows: np.ndarray) -> np.ndarray:
    return rows / np.maximum(np.linalg.norm(rows, axis=-1, keepdims=True), 1e-12)


def read_fvecs(path: Path) -> np.ndarray:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    raw = np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1)
    if not np.all(raw[:, 0].copy().view(np.int32) == dim):
        raise ValueError(f"invalid fvec headers: {path}")
    return np.asarray(raw[:, 1:], dtype=np.float32).copy()


def read_ivecs(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.int32)
    width = int(raw[0])
    rows = raw.reshape(-1, width + 1)
    if not np.all(rows[:, 0] == width):
        raise ValueError(f"invalid ivec headers: {path}")
    return rows[:, 1:]


def fvecs_memmap(path: Path) -> tuple[np.memmap, int]:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    size = path.stat().st_size
    if size % ((dim + 1) * 4):
        raise ValueError(f"invalid base fvecs: {path}")
    return np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1), dim


def spherical_two_means(rows: np.ndarray, primary: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if len(rows) < MIN_MODE_SAMPLES:
        return np.stack((primary, primary)), np.asarray((0.5, 0.5), dtype=np.float32)
    seed0 = int(np.argmax(rows @ primary))
    seed1 = int(np.argmin(rows @ rows[seed0]))
    centers = np.stack((rows[seed0], rows[seed1])).copy()
    assignment = np.full(len(rows), -1, dtype=np.int32)
    for _ in range(20):
        updated = np.argmax(rows @ centers.T, axis=1).astype(np.int32)
        if np.array_equal(updated, assignment):
            break
        assignment = updated
        for mode in range(MODE_COUNT):
            members = rows[assignment == mode]
            if not len(members):
                assignment[int(np.argmin(rows @ centers[1 - mode]))] = mode
                members = rows[assignment == mode]
            centers[mode] = normalize(members.mean(axis=0, keepdims=True))[0]
    counts = np.bincount(assignment, minlength=MODE_COUNT).astype(np.float32)
    return centers.astype(np.float32), counts / counts.sum()


def candidate_matrix(utility: dict) -> np.ndarray:
    if utility.get("split") != "drl_train" or utility.get("utility_shortlist") != SHORTLIST:
        raise ValueError("requires frozen top-32 drl_train sparse utility")
    matrices = []
    for operating_point in utility["results"]:
        matrix = np.asarray([row["candidate_entry_ids"] for row in operating_point["queries"]], dtype=np.int32)
        matrices.append(matrix)
    if not matrices or any(not np.array_equal(matrices[0], matrix) for matrix in matrices[1:]):
        raise ValueError("candidate shortlist differs across operating points")
    if matrices[0].shape != (10000, SHORTLIST):
        raise ValueError(f"unexpected shortlist shape: {matrices[0].shape}")
    return matrices[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--gt", type=Path, required=True)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--hub-ids", type=Path, required=True)
    parser.add_argument("--raw-hubs", type=Path, required=True)
    parser.add_argument("--primary-prototypes", type=Path, required=True)
    parser.add_argument("--utility-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError(args.output_dir)

    queries = normalize(read_fvecs(args.queries))
    gt = read_ivecs(args.gt)
    if len(queries) < FIT_END or len(gt) < FIT_END:
        raise ValueError("need at least 30K independent train queries and GT")
    hub_ids = np.fromfile(args.hub_ids, dtype=np.int32)
    raw_hubs = normalize(np.fromfile(args.raw_hubs, dtype=np.float32).reshape(len(hub_ids), -1))
    primary = normalize(np.fromfile(args.primary_prototypes, dtype=np.float32).reshape(len(hub_ids), -1))
    if queries.shape[1] != raw_hubs.shape[1] or primary.shape != raw_hubs.shape:
        raise ValueError("query/hub/prototype dimension mismatch")
    base, base_dim = fvecs_memmap(args.base)
    if base_dim != queries.shape[1]:
        raise ValueError("base/query dimension mismatch")
    gt_ids = gt[FIT_START:FIT_END, 0]
    if gt_ids.min() < 0 or gt_ids.max() >= len(base):
        raise ValueError("GT ID outside base")
    headers = base[gt_ids, 0].copy().view(np.int32)
    if not np.all(headers == base_dim):
        raise ValueError("invalid selected base headers")
    targets = normalize(np.asarray(base[gt_ids, 1:], dtype=np.float32))

    assignment = np.empty(FIT_END - FIT_START, dtype=np.int32)
    for start in range(0, len(targets), 2048):
        end = min(start + 2048, len(targets))
        assignment[start:end] = np.argmax(targets[start:end] @ raw_hubs.T, axis=1)

    modes = np.empty((len(hub_ids), MODE_COUNT, queries.shape[1]), dtype=np.float32)
    weights = np.empty((len(hub_ids), MODE_COUNT), dtype=np.float32)
    counts = np.bincount(assignment, minlength=len(hub_ids))
    fit_queries = queries[FIT_START:FIT_END]
    for hub in range(len(hub_ids)):
        modes[hub], weights[hub] = spherical_two_means(fit_queries[assignment == hub], primary[hub])

    utility = json.loads(args.utility_json.read_text())
    candidates = candidate_matrix(utility)
    id_to_local = {int(entry): local for local, entry in enumerate(hub_ids)}
    try:
        local_candidates = np.asarray([[id_to_local[int(entry)] for entry in row] for row in candidates], dtype=np.int32)
    except KeyError as error:
        raise ValueError(f"utility shortlist contains a non-frozen hub: {error}") from error
    route_queries = queries[:len(candidates)]
    routes = np.empty((len(candidates), TOP_M), dtype=np.int32)
    baseline_routes = candidates[:, :TOP_M]
    for start in range(0, len(candidates), 512):
        end = min(start + 512, len(candidates))
        q = route_queries[start:end]
        local = local_candidates[start:end]
        primary_score = np.einsum("bd,bkd->bk", q, primary[local])
        mode_score = np.einsum("bd,bkmd->bkm", q, modes[local])
        mode_score += np.log(np.maximum(weights[local], 1e-12)) / queries.shape[1]
        score = np.maximum(primary_score, mode_score.max(axis=2))
        order = np.argsort(-score, axis=1, kind="stable")[:, :TOP_M]
        routes[start:end] = np.take_along_axis(candidates[start:end], order, axis=1)

    args.output_dir.mkdir(parents=True)
    modes_path = args.output_dir / "target_basin_modes.npz"
    np.savez(modes_path, hub_ids=hub_ids, primary=primary, modes=modes, weights=weights, counts=counts)
    routes_path = args.output_dir / "routes_train10k_top3.i32"
    routes.tofile(routes_path)
    report = {
        "schema_version": 1, "status": "complete", "method": "Fast-anchored residual target-basin modes",
        "heldout_accessed": False, "validation_accessed": False,
        "fit_rows": [FIT_START, FIT_END], "route_rows": [0, len(routes)],
        "hub_count": len(hub_ids), "mode_count": MODE_COUNT, "min_mode_samples": MIN_MODE_SAMPLES,
        "hubs_with_two_modes": int((counts >= MIN_MODE_SAMPLES).sum()),
        "basin_count_min_mean_max": [int(counts.min()), float(counts.mean()), int(counts.max())],
        "route_top1_changed_fraction": float((routes[:, 0] != baseline_routes[:, 0]).mean()),
        "route_top3_order_changed_fraction": float(np.any(routes != baseline_routes, axis=1).mean()),
        "route_top3_set_changed_fraction": float(np.mean([
            set(map(int, routes[i])) != set(map(int, baseline_routes[i])) for i in range(len(routes))])),
        "online_extra_dot_products": SHORTLIST * MODE_COUNT,
        "online_graph_probes": 0,
        "sources": {name: {"path": str(path), "sha256": sha256(path)} for name, path in {
            "queries": args.queries, "gt": args.gt, "base": args.base, "hub_ids": args.hub_ids,
            "raw_hubs": args.raw_hubs, "primary_prototypes": args.primary_prototypes,
            "utility_json": args.utility_json}.items()},
        "artifacts": {"modes": {"path": str(modes_path), "sha256": sha256(modes_path), "bytes": modes_path.stat().st_size},
                      "routes": {"path": str(routes_path), "sha256": sha256(routes_path), "bytes": routes_path.stat().st_size}},
    }
    (args.output_dir / "build_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
