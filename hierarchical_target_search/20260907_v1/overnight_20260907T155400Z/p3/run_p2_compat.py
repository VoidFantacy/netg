#!/usr/bin/env python3
"""Controlled-root runner: four sequential 32-query P2 compatibility batches.
Run only through the existing task controller as one heavy task. Never launches itself.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path("/data/netg/ACSG")
RUN = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benches/bench_hierarchical_eval_p3.cpp"
SOURCE_SHA = "cf40032dc469c08840e409af23bd503e1ad6571184351a2694776247e21d1316"
BINARY_SHA = "2f234d1276fdafebe0ab706ebccc37f4c52312ca16ca09b512530f404b0ce580"
DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
METHODS = "fast,geom_unified,geom_uniform,geom_probability,oracle_unified,oracle_probability"

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluator", type=Path, default=ROOT / "build/benches/bench_hierarchical_eval_p3")
    args = parser.parse_args()
    if json.loads((RUN / "gates/P1.json").read_text())["status"] != "PASS":
        raise ValueError("Original P1 PASS is required")
    if sha(SOURCE) != SOURCE_SHA or sha(args.evaluator) != BINARY_SHA:
        raise ValueError("P3 evaluator differs from source/binary accepted by synthetic self-test")
    jobs = []
    manifests = []
    for alias in ("webvid", "yandex"):
        path = RUN / f"p2/{alias}_eval/count.json.parts/manifest.json"
        data = json.loads(path.read_text())
        if data["model_manifest"]["schema_version"] != 1 or data["source_query_range"] != [0, 10000]:
            raise ValueError("Saved P2 manifest shape/range mismatch")
        manifests.append({"path": str(path), "sha256": sha(path)})
        base = [str(args.evaluator.resolve()), "--stage", "P1", "--split", "pilot", "--dataset", data["dataset"],
                "--index-file", data["index_file"], "--model", data["model_file"], "--fast-hubs", data["fast_hubs"],
                "--fast-ids", data["fast_ids"], "--fast-m", "3", "--search-ls", "64,128", "--top-k", "10", "--query-offset", "0",
                "--hnsw-seed", "100", "--methods", METHODS, "--max-queries", "32", "--threads", "16", "--warmup-queries", "32"]
        for measurement, rounds in (("count", 1), ("timing", 5)):
            name = f"{alias}_{measurement}"
            jobs.append((name, base + ["--measurement", measurement, "--rounds", str(rounds), "--output", str((args.output / f"{name}.json").resolve())]))
    checker = RUN / "p3/check_p2_compat.py"
    jobs.append(("compare", [sys.executable, str(checker), "--old-p2-dir", str(RUN / "p2"), "--new-dir", str(args.output.resolve()), "--output", str((args.output / "compatibility.json").resolve())]))
    if time.time() >= DEADLINE:
        raise RuntimeError("Research soft deadline closed")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"schema_version": 1, "status": "INCOMPLETE", "stage": "P1_P3_REACCEPTANCE", "started_utc": now(),
              "source_sha256": SOURCE_SHA, "binary_sha256": BINARY_SHA, "runner_sha256": sha(Path(__file__)),
              "checker_sha256": sha(checker), "protocol_sha256": sha(RUN / "p3/protocol.json"), "baseline_manifests": manifests,
              "cpu_only": True, "heldout_accessed": False, "validation_accessed": False, "invocations": []}
    def save():
        temporary = args.output / "execution.tmp.json"
        temporary.write_text(json.dumps(record, indent=2) + "\n")
        temporary.replace(args.output / "execution.json")
    save()
    try:
        for name, command in jobs:
            if time.time() >= DEADLINE:
                raise RuntimeError("Research soft deadline closed between phases")
            if sha(SOURCE) != SOURCE_SHA or sha(args.evaluator) != BINARY_SHA:
                raise RuntimeError("Evaluator changed between compatibility phases")
            item = {"name": name, "command": command, "status": "RUNNING", "started_utc": now()}
            record["invocations"].append(item); save()
            print("P3_COMPAT_BEGIN", name, flush=True)
            with (args.output / f"{name}.log").open("xb") as f:
                child = subprocess.Popen(command, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
                item.update(pid=child.pid, pgid=os.getpgid(child.pid)); save()
                item["returncode"] = child.wait()
            item.update(status="COMPLETE" if item["returncode"] == 0 else "FAILED", ended_utc=now()); save()
            if item["returncode"] != 0:
                raise RuntimeError(f"Compatibility phase {name} failed; preserve incomplete output and logs")
            with (args.output / f"checkpoint_{len(record['invocations'])}.json").open("x") as f:
                json.dump({"status": "INCOMPLETE", "completed_phases": len(record["invocations"]), "last_phase": name}, f)
            print("P3_COMPAT_DONE", name, flush=True)
        if json.loads((args.output / "compatibility.json").read_text())["status"] != "PASS":
            raise RuntimeError("Comparison did not produce PASS")
        record["status"] = "PASS_P2_COMPATIBILITY"
    except BaseException as e:
        record["error"] = repr(e)
        raise
    finally:
        record["ended_utc"] = now(); save()
    print(json.dumps({"status": record["status"], "execution": str(args.output / "execution.json")}), flush=True)

if __name__ == "__main__":
    main()
