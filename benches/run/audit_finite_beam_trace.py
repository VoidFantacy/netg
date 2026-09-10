#!/usr/bin/env python3
"""Corrected, non-overwriting audit of the finite-beam train-only gate."""
import argparse
import json
from collections import Counter
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import numpy as np


def load_analysis_module():
    path = Path(__file__).with_name("analyze_finite_beam_trace.py")
    spec = spec_from_file_location("finite_beam_original_analysis", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ORIG = load_analysis_module()


def bootstrap_interval(values, seed, rounds=10000):
    rng = np.random.default_rng(seed)
    values = np.asarray(values, float)
    means = np.empty(rounds)
    for start in range(0, rounds, 200):
        count = min(200, rounds - start)
        sample = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start + count] = values[sample].mean(axis=1)
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def pairwise_accuracy(query_ids, prediction, utility):
    correct = total = 0
    for query in np.unique(query_ids):
        ids = np.flatnonzero(query_ids == query)
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                i, j = ids[a], ids[b]
                truth = np.sign(utility[i] - utility[j])
                if truth == 0:
                    continue
                estimate = np.sign(prediction[i] - prediction[j])
                correct += estimate == truth
                total += 1
    return float(correct / total), total


def choose(query_ids, prediction):
    return np.asarray([
        ids[np.argmax(prediction[ids])]
        for query in np.unique(query_ids)
        for ids in [np.flatnonzero(query_ids == query)]
    ], int)


def load_ivecs(path):
    raw = np.fromfile(path, dtype=np.int32)
    if raw.size == 0:
        raise ValueError(f"empty ivecs file: {path}")
    width = int(raw[0])
    if width < 10 or raw.size % (width + 1):
        raise ValueError(f"invalid ivecs shape: {path}")
    rows = raw.reshape(-1, width + 1)
    if not np.all(rows[:, 0] == width):
        raise ValueError(f"inconsistent ivecs row width: {path}")
    return rows[:, 1:].astype(np.int64, copy=False)


def validate_trace(data, gt):
    rows = data["rows"]
    keys = [(row["query_id"], row["entry_id"], row["search_L"]) for row in rows]
    duplicate_keys = len(keys) - len(set(keys))
    query_ids = sorted({row["query_id"] for row in rows})
    search_ls = sorted({row["search_L"] for row in rows})
    candidate_count = int(data["candidate_count"])
    expected_rows = len(query_ids) * len(search_ls) * candidate_count
    rank_layout_ok = True
    controls_consistent = True
    invariant_failures = 0
    recall_mismatches = 0
    ndc_mismatches = 0
    nonnegative_trace_fields = (
        "distance_evaluations", "evaluated_neighbor_count", "expanded_count",
        "accepted_insertion_count", "rejected_by_pool_bound_count", "rewind_count",
        "rewind_span_sum", "rewind_span_max", "best_distance_improvement_count",
        "best_distance_improvement_sum", "pool_bound_improvement_count",
        "pool_bound_improvement_sum", "max_stagnation_expansions",
        "stagnation_run_count", "stagnation_expansion_sum", "final_frontier_gap",
        "final_pool_gap", "first_top10_gt_evaluation_ndc", "first_top10_gt_expansion",
    )
    for query in query_ids:
        for search_l in search_ls:
            group = [row for row in rows if row["query_id"] == query and row["search_L"] == search_l]
            rank_layout_ok &= sorted(row["geometry_rank"] for row in group) == list(range(candidate_count))
            for field in ("fast_top3_recall_at_10", "fast_top3_graph_ndc",
                          "medoid_recall_at_10", "medoid_graph_ndc"):
                controls_consistent &= len({row[field] for row in group}) == 1
    for row in rows:
        trace = row["trace"]
        numeric = [trace[field] for field in nonnegative_trace_fields if trace[field] is not None]
        ok = all(value >= 0 for value in numeric)
        ok &= trace["accepted_insertion_count"] + trace["rejected_by_pool_bound_count"] <= trace["evaluated_neighbor_count"]
        ok &= trace["best_distance_improvement_count"] <= trace["accepted_insertion_count"]
        ok &= trace["pool_bound_improvement_count"] <= trace["accepted_insertion_count"]
        ok &= trace["rewind_span_max"] <= trace["rewind_span_sum"]
        if trace["first_top10_gt_evaluation_ndc"] is not None:
            ok &= trace["first_top10_gt_evaluation_ndc"] <= trace["distance_evaluations"]
        invariant_failures += not ok
        ndc_mismatches += trace["distance_evaluations"] != row["graph_ndc"]
        truth = set(map(int, gt[row["query_id"], :10]))
        recalled = sum(int(result) in truth for result in row["result_ids"]) / 10.0
        recall_mismatches += abs(recalled - row["recall_at_10"]) > 1e-12
    passed = (len(rows) == expected_rows and duplicate_keys == 0 and rank_layout_ok
              and controls_consistent and invariant_failures == 0
              and recall_mismatches == 0 and ndc_mismatches == 0)
    return {
        "passed": bool(passed), "row_count": len(rows), "expected_row_count": expected_rows,
        "duplicate_primary_keys": duplicate_keys, "query_range": [query_ids[0], query_ids[-1] + 1],
        "search_Ls": search_ls, "geometry_rank_layout_ok": bool(rank_layout_ok),
        "controls_consistent_within_query_L": bool(controls_consistent),
        "trace_invariant_failures": int(invariant_failures),
        "recall_recompute_mismatches": int(recall_mismatches),
        "trace_ndc_recompute_mismatches": int(ndc_mismatches),
    }


