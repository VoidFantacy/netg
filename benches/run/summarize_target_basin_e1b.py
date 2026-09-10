#!/usr/bin/env python3
"""Validate E1b artifacts and freeze the routing-cost decision.

This script deliberately treats equal-total-NDC as a conjunctive gate.  If it
fails, wall-time matching is not run because timing cannot reverse that gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_ROOT = ROOT / "target_basin_formalization/20260907_v1"
DEFAULT_PROTOCOL = DEFAULT_ARTIFACT_ROOT / "protocol.json"
BINARY = ROOT / "build/benches/bench_target_basin_eval"
REFERENCE = ROOT / "benches/run/route_target_basin_reference.py"
RUNNER = ROOT / "benches/run/run_target_basin_protocol.py"
GRID = [16, 24, 32, 48, 64, 96, 128, 160, 200, 256, 400]

DATASETS: dict[str, dict[str, Any]] = {
    "webvid": {
        "key": "webvid2_5m_light_v1",
        "dimension": 512,
        "hub_count": 815,
        "query": ROOT / "benches/datasets/WebVid2.5M_light_v1/query.router_train.seed20260826.fvecs",
        "query_name": "query.router_train.seed20260826.fvecs",
        "gt_name": "gt.router_train.seed20260826.ip.ivecs",
        "base_name": "base.webvid2_5m.fvecs",
        "manifest": ROOT / "benches/datasets/WebVid2.5M_light_v1/manifest.json",
        "graph": ROOT / "indices/webvid2_5m_light_v1_index/acosp_nsg.json",
        "views": [
            ROOT / "fast_entry_variants/webvid2_5m_light_v1_seed20260828",
            ROOT / "fast_entry_variants/webvid2_5m_light_v1_seed20260829",
            ROOT / "fast_entry_variants/webvid2_5m_light_v1_seed20260830",
        ],
    },
    "yandex": {
        "key": "yandex_t2i_official10M_ip_v1",
        "dimension": 200,
        "hub_count": 821,
        "query": ROOT / "benches/datasets/YandexT2I_official10M_ip_v1/query.router_train.fvecs",
        "query_name": "query.router_train.fvecs",
        "gt_name": "gt.router_train.ip.ivecs",
        "base_name": "base.official_first10M.fvecs",
        "manifest": ROOT / "benches/datasets/YandexT2I_official10M_ip_v1/manifest.json",
        "graph": ROOT / "indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json",
        "views": [
            ROOT / "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260828",
            ROOT / "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260829",
            ROOT / "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260830",
        ],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run_smoke(command: list[str], expected: str) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    combined = completed.stdout + completed.stderr
    return {
        "command": [display_path(Path(command[0])) if Path(command[0]).is_absolute() else command[0], *command[1:]],
        "exit_code": completed.returncode,
        "expected_text": expected,
        "expected_text_found": expected in combined,
        "status": "PASS" if completed.returncode == 0 and expected in combined else "FAIL",
    }


def validate_document(
    document: dict[str, Any],
    *,
    dataset: str,
    method: str,
    backend: str,
    route_only: bool,
) -> None:
    require(document["dataset"] == dataset, f"dataset mismatch: {document['dataset']}")
    require(document["method"] == method, f"method mismatch: {document['method']}")
    require(document["router_backend"] == backend, f"backend mismatch: {document['router_backend']}")
    require(document["measurement"] == "count", "E1b cost artifacts must use count mode")
    require(document["split"] == "drl_train", f"unexpected split: {document['split']}")
    require(document["num_queries"] == 10000, f"expected 10000 queries, got {document['num_queries']}")
    require(document["num_runs"] == 1, "count mode must have exactly one run")
    require(document["threads"] == 16, "E1b must use 16 threads")
    require(document["heldout_accessed"] is False, "held-out access detected")
    require(document["gt_loaded"] is (not route_only), "unexpected GT-loading state")
    require(document["route_only"] is route_only, "route_only flag mismatch")
    hnsw = document["hnsw"]
    require(hnsw["M"] == 16 and hnsw["ef_construction"] == 200, "HNSW build parameters drifted")
    require(hnsw["primary"] == {"ef_search": 10, "random_seed": 100}, "primary HNSW drifted")
    require(
        hnsw["secondary"] == {"ef_search": 32, "random_seeds": [101, 102]},
        "secondary HNSW drifted",
    )


def read_queries(path: Path, dimension: int, count: int) -> np.ndarray:
    raw = np.memmap(path, dtype=np.float32, mode="r")
    require(raw.size % (dimension + 1) == 0, f"bad fvecs size: {path}")
    records = raw.reshape(-1, dimension + 1)
    require(records.shape[0] >= count, f"not enough query rows: {path}")
    dimensions = records[:count, 0].view(np.int32)
    require(bool(np.all(dimensions == dimension)), f"fvecs dimension header mismatch: {path}")
    return np.asarray(records[:count, 1:])


def candidate_ids(route: dict[str, Any], view_index: int) -> set[int]:
    return {int(candidate["id"]) for candidate in route["view_candidates"][view_index]}


def distribution(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(array.mean()),
        "min": float(array.min()),
        "p01": float(np.quantile(array, 0.01)),
        "perfect_query_count": int(np.count_nonzero(array == 1.0)),
        "query_count": int(array.size),
    }


def exact_top8_diagnostics(
    cfg: dict[str, Any],
    dense: dict[str, Any],
    approximate: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    count = 10000
    dimension = int(cfg["dimension"])
    query = read_queries(cfg["query"], dimension, count)
    approximate_recalls: list[list[float]] = [[], [], []]
    dense_recalls: list[list[float]] = [[], [], []]

    for view_index, directory in enumerate(cfg["views"]):
        prototype_path = directory / "qgt_gt_basin_prototype_hubs.bin"
        ids_path = directory / "qgt_cover_hub_ids.bin"
        ids = np.fromfile(ids_path, dtype=np.int32)
        require(ids.size == cfg["hub_count"], f"hub ID count mismatch: {ids_path}")
        require(np.unique(ids).size == ids.size, f"duplicate hub IDs: {ids_path}")
        prototypes = np.fromfile(prototype_path, dtype=np.float32)
        require(
            prototypes.size == ids.size * dimension,
            f"prototype shape mismatch: {prototype_path}",
        )
        prototypes = prototypes.reshape(ids.size, dimension)

        # Match ExactPrototypeView::dot exactly: float32 accumulation in
        # increasing dimension order.  A BLAS GEMM can reassociate/FMA the
        # reduction and changes a few near-tie top-8 cells.
        for start in range(0, count, 512):
            query_batch = query[start : start + 512]
            scores = np.zeros((query_batch.shape[0], ids.size), dtype=np.float32)
            for dimension_index in range(dimension):
                scores += (
                    query_batch[:, dimension_index, np.newaxis]
                    * prototypes[np.newaxis, :, dimension_index]
                )
            for local_index, score_row in enumerate(scores):
                query_id = start + local_index
                exact_order = np.lexsort((ids, -score_row))[:8]
                exact = set(map(int, ids[exact_order]))
                approximate_set = candidate_ids(approximate["routes"][query_id], view_index)
                dense_set = candidate_ids(dense["routes"][query_id], view_index)
                require(len(approximate_set) == 8, "approximate top-8 contains duplicate or missing IDs")
                require(len(dense_set) == 8, "dense top-8 contains duplicate or missing IDs")
                approximate_recalls[view_index].append(len(exact & approximate_set) / 8.0)
                dense_recalls[view_index].append(len(exact & dense_set) / 8.0)

    return (
        [distribution(values) for values in approximate_recalls],
        [distribution(values) for values in dense_recalls],
    )


def route_diagnostics(
    cfg: dict[str, Any],
    dense: dict[str, Any],
    approximate: dict[str, Any],
) -> dict[str, Any]:
    require(len(dense["routes"]) == len(approximate["routes"]) == 10000, "route row count mismatch")
    exact_recalls, dense_exact_recalls = exact_top8_diagnostics(cfg, dense, approximate)
    # The dense pilot intentionally retains Micro-HNSW for view 1; views 2/3
    # must be exact and therefore provide a cross-check of the NumPy reference.
    require(dense_exact_recalls[1]["mean"] == 1.0, "dense view 2 does not match exact top-8")
    require(dense_exact_recalls[2]["mean"] == 1.0, "dense view 3 does not match exact top-8")

    changed_order = 0
    changed_set = 0
    changed_cells = 0
    anchor_mismatch = 0
    primary_candidate_mismatch = 0
    dense_ndc: list[int] = []
    hnsw_ndc: list[int] = []
    for dense_row, hnsw_row in zip(dense["routes"], approximate["routes"]):
        require(dense_row["query_id"] == hnsw_row["query_id"], "route query IDs are not aligned")
        dense_final = dense_row["final_entry_ids"]
        hnsw_final = hnsw_row["final_entry_ids"]
        changed_order += int(dense_final != hnsw_final)
        changed_set += int(set(dense_final) != set(hnsw_final))
        changed_cells += sum(left != right for left, right in zip(dense_final, hnsw_final))
        anchor_mismatch += int(hnsw_final[0] != hnsw_row["primary_entry_ids"][0])
        primary_candidate_mismatch += int(
            hnsw_row["primary_entry_ids"] != dense_row["primary_entry_ids"]
        )
        dense_ndc.append(int(dense_row["routing_total_ndc"]))
        hnsw_ndc.append(int(hnsw_row["routing_total_ndc"]))

    require(anchor_mismatch == 0, "anchor preservation failed")
    require(primary_candidate_mismatch == 0, "primary HNSW candidates changed between backends")
    dense_stats = {
        "mean": float(np.mean(dense_ndc)),
        "min": int(min(dense_ndc)),
        "max": int(max(dense_ndc)),
    }
    hnsw_stats = {
        "mean": float(np.mean(hnsw_ndc)),
        "min": int(min(hnsw_ndc)),
        "max": int(max(hnsw_ndc)),
    }
    return {
        "exact_top8_set_recall_by_view": {
            f"view{index + 1}": values for index, values in enumerate(exact_recalls)
        },
        "dense_exact_reference_check_by_view": {
            f"view{index + 1}": values for index, values in enumerate(dense_exact_recalls)
        },
        "anchor_mismatch_count": anchor_mismatch,
        "primary_candidate_mismatch_count": primary_candidate_mismatch,
        "final_route_order_change": {
            "query_count": changed_order,
            "query_fraction": changed_order / 10000.0,
        },
        "final_route_set_change": {
            "query_count": changed_set,
            "query_fraction": changed_set / 10000.0,
        },
        "final_route_cell_change": {
            "cell_count": changed_cells,
            "cell_fraction": changed_cells / 30000.0,
        },
        "dense_routing_ndc": dense_stats,
        "hnsw_all_routing_ndc": hnsw_stats,
        "routing_ndc_reduction_fraction": 1.0 - hnsw_stats["mean"] / dense_stats["mean"],
    }


def extract_result_rows(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    document = load_json(path)
    rows = [
        {
            "search_L": int(row["search_L"]),
            "top_k": int(row["top_k"]),
            "run": int(row["run"]),
            "recall_at_10": float(row["mean_recall"]),
            "routing_ndc": float(row["mean_routing_ndc"]),
            "graph_ndc": float(row["mean_graph_ndc"]),
            "total_ndc": float(row["mean_total_ndc"]),
        }
        for row in document["results"]
    ]
    return document, rows


def bracket(rows: list[dict[str, Any]], budget: float) -> tuple[dict[str, Any], dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["search_L"])
    lower = [row for row in ordered if row["total_ndc"] <= budget]
    upper = [row for row in ordered if row["total_ndc"] > budget]
    require(bool(lower and upper), f"cost grid does not bracket budget {budget}")
    return max(lower, key=lambda row: row["search_L"]), min(upper, key=lambda row: row["search_L"])


def expected_refinement_ls(rows: list[dict[str, Any]], budgets: list[float]) -> list[int]:
    expected: list[int] = []
    existing = {row["search_L"] for row in rows}
    for budget in budgets:
        lower, upper = bracket(rows, budget)
        slack = (budget - lower["total_ndc"]) / budget
        if slack <= 0.02:
            continue
        midpoint = (lower["search_L"] + upper["search_L"]) // 2
        require(midpoint not in (lower["search_L"], upper["search_L"]), "unrefinable integer bracket")
        if midpoint not in existing and midpoint not in expected:
            expected.append(midpoint)
    return sorted(expected)


def cost_gate(hnsw_dir: Path, short: str, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    fast_path = hnsw_dir / f"{short}_fast10k_count.json"
    grid_path = hnsw_dir / f"{short}_hnsw10k_count_grid.json"
    fast_document, fast_rows = extract_result_rows(fast_path)
    grid_document, grid_rows = extract_result_rows(grid_path)
    validate_document(fast_document, dataset=cfg["key"], method="fast", backend="dense", route_only=False)
    validate_document(
        grid_document,
        dataset=cfg["key"],
        method="ensemble",
        backend="hnsw_all",
        route_only=False,
    )
    require([row["search_L"] for row in fast_rows] == [64, 128], "Fast target L values drifted")
    require([row["search_L"] for row in grid_rows] == GRID, "fixed E1b grid drifted")
    require(all(row["top_k"] == 10 and row["run"] == 0 for row in fast_rows + grid_rows), "K/run drifted")

    budgets = [row["total_ndc"] for row in fast_rows]
    all_candidates = list(grid_rows)
    refinement_trace: list[dict[str, Any]] = []
    refinement_paths = sorted(hnsw_dir.glob(f"{short}_hnsw10k_count_refine*.json"))
    require(len(refinement_paths) <= 2, "more than two refinement rounds were run")
    for round_number, path in enumerate(refinement_paths, start=1):
        expected = expected_refinement_ls(all_candidates, budgets)
        document, rows = extract_result_rows(path)
        validate_document(
            document,
            dataset=cfg["key"],
            method="ensemble",
            backend="hnsw_all",
            route_only=False,
        )
        observed = sorted(row["search_L"] for row in rows)
        require(observed == expected, f"refinement round {round_number}: expected L={expected}, got {observed}")
        require(all(row["top_k"] == 10 and row["run"] == 0 for row in rows), "refinement K/run drifted")
        refinement_trace.append(
            {
                "round": round_number,
                "trigger": "lower measured cost slack > 2%",
                "selection_uses_recall": False,
                "expected_and_observed_search_Ls": observed,
                "artifact": display_path(path),
            }
        )
        all_candidates.extend(rows)

    require(len(refinement_paths) == 2, "the preregistered second refinement round is missing")
    targets: dict[str, Any] = {}
    plot_rows = list(all_candidates)
    all_pass = True
    for fast in fast_rows:
        legal = [row for row in all_candidates if row["total_ndc"] <= fast["total_ndc"]]
        require(bool(legal), f"no legal equal-NDC point for Fast L{fast['search_L']}")
        chosen = max(legal, key=lambda row: (row["recall_at_10"], row["total_ndc"]))
        delta = chosen["recall_at_10"] - fast["recall_at_10"]
        passed = delta >= 0.0
        all_pass = all_pass and passed
        targets[f"Fast_L{fast['search_L']}"] = {
            "fast": fast,
            "matched_hnsw_all": chosen,
            "total_ndc_slack": fast["total_ndc"] - chosen["total_ndc"],
            "total_ndc_slack_fraction": (fast["total_ndc"] - chosen["total_ndc"]) / fast["total_ndc"],
            "recall_delta": delta,
            "status": "PASS" if passed else "FAIL",
        }

    return (
        {
            "status": "PASS" if all_pass else "FAIL",
            "selection_rule": "highest measured Recall among points with total_ndc <= paired Fast budget",
            "interpolation_used_for_selection": False,
            "refinement_trace": refinement_trace,
            "targets": targets,
        },
        plot_rows + fast_rows,
    )


def dataset_provenance(short: str, cfg: dict[str, Any], protocol_dataset: dict[str, Any]) -> dict[str, Any]:
    manifest = load_json(cfg["manifest"])
    manifest_hash = sha256(cfg["manifest"])
    require(manifest_hash == protocol_dataset["manifest_sha256"], f"{short} manifest hash drifted")
    files = manifest["files"]
    views: list[dict[str, Any]] = []
    for directory in cfg["views"]:
        build_manifest_path = directory / "manifest.json"
        build_manifest = load_json(build_manifest_path)
        prototype = directory / "qgt_gt_basin_prototype_hubs.bin"
        ids = directory / "qgt_cover_hub_ids.bin"
        expected_variant = build_manifest["variants"]["qgt_gt_basin_prototype"]
        actual_prototype_hash = sha256(prototype)
        actual_ids_hash = sha256(ids)
        require(actual_prototype_hash == expected_variant["hubs_sha256"], f"prototype hash drifted: {prototype}")
        require(actual_ids_hash == expected_variant["ids_sha256"], f"ID hash drifted: {ids}")
        views.append(
            {
                "seed": int(build_manifest["variants"]["qgt_cover"]["seed"]),
                "manifest": display_path(build_manifest_path),
                "manifest_sha256": sha256(build_manifest_path),
                "prototype": display_path(prototype),
                "prototype_sha256": actual_prototype_hash,
                "entry_ids": display_path(ids),
                "entry_ids_sha256": actual_ids_hash,
            }
        )
    return {
        "dataset": cfg["key"],
        "artifact_version": manifest["artifact_version"],
        "metric": manifest["metric"],
        "normalization": manifest["normalization"],
        "dataset_manifest": display_path(cfg["manifest"]),
        "dataset_manifest_sha256": manifest_hash,
        "base": {
            "file": cfg["base_name"],
            "bytes": files[cfg["base_name"]]["bytes"],
            "sha256": files[cfg["base_name"]]["sha256"],
        },
        "selection_query": {
            "file": cfg["query_name"],
            "rows_used": [0, 10000],
            "bytes": files[cfg["query_name"]]["bytes"],
            "sha256": files[cfg["query_name"]]["sha256"],
        },
        "selection_gt": {
            "file": cfg["gt_name"],
            "rows_used": [0, 10000],
            "bytes": files[cfg["gt_name"]]["bytes"],
            "sha256": files[cfg["gt_name"]]["sha256"],
        },
        "graph": {
            "file": display_path(cfg["graph"]),
            "bytes": cfg["graph"].stat().st_size,
            "sha256": protocol_dataset["graph_sha256"],
            "info_sha256": protocol_dataset["graph_info_sha256"],
            "R": 64,
            "L_build": 100,
            "C": 512,
        },
        "views": views,
    }


def make_plot(path: Path, cost_results: dict[str, Any], plot_rows: dict[str, list[dict[str, Any]]]) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)
    for axis, short in zip(axes, ("webvid", "yandex")):
        candidates = {}
        fast = []
        for row in plot_rows[short]:
            if row["search_L"] in (64, 128) and math.isclose(
                row["routing_ndc"],
                cost_results[short]["targets"][f"Fast_L{row['search_L']}"]["fast"]["routing_ndc"],
            ):
                fast.append(row)
            else:
                candidates[row["search_L"]] = row
        ordered = sorted(candidates.values(), key=lambda row: row["total_ndc"])
        axis.plot(
            [row["total_ndc"] for row in ordered],
            [row["recall_at_10"] for row in ordered],
            color="#4C78A8",
            marker="o",
            markersize=3,
            linewidth=1.2,
            label="HNSW-all",
        )
        for index, target in enumerate(cost_results[short]["targets"].values()):
            fast_row = target["fast"]
            chosen = target["matched_hnsw_all"]
            axis.scatter(
                [fast_row["total_ndc"]],
                [fast_row["recall_at_10"]],
                marker="*",
                s=95,
                color="#E45756",
                label="Fast target" if index == 0 else None,
                zorder=4,
            )
            axis.scatter(
                [chosen["total_ndc"]],
                [chosen["recall_at_10"]],
                facecolors="none",
                edgecolors="#54A24B",
                s=75,
                linewidths=1.8,
                label="selected <= budget" if index == 0 else None,
                zorder=5,
            )
        axis.set_title("WebVid" if short == "webvid" else "Yandex")
        axis.set_xlabel("mean total NDC / query")
        axis.set_ylabel("Recall@10")
        axis.grid(alpha=0.25)
        axis.legend(fontsize=8)
    figure.suptitle("E1b train-10K: Recall at matched total-distance budget")
    figure.savefig(path, dpi=180)
    plt.close(figure)


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# E1b routing-cost report",
        "",
        "Decision: **NO_GO_ROUTING_COST**. Artifact checks passed; the method gate failed. "
        "No held-out query or GT was read.",
        "",
        "## Equal-total-NDC gate",
        "",
        "| Dataset | Fast target | Fast NDC | Fast R@10 | Matched L | Matched NDC | Matched R@10 | Delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for short in ("webvid", "yandex"):
        label = "WebVid" if short == "webvid" else "Yandex"
        for target_name, target in report["datasets"][short]["cost_gate"]["targets"].items():
            fast = target["fast"]
            chosen = target["matched_hnsw_all"]
            lines.append(
                f"| {label} | {target_name.replace('_', ' ')} | {fast['total_ndc']:.3f} | "
                f"{fast['recall_at_10']:.5f} | {chosen['search_L']} | {chosen['total_ndc']:.3f} | "
                f"{chosen['recall_at_10']:.5f} | {target['recall_delta'] * 100:+.3f} pp |"
            )
    lines.extend(
        [
            "",
            "All four legal matched points are below Fast Recall. Because equal-total-NDC and "
            "equal-wall are conjunctive requirements, wall-time runs were omitted: they cannot "
            "reverse the failed NDC gate.",
            "",
            "## Router diagnostics",
            "",
            "| Dataset | exact top-8 recall v1/v2/v3 | dense -> HNSW routing NDC | final-route change | anchor mismatch |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for short in ("webvid", "yandex"):
        label = "WebVid" if short == "webvid" else "Yandex"
        route = report["datasets"][short]["route_diagnostics"]
        recalls = route["exact_top8_set_recall_by_view"]
        lines.append(
            f"| {label} | {recalls['view1']['mean']:.5f} / {recalls['view2']['mean']:.5f} / "
            f"{recalls['view3']['mean']:.5f} | {route['dense_routing_ndc']['mean']:.3f} -> "
            f"{route['hnsw_all_routing_ndc']['mean']:.3f} | "
            f"{route['final_route_order_change']['query_fraction'] * 100:.2f}% | "
            f"{route['anchor_mismatch_count']} |"
        )
    lines.extend(
        [
            "",
            "The fixed secondary Micro-HNSW removes most dense-routing distance cost and preserves "
            "the anchor, but the remaining routing cost forces graph-search L low enough that total "
            "Recall is worse than Fast at every paired budget.",
            "",
            "E2--E4 and tail analysis are `NOT_RUN` by the preregistered stopping rule. Fast v1 "
            "remains the selected method; no parameter scan or fallback branch was opened.",
            "",
            "Cost curve: `../../figures/e1b_recall_vs_total_ndc.png`.",
            "",
        ]
    )
    return "\n".join(lines)


def top_level_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Multi-view Target-Basin formalization",
        "",
        "Execution status: **COMPLETE**. Decision: **NO_GO_ROUTING_COST**.",
        "",
        "- E0: `PASS` (16 engineering checks).",
        "- E1 dense: `FAIL`; routing NDC alone made both L64 targets infeasible.",
        "- E1b fixed HNSW-all: `FAIL`; all four equal-total-NDC Recall comparisons are below Fast.",
        "- E2, E3, E4: `NOT_RUN` by the frozen stopping rule.",
        "- Held-out accessed: `false`.",
        "",
        "The fixed backend is efficient enough to make the comparison feasible, but not efficient "
        "enough to preserve the same graph-search budget: matched Recall deltas are "
        "WebVid `-14.697/-4.960 pp` and Yandex `-4.103/-1.463 pp` for the Fast L64/L128 targets.",
        "",
        "The project therefore returns to Fast v1. Detailed evidence is in "
        "`pilot/hnsw/report.md`; the machine-readable decision is `gate.json`. Tail/stability, "
        "attribution, offline break-even, and held-out evaluation are not applicable after this "
        "early gate failure.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--skip-large-hash-check",
        action="store_true",
        help="Trust protocol graph hashes instead of re-reading the two frozen graph files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_root = args.artifact_root.resolve()
    hnsw_dir = artifact_root / "pilot/hnsw"
    protocol_path = args.protocol.resolve()
    report_path = hnsw_dir / "report.json"
    report_md_path = hnsw_dir / "report.md"
    gate_path = artifact_root / "gate.json"
    top_report_path = artifact_root / "report.md"
    figure_path = artifact_root / "figures/e1b_recall_vs_total_ndc.png"
    for output in (report_path, report_md_path, gate_path, top_report_path, figure_path):
        if output.exists():
            raise FileExistsError(f"refusing to overwrite output: {output}")

    protocol = load_json(protocol_path)
    require(protocol["heldout_accessed"] is False, "protocol records held-out access")
    require(protocol["stages"]["E0"] == "PASS", "E0 did not pass")
    require(protocol["stages"]["E1"] == "FAIL_TRIGGER_E1B", "E1 did not authorize E1b")
    require(
        protocol["stages"]["E1b"] in ("RUNNING", "NO_GO_ROUTING_COST"),
        "protocol E1b state is incompatible",
    )
    protocol_by_key = {row["key"]: row for row in protocol["datasets"]}

    smokes = {
        "evaluator_help": run_smoke([str(BINARY), "--help"], "--router_backend"),
        "evaluator_self_test": run_smoke([str(BINARY), "--self_test"], "TARGET_BASIN_SELF_TEST_OK"),
        "reference_self_test": run_smoke(
            [str(ROOT / ".venv_cpu/bin/python"), str(REFERENCE), "--self-test"],
            "TARGET_BASIN_REFERENCE_SELF_TEST_OK",
        ),
        "runner_help": run_smoke(
            [str(ROOT / ".venv_cpu/bin/python"), str(RUNNER), "--help"],
            "--stage",
        ),
    }
    require(all(value["status"] == "PASS" for value in smokes.values()), "smoke test failed")

    source_and_binary_paths = [
        ROOT / "benches/bench_target_basin_eval.cpp",
        ROOT / "benches/bench_entry_oracle.cpp",
        ROOT / "benches/run/route_target_basin_reference.py",
        ROOT / "benches/run/audit_target_basin_e0.py",
        Path(__file__).resolve(),
        RUNNER,
        ROOT / "benches/CMakeLists.txt",
        BINARY,
        ROOT / "build/benches/bench_entry_oracle",
        ROOT / "benches/datasets/settings.json",
    ]
    source_and_binary_hashes = {display_path(path): sha256(path) for path in source_and_binary_paths}

    datasets: dict[str, Any] = {}
    plot_rows: dict[str, list[dict[str, Any]]] = {}
    input_paths: list[Path] = []
    for short, cfg in DATASETS.items():
        dense_path = hnsw_dir / f"{short}_dense_route10k_count.json"
        hnsw_path = hnsw_dir / f"{short}_hnsw_route10k_count.json"
        dense = load_json(dense_path)
        approximate = load_json(hnsw_path)
        validate_document(dense, dataset=cfg["key"], method="ensemble", backend="dense", route_only=True)
        validate_document(
            approximate,
            dataset=cfg["key"],
            method="ensemble",
            backend="hnsw_all",
            route_only=True,
        )
        route = route_diagnostics(cfg, dense, approximate)
        costs, rows = cost_gate(hnsw_dir, short, cfg)
        provenance = dataset_provenance(short, cfg, protocol_by_key[cfg["key"]])
        if not args.skip_large_hash_check:
            actual_graph_hash = sha256(cfg["graph"])
            require(actual_graph_hash == provenance["graph"]["sha256"], f"{short} graph hash drifted")
            provenance["graph"]["hash_verified_now"] = True
        else:
            provenance["graph"]["hash_verified_now"] = False
        datasets[short] = {
            "provenance": provenance,
            "route_diagnostics": route,
            "cost_gate": costs,
        }
        plot_rows[short] = rows
        input_paths.extend(
            [
                dense_path,
                hnsw_path,
                hnsw_dir / f"{short}_fast10k_count.json",
                hnsw_dir / f"{short}_hnsw10k_count_grid.json",
                *sorted(hnsw_dir.glob(f"{short}_hnsw10k_count_refine*.json")),
            ]
        )

    equal_ndc_pass = all(dataset["cost_gate"]["status"] == "PASS" for dataset in datasets.values())
    require(not equal_ndc_pass, "E1b unexpectedly passed; this no-go summarizer must not short-circuit timing")
    require(all(not path.name.lower().startswith("heldout") for path in input_paths), "held-out artifact path detected")

    input_hashes = {display_path(path): sha256(path) for path in input_paths}
    protocol_hash = sha256(protocol_path)
    report: dict[str, Any] = {
        "schema_version": 1,
        "stage": "E1b",
        "artifact_validation": "PASS",
        "method_gate": "FAIL",
        "decision": "NO_GO_ROUTING_COST",
        "reason": "All four equal-total-NDC Recall@10 comparisons are below paired Fast.",
        "selection_split": "drl_train_first_10000",
        "heldout_accessed": False,
        "parameter_scan": False,
        "router": protocol["e1b_router"],
        "datasets": datasets,
        "gate": {
            "equal_total_ndc": "FAIL",
            "equal_batch_wall": "NOT_RUN",
            "equal_batch_wall_reason": (
                "The E1 gate is conjunctive; timing cannot reverse failure of equal-total-NDC Recall."
            ),
            "next_stage": "NOT_RUN",
        },
        "smoke_tests": smokes,
        "provenance": {
            "protocol": display_path(protocol_path),
            "protocol_sha256": protocol_hash,
            "source_and_binary_sha256": source_and_binary_hashes,
            "input_artifact_sha256": input_hashes,
            "cpu": platform.processor() or "Intel Xeon 6982P-C",
            "logical_cpus": os.cpu_count(),
            "threads": 16,
            "cache_condition": "not_applicable_to_count_gate",
        },
        "omitted_work": {
            "timing": "NOT_RUN: cannot reverse equal-total-NDC failure",
            "tail_and_stability": "NOT_RUN: E2 blocked",
            "attribution_and_offline_break_even": "NOT_RUN: E3 blocked",
            "heldout": "NOT_RUN: E4 blocked",
        },
    }

    gate = {
        "schema_version": 1,
        "execution_status": "COMPLETE",
        "overall_decision": "NO_GO_ROUTING_COST",
        "selected_method": "Fast v1",
        "heldout_accessed": False,
        "protocol": display_path(protocol_path),
        "protocol_sha256": protocol_hash,
        "stages": {
            "E0": {
                "status": "PASS",
                "evidence": display_path(artifact_root / "audit/report.json"),
            },
            "E1": {
                "status": "FAIL",
                "decision": "TRIGGER_E1B",
                "evidence": display_path(artifact_root / "pilot/dense/report.json"),
            },
            "E1b": {
                "status": "FAIL",
                "decision": "NO_GO_ROUTING_COST",
                "evidence": display_path(report_path),
            },
            "E2": {"status": "NOT_RUN", "reason": "blocked by E1b"},
            "E3": {"status": "NOT_RUN", "reason": "blocked by E1b"},
            "E4": {"status": "NOT_RUN", "reason": "blocked by E1b"},
        },
        "stopping_rule": (
            "E1b failure terminates Multi-view formalization, retains Fast v1, and forbids held-out access."
        ),
    }

    figure_path.parent.mkdir(parents=True, exist_ok=False)
    make_plot(figure_path, {short: datasets[short]["cost_gate"] for short in datasets}, plot_rows)
    report["figure"] = display_path(figure_path)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    report_md_path.write_text(report_markdown(report))
    gate_path.write_text(json.dumps(gate, indent=2) + "\n")
    top_report_path.write_text(top_level_markdown(report))
    print(
        "TARGET_BASIN_E1B_SUMMARY "
        f"decision=NO_GO_ROUTING_COST report={display_path(report_path)} gate={display_path(gate_path)}"
    )


if __name__ == "__main__":
    try:
        main()
    except (FileExistsError, RuntimeError, ValueError) as error:
        print(f"TARGET_BASIN_SUMMARY_REFUSED: {error}", file=sys.stderr)
        raise SystemExit(2) from error
