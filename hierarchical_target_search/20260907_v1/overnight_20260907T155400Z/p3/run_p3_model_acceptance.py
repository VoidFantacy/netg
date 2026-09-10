#!/usr/bin/env python3
"""Controlled-root P1 acceptance of one real P3 lambda0/frequency3 model.
Run after new-evaluator P2 compatibility PASS, before P3 performance. It executes
count32, plain32/five rounds and trace4 sequentially; all results are correctness-only.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import struct
import sys
import time

ROOT = Path("/data/netg/ACSG")
RUN = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benches/bench_hierarchical_eval_p3.cpp"
SOURCE_SHA = "cf40032dc469c08840e409af23bd503e1ad6571184351a2694776247e21d1316"
BINARY_SHA = "2f234d1276fdafebe0ab706ebccc37f4c52312ca16ca09b512530f404b0ce580"
DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
ALIASES = {"webvid2_5m_light_v1": "webvid", "yandex_t2i_official10M_ip_v1": "yandex"}
ROUTE_RESULT = ("query_id", "recall", "result_ids", "entry_ids", "fast_anchor_id", "shared_seed", "actual_entry_count", "regions", "weights")
COUNTS = ("routing_ndc", "graph_ndc", "total_ndc", "routing_mac", "graph_mac", "total_mac", "expanded", "rejected", "evicted_unexpanded")
ORACLES = ("oracle_unified", "oracle_probability")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def bound(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def freeze_fast_inputs(manifest_path, fast, audit_path):
    require(fast['input_audit_sha256'] == sha(audit_path), 'Fast manifest belongs to another input audit')
    bindings = {'manifest': bound(manifest_path)}
    for kind in ('hubs', 'ids'):
        path = Path(fast[kind + '_file'])
        if not path.is_absolute():
            path = Path(manifest_path).resolve().parent / path
        bindings[kind] = bound(path)
        require(bindings[kind]['sha256'] == fast[kind + '_sha256'], 'Fast raw ' + kind + ' differs from paired manifest')
    return bindings


def verify_frozen_fast(bindings):
    for kind in ('manifest', 'hubs', 'ids'):
        require(sha(bindings[kind]['path']) == bindings[kind]['sha256'], 'Frozen Fast ' + kind + ' changed between cells')


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write_new(path, data):
    with Path(path).open("x") as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write("\n")

def result_map(path, dataset, measurement, nq, rounds, methods):
    data = read(path)
    require(data["status"] == "COMPLETE" and data["stage"] == "P1" and data["dataset"] == dataset, f"Incomplete or wrong acceptance output: {path}")
    require(data["measurement"] == measurement and data["num_queries"] == nq and data["source_query_range"] == [0, nq], f"Measurement/query shape: {path}")
    require(data["rounds"] == rounds and data["search_Ls"] == [64, 128] and data["top_k"] == 10 and data["fast_m"] == 3, f"Frozen K/L/round/m: {path}")
    require(data["split"] == "pilot" and data["source_query_type"] == "drl_train" and data["heldout_accessed"] is False, f"Split boundary: {path}")
    require(data["region_count"] == 256 and data["portals_per_region"] == 3, f"P3 model shape: {path}")
    require(data["evaluator_provenance"]["source_sha256"] == SOURCE_SHA and data["evaluator_provenance"]["binary_sha256"] == BINARY_SHA, f"Evaluator changed: {path}")
    results = {}
    for row in data["results"]:
        key = row["method"], row["search_L"], row["round"]
        require(key not in results, f"Duplicate result: {key}")
        results[key] = row
    expected = {(m, l, r) for m in methods for l in (64, 128) for r in range(rounds)}
    require(set(results) == expected, f"Incomplete method/L/round matrix: {path}")
    for method in methods:
        for l in (64, 128):
            first = results[method, l, 0]
            require([x["query_id"] for x in first["per_query"]] == list(range(nq)), f"Query alignment: {path}")
            for r in range(rounds):
                item = results[method, l, r]
                require(item["result_hash_fnv1a64"] == first["result_hash_fnv1a64"] and item["route_hash_fnv1a64"] == first["route_hash_fnv1a64"], f"Repeated timing identity: {path}")
    return data, results

def compare(args, model, compatibility, source_manifest, fast_bindings):
    count, cr = result_map(args.output / "count.json", args.dataset, "count", 32, 1, ("fast", *ORACLES))
    timing, pr = result_map(args.output / "timing.json", args.dataset, "timing", 32, 5, ("fast", *ORACLES))
    trace, tr = result_map(args.output / "trace.json", args.dataset, "trace", 4, 1, ORACLES)
    for data in (count, timing, trace):
        require(data["model_manifest"] == model and data["model_sha256"] == sha(args.model), "Model manifest changed between modes")
        for key in ("index_file", "fast_hubs", "fast_ids"):
            require(data[key] == source_manifest[key], f"Frozen Fast/index input changed: {key}")
        for key in ("M", "ef_construction", "ef_search", "seed"):
            require(data["hnsw"][key] == source_manifest["hnsw"][key], f"Frozen Fast router setting changed: {key}")
        require(data["evaluator_provenance"] == count["evaluator_provenance"], "Evaluator path/build changed between modes")
    require(count["threads"] == timing["threads"] == 16 and trace["threads"] == 1, "Mode thread counts changed")
    baseline_candidates = [Path(x["path"]) for x in compatibility["inputs"] if Path(x["path"]).name == ALIASES[args.dataset] + "_count.json"]
    require(len(baseline_candidates) == 1, "Need exact new-evaluator P2 Fast reference")
    baseline_path = baseline_candidates[0]
    baseline_binding = next(x for x in compatibility["inputs"] if x["path"] == str(baseline_path))
    require(sha(baseline_path) == baseline_binding["sha256"], "P2 compatibility Fast reference changed")
    baseline = read(baseline_path)
    baseline_rows = {(r["method"], r["search_L"]): r["per_query"] for r in baseline["results"]}
    label_path = Path(model["labels_file"])
    if not label_path.is_absolute():
        label_path = args.model.parent / label_path
    portal_path = Path(model["portals_file"])
    if not portal_path.is_absolute():
        portal_path = args.model.parent / portal_path
    require(sha(label_path) == model["labels_sha256"] and sha(portal_path) == model["portals_sha256"], "Real labels/portals changed")
    require(sys.byteorder == "little" and label_path.stat().st_size == 2 * model["base_nodes"], "Label shape/byte order changed")
    labels = memoryview(label_path.read_bytes()).cast("H")
    flat_portals = struct.unpack("<768i", portal_path.read_bytes())
    portals = [flat_portals[r * 3:r * 3 + 3] for r in range(256)]
    for region, ids in enumerate(portals):
        require(len(set(map(int, ids))) == 3 and all(0 <= int(x) < len(labels) and int(labels[x]) == region for x in ids), "Invalid real portal ownership")
    route_rows, trace_files, discovered_nodes = 0, 0, 0
    for method in ("fast", *ORACLES):
        for l in (64, 128):
            counted, plain = cr[method, l, 0]["per_query"], pr[method, l, 0]["per_query"]
            for row, other in zip(counted, plain):
                for key in ROUTE_RESULT:
                    require(row[key] == other[key], f"Count/plain {method}/L{l}/q{row['query_id']}/{key}")
                if method == "fast":
                    reference = baseline_rows[method, l][row["query_id"]]
                    for key in ROUTE_RESULT + COUNTS:
                        require(row[key] == reference[key], f"P3 model changed Fast control {l}/{row['query_id']}/{key}")
                else:
                    regions, weights = row["regions"], row["weights"]
                    require(len(regions) == len(set(regions)) == 4 and all(0 <= r < 256 for r in regions), "Invalid active leaf route")
                    require(all(math.isfinite(w) and w >= 0 for w in weights) and abs(sum(weights) - 1) < 1e-12, "Invalid oracle weights")
                    seeds = [row["shared_seed"], row["fast_anchor_id"]] + [int(x) for r in regions for x in portals[r]]
                    unique = list(dict.fromkeys(seeds))
                    require(unique[0] >= 0 and row["entry_ids"] == unique[1:] and row["actual_entry_count"] == len(unique), "Actual route differs from deduplicated real default/anchor/portals")
                    require(12 <= len(unique) <= 14, "Unexpected P3 seed count")
                route_rows += 1
    for l in (64, 128):
        for unified, protected in zip(cr[ORACLES[0], l, 0]["per_query"], cr[ORACLES[1], l, 0]["per_query"]):
            for key in ROUTE_RESULT[3:]:
                require(unified[key] == protected[key], f"Oracle ablations have different routes: L{l}/q{unified['query_id']}/{key}")
        for method in ORACLES:
            trace_result = tr[method, l, 0]
            require(len(trace_result["trace_files"]) == 4, "Expected exactly four trace queries per method/L")
            for row, filename in zip(trace_result["per_query"], trace_result["trace_files"]):
                reference = cr[method, l, 0]["per_query"][row["query_id"]]
                for key in ROUTE_RESULT + COUNTS:
                    require(row[key] == reference[key], f"Trace/count parity {method}/L{l}/q{row['query_id']}/{key}")
                trace_path = Path(trace["parts_directory"]) / filename
                payload = read(trace_path)
                require(payload["query_id"] == row["query_id"] and payload["method"] == method and payload["L"] == l, "Trace identity mismatch")
                require(payload["result_ids"] == row["result_ids"] and payload["ndc"] == row["graph_ndc"] and payload["gt_associated_after_search"] is True, "Trace output/count/GT boundary mismatch")
                events = payload["events"]
                discoveries = [x for x in events if x["kind"] == "discover"]
                require(len(discoveries) == row["graph_ndc"] and len({x["id"] for x in discoveries}) == len(discoveries), "Trace discovery count or shared visited mismatch")
                actual_seeds = [x["id"] for x in discoveries if x["parent"] == -1]
                require(actual_seeds == [row["shared_seed"], *row["entry_ids"]], "Trace did not consume all unique seeds in order")
                for event in events:
                    node = event["id"]
                    require(0 <= node < len(labels), "Trace node outside base")
                    owner = 0
                    if method == "oracle_probability" and node != row["shared_seed"] and int(labels[node]) in row["regions"]:
                        owner = row["regions"].index(int(labels[node])) + 1
                    require(event["queue"] == owner, "Trace candidate belongs to wrong leaf/shared queue")
                require(sum(x["kind"] == "expand" for x in events) == row["expanded"], "Trace expansion counter mismatch")
                require(sum(x["kind"] == "reject" for x in events) == row["rejected"], "Trace rejection counter mismatch")
                require(sum(x["kind"] == "evict" and not x["expanded"] for x in events) == row["evicted_unexpanded"], "Trace eviction counter mismatch")
                trace_files += 1; discovered_nodes += len(discoveries)
    return {"schema_version": 1, "stage": "P1_P3_REAL_MODEL_REACCEPTANCE", "status": "PASS", "dataset": args.dataset,
            "model": str(args.model.resolve()), "model_sha256": sha(args.model), "structure_lambda": 0, "portal_rule": "frequency3",
            "aligned_count_plain_rows": route_rows, "traces_checked": trace_files, "discovered_node_owner_checks": discovered_nodes,
            "source_sha256": SOURCE_SHA, "binary_sha256": BINARY_SHA, "fast_inputs": fast_bindings, "p2_compatibility": {"path": str(args.p2_compat.resolve()), "sha256": sha(args.p2_compat)},
            "same_Fast_as_accepted_P2_prefix": True, "five_timing_rounds_stable": True, "all_actual_seeds_consumed": True,
            "scope": "First32 pilot correctness only; four traced queries per method/L; no new performance gate or deployment claim",
            "heldout_accessed": False, "validation_accessed": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=tuple(ALIASES), required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--p2-compat", type=Path, required=True, help="PASS compatibility.json from run_p2_compat.py")
    parser.add_argument("--fast-manifest", type=Path, help="Defaults to the paired20K Fast manifest for this dataset")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluator", type=Path, default=ROOT / "build/benches/bench_hierarchical_eval_p3")
    args = parser.parse_args(); args.model = args.model.resolve(); args.output = args.output.resolve()
    compatibility = read(args.p2_compat)
    require(compatibility["status"] == "PASS" and compatibility["evaluator_provenance"]["source_sha256"] == SOURCE_SHA and
            compatibility["evaluator_provenance"]["binary_sha256"] == BINARY_SHA, "New-evaluator P2 compatibility PASS required")
    require(sha(SOURCE) == SOURCE_SHA and sha(args.evaluator) == BINARY_SHA, "Evaluator source/build changed")
    model = read(args.model)
    require(model["status"] == "COMPLETE" and model["stage"] == "P3" and model["dataset"] == args.dataset and model["schema_version"] == 2 and
            model["region_count"] == 256 and model["portals_per_region"] == 3 and model["lambda"] == 0 and model["portal_rule"] == "frequency3", "Expected first real P3 lambda0/frequency3 model")
    manifest_path = RUN / f"p2/{ALIASES[args.dataset]}_eval/count.json.parts/manifest.json"
    source_manifest = read(manifest_path)
    fast_manifest_path = args.fast_manifest or RUN / f"p1/paired_fast20k/{args.dataset}/manifest.json"
    fast = read(fast_manifest_path)
    require(fast["status"] == "COMPLETE" and fast["dataset"] == args.dataset and fast["fit_queries"] == 20000 and
            fast["pilot_queries_used"] == 0 and fast["fit_query_values_sha256"] == model["fit_query_values_sha256"] and
            fast["fit_gt_values_sha256"] == model["fit_gt_values_sha256"], "Paired Fast fit/model contract mismatch")
    audit_path = Path(model["audit"]["path"])
    require(sha(audit_path) == model["audit"]["sha256"] == model["input_audit_sha256"], "Model input audit binding changed")
    fast_bindings = freeze_fast_inputs(fast_manifest_path, fast, audit_path)
    for key, kind in (("fast_hubs", "hubs"), ("fast_ids", "ids")):
        require(Path(source_manifest[key]).resolve() == Path(fast_bindings[kind]["path"]), "Fast input paths differ from accepted P2 prefix")
    base = [str(args.evaluator.resolve()), "--stage", "P1", "--split", "pilot", "--dataset", args.dataset,
            "--index-file", source_manifest["index_file"], "--model", str(args.model), "--fast-hubs", fast_bindings["hubs"]["path"], "--fast-ids", fast_bindings["ids"]["path"],
            "--fast-m", "3", "--search-ls", "64,128", "--top-k", "10", "--query-offset", "0", "--hnsw-seed", "100"]
    phases = [("count", "1", "32", "16", "fast," + ",".join(ORACLES)), ("timing", "5", "32", "16", "fast," + ",".join(ORACLES)),
              ("trace", "1", "4", "1", ",".join(ORACLES))]
    require(time.time() < DEADLINE, "Research soft deadline closed")
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"schema_version": 1, "status": "INCOMPLETE", "stage": "P1_P3_REAL_MODEL_REACCEPTANCE", "started_utc": now(), "dataset": args.dataset,
              "model": str(args.model), "model_sha256": sha(args.model), "source_sha256": SOURCE_SHA, "binary_sha256": BINARY_SHA,
              "runner_sha256": sha(Path(__file__)), "fast_inputs": fast_bindings, "protocol_sha256": sha(RUN / "p3/protocol.json"), "cpu_only": True, "invocations": []}
    def save():
        tmp = args.output / "execution.tmp.json"; tmp.write_text(json.dumps(record, indent=2) + "\n"); tmp.replace(args.output / "execution.json")
    save()
    try:
        for name, rounds, queries, threads, methods in phases:
            require(time.time() < DEADLINE, "Research soft deadline closed between phases")
            require(sha(SOURCE) == SOURCE_SHA and sha(args.evaluator) == BINARY_SHA and sha(args.model) == record["model_sha256"], "Source/build/model changed between phases")
            verify_frozen_fast(fast_bindings)
            command = base + ["--measurement", name, "--rounds", rounds, "--max-queries", queries, "--threads", threads, "--methods", methods,
                              "--warmup-queries", queries, "--output", str(args.output / f"{name}.json")]
            item = {"name": name, "command": command, "status": "RUNNING", "started_utc": now()}; record["invocations"].append(item); save()
            print("P3_REAL_ACCEPT_BEGIN", args.dataset, name, flush=True)
            with (args.output / f"{name}.log").open("xb") as f:
                child = subprocess.Popen(command, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT)
                item.update(pid=child.pid, pgid=os.getpgid(child.pid)); save(); item["returncode"] = child.wait()
            item.update(status="COMPLETE" if item["returncode"] == 0 else "FAILED", ended_utc=now()); save()
            require(item["returncode"] == 0, f"Acceptance phase {name} failed; preserve incomplete evidence")
            verify_frozen_fast(fast_bindings)
            write_new(args.output / f"checkpoint_{len(record['invocations'])}.json", {"status": "INCOMPLETE", "complete_phases": len(record["invocations"]), "last_phase": name})
            print("P3_REAL_ACCEPT_DONE", args.dataset, name, flush=True)
        require(sha(SOURCE) == SOURCE_SHA and sha(args.evaluator) == BINARY_SHA, "Evaluator changed before comparison")
        verify_frozen_fast(fast_bindings)
        report = compare(args, model, compatibility, source_manifest, fast_bindings)
        write_new(args.output / "acceptance.json", report)
        record["status"] = "PASS_REAL_P3_MODEL_REACCEPTANCE"
    except BaseException as error:
        record["error"] = repr(error)
        raise
    finally:
        record["ended_utc"] = now(); save()
    print(json.dumps({"status": record["status"], "report": str(args.output / "acceptance.json")}), flush=True)

if __name__ == "__main__":
    main()
