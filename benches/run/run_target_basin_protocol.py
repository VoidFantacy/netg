#!/usr/bin/env python3
"""Stage-aware runner for the target-basin formalization protocol.

The only executable experiment stage in this frozen version is E1b.  E0 is
audited by ``audit_target_basin_e0.py`` and E1 is already frozen in the
protocol.  E2--E4 are deliberately guarded: they cannot run unless the
upstream gate says that proceeding is legal.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = ROOT / "target_basin_formalization/20260907_v1/protocol.json"
BINARY = ROOT / "build/benches/bench_target_basin_eval"
SUMMARIZER = ROOT / "benches/run/summarize_target_basin_e1b.py"
GRID = [16, 24, 32, 48, 64, 96, 128, 160, 200, 256, 400]

DATASETS: dict[str, dict[str, Any]] = {
    "webvid": {
        "dataset": "webvid2_5m_light_v1",
        "index": "indices/webvid2_5m_light_v1_index/acosp_nsg.json",
        "views": [
            "fast_entry_variants/webvid2_5m_light_v1_seed20260828",
            "fast_entry_variants/webvid2_5m_light_v1_seed20260829",
            "fast_entry_variants/webvid2_5m_light_v1_seed20260830",
        ],
    },
    "yandex": {
        "dataset": "yandex_t2i_official10M_ip_v1",
        "index": "indices/yandex_t2i_official10M_ip_v1_index/acosp_nsg.json",
        "views": [
            "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260828",
            "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260829",
            "fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260830",
        ],
    },
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def stage_state(protocol: dict[str, Any], stage: str) -> str:
    return str(protocol.get("stages", {}).get(stage, "NOT_RUN"))


def require_stage_allowed(protocol: dict[str, Any], stage: str) -> None:
    e0 = stage_state(protocol, "E0")
    e1 = stage_state(protocol, "E1")
    e1b = stage_state(protocol, "E1b")
    e2 = stage_state(protocol, "E2")
    e3 = stage_state(protocol, "E3")

    if stage == "E1b":
        if e0 != "PASS" or e1 != "FAIL_TRIGGER_E1B":
            raise RuntimeError(
                f"E1b blocked: requires E0=PASS and E1=FAIL_TRIGGER_E1B; got E0={e0}, E1={e1}"
            )
        return
    if stage == "E2":
        if e1 != "PASS" and e1b != "PASS":
            raise RuntimeError(f"E2 blocked by routing-cost gate: E1={e1}, E1b={e1b}")
        raise NotImplementedError("E2 runner is intentionally absent until its upstream gate passes")
    if stage == "E3":
        if e2 != "GO_TO_ATTRIBUTION":
            raise RuntimeError(f"E3 blocked by stability gate: E2={e2}")
        raise NotImplementedError("E3 runner is intentionally absent until its upstream gate passes")
    if stage == "E4":
        if e3 != "GO_TO_HELDOUT":
            raise RuntimeError(f"E4 blocked by attribution gate: E3={e3}")
        raise NotImplementedError("E4 runner is intentionally absent until its upstream gate passes")
    raise ValueError(f"unsupported stage: {stage}")


def common_command(short: str, output_file: Path) -> list[str]:
    cfg = DATASETS[short]
    command = [
        str(BINARY),
        "--dataset", str(cfg["dataset"]),
        "--index_file", str(cfg["index"]),
        "--query_type", "drl_train",
        "--max_queries", "10000",
        "--top_ks", "10",
        "--num_runs", "1",
        "--threads", "16",
    ]
    for view_number, directory in enumerate(cfg["views"], start=1):
        command.extend(
            [
                f"--view{view_number}_hubs",
                f"{directory}/qgt_gt_basin_prototype_hubs.bin",
                f"--view{view_number}_ids",
                f"{directory}/qgt_cover_hub_ids.bin",
            ]
        )
    command.extend(["--output_file", str(output_file)])
    return command


def evaluator_command(
    short: str,
    output_file: Path,
    *,
    method: str,
    backend: str,
    search_ls: list[int] | None = None,
    route_only: bool = False,
) -> list[str]:
    command = common_command(short, output_file)
    command.extend(["--method", method, "--measurement", "count", "--router_backend", backend])
    if search_ls is not None:
        command.extend(["--search_Ls", ",".join(map(str, search_ls))])
    if route_only:
        command.extend(["--route_only", "--export_route_details"])
    return command


def run(command: list[str], *, plan_only: bool) -> None:
    printable = " ".join(command)
    if plan_only:
        print(printable)
        return
    print(f"TARGET_BASIN_RUN command={printable}", flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def result_summaries(path: Path) -> list[dict[str, Any]]:
    document = load_json(path)
    return [
        {
            "search_L": int(row["search_L"]),
            "total_ndc": float(row["mean_total_ndc"]),
            "recall": float(row["mean_recall"]),
        }
        for row in document["results"]
    ]


def bracket(rows: list[dict[str, Any]], budget: float) -> tuple[dict[str, Any], dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: row["search_L"])
    lower = [row for row in ordered if row["total_ndc"] <= budget]
    upper = [row for row in ordered if row["total_ndc"] > budget]
    if not lower or not upper:
        raise RuntimeError(f"cost grid does not bracket budget {budget}")
    return max(lower, key=lambda row: row["search_L"]), min(upper, key=lambda row: row["search_L"])


def midpoint(lower: dict[str, Any], upper: dict[str, Any]) -> int:
    value = (int(lower["search_L"]) + int(upper["search_L"])) // 2
    if value in (int(lower["search_L"]), int(upper["search_L"])):
        raise RuntimeError("integer L bracket cannot be refined further")
    return value


def run_e1b(output_root: Path, *, plan_only: bool) -> None:
    hnsw_dir = output_root / "pilot/hnsw"
    if not plan_only:
        if output_root.exists():
            raise FileExistsError(f"refusing to overwrite output root: {output_root}")
        hnsw_dir.mkdir(parents=True)

    for short in DATASETS:
        run(
            evaluator_command(
                short,
                hnsw_dir / f"{short}_dense_route10k_count.json",
                method="ensemble",
                backend="dense",
                route_only=True,
            ),
            plan_only=plan_only,
        )
        run(
            evaluator_command(
                short,
                hnsw_dir / f"{short}_hnsw_route10k_count.json",
                method="ensemble",
                backend="hnsw_all",
                route_only=True,
            ),
            plan_only=plan_only,
        )
        run(
            evaluator_command(
                short,
                hnsw_dir / f"{short}_fast10k_count.json",
                method="fast",
                backend="dense",
                search_ls=[64, 128],
            ),
            plan_only=plan_only,
        )
        run(
            evaluator_command(
                short,
                hnsw_dir / f"{short}_hnsw10k_count_grid.json",
                method="ensemble",
                backend="hnsw_all",
                search_ls=GRID,
            ),
            plan_only=plan_only,
        )

        if plan_only:
            print(
                f"# {short}: refinement rounds are chosen only from measured cost brackets; "
                "at most two rounds, triggered when lower-point slack exceeds 2%."
            )
            continue

        fast_rows = result_summaries(hnsw_dir / f"{short}_fast10k_count.json")
        rows = result_summaries(hnsw_dir / f"{short}_hnsw10k_count_grid.json")
        budgets = [row["total_ndc"] for row in sorted(fast_rows, key=lambda row: row["search_L"])]
        for round_number in (1, 2):
            refine_ls: list[int] = []
            for budget in budgets:
                lower, upper = bracket(rows, budget)
                slack_fraction = (budget - lower["total_ndc"]) / budget
                if slack_fraction > 0.02:
                    candidate = midpoint(lower, upper)
                    if candidate not in refine_ls and all(row["search_L"] != candidate for row in rows):
                        refine_ls.append(candidate)
            if not refine_ls:
                break
            refine_path = hnsw_dir / f"{short}_hnsw10k_count_refine{round_number}.json"
            run(
                evaluator_command(
                    short,
                    refine_path,
                    method="ensemble",
                    backend="hnsw_all",
                    search_ls=sorted(refine_ls),
                ),
                plan_only=False,
            )
            rows.extend(result_summaries(refine_path))

    if plan_only:
        print(f"{sys.executable} {SUMMARIZER} --artifact-root {output_root}")
        return
    subprocess.run(
        [sys.executable, str(SUMMARIZER), "--artifact-root", str(output_root)],
        cwd=ROOT,
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("E1b", "E2", "E3", "E4"), required=True)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument(
        "--output-root",
        type=Path,
        help="New, non-existent artifact root; required for --execute E1b",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="Print the frozen E1b plan without writing")
    mode.add_argument("--execute", action="store_true", help="Execute the requested stage")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    protocol = load_json(args.protocol.resolve())
    require_stage_allowed(protocol, args.stage)
    if args.stage != "E1b":
        raise AssertionError("unreachable: allowed downstream stage has no runner yet")
    if args.output_root is None:
        if args.execute:
            raise ValueError("--output-root is required with --execute")
        output_root = ROOT / "target_basin_formalization/REPRODUCTION_ROOT"
    else:
        output_root = args.output_root.resolve()
    run_e1b(output_root, plan_only=args.plan)


if __name__ == "__main__":
    try:
        main()
    except (FileExistsError, NotImplementedError, RuntimeError, ValueError) as error:
        print(f"TARGET_BASIN_STAGE_REFUSED: {error}", file=sys.stderr)
        raise SystemExit(2) from error
