#!/usr/bin/env python3
"""Train-only incremental-explanatory gate for finite-beam trace diagnostics."""
import argparse
import json
from pathlib import Path

import numpy as np

GEOMETRY = ["prototype_distance", "raw_entry_distance", "geometry_rank", "entry_prior"]
TRACE = [
    "distance_evaluations", "evaluated_neighbor_count", "expanded_count",
    "accepted_insertion_count", "rejected_by_pool_bound_count", "rewind_count",
    "rewind_span_sum", "rewind_span_max", "best_distance_improvement_count",
    "best_distance_improvement_sum", "pool_bound_improvement_count",
    "pool_bound_improvement_sum", "max_stagnation_expansions", "stagnation_run_count",
    "stagnation_expansion_sum", "initial_best_distance", "final_best_distance",
    "final_frontier_gap", "final_pool_gap",
]


def load(path):
    with open(path) as f:
        data = json.load(f)
    if data.get("status") != "complete" or data.get("heldout_accessed") is not False:
        raise RuntimeError(f"invalid trace input: {path}")
    return data


def standard_ridge(x_train, y_train, x_eval, alpha=1.0):
    mean = x_train.mean(0)
    scale = x_train.std(0)
    scale[scale < 1e-12] = 1.0
    train = (x_train - mean) / scale
    test = (x_eval - mean) / scale
    design = np.column_stack([np.ones(len(train)), train])
    penalty = np.eye(design.shape[1]) * alpha
    penalty[0, 0] = 0.0
    coef = np.linalg.solve(design.T @ design + penalty, design.T @ y_train)
    return np.column_stack([np.ones(len(test)), test]) @ coef


def grouped_choice(query_ids, predictions, utility, recall, ndc, rank):
    selected = []
    for q in np.unique(query_ids):
        mask = query_ids == q
        choices = np.flatnonzero(mask)
        best = choices[np.argmax(predictions[mask])]
        rank0 = choices[np.argmin(rank[mask])]
        selected.append((utility[best], recall[best], ndc[best], utility[rank0], recall[rank0], ndc[rank0]))
    return np.asarray(selected, dtype=float)


def bootstrap_lower(values, seed=20260903, rounds=10000):
    rng = np.random.default_rng(seed)
    n = len(values)
    means = np.empty(rounds)
    for start in range(0, rounds, 200):
        take = min(200, rounds - start)
        ids = rng.integers(0, n, size=(take, n))
        means[start:start + take] = values[ids].mean(1)
    return float(np.quantile(means, 0.025))


def analyze_one(data):
    rows = data["rows"]
    ls = sorted(set(row["search_L"] for row in rows))
    result = {"dataset": data["dataset"], "split": data["split"], "rows": len(rows), "by_L": {}}
    for L in ls:
        sub = [row for row in rows if row["search_L"] == L]
        qid = np.asarray([row["query_id"] for row in sub], int)
        rank = np.asarray([row["geometry_rank"] for row in sub], float)
        entry = np.asarray([row["entry_id"] for row in sub], int)
        recall = np.asarray([row["recall_at_10"] for row in sub], float)
        ndc = np.asarray([row["graph_ndc"] for row in sub], float)
        fast_ndc = np.asarray([row["fast_top3_graph_ndc"] for row in sub], float)
        utility = recall - 0.05 * ndc / np.maximum(fast_ndc, 1.0)
        fit_queries = qid < 1600
        eval_queries = ~fit_queries
        if not fit_queries.any() or not eval_queries.any():
            raise RuntimeError("frozen 80/20 query split unavailable")
        prior = {}
        for e in np.unique(entry[fit_queries]):
            prior[int(e)] = float(utility[fit_queries & (entry == e)].mean())
        global_prior = float(utility[fit_queries].mean())
        values = {"prototype_distance": [], "raw_entry_distance": [], "geometry_rank": [], "entry_prior": []}
        trace_values = {key: [] for key in TRACE}
        for row in sub:
            values["prototype_distance"].append(row["prototype_distance"])
            values["raw_entry_distance"].append(row["raw_entry_distance"])
            values["geometry_rank"].append(row["geometry_rank"])
            values["entry_prior"].append(prior.get(row["entry_id"], global_prior))
            for key in TRACE:
                value = row["trace"][key]
                trace_values[key].append(np.nan if value is None else value)
        geom = np.column_stack([np.asarray(values[key], float) for key in GEOMETRY])
        trace = np.column_stack([np.asarray(trace_values[key], float) for key in TRACE])
        for matrix in (geom, trace):
            med = np.nanmedian(matrix[fit_queries], axis=0)
            matrix[np.isnan(matrix)] = np.take(med, np.where(np.isnan(matrix))[1])
        pred_geom = standard_ridge(geom[fit_queries], utility[fit_queries], geom[eval_queries])
        both = np.column_stack([geom, trace])
        pred_trace = standard_ridge(both[fit_queries], utility[fit_queries], both[eval_queries])
        actual = {"qid": qid[eval_queries], "utility": utility[eval_queries], "recall": recall[eval_queries], "ndc": ndc[eval_queries], "rank": rank[eval_queries]}
        choices = {}
        for name, pred in (("geometry", pred_geom), ("geometry_plus_trace", pred_trace)):
            chosen = grouped_choice(actual["qid"], pred, actual["utility"], actual["recall"], actual["ndc"], actual["rank"])
            utility_delta = chosen[:, 0] - chosen[:, 3]
            choices[name] = {
                "selected_mean_utility": float(chosen[:, 0].mean()), "rank0_mean_utility": float(chosen[:, 3].mean()),
                "utility_delta_vs_rank0": float(utility_delta.mean()), "utility_delta_ci95_lower": bootstrap_lower(utility_delta, seed=20260903 + L),
                "selected_mean_recall_at_10": float(chosen[:, 1].mean()), "rank0_mean_recall_at_10": float(chosen[:, 4].mean()),
                "recall_delta_vs_rank0": float((chosen[:, 1] - chosen[:, 4]).mean()),
                "selected_mean_graph_ndc": float(chosen[:, 2].mean()), "rank0_mean_graph_ndc": float(chosen[:, 5].mean()),
                "ndc_delta_relative_to_rank0": float(chosen[:, 2].mean() / chosen[:, 5].mean() - 1.0), "eval_queries": int(len(chosen)),
            }
        result["by_L"][str(L)] = choices
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--webvid", required=True); parser.add_argument("--yandex", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = {"schema_version": 1, "status": "complete", "heldout_accessed": False,
              "selection_protocol": "train query rows [0,1600) fit; [1600,2000) evaluate; ridge alpha=1; lambda=0.05; 10k query-bootstrap",
              "geometry_features": GEOMETRY, "trace_features": TRACE, "datasets": [analyze_one(load(args.webvid)), analyze_one(load(args.yandex))]}
    checks = []
    for dataset in report["datasets"]:
        for L, modes in dataset["by_L"].items():
            trace = modes["geometry_plus_trace"]
            checks.append(trace["utility_delta_vs_rank0"] > 0 and trace["utility_delta_ci95_lower"] > 0 and trace["recall_delta_vs_rank0"] >= 0 and trace["ndc_delta_relative_to_rank0"] <= 0.005)
    report["gate_status"] = "PASS" if all(checks) else "NO_GO_TRACE_NOT_INCREMENTAL"
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"FINITE_BEAM_ANALYSIS_COMPLETE gate={report['gate_status']} output={output}")


if __name__ == "__main__":
    main()
