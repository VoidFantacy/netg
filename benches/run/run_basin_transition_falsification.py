#!/usr/bin/env python3
"""Minimal train/validation falsification of a basin-transition entry score.

The script never reads held-out queries or labels.  It combines frozen-graph
basin transition counts with the existing Fast top-32 sparse utility matrices,
tunes both a shared tuple and one train-only tuple per dataset on the last 2K
prototype-train queries, then evaluates each selected single-entry policy once
on the two independent validation splits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import time
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
COST_WEIGHT = 0.05
DEV_START = 8000
EPS = 1e-12

DATASETS = {
    "webvid": {
        "dataset": "webvid2_5m_light_v1",
        "artifact_version": "roargraph-webvid2.5m-ip-v1",
        "normalization": "source_unit_norm_no_additional",
        "dim": 512,
        "train_query": "benches/datasets/WebVid2.5M_light_v1/query.router_train.seed20260826.fvecs",
        "validation_query": "benches/datasets/WebVid2.5M_light_v1/query.validation.seed20260826.fvecs",
        "hub_ids": "fast_entry_variants/webvid2_5m_light_v1_seed20260828/qgt_cover_hub_ids.bin",
        "prototypes": "fast_entry_variants/webvid2_5m_light_v1_seed20260828/qgt_gt_basin_prototype_hubs.bin",
        "transition_dir": "basin_transition_diagnostics/webvid_seed20260828_graph_bfs_v1",
        "train_utility": "sparse_utility_datasets/webvid_train10k_top32_l64_128_r10_v1/results.json",
        "validation_utility": "sparse_utility_datasets/webvid_validation10k_top32_l64_128_r10_v1/results.json",
        "index_info": "indices/webvid2_5m_light_v1_index/acosp_nsg.json.info",
        "index": "indices/webvid2_5m_light_v1_index/acosp_nsg.json",
    },
    "yandex": {
        "dataset": "yandex_t2i_official10M_ip_v1",
        "artifact_version": "yandex-t2i-official-first10m-ip-v1",
        "normalization": "none",
        "dim": 200,
        "train_query": "benches/datasets/YandexT2I_official10M_ip_v1/query.router_train.fvecs",
        "validation_query": "benches/datasets/YandexT2I_official10M_ip_v1/query.validation.fvecs",
        "hub_ids": "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260828/qgt_cover_hub_ids.bin",
        "prototypes": "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260828/qgt_gt_basin_prototype_hubs.bin",
        "transition_dir": "basin_transition_diagnostics/yandex_seed20260828_graph_bfs_v1",
        "train_utility": "sparse_utility_datasets/yandex_train10k_top32_l64_128_r10_v1/results.json",
        "validation_utility": "sparse_utility_datasets/yandex_validation10k_top32_l64_128_r10_v1/results.json",
        "index_info": "indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json.info",
        "index": "indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_fvecs(path: Path, count: int, dim: int) -> np.ndarray:
    row_width = dim + 1
    expected_min = count * row_width * 4
    if path.stat().st_size < expected_min:
        raise ValueError(f"too few fvecs bytes: {path}")
    rows = np.memmap(path, dtype=np.float32, mode="r", shape=(path.stat().st_size // (row_width * 4), row_width))
    headers = rows[:count, 0].view(np.int32)
    if not np.all(headers == dim):
        raise ValueError(f"fvec dimension mismatch: {path}")
    return np.asarray(rows[:count, 1:], dtype=np.float32)


def load_utility(path: Path, expected_dataset: str, expected_split: str) -> dict[str, np.ndarray]:
    document = json.loads(path.read_text())
    if document.get("status") != "complete":
        raise ValueError(f"incomplete utility artifact: {path}")
    if document.get("dataset") != expected_dataset or document.get("split") != expected_split:
        raise ValueError(f"utility contract mismatch: {path}")
    if document.get("top_ks") != [10] or document.get("search_Ls") != [64, 128]:
        raise ValueError(f"unexpected utility budget: {path}")
    rows = document["results"]
    ids = np.stack([[query["candidate_entry_ids"] for query in row["queries"]] for row in rows]).astype(np.int32)
    if not np.all(ids == ids[:1]):
        raise ValueError(f"candidate IDs differ across L: {path}")
    recalls = np.stack([[query["candidate_recalls"] for query in row["queries"]] for row in rows]).astype(np.float32)
    ndcs = np.stack([[query["candidate_graph_ndcs"] for query in row["queries"]] for row in rows]).astype(np.float32)
    fast_recalls = np.stack([[query["fast_top3_recall"] for query in row["queries"]] for row in rows]).astype(np.float32)
    fast_ndcs = np.stack([[query["fast_top3_graph_ndc"] for query in row["queries"]] for row in rows]).astype(np.float32)
    medoid_recalls = np.stack([[query["medoid_recall"] for query in row["queries"]] for row in rows]).astype(np.float32)
    medoid_ndcs = np.stack([[query["medoid_graph_ndc"] for query in row["queries"]] for row in rows]).astype(np.float32)
    query_ids = np.asarray([query["query_id"] for query in rows[0]["queries"]], dtype=np.int32)
    if not np.array_equal(query_ids, np.arange(len(query_ids), dtype=np.int32)):
        raise ValueError(f"query IDs are not aligned: {path}")
    relative_ndc = ndcs / np.maximum(fast_ndcs[:, :, None], 1.0)
    utility = recalls.mean(axis=0) - COST_WEIGHT * relative_ndc.mean(axis=0)
    return {
        "ids": ids[0], "recalls": recalls, "ndcs": ndcs,
        "fast_recalls": fast_recalls, "fast_ndcs": fast_ndcs,
        "medoid_recalls": medoid_recalls, "medoid_ndcs": medoid_ndcs,
        "relative_ndc": relative_ndc, "utility": utility,
    }


def row_zscore(values: np.ndarray) -> np.ndarray:
    mean = values.mean(axis=1, keepdims=True)
    std = values.std(axis=1, keepdims=True)
    return (values - mean) / np.maximum(std, 1e-6)


def softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    scaled = values / temperature
    scaled -= scaled.max(axis=1, keepdims=True)
    weights = np.exp(scaled)
    return weights / np.maximum(weights.sum(axis=1, keepdims=True), EPS)


def transition_variants(counts: np.ndarray) -> dict[str, np.ndarray]:
    variants: dict[str, np.ndarray] = {}
    all_rows = counts.astype(np.float64)
    variants["all_edges"] = (all_rows / np.maximum(all_rows.sum(axis=1, keepdims=True), 1.0)).astype(np.float32)
    cross = all_rows.copy()
    np.fill_diagonal(cross, 0.0)
    cross /= np.maximum(cross.sum(axis=1, keepdims=True), 1.0)
    identity = np.eye(len(cross), dtype=np.float64)
    for stay in (0.0, 0.25, 0.5, 0.75):
        variants[f"cross_stay_{stay:.2f}"] = ((1.0 - stay) * cross + stay * identity).astype(np.float32)
    return variants


def transition_powers(variants: dict[str, np.ndarray]) -> dict[tuple[str, int], np.ndarray]:
    powers: dict[tuple[str, int], np.ndarray] = {}
    for name, matrix in variants.items():
        current = matrix.astype(np.float64)
        for horizon in (1, 2, 3, 4):
            powers[(name, horizon)] = current.astype(np.float32)
            current = current @ matrix
    return powers


def reachability_features(
    powers: dict[tuple[str, int], np.ndarray],
    candidate_local: np.ndarray,
    geometry_z: np.ndarray,
) -> dict[tuple[str, int, float], np.ndarray]:
    features: dict[tuple[str, int, float], np.ndarray] = {}
    for key, matrix in powers.items():
        for temperature in (0.25, 0.5, 1.0, 2.0):
            target_weights = softmax(geometry_z, temperature)
            output = np.empty_like(geometry_z, dtype=np.float32)
            for start in range(0, len(candidate_local), 512):
                end = min(len(candidate_local), start + 512)
                local = candidate_local[start:end]
                pairwise = matrix[local[:, :, None], local[:, None, :]]
                probability = np.einsum("bij,bj->bi", pairwise, target_weights[start:end], optimize=True)
                output[start:end] = row_zscore(np.log(np.maximum(probability, EPS))).astype(np.float32)
            features[(key[0], key[1], temperature)] = output
    return features


def prepare_dataset(name: str, spec: dict) -> dict:
    transition_dir = ROOT / spec["transition_dir"]
    transition_manifest = json.loads((transition_dir / "manifest.json").read_text())
    if transition_manifest.get("status") != "complete" or transition_manifest.get("heldout_accessed") is not False:
        raise ValueError(f"invalid transition manifest: {transition_dir}")
    if transition_manifest.get("dataset") != spec["dataset"] or transition_manifest.get("artifact_version") != spec["artifact_version"]:
        raise ValueError(f"transition identity mismatch: {transition_dir}")
    hub_ids = np.fromfile(ROOT / spec["hub_ids"], dtype=np.int32)
    hub_count = len(hub_ids)
    if transition_manifest.get("hub_count") != hub_count:
        raise ValueError(f"hub count mismatch: {name}")
    prototypes = np.fromfile(ROOT / spec["prototypes"], dtype=np.float32)
    if prototypes.size != hub_count * spec["dim"]:
        raise ValueError(f"prototype shape mismatch: {name}")
    prototypes = prototypes.reshape(hub_count, spec["dim"])
    counts = np.fromfile(transition_dir / "transition_counts.u64", dtype=np.uint64)
    if counts.size != hub_count * hub_count:
        raise ValueError(f"transition matrix shape mismatch: {name}")
    counts = counts.reshape(hub_count, hub_count)
    train = load_utility(ROOT / spec["train_utility"], spec["dataset"], "drl_train")
    validation = load_utility(ROOT / spec["validation_utility"], spec["dataset"], "validation")
    id_to_local = {int(entry): i for i, entry in enumerate(hub_ids)}

    def add_geometry(split: dict, query_path: str) -> None:
        try:
            local = np.asarray([[id_to_local[int(entry)] for entry in row] for row in split["ids"]], dtype=np.int32)
        except KeyError as error:
            raise ValueError(f"utility candidate absent from hub IDs: {name}/{error}") from error
        queries = load_fvecs(ROOT / query_path, len(local), spec["dim"])
        candidate_prototypes = prototypes[local]
        geometry = np.einsum("bd,bkd->bk", queries, candidate_prototypes, optimize=True)
        geometry_z = row_zscore(geometry.astype(np.float64)).astype(np.float32)
        split["candidate_local"] = local
        split["geometry"] = geometry.astype(np.float32)
        split["geometry_z"] = geometry_z
        split["rank0_exact_match_fraction"] = float((np.argmax(geometry, axis=1) == 0).mean())

    add_geometry(train, spec["train_query"])
    add_geometry(validation, spec["validation_query"])
    powers = transition_powers(transition_variants(counts))
    train["reachability"] = reachability_features(powers, train["candidate_local"], train["geometry_z"])
    validation["reachability"] = reachability_features(powers, validation["candidate_local"], validation["geometry_z"])
    return {
        "name": name, "spec": spec, "transition_manifest": transition_manifest,
        "hub_ids": hub_ids, "counts": counts, "train": train, "validation": validation,
    }


def choose_indices(geometry_z: np.ndarray, reachability_z: np.ndarray, gamma: float, margin: float) -> np.ndarray:
    score = geometry_z + gamma * reachability_z
    best = np.argmax(score, axis=1)
    rows = np.arange(len(best))
    improvement = score[rows, best] - score[:, 0]
    return np.where(improvement >= margin, best, 0).astype(np.int32)


def selected_summary(split: dict, selected: np.ndarray) -> dict:
    rows = np.arange(len(selected))
    selected_utility = split["utility"][rows, selected]
    rank0_utility = split["utility"][:, 0]
    oracle_index = np.argmax(split["utility"], axis=1)
    result = {
        "mean_utility": float(selected_utility.mean()),
        "rank0_mean_utility": float(rank0_utility.mean()),
        "shortlist_oracle_mean_utility": float(split["utility"][rows, oracle_index].mean()),
        "utility_delta_vs_rank0": float((selected_utility - rank0_utility).mean()),
        "switch_fraction": float((selected != 0).mean()),
        "selected_oracle_match_fraction": float((selected == oracle_index).mean()),
        "points": [],
    }
    for budget_index, search_l in enumerate((64, 128)):
        recall = split["recalls"][budget_index, rows, selected]
        ndc = split["ndcs"][budget_index, rows, selected]
        rank0_recall = split["recalls"][budget_index, :, 0]
        rank0_ndc = split["ndcs"][budget_index, :, 0]
        fast_recall = split["fast_recalls"][budget_index]
        fast_ndc = split["fast_ndcs"][budget_index]
        result["points"].append({
            "search_L": search_l,
            "selected_recall_at_10": float(recall.mean()),
            "selected_graph_ndc": float(ndc.mean()),
            "rank0_recall_at_10": float(rank0_recall.mean()),
            "rank0_graph_ndc": float(rank0_ndc.mean()),
            "fast_top3_recall_at_10": float(fast_recall.mean()),
            "fast_top3_graph_ndc": float(fast_ndc.mean()),
            "recall_delta_vs_rank0": float((recall - rank0_recall).mean()),
            "graph_ndc_delta_pct_vs_rank0": float((ndc.mean() / rank0_ndc.mean() - 1.0) * 100.0),
            "recall_delta_vs_fast_top3": float((recall - fast_recall).mean()),
            "graph_ndc_delta_pct_vs_fast_top3": float((ndc.mean() / fast_ndc.mean() - 1.0) * 100.0),
        })
    return result


def tune_shared(datasets: dict[str, dict]) -> tuple[dict, list[dict]]:
    records = []
    feature_keys = sorted(next(iter(datasets.values()))["train"]["reachability"])
    for feature_key in feature_keys:
        for gamma in (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0):
            for margin in (0.0, 0.05, 0.1, 0.2, 0.5, 1.0):
                deltas = []
                ndc_deltas = []
                switches = []
                per_dataset = {}
                for name, data in datasets.items():
                    split = data["train"]
                    selected_all = choose_indices(split["geometry_z"], split["reachability"][feature_key], gamma, margin)
                    selected = selected_all[DEV_START:]
                    rows = np.arange(DEV_START, len(selected_all))
                    utility = split["utility"][rows, selected]
                    rank0 = split["utility"][rows, 0]
                    relative_ndc = split["relative_ndc"].mean(axis=0)
                    delta = float((utility - rank0).mean())
                    ndc_delta = float((relative_ndc[rows, selected] - relative_ndc[rows, 0]).mean())
                    switch = float((selected != 0).mean())
                    deltas.append(delta); ndc_deltas.append(ndc_delta); switches.append(switch)
                    per_dataset[name] = {"utility_delta_vs_rank0": delta, "relative_ndc_delta_vs_rank0": ndc_delta, "switch_fraction": switch}
                records.append({
                    "transition_mode": feature_key[0], "horizon": feature_key[1], "target_temperature": feature_key[2],
                    "gamma": gamma, "margin": margin,
                    "mean_utility_delta_vs_rank0": float(np.mean(deltas)),
                    "min_dataset_utility_delta_vs_rank0": float(np.min(deltas)),
                    "mean_relative_ndc_delta_vs_rank0": float(np.mean(ndc_deltas)),
                    "mean_switch_fraction": float(np.mean(switches)),
                    "per_dataset": per_dataset,
                })
    records.sort(key=lambda row: (
        -row["min_dataset_utility_delta_vs_rank0"],
        -row["mean_utility_delta_vs_rank0"],
        row["mean_relative_ndc_delta_vs_rank0"],
        row["mean_switch_fraction"],
    ))
    return records[0], records[:20]


def tune_individual(data: dict) -> tuple[dict, list[dict]]:
    split = data["train"]
    rows = np.arange(DEV_START, len(split["ids"]))
    relative_ndc = split["relative_ndc"].mean(axis=0)
    records = []
    for feature_key, reachability in split["reachability"].items():
        for gamma in (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0):
            for margin in (0.0, 0.05, 0.1, 0.2, 0.5, 1.0):
                selected_all = choose_indices(split["geometry_z"], reachability, gamma, margin)
                selected = selected_all[DEV_START:]
                utility_delta = float((split["utility"][rows, selected] - split["utility"][rows, 0]).mean())
                ndc_delta = float((relative_ndc[rows, selected] - relative_ndc[rows, 0]).mean())
                records.append({
                    "transition_mode": feature_key[0], "horizon": feature_key[1],
                    "target_temperature": feature_key[2], "gamma": gamma, "margin": margin,
                    "utility_delta_vs_rank0": utility_delta,
                    "relative_ndc_delta_vs_rank0": ndc_delta,
                    "switch_fraction": float((selected != 0).mean()),
                })
    records.sort(key=lambda row: (-row["utility_delta_vs_rank0"], row["relative_ndc_delta_vs_rank0"], row["switch_fraction"]))
    return records[0], records[:20]


def gate_passed(summary: dict) -> bool:
    mean_ndc_growth = float(np.mean([point["graph_ndc_delta_pct_vs_rank0"] for point in summary["points"]]))
    point_recall_nonnegative = all(point["recall_delta_vs_rank0"] >= -1e-9 for point in summary["points"])
    return summary["utility_delta_vs_rank0"] > 1e-4 and point_recall_nonnegative and mean_ndc_growth <= 0.5


def render_markdown(report: dict) -> str:
    hp = report["selected_shared_hyperparameters"]
    lines = [
        "# Basin Transition Graph Minimal Falsification",
        "",
        "## Decision",
        "",
        f"**{report['decision']}** — {report['decision_reason']}",
        "",
        "No held-out queries or labels were read. One shared parameter tuple was selected on the last 2K rows of each independent prototype-train utility artifact, then evaluated once on WebVid and Yandex validation 10K.",
        "",
        "## Selected shared configuration",
        "",
        f"- transition mode: `{hp['transition_mode']}`",
        f"- horizon: `{hp['horizon']}`",
        f"- target temperature: `{hp['target_temperature']}`",
        f"- reachability weight gamma: `{hp['gamma']}`",
        f"- conservative switch margin: `{hp['margin']}`",
        "",
        "## Validation",
        "",
        "| Dataset | Utility delta vs rank-0 | Switch fraction | L | Recall delta vs rank-0 | graph NDC delta vs rank-0 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, data in report["datasets"].items():
        summary = data["validation"]
        for index, point in enumerate(summary["points"]):
            lines.append(
                f"| {name if index == 0 else ''} | {summary['utility_delta_vs_rank0']:+.6f} | "
                f"{summary['switch_fraction']:.2%} | {point['search_L']} | "
                f"{point['recall_delta_vs_rank0'] * 100:+.3f} pp | {point['graph_ndc_delta_pct_vs_rank0']:+.3f}% |"
            )
    lines += [
        "",
        "## Per-dataset train-tuned diagnostic",
        "",
        "| Dataset | Utility delta vs rank-0 | Switch fraction | L | Recall delta vs rank-0 | graph NDC delta vs rank-0 | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for name, data in report["datasets"].items():
        diagnostic = data["individual_train_tuned_diagnostic"]
        summary = diagnostic["validation"]
        for index, point in enumerate(summary["points"]):
            lines.append(
                f"| {name if index == 0 else ''} | {summary['utility_delta_vs_rank0']:+.6f} | "
                f"{summary['switch_fraction']:.2%} | {point['search_L']} | "
                f"{point['recall_delta_vs_rank0'] * 100:+.3f} pp | {point['graph_ndc_delta_pct_vs_rank0']:+.3f}% | "
                f"{'PASS' if diagnostic['gate_passed'] else 'FAIL'} |"
            )
    lines += [
        "",
        "## Gate",
        "",
        "The primary decision uses the independently train-tuned configuration for each dataset and passes only if both datasets have positive mean utility delta, neither L=64 nor L=128 loses Recall, and mean graph-NDC growth versus rank-0 is at most 0.5% on each dataset. The shared configuration is a stricter transfer diagnostic. This is a mechanism diagnostic over the existing top-32 sparse counterfactual matrix, not a final end-to-end result.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite output directory: {output_dir}")
    output_dir.mkdir(parents=True)
    started = time.time()

    datasets = {name: prepare_dataset(name, spec) for name, spec in DATASETS.items()}
    selected_hp, top_configs = tune_shared(datasets)
    feature_key = (selected_hp["transition_mode"], selected_hp["horizon"], selected_hp["target_temperature"])

    dataset_reports = {}
    shared_gate_flags = []
    individual_gate_flags = []
    for name, data in datasets.items():
        validation = data["validation"]
        selected = choose_indices(
            validation["geometry_z"], validation["reachability"][feature_key],
            selected_hp["gamma"], selected_hp["margin"],
        )
        selected_ids = validation["ids"][np.arange(len(selected)), selected].astype(np.int32)
        routes_path = output_dir / f"{name}_validation_single_routes.int32"
        selected_ids.tofile(routes_path)
        validation_summary = selected_summary(validation, selected)
        shared_passed = gate_passed(validation_summary)
        shared_gate_flags.append(shared_passed)

        individual_hp, individual_top_configs = tune_individual(data)
        individual_key = (individual_hp["transition_mode"], individual_hp["horizon"], individual_hp["target_temperature"])
        individual_selected = choose_indices(
            validation["geometry_z"], validation["reachability"][individual_key],
            individual_hp["gamma"], individual_hp["margin"],
        )
        individual_ids = validation["ids"][np.arange(len(individual_selected)), individual_selected].astype(np.int32)
        individual_routes_path = output_dir / f"{name}_validation_individual_train_tuned_single_routes.int32"
        individual_ids.tofile(individual_routes_path)
        individual_summary = selected_summary(validation, individual_selected)
        individual_passed = gate_passed(individual_summary)
        individual_gate_flags.append(individual_passed)
        spec = data["spec"]
        source_paths = {
            "transition_manifest": ROOT / spec["transition_dir"] / "manifest.json",
            "transition_counts": ROOT / spec["transition_dir"] / "transition_counts.u64",
            "basin_sizes": ROOT / spec["transition_dir"] / "basin_sizes.u64",
            "hub_ids": ROOT / spec["hub_ids"], "prototypes": ROOT / spec["prototypes"],
            "train_query": ROOT / spec["train_query"], "validation_query": ROOT / spec["validation_query"],
            "train_utility": ROOT / spec["train_utility"], "validation_utility": ROOT / spec["validation_utility"],
            "index_info": ROOT / spec["index_info"],
            "index": ROOT / spec["index"],
        }
        dataset_reports[name] = {
            "dataset": spec["dataset"], "artifact_version": spec["artifact_version"],
            "metric": "ip", "normalization": spec["normalization"], "build_seed": 20260828,
            "hub_count": len(data["hub_ids"]), "candidate_budget": int(validation["ids"].shape[1]),
            "online_entry_count": 1, "heldout_accessed": False,
            "rank0_exact_geometry_match_fraction_train": data["train"]["rank0_exact_match_fraction"],
            "rank0_exact_geometry_match_fraction_validation": validation["rank0_exact_match_fraction"],
            "transition_graph": data["transition_manifest"],
            "validation": validation_summary, "shared_gate_passed": shared_passed,
            "routes_file": str(routes_path.relative_to(ROOT)), "routes_sha256": sha256(routes_path),
            "individual_train_tuned_diagnostic": {
                "selected_hyperparameters": {key: individual_hp[key] for key in ("transition_mode", "horizon", "target_temperature", "gamma", "margin")},
                "dev_metrics": {key: individual_hp[key] for key in ("utility_delta_vs_rank0", "relative_ndc_delta_vs_rank0", "switch_fraction")},
                "top_20_dev_configurations": individual_top_configs,
                "validation": individual_summary, "gate_passed": individual_passed,
                "routes_file": str(individual_routes_path.relative_to(ROOT)),
                "routes_sha256": sha256(individual_routes_path),
            },
            "sources": {key: {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for key, path in source_paths.items()},
        }

    passed = all(individual_gate_flags)
    report = {
        "schema_version": 1, "status": "complete", "framework_version": "btg_falsification_v1",
        "core_mechanism": "query-conditioned finite-horizon diffusion on directed graph-BFS basin transitions",
        "component_role": "diagnostic_core_mechanism", "selection_split": "prototype-train last 2K per dataset",
        "validation_split": "independent validation 10K per dataset", "heldout_accessed": False,
        "objective_terms": {"quality": "mean Recall@10 over L=64/128", "cost": "0.05 * graph_NDC / Fast-top3 graph_NDC", "tail_risk": None},
        "constraints": {"candidate_pool": "existing Fast top-32", "online_entry_count": 1, "frozen_graph": True, "online_probe": False},
        "gate_definition": {"decision_scope": "per-dataset configuration selected only on its prototype-train dev split", "both_dataset_utility_delta_min": 0.0001, "per_L_recall_delta_min": 0.0, "mean_graph_ndc_growth_pct_max": 0.5},
        "selected_shared_hyperparameters": {key: selected_hp[key] for key in ("transition_mode", "horizon", "target_temperature", "gamma", "margin")},
        "shared_selection_rule": "maximize the minimum utility delta across the two prototype-train dev splits, then mean utility delta, then lower NDC and switch rate",
        "shared_dev_metrics": {key: selected_hp[key] for key in ("min_dataset_utility_delta_vs_rank0", "mean_utility_delta_vs_rank0", "mean_relative_ndc_delta_vs_rank0", "mean_switch_fraction", "per_dataset")},
        "top_20_shared_dev_configurations": top_configs,
        "datasets": dataset_reports,
        "decision": "GO" if passed else "NO-GO",
        "shared_transfer_gate_passed": all(shared_gate_flags),
        "decision_reason": "BTG transition score passed all cross-dataset validation conditions even with independently train-tuned configurations." if passed else "BTG transition score failed at least one cross-dataset validation condition even when each dataset used its own train-only selected configuration.",
        "wall_seconds": time.time() - started,
        "environment": {"python": platform.python_version(), "numpy": np.__version__, "platform": platform.platform(), "cpu_count": os.cpu_count()},
        "implementation": {
            "analysis_script": {"path": str(Path(__file__).resolve().relative_to(ROOT)), "sha256": sha256(Path(__file__).resolve())},
            "graph_builder": {"path": "benches/build_basin_transition_graph.cpp", "sha256": sha256(ROOT / "benches/build_basin_transition_graph.cpp")},
        },
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    (output_dir / "analysis.md").write_text(render_markdown(report))
    print(json.dumps({"status": "complete", "decision": report["decision"], "wall_seconds": report["wall_seconds"], "output": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
