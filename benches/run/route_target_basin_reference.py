#!/usr/bin/env python3
"""Deterministic merge reference for exported target-basin candidates.

This script never reads GT. It consumes the exact candidate IDs and scores
exported by bench_target_basin_eval, independently replays duplicate merging,
anchor preservation, and the score-desc/ID-asc tie break, then writes both a
JSON audit and an optional raw int32 route matrix.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Iterable


def merge_route(anchor: int, views: Iterable[list[dict[str, float | int]]]) -> list[int]:
    best: dict[int, float] = {}
    for view in views:
        for item in view:
            entry_id = int(item["id"])
            score = float(item["score"])
            if entry_id not in best or score > best[entry_id]:
                best[entry_id] = score
    best.pop(anchor, None)
    ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) < 2:
        raise ValueError("fewer than two non-anchor candidates after merge")
    return [anchor, ranked[0][0], ranked[1][0]]


def write_new(path: Path, data: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def self_test() -> None:
    views = [
        [{"id": 10, "score": 0.5}, {"id": 11, "score": 0.9}],
        [{"id": 11, "score": 0.95}, {"id": 20, "score": 0.7}],
        [{"id": 30, "score": 0.85}, {"id": 20, "score": 0.75}],
    ]
    assert merge_route(10, views) == [10, 11, 30]
    tie_views = [
        [{"id": 5, "score": 1.0}],
        [{"id": 9, "score": 0.8}],
        [{"id": 7, "score": 0.8}],
    ]
    assert merge_route(5, tie_views) == [5, 7, 9]
    print("TARGET_BASIN_REFERENCE_SELF_TEST_OK")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output")
    parser.add_argument("--routes-output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        self_test()
        return
    if not args.input or not args.output:
        parser.error("--input and --output are required unless --self-test is used")

    source_path = Path(args.input)
    source = json.loads(source_path.read_text())
    if source.get("status") != "complete" or not source.get("route_only"):
        raise ValueError("input is not a complete route-only evaluator artifact")
    if source.get("gt_loaded") is not False:
        raise ValueError("route reference requires an explicitly GT-free input")
    if source.get("method") != "ensemble":
        raise ValueError("route reference requires method=ensemble")

    route_rows = source.get("routes", [])
    rebuilt: list[list[int]] = []
    cell_mismatches = 0
    row_mismatches = 0
    anchor_mismatches = 0
    mismatch_examples: list[dict[str, object]] = []
    for expected_query_id, row in enumerate(route_rows):
        if int(row["query_id"]) != expected_query_id:
            raise ValueError("query IDs are not contiguous and aligned")
        primary = [int(value) for value in row["primary_entry_ids"]]
        if len(primary) != 8:
            raise ValueError("primary_top8 is not length eight")
        reference = merge_route(primary[0], row["view_candidates"])
        actual = [int(value) for value in row["final_entry_ids"]]
        rebuilt.append(reference)
        mismatched = sum(left != right for left, right in zip(reference, actual))
        cell_mismatches += mismatched
        row_mismatches += int(mismatched > 0)
        anchor_mismatches += int(actual[0] != primary[0])
        if mismatched and len(mismatch_examples) < 16:
            mismatch_examples.append(
                {"query_id": expected_query_id, "cpp": actual, "reference": reference}
            )

    total_cells = len(rebuilt) * 3
    report = {
        "schema_version": 1,
        "status": "PASS" if cell_mismatches == 0 and anchor_mismatches == 0 else "FAIL",
        "source": str(source_path),
        "dataset": source.get("dataset"),
        "split": source.get("split"),
        "heldout_accessed": False,
        "gt_loaded": False,
        "num_queries": len(rebuilt),
        "route_cells": total_cells,
        "route_cell_mismatch_count": cell_mismatches,
        "route_cell_mismatch_fraction": cell_mismatches / total_cells if total_cells else 0.0,
        "route_row_mismatch_count": row_mismatches,
        "rank0_mismatch_count": anchor_mismatches,
        "rank0_preserved": anchor_mismatches == 0,
        "tie_break": "score_desc_then_entry_id_asc",
        "duplicate_merge": "maximum_score",
        "mismatch_examples": mismatch_examples,
    }
    write_new(Path(args.output), (json.dumps(report, indent=2) + "\n").encode())
    if args.routes_output:
        flattened = [value for route in rebuilt for value in route]
        payload = struct.pack(f"<{len(flattened)}i", *flattened)
        write_new(Path(args.routes_output), payload)
    print(
        "TARGET_BASIN_REFERENCE_COMPLETE "
        f"status={report['status']} queries={len(rebuilt)} mismatches={cell_mismatches}"
    )


if __name__ == "__main__":
    main()
