"""Check this research delivery and seal its files, without running experiments."""

import ast
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
ROOT_DOCS = ["summary.md", "spec.md", "s-target.md", "s-experiment.md"]
CARD = ROOT / "experiment_history/126_qps_first_entry_theory.md"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    assert not (HERE / "seal.json").exists()
    locked = json.loads((HERE / "inputs.locked.json").read_text())
    router = json.loads((HERE / "reviews/router_state_facts.json").read_text())
    all_inputs = {**locked, **router["inputs"]}
    for name, digest in all_inputs.items():
        assert sha(ROOT / name) == digest, name
    primary = json.loads((HERE / "reviews/independent_verification.json").read_text())
    supplement = json.loads((HERE / "reviews/supplement_verification.json").read_text())
    assert primary["status"] == supplement["status"] == router["status"] == "PASS"
    assert len(primary["synthetic_checks"]) == 12
    assert len(primary["sensitivity_envelopes"]) == 4
    assert sum(r["combinations"] for r in primary["sensitivity_envelopes"]) == 2916
    assert sum(r["covered"] for r in supplement["historical_thresholds"]) == 6
    documents = {p: p.read_text() for p in HERE.glob("*.md")}
    documents.update({p: p.read_text() for p in (HERE / "reviews").glob("*.md")})
    documents[CARD] = CARD.read_text()
    preserved = []
    for name in ROOT_DOCS:
        old = (HERE / "source_before" / name).read_text()
        new = (ROOT / name).read_text()
        heading, _, previous_body = old.partition("\n\n")
        assert new.startswith(heading + "\n\n")
        assert new.endswith(previous_body), name
        documents[ROOT / name] = new[:-len(previous_body)]
        preserved.append(name)
    report = (HERE / "report.md").read_text()
    accounting = json.loads((HERE / "results_v2/accounting.json").read_text())
    discrete = json.loads((HERE / "results_v2/discrete_thresholds.json").read_text())
    assert discrete["status"] == "PASS" and len(discrete["comparisons"]) == 4
    for comparison in discrete["comparisons"]:
        for method, chosen in comparison["methods"].items():
            feasible = [row for row in accounting["points"] if row["dataset"] == comparison["dataset"]
                        and row["K"] == comparison["K"] and row["method"] == method and row["recall"] >= .9]
            expected = min(feasible, key=lambda row: row["time_us"])
            assert chosen["L"] == expected["L"] and chosen["recall"] == expected["recall"]
            assert abs(chosen["time_us"] - expected["time_us"]) < 1e-8
    for row in accounting["thresholds"]:
        if row["covered"]:
            for value in [row["baseline"]["time_us"], row["candidate"]["time_us"], row["baseline_budget_credit_us"]]:
                assert f"{value:.3f}" in report
    links = []
    for path, content in documents.items():
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", content):
            if target.startswith(("https://", "http://", "#")):
                continue
            target = target.split("#", 1)[0]
            resolved = (path.parent / target).resolve()
            if resolved != HERE / "state.json":
                assert resolved.is_file(), (str(path), target)
            links.append({"document": str(path.relative_to(ROOT)), "target": target})
    checked_sources = []
    for path in sorted((HERE / "src").glob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module.split(".")[0])
        assert imports <= sys.stdlib_module_names, (path, imports - sys.stdlib_module_names)
        assert not imports.intersection({"subprocess", "ctypes", "multiprocessing"})
        checked_sources.append(str(path.relative_to(HERE)))
    fresh_files = list(HERE.glob("*.md")) + list((HERE / "reviews").glob("*.md")) + list((HERE / "src").glob("*.py")) + [CARD]
    whitespace_errors = [(str(path), i) for path in fresh_files for i, line in enumerate(path.read_text().splitlines(), 1)
                         if line.rstrip() != line]
    assert not whitespace_errors, whitespace_errors
    checked_at = datetime.now(timezone.utc).isoformat()
    write_new(HERE / "reviews/delivery_checks.json", {
        "status": "PASS", "checked_utc": checked_at, "unchanged_consumed_inputs": all_inputs,
        "prior_root_document_bodies_preserved": preserved, "verified_local_links": links,
        "stdlib_only_sources_parsed": checked_sources, "new_file_whitespace_errors": whitespace_errors,
        "report_cost_cells_recovered": 12,
        "discrete_constraint_comparisons_verified": 4,
        "scope_note": "Existing worktree-wide git diff --check reports unrelated historical whitespace. No such files were changed; this check covers new research sources/documents and root additions.",
        "review_identity": "Same session, independently implemented arithmetic; not independent personnel"})
    write_new(HERE / "state.json", {
        "status": "RESEARCH_COMPLETE_NO_IMPLEMENTATION_GO", "completed_utc": checked_at,
        "deadline_utc": "2026-09-22T08:00:00+00:00", "deadline_timezone": "Asia/Shanghai",
        "scope": "Read-only evidence arithmetic, primary literature, conditional theory and candidate review",
        "defaults": {"WebVid": "GT10-soft-t1", "Yandex": "GT10-hard", "production": "E99"},
        "default_changed": False, "production_interface_changed": False,
        "new_searches": 0, "new_training": 0, "new_optimizer_steps": 0, "new_GT": 0,
        "new_graphs": 0, "new_query_timing": 0, "new_test_payload_reads": 0,
        "implementation_candidates": 0, "prioritized_unvalidated_hypotheses": 1,
        "candidate_A": "HOLD_MISSING_TARGET_STATE_RESPONSE_COST",
        "candidate_B": "DO_NOT_IMPLEMENT_NO_NEW_INFORMATION_CASE",
        "primary_analysis_wall_seconds": accounting["analysis_wall_seconds"],
        "primary_verification_wall_seconds": primary["analysis_wall_seconds"],
        "analysis_time_is_query_performance": False,
        "pending_jobs": [], "automatic_followup_experiment": False,
        "historical_record": str(CARD.relative_to(ROOT))})
    after = HERE / "source_after"
    after.mkdir(exist_ok=False)
    for name in ROOT_DOCS:
        shutil.copy2(ROOT / name, after / name)
    shutil.copy2(ROOT / "experiment_history/README.md", after / "experiment_history_README.md")
    protected = {str(path.relative_to(ROOT)): sha(path) for path in [CARD, ROOT / "experiment_history/README.md", *(ROOT / n for n in ROOT_DOCS)]}
    files = {str(path.relative_to(HERE)): sha(path) for path in sorted(HERE.rglob("*")) if path.is_file()}
    write_new(HERE / "seal.json", {"status": "SEALED", "created_utc": checked_at,
                                    "version_files": files, "root_delivery_files": protected})
    for name, digest in all_inputs.items():
        assert sha(ROOT / name) == digest
    print(json.dumps({"status": "PASS", "version_files": len(files), "local_links": len(links),
                      "root_original_bodies_preserved": len(preserved), "new_searches": 0,
                      "new_training": 0, "implementation_candidates": 0}))


if __name__ == "__main__":
    main()