def prepare(data, search_l):
    rows = [row for row in data["rows"] if row["search_L"] == search_l]
    query = np.asarray([row["query_id"] for row in rows], int)
    entry = np.asarray([row["entry_id"] for row in rows], int)
    rank = np.asarray([row["geometry_rank"] for row in rows], int)
    recall = np.asarray([row["recall_at_10"] for row in rows], float)
    ndc = np.asarray([row["graph_ndc"] for row in rows], float)
    fast_ndc = np.asarray([row["fast_top3_graph_ndc"] for row in rows], float)
    utility = recall - 0.05 * ndc / np.maximum(fast_ndc, 1.0)
    fit = query < 1600
    evaluate = ~fit
    prior = {int(e): float(utility[fit & (entry == e)].mean()) for e in np.unique(entry[fit])}
    global_prior = float(utility[fit].mean())
    geometry = np.column_stack([
        np.asarray([row["prototype_distance"] for row in rows], float),
        np.asarray([row["raw_entry_distance"] for row in rows], float),
        rank.astype(float),
        np.asarray([prior.get(row["entry_id"], global_prior) for row in rows], float),
    ])
    trace = np.column_stack([
        np.asarray([np.nan if row["trace"][key] is None else row["trace"][key] for row in rows], float)
        for key in ORIG.TRACE
    ])
    for matrix in (geometry, trace):
        medians = np.nanmedian(matrix[fit], axis=0)
        locations = np.where(np.isnan(matrix))
        matrix[locations] = np.take(medians, locations[1])
    pred_geometry = ORIG.standard_ridge(geometry[fit], utility[fit], geometry[evaluate])
    combined = np.column_stack([geometry, trace])
    pred_trace = ORIG.standard_ridge(combined[fit], utility[fit], combined[evaluate])
    return {
        "query": query[evaluate], "entry": entry[evaluate], "rank": rank[evaluate],
        "recall": recall[evaluate], "ndc": ndc[evaluate], "utility": utility[evaluate],
        "pred_geometry": pred_geometry, "pred_trace": pred_trace,
    }


