#!/usr/bin/env python3
"""Administrative Git snapshot inventory; never runs experiments or decodes arrays."""
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "research_snapshots/20261002"
ROOT_SKIP = {".git", ".git_old_backup", ".agents", ".venv_cpu", ".vscode", ".idea", "build", "faiss", "logs"}
TREE_SKIP = {".git", "__pycache__", "site-packages", "dist-packages", "node_modules",
             ".cache", ".venv", "venv", "env", "checkpoints", "CMakeFiles", "build"}
PREFIX_SKIP = (
    "entry_method_exploration/20260911_gt10_shared_transform_v1/src/vendor",
    "entry_method_exploration/20260922_service_capability_v1/vendor",
    "entry_method_exploration/20260930_theory_until2200_v1/literature/tools",
    "hierarchical_target_search/20260907_v1/tools/python",
    "hierarchical_target_search/20260907_v1/tools/mkl-sysroot",
    "hierarchical_target_search/20260907_v1/tools/mkl_packages",
    "hierarchical_target_search/20260907_v1/tools/local",
    "hierarchical_target_search/20260907_v1/tools/mkl",
    "hierarchical_target_search/20260907_v1/tools/gp-ann",
    "hierarchical_target_search/20260907_v1/tools/RoarGraph",
    "hierarchical_target_search/20260907_v1/tools/roargraph",
    "hierarchical_target_search/20260907_v1/tools/metis",
    "hierarchical_target_search/20260907_v1/tools/METIS",
    "hierarchical_target_search/20260907_v1/tools/GKlib",
    "hierarchical_target_search/20260907_v1/tools/LIRA",
    "entry_method_exploration/20260909_c_stage1_v1/results/c2_main_webvid_v1/states",
    "entry_method_exploration/20260909_c_stage1_v1/results/c2_main_yandex_v1/states",
)
CODE = {".py", ".cpp", ".cc", ".c", ".cxx", ".h", ".hpp", ".sh", ".bash", ".cmake"}
TEXT = {".md", ".diff", ".patch", ".yml", ".yaml", ".toml", ".ini", ".info"}
SELF_RECORDS = {"snapshot_manifest.json", "omitted_paths.tsv", "verification.json"}
RECENT = tuple("entry_method_exploration/" + s for s in (
    "20261002_theory_until1300_v1", "20261002_theory_until1600_v1", "20261002_gt10_paper_theory_v1"))
MIB = 1024 * 1024


