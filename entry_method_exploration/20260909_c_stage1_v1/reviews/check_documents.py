#!/usr/bin/env python3
"""Read-only bounded C-stage documentation/identity checks; writes one new report.

No ANN, GT, validation/held-out vectors, or large base/graph reads are performed.
"""
from pathlib import Path
from urllib.parse import unquote
import argparse
import datetime
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
STAGE = HERE.parent
ROOT = STAGE.parents[1]


def sha(path):
    if path.stat().st_size > 2_000_000:
        raise ValueError(f"Refusing oversized documentation/source file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite existing audit output")
    cards = sorted((ROOT / "experiment_history").glob("[0-9][0-9]_*.md"))
    docs = [ROOT / x for x in ("AGENTS.md", "spec.md", "summary.md", "s-target.md", "s-experiment.md")]
    docs += [ROOT / "experiment_history/README.md"] + cards
    docs += sorted(STAGE.glob("*.md")) + sorted(HERE.glob("*.md"))
    missing, format_issues, identities = [], [], {}
    links = 0
    for doc in docs:
        rel = str(doc.relative_to(ROOT))
        identities[rel] = sha(doc)
        body = doc.read_text()
        if len(re.findall(r"^```", body, re.M)) % 2:
            format_issues.append({"file": rel, "issue": "Unbalanced code fence"})
        for raw in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
            target = raw.strip().strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            destination = unquote(target.split("#", 1)[0])
            if not destination:
                continue
            links += 1
            if not (doc.parent / destination).exists():
                missing.append({"file": rel, "target": target})
    index = (ROOT / "s-experiment.md").read_text()
    entries = re.findall(r"^\| (E\d{2})\b", index, re.M)
    targets = set(re.findall(r"\]\((experiment_history/[^)]+)\)", index))
    all_indexed = all(str(c.relative_to(ROOT)) in targets for c in cards)
    manifest = json.loads((STAGE / "source_manifest.json").read_text())
    unchanged, permitted_changed_docs, unexpected_changed, bad_snapshots = [], [], [], []
    allowed = {"summary.md", "spec.md", "s-target.md", "s-experiment.md", "experiment_history/09_research_designs_not_experiments.md"}
    for item in manifest["protected_sources"]:
        rel = item["path"]
        live, snapshot = ROOT / rel, STAGE / "source_before" / rel
        if not snapshot.is_file() or sha(snapshot) != item["sha256"]:
            bad_snapshots.append(rel)
        if live.is_file() and sha(live) == item["sha256"]:
            unchanged.append(rel)
        elif rel in allowed:
            permitted_changed_docs.append(rel)
        else:
            unexpected_changed.append(rel)
    gate = json.loads((STAGE / "results/c1_gate.json").read_text())
    c1_hashes = []
    for item in gate["parity_files"]:
        c1_hashes.append({"path": item["path"], "match": sha(Path(item["path"])) == item["sha256"]})
    c1_hashes.append({"path": "src/state_machine.hpp", "match": sha(STAGE / "src/state_machine.hpp") == gate["state_machine_sha256"]})
    final_index = len(cards) == 10 and entries == [f"E{i:02}" for i in range(1, 22)]
    result = {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "scope": "Markdown local target existence/fences, index coverage, small protected identities and C1 gate hashes; no ANN or GT access",
        "final_delivery_expected": args.final,
        "document_files_checked": len(docs), "history_cards": len(cards),
        "experiment_family_entries": entries, "all_cards_indexed": all_indexed,
        "local_links_checked": links, "missing_links": missing,
        "format_issues": format_issues, "protected_sources_unchanged": unchanged,
        "authorized_document_updates": permitted_changed_docs,
        "unexpected_protected_changes": unexpected_changed, "bad_frozen_snapshots": bad_snapshots,
        "c1_gate_identity_checks": c1_hashes, "final_index_has_10_cards_and_E01_E21": final_index,
        "document_sha256": identities,
    }
    okay = not any([missing, format_issues, unexpected_changed, bad_snapshots]) and all_indexed and all(x["match"] for x in c1_hashes)
    if args.final:
        okay = okay and final_index
    result["status"] = "PASS" if okay else "FAIL"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k != "document_sha256"}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if okay else 1)


if __name__ == "__main__":
    main()
