#!/usr/bin/env python3
"""Final, non-destructive consistency audit for the terminal target-basin run."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT_ROOT = ROOT / "target_basin_formalization/20260907_v1"
BINARY = ROOT / "build/benches/bench_target_basin_eval"
PYTHON = ROOT / ".venv_cpu/bin/python"
RUNNER = ROOT / "benches/run/run_target_basin_protocol.py"
SUMMARIZER = ROOT / "benches/run/summarize_target_basin_e1b.py"


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def normalized_routes(document: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for route in document["routes"]:
        normalized.append(
            {
                "query_id": route["query_id"],
                "primary_entry_ids": route["primary_entry_ids"],
                "final_entry_ids": route["final_entry_ids"],
                "view_candidates": route["view_candidates"],
                "routing_hnsw_ndc": route["routing_hnsw_ndc"],
                "routing_exact_ndc": route["routing_exact_ndc"],
                "routing_total_ndc": route["routing_total_ndc"],
            }
        )
    return normalized


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, details: Any) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "details": details})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ARTIFACT_ROOT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact_root = args.artifact_root.resolve()
    output_json = artifact_root / "audit/completion_report.json"
    output_md = artifact_root / "audit/completion_report.md"
    if output_json.exists() or output_md.exists():
        raise FileExistsError("refusing to overwrite completion audit")

    protocol_path = artifact_root / "protocol.json"
    gate_path = artifact_root / "gate.json"
    e0_path = artifact_root / "audit/report.json"
    e1_path = artifact_root / "pilot/dense/report.json"
    e1b_path = artifact_root / "pilot/hnsw/report.json"
    protocol = load_json(protocol_path)
    gate = load_json(gate_path)
    e0 = load_json(e0_path)
    e1 = load_json(e1_path)
    e1b = load_json(e1b_path)
    checks: list[dict[str, Any]] = []

    expected_stages = {
        "E0": "PASS",
        "E1": "FAIL_TRIGGER_E1B",
        "E1b": "NO_GO_ROUTING_COST",
        "E2": "NOT_RUN",
        "E3": "NOT_RUN",
        "E4": "NOT_RUN",
    }
    add_check(
        checks,
        "protocol_terminal_stage_state",
        protocol["stages"] == expected_stages and protocol["heldout_accessed"] is False,
        protocol["stages"],
    )
    add_check(
        checks,
        "gate_terminal_decision",
        gate["execution_status"] == "COMPLETE"
        and gate["overall_decision"] == "NO_GO_ROUTING_COST"
        and gate["selected_method"] == "Fast v1"
        and gate["heldout_accessed"] is False,
        {
            "execution_status": gate["execution_status"],
            "decision": gate["overall_decision"],
            "selected_method": gate["selected_method"],
        },
    )
    actual_protocol_hash = sha256(protocol_path)
    add_check(
        checks,
        "protocol_hash_bound_to_reports",
        gate["protocol_sha256"] == actual_protocol_hash
        and e1b["provenance"]["protocol_sha256"] == actual_protocol_hash,
        {"actual_sha256": actual_protocol_hash},
    )
    add_check(
        checks,
        "stage_evidence_consistent",
        e0["status"] == "PASS"
        and e1["status"] == "FAIL"
        and e1["decision"] == "TRIGGER_E1B"
        and e1b["artifact_validation"] == "PASS"
        and e1b["method_gate"] == "FAIL"
        and e1b["decision"] == "NO_GO_ROUTING_COST",
        {
            "E0": e0["status"],
            "E1": f"{e1['status']}/{e1['decision']}",
            "E1b": f"{e1b['method_gate']}/{e1b['decision']}",
        },
    )

    recorded_hashes = e1b["provenance"]["source_and_binary_sha256"]
    actual_hashes = {name: sha256(ROOT / name) for name in recorded_hashes}
    mismatches = {
        name: {"recorded": recorded_hashes[name], "actual": actual_hashes[name]}
        for name in recorded_hashes
        if recorded_hashes[name] != actual_hashes[name]
    }
    add_check(checks, "source_and_binary_hashes_current", not mismatches, mismatches)

    for short in ("webvid", "yandex"):
        prior = load_json(artifact_root / f"audit/{short}_route128_post_backend.json")
        current = load_json(artifact_root / f"audit/{short}_route128_final.json")
        same = normalized_routes(prior) == normalized_routes(current)
        safe = (
            current["split"] == "drl_train"
            and current["gt_loaded"] is False
            and current["heldout_accessed"] is False
            and current["rank0_preserved"] is True
            and current["rank0_mismatch_count"] == 0
        )
        add_check(
            checks,
            f"{short}.current_binary_route_regression",
            same and safe,
            {"queries": current["num_queries"], "semantic_match": same, "heldout_accessed": False},
        )

    evaluator_test = run([str(BINARY), "--self_test"])
    add_check(
        checks,
        "evaluator_self_test",
        evaluator_test.returncode == 0 and "TARGET_BASIN_SELF_TEST_OK" in evaluator_test.stdout,
        {"exit_code": evaluator_test.returncode},
    )

    e2_guard = run([str(PYTHON), str(RUNNER), "--stage", "E2", "--plan"])
    add_check(
        checks,
        "runner_blocks_E2_after_no_go",
        e2_guard.returncode == 2 and "E2 blocked by routing-cost gate" in e2_guard.stderr,
        {"exit_code": e2_guard.returncode, "stderr": e2_guard.stderr.strip()},
    )
    overwrite_guard = run(
        [
            str(PYTHON),
            str(RUNNER),
            "--stage",
            "E1b",
            "--execute",
            "--output-root",
            str(artifact_root),
        ]
    )
    add_check(
        checks,
        "runner_refuses_existing_output_root",
        overwrite_guard.returncode == 2 and "refusing to overwrite output root" in overwrite_guard.stderr,
        {"exit_code": overwrite_guard.returncode, "stderr": overwrite_guard.stderr.strip()},
    )
    summary_guard = run([str(PYTHON), str(SUMMARIZER), "--artifact-root", str(artifact_root)])
    add_check(
        checks,
        "summarizer_refuses_existing_outputs",
        summary_guard.returncode == 2 and "refusing to overwrite output" in summary_guard.stderr,
        {"exit_code": summary_guard.returncode, "stderr": summary_guard.stderr.strip()},
    )

    heldout_scan = run(["rg", "-l", '"heldout_accessed"\\s*:\\s*true', str(artifact_root)])
    heldout_directory = artifact_root / "heldout"
    add_check(
        checks,
        "no_heldout_artifact_or_access_flag",
        heldout_scan.returncode == 1 and not heldout_directory.exists(),
        {
            "rg_exit_code": heldout_scan.returncode,
            "matching_files": heldout_scan.stdout.splitlines(),
            "heldout_directory_exists": heldout_directory.exists(),
        },
    )

    doc_expectations = {
        "spec.md": ["NO_GO_ROUTING_COST", "stage runner 会拒绝"],
        "summary.md": ["NO_GO_ROUTING_COST", "四点全 FAIL"],
        "s-target.md": ["NO_GO_ROUTING_COST", "execution status 为 `COMPLETE`"],
    }
    missing_doc_text: dict[str, list[str]] = {}
    for name, needles in doc_expectations.items():
        content = (ROOT / name).read_text()
        missing = [needle for needle in needles if needle not in content]
        if missing:
            missing_doc_text[name] = missing
    add_check(checks, "handoff_documents_synchronized", not missing_doc_text, missing_doc_text)

    cost_failures = []
    for short in ("webvid", "yandex"):
        for target_name, target in e1b["datasets"][short]["cost_gate"]["targets"].items():
            if target["status"] != "FAIL" or target["recall_delta"] >= 0:
                cost_failures.append(f"{short}/{target_name}")
    add_check(
        checks,
        "four_equal_ndc_points_fail_as_reported",
        not cost_failures
        and e1b["gate"]["equal_total_ndc"] == "FAIL"
        and e1b["gate"]["equal_batch_wall"] == "NOT_RUN",
        {"unexpected_points": cost_failures},
    )

    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    disk = shutil.disk_usage(artifact_root)
    current_hashes = {
        relative(Path(__file__)): sha256(Path(__file__)),
        relative(BINARY): sha256(BINARY),
        relative(RUNNER): sha256(RUNNER),
        relative(SUMMARIZER): sha256(SUMMARIZER),
        relative(protocol_path): actual_protocol_hash,
        relative(gate_path): sha256(gate_path),
        relative(e1b_path): sha256(e1b_path),
    }
    report = {
        "schema_version": 1,
        "stage": "completion_audit",
        "status": status,
        "execution_status": gate["execution_status"],
        "decision": gate["overall_decision"],
        "heldout_accessed": False,
        "checks": checks,
        "current_sha256": current_hashes,
        "resources": {
            "data_available_bytes": disk.free,
            "data_available_gib": disk.free / (1024**3),
        },
    }
    output_json.write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Target-Basin completion audit",
        "",
        f"Status: **{status}**. Execution: **{gate['execution_status']}**. "
        f"Decision: **{gate['overall_decision']}**. Held-out accessed: **false**.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {check['status']}: `{check['name']}`" for check in checks)
    lines.append("")
    output_md.write_text("\n".join(lines))
    print(f"TARGET_BASIN_COMPLETION_AUDIT status={status} checks={len(checks)}")
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except FileExistsError as error:
        print(f"TARGET_BASIN_COMPLETION_AUDIT_REFUSED: {error}", file=sys.stderr)
        raise SystemExit(2) from error