def identity(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def skip_dir(rel):
    p = Path(rel)
    if len(p.parts) == 1 and p.name in ROOT_SKIP:
        return "external_dependency" if p.name == "faiss" else "environment_or_generated_tree"
    if p.name in TREE_SKIP or p.name.endswith(".json.parts") or re.match(r"checkpoint_\d", p.name):
        return "environment_or_generated_tree"
    if any(rel == x or rel.startswith(x + "/") for x in PREFIX_SKIP):
        return "vendor_environment_or_iteration_states"
    if p.name.startswith("subgraphs"):
        return "graph_training_payload"
    return None


def include_reason(rel, size):
    p = Path(rel)
    suffix = p.suffix.lower()
    if p.name in {"acosp_nsg.json", "acpg_nsg.json", "neural_entry_points.json"}:
        return None
    if rel.startswith(RECENT[0] + "/") and p.name.endswith("bucket_alignment.npz"):
        return "small_sealed_diagnostic_attachment"
    if p.name in {".gitignore", ".gitmodules", "CMakeLists.txt", "LICENSE", "LICENSE.txt", "COPYING"}:
        return "source_configuration"
    if p.name.startswith("requirements") and suffix == ".txt":
        return "source_configuration"
    if suffix in CODE:
        return "source_code"
    if suffix in TEXT and size <= 10 * MIB:
        return "documentation_or_identity"
    if rel.startswith(RECENT) and size <= 5 * MIB and suffix in {".json", ".pdf", ".svg", ".png", ".csv"}:
        return "latest_sealed_research"
    if rel.startswith("experiment_history/") and size <= 10 * MIB:
        return "experiment_history"
    if suffix == ".json":
        if re.fullmatch(r"\d+\.json", p.name) or re.match(r"checkpoint_\d", p.name):
            return None
        if any(s in p.name.lower() for s in ("per_query", "training_curves")):
            return None
        cap = 10 * MIB if any(s in p.name.lower() for s in ("manifest", "identity", "inventory", "seal", "artifacts_stat")) else MIB
        if size <= cap:
            return "protocol_state_or_saved_result"
    if suffix in {".csv", ".tsv"} and size <= MIB and not any(s in p.name.lower() for s in ("per_query", "failed_queries", "zero_gt", "failure_cases", "all_query")):
        return "saved_result_table"
    if suffix in {".svg", ".png", ".pdf"} and size <= 2 * MIB and not ("/sources/" in rel or rel.startswith("papers/")):
        return "saved_figure_or_report"
    return None


def verify_protected():
    latest = ROOT / RECENT[-1]
    records = [(latest, json.loads((latest / "seal.json").read_text())["artifacts"])]
    for dirname in RECENT[:2]:
        records.append((ROOT / dirname, json.loads((latest / (Path(dirname).name + "_frozen_identity.json")).read_text())))
    counts = {}
    for directory, files in records:
        for name, expected in files.items():
            assert identity(directory / name) == expected, directory / name
        counts[directory.name] = len(files)
    return counts


def main():
    included = {}
    omitted = []
    for dp, ds, fs in os.walk(ROOT, followlinks=False):
        for name in list(ds):
            p = Path(dp) / name
            rel = p.relative_to(ROOT).as_posix()
            reason = skip_dir(rel)
            if reason or p.is_symlink():
                ds.remove(name)
                omitted.append((rel + "/", "directory", reason or "symlink"))
        for name in fs:
            p = Path(dp) / name
            rel = p.relative_to(ROOT).as_posix()
            if p.parent == SNAPSHOT and name in SELF_RECORDS:
                continue
            if p.is_symlink():
                omitted.append((rel, "symlink", "symlink"))
                continue
            if not p.is_file():
                continue
            size = p.stat().st_size
            reason = include_reason(rel, size)
            if reason:
                included[rel] = {**identity(p), "reason": reason, "mode": oct(p.stat().st_mode & 0o777)}
            else:
                omitted.append((rel, str(size), "payload_raw_output_or_non_source"))
    omitted.sort()
    ledger = SNAPSHOT / "omitted_paths.tsv"
    ledger.write_text("path\tbytes_or_kind\treason\n" + "".join("\t".join(x) + "\n" for x in omitted))
    parent = git("rev-parse", "HEAD")
    deleted_sources = [p for p in git("diff", "--diff-filter=D", "--name-only").splitlines()
                       if Path(p).suffix.lower() in CODE and not p.startswith("build/")]
    payload = {
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        "kind": "LOCAL_RESEARCH_STATE_SOURCE_AND_HISTORY_SNAPSHOT",
        "parent_commit": parent,
        "branch": git("branch", "--show-current"),
        "main_commit_unchanged": git("rev-parse", "main"),
        "current_state": {"production": "E99", "webvid": "GT10-soft-t1", "yandex": "GT10-hard",
                          "latest_performance_record": 166, "latest_theory_record": 169,
                          "capacity_service_candidate": "PROPOSED_UNIMPLEMENTED_NO_EXPERIMENTS",
                          "new_experiments_in_this_task": 0, "reliable_joint_gain_established": False},
        "selection": {"code_extensions": sorted(CODE), "text_extensions": sorted(TEXT),
                      "root_skip": sorted(ROOT_SKIP), "tree_skip": sorted(TREE_SKIP),
                      "prefix_skip": PREFIX_SKIP, "regular_json_max_bytes": MIB,
                      "identity_json_max_bytes": 10 * MIB,
                      "explicit_force_stage": "Tracked and ignored source/configuration may be deliberately included; no git add of whole directories.",
                      "omitted_paths": {"path": ledger.name, **identity(ledger)},
                      "self_identity_exclusion": sorted(SELF_RECORDS)},
        "protected_theory_bytes_verified": verify_protected(),
        "included_count": len(included), "included_bytes": sum(x["bytes"] for x in included.values()),
        "category_counts": dict(collections.Counter(x["reason"] for x in included.values())),
        "omitted_entries": len(omitted), "deleted_source_paths": deleted_sources,
        "included_files": dict(sorted(included.items())),
    }
    (SNAPSHOT / "snapshot_manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    selected = list(included) + ["research_snapshots/20261002/" + x for x in SELF_RECORDS if (SNAPSHOT / x).exists()]
    Path("/tmp/acsg-state-20261002-paths").write_bytes(b"\0".join(os.fsencode(x) for x in sorted(selected)) + b"\0")
    print(json.dumps({k: payload[k] for k in ("branch", "included_count", "included_bytes", "category_counts", "omitted_entries", "protected_theory_bytes_verified")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
