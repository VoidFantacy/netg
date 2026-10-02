"""Administrative identity/link/scope verification only; no mathematical checks."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone, timedelta

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ROOT_FILES = [
    "AGENTS.md", "summary.md", "spec.md", "s-target.md", "s-experiment.md",
    "experiment_history/README.md", "experiment_history/169_gt10_algorithm_paper_theory.md",
]
EXCLUDED = {"seal.json", "delivery_checks.json"}


def read_json(path):
    return json.loads(path.read_text())


def identity(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def verify_manifest(folder, expected):
    actual_names = {str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()}
    assert actual_names == set(expected), f"inventory mismatch: {folder}"
    for name, wanted in expected.items():
        assert identity(folder / name) == wanted, f"identity mismatch: {folder / name}"
    return len(expected)


def current_inventory():
    return {
        str(path.relative_to(HERE)): identity(path)
        for path in sorted(HERE.rglob("*"))
        if path.is_file() and path.name not in EXCLUDED
    }


def check_links():
    documents = list(HERE.glob("*.md")) + [ROOT / ROOT_FILES[-1]]
    checked = 0
    for document in documents:
        for target in re.findall(r"\[[^\]]*\]\(([^\n]*?)\)", document.read_text()):
            target = target.strip().strip("<>")
            if not target or target.startswith(("#", "http:", "https:", "mailto:", "app:")):
                continue
            target = target.split("#", 1)[0]
            target = re.sub(r":\d+$", "", target)
            resolved = document.parent / target
            assert resolved.exists(), f"broken link: {document.name} -> {target}"
            checked += 1
    for name in ROOT_FILES[1:]:
        document = ROOT / name
        for target in re.findall(r"\[[^\]]*\]\(([^\n]*?)\)", document.read_text()):
            if "20261002_gt10_paper_theory_v1" not in target and "169_gt10_algorithm_paper_theory" not in target:
                continue
            target = re.sub(r":\d+$", "", target.split("#", 1)[0])
            assert (document.parent / target).exists(), f"new root link missing: {name}"
            checked += 1
    return checked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--verify-seal", action="store_true")
    arguments = parser.parse_args()
    assert not (arguments.seal and arguments.verify_seal)
    state = read_json(HERE / "state.json")
    assert state["status"] == "COMPLETED_GT10_THEORY_PAPER_FRAMEWORK_NO_EXPERIMENTS"
    assert state["publication_target"] == "CCF_B_JOURNAL"
    assert not state["experiment_execution_authorized"]
    assert not state["default_changed"] and not state["old_campaign_resumed"]
    assert not state["publication_acceptance_established"]
    for key, value in state.items():
        if key.startswith("new_"):
            assert value == 0, f"declared scope mismatch: {key}"
    before = read_json(HERE / "source_before_identity.json")
    before_count = verify_manifest(HERE / "source_before", before)
    protected = {}
    for version in ["20261002_theory_until1300_v1", "20261002_theory_until1600_v1"]:
        protected[version] = verify_manifest(
            HERE.parent / version, read_json(HERE / f"{version}_frozen_identity.json")
        )
    local_links = check_links()
    for path in HERE.rglob("*.json"):
        read_json(path)
    assert identity(ROOT / "AGENTS.md") == before["AGENTS.md"]
    size = sum(path.stat().st_size for path in HERE.rglob("*") if path.is_file())
    assert size < state["bytes_cap"]
    if arguments.seal:
        assert not (HERE / "seal.json").exists(), "do not overwrite historical seal"
        for name in ROOT_FILES:
            destination = HERE / "source_after" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        dump(HERE / "root_handoff_identity.json", {name: identity(ROOT / name) for name in ROOT_FILES})
        checks = {
            "status": "PASS_ADMINISTRATIVE_ONLY",
            "checked_local_links": local_links,
            "source_before_files_unchanged": before_count,
            "protected_prior_versions_unchanged": protected,
            "mathematics_verified_by_program": False,
            "performance_verified_by_this_script": False,
            "scope_counts_are_declared_and_not_runtime_telemetry": True,
        }
        dump(HERE / "delivery_checks.json", checks)
        dump(HERE / "seal.json", {
            "sealed_local": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "timezone": "Asia/Hong_Kong",
            "artifacts": current_inventory(),
            "administrative_checks": checks,
        })
    if arguments.verify_seal:
        seal = read_json(HERE / "seal.json")
        assert current_inventory() == seal["artifacts"], "sealed delivery mismatch"
        verify_manifest(HERE / "source_after", read_json(HERE / "root_handoff_identity.json"))
        for name, wanted in read_json(HERE / "root_handoff_identity.json").items():
            assert identity(ROOT / name) == wanted, f"live handoff changed: {name}"
    print(json.dumps({"status": "PASS_ADMINISTRATIVE_ONLY", "checked_local_links": local_links,
                      "protected_prior_versions_unchanged": protected,
                      "sealed": arguments.seal or arguments.verify_seal}, ensure_ascii=False))


if __name__ == "__main__":
    main()
