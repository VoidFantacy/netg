#!/usr/bin/env python3
"""Fail-fast sanity checks between ACSG training stages."""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
from pathlib import Path

import numpy as np


ACO_RE = re.compile(
    r"ACO_SANITY AvgError=(\S+) MinError=(\S+) MaxError=(\S+) "
    r"ZeroErrorRate=(\S+) AvgHops=(\S+) InvalidLoss=(\d+) EmptyPath=(\d+)"
)


def validate_aco(args: argparse.Namespace) -> None:
    text = args.log.read_text(errors="replace")
    rows = [match.groups() for match in ACO_RE.finditer(text)]
    if len(rows) != args.expected_iterations:
        raise ValueError(
            f"ACO sanity rows {len(rows)} != expected iterations {args.expected_iterations}"
        )
    parsed = []
    for iteration, row in enumerate(rows, 1):
        avg, minimum, maximum, zero_rate, hops = map(float, row[:5])
        invalid, empty = map(int, row[5:])
        values = (avg, minimum, maximum, zero_rate, hops)
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"ACO iteration {iteration} contains non-finite diagnostics")
        if minimum < 0 or maximum < minimum or avg < minimum or avg > maximum + 1e-9:
            raise ValueError(f"ACO iteration {iteration} has inconsistent error statistics")
        if not 0 <= zero_rate <= 1 or hops <= 0 or invalid != 0 or empty != 0:
            raise ValueError(f"ACO iteration {iteration} failed sanity diagnostics")
        parsed.append((avg, maximum, zero_rate, hops))
    if args.require_first_nonzero and parsed[0][1] <= 0:
        raise ValueError("ACO first iteration has no accuracy-ranking signal")
    print(
        json.dumps(
            {
                "status": "ok",
                "stage": "aco",
                "iterations": len(parsed),
                "first": parsed[0],
                "last": parsed[-1],
            },
            sort_keys=True,
        )
    )


def validate_dpc(args: argparse.Namespace) -> None:
    data = json.loads(args.path.read_text())
    top = data.get("top_centers", [])
    bottom = data.get("bottom_centers", [])
    if not top or not bottom:
        raise ValueError("DPC must produce non-empty top and bottom centers")
    centers = [int(value) for value in top + bottom]
    if any(value < 0 or value >= args.base_count for value in centers):
        raise ValueError("DPC center ID is outside the base range")
    unique = len(set(centers))
    if unique < 2:
        raise ValueError("DPC produced fewer than two unique centers")
    print(
        json.dumps(
            {
                "status": "ok",
                "stage": "dpc",
                "top": len(top),
                "bottom": len(bottom),
                "unique": unique,
            },
            sort_keys=True,
        )
    )


def read_label_matrix(path: Path) -> np.ndarray:
    with path.open("rb") as source:
        header = source.read(8)
        if len(header) != 8:
            raise ValueError("label file is missing its two-int header")
        declared_rows, dim = struct.unpack("<ii", header)
        payload = np.fromfile(source, dtype="<i4")
    if dim != 3 or payload.size % dim:
        raise ValueError(f"invalid label payload: dim={dim}, ints={payload.size}")
    rows = payload.reshape(-1, dim)
    if declared_rows != len(rows):
        raise ValueError(f"declared label rows {declared_rows} != actual {len(rows)}")
    return rows


def validate_labels(args: argparse.Namespace) -> None:
    rows = read_label_matrix(args.path)
    if len(rows) != args.expected_rows:
        raise ValueError(f"label rows {len(rows)} != expected {args.expected_rows}")
    query_ids, hub_ids, costs = rows.T
    if np.any(query_ids < 0) or np.any(query_ids >= args.query_count):
        raise ValueError("label query ID is outside the training-query range")
    if len(np.unique(query_ids)) != len(query_ids):
        raise ValueError("label query IDs are not unique")
    valid = costs != -1
    if np.any(costs[valid] < 0):
        raise ValueError("valid labels contain a negative cost")
    if np.any(hub_ids[valid] < 0) or np.any(hub_ids[valid] >= args.hub_count):
        raise ValueError("valid label hub index is outside the DPC hub range")
    valid_ratio = float(valid.mean())
    if valid_ratio < args.min_valid_ratio:
        raise ValueError(
            f"valid-label ratio {valid_ratio:.6f} < required {args.min_valid_ratio:.6f}"
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "stage": "labels",
                "rows": len(rows),
                "valid": int(valid.sum()),
                "valid_ratio": valid_ratio,
                "cost_min": int(costs[valid].min()),
                "cost_max": int(costs[valid].max()),
            },
            sort_keys=True,
        )
    )


def validate_router(args: argparse.Namespace) -> None:
    hub_ids = np.fromfile(args.hub_ids, dtype="<i4")
    raw = np.fromfile(args.raw_hubs, dtype="<f4")
    transformed = np.fromfile(args.transformed_hubs, dtype="<f4")
    expected = len(hub_ids) * args.dim
    if len(hub_ids) < 2 or raw.size != expected or transformed.size != expected:
        raise ValueError("Router artifact shapes do not agree")
    if not np.isfinite(raw).all() or not np.isfinite(transformed).all():
        raise ValueError("Router artifacts contain non-finite values")
    transformed = transformed.reshape(-1, args.dim)
    norms = np.linalg.norm(transformed, axis=1)
    if not np.allclose(norms, 1.0, atol=1e-4, rtol=1e-4):
        raise ValueError(
            f"transformed hub norms are invalid: min={norms.min()}, max={norms.max()}"
        )
    print(
        json.dumps(
            {
                "status": "ok",
                "stage": "router",
                "hubs": len(hub_ids),
                "dim": args.dim,
                "norm_min": float(norms.min()),
                "norm_max": float(norms.max()),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="stage", required=True)

    aco = sub.add_parser("aco")
    aco.add_argument("--log", type=Path, required=True)
    aco.add_argument("--expected-iterations", type=int, required=True)
    aco.add_argument("--require-first-nonzero", action="store_true")
    aco.set_defaults(func=validate_aco)

    dpc = sub.add_parser("dpc")
    dpc.add_argument("--path", type=Path, required=True)
    dpc.add_argument("--base-count", type=int, required=True)
    dpc.set_defaults(func=validate_dpc)

    labels = sub.add_parser("labels")
    labels.add_argument("--path", type=Path, required=True)
    labels.add_argument("--expected-rows", type=int, required=True)
    labels.add_argument("--query-count", type=int, required=True)
    labels.add_argument("--hub-count", type=int, required=True)
    labels.add_argument("--min-valid-ratio", type=float, default=0.9)
    labels.set_defaults(func=validate_labels)

    router = sub.add_parser("router")
    router.add_argument("--hub-ids", type=Path, required=True)
    router.add_argument("--raw-hubs", type=Path, required=True)
    router.add_argument("--transformed-hubs", type=Path, required=True)
    router.add_argument("--dim", type=int, required=True)
    router.set_defaults(func=validate_router)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
