#!/usr/bin/env python3
"""Replay existing P2 traces and describe paired candidate competition; no search."""
from __future__ import annotations

import argparse
import bisect
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
import math
import mmap
from pathlib import Path
import statistics
import struct
import sys
import tempfile

RUN = Path(__file__).resolve().parents[1]
ROOT = Path("/data/netg/ACSG")
ALIASES = {"geom_weighted": "geom_probability", "oracle_weighted": "oracle_probability"}
PAIRS = (("geom_unified", "geom_uniform"),
         ("geom_unified", "geom_probability"),
         ("oracle_unified", "oracle_probability"))
REGIONAL = {"geom_uniform", "geom_probability", "oracle_probability"}
THRESHOLDS = (.1, .2, .5, .8)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path):
    with Path(path).open() as stream:
        return json.load(stream)


def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def canonical(method):
    return ALIASES.get(method, method)


class SparseLabels:
    """Map the small region artifact and touch only nodes present in traces."""
    def __init__(self, model_path):
        self.model_path = Path(model_path).resolve()
        self.model = read_json(self.model_path)
        require(self.model.get("status") == "COMPLETE", "model is not COMPLETE")
        self.dataset = self.model["dataset"]
        path = Path(self.model["labels_file"])
        self.path = path if path.is_absolute() else self.model_path.parent / path
        size = self.path.stat().st_size
        require(size > 0 and size % 2 == 0, "invalid uint16 labels size")
        self.n = size // 2
        if "region_sizes" in self.model:
            require(sum(self.model["region_sizes"]) == self.n, "model/labels row count mismatch")
        self.stream = self.path.open("rb")
        self.mapping = mmap.mmap(self.stream.fileno(), 0, access=mmap.ACCESS_READ)
        self.observed = {}

    def __call__(self, node):
        require(0 <= node < self.n, "trace node outside region map")
        if node not in self.observed:
            region = struct.unpack_from("<H", self.mapping, node * 2)[0]
            require(region < self.model["region_count"], "invalid sparse region label")
            self.observed[node] = region
        return self.observed[node]

    def evidence(self):
        observed = sorted(self.observed.items())
        return {"model_file": str(self.model_path), "model_sha256": sha(self.model_path),
                "labels_file": str(self.path), "labels_bytes": self.n * 2,
                "labels_sha256_inherited_from_model": self.model.get("labels_sha256"),
                "whole_labels_checksum_recomputed": False,
                "access": "Read-only mmap; sparse node/parent lookup; no base/GT/graph read",
                "observed_node_count": len(observed),
                "observed_node_region_pairs_sha256": hashlib.sha256(
                    json.dumps(observed, separators=(",", ":")).encode()).hexdigest()}

    def close(self):
        self.mapping.close()
        self.stream.close()


def route_of(row):
    route = {name: row[name] for name in
             ("entry_ids", "fast_anchor_id", "shared_seed", "actual_entry_count", "regions", "weights")}
    require(len(route["regions"]) == len(route["weights"]) <= 4, "invalid route region/weight lengths")
    require(len(set(route["regions"])) == len(route["regions"]), "duplicate active region")
    require(all(math.isfinite(w) and w >= 0 for w in route["weights"]), "invalid route weight")
    seeds = ([route["shared_seed"]] if route["shared_seed"] >= 0 else []) + route["entry_ids"]
    require(all(isinstance(x, int) and x >= 0 for x in seeds), "invalid route seed")
    require(len(seeds) == len(set(seeds)) == route["actual_entry_count"], "route seed count/dedup mismatch")
    require(route["fast_anchor_id"] in seeds, "Fast anchor was not retained")
    return route


def capacities(route, l, method):
    active = len(route["regions"])
    if method not in REGIONAL or active == 0:
        return [l]
    shared = l // 4
    remainder = l - shared - 4 * active
    require(shared >= 1 and remainder >= 0, "candidate capacity minima violated")
    total = sum(route["weights"])
    require(math.isfinite(total) and total > 0, "regional route has no finite positive mass")
    portions = [remainder * (1 / active if method == "geom_uniform" else w / total)
                for w in route["weights"]]
    floors = [math.floor(value) for value in portions]
    extra_order = sorted(range(active), key=lambda i: (-(portions[i] - floors[i]), route["regions"][i]))
    output = [shared] + [4 + value for value in floors]
    for i in extra_order[:remainder - sum(floors)]:
        output[i + 1] += 1
    require(sum(output) == l, "capacity sum does not equal L")
    return output


def final_state(node):
    if node is None:
        return "not_discovered"
    if node["decision"] == "reject":
        return "rejected"
    if node["expanded_at"] is None:
        return "evicted_unexpanded"
    return "expanded_evicted" if node["evicted_at"] is not None else "expanded_retained"


