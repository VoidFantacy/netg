#!/usr/bin/env python3
"""Build closed-form prototypes from independent single-oracle entry labels.

This is a predictability diagnostic, not the final utility-ranking method.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_fvecs(path: Path, limit: int) -> np.ndarray:
    with path.open("rb") as stream:
        dim = struct.unpack("i", stream.read(4))[0]
    raw = np.memmap(path, mode="r", dtype=np.float32).reshape(-1, dim + 1)
    rows = np.asarray(raw[:limit, 1:], dtype=np.float32)
    return rows.copy()


def normalize(rows: np.ndarray) -> np.ndarray:
    return rows / np.maximum(np.linalg.norm(rows, axis=1, keepdims=True), 1e-12)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle-json", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--raw-hubs", type=Path, required=True)
    parser.add_argument("--hub-ids", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--search-L", type=int, default=64)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--prior-strength", type=float, default=1.0)
    args = parser.parse_args()

    document = json.loads(args.oracle_json.read_text())
    if document.get("status") != "complete" or document.get("split") != "drl_train":
        raise ValueError("requires completed independent drl_train oracle result")
    row = next(item for item in document["results"]
               if item["search_L"] == args.search_L and item["top_k"] == args.top_k)
    selected_ids = np.asarray(row["selected_single_entry_ids"], dtype=np.int32)
    queries = normalize(read_fvecs(args.queries, len(selected_ids)))
    hub_ids = np.fromfile(args.hub_ids, dtype=np.int32)
    raw_hubs = np.fromfile(args.raw_hubs, dtype=np.float32).reshape(len(hub_ids), -1)
    raw_hubs = normalize(raw_hubs)
    id_to_local = {int(value): index for index, value in enumerate(hub_ids)}
    try:
        labels = np.asarray([id_to_local[int(value)] for value in selected_ids], dtype=np.int32)
    except KeyError as error:
        raise ValueError(f"oracle selected non-current hub: {error}") from error

    sums = args.prior_strength * raw_hubs
    np.add.at(sums, labels, queries)
    prototypes = normalize(sums).astype(np.float32)
    counts = np.bincount(labels, minlength=len(hub_ids))

    args.output_dir.mkdir(parents=True, exist_ok=False)
    prototype_path = args.output_dir / "search_aware_oracle_label_prototypes.bin"
    ids_path = args.output_dir / "hub_ids.bin"
    prototypes.tofile(prototype_path)
    hub_ids.tofile(ids_path)
    manifest = {
        "schema_version": 1,
        "purpose": "closed-form oracle-label predictability diagnostic; not final method",
        "dataset": document["dataset"],
        "train_split": document["split"],
        "train_queries": len(selected_ids),
        "label_search_L": args.search_L,
        "label_top_k": args.top_k,
        "prior_strength": args.prior_strength,
        "hub_count": len(hub_ids),
        "hubs_with_labels": int((counts > 0).sum()),
        "min_labels_per_observed_hub": int(counts[counts > 0].min()),
        "max_labels_per_hub": int(counts.max()),
        "sources": {
            "oracle_json": str(args.oracle_json), "oracle_sha256": sha256(args.oracle_json),
            "queries": str(args.queries), "queries_sha256": sha256(args.queries),
            "raw_hubs": str(args.raw_hubs), "raw_hubs_sha256": sha256(args.raw_hubs),
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
