#!/usr/bin/env python3
"""Prepare the leak-free, official BigANN Yandex T2I 10M/IP protocol.

The source base is the first 10M records of ``base.1B.fbin``.  Training
queries are disjoint contiguous ranges from ``query.learn.50M.fbin`` and the
complete public 100K query set is held out for final evaluation.
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
DEFAULT_SOURCE = ROOT / "benches/datasets/YandexT2I_official10M_ip_v1/source"
DEFAULT_OUTPUT = ROOT / "benches/datasets/YandexT2I_official10M_ip_v1"
PUBLIC_QUERY_SOURCE = ROOT / "benches/datasets/YandexT2I/query.public.100K.fbin"

SPLITS = {
    "aco_train": (0, 5_000),
    "router_train": (5_000, 35_000),
    "validation": (35_000, 45_000),
}


def read_fbin_header(path: Path) -> tuple[int, int]:
    with path.open("rb") as src:
        raw = src.read(8)
    if len(raw) != 8:
        raise ValueError(f"short fbin header: {path}")
    return struct.unpack("<II", raw)


def convert_fbin_range(path: Path, output: Path, start: int, stop: int) -> None:
    count = stop - start
    total, dim = read_fbin_header(path)
    if start < 0 or stop > total or count <= 0:
        raise ValueError(f"invalid range [{start}, {stop}) for {path} with {total} rows")
    expected = 8 + total * dim * 4
    if path.stat().st_size < 8 + stop * dim * 4:
        raise ValueError(f"truncated fbin source: {path}")
    if path.stat().st_size != expected:
        print(f"note: {path.name} is a deliberate prefix download ({path.stat().st_size} bytes)")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".part")
    with path.open("rb") as src, tmp.open("wb") as dst:
        src.seek(8 + start * dim * 4)
        remaining = count
        while remaining:
            rows = min(8192, remaining)
            payload = src.read(rows * dim * 4)
            if len(payload) != rows * dim * 4:
                raise ValueError(f"short payload while reading {path}")
            vectors = np.frombuffer(payload, dtype="<f4").reshape(rows, dim)
            records = np.empty((rows, dim + 1), dtype="<f4")
            records[:, 0].view("<i4")[:] = dim
            records[:, 1:] = vectors
            records.tofile(dst)
            remaining -= rows
    os.replace(tmp, output)


def convert_official_gt(path: Path, output: Path) -> None:
    nq, k = read_fbin_header(path)
    expected = 8 + nq * k * 8
    if path.stat().st_size != expected:
        raise ValueError(f"official GT size mismatch: got {path.stat().st_size}, expected {expected}")
    ids = np.memmap(path, dtype="<i4", mode="r", offset=8, shape=(nq, k))
    write_ivecs(output, np.asarray(ids))


def write_ivecs(path: Path, values: np.ndarray) -> None:
    values = np.asarray(values, dtype="<i4", order="C")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    header = np.asarray([values.shape[1]], dtype="<i4")
    with tmp.open("wb") as dst:
        for batch_start in range(0, len(values), 8192):
            batch = values[batch_start : batch_start + 8192]
            records = np.empty((len(batch), values.shape[1] + 1), dtype="<i4")
            records[:, 0] = header[0]
            records[:, 1:] = batch
            records.tofile(dst)
    os.replace(tmp, path)


def read_fvecs(path: Path) -> np.ndarray:
    dim = int(np.fromfile(path, dtype="<i4", count=1)[0])
    record = dim + 1
    raw = np.memmap(path, dtype="<f4", mode="r")
    if raw.size % record:
        raise ValueError(f"invalid fvecs record size: {path}")
    headers = raw.view("<i4").reshape(-1, record)[:, 0]
    if not np.all(headers == dim):
        raise ValueError(f"inconsistent fvecs dimensions: {path}")
    return raw.reshape(-1, record)[:, 1:]


def read_ivecs(path: Path) -> np.ndarray:
    k = int(np.fromfile(path, dtype="<i4", count=1)[0])
    raw = np.memmap(path, dtype="<i4", mode="r")
    if raw.size % (k + 1):
        raise ValueError(f"invalid ivecs record size: {path}")
    records = raw.reshape(-1, k + 1)
    if not np.all(records[:, 0] == k):
        raise ValueError(f"inconsistent ivecs dimensions: {path}")
    return records[:, 1:]


def exact_ip_gt(index: faiss.IndexFlatIP, query_path: Path, output: Path, k: int) -> None:
    if output.exists():
        print(f"reuse {output}")
        return
    queries = read_fvecs(query_path)
    print(f"exact IP GT: {len(queries)} x {index.ntotal}, d={index.d}, k={k}")
    all_ids = np.empty((len(queries), k), dtype=np.int32)
    for start in range(0, len(queries), 256):
        stop = min(start + 256, len(queries))
        _, ids = index.search(np.asarray(queries[start:stop], dtype=np.float32), k)
        all_ids[start:stop] = ids
        print(f"  {stop}/{len(queries)}", flush=True)
    write_ivecs(output, all_ids)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        while chunk := src.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def row_hashes(path: Path) -> set[bytes]:
    vectors = read_fvecs(path)
    return {hashlib.blake2b(np.asarray(row).tobytes(), digest_size=16).digest() for row in vectors}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--gt-k", type=int, default=100)
    args = parser.parse_args()

    source = args.source_dir.resolve()
    output = args.output_dir.resolve()
    base_source = source / "base.1B.fbin.crop_nb_10000000"
    learn_source = source / "query.learn.first45K.fbin"
    official_gt = source / "text2image-10M.gt"
    for required in (base_source, learn_source, official_gt, PUBLIC_QUERY_SOURCE):
        if not required.exists():
            raise FileNotFoundError(required)

    base_fvecs = output / "base.official_first10M.fvecs"
    if not base_fvecs.exists():
        convert_fbin_range(base_source, base_fvecs, 0, 10_000_000)

    split_paths: dict[str, Path] = {}
    for name, (start, stop) in SPLITS.items():
        path = output / f"query.{name}.fvecs"
        if not path.exists():
            convert_fbin_range(learn_source, path, start, stop)
        split_paths[name] = path

    test_query = output / "query.test.public100K.fvecs"
    if not test_query.exists():
        convert_fbin_range(PUBLIC_QUERY_SOURCE, test_query, 0, 100_000)
    split_paths["test"] = test_query

    test_gt = output / "gt.test.public100K.ip.ivecs"
    if not test_gt.exists():
        convert_official_gt(official_gt, test_gt)

    gt_paths = {"test": test_gt}
    missing_train_gt = [
        name for name in ("aco_train", "router_train", "validation")
        if not (output / f"gt.{name}.ip.ivecs").exists()
    ]
    index = None
    if missing_train_gt:
        base = read_fvecs(base_fvecs)
        index = faiss.IndexFlatIP(base.shape[1])
        print(f"building exact-IP flat index with {len(base)} base vectors")
        index.add(np.ascontiguousarray(base, dtype=np.float32))
    for name in ("aco_train", "router_train", "validation"):
        gt_path = output / f"gt.{name}.ip.ivecs"
        if index is not None:
            exact_ip_gt(index, split_paths[name], gt_path, args.gt_k)
        gt_paths[name] = gt_path

    if index is None:
        base = read_fvecs(base_fvecs)
        index = faiss.IndexFlatIP(base.shape[1])
        index.add(np.ascontiguousarray(base, dtype=np.float32))
    sample_n = 64
    test_vectors = read_fvecs(test_query)
    _, check_ids = index.search(np.ascontiguousarray(test_vectors[:sample_n], dtype=np.float32), args.gt_k)
    expected_ids = read_ivecs(test_gt)[:sample_n]
    validation_recall = float(np.mean([
        len(set(actual) & set(expected)) / args.gt_k
        for actual, expected in zip(check_ids, expected_ids)
    ]))
    if validation_recall < 0.999999:
        raise ValueError(f"official GT does not match rebuilt base/IP: sample recall={validation_recall}")

    hashes = {name: row_hashes(path) for name, path in split_paths.items()}
    overlap = {}
    names = list(split_paths)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            count = len(hashes[left] & hashes[right])
            overlap[f"{left}__{right}"] = count
            if count:
                raise ValueError(f"query leakage: {left} and {right} share {count} vectors")

    files = [base_fvecs, *split_paths.values(), *gt_paths.values()]
    manifest = {
        "schema_version": 1,
        "artifact_version": "yandex-t2i-official-first10m-ip-v1",
        "created_unix": int(time.time()),
        "metric": "ip",
        "normalization": "none",
        "base": {"source": "T2I/base.1B.fbin", "range": [0, 10_000_000]},
        "query_source": "T2I/query.learn.50M.fbin",
        "splits": {
            **{name: {"source_range": list(SPLITS[name])} for name in SPLITS},
            "test": {"source": "T2I/query.public.100K.fbin", "source_range": [0, 100_000]},
        },
        "ground_truth": {"k": args.gt_k, "metric": "exact_inner_product"},
        "official_gt_validation": {"sample_queries": sample_n, "set_recall_at_100": validation_recall},
        "query_overlap_counts": overlap,
        "sources": {
            str(path): {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in (base_source, learn_source, official_gt, PUBLIC_QUERY_SOURCE)
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