def replay(trace, row, method, k, labels=None):
    """Independent event-state reconstruction, including the weighted scheduler."""
    method = canonical(method)
    route = route_of(row)
    l = trace["L"]
    caps = capacities(route, l, method)
    queues = [[] for _ in caps]
    credits = [0.0 for _ in caps]
    peaks = [0 for _ in caps]
    nodes = {}
    pending = None
    eviction_pending_for = None
    current_expanded = None
    counters = Counter()
    per_queue = [Counter() for _ in caps]
    seed_order = []
    expanded_order = []
    require(trace.get("gt_associated_after_search") is True, "trace lacks post-search GT association contract")
    require(trace.get("timing_publishable") is False, "trace must not be publishable timing")
    for sequence, event in enumerate(trace["events"]):
        kind, node_id, owner = event["kind"], event["id"], event["queue"]
        require(kind in {"discover", "accept", "reject", "evict", "expand"}, "unknown event kind")
        require(isinstance(node_id, int) and node_id >= 0, "invalid event node")
        require(isinstance(owner, int) and 0 <= owner < len(caps), "invalid event queue")
        require(math.isfinite(event["distance"]), "nonfinite trace distance")
        require(isinstance(event["is_gt10"], bool), "missing/bad GT flag")
        if eviction_pending_for is not None:
            require(kind == "accept" and node_id == eviction_pending_for,
                    "eviction is not immediately followed by admission of its replacing candidate")
        queue = queues[owner]
        counters[kind] += 1
        per_queue[owner][kind] += 1
        if kind == "discover":
            require(pending is None, "new discovery before previous admission decision")
            require(node_id not in nodes, "duplicate discovery violates shared visited/NDC")
            parent = event["parent"]
            require(parent == -1 and current_expanded is None or parent == current_expanded,
                    "discovery parent is not the current expansion, or seed appears after expansion began")
            require(not event["expanded"], "discovery is already expanded")
            region = labels(node_id) if labels else None
            if labels and len(caps) > 1:
                expected_owner = 0
                if node_id != route["shared_seed"] and region in route["regions"]:
                    expected_owner = 1 + route["regions"].index(region)
                require(owner == expected_owner, "node admitted to wrong region/shared queue")
            nodes[node_id] = {"id": node_id, "parent": parent, "queue": owner,
                              "distance": event["distance"], "is_gt10": event["is_gt10"],
                              "region": region, "discovered_at": sequence, "decision": None,
                              "accepted_at": None, "rejected_at": None, "expanded_at": None,
                              "evicted_at": None, "evicted_by": None}
            if parent == -1:
                seed_order.append(node_id)
            pending = node_id
            continue
        require(node_id in nodes, "event before discovery")
        node = nodes[node_id]
        require(node["queue"] == owner and node["distance"] == event["distance"] and
                node["is_gt10"] == event["is_gt10"], "node metadata changed within trace")
        if kind in {"accept", "reject"}:
            require(pending == node_id, "admission is not for the pending discovery")
            require(node["decision"] is None, "multiple admission decisions")
            require(event["parent"] == node["parent"] and not event["expanded"], "bad admission event")
            node["decision"] = kind
            if kind == "accept":
                require(len(queue) < caps[owner], "accept exceeds fixed capacity")
                position = bisect.bisect_right([nodes[x]["distance"] for x in queue], node["distance"])
                queue.insert(position, node_id)
                peaks[owner] = max(peaks[owner], len(queue))
                node["accepted_at"] = sequence
            else:
                require(len(queue) == caps[owner] and node["distance"] >= nodes[queue[-1]]["distance"],
                        "rejection is not explained by the queue bound")
                node["rejected_at"] = sequence
                node["rejection_bound"] = {"id": queue[-1], "distance": nodes[queue[-1]]["distance"],
                                           "expanded": nodes[queue[-1]]["expanded_at"] is not None}
            pending = None
            eviction_pending_for = None
        elif kind == "evict":
            require(len(queue) == caps[owner] and queue[-1] == node_id, "eviction is not the full queue's worst node")
            incoming = event["parent"]  # This field is the replacing candidate, not a graph parent.
            require(incoming == pending and incoming in nodes and nodes[incoming]["queue"] == owner and
                    nodes[incoming]["decision"] is None and
                    nodes[incoming]["distance"] < node["distance"], "invalid replacing candidate")
            require(event["expanded"] == (node["expanded_at"] is not None), "eviction expansion flag mismatch")
            require(node["evicted_at"] is None, "node evicted twice")
            queue.pop()
            node["evicted_at"] = sequence
            node["evicted_by"] = incoming
            eviction_pending_for = incoming
            name = "evicted_expanded" if event["expanded"] else "evicted_unexpanded"
            counters[name] += 1
            per_queue[owner][name] += 1
        else:
            require(pending is None, "expansion before pending candidate admission")
            require(node_id in queue and node["expanded_at"] is None and event["expanded"],
                    "expansion of absent/already expanded node")
            live = {}
            for q, retained in enumerate(queues):
                head_candidate = next((x for x in retained if nodes[x]["expanded_at"] is None), None)
                if head_candidate is None:
                    credits[q] = 0.0
                else:
                    live[q] = head_candidate
                    credits[q] += caps[q]
            chosen = max(live, key=lambda q: (credits[q], -q))
            require(chosen == owner and live[chosen] == node_id, "expansion violates weighted scheduler or queue order")
            credits[chosen] -= sum(caps[q] for q in live)
            node["expanded_at"] = sequence
            expanded_order.append(node_id)
            current_expanded = node_id
    expected_seeds = ([route["shared_seed"]] if route["shared_seed"] >= 0 else []) + route["entry_ids"]
    require(seed_order == expected_seeds, "actual seed discovery order differs from route")
    require(pending is None and eviction_pending_for is None, "unfinished candidate admission")
    require(all(node["decision"] is not None for node in nodes.values()), "discovery lacks admission decision")
    require(all(nodes[node]["expanded_at"] is not None for queue in queues for node in queue),
            "trace terminates with retained unexpanded candidates")
    require(len(nodes) == trace["ndc"], "trace NDC does not equal unique discoveries")
    if "graph_ndc" in row:
        require(row["graph_ndc"] == len(nodes), "aligned/trace graph NDC mismatch")
    ordered = sorted(nodes, key=lambda node: nodes[node]["distance"])
    expected_ids = ordered[:k] + [-1] * max(0, k - len(ordered))
    require(trace["result_ids"] == row["result_ids"] == expected_ids,
            "global result IDs differ from all evaluated nodes sorted with stable distance ties")
    returned_gt = [node for node in expected_ids if node >= 0 and nodes[node]["is_gt10"]]
    require(abs(row["recall"] - len(returned_gt) / k) <= 1e-12, "GT flags do not reconstruct aligned Recall")
    gt_nodes = [node for node in nodes.values() if node["is_gt10"]]
    require(len(gt_nodes) <= k, "more GT10 nodes discovered than expected K")
    stages = {"discovered": sorted(node["id"] for node in gt_nodes),
              "accepted": sorted(node["id"] for node in gt_nodes if node["decision"] == "accept"),
              "rejected": sorted(node["id"] for node in gt_nodes if node["decision"] == "reject"),
              "evicted_unexpanded": sorted(node["id"] for node in gt_nodes if final_state(node) == "evicted_unexpanded"),
              "evicted_after_expansion": sorted(node["id"] for node in gt_nodes if final_state(node) == "expanded_evicted"),
              "expanded": sorted(node["id"] for node in gt_nodes if node["expanded_at"] is not None),
              "returned": sorted(returned_gt)}
    cross = {"status": "NOT_AVAILABLE", "reason": "No --model region artifact supplied; queue0 is not a real region ID"}
    if labels:
        edges = [node for node in nodes.values() if node["parent"] >= 0]
        crossing = [node for node in edges if node["region"] != nodes[node["parent"]]["region"]]
        cross = {"status": "OBSERVED_FIRST_DISCOVERY_EDGES_ONLY", "first_discovery_edges": len(edges),
                 "cross_region_first_discovery_edges": len(crossing),
                 "cross_region_gt_first_discoveries": sum(node["is_gt10"] for node in crossing),
                 "discovered_region_counts": dict(sorted(Counter(node["region"] for node in nodes.values()).items())),
                 "expanded_region_counts": dict(sorted(Counter(nodes[node]["region"] for node in expanded_order).items())),
                 "discovered_outside_active_regions": sum(node["region"] not in route["regions"] for node in nodes.values()),
                 "expanded_outside_active_regions": sum(nodes[node]["region"] not in route["regions"] for node in expanded_order),
                 "limitation": "Repeated/visited adjacency edges are not logged; these are not total traversed-edge counts"}
    summary = {"query_id": row["query_id"], "method": method, "L": l, "K": k,
               "recall": row["recall"], "result_ids": expected_ids, "route": route,
               "capacity": caps, "peak_retained_per_queue": peaks,
               "events": dict(counters), "events_per_queue": [dict(value) for value in per_queue],
               "node_final_states": dict(Counter(final_state(node) for node in nodes.values())),
               "gt_stage_ids": stages, "gt_not_discovered_count": k - len(gt_nodes),
               "cross_region": cross, "all_retained_expanded_at_termination": True,
               "queue_rejection_does_not_imply_result_loss": True}
    return {"summary": summary, "nodes": nodes}


