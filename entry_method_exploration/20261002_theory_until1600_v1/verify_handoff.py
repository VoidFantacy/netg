"""Administrative identity, JSON, and local-link checks only. No math/data tests."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
MORNING = HERE.parent / "20261002_theory_until1300_v1"
ROOT_HANDOFF = [
    "AGENTS.md", "summary.md", "spec.md", "s-target.md", "s-experiment.md",
    "experiment_history/168_theory_proxy_information_local_certificate.md",
    "experiment_history/README.md",
]
EXCLUDE_SEAL = {"seal.json", "seal_verification.json"}


def identity(path: Path) -> dict:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": h.hexdigest()}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def administrative_checks(verify_historical: bool = False) -> dict:
    errors = []
    before = load(HERE / "source_before_identity.json")
    for name, expected in before.items():
        if identity(HERE / "source_before" / name) != expected:
            errors.append("source_before identity changed: " + name)
    if not verify_historical and identity(PROJECT / "AGENTS.md") != before["AGENTS.md"]:
        errors.append("AGENTS.md changed")

    review = load(HERE / "proof_review_completion.json")
    for name, frozen_identity in review["owned_document_identities"].items():
        expected = {key: frozen_identity[key] for key in ["bytes", "sha256"]}
        if identity(HERE / name) != expected:
            errors.append("reviewed-owned identity changed: " + name)

    handoff_path = HERE / "root_handoff_identity.json"
    if handoff_path.exists():
        handoff = load(handoff_path)
        if set(handoff["files"]) != set(ROOT_HANDOFF):
            errors.append("root handoff snapshot inventory changed")
        for name, record in handoff["files"].items():
            expected = record["identity"]
            if identity(HERE / record["snapshot"]) != expected:
                errors.append("root handoff snapshot identity changed: " + name)
            if not verify_historical and identity(PROJECT / name) != expected:
                errors.append("current root differs from closing snapshot: " + name)

    frozen = load(HERE / "morning_frozen_identity.json")
    morning_seal = identity(MORNING / "identity.json")
    if morning_seal["sha256"] != frozen["morning_seal_sha256"]:
        errors.append("morning identity.json changed")
    for name, expected in frozen["artifacts"].items():
        if identity(MORNING / name) != expected:
            errors.append("morning artifact changed: " + name)
    morning_files = {str(p.relative_to(MORNING)) for p in MORNING.rglob("*") if p.is_file()}
    expected_morning_files = set(frozen["artifacts"]) | {"identity.json"}
    if morning_files != expected_morning_files:
        errors.append("morning file inventory changed")

    state = load(HERE / "state.json")
    counters = {k: v for k, v in state.items() if k.startswith("new_")}
    if any(value != 0 for value in counters.values()):
        errors.append("declared no-experiment counters are not zero")
    for key in ["default_changed", "old_campaign_resumed", "morning_research_reopened", "experiment_execution_authorized", "performance_goal_achieved"]:
        if state.get(key) is not False:
            errors.append("scope flag changed: " + key)
    if state.get("latest_performance_history") != 166:
        errors.append("latest performance history changed")

    files = [p for p in HERE.rglob("*") if p.is_file()]
    total_bytes = sum(p.stat().st_size for p in files)
    if total_bytes >= state["bytes_cap"]:
        errors.append("version byte cap exceeded")
    for path in files:
        if path.suffix not in {".md", ".json", ".py"}:
            errors.append("unexpected new-version artifact type: " + str(path.relative_to(HERE)))
        if path.suffix == ".py" and path.name != "verify_handoff.py":
            errors.append("unexpected executable artifact: " + str(path.relative_to(HERE)))
        if path.suffix == ".json":
            load(path)

    documents = [(path, path.parent) for path in HERE.glob("*.md")]
    card_path = (HERE / "source_after" / ROOT_HANDOFF[-2]) if verify_historical else (PROJECT / ROOT_HANDOFF[-2])
    documents.append((card_path, (PROJECT / ROOT_HANDOFF[-2]).parent))
    checked_local_links = 0
    for path, original_link_base in documents:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if target.startswith(("http:", "https:", "mailto:", "#")):
                continue
            target = target.strip("<>").split("#", 1)[0]
            target = re.sub(r":\d+$", "", target)
            dest = Path(target) if target.startswith("/") else original_link_base / target
            checked_local_links += 1
            if not dest.exists():
                errors.append("missing local link: " + str(path.relative_to(PROJECT)) + " -> " + target)

    return {
        "status": "PASS" if not errors else "FAIL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "file_identity_json_local_links_only_no_math_or_array_diagnostics",
        "source_before_files_verified": len(before),
        "reviewed_owned_documents_verified": len(review["owned_document_identities"]),
        "root_handoff_snapshot_present": handoff_path.exists(),
        "root_handoff_live_files_are_historical_after_seal": True,
        "morning_artifacts_verified": len(frozen["artifacts"]),
        "morning_seal_unchanged": morning_seal["sha256"] == frozen["morning_seal_sha256"],
        "morning_root_handoff_hashes_are_historical_not_current": True,
        "checked_local_links": checked_local_links,
        "version_tree_bytes_before_this_check_output": total_bytes,
        "bytes_cap": state["bytes_cap"],
        "declared_no_experiment_counters": counters,
        "counters_are_scope_records_not_independent_execution_measurements": True,
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--verify-seal", action="store_true")
    args = parser.parse_args()
    if args.seal and args.verify_seal:
        parser.error("choose one administrative mode")
    if not args.verify_seal and (HERE / "seal.json").exists():
        raise SystemExit("seal already exists; use --verify-seal to keep sealed checks unchanged")
    if args.seal:
        state = load(HERE / "state.json")
        if state["status"] != "COMPLETED_THEORY_ONLY_NO_EXPERIMENTS":
            raise SystemExit("cannot seal an active stage")
        if datetime.fromisoformat(state["completed_local"]) < datetime.fromisoformat(state["deadline_local"]):
            raise SystemExit("cannot close before the authorized research deadline")
        if datetime.now(timezone.utc) < datetime.fromisoformat(state["deadline_local"]):
            raise SystemExit("current time is before the authorized research deadline")
        closing_files = {}
        for name in ROOT_HANDOFF:
            snapshot = HERE / "source_after" / name
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            snapshot.write_bytes((PROJECT / name).read_bytes())
            closing_files[name] = {"snapshot": str(snapshot.relative_to(HERE)), "identity": identity(snapshot)}
        dump(HERE / "root_handoff_identity.json", {
            "files": closing_files,
            "root_live_identities_are_historical_after_seal": True,
            "completed_local": state["completed_local"],
        })
    checks = administrative_checks(verify_historical=args.verify_seal)
    if checks["status"] != "PASS":
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    if args.verify_seal:
        seal = load(HERE / "seal.json")
        failures = [name for name, expected in seal["artifacts"].items() if identity(PROJECT / name) != expected]
        current_inventory = {str(p.relative_to(PROJECT)) for p in HERE.rglob("*")
                             if p.is_file() and str(p.relative_to(HERE)) not in EXCLUDE_SEAL}
        if current_inventory != set(seal["artifacts"]):
            failures.append("sealed version file inventory changed")
        result = {"status": "PASS" if not failures else "FAIL", "sealed_artifacts_verified": len(seal["artifacts"]),
                  "morning_artifacts_verified": checks["morning_artifacts_verified"], "errors": failures,
                  "scope": checks["scope"], "checked_at_utc": checks["checked_at_utc"]}
        dump(HERE / "seal_verification.json", result)
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(bool(failures))
    dump(HERE / "document_checks.json", checks)
    if args.seal:
        paths = [p for p in HERE.rglob("*") if p.is_file() and str(p.relative_to(HERE)) not in EXCLUDE_SEAL]
        artifacts = {str(p.relative_to(PROJECT)): identity(p) for p in sorted(paths)}
        dump(HERE / "seal.json", {"status": "COMPLETED_THEORY_ONLY_NO_EXPERIMENTS", "artifacts": artifacts,
             "scope": checks["scope"], "completed_local": state["completed_local"],
             "root_handoff_identity": "root_handoff_identity.json",
             "root_live_files_may_change_after_this_historical_snapshot": True,
             "morning_seal_sha256": load(HERE / "morning_frozen_identity.json")["morning_seal_sha256"]})
    print(json.dumps({"status": checks["status"], "morning_artifacts_verified": checks["morning_artifacts_verified"],
                      "checked_local_links": checks["checked_local_links"], "sealed": args.seal}, ensure_ascii=False))


if __name__ == "__main__":
    main()