def audit_dataset(data, gt):
    result = {"dataset": data["dataset"], "split": data["split"], "heldout_accessed": False,
              "data_integrity": validate_trace(data, gt), "by_L": {}}
    for search_l in sorted(set(row["search_L"] for row in data["rows"])):
        d = prepare(data, search_l)
        geometry_ids = choose(d["query"], d["pred_geometry"])
        trace_ids = choose(d["query"], d["pred_trace"])
        rank0_ids = np.asarray([
            ids[np.argmin(d["rank"][ids])]
            for query in np.unique(d["query"])
            for ids in [np.flatnonzero(d["query"] == query)]
        ], int)
        incremental_utility = d["utility"][trace_ids] - d["utility"][geometry_ids]
        incremental_recall = d["recall"][trace_ids] - d["recall"][geometry_ids]
        incremental_ndc = d["ndc"][trace_ids] - d["ndc"][geometry_ids]
        versus_rank0_recall = d["recall"][trace_ids] - d["recall"][rank0_ids]
        relative_ndc = d["ndc"][trace_ids].mean() / d["ndc"][rank0_ids].mean() - 1.0
        geometry_pairwise, pair_count = pairwise_accuracy(d["query"], d["pred_geometry"], d["utility"])
        trace_pairwise, _ = pairwise_accuracy(d["query"], d["pred_trace"], d["utility"])

        constrained = []
        for query in np.unique(d["query"]):
            ids = np.flatnonzero(d["query"] == query)
            rank0 = ids[np.argmin(d["rank"][ids])]
            feasible = ids[d["ndc"][ids] <= d["ndc"][rank0] * 1.005 + 1e-12]
            best = feasible[np.lexsort((d["ndc"][feasible], -d["utility"][feasible]))[0]]
            constrained.append((best, rank0))
        oracle_ids = np.asarray([pair[0] for pair in constrained], int)
        oracle_rank0 = np.asarray([pair[1] for pair in constrained], int)
        oracle_delta = d["utility"][oracle_ids] - d["utility"][oracle_rank0]

        positive = np.sort(incremental_utility[incremental_utility > 0])[::-1]
        top_decile = max(1, len(incremental_utility) // 10)
        concentration = float(positive[:top_decile].sum() / positive.sum()) if positive.size and positive.sum() else None
        selected_counts = Counter(map(int, d["entry"][trace_ids]))
        result["by_L"][str(search_l)] = {
            "trace_vs_geometry": {
                "mean_utility_delta": float(incremental_utility.mean()),
                "utility_delta_ci95": bootstrap_interval(incremental_utility, 20260903 + search_l),
                "mean_recall_delta": float(incremental_recall.mean()),
                "mean_ndc_delta_absolute": float(incremental_ndc.mean()),
                "geometry_pairwise_accuracy": geometry_pairwise,
                "trace_pairwise_accuracy": trace_pairwise,
                "pair_count": pair_count,
                "positive_query_fraction": float((incremental_utility > 0).mean()),
                "top_decile_share_of_positive_gain": concentration,
                "max_selected_entry_share": max(selected_counts.values()) / len(trace_ids),
            },
            "trace_vs_rank0_cost_gate": {
                "mean_recall_delta": float(versus_rank0_recall.mean()),
                "mean_ndc_delta_relative": float(relative_ndc),
                "passes_0_5_percent_ndc": bool(relative_ndc <= 0.005),
            },
            "cost_constrained_top8_oracle_vs_rank0": {
                "mean_utility_delta": float(oracle_delta.mean()),
                "utility_delta_ci95": bootstrap_interval(oracle_delta, 20261003 + search_l),
                "mean_recall_delta": float((d["recall"][oracle_ids] - d["recall"][oracle_rank0]).mean()),
                "mean_per_query_relative_ndc": float(np.mean(d["ndc"][oracle_ids] / d["ndc"][oracle_rank0] - 1.0)),
            },
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--webvid", required=True)
    parser.add_argument("--yandex", required=True)
    parser.add_argument("--webvid-gt", required=True)
    parser.add_argument("--yandex-gt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    inputs = [ORIG.load(args.webvid), ORIG.load(args.yandex)]
    ground_truth = [load_ivecs(args.webvid_gt), load_ivecs(args.yandex_gt)]
    datasets = [audit_dataset(data, gt) for data, gt in zip(inputs, ground_truth)]
    if not all(dataset["data_integrity"]["passed"] for dataset in datasets):
        raise RuntimeError("trace data-integrity audit failed")
    incremental_pass = all(
        point["trace_vs_geometry"]["mean_utility_delta"] > 0
        and point["trace_vs_geometry"]["utility_delta_ci95"][0] > 0
        for dataset in datasets for point in dataset["by_L"].values()
    )
    cost_pass = all(
        point["trace_vs_rank0_cost_gate"]["mean_recall_delta"] >= 0
        and point["trace_vs_rank0_cost_gate"]["passes_0_5_percent_ndc"]
        for dataset in datasets for point in dataset["by_L"].values()
    )
    oracle_pass = all(
        point["cost_constrained_top8_oracle_vs_rank0"]["mean_utility_delta"] > 0
        and point["cost_constrained_top8_oracle_vs_rank0"]["utility_delta_ci95"][0] > 0
        for dataset in datasets for point in dataset["by_L"].values()
    )
    report = {
        "schema_version": 2, "status": "complete", "heldout_accessed": False,
        "validation_accessed": False, "terminal_status": "NO_GO_NOT_LIGHTWEIGHT",
        "stop_stage": "D", "stage_e_triggered": False,
        "protocol": "existing train-only traces; fit [0,1600), audit [1600,2000); no validation access",
        "original_report_accepted": False,
        "gate_components": {"trace_incremental": incremental_pass, "trace_selector_cost_aligned": cost_pass, "cost_constrained_top8_oracle_headroom": oracle_pass},
        "corrected_status": "TRACE_INCREMENTAL_PASS_COST_ALIGNMENT_FAIL_COMPRESSION_UNTESTED" if incremental_pass and not cost_pass else "REVIEW_REQUIRED",
        "datasets": datasets,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(report["corrected_status"])


if __name__ == "__main__":
    main()
