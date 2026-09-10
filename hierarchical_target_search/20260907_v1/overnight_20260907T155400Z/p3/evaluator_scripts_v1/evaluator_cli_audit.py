#!/usr/bin/env python3
"""CPU-only synthetic P3 model-loader and CLI boundary audit.
Creates a private 768-node native-v1 fixture and its own settings.json under output;
uses no real dataset, fits no model, and makes no performance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path("/data/netg/ACSG")
RUN = Path(__file__).resolve().parents[1]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_json(p, value):
    with p.open("x") as f:
        json.dump(value, f, indent=2)
        f.write("\n")

def replaced(args, key, value):
    output = list(args)
    output[output.index(key) + 1] = str(value)
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--evaluator", type=Path, default=ROOT / "build/benches/bench_hierarchical_eval_p3")
    args = parser.parse_args()
    dest = args.output_dir.resolve()
    dest.mkdir(parents=True, exist_ok=False)
    fixture = dest / "fixture"
    (fixture / "benches/datasets").mkdir(parents=True)
    n, dim, degree = 768, 8, 1
    values = [1.0] + [0.0] * 7
    one_vec = struct.pack("<i8f", dim, *values)
    (fixture / "base.fvecs").write_bytes(one_vec * n)
    (fixture / "pilot.fvecs").write_bytes(one_vec * 10000)
    (fixture / "pilot.ivecs").write_bytes(struct.pack("<i10i", 10, *range(10)) * 10000)
    name = "p3_synthetic_fixture"
    write_json(fixture / "benches/datasets/settings.json", {"root_dir": str(fixture), "datasets": {name: {
        "dataset_dir": ".", "base_path": "base.fvecs", "drl_train_query_path": "pilot.fvecs", "drl_train_gt_path": "pilot.ivecs",
        "nvecs": n, "metric": "ip", "normalization": "synthetic_unit", "artifact_version": "synthetic_cli_v1"}}})
    # Exact native v1 serialization read by IndexACSG::loadACPG; no production index is opened.
    native = struct.pack("<iqiiBBb", 1, n, dim, 0, 1, 1, 0)
    native += struct.pack("<4f5iq", 1.0, 1.0, 0.0, 0.0, 0, 0, 64, degree, 0, 0)
    native += struct.pack("<Q", n) + struct.pack(f"<{n}f", *([0.0] * n))
    native += struct.pack("<Q", n) + struct.pack(f"<{n}f", *([0.0] * n))
    native += struct.pack("<iQ", degree, n * degree) + struct.pack(f"<{n}i", *((i + 1) % n for i in range(n)))
    native += struct.pack("<Q", n * dim) + struct.pack(f"<{n * dim}f", *(values * n))
    (fixture / "graph.bin").write_bytes(native)
    labels = [i % 256 for i in range(n)]
    portals = [r + j * 256 for r in range(256) for j in range(3)]
    (fixture / "labels.u16").write_bytes(struct.pack(f"<{n}H", *labels))
    (fixture / "portals.i32").write_bytes(struct.pack("<768i", *portals))
    (fixture / "fast_ids.i32").write_bytes(struct.pack("<64i", *range(64)))
    (fixture / "fast_hubs.f32").write_bytes(struct.pack("<512f", *(values * 64)))
    model = {"schema_version": 2, "status": "COMPLETE", "stage": "P3", "dataset": name, "dim": dim, "base_nodes": n,
             "region_count": 256, "coarse_count": 16, "leaves_per_coarse": 16, "parent_rule": "leaf_id // 16",
             "active_regions": 4, "portals_per_region": 3, "oracle_diagnostic_only": True, "portal_rule": "frequency3", "lambda": 0,
             "labels_file": "labels.u16", "labels_sha256": sha(fixture / "labels.u16"),
             "portals_file": "portals.i32", "portals_sha256": sha(fixture / "portals.i32"), "fit_range": [10000, 30000],
             "synthetic_fixture_only": True}
    write_json(fixture / "model.json", model)
    bad_shape = dict(model, region_count=64)
    bad_sha = dict(model, portals_sha256="0" * 64)
    write_json(fixture / "bad_shape.json", bad_shape)
    write_json(fixture / "bad_sha.json", bad_sha)
    base = ["--stage", "P3", "--split", "pilot", "--measurement", "count", "--rounds", "1", "--threads", "1", "--warmup-queries", "1",
            "--max-queries", "1", "--search-ls", "64", "--top-k", "10", "--dataset", name, "--index-file", str(fixture / "graph.bin"),
            "--model", str(fixture / "model.json"), "--fast-hubs", str(fixture / "fast_hubs.f32"), "--fast-ids", str(fixture / "fast_ids.i32"),
            "--methods", "oracle_unified,oracle_probability", "--output", "PLACEHOLDER"]
    cases = [
        ("oracle_schema2_positive", base, None),
        ("heldout_rejected", replaced(base, "--split", "heldout"), "validation/heldout forbidden"),
        ("validation_rejected", replaced(base, "--split", "validation"), "validation/heldout forbidden"),
        ("geometry_rejected", replaced(base, "--methods", "geom_unified"), "P3 model only permits Fast and diagnostic oracle"),
        ("wrong_schema2_shape", replaced(base, "--model", fixture / "bad_shape.json"), "fixed P3 oracle-only schema"),
        ("portal_sha_mismatch", replaced(base, "--model", fixture / "bad_sha.json"), "label/portal SHA256 mismatch"),
    ]
    results = []
    for case, command, error in cases:
        output = dest / f"{case}.json"
        command = [str(args.evaluator.resolve()), *replaced(command, "--output", output)]
        proc = subprocess.run(command, cwd=fixture, capture_output=True, text=True, timeout=30)
        passed = proc.returncode == (2 if error else 0)
        if error:
            passed = passed and error in proc.stderr and not output.exists()
        else:
            data = json.loads(output.read_text()) if output.exists() else {}
            passed = passed and data.get("status") == "COMPLETE" and data.get("region_count") == 256 and data.get("portals_per_region") == 3
            passed = passed and all(row["oracle"] for row in data.get("results", []))
        if case in ("heldout_rejected", "validation_rejected"):
            passed = passed and "Loading" not in proc.stdout and not Path(str(output) + ".parts").exists()
        results.append({"name": case, "command": command, "expected_error": error, "returncode": proc.returncode,
                        "stdout": proc.stdout, "stderr": proc.stderr, "passed": passed})
    report = {"schema_version": 1, "status": "PASS" if all(x["passed"] for x in results) else "FAIL", "checks": results,
              "real_datasets_accessed": False, "heldout_accessed": False, "validation_accessed": False, "synthetic_base_nodes": n,
              "synthetic_queries_loaded": 10000, "synthetic_queries_measured": 1, "geometry_prototypes_in_model": False,
              "source_sha256": sha(ROOT / "benches/bench_hierarchical_eval_p3.cpp"), "binary_sha256": sha(args.evaluator), "script_sha256": sha(Path(__file__))}
    write_json(dest / "report.json", report)
    print(json.dumps({"status": report["status"], "checks": len(results), "report": str(dest / "report.json")}))
    if report["status"] != "PASS":
        raise RuntimeError("Synthetic CLI audit failed; preserve all fixtures and error evidence")

if __name__ == "__main__":
    main()
