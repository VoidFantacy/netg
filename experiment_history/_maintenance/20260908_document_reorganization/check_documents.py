#!/usr/bin/env python3
"""Bounded local checks for this documentation delivery; no experiment execution."""
from pathlib import Path
from urllib.parse import unquote
import datetime
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIMARY = [ROOT / n for n in ("AGENTS.md", "spec.md", "summary.md", "s-target.md", "s-experiment.md")]
CARDS = sorted((ROOT / "experiment_history").glob("[0-9][0-9]_*.md"))
DOCS = PRIMARY + [ROOT / "experiment_history/README.md"] + CARDS + sorted(HERE.glob("*.md"))


def identity(path):
    size = path.stat().st_size
    if size > 2_000_000:
        raise ValueError(f"Refusing oversized input: {path.relative_to(ROOT)} ({size})")
    return {"bytes": size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


missing = []
format_issues = []
link_count = 0
identities = {}
for path in DOCS:
    rel = str(path.relative_to(ROOT))
    identities[rel] = identity(path)
    body = path.read_text(encoding="utf-8")
    if len(re.findall(r"^```", body, flags=re.M)) % 2:
        format_issues.append({"file": rel, "issue": "Unbalanced fenced blocks"})
    for target in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", body):
        target = target.strip().strip("<>")
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        destination = unquote(target.split("#", 1)[0])
        if not destination:
            continue
        link_count += 1
        if not (path.parent / destination).exists():
            missing.append({"file": rel, "target": target})

protected = json.loads((HERE / "source_before/protected_manifest.json").read_text())
changed = []
for rel, expected in protected.items():
    path = ROOT / rel
    if not path.is_file() or identity(path) != expected:
        changed.append(rel)

index = (ROOT / "s-experiment.md").read_text()
entries = re.findall(r"^\| (E\d{2})\b", index, flags=re.M)
card_targets = {str(p.relative_to(ROOT)) for p in CARDS}
indexed = card_targets.issubset(set(re.findall(r"\]\((experiment_history/[^)]+)\)", index)))
checks = {
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "document_files_checked": len(DOCS),
    "history_cards": len(CARDS),
    "experiment_family_entries": entries,
    "all_cards_indexed": indexed,
    "local_links_checked": link_count,
    "missing_links": missing,
    "format_issues": format_issues,
    "protected_files_checked": len(protected),
    "protected_files_changed": changed,
    "four_main_files_same_directory": all((ROOT / n).is_file() for n in ("spec.md", "summary.md", "s-target.md", "s-experiment.md")),
    "scope": "Small document/source identities and Markdown target existence, not raw experiment reproduction or large data hashes.",
    "document_identities": identities,
}
checks["status"] = "PASS" if (
    not missing and not format_issues and not changed and indexed
    and len(CARDS) == 9 and entries == [f"E{i:02}" for i in range(1, 21)]
    and checks["four_main_files_same_directory"]
) else "FAIL"
(HERE / "document_checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({k: v for k, v in checks.items() if k != "document_identities"}, ensure_ascii=False, indent=2))
raise SystemExit(0 if checks["status"] == "PASS" else 1)
