#!/usr/bin/env python3
"""Build fast no-network and no-ACO entry-routing variants.

The outputs are isolated from the formal ACSG artifacts:

* prototype_uniform: normalized mean query direction for each existing hub.
* prototype_cost: the same prototype with a clipped sqrt(NDC) hardness weight.
* gt_basin_prototype: assign each train GT node to its nearest existing hub,
  then average the corresponding queries; this needs neither probe labels nor a
  neural network.
* qgt_cover: spherical query clusters represented by unique train-GT base nodes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import time
from pathlib import Path

import faiss
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "benches/datasets/settings.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_paths(dataset: str) -> tuple[dict, Path]:
    settings = json.loads(SETTINGS.read_text())
    config = settings["datasets"][dataset]
    root = Path(settings.get("root_dir", "./benches/datasets"))
    if not root.is_absolute():
        root = ROOT / str(root).removeprefix("./")
    return config, root / config["dataset_dir"]


def read_fvecs(path: Path) -> np.ndarray:
    size = path.stat().st_size
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    record = dim + 1
    if size % (record * 4):
        raise ValueError(f"invalid fvecs size: {path}")
    raw = np.fromfile(path, dtype=np.float32).reshape(-1, record)
    headers = raw[:, 0].view(np.int32)
    if not np.all(headers == dim):
        raise ValueError(f"inconsistent fvecs headers: {path}")
    return raw[:, 1:].copy()


def fvecs_memmap(path: Path) -> tuple[np.memmap, int]:
    size = path.stat().st_size
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    record_bytes = (dim + 1) * 4
    if size % record_bytes:
        raise ValueError(f"invalid fvecs size: {path}")
    rows = size // record_bytes
    raw = np.memmap(path, mode="r", dtype=np.float32, shape=(rows, dim + 1))
    return raw, dim


def read_ivecs(path: Path) -> np.ndarray:
    raw = np.fromfile(path, dtype=np.int32)
    if raw.size == 0:
        raise ValueError(f"empty ivecs: {path}")
    dim = int(raw[0])
    if raw.size % (dim + 1):
        raise ValueError(f"invalid ivecs size: {path}")
    rows = raw.reshape(-1, dim + 1)
    if not np.all(rows[:, 0] == dim):
        raise ValueError(f"inconsistent ivecs headers: {path}")
    return rows[:, 1:].copy()


def read_labels(path: Path) -> np.ndarray:
    with path.open("rb") as stream:
        header = np.fromfile(stream, dtype=np.int32, count=2)
        if header.size != 2:
            raise ValueError(f"invalid label header: {path}")
        count, dim = map(int, header)
        values = np.fromfile(stream, dtype=np.int32)
    if dim != 3 or values.size != count * dim:
        raise ValueError(f"invalid label payload: {path}")
    return values.reshape(count, dim)


def normalize(rows: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(rows, axis=1, keepdims=True)
    return rows / np.maximum(norms, 1e-12)


def build_prototypes(
    queries: np.ndarray,
    labels: np.ndarray,
    raw_hubs: np.ndarray,
    mode: str,
    prior_strength: float,
) -> tuple[np.ndarray, dict]:
    valid = labels[:, 2] >= 0
    selected = labels[valid]
    q = normalize(queries[selected[:, 0]].astype(np.float32))
    hub_index = selected[:, 1]
    costs = selected[:, 2].astype(np.float32)
    if mode == "uniform":
        weights = np.ones(len(selected), dtype=np.float32)
    elif mode == "cost":
        median = float(np.median(costs))
        weights = np.sqrt(costs / max(median, 1.0))
        weights = np.clip(weights, 0.5, 2.0).astype(np.float32)
    else:
        raise ValueError(mode)

    raw_n = normalize(raw_hubs.astype(np.float32))
    sums = prior_strength * raw_n
    counts = np.full(len(raw_hubs), prior_strength, dtype=np.float64)
    np.add.at(sums, hub_index, q * weights[:, None])
    np.add.at(counts, hub_index, weights.astype(np.float64))
    prototypes = normalize(sums).astype(np.float32)
    observed = np.bincount(hub_index, minlength=len(raw_hubs))
    return prototypes, {
        "mode": mode,
        "valid_labels": int(valid.sum()),
        "hub_count": len(raw_hubs),
        "hubs_with_labels": int((observed > 0).sum()),
        "min_labels_per_observed_hub": int(observed[observed > 0].min()),
        "max_labels_per_hub": int(observed.max()),
        "prior_strength": prior_strength,
    }


def build_gt_basin_prototypes(
    queries: np.ndarray,
    gt: np.ndarray,
    gt_vectors: np.ndarray,
    raw_hubs: np.ndarray,
    prior_strength: float,
) -> tuple[np.ndarray, dict]:
    if len(queries) != len(gt) or len(gt_vectors) != len(gt):
        raise ValueError("router query/GT/base-vector count mismatch")
    query_n = normalize(queries.astype(np.float32))
    target_n = normalize(gt_vectors.astype(np.float32))
    raw_n = normalize(raw_hubs.astype(np.float32))
    assignment = np.empty(len(queries), dtype=np.int32)
    batch_size = 4096
    for start in range(0, len(queries), batch_size):
        end = min(len(queries), start + batch_size)
        assignment[start:end] = np.argmax(target_n[start:end] @ raw_n.T, axis=1)

    sums = prior_strength * raw_n
    np.add.at(sums, assignment, query_n)
    prototypes = normalize(sums).astype(np.float32)
    counts = np.bincount(assignment, minlength=len(raw_hubs))
    return prototypes, {
        "method": "nearest-existing-hub-to-train-GT-vector then spherical query prototype",
        "train_queries": len(queries),
        "hub_count": len(raw_hubs),
        "hubs_with_assignments": int((counts > 0).sum()),
        "min_queries_per_observed_hub": int(counts[counts > 0].min()),
        "max_queries_per_hub": int(counts.max()),
        "prior_strength": prior_strength,
        "requires_aco_dpc": True,
        "requires_probe_labels": False,
        "requires_neural_training": False,
    }


def choose_unique_gt_hubs(
    queries: np.ndarray,
    gt: np.ndarray,
    target_hubs: int,
    seed: int,
    niter: int,
) -> tuple[np.ndarray, dict]:
    q = normalize(queries.astype(np.float32))
    target_hubs = min(target_hubs, len(q))
    kmeans = faiss.Kmeans(
        q.shape[1], target_hubs, niter=niter, nredo=1,
        verbose=False, spherical=True, seed=seed,
    )
    kmeans.train(q)
    _, assignment = kmeans.index.search(q, 1)
    assignment = assignment[:, 0]
    centroids = normalize(kmeans.centroids.astype(np.float32))

    used: set[int] = set()
    selected: list[int] = []
    empty_clusters = 0
    for cluster in range(target_hubs):
        members = np.flatnonzero(assignment == cluster)
        if not len(members):
            empty_clusters += 1
            continue
        similarity = q[members] @ centroids[cluster]
        members = members[np.argsort(-similarity)]
        picked = None
        for query_id in members:
            for node in gt[query_id]:
                candidate = int(node)
                if candidate not in used:
                    picked = candidate
                    break
            if picked is not None:
                break
        if picked is not None:
            used.add(picked)
            selected.append(picked)

    if len(selected) < target_hubs:
        for node in gt.ravel():
            candidate = int(node)
            if candidate not in used:
                used.add(candidate)
                selected.append(candidate)
                if len(selected) == target_hubs:
                    break
    if len(selected) != target_hubs:
        raise RuntimeError(f"could only choose {len(selected)}/{target_hubs} unique GT hubs")
    return np.asarray(sorted(selected), dtype=np.int32), {
        "method": "spherical-query-kmeans-representative-GT-cover",
        "target_hubs": target_hubs,
        "selected_hubs": len(selected),
        "empty_clusters": empty_clusters,
        "kmeans_iterations": niter,
        "seed": seed,
        "gt_candidates_per_query": int(gt.shape[1]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="webvid2_5m_light_v1")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--seed", type=int, default=20260828)
    parser.add_argument("--kmeans-iterations", type=int, default=25)
    parser.add_argument("--prior-strength", type=float, default=1.0)
    parser.add_argument(
        "--qgt-only", action="store_true",
        help="build only QGT-Cover and its closed-form prototype without reading ACO/DPC/label artifacts",
    )
    parser.add_argument(
        "--target-hubs", type=int,
        help="explicit hub budget; required with --qgt-only",
    )
    args = parser.parse_args()

    config, data_dir = dataset_paths(args.dataset)
    if config.get("metric", "l2").lower() not in {"ip", "inner_product", "cosine"}:
        raise ValueError("fast prototype currently requires an IP/cosine dataset")
    output = args.output_dir or ROOT / "fast_entry_variants" / args.dataset
    output.mkdir(parents=True, exist_ok=True)

    drl = ROOT / "drl" / f"{args.dataset}_results"
    labels_path = drl / "topo_aware_labels.ivecs"
    ids_path = drl / "transformed_hub_ids.bin"
    raw_hubs_path = drl / "raw_hubs.bin"
    router_query_path = data_dir / config["drl_train_query_path"]
    router_gt_path = data_dir / config["drl_train_gt_path"]
    aco_query_path = data_dir / config["acpg_query_path"]
    aco_gt_path = data_dir / config["acpg_gt_path"]
    base_path = data_dir / config["base_path"]

    started = time.perf_counter()
    if args.qgt_only:
        if args.target_hubs is None or args.target_hubs <= 0:
            raise ValueError("--qgt-only requires a positive --target-hubs")
        router_queries = read_fvecs(router_query_path)
        router_gt = read_ivecs(router_gt_path)
        aco_queries = read_fvecs(aco_query_path)
        aco_gt = read_ivecs(aco_gt_path)
        if len(router_queries) != len(router_gt):
            raise ValueError("router query/GT count mismatch")
        if len(aco_queries) != len(aco_gt):
            raise ValueError("ACO query/GT count mismatch")

        base_map, base_dim = fvecs_memmap(base_path)
        if base_dim != router_queries.shape[1] or base_dim != aco_queries.shape[1]:
            raise ValueError("query/base dimension mismatch")
        if router_gt[:, 0].max() >= len(base_map):
            raise ValueError("router GT/base contract mismatch")
        router_gt_vectors = np.asarray(base_map[router_gt[:, 0], 1:], dtype=np.float32)

        qgt_ids, qgt_details = choose_unique_gt_hubs(
            aco_queries, aco_gt, args.target_hubs, args.seed, args.kmeans_iterations
        )
        if qgt_ids.max() >= len(base_map):
            raise ValueError("QGT/base contract mismatch")
        headers = base_map[qgt_ids, 0].view(np.int32)
        if not np.all(headers == base_dim):
            raise ValueError("invalid base fvec headers at selected QGT ids")
        qgt_hubs = np.asarray(base_map[qgt_ids, 1:], dtype=np.float32)
        qgt_hubs_path = output / "qgt_cover_hubs.bin"
        qgt_ids_path = output / "qgt_cover_hub_ids.bin"
        qgt_hubs.tofile(qgt_hubs_path)
        qgt_ids.tofile(qgt_ids_path)

        prototype, prototype_details = build_gt_basin_prototypes(
            router_queries, router_gt, router_gt_vectors,
            qgt_hubs, args.prior_strength,
        )
        prototype_path = output / "qgt_gt_basin_prototype_hubs.bin"
        prototype.tofile(prototype_path)
        variants = {
            "qgt_cover": {
                **qgt_details,
                "hubs_file": str(qgt_hubs_path.relative_to(ROOT)),
                "ids_file": str(qgt_ids_path.relative_to(ROOT)),
                "hubs_sha256": sha256(qgt_hubs_path),
                "ids_sha256": sha256(qgt_ids_path),
            },
            "qgt_gt_basin_prototype": {
                **prototype_details,
                "method": "QGT-Cover hubs plus GT-basin spherical query prototypes",
                "hubs_file": str(prototype_path.relative_to(ROOT)),
                "ids_file": str(qgt_ids_path.relative_to(ROOT)),
                "hubs_sha256": sha256(prototype_path),
                "ids_sha256": sha256(qgt_ids_path),
                "requires_aco_dpc": False,
                "requires_probe_labels": False,
                "requires_neural_training": False,
            },
        }
        manifest = {
            "schema_version": 2,
            "dataset": args.dataset,
            "metric": config.get("metric"),
            "artifact_version": config.get("artifact_version"),
            "purpose": "QGT-only fast entry routing; no ACO/DPC/probe-label/neural artifacts",
            "qgt_only": True,
            "target_hubs": args.target_hubs,
            "sources": {
                "router_queries": str(router_query_path.relative_to(ROOT)),
                "router_queries_sha256": sha256(router_query_path),
                "router_gt": str(router_gt_path.relative_to(ROOT)),
                "router_gt_sha256": sha256(router_gt_path),
                "aco_queries": str(aco_query_path.relative_to(ROOT)),
                "aco_queries_sha256": sha256(aco_query_path),
                "aco_gt": str(aco_gt_path.relative_to(ROOT)),
                "aco_gt_sha256": sha256(aco_gt_path),
                "base": str(base_path.relative_to(ROOT)),
            },
            "variants": variants,
            "build_wall_seconds": time.perf_counter() - started,
        }
        manifest_path = output / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return

    labels = read_labels(labels_path)
    hub_ids = np.fromfile(ids_path, dtype=np.int32)
    router_queries = read_fvecs(router_query_path)
    raw_hubs = np.fromfile(raw_hubs_path, dtype=np.float32).reshape(len(hub_ids), -1)
    if raw_hubs.shape[1] != router_queries.shape[1]:
        raise ValueError("hub/query dimension mismatch")

    variants: dict[str, dict] = {}
    for mode in ("uniform", "cost"):
        prototype, details = build_prototypes(
            router_queries, labels, raw_hubs, mode, args.prior_strength
        )
        path = output / f"prototype_{mode}_hubs.bin"
        prototype.tofile(path)
        variants[f"prototype_{mode}"] = {
            **details,
            "hubs_file": str(path.relative_to(ROOT)),
            "hubs_sha256": sha256(path),
        }
    prototype_ids = output / "prototype_hub_ids.bin"
    hub_ids.tofile(prototype_ids)

    base_map, base_dim = fvecs_memmap(base_path)
    router_gt = read_ivecs(router_gt_path)
    if base_dim != router_queries.shape[1] or router_gt[:, 0].max() >= len(base_map):
        raise ValueError("router GT/base contract mismatch")
    router_gt_vectors = np.asarray(base_map[router_gt[:, 0], 1:], dtype=np.float32)
    gt_basin, gt_basin_details = build_gt_basin_prototypes(
        router_queries, router_gt, router_gt_vectors, raw_hubs, args.prior_strength
    )
    gt_basin_path = output / "gt_basin_prototype_hubs.bin"
    gt_basin.tofile(gt_basin_path)
    variants["gt_basin_prototype"] = {
        **gt_basin_details,
        "hubs_file": str(gt_basin_path.relative_to(ROOT)),
        "hubs_sha256": sha256(gt_basin_path),
    }

    aco_queries = read_fvecs(aco_query_path)
    aco_gt = read_ivecs(aco_gt_path)
    if len(aco_queries) != len(aco_gt):
        raise ValueError("ACO query/GT count mismatch")
    qgt_ids, qgt_details = choose_unique_gt_hubs(
        aco_queries, aco_gt, len(hub_ids), args.seed, args.kmeans_iterations
    )
    if base_dim != aco_queries.shape[1] or qgt_ids.max() >= len(base_map):
        raise ValueError("QGT/base contract mismatch")
    headers = base_map[qgt_ids, 0].view(np.int32)
    if not np.all(headers == base_dim):
        raise ValueError("invalid base fvec headers at selected QGT ids")
    qgt_hubs = np.asarray(base_map[qgt_ids, 1:], dtype=np.float32)
    qgt_hubs_path = output / "qgt_cover_hubs.bin"
    qgt_ids_path = output / "qgt_cover_hub_ids.bin"
    qgt_hubs.tofile(qgt_hubs_path)
    qgt_ids.tofile(qgt_ids_path)
    variants["qgt_cover"] = {
        **qgt_details,
        "hubs_file": str(qgt_hubs_path.relative_to(ROOT)),
        "ids_file": str(qgt_ids_path.relative_to(ROOT)),
        "hubs_sha256": sha256(qgt_hubs_path),
        "ids_sha256": sha256(qgt_ids_path),
    }
    qgt_gt_basin, qgt_gt_basin_details = build_gt_basin_prototypes(
        router_queries, router_gt, router_gt_vectors, qgt_hubs, args.prior_strength
    )
    qgt_gt_basin_path = output / "qgt_gt_basin_prototype_hubs.bin"
    qgt_gt_basin.tofile(qgt_gt_basin_path)
    variants["qgt_gt_basin_prototype"] = {
        **qgt_gt_basin_details,
        "method": "QGT-Cover hubs plus GT-basin spherical query prototypes",
        "hubs_file": str(qgt_gt_basin_path.relative_to(ROOT)),
        "ids_file": str(qgt_ids_path.relative_to(ROOT)),
        "hubs_sha256": sha256(qgt_gt_basin_path),
        "ids_sha256": sha256(qgt_ids_path),
        "requires_aco_dpc": False,
        "requires_probe_labels": False,
        "requires_neural_training": False,
    }

    manifest = {
        "schema_version": 1,
        "dataset": args.dataset,
        "metric": config.get("metric"),
        "artifact_version": config.get("artifact_version"),
        "purpose": "exploratory fast entry-routing alternatives; not formal results",
        "sources": {
            "router_queries": str(router_query_path.relative_to(ROOT)),
            "router_queries_sha256": sha256(router_query_path),
            "router_gt": str(router_gt_path.relative_to(ROOT)),
            "router_gt_sha256": sha256(router_gt_path),
            "labels": str(labels_path.relative_to(ROOT)),
            "labels_sha256": sha256(labels_path),
            "aco_queries": str(aco_query_path.relative_to(ROOT)),
            "aco_queries_sha256": sha256(aco_query_path),
            "aco_gt": str(aco_gt_path.relative_to(ROOT)),
            "aco_gt_sha256": sha256(aco_gt_path),
            "base": str(base_path.relative_to(ROOT)),
        },
        "shared_ids_file": str(prototype_ids.relative_to(ROOT)),
        "shared_ids_sha256": sha256(prototype_ids),
        "variants": variants,
        "build_wall_seconds": time.perf_counter() - started,
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