def witness_paths(source, other, targets):
    """Observed discovery-tree paths, never a claim of unique causal bridges."""
    result = []
    for target in sorted(targets):
        chain = []
        node = source["nodes"][target]
        while True:
            chain.append(node["id"])
            if node["parent"] < 0:
                break
            node = source["nodes"][node["parent"]]
        chain.reverse()
        witnesses = []
        new_ancestors = []
        for ancestor in chain[:-1]:
            before = other["nodes"].get(ancestor)
            now = source["nodes"][ancestor]
            state = final_state(before)
            if state in {"rejected", "evicted_unexpanded"}:
                witnesses.append({"id": ancestor, "is_gt10": now["is_gt10"], "region": now["region"],
                                  "other_state": state, "other_queue": before["queue"],
                                  "other_evicted_by": before["evicted_by"],
                                  "source_expanded_at": now["expanded_at"]})
            elif state == "not_discovered":
                new_ancestors.append(ancestor)
        result.append({"target_id": target, "first_discovery_path": chain,
                       "expanded_ancestors_rejected_or_evicted_unexpanded_in_other": witnesses,
                       "ancestors_not_discovered_in_other": new_ancestors,
                       "causal_bridge_proven": False})
    return result


def compare(base, regional):
    a, b = base["summary"], regional["summary"]
    require(a["route"] == b["route"], "paired queue controls have different actual routes")
    require((a["query_id"], a["L"], a["K"]) == (b["query_id"], b["L"], b["K"]), "comparison identity mismatch")
    for node in set(base["nodes"]) & set(regional["nodes"]):
        require(base["nodes"][node]["is_gt10"] == regional["nodes"][node]["is_gt10"], "paired GT flags disagree")
        require(base["nodes"][node]["distance"] == regional["nodes"][node]["distance"], "paired raw node distances disagree")
    before, after = set(a["gt_stage_ids"]["returned"]), set(b["gt_stage_ids"]["returned"])
    rescued_targets, harmed_targets = after - before, before - after
    transitions = Counter()
    extra_expanded = defaultdict(list)
    lost_expanded = defaultdict(list)
    for node in sorted(set(base["nodes"]) | set(regional["nodes"])):
        x, y = base["nodes"].get(node), regional["nodes"].get(node)
        sx, sy = final_state(x), final_state(y)
        transitions[f"{sx} -> {sy}"] += 1
        if y is not None and y["expanded_at"] is not None and (x is None or x["expanded_at"] is None):
            extra_expanded[sx].append(node)
        if x is not None and x["expanded_at"] is not None and (y is None or y["expanded_at"] is None):
            lost_expanded[sy].append(node)
    recovered_paths = witness_paths(regional, base, rescued_targets)
    harmed_paths = witness_paths(base, regional, harmed_targets)
    recovery_witnesses = {node["id"]: node for path in recovered_paths
                          for node in path["expanded_ancestors_rejected_or_evicted_unexpanded_in_other"]}
    harm_witnesses = {node["id"]: node for path in harmed_paths
                      for node in path["expanded_ancestors_rejected_or_evicted_unexpanded_in_other"]}
    return {"query_id": a["query_id"], "L": a["L"], "baseline": a["method"], "regional": b["method"],
            "same_route_verified": True, "baseline_recall": a["recall"], "regional_recall": b["recall"],
            "recall_delta_pp": (b["recall"] - a["recall"]) * 100,
            "rescued_gt_result_ids": sorted(rescued_targets), "newly_harmed_gt_result_ids": sorted(harmed_targets),
            "baseline_ndc": a["events"]["discover"], "regional_ndc": b["events"]["discover"],
            "baseline_expanded": a["events"].get("expand", 0), "regional_expanded": b["events"].get("expand", 0),
            "baseline_evicted_unexpanded": a["events"].get("evicted_unexpanded", 0),
            "regional_evicted_unexpanded": b["events"].get("evicted_unexpanded", 0),
            "all_node_state_transitions": dict(transitions),
            "regional_extra_expanded_ids_by_baseline_state": dict(extra_expanded),
            "baseline_extra_expanded_ids_by_regional_state": dict(lost_expanded),
            "rescued_target_discovery_paths": recovered_paths, "harmed_target_discovery_paths": harmed_paths,
            "recovery_path_retention_witness_count": len(recovery_witnesses),
            "recovery_path_non_gt_retention_witness_count": sum(not node["is_gt10"] for node in recovery_witnesses.values()),
            "harm_path_retention_witness_count": len(harm_witnesses),
            "harm_path_non_gt_retention_witness_count": sum(not node["is_gt10"] for node in harm_witnesses.values()),
            "thresholds": {str(t): {"rescued_query": a["recall"] < t <= b["recall"],
                                     "newly_harmed_query": b["recall"] < t <= a["recall"]} for t in THRESHOLDS},
            "interpretation": "Witnesses are expanded nonterminal nodes on observed discovery paths that the paired control rejected or evicted before expansion. They may be non-GT nodes. This does not prove a unique necessary bridge or exclude alternative unobserved paths."}


