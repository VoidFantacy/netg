#!/usr/bin/env python3
"""Prepare a leak-free training protocol for RoarGraph CLIP-WebVid-2.5M.

The base, public test queries, and public GT come from RoarGraph's Zenodo
record 11090378.  A fixed seed samples the complete 2.5M training-query file.
Exact duplicate vectors (including any public-test vectors) are excluded before
selecting 5K ACO, 30K Router, and 10K validation queries.  All search/GT
operations use inner product without additional normalization.
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
    convert_fbin_range,
    exact_ip_gt,
    read_fbin_header,
    read_fvecs,
    read_ivecs,
    row_hashes,
    sha256,
    write_ivecs,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "benches/datasets/WebVid2.5M_light_v1"
DEFAULT_SOURCE = DEFAULT_OUTPUT / "source"
ZENODO_RECORD = "https://zenodo.org/records/11090378"

SPLIT_COUNTS = {
    "aco_train": 5_000,
    "router_train": 30_000,
    "validation": 10_000,
}

SOURCE_META = {
    "clip.webvid.base.2.5M.fbin": {
        "bytes": 5_130_240_008,
        "md5": "0a3d70417a5536241950c9a5a4b45163",
    },
    "webvid.query.train.2.5M.fbin": {
        "bytes": 5_120_000_008,
        "md5": "cef416cd7c69cdae27e0517a7dca668d",
    },
    "webvid.query.10k.fbin": {
        "bytes": 20_480_008,
        "md5": "af1343dc16554d87c43326cf4024493d",
    },
    "webvid.gt.10k.ibin": {
        "bytes": 40_000_008,
        "md5": "d38e61f1d3ae8ed4e7b2dd821ec5ac6f",
    },
}


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as src:
        while chunk := src.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def convert_gt_topk(source: Path, output: Path, top_k: int) -> None:
    if output.exists():
        print(f"reuse {output}")
        return
    nq, source_k = read_fbin_header(source)
    expected = 8 + nq * source_k * 8
    if source.stat().st_size != expected:
        raise ValueError(
            f"RoarGraph GT size mismatch: got {source.stat().st_size}, expected {expected}"
        )
    if top_k > source_k:
        raise ValueError(f"requested top-{top_k} from top-{source_k} GT")
    ids = np.memmap(source, dtype="<i4", mode="r", offset=8, shape=(nq, source_k))
    write_ivecs(output, np.asarray(ids[:, :top_k]))


def fbin_vectors(source: Path, available_rows: int | None = None) -> np.ndarray:
    total, dim = read_fbin_header(source)
    rows_on_disk = (source.stat().st_size - 8) // (dim * 4)
    rows = rows_on_disk if available_rows is None else available_rows
    if rows > total or rows > rows_on_disk:
        raise ValueError(f"requested {rows} rows from {source}, only {rows_on_disk} available")
    return np.memmap(source, dtype="<f4", mode="r", offset=8, shape=(rows, dim))


def write_selected_fvecs(source: Path, output: Path, row_ids: list[int]) -> None:
    vectors = fbin_vectors(source)
    dim = vectors.shape[1]
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".part")
    with tmp.open("wb") as dst:
        for start in range(0, len(row_ids), 8192):
            ids = row_ids[start : start + 8192]
            batch = np.asarray(vectors[ids], dtype="<f4")
            records = np.empty((len(batch), dim + 1), dtype="<f4")
            records[:, 0].view("<i4")[:] = dim
            records[:, 1:] = batch
            records.tofile(dst)
    os.replace(tmp, output)


def select_disjoint_train_rows(
    train_source: Path, test_source: Path, seed: int
) -> tuple[dict[str, list[int]], dict[str, int]]:
    train = fbin_vectors(train_source)
    test = fbin_vectors(test_source)
    test_hashes = {
        hashlib.blake2b(np.asarray(row).tobytes(), digest_size=16).digest()
        for row in test
    }
    seen = set(test_hashes)
    selected: dict[str, list[int]] = {}
    skipped = {"duplicate_train": 0, "overlap_public_test": 0}
    rng = np.random.default_rng(seed)
    candidate_order = rng.permutation(len(train))
    cursor = 0
    for name, target_count in SPLIT_COUNTS.items():
        ids: list[int] = []
        while cursor < len(candidate_order) and len(ids) < target_count:
            source_row = int(candidate_order[cursor])
            row_hash = hashlib.blake2b(
                np.asarray(train[source_row]).tobytes(), digest_size=16
            ).digest()
            if row_hash in test_hashes:
                skipped["overlap_public_test"] += 1
            elif row_hash in seen:
                skipped["duplicate_train"] += 1
            else:
                ids.append(source_row)
                seen.add(row_hash)
            cursor += 1
        if len(ids) != target_count:
            raise ValueError(
                f"full train source has only {len(ids)}/{target_count} usable rows for {name}"
            )
        selected[name] = ids
    skipped["source_rows_consumed"] = cursor
    return selected, skipped


def add_fbin_to_flat_ip(index: faiss.IndexFlatIP, source: Path) -> tuple[int, int]:
    total, dim = read_fbin_header(source)
    expected = 8 + total * dim * 4
    if source.stat().st_size != expected:
        raise ValueError(f"base size mismatch: got {source.stat().st_size}, expected {expected}")
    vectors = np.memmap(source, dtype="<f4", mode="r", offset=8, shape=(total, dim))
    print(f"building exact-IP flat index with {total} base vectors, d={dim}")
    for start in range(0, total, 100_000):
        stop = min(start + 100_000, total)
        index.add(np.ascontiguousarray(vectors[start:stop]))
        print(f"  indexed {stop}/{total}", flush=True)
    return total, dim


def norm_summary(path: Path, max_rows: int = 20_000) -> dict[str, float]:
    vectors = read_fvecs(path)
    sample = np.asarray(vectors[:max_rows], dtype=np.float32)
    norms = np.linalg.norm(sample, axis=1)
    return {
        "sample_rows": int(len(sample)),
        "min": float(norms.min()),
        "max": float(norms.max()),
        "mean": float(norms.mean()),
        "std": float(norms.std()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gt-k", type=int, default=100)
    parser.add_argument("--threads", type=int, default=16)
    parser.add_argument("--split-seed", type=int, default=20260826)
    args = parser.parse_args()

    source = args.source_dir.resolve()
    output = args.output_dir.resolve()
    base_source = source / "clip.webvid.base.2.5M.fbin"
    train_source = source / "webvid.query.train.2.5M.fbin"
    test_source = source / "webvid.query.10k.fbin"
    official_gt_source = source / "webvid.gt.10k.ibin"
    for required in (base_source, train_source, test_source, official_gt_source):
        if not required.exists():
            raise FileNotFoundError(required)

    if read_fbin_header(base_source) != (2_505_000, 512):
        raise ValueError("unexpected WebVid base header")
    if read_fbin_header(train_source) != (2_500_000, 512):
        raise ValueError("unexpected WebVid train-query header")
    if train_source.stat().st_size != 8 + 2_500_000 * 512 * 4:
        raise ValueError("WebVid train-query source is incomplete")
    if read_fbin_header(test_source) != (10_000, 512):
        raise ValueError("unexpected WebVid public-query header")
    if read_fbin_header(official_gt_source) != (10_000, 500):
        raise ValueError("unexpected WebVid GT header")

    expected_base_md5 = SOURCE_META[base_source.name]["md5"]
    actual_base_md5 = md5(base_source)
    if actual_base_md5 != expected_base_md5:
        raise ValueError(f"base MD5 mismatch: {actual_base_md5} != {expected_base_md5}")
    for full_source in (train_source, test_source, official_gt_source):
        expected_md5 = SOURCE_META[full_source.name]["md5"]
        actual_md5 = md5(full_source)
        if actual_md5 != expected_md5:
            raise ValueError(f"{full_source.name} MD5 mismatch: {actual_md5} != {expected_md5}")

    base_fvecs = output / "base.webvid2_5m.fvecs"
    if not base_fvecs.exists():
        convert_fbin_range(base_source, base_fvecs, 0, 2_505_000)

    selected_rows, skipped_rows = select_disjoint_train_rows(
        train_source, test_source, args.split_seed
    )
    selection_path = output / f"split_source_indices.seed{args.split_seed}.json"
    selection_payload = {
        "source": "webvid.query.train.2.5M.fbin",
        "source_range": [0, 2_500_000],
        "sampling": "numpy.default_rng permutation without replacement",
        "seed": args.split_seed,
        "selected_source_rows": selected_rows,
        "skipped": skipped_rows,
    }
    selection_tmp = selection_path.with_suffix(".json.part")
    selection_tmp.write_text(json.dumps(selection_payload, indent=2, sort_keys=True) + "\n")
    os.replace(selection_tmp, selection_path)

    split_paths: dict[str, Path] = {}
    for name in SPLIT_COUNTS:
        path = output / f"query.{name}.seed{args.split_seed}.fvecs"
        write_selected_fvecs(train_source, path, selected_rows[name])
        split_paths[name] = path

    test_query = output / "query.test.public10K.fvecs"
    if not test_query.exists():
        convert_fbin_range(test_source, test_query, 0, 10_000)
    split_paths["test"] = test_query

    test_gt = output / "gt.test.public10K.ip.top100.ivecs"
    convert_gt_topk(official_gt_source, test_gt, args.gt_k)
    gt_paths = {"test": test_gt}

    faiss.omp_set_num_threads(args.threads)
    index = faiss.IndexFlatIP(512)
    add_fbin_to_flat_ip(index, base_source)
    for name in ("aco_train", "router_train", "validation"):
        gt_path = output / f"gt.{name}.seed{args.split_seed}.ip.ivecs"
        exact_ip_gt(index, split_paths[name], gt_path, args.gt_k)
        gt_paths[name] = gt_path

    sample_n = 32
    test_vectors = read_fvecs(test_query)
    _, actual_ids = index.search(
        np.ascontiguousarray(test_vectors[:sample_n], dtype=np.float32), args.gt_k
    )
    expected_ids = read_ivecs(test_gt)[:sample_n]
    validation_recall = float(
        np.mean(
            [
                len(set(actual) & set(expected)) / args.gt_k
                for actual, expected in zip(actual_ids, expected_ids)
            ]
        )
    )
    if validation_recall < 0.999999:
        raise ValueError(f"official GT/base/IP mismatch: sample recall={validation_recall}")

    hashes = {name: row_hashes(path) for name, path in split_paths.items()}
    overlap: dict[str, int] = {}
    names = list(split_paths)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            count = len(hashes[left] & hashes[right])
            overlap[f"{left}__{right}"] = count
            if count:
                raise ValueError(f"query leakage: {left} and {right} share {count} rows")

    files = [base_fvecs, selection_path, *split_paths.values(), *gt_paths.values()]
    manifest = {
        "schema_version": 1,
        "artifact_version": "roargraph-webvid2.5m-ip-v1",
        "created_unix": int(time.time()),
        "source_record": ZENODO_RECORD,
        "metric": "ip",
        "normalization": "source_unit_norm_no_additional",
        "base": {"source": base_source.name, "range": [0, 2_505_000]},
        "splits": {
            **{
                name: {
                    "source": "webvid.query.train.2.5M.fbin",
                    "selection_file": selection_path.name,
                    "selected_count": len(selected_rows[name]),
                    "first_source_row": selected_rows[name][0],
                    "last_source_row": selected_rows[name][-1],
                }
                for name in SPLIT_COUNTS
            },
            "test": {"source": test_source.name, "source_range": [0, 10_000]},
        },
        "ground_truth": {
            "k": args.gt_k,
            "metric": "exact_inner_product",
            "test_source_k": 500,
        },
        "official_gt_validation": {
            "sample_queries": sample_n,
            "set_recall_at_100": validation_recall,
        },
        "query_overlap_counts": overlap,
        "split_seed": args.split_seed,
        "dedup_selection": skipped_rows,
        "norm_samples": {
            "base": norm_summary(base_fvecs),
            **{name: norm_summary(path) for name, path in split_paths.items()},
        },
        "official_sources": SOURCE_META,
        "local_sources": {
            str(path.relative_to(output)): {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
                "complete_official_file": True,
            }
            for path in (base_source, train_source, test_source, official_gt_source)
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
