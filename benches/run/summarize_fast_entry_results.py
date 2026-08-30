#!/usr/bin/env python3
"""Create a provenance-aware summary for the exploratory fast-entry runs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
FAST = ROOT / "fast_entry_variants/webvid2_5m_light_v1"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def performance(path: Path, method: str) -> dict[str, float]:
    document = load(path)
    row = next(item for item in document["results"] if item["method_name"] == method)
    return {str(item["search_L"]): item["recall"] for item in row["performance"]}


def per_query(path: Path, method: str) -> list[dict]:
    document = load(path)
    return next(item for item in document["methods"] if item["method"] == method)["search_results"]


def tail_summary(path: Path) -> dict:
    base_rows = per_query(path, "NSG_Medoid")
    fast_rows = per_query(path, "NETG_AsymHNSW")
    output = {}
    for search_l, base_row, fast_row in zip((64, 128, 200, 400), base_rows, fast_rows):
        base = np.asarray(base_row["per_query_recalls_aligned"])
        fast = np.asarray(fast_row["per_query_recalls_aligned"])
        thresholds = {}
        for threshold in (0.1, 0.2, 0.5, 0.8):
            base_failed = base < threshold
            fast_failed = fast < threshold
            thresholds[str(threshold)] = {
                "medoid_failed": int(base_failed.sum()),
                "fast_failed": int(fast_failed.sum()),
                "rescued": int((base_failed & ~fast_failed).sum()),
                "still_failed": int((base_failed & fast_failed).sum()),
                "newly_harmed": int((~base_failed & fast_failed).sum()),
            }
        output[str(search_l)] = {
            "medoid_mean_recall10": float(base.mean()),
            "fast_mean_recall10": float(fast.mean()),
            "thresholds": thresholds,
        }
    return output


def main() -> None:
    old_r1 = ROOT / "test/webvid2_5m_light_v1_results/webvid2_5m_light_v1_recall1_light.json"
    old_r100 = ROOT / "test/webvid2_5m_light_v1_results/webvid2_5m_light_v1_recall100_light.json"
    fast_r1 = FAST / "eval_qgt_full_fast_nsg_r1.json"
    fast_r100 = FAST / "eval_qgt_full_fast_r100.json"
    fast_tail = FAST / "per_query_qgt_full_fast_r10.json"
    report = {
        "schema_version": 1,
        "status": "exploratory 10K x 1 run; not a final paper result",
        "dataset": "webvid2_5m_light_v1",
        "split": "held-out-test",
        "method_aliases": {
            "fast R1/R100 raw task": "QGT-Cover raw hubs",
            "fast R1/R100 neural task": "QGT-Cover plus closed-form GT-basin query prototypes; no neural network",
            "fast per-query NETG_AsymHNSW": "QGT-Cover plus closed-form GT-basin query prototypes; no neural network",
        },
        "validity": {
            "eval_qgt_vs_prototype_r1.json/raw task": "INVALID: QGT vectors were paired with W-DPC IDs",
            "eval_qgt_vs_prototype_r1.json/neural task": "valid prototype-uniform result on W-DPC hubs",
            "eval_qgt_full_fast_nsg_r1.json": "valid; loads the version-1 frozen NSG artifact and has no ACO dependency",
            "eval_qgt_full_fast_r100.json": "valid; graph bytes come from the matching ACPG container but weights are released and unused",
            "per_query_qgt_full_fast_r10.json": "valid under the same matching-graph condition",
        },
        "offline_wall_seconds": {
            "formal_aco": 1591.43,
            "formal_dpc": 307.12,
            "formal_probe_labels": 2755.44,
            "formal_neural_router": 1847.95,
            "fast_variants_cold_observed": 12.13960617199973,
            "fast_variants_warm_observed": load(FAST / "manifest.json")["build_wall_seconds"],
        },
        "recall1": {
            "medoid": performance(old_r1, "0. Medoid (Baseline)"),
            "wdpc_raw": performance(old_r1, "2. Raw HNSW Routing (Ablation Baseline)"),
            "neural": performance(old_r1, "5. Asym-Neural HNSW Routing (0ms inference)"),
            "qgt_raw": performance(fast_r1, "2. Raw HNSW Routing (Ablation Baseline)"),
            "qgt_gt_basin_prototype": performance(fast_r1, "5. Asym-Neural HNSW Routing (0ms inference)"),
        },
        "recall100": {
            "medoid": performance(old_r100, "0. Medoid (Baseline)"),
            "wdpc_raw": performance(old_r100, "2. Raw HNSW Routing (Ablation Baseline)"),
            "neural": performance(old_r100, "5. Asym-Neural HNSW Routing (0ms inference)"),
            "qgt_raw": performance(fast_r100, "2. Raw HNSW Routing (Ablation Baseline)"),
            "qgt_gt_basin_prototype": performance(fast_r100, "5. Asym-Neural HNSW Routing (0ms inference)"),
        },
        "tail_recall10": tail_summary(fast_tail),
        "source_files": [
            str(path.relative_to(ROOT))
            for path in (old_r1, old_r100, fast_r1, fast_r100, fast_tail, FAST / "manifest.json")
        ],
    }
    output = FAST / "evaluation_summary.json"
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
