"""Seal the new deliverables after the complete timing and verification."""
import csv

from run_experiment import DATASETS, ROOT, read, verify, write
from run import digest


def main():
    phase = read(ROOT / "timing_complete.json")
    assert phase["status"] == "PASS_E213_TIMING_COMPLETE"
    assert read(ROOT / "reviews/output_audit.json")["status"] == "PASS_E213_PACKETS"
    assert read(ROOT / "reviews/independent_audit.json")["status"] == "PASS_E213_STDLIB_AUDIT"
    for name in ("input_freeze.json", "bin/freeze.json"):
        verify(read(ROOT / name)["files"])
    with (ROOT / "analysis/rounds.csv").open() as source:
        rounds = list(csv.DictReader(source))
    assert len(rounds) == 448 and all(int(row["cpu"]) == 15 and int(row["threads"]) == 1 for row in rounds)
    assert all((ROOT / "analysis" / f"recall_qps_k{k}.{ext}").stat().st_size > 10000
               for k in (1, 100) for ext in ("png", "svg"))
    state = {"status": "SEALED_E213_SPAN4_GT10_B32_NSG_GATE", "datasets": DATASETS,
        "primary_points": 168, "primary_batches": 336, "gate_scalar_points": 56, "gate_scalar_batches": 112,
        "points": phase["points"], "batches": phase["batches"], "query_calls": phase["query_calls"],
        "timed_wall_seconds": sum(float(row["seconds"]) for row in rounds),
        "query_core": "E211 SPAN4", "pending_experiment_queue": False, "report": "report.md"}
    write(ROOT / "state.json", state)
    external = [ROOT.parent / "20261120_gt10_nsg_b32_four_way_v1" / "scripts" / f"{name}.py"
                for name in ("run", "analyze", "audit")]
    files = {str(path.relative_to(ROOT)): {"bytes": path.stat().st_size, "sha256": digest(path)}
             for path in sorted(ROOT.rglob("*")) if path.is_file() and "__pycache__" not in path.parts}
    write(ROOT / "seal.json", {"status": "SEALED_E213", "experiment_files": files,
          "external_analysis_sources": {str(p): digest(p) for p in external}})
    print(f"sealed {len(files)} files and {len(external)} referenced analysis sources")


if __name__ == "__main__":
    main()