def input_batches(path):
    path = Path(path).resolve()
    if path.is_dir():
        parts = path
        manifest = read_json(parts / "manifest.json")
        batches = sorted(parts.glob("batch_*.json"), key=lambda p: int(p.stem.removeprefix("batch_")))
        require(batches, "parts directory has no completed batch artifacts")
        return manifest, [(read_json(batch), batch) for batch in batches], parts, [parts / "manifest.json", *batches]
    value = read_json(path)
    if "results" in value:
        parts = Path(value["parts_directory"])
        if not parts.is_absolute():
            # The evaluator records output + '.parts', relative to its cwd.
            parts = ROOT / parts
        return value, [(batch, path) for batch in value["results"]], parts.resolve(), [path]
    require("trace_files" in value, "input must be an evaluator trace result, batch, or .parts directory")
    parts = path.parent
    return read_json(parts / "manifest.json"), [(value, path)], parts, [parts / "manifest.json", path]


def analyze(inputs, protocol, label_maps):
    allowed = set(protocol["p2_preregistered"]["trace_query_ids"])
    allowed_ls = set(protocol["p2_preregistered"]["search_Ls"])
    require(protocol["p2_preregistered"]["top_k"] == 10, "P2 trace protocol requires K10")
    observations, evidence, provenance = {}, {}, {}
    for path in inputs:
        meta, batches, parts, source_files = input_batches(path)
        require(meta.get("measurement") == "trace", "analysis accepts only independent trace outputs")
        require(meta.get("cpu_only") is True and meta.get("heldout_accessed") is False,
                "trace must affirm CPU-only execution and no held-out access")
        require(meta.get("split") == "pilot" and meta.get("source_query_type") == "drl_train",
                "prespecified trace IDs refer only to development pilot rows")
        require(meta.get("top_k") == 10 and meta.get("stage") == "P2", "trace must be P2 K10")
        dataset = meta["dataset"]
        require(dataset in protocol["datasets"], "unregistered dataset")
        model = meta.get("model_manifest") or {}
        signature = (meta["index_file"], meta["fast_hubs"], meta["fast_ids"],
                     model.get("labels_sha256"), model.get("profiles_sha256"), model.get("portals_sha256"))
        require(dataset not in provenance or provenance[dataset] == signature,
                "mixed graph/Fast/model provenance within one dataset")
        provenance[dataset] = signature
        labels = label_maps.get(dataset)
        if labels:
            require(model.get("labels_sha256") == labels.model.get("labels_sha256"), "--model and trace labels hashes differ")
            require(model.get("profiles_sha256") == labels.model.get("profiles_sha256") and
                    model.get("portals_sha256") == labels.model.get("portals_sha256"), "--model and trace profile/portal hashes differ")
        for source in source_files:
            evidence[str(source)] = {"sha256": sha(source), "bytes": source.stat().st_size}
        for batch, batch_path in batches:
            require(batch.get("round") == 0 and batch.get("top_k") == 10, "trace batch must be one round at K10")
            method = canonical(batch["method"])
            require(batch["search_L"] in allowed_ls, "unregistered trace L")
            rows = {row["query_id"]: row for row in batch["per_query"]}
            require(len(rows) == len(batch["per_query"]), "duplicate aligned query ID")
            trace_rows = set()
            for filename in batch["trace_files"]:
                trace_path = Path(filename)
                if not trace_path.is_absolute():
                    trace_path = parts / trace_path
                trace = read_json(trace_path)
                qid = trace["query_id"]
                require(qid in allowed, f"query {qid} is not in preregistered trace selection")
                require(qid in rows and qid not in trace_rows, "missing or duplicate aligned trace query")
                trace_rows.add(qid)
                require(canonical(trace["method"]) == method and trace["L"] == batch["search_L"], "trace/batch identity mismatch")
                observed = replay(trace, rows[qid], method, 10, labels)
                observed["summary"].update(dataset=dataset, trace_file=str(trace_path), trace_sha256=sha(trace_path),
                                           batch_source=str(batch_path))
                key = (dataset, batch["search_L"], method, qid)
                if key in observations:
                    require(observations[key]["summary"]["trace_sha256"] == observed["summary"]["trace_sha256"],
                            "conflicting duplicate trace observation")
                else:
                    observations[key] = observed
                evidence[str(trace_path)] = {"sha256": sha(trace_path), "bytes": trace_path.stat().st_size}
            require(trace_rows == set(rows), "some aligned trace rows lack completed trace artifacts")
    require(observations, "no trace observations found")
    comparisons, groups, missing = [], [], []
    dataset_ls = [(dataset, l) for dataset in protocol["datasets"] for l in sorted(allowed_ls)]
    for dataset, l in dataset_ls:
        for baseline, regional in PAIRS:
            before = {qid for ds, cap, method, qid in observations if (ds, cap, method) == (dataset, l, baseline)}
            after = {qid for ds, cap, method, qid in observations if (ds, cap, method) == (dataset, l, regional)}
            if not before or not after:
                missing.append({"dataset": dataset, "L": l, "comparison": [baseline, regional],
                                "reason": "one or both methods were not observed",
                                "baseline_query_ids": sorted(before), "regional_query_ids": sorted(after)})
                continue
            paired_ids = before & after
            if before != after:
                missing.append({"dataset": dataset, "L": l, "comparison": [baseline, regional],
                                "reason": "incomplete input coverage; only explicitly listed complete query pairs are analyzed",
                                "baseline_only_query_ids": sorted(before - after),
                                "regional_only_query_ids": sorted(after - before)})
            if not paired_ids:
                continue
            values = []
            for qid in sorted(paired_ids):
                pair = compare(observations[dataset, l, baseline, qid], observations[dataset, l, regional, qid])
                pair["dataset"] = dataset
                comparisons.append(pair)
                values.append(pair)
            groups.append({"dataset": dataset, "L": l, "baseline": baseline, "regional": regional,
                           "num_queries": len(values), "actual_query_ids": sorted(paired_ids),
                           "unobserved_preregistered_query_ids": sorted(allowed - paired_ids),
                           "mean_recall_delta_pp_on_selected_subset": statistics.mean(x["recall_delta_pp"] for x in values),
                           "rescued_gt_targets": sum(len(x["rescued_gt_result_ids"]) for x in values),
                           "newly_harmed_gt_targets": sum(len(x["newly_harmed_gt_result_ids"]) for x in values),
                           "queries_with_recovery_retention_witness": sum(x["recovery_path_retention_witness_count"] > 0 for x in values),
                           "queries_with_non_gt_recovery_retention_witness": sum(x["recovery_path_non_gt_retention_witness_count"] > 0 for x in values),
                           "queries_with_harm_retention_witness": sum(x["harm_path_retention_witness_count"] > 0 for x in values),
                           "sum_baseline_expanded": sum(x["baseline_expanded"] for x in values),
                           "sum_regional_expanded": sum(x["regional_expanded"] for x in values),
                           "sum_baseline_evicted_unexpanded": sum(x["baseline_evicted_unexpanded"] for x in values),
                           "sum_regional_evicted_unexpanded": sum(x["regional_evicted_unexpanded"] for x in values),
                           "threshold_counts": {str(t): {"rescued": sum(x["thresholds"][str(t)]["rescued_query"] for x in values),
                                                          "newly_harmed": sum(x["thresholds"][str(t)]["newly_harmed_query"] for x in values)} for t in THRESHOLDS},
                           "population_inference_allowed": False})
    actual = sorted({qid for _, _, _, qid in observations})
    observed_dataset_ls = sorted({(dataset, l) for dataset, l, _, _ in observations})
    all_groups_cover_selection = bool(groups) and not missing and all(
        set(group["actual_query_ids"]) == allowed for group in groups)
    return {"status": "COMPLETE_ANALYSIS", "stage_gate_decision": None,
            "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "scope": "Descriptive replay of existing preselected pilot traces; no new ANN query or population inference",
            "preselected_query_ids": sorted(allowed), "actual_query_ids_union": actual,
            "unobserved_preselected_query_ids": sorted(allowed - set(actual)),
            "selection_coverage": "FULL_REGISTERED_LIST" if set(actual) == allowed else "PARTIAL_PRESELECTED_SUBSET",
            "selection_coverage_scope": "Query-ID union across observed cells; full matrix coverage is separate below",
            "all_present_comparisons_cover_full_selection": all_groups_cover_selection,
            "registered_matrix_coverage": {
                "expected_dataset_L_comparison_cells": len(dataset_ls) * len(PAIRS),
                "expected_query_pairs": len(dataset_ls) * len(PAIRS) * len(allowed),
                "observed_cells_with_complete_pairs": len(groups), "observed_query_pairs": len(comparisons),
                "missing_dataset_L_cells": [{"dataset": dataset, "L": l} for dataset, l in dataset_ls
                                            if (dataset, l) not in observed_dataset_ls],
                "observed_dataset_L_cells": [{"dataset": dataset, "L": l} for dataset, l in observed_dataset_ls],
                "full_registered_matrix_complete": all_groups_cover_selection},
            "trace_count": len(observations), "comparison_count": len(comparisons),
            "groups": groups, "paired_queries": comparisons,
            "trace_summaries": [value["summary"] for _, value in sorted(observations.items())],
            "missing_comparisons": missing, "evidence": evidence,
            "sparse_region_evidence": {dataset: labels.evidence() for dataset, labels in label_maps.items()},
            "limitations": ["Preselected small trace subsets do not estimate full-pilot prevalence or establish performance improvement.",
                            "No timing or CI is inferred from trace instrumentation. Oracle traces never enter a deployment frontier.",
                            "A returned GT may have been rejected by its candidate queue; global top-K is independently reconstructed.",
                            "A retention witness is an observed nonterminal discovery-path node, possibly non-GT. Alternative unobserved paths remain possible; causal bridge necessity is not proven.",
                            "Only first-discovery parent edges are recorded, so cross-region counts exclude already-visited adjacency accesses.",
                            "Failure at threshold t means Recall@10 < t, matching existing ACSG tail reporting."]}


