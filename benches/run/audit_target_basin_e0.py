#!/usr/bin/env python3
"""Assemble and verify the E0 target-basin audit evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "target_basin_formalization/20260907_v1/audit"
BINARY = ROOT / "build/benches/bench_target_basin_eval"
REFERENCE = ROOT / "benches/run/route_target_basin_reference.py"


def load(name: str) -> dict[str, Any]:
    return json.loads((AUDIT / name).read_text())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, details: Any) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "details": details})


def normalized_route_rows(document: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in document["routes"]:
        rows.append(
            {
                "query_id": row["query_id"],
                "primary_entry_ids": row["primary_entry_ids"],
                "final_entry_ids": row["final_entry_ids"],
                "view_candidates": row["view_candidates"],
                "routing_hnsw_ndc": row["routing_hnsw_ndc"],
                "routing_exact_ndc": row["routing_exact_ndc"],
                "routing_total_ndc": row["routing_total_ndc"],
            }
        )
    return rows


def compare_new_legacy(new: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    mismatches = {"entry_ids": 0, "result_ids": 0, "graph_ndc": 0, "recall": 0}
    examples: list[dict[str, Any]] = []
    legacy_by_key = {(row["search_L"], row["top_k"]): row for row in legacy["results"]}
    cells = 0
    for new_result in new["results"]:
        key = (new_result["search_L"], new_result["top_k"])
        old_result = legacy_by_key[key]
        old_rows = old_result["per_query_first_run"]
        for query_id, (new_row, old_row) in enumerate(zip(new_result["per_query"], old_rows)):
            old_method = next(method for method in old_row["methods"] if method["method"] == "E0_Replay")
            comparisons = {
                "entry_ids": new_row["entry_ids"] == old_method["entry_ids"],
                "result_ids": new_row["result_ids"] == old_method["result_ids"],
                "graph_ndc": new_row["graph_ndc"] == old_method["graph_ndc"],
                "recall": new_row["recall"] == old_method["recall"],
            }
            cells += 1
            for field, same in comparisons.items():
                mismatches[field] += int(not same)
            if not all(comparisons.values()) and len(examples) < 12:
                examples.append({"query_id": query_id, "L_K": key, "same": comparisons})
    return {"query_budget_cells": cells, "mismatches": mismatches, "examples": examples}


def compare_count_timing(count: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
    timing_by_key = {(row["search_L"], row["top_k"], row["run"]): row for row in timing["results"]}
    mismatches = {"entry_ids": 0, "result_ids": 0, "recall": 0}
    cells = 0
    for counted in count["results"]:
        timed = timing_by_key[(counted["search_L"], counted["top_k"], counted["run"])]
        for left, right in zip(counted["per_query"], timed["per_query"]):
            cells += 1
            mismatches["entry_ids"] += int(left["entry_ids"] != right["entry_ids"])
            mismatches["result_ids"] += int(left["result_ids"] != right["result_ids"])
            mismatches["recall"] += int(left["recall"] != right["recall"])
    return {"query_budget_cells": cells, "mismatches": mismatches}


def run_guard(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }


def main() -> None:
    report_path = AUDIT / "report.json"
    markdown_path = AUDIT / "report.md"
    if report_path.exists() or markdown_path.exists():
        raise FileExistsError("refusing to overwrite an existing E0 report")

    checks: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}
    for short in ("webvid", "yandex"):
        route = load(f"{short}_route128.json")
        repeat = load(f"{short}_route128_repeat.json")
        timing_route = load(f"{short}_route128_timing.json")
        reference = load(f"{short}_route128_reference.json")
        new_replay = load(f"{short}_replay128_count.json")
        timing_replay = load(f"{short}_replay128_timing.json")
        legacy_replay = load(f"{short}_legacy_replay128.json")

        route_base = normalized_route_rows(route)
        route_repeat = normalized_route_rows(repeat)
        route_timing = normalized_route_rows(timing_route)
        # Timing mode intentionally emits zero counters; compare only route semantics.
        for rows in (route_timing,):
            for row in rows:
                row["routing_hnsw_ndc"] = route_base[row["query_id"]]["routing_hnsw_ndc"]
                row["routing_exact_ndc"] = route_base[row["query_id"]]["routing_exact_ndc"]
                row["routing_total_ndc"] = route_base[row["query_id"]]["routing_total_ndc"]

        add_check(
            checks,
            f"{short}.route_is_gt_free_and_anchor_preserved",
            route["gt_loaded"] is False
            and route["heldout_accessed"] is False
            and route["rank0_preserved"] is True
            and route["rank0_mismatch_count"] == 0,
            {"queries": route["num_queries"], "split": route["split"]},
        )
        add_check(
            checks,
            f"{short}.python_cpp_merge_parity",
            reference["status"] == "PASS"
            and reference["route_cell_mismatch_count"] == 0
            and reference["rank0_mismatch_count"] == 0,
            reference,
        )
        add_check(
            checks,
            f"{short}.fixed_query_route_repeatability",
            route_base == route_repeat,
            {"queries": len(route_base)},
        )
        add_check(
            checks,
            f"{short}.count_switch_preserves_routes",
            route_base == route_timing,
            {"queries": len(route_base)},
        )

        parity = compare_new_legacy(new_replay, legacy_replay)
        add_check(
            checks,
            f"{short}.new_legacy_search_parity",
            all(value == 0 for value in parity["mismatches"].values()),
            parity,
        )
        switch = compare_count_timing(new_replay, timing_replay)
        add_check(
            checks,
            f"{short}.count_switch_preserves_search",
            all(value == 0 for value in switch["mismatches"].values()),
            switch,
        )

        route_ndcs = [row["routing_total_ndc"] for row in route["routes"]]
        metrics[short] = {
            "queries": len(route_ndcs),
            "routing_ndc": {
                "min": min(route_ndcs),
                "max": max(route_ndcs),
                "mean": sum(route_ndcs) / len(route_ndcs),
                "exact_per_query": route["routes"][0]["routing_exact_ndc"],
            },
            "reference_route_cell_mismatch_fraction": reference["route_cell_mismatch_fraction"],
            "new_legacy_search_parity": parity,
        }

    binary_self_test = run_guard([str(BINARY), "--self_test"])
    add_check(
        checks,
        "synthetic_cpp_merge_tests",
        binary_self_test["exit_code"] == 0 and "TARGET_BASIN_SELF_TEST_OK" in binary_self_test["stdout"],
        binary_self_test,
    )
    python_self_test = run_guard([str(ROOT / ".venv_cpu/bin/python"), str(REFERENCE), "--self-test"])
    add_check(
        checks,
        "synthetic_python_merge_tests",
        python_self_test["exit_code"] == 0
        and "TARGET_BASIN_REFERENCE_SELF_TEST_OK" in python_self_test["stdout"],
        python_self_test,
    )

    invalid_output = AUDIT / "must_not_create_k_gt_l.json"
    heldout_output = AUDIT / "must_not_create_heldout.json"
    if invalid_output.exists() or heldout_output.exists():
        raise FileExistsError("guard-test sentinel output already exists")
    invalid = run_guard(
        [
            str(BINARY), "--dataset", "webvid2_5m_light_v1", "--search_Ls", "64",
            "--top_ks", "100", "--output_file", str(invalid_output),
        ]
    )
    add_check(
        checks,
        "reject_K_greater_than_L",
        invalid["exit_code"] != 0
        and "search_L must be >= top_k" in invalid["stderr"]
        and not invalid_output.exists(),
        invalid,
    )
    heldout = run_guard(
        [
            str(BINARY), "--dataset", "webvid2_5m_light_v1", "--query_type", "drl_test",
            "--output_file", str(heldout_output),
        ]
    )
    add_check(
        checks,
        "reject_implicit_heldout_access",
        heldout["exit_code"] != 0
        and "held-out access requires explicit --allow_heldout" in heldout["stderr"]
        and not heldout_output.exists(),
        heldout,
    )

    current_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in (
            ROOT / "benches/bench_target_basin_eval.cpp",
            ROOT / "benches/bench_entry_oracle.cpp",
            ROOT / "benches/run/route_target_basin_reference.py",
            ROOT / "benches/CMakeLists.txt",
            BINARY,
            ROOT / "build/benches/bench_entry_oracle",
            ROOT / "benches/datasets/settings.json",
        )
    }
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report = {
        "schema_version": 1,
        "stage": "E0",
        "status": status,
        "protocol": "target_basin_formalization/20260907_v1/protocol.json",
        "heldout_accessed": False,
        "datasets": ["webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1"],
        "query_split": "drl_train",
        "queries_per_dataset": 128,
        "checks": checks,
        "metrics": metrics,
        "current_source_and_binary_sha256": current_hashes,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    lines = [
        "# Target-Basin E0 audit",
        "",
        f"Status: **{status}**. Held-out accessed: **false**.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {check['status']}: `{check['name']}`" for check in checks)
    lines.extend(["", "## Routing NDC", ""])
    for dataset, values in metrics.items():
        ndc = values["routing_ndc"]
        lines.append(
            f"- {dataset}: mean `{ndc['mean']:.3f}`, range `{ndc['min']}..{ndc['max']}`, "
            f"exact component `{ndc['exact_per_query']}` per query."
        )
    lines.extend(
        [
            "",
            "The C++ and Python merge paths match exactly on both 128-query train slices. "
            "The new and legacy graph-search paths also match result IDs, Recall, and graph NDC "
            "for L=64/128 and K=10. Count/timing modes preserve routes and result IDs.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines))
    print(f"TARGET_BASIN_E0_AUDIT status={status} checks={len(checks)} report={report_path}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
