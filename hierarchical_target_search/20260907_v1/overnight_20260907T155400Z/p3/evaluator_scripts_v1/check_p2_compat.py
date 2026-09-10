#!/usr/bin/env python3
"""Check new P3 evaluator's first-32 P2 rows against saved complete P2 evidence.
No evaluator launches and no performance interpretation. All report writes are exclusive.
"""
import argparse
import hashlib
import json
from pathlib import Path

DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
METHODS = {"fast", "geom_unified", "geom_uniform", "geom_probability", "oracle_unified", "oracle_probability"}
ROUTE_RESULT = ("query_id", "recall", "result_ids", "entry_ids", "fast_anchor_id", "shared_seed", "actual_entry_count", "regions", "weights")
COUNTS = ("routing_ndc", "graph_ndc", "total_ndc", "routing_mac", "graph_mac", "total_mac", "expanded", "rejected", "evicted_unexpanded")
METADATA = ("dataset", "split", "source_query_type", "threads", "cpu_only", "metric", "dim", "base_nodes", "normalization", "artifact_version", "index_file", "model_file", "fast_hubs", "fast_ids", "model_manifest", "fast_m", "top_k", "search_Ls")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read(path, dataset, measurement, nq, rounds):
    data = json.loads(path.read_text())
    require(data["status"] == "COMPLETE", f"incomplete {path}")
    require(data["dataset"] == dataset and data["measurement"] == measurement, f"dataset/measurement {path}")
    require(data["source_query_range"] == [0, nq] and data["num_queries"] == nq and data["split"] == "pilot", f"query range {path}")
    require(data["rounds"] == rounds and data["heldout_accessed"] is False, f"round/split guard {path}")
    require(data["top_k"] == 10 and data["search_Ls"] == [64, 128] and data["fast_m"] == 3, f"K/L/m guard {path}")
    results = {}
    for result in data["results"]:
        key = result["method"], result["search_L"], result["round"]
        require(key not in results, f"duplicate result {key} {path}")
        results[key] = result
    expected = {(m, l, r) for m in METHODS for l in (64, 128) for r in range(rounds)}
    require(set(results) == expected, f"incomplete method/L/round matrix {path}")
    for m in METHODS:
        for l in (64, 128):
            first = results[m, l, 0]
            require([x["query_id"] for x in first["per_query"]] == list(range(nq)), f"query alignment {path} {m} {l}")
            for r in range(rounds):
                row = results[m, l, r]
                require(row["result_hash_fnv1a64"] == first["result_hash_fnv1a64"] and row["route_hash_fnv1a64"] == first["route_hash_fnv1a64"], f"repeat hash instability {path} {m} {l}")
    return data, results

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-p2-dir", type=Path, required=True)
    parser.add_argument("--new-dir", type=Path, required=True, help="contains webvid_count.json/webvid_timing.json and yandex counterparts")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), "output already exists")
    reports, bindings, provenance = [], [], None
    for alias, dataset in zip(("webvid", "yandex"), DATASETS):
        oldpath = args.old_p2_dir / f"{alias}_eval/count.json"
        old, oldrows = read(oldpath, dataset, "count", 10000, 1)
        countpath = args.new_dir / f"{alias}_count.json"
        timingpath = args.new_dir / f"{alias}_timing.json"
        counted, countrows = read(countpath, dataset, "count", 32, 1)
        timing, timingrows = read(timingpath, dataset, "timing", 32, 5)
        for key in METADATA:
            require(old[key] == counted[key] == timing[key], f"input metadata changed {dataset} {key}")
        require(counted["region_count"] == timing["region_count"] == 64 and counted["portals_per_region"] == timing["portals_per_region"] == 2, f"P2 shape {dataset}")
        for data in (counted, timing):
            if provenance is None:
                provenance = data["evaluator_provenance"]
            require(data["evaluator_provenance"] == provenance, "new evaluator source/binary differs across files")
        compared = 0
        for method in sorted(METHODS):
            for l in (64, 128):
                baseline = oldrows[method, l, 0]["per_query"][:32]
                newcount = countrows[method, l, 0]["per_query"]
                newplain = timingrows[method, l, 0]["per_query"]
                for before, after, plain in zip(baseline, newcount, newplain):
                    for key in ROUTE_RESULT + COUNTS:
                        require(before[key] == after[key], f"P2 count compatibility {dataset} {method} L{l} q{before['query_id']} {key}")
                    for key in ROUTE_RESULT:
                        require(after[key] == plain[key], f"P3 count/plain compatibility {dataset} {method} L{l} q{before['query_id']} {key}")
                    compared += 1
        reports.append({"dataset": dataset, "aligned_query_method_L_rows": compared, "count_fields": list(COUNTS), "route_result_fields": list(ROUTE_RESULT), "five_timing_rounds_stable": True})
        bindings.extend({"path": str(p.resolve()), "sha256": sha(p)} for p in (oldpath, countpath, timingpath))
    for prefix in ("source", "binary"):
        require(sha(Path(provenance[f"{prefix}_path"])) == provenance[f"{prefix}_sha256"], f"current {prefix} differs from recorded build execution")
    output = {"schema_version": 1, "status": "PASS", "scope": "P1 reacceptance: first32 saved P2 queries, 64regions2portals, both datasets6methods2Ls; no new performance claim", "datasets": reports, "inputs": bindings, "evaluator_provenance": provenance, "script_sha256": sha(Path(__file__)), "heldout_accessed": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(output, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "PASS", "output": str(args.output), "aligned_rows": sum(x["aligned_query_method_L_rows"] for x in reports)}))

if __name__ == "__main__":
    main()
