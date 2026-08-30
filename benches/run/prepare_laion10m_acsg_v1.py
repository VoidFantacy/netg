#!/usr/bin/env python3
"""Prepare the leak-free ACSG protocol for RoarGraph LAION-10M.

The base follows RoarGraph exactly: fp16 LAION-400M image-embedding shards
0..7,9,10, cast to float32, row-normalized, and concatenated in that order. ACSG uses only
45K independently selected historical text queries from official shard 0;
the public 10K query/GT pair remains held out.  Search and GT use raw inner
product after explicit row normalization, matching RoarGraph's public GT.
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

from prepare_yandex_official10m_ip import (
    exact_ip_gt,
    read_fbin_header,
    read_fvecs,
    read_ivecs,
    row_hashes,
    sha256,
    write_ivecs,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "benches/datasets/LAION10M_acsg_v1"
DEFAULT_SOURCE = DEFAULT_OUTPUT / "source"
SHARDS = (0, 1, 2, 3, 4, 5, 6, 7, 9, 10)
ROWS_PER_SHARD = 1_000_448
DIM = 512
SPLIT_COUNTS = {"aco_train": 5_000, "router_train": 30_000, "validation": 10_000}
ZENODO_RECORD = "https://zenodo.org/records/11090378"
LAION_SOURCE = "https://deploy.laion.ai/8f83b608504d46bb81708ec86e912220/embeddings"


def validate_npy(path: Path) -> np.ndarray:
    values = np.load(path, mmap_mode="r", allow_pickle=False)
    if values.shape != (ROWS_PER_SHARD, DIM) or values.dtype != np.dtype("<f2"):
        raise ValueError(f"unexpected LAION shard contract: {path}: {values.shape}/{values.dtype}")
    if path.stat().st_size != 1_024_458_880:
        raise ValueError(f"unexpected LAION shard size: {path}: {path.stat().st_size}")
    return values


def write_base_fvecs(source: Path, output: Path) -> None:
    if output.exists():
        print(f"reuse {output}")
        return
    tmp = output.with_suffix(output.suffix + ".part")
    with tmp.open("wb") as dst:
        for shard in SHARDS:
            values = validate_npy(source / f"img_emb_{shard}.npy")
            for start in range(0, len(values), 8192):
                batch = np.asarray(values[start : start + 8192], dtype="<f4")
                norms = np.linalg.norm(batch, axis=1, keepdims=True)
                if np.any(norms == 0):
                    raise ValueError(f"zero-norm row in image shard {shard}")
                batch /= norms
                records = np.empty((len(batch), DIM + 1), dtype="<f4")
                records[:, 0].view("<i4")[:] = DIM
                records[:, 1:] = batch
                records.tofile(dst)
            print(f"converted image shard {shard}", flush=True)
    os.replace(tmp, output)


def fbin_vectors(path: Path) -> np.ndarray:
    rows, dim = read_fbin_header(path)
    if path.stat().st_size != 8 + rows * dim * 4:
        raise ValueError(f"truncated fbin: {path}")
    return np.memmap(path, dtype="<f4", mode="r", offset=8, shape=(rows, dim))


def write_rows_as_fvecs(values: np.ndarray, output: Path, row_ids: list[int] | None = None) -> None:
    if output.exists():
        print(f"reuse {output}")
        return
    tmp = output.with_suffix(output.suffix + ".part")
    total = len(values) if row_ids is None else len(row_ids)
    with tmp.open("wb") as dst:
        for start in range(0, total, 8192):
            if row_ids is None:
                batch = np.array(values[start : start + 8192], dtype="<f4", copy=True)
            else:
                batch = np.array(values[row_ids[start : start + 8192]], dtype="<f4", copy=True)
            norms = np.linalg.norm(batch, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError(f"zero-norm row while writing {output}")
            batch /= norms
            records = np.empty((len(batch), DIM + 1), dtype="<f4")
            records[:, 0].view("<i4")[:] = DIM
            records[:, 1:] = batch
            records.tofile(dst)
    os.replace(tmp, output)


def select_rows(train: np.ndarray, test: np.ndarray, seed: int) -> tuple[dict[str, list[int]], dict[str, int]]:
    test_hashes = {
        hashlib.blake2b(np.asarray(row, dtype="<f4").tobytes(), digest_size=16).digest()
        for row in test
    }
    seen = set(test_hashes)
    selected: dict[str, list[int]] = {}
    skipped = {"duplicate_train": 0, "overlap_public_test": 0}
    order = np.random.default_rng(seed).permutation(len(train))
    cursor = 0
    for name, count in SPLIT_COUNTS.items():
        ids: list[int] = []
        while cursor < len(order) and len(ids) < count:
            row_id = int(order[cursor])
            digest = hashlib.blake2b(
                np.asarray(train[row_id], dtype="<f4").tobytes(), digest_size=16
            ).digest()
            if digest in test_hashes:
                skipped["overlap_public_test"] += 1
            elif digest in seen:
                skipped["duplicate_train"] += 1
            else:
                ids.append(row_id)
                seen.add(digest)
            cursor += 1
        if len(ids) != count:
            raise ValueError(f"only {len(ids)}/{count} usable rows for {name}")
        selected[name] = ids
    skipped["source_rows_consumed"] = cursor
    return selected, skipped


def convert_official_gt_top100(source: Path, output: Path) -> None:
    if output.exists():
        print(f"reuse {output}")
        return
    nq, k = read_fbin_header(source)
    # RoarGraph's GT container stores all int32 IDs first and then the same
    # number of float32 distances (DiskANN truthset format).
    if (nq, k) != (10_000, 500) or source.stat().st_size != 8 + nq * k * 8:
        raise ValueError(f"unexpected official LAION GT: {(nq, k)}/{source.stat().st_size}")
    ids = np.memmap(source, dtype="<i4", mode="r", offset=8, shape=(nq, k))
    write_ivecs(output, np.asarray(ids[:, :100]))


def norm_summary(path: Path, max_rows: int = 20_000) -> dict[str, float | int]:
    sample = np.asarray(read_fvecs(path)[:max_rows], dtype=np.float32)
    norms = np.linalg.norm(sample, axis=1)
    return {
        "sample_rows": int(len(sample)), "min": float(norms.min()),
        "max": float(norms.max()), "mean": float(norms.mean()), "std": float(norms.std()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--split-seed", type=int, default=20260830)
    parser.add_argument("--threads", type=int, default=16)
    args = parser.parse_args()
    source, output = args.source_dir.resolve(), args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    for shard in SHARDS:
        validate_npy(source / f"img_emb_{shard}.npy")
    train_source = validate_npy(source / "text_emb_0.npy")
    test_source_path = source / "laion.query.10k.fbin"
    official_gt_path = source / "laion.gt.10k.ibin"
    if read_fbin_header(test_source_path) != (10_000, DIM):
        raise ValueError("unexpected official LAION query header")
    if hashlib.md5(test_source_path.read_bytes()).hexdigest() != "af1343dc16554d87c43326cf4024493d":
        raise ValueError("official LAION query MD5 mismatch")
    if hashlib.md5(official_gt_path.read_bytes()).hexdigest() != "d76a89a9e05ce4a18a5ebdaa3e159796":
        raise ValueError("official LAION GT MD5 mismatch")

    base_path = output / "base.roargraph_laion10m.unit.fvecs"
    write_base_fvecs(source, base_path)
    expected_rows = ROWS_PER_SHARD * len(SHARDS)
    if read_fvecs(base_path).shape != (expected_rows, DIM):
        raise ValueError("converted base shape mismatch")

    test_values = fbin_vectors(test_source_path)
    selected, skipped = select_rows(train_source, test_values, args.split_seed)
    selection_path = output / f"split_source_indices.seed{args.split_seed}.json"
    selection = {
        "source": "text_emb_0.npy", "seed": args.split_seed,
        "sampling": "numpy.default_rng permutation without replacement after exact-row dedup",
        "selected_source_rows": selected, "skipped": skipped,
    }
    tmp = selection_path.with_suffix(".json.part")
    tmp.write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, selection_path)

    split_paths: dict[str, Path] = {}
    for name, ids in selected.items():
        path = output / f"query.{name}.seed{args.split_seed}.unit.fvecs"
        write_rows_as_fvecs(train_source, path, ids)
        split_paths[name] = path
    test_path = output / "query.test.public10K.unit.fvecs"
    write_rows_as_fvecs(test_values, test_path)
    split_paths["test"] = test_path

    test_gt = output / "gt.test.public10K.unit_ip.top100.ivecs"
    convert_official_gt_top100(official_gt_path, test_gt)
    gt_paths = {"test": test_gt}

    faiss.omp_set_num_threads(args.threads)
    base = read_fvecs(base_path)
    index = faiss.IndexFlatIP(DIM)
    print(f"building exact-IP flat index with {len(base)} base vectors", flush=True)
    for start in range(0, len(base), 100_000):
        index.add(np.ascontiguousarray(base[start : start + 100_000], dtype=np.float32))
        print(f"  indexed {min(start + 100_000, len(base))}/{len(base)}", flush=True)
    for name in ("aco_train", "router_train", "validation"):
        gt = output / f"gt.{name}.seed{args.split_seed}.unit_ip.ivecs"
        exact_ip_gt(index, split_paths[name], gt, 100)
        gt_paths[name] = gt

    sample_n = 32
    _, actual = index.search(np.ascontiguousarray(read_fvecs(test_path)[:sample_n]), 100)
    expected = read_ivecs(test_gt)[:sample_n]
    official_recall = float(np.mean([
        len(set(a) & set(e)) / 100 for a, e in zip(actual, expected)
    ]))
    if official_recall < 0.999999:
        raise ValueError(f"official GT/base/IP mismatch: sample recall={official_recall}")

    hashes = {name: row_hashes(path) for name, path in split_paths.items()}
    overlap: dict[str, int] = {}
    names = list(split_paths)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            count = len(hashes[left] & hashes[right])
            overlap[f"{left}__{right}"] = count
            if count:
                raise ValueError(f"query leakage: {left}/{right}: {count}")

    files = [base_path, selection_path, *split_paths.values(), *gt_paths.values()]
    manifest = {
        "schema_version": 1,
        "artifact_version": "roargraph-laion10m-unit-ip-acsg-v1",
        "created_unix": int(time.time()),
        "metric": "ip", "normalization": "explicit_l2_unit_all_base_and_queries",
        "base": {
            "source": "LAION-400M fp16 image embeddings",
            "shards_in_order": list(SHARDS), "rows_per_shard": ROWS_PER_SHARD,
            "rows": expected_rows, "dimension": DIM,
        },
        "splits": {
            **{name: {"source": "text_emb_0.npy", "selected_count": len(ids)} for name, ids in selected.items()},
            "test": {"source": "laion.query.10k.fbin", "source_range": [0, 10_000]},
        },
        "ground_truth": {"k": 100, "metric": "exact_inner_product", "test_source_k": 500},
        "official_gt_validation": {"sample_queries": sample_n, "set_recall_at_100": official_recall},
        "query_overlap_counts": overlap, "split_seed": args.split_seed,
        "dedup_selection": skipped,
        "norm_samples": {name: norm_summary(path) for name, path in {"base": base_path, **split_paths}.items()},
        "provenance": {"roargraph_record": ZENODO_RECORD, "laion_embedding_source": LAION_SOURCE},
        "sources": {
            str(path.relative_to(output)): {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(source.iterdir()) if path.is_file()
        },
        "files": {
            str(path.relative_to(output)): {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        },
    }
    manifest_path = output / "manifest.json"
    tmp = manifest_path.with_suffix(".json.part")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, manifest_path)
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
