#!/usr/bin/env python3
"""Aggregate provenance-aware fast-entry results across clustering seeds."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    with path.open() as stream:
        return json.load(stream)


def mean_std(values: list[float | int]) -> dict[str, float]:
    numeric = [float(value) for value in values]
    return {
        "mean": statistics.fmean(numeric),
        "std_across_seeds": statistics.pstdev(numeric),
        "min": min(numeric),
        "max": max(numeric),
    }


def method_map(document: dict) -> dict[str, dict]:
    return {entry["method_name"]: entry for entry in document["results"]}


def performance_map(method: dict) -> dict[int, dict]:
    return {int(row["search_L"]): row for row in method["performance"]}


def per_query_map(document: dict) -> dict[str, dict[int, dict]]:
    return {
        method["method"]: {
            int(row["search_L"]): row for row in method["search_results"]
        }
        for method in document["methods"]
    }


def aggregate_search(seed_docs: dict[int, dict], method_name: str) -> dict:
    by_seed = {
        seed: performance_map(method_map(document)[method_name])
        for seed, document in seed_docs.items()
    }
    search_ls = sorted(set.intersection(*(set(rows) for rows in by_seed.values())))
    output = {}
    for search_l in search_ls:
        recalls = [rows[search_l]["recall"] for rows in by_seed.values()]
        qps = [rows[search_l]["qps"] for rows in by_seed.values()]
        output[str(search_l)] = {
            "recall": mean_std(recalls),
            "qps": mean_std(qps),
            "per_seed": {
                str(seed): {
                    "recall": rows[search_l]["recall"],
                    "qps_mean_over_internal_runs": rows[search_l]["qps"],
                    "qps_std_over_internal_runs": rows[search_l]["qps_std"],
                }
                for seed, rows in by_seed.items()
            },
        }
    return output


def aggregate_tail(seed_docs: dict[int, dict]) -> dict:
    thresholds = (0.1, 0.2, 0.5, 0.8)
    per_seed: dict[int, dict] = {}
    for seed, document in seed_docs.items():
        methods = per_query_map(document)
        medoid = methods["NSG_Medoid"]
        fast = methods["NETG_AsymHNSW"]
        rows = {}
        for search_l in sorted(set(medoid) & set(fast)):
            baseline = medoid[search_l]["per_query_recalls_aligned"]
            candidate = fast[search_l]["per_query_recalls_aligned"]
            if len(baseline) != len(candidate):
                raise ValueError(f"aligned length mismatch for seed={seed}, L={search_l}")
            threshold_rows = {}
            for threshold in thresholds:
                base_failed = [value < threshold for value in baseline]
                fast_failed = [value < threshold for value in candidate]
                rescued = sum(a and not b for a, b in zip(base_failed, fast_failed))
                harmed = sum(not a and b for a, b in zip(base_failed, fast_failed))
                threshold_rows[str(threshold)] = {
                    "medoid_failed": sum(base_failed),
                    "fast_failed": sum(fast_failed),
                    "rescued": rescued,
                    "newly_harmed": harmed,
                    "net_rescued": rescued - harmed,
                }
            rows[str(search_l)] = {
                "medoid_mean_recall10": medoid[search_l]["mean_recall"],
                "fast_mean_recall10": fast[search_l]["mean_recall"],
                "thresholds": threshold_rows,
            }
        per_seed[seed] = rows

    output = {}
    search_ls = sorted(set.intersection(*(set(rows) for rows in per_seed.values())), key=int)
    for search_l in search_ls:
        output[search_l] = {
            "medoid_mean_recall10": mean_std(
                [rows[search_l]["medoid_mean_recall10"] for rows in per_seed.values()]
            ),
            "fast_mean_recall10": mean_std(
                [rows[search_l]["fast_mean_recall10"] for rows in per_seed.values()]
            ),
            "thresholds": {},
            "per_seed": {str(seed): rows[search_l] for seed, rows in per_seed.items()},
        }
        for threshold in map(str, thresholds):
            output[search_l]["thresholds"][threshold] = {
                field: mean_std(
                    [
                        rows[search_l]["thresholds"][threshold][field]
                        for rows in per_seed.values()
                    ]
                )
                for field in (
                    "medoid_failed", "fast_failed", "rescued",
                    "newly_harmed", "net_rescued",
                )
            }
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="webvid2_5m_light_v1")
    parser.add_argument("--seeds", default="20260828,20260829,20260830")
    parser.add_argument("--variant-name")
    parser.add_argument("--split", choices=("held-out-test", "validation"), default="held-out-test")
    parser.add_argument("--status")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    variant_name = args.variant_name or args.dataset
    seeds = [int(token) for token in args.seeds.split(",") if token]
    if len(set(seeds)) < 2:
        raise ValueError("multi-seed summary requires at least two unique seeds")
    seed_dirs = {
        seed: ROOT / "fast_entry_variants" / f"{variant_name}_seed{seed}"
        for seed in seeds
    }
    manifests = {seed: load(path / "manifest.json") for seed, path in seed_dirs.items()}
    for seed, manifest in manifests.items():
        if manifest["dataset"] != args.dataset:
            raise ValueError(f"dataset mismatch for seed {seed}")
        if manifest["variants"]["qgt_cover"]["seed"] != seed:
            raise ValueError(f"manifest seed mismatch for seed {seed}")

    r1 = {seed: load(path / "eval_r1_3run.json") for seed, path in seed_dirs.items()}
    r100 = {seed: load(path / "eval_r100_3run.json") for seed, path in seed_dirs.items()}
    tail = {seed: load(path / "per_query_r10.json") for seed, path in seed_dirs.items()}
    for top_k, documents in ((1, r1), (100, r100)):
        for seed, document in documents.items():
            expected = (args.dataset, args.split, top_k, 10000, 3)
            observed = (
                document["dataset"], document["split"], document["top_k"],
                document["num_queries"], document["num_runs"],
            )
            if observed != expected:
                raise ValueError(f"evaluation contract mismatch seed={seed}: {observed}")
    for seed, document in tail.items():
        expected = (args.dataset, args.split, 10, 10000)
        observed = (
            document["dataset"], document["split"], document["top_k"],
            document["num_queries"],
        )
        if observed != expected:
            raise ValueError(f"tail contract mismatch seed={seed}: {observed}")

    raw_name = "2. Raw HNSW Routing (Ablation Baseline)"
    prototype_name = "5. Asym-Neural HNSW Routing (0ms inference)"
    recall1 = {
        "qgt_raw": aggregate_search(r1, raw_name),
        "qgt_gt_basin_prototype": aggregate_search(r1, prototype_name),
    }
    recall100 = {
        "qgt_raw": aggregate_search(r100, raw_name),
        "qgt_gt_basin_prototype": aggregate_search(r100, prototype_name),
    }
    medoid_name = "0. Medoid (Baseline)"
    if all(medoid_name in method_map(document) for document in r1.values()):
        recall1["medoid"] = aggregate_search(r1, medoid_name)
    if all(medoid_name in method_map(document) for document in r100.values()):
        recall100["medoid"] = aggregate_search(r100, medoid_name)

    output = {
        "schema_version": 1,
        "status": args.status or f"exploratory-multiseed-{args.split}",
        "dataset": args.dataset,
        "split": args.split,
        "num_queries": 10000,
        "internal_runs_per_seed": 3,
        "clustering_seeds": seeds,
        "method_aliases": {
            raw_name: "QGT-Cover raw hubs",
            prototype_name: "QGT-Cover plus closed-form GT-basin prototype; no neural network",
            "NETG_AsymHNSW in per-query files": "same closed-form prototype method; no neural network",
        },
        "recall1": recall1,
        "recall100": recall100,
        "tail_recall10": aggregate_tail(tail),
        "build_wall_seconds": {
            str(seed): manifest["build_wall_seconds"] for seed, manifest in manifests.items()
        },
        "limitations": [
            "validation split only; held-out test was not accessed" if args.split == "validation"
            else "held-out test result; validation must remain separate",
            "three clustering seeds share the same fixed data split",
            "exact train GT preparation cost is excluded",
            "internal QPS repetitions are not interleaved across methods or seeds",
        ],
    }
    output_path = args.output or (
        ROOT / "fast_entry_variants" / f"{variant_name}_multiseed_summary.json"
    )
    output_path.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(output_path)


if __name__ == "__main__":
    main()