def self_test():
    # Hand-authored traces, independent of the replay scheduler implementation.
    def event(kind, node, parent=-1, owner=0, distance=None, expanded=False):
        return {"kind": kind, "id": node, "parent": parent, "queue": owner,
                "distance": float(node if distance is None else distance), "expanded": expanded,
                "is_gt10": node == 9}
    route = {"entry_ids": [], "fast_anchor_id": 0, "shared_seed": 0, "actual_entry_count": 1,
             "regions": [1], "weights": [1.0], "query_id": 0}
    common = [event("discover", 0), event("accept", 0), event("expand", 0, expanded=True)]
    unified, protected = list(common), list(common)
    for node in range(1, 8):
        unified += [event("discover", node, 0), event("accept", node, 0)]
        protected += [event("discover", node, 0), event("accept" if node == 1 else "reject", node, 0)]
    unified += [event("discover", 8, 0, distance=100), event("reject", 8, 0, distance=100)]
    unified += [event("expand", node, expanded=True) for node in range(1, 8)]
    protected += [event("discover", 8, 0, 1, 100), event("accept", 8, 0, 1, 100),
                  event("expand", 8, owner=1, distance=100, expanded=True),
                  event("discover", 9, 8, 1, -100), event("accept", 9, 8, 1, -100),
                  event("expand", 1, expanded=True), event("expand", 9, owner=1, distance=-100, expanded=True)]
    def package(events, results, ndc):
        return {"L": 8, "events": events, "result_ids": results, "ndc": ndc,
                "gt_associated_after_search": True, "timing_publishable": False}
    labels = lambda node: int(node in (8, 9))
    a = replay(package(unified, [0, 1], 9), dict(route, result_ids=[0, 1], recall=0), "geom_unified", 2, labels)
    b = replay(package(protected, [9, 0], 10), dict(route, result_ids=[9, 0], recall=.5), "geom_probability", 2, labels)
    paired = compare(a, b)
    require(paired["rescued_gt_result_ids"] == [9] and paired["recovery_path_non_gt_retention_witness_count"] == 1,
            "non-GT bridge witness not recovered")
    require(paired["rescued_target_discovery_paths"][0]["first_discovery_path"] == [0, 8, 9], "wrong discovery path")
    require(b["summary"]["cross_region"]["cross_region_first_discovery_edges"] == 1, "wrong cross-region count")
    evictions = [event("discover", 0), event("accept", 0), event("expand", 0, expanded=True),
                 event("discover", 1, 0, distance=10), event("accept", 1, 0, distance=10),
                 event("discover", 2, 0, distance=5), event("evict", 1, 2, distance=10), event("accept", 2, 0, distance=5),
                 event("discover", 3, 0, distance=-1), event("evict", 2, 3, distance=5), event("accept", 3, 0, distance=-1),
                 event("expand", 3, distance=-1, expanded=True), event("discover", 9, 3, distance=-2),
                 event("evict", 0, 9, expanded=True), event("accept", 9, 3, distance=-2), event("expand", 9, distance=-2, expanded=True)]
    packet = package(evictions, [9, 3], 5); packet["L"] = 2
    item = replay(packet, dict(route, result_ids=[9, 3], recall=.5), "geom_unified", 2)
    require(item["summary"]["events"]["evicted_unexpanded"] == 2 and
            item["summary"]["events"]["evicted_expanded"] == 1, "eviction states conflated")
    require(item["nodes"][1]["parent"] == 0 and item["nodes"][1]["evicted_by"] == 2,
            "eviction replacing candidate confused with discovery parent")
    rejected = 0
    for change in ("duplicate_discovery", "wrong_result", "wrong_region_owner", "unfinished", "different_route", "historical_parent"):
        try:
            if change == "different_route":
                changed = json.loads(json.dumps(b)); changed["summary"]["route"]["weights"] = [.5]
                compare(a, changed)
            else:
                bad = json.loads(json.dumps(package(protected, [9, 0], 10)))
                if change == "duplicate_discovery": bad["events"].insert(1, bad["events"][0])
                if change == "wrong_result": bad["result_ids"] = [0, 9]
                if change == "wrong_region_owner": bad["events"][17]["queue"] = 0
                if change == "unfinished": bad["events"].pop()
                if change == "historical_parent": bad["events"][20]["parent"] = 0
                replay(bad, dict(route, result_ids=[9, 0], recall=.5), "geom_probability", 2, labels)
        except ValueError:
            rejected += 1
    require(rejected == 6, "malformed trace or unmatched route accepted")
    # Exercise the public evaluator-file adapter with a complete, tiny fixture.
    with tempfile.TemporaryDirectory(prefix="trace_analyzer_selftest_", dir=RUN / "p2") as folder:
        folder = Path(folder)
        fixture_parts = folder / "fixture.parts"; fixture_parts.mkdir()
        seed_row = dict(route, regions=[0, 1, 2, 3], weights=[.25] * 4,
                        result_ids=[0] + [-1] * 9, recall=0, graph_ndc=1)
        fixture_batches = []
        for method in ("geom_unified", "geom_uniform", "geom_probability"):
            trace = package(common, seed_row["result_ids"], 1)
            trace.update(L=64, method=method, query_id=0)
            name = method + ".json"; write_new(fixture_parts / name, trace)
            fixture_batches.append({"method": method, "round": 0, "top_k": 10, "search_L": 64,
                                    "per_query": [seed_row], "trace_files": [name]})
        meta = {"measurement": "trace", "stage": "P2", "split": "pilot", "source_query_type": "drl_train",
                "cpu_only": True, "heldout_accessed": False,
                "top_k": 10, "dataset": "synthetic", "index_file": "not-read", "fast_hubs": "not-read",
                "fast_ids": "not-read", "parts_directory": str(fixture_parts), "results": fixture_batches}
        fixture = folder / "fixture.json"; write_new(fixture, meta)
        fixture_protocol = {"datasets": ["synthetic"], "p2_preregistered": {
            "trace_query_ids": [0, 157], "search_Ls": [64, 128], "top_k": 10}}
        analysis = analyze([fixture], fixture_protocol, {})
        require(analysis["trace_count"] == 3 and analysis["comparison_count"] == 2 and
                analysis["selection_coverage"] == "PARTIAL_PRESELECTED_SUBSET" and
                analysis["unobserved_preselected_query_ids"] == [157], "wrong file-adapter/selection coverage")
        require(analysis["registered_matrix_coverage"]["expected_dataset_L_comparison_cells"] == 6 and
                analysis["registered_matrix_coverage"]["missing_dataset_L_cells"] == [{"dataset": "synthetic", "L": 128}],
                "missing registered working point was hidden")
        nested = folder / "nested"; nested.mkdir()
        relative_fixture = nested / "relative_output.json"
        write_new(relative_fixture, dict(meta, parts_directory=str(fixture_parts.relative_to(ROOT))))
        relative = analyze([relative_fixture], fixture_protocol, {})
        require(relative["paired_queries"] == analysis["paired_queries"], "relative parts path did not use evaluator cwd")
        missing_protocol = {"datasets": ["synthetic", "missing_dataset"], "p2_preregistered": {
            "trace_query_ids": [0], "search_Ls": [64, 128], "top_k": 10}}
        missing_matrix = analyze([fixture], missing_protocol, {})
        require(missing_matrix["selection_coverage"] == "FULL_REGISTERED_LIST" and
                not missing_matrix["registered_matrix_coverage"]["full_registered_matrix_complete"] and
                {"dataset": "missing_dataset", "L": 64} in missing_matrix["registered_matrix_coverage"]["missing_dataset_L_cells"],
                "full observed query-ID union incorrectly implies full dataset/work-point matrix")
        write_new(fixture_parts / "manifest.json", dict(meta, results=[]))
        for i, batch in enumerate(fixture_batches):
            write_new(fixture_parts / f"batch_{i}.json", batch)
        partial = analyze([fixture_parts], fixture_protocol, {})
        require(partial["paired_queries"] == analysis["paired_queries"], "parts/final JSON analysis mismatch")
        marker = folder / "existing.json"; marker.write_text("keep")
        try:
            write_new(marker, {})
            raise AssertionError("existing output was overwritten")
        except FileExistsError:
            require(marker.read_text() == "keep", "collision modified existing output")
    return {"status": "PASS_SYNTHETIC_TRACE_ANALYZER", "rejected_bad_cases": rejected,
            "tests": ["independent golden unified/regional traces", "weighted scheduler and capacities",
                      "non-GT retention path witness", "raw region crossing", "expanded/unexpanded eviction",
                      "discovery parent versus eviction replacer", "global top-K and GT Recall reconstruction",
                      "route mismatch and malformed trace rejection", "evaluator final/parts input adapter",
                      "relative parts path anchored to evaluator cwd", "explicit partial prespecified selection",
                      "missing whole dataset/work-point matrix remains visible", "output collision protection"], "real_data_read": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", type=Path, help="Completed evaluator trace JSONs or .parts directories")
    parser.add_argument("--protocol", type=Path, default=RUN / "protocol.json")
    parser.add_argument("--model", action="append", type=Path, default=[], help="Optional model JSON per dataset for sparse region lookup; repeatable")
    parser.add_argument("--output", type=Path, help="New output directory; existing artifacts are never overwritten")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), indent=2)); return
    if not args.inputs or not args.output:
        parser.error("--inputs and --output are required")
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output / "started.json", {"status": "INCOMPLETE", "kind": "EXISTING_TRACE_ANALYSIS",
                                             "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()})
    mappings = {}
    try:
        for path in args.model:
            labels = SparseLabels(path)
            require(labels.dataset not in mappings, "multiple --model inputs for one dataset")
            mappings[labels.dataset] = labels
        report = analyze(args.inputs, read_json(args.protocol), mappings)
        report["protocol_file"] = str(args.protocol.resolve())
        report["protocol_sha256"] = sha(args.protocol)
        report["source_sha256"] = sha(Path(__file__))
        write_new(args.output / "report.json", report)
        lines = ["# P2 预选查询 trace 分析", "",
                 f"已独立重放 {report['trace_count']} 条搜索 trace、完成 {report['comparison_count']} 个同入口配对。实际 query IDs：{report['actual_query_ids_union']}。",
                f"选择覆盖：{report['selection_coverage']}；未观察的预选 IDs：{report['unobserved_preselected_query_ids']}。这份小样本描述不判定 P2 gate，也不证明总体性能收益。", "",
                 f"完整预注册矩阵另行检查：{report['registered_matrix_coverage']['observed_cells_with_complete_pairs']} / {report['registered_matrix_coverage']['expected_dataset_L_comparison_cells']} 个数据集×L×比较单元有完整查询对；全矩阵及全部预选 IDs 齐全：{report['registered_matrix_coverage']['full_registered_matrix_complete']}。", "",
                 "| 数据集 | L | 对照 | 查询数 | 获得/损失 GT 结果数 | 非 GT 保留路径证据的查询数 |",
                 "| --- | --- | --- | --- | --- | --- |"]
        for group in report["groups"]:
            lines.append(f"| {group['dataset']} | {group['L']} | {group['baseline']} → {group['regional']} | {group['num_queries']} | {group['rescued_gt_targets']} / {group['newly_harmed_gt_targets']} | {group['queries_with_non_gt_recovery_retention_witness']} |")
        lines += ["", "路径证据要求中间节点在当前方法被扩展、在配对方法被拒绝或在扩展前淘汰，且实际成为新增 GT 的首次发现祖先；中间节点可以不是 GT。它不能证明该节点是必要或唯一的桥，其他未观察路径仍可能存在。", "",
                  "所有候选事件、GT 阶段、同 route 校验、扩展/未扩展淘汰、获益与受损的对称路径证据、阈值统计及证据 checksum 见 [report.json](report.json)。跨区域统计仅覆盖首次发现边，未把已 visited 的邻接访问算作已观察边。"]
        with (args.output / "report.md").open("x") as stream:
            stream.write("\n".join(lines) + "\n")
        print(json.dumps({"status": report["status"], "output": str(args.output),
                          "trace_count": report["trace_count"], "comparison_count": report["comparison_count"]}))
    except Exception as error:
        write_new(args.output / "failure.json", {"status": "FAILED_ANALYSIS", "error": str(error)})
        raise
    finally:
        for labels in mappings.values():
            labels.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"TRACE_ANALYSIS_ERROR {error}", file=sys.stderr)
        raise SystemExit(2)
