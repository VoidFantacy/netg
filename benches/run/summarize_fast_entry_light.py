#!/usr/bin/env python3
"""Summarize one QGT fast-entry light evaluation without ambiguous task names."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW = "2. Raw HNSW Routing (Ablation Baseline)"
PROTOTYPE = "5. Asym-Neural HNSW Routing (0ms inference)"


def load(path: Path) -> dict:
    with path.open() as stream:
        return json.load(stream)


def search_results(document: dict, method_name: str) -> dict[str, dict]:
    method = next(row for row in document["results"] if row["method_name"] == method_name)
    return {str(row["search_L"]): row for row in method["performance"]}


def per_query_results(document: dict, method_name: str) -> dict[int, dict]:
    method = next(row for row in document["methods"] if row["method"] == method_name)
    return {int(row["search_L"]): row for row in method["search_results"]}


def tail_summary(document: dict) -> dict:
    baseline = per_query_results(document, "NSG_Medoid")
    candidate = per_query_results(document, "NETG_AsymHNSW")
    output = {}
    for search_l in sorted(set(baseline) & set(candidate)):
        before = baseline[search_l]["per_query_recalls_aligned"]
        after = candidate[search_l]["per_query_recalls_aligned"]
        if len(before) != len(after):
            raise ValueError(f"aligned length mismatch at L={search_l}")
        thresholds = {}
        for threshold in (0.1, 0.2, 0.5, 0.8):
            before_failed = [value < threshold for value in before]
            after_failed = [value < threshold for value in after]
            rescued = sum(a and not b for a, b in zip(before_failed, after_failed))
            harmed = sum(not a and b for a, b in zip(before_failed, after_failed))
            thresholds[str(threshold)] = {
                "medoid_failed": sum(before_failed),
                "fast_failed": sum(after_failed),
                "rescued": rescued,
                "newly_harmed": harmed,
                "net_rescued": rescued - harmed,
            }
        output[str(search_l)] = {
            "medoid_mean_recall10": baseline[search_l]["mean_recall"],
            "fast_mean_recall10": candidate[search_l]["mean_recall"],
            "thresholds": thresholds,
        }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast-dir", type=Path, required=True)
    parser.add_argument("--r1", default="eval_r1_light.json")
    parser.add_argument("--r100", default="eval_r100_light.json")
    parser.add_argument("--per-query", default="per_query_r10_light.json")
    parser.add_argument("--output", default="evaluation_summary.json")
    args = parser.parse_args()

    directory = args.fast_dir.resolve()
    manifest = load(directory / "manifest.json")
    r1 = load(directory / args.r1)
    r100 = load(directory / args.r100)
    per_query = load(directory / args.per_query)
    contracts = {
        (document["dataset"], document["split"], document["num_queries"])
        for document in (r1, r100, per_query)
    }
    if len(contracts) != 1 or next(iter(contracts))[0] != manifest["dataset"]:
        raise ValueError(f"evaluation contract mismatch: {contracts}")
    if not manifest.get("qgt_only"):
        raise ValueError("expected a qgt_only manifest")

    output = {
        "schema_version": 1,
        "status": "exploratory-single-seed-held-out",
        "dataset": manifest["dataset"],
        "split": r1["split"],
        "num_queries": r1["num_queries"],
        "seed": manifest["variants"]["qgt_cover"]["seed"],
        "target_hubs": manifest["target_hubs"],
        "build_wall_seconds": manifest["build_wall_seconds"],
        "num_runs": {"recall1": r1["num_runs"], "recall100": r100["num_runs"]},
        "method_aliases": {
            RAW: "QGT-Cover raw hubs",
            PROTOTYPE: "QGT-Cover plus closed-form GT-basin prototype; no neural network",
            "NETG_AsymHNSW": "same closed-form prototype in the per-query file; no neural network",
        },
        "recall1": {
            "qgt_raw": search_results(r1, RAW),
            "qgt_gt_basin_prototype": search_results(r1, PROTOTYPE),
        },
        "recall100": {
            "qgt_raw": search_results(r100, RAW),
            "qgt_gt_basin_prototype": search_results(r100, PROTOTYPE),
        },
        "tail_recall10": tail_summary(per_query),
        "limitations": [
            "single clustering seed and one internal search run",
            "exact train GT preparation cost is excluded",
            "QPS is a single run and is not a stable speed claim",
        ],
    }
    output_path = directory / args.output
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
