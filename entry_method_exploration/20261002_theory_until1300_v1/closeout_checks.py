#!/usr/bin/env python3
"""Verify research artifacts and frozen inputs; never execute research/performance tools."""
import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
TZ = timezone(timedelta(hours=8))


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def read(name):
    return json.loads((ROOT / name).read_text())


def require(condition, detail):
    if not condition:
        raise AssertionError(detail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    now = datetime.now(TZ)
    state = read("state.json")
    if args.final:
        require(now >= datetime.fromisoformat(state["deadline_local"]), "deadline not reached")
        require(state["status"] == "COMPLETED_THEORY_ONLY_NO_DEFAULT_CHANGE", "research not closed")
    require(not state["default_changed"], "default changed")
    require(not state["historical_campaign_resumed"], "historical campaign resumed")
    for name in ("new_real_ANN_calls", "new_NSG_calls", "new_GT_queries", "new_training_runs", "new_graphs", "new_performance_points", "new_query_vectors_read"):
        require(state[name] == 0, name)
    old_root = ROOT.parent / "20260930_theory_until2200_v1"
    for name in ("state.json", "user_pause.json"):
        old_state = json.loads((old_root / name).read_text())
        require(old_state["status"] == "PAUSED_BY_USER", "old pause state changed")
        require(old_state["active_process"] is None, "old active process declared")

    before = read("source_before_identity.json")
    for name, expected in before.items():
        got = identity(ROOT / "source_before" / name)
        require(got == {"bytes": expected["size"], "sha256": expected["sha256"]}, "source-before drift: " + name)
    require(identity(REPO / "AGENTS.md")["sha256"] == before["AGENTS.md"]["sha256"], "AGENTS drift")

    frozen = {}
    for manifest in (read("bucket_input_identity.json"), read("response_class_input_identity.json")["files"]):
        for name, expected in manifest.items():
            if name in frozen:
                require(frozen[name] == expected, "input manifests disagree: " + name)
            frozen[name] = expected
    for name, expected in frozen.items():
        require(identity(Path(name)) == expected, "frozen input drift: " + name)
    response_audit = read("response_class_independent_audit.json")
    for name, expected in response_audit["control_identities"].items():
        require(identity(Path(name)) == expected, "independent control drift: " + name)

    require(read("bucket_independent_audit.json")["status"] == "PASS", "bucket audit")
    require(response_audit["status"] == "PASS_INDEPENDENT_STDLIB_OLD_RESPONSE_CLASS_AUDIT", "response audit")
    require(response_audit["all_main_fields_compared"] == 828, "response audit field count")
    for artifact, source, field in (
        ("search_effect_math_check.json", "search_effect_math_check.py", "source_sha256"),
        ("algebra_checks.json", "algebra_checks.py", "source_sha256"),
        ("response_class_check.json", "response_class_check.py", "script_sha256"),
        ("response_class_check.json", "response_equivalence_protocol.md", "protocol_sha256"),
    ):
        require(read(artifact)[field] == identity(ROOT / source)["sha256"], "source/result drift: " + source)
    require(read("search_effect_math_check.json")["status"] == "PURE_SYNTHETIC_MATHEMATICAL_CHECK_PASS", "math status")
    require(read("algebra_checks.json")["status"] == "PASS", "algebra status")

    syntax_checked = []
    for path in sorted(ROOT.glob("*.py")):
        ast.parse(path.read_text(), filename=str(path))
        syntax_checked.append(path.name)
    json_checked = []
    for path in sorted(ROOT.glob("*.json")):
        json.loads(path.read_text())
        json_checked.append(path.name)

    papers = read("literature_manifest.json")["papers"]
    expected_papers = state.get("primary_papers_read", 17)
    require(len(papers) == expected_papers, "literature manifest count")
    require(len({p["source"] for p in papers}) == expected_papers, "duplicate literature source")
    for paper in papers:
        require(paper["source"].startswith("https://"), "primary URL missing")
        require(bool(paper["read"]), "read scope missing")
        for note in paper["note"].split(";"):
            require((ROOT / note.strip()).is_file(), "literature note missing")

    checked_links = 0
    card = REPO / "experiment_history/167_theory_search_response_access_cost.md"
    docs = [*sorted(ROOT.glob("*.md")), card]
    for path in docs:
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            target = target.strip().strip("<>")
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("#"):
                continue
            local = re.sub(r":\d+$", "", target.split("#", 1)[0].split("?", 1)[0])
            if local:
                require((path.parent / local).exists(), "broken research link: " + str(path) + " -> " + target)
                checked_links += 1
    for path in (REPO / "summary.md", REPO / "spec.md", REPO / "s-target.md", REPO / "s-experiment.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            if "20261002_theory_until1300_v1" in target or "167_theory_search_response_access_cost" in target:
                require((path.parent / target.split("#", 1)[0]).exists(), "broken new root handoff link")
                checked_links += 1

    total_bytes = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    require(total_bytes < state["bytes_cap"], "research bytes cap exceeded")
    result = {
        "status": "PASS_FINAL_RESEARCH_CLOSEOUT" if args.final else "PASS_PREFLIGHT_RESEARCH_CLOSEOUT",
        "checked_local": now.isoformat(timespec="seconds"),
        "scope": "Artifact syntax, local links, identities and declared research scope only; no native execution or new performance validation.",
        "source_before_files_verified": len(before),
        "union_frozen_input_files_verified": len(frozen),
        "response_independent_controls_verified": len(response_audit["control_identities"]),
        "python_syntax_checked": syntax_checked,
        "json_documents_checked": json_checked,
        "primary_papers_manifested": len(papers),
        "local_links_checked": checked_links,
        "research_bytes_before_closeout_write": total_bytes,
        "bytes_cap": state["bytes_cap"],
        "all_new_real_search_training_graph_GT_and_performance_counts_zero": True,
        "default_changed": False,
        "historical_campaign_state": "PAUSED_BY_USER",
        "performance_objective_achieved": False,
    }
    output = ROOT / ("closeout_checks.json" if args.final else "closeout_preflight.json")
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if args.final:
        paths = sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "identity.json")
        artifacts = {str(p.relative_to(ROOT)): identity(p) for p in paths}
        handoff = {str(p.relative_to(REPO)): identity(p) for p in [REPO / "summary.md", REPO / "spec.md", REPO / "s-target.md", REPO / "s-experiment.md", card]}
        seal = {
            "status": "SEALED_THEORY_ONLY_NO_DEFAULT_CHANGE",
            "sealed_local": datetime.now(TZ).isoformat(timespec="seconds"),
            "artifacts": artifacts,
            "root_handoff_documents": handoff,
            "seal_self_excluded": True,
            "reopen_requires_new_authorization": "New real experiments were not authorized or run in this research session.",
        }
        (ROOT / "identity.json").write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if not isinstance(v, list)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
