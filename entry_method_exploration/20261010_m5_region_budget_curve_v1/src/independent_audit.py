#!/usr/bin/env python3
"""Independent E175 ID/set, wall, receipt and trace audit, AFTER all native jobs.

Does not import the evaluator, read vector values/base/index, compute distances,
generate GT, fit, or run ANN. Merely writing/parsing this file is not execution.
The entire administrative gate runs before any GT or return packet is decoded.
"""
import argparse
import array
import csv
import hashlib
import json
import math
import statistics
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ("webvid2_5m_light_v1", "yandex_t2i_official10M_ip_v1")
ROLES = ("public_test",)
METHODS = ("NSG", "GT", "M5", "M5REG96")
L_VALUES = (200, 400, 800, 1000, 1200)
N_QUERY = 10000
LIMITS = {
    "count_scope": "fixed 256 only; post included in graph_ndc",
    "same_pair": "same KL round matched sequential methods",
    "cross_pair": "cross L round index only, descriptive, not simultaneous or randomized pairing",
    "bootstrap": "descriptive paired query bootstrap, no semantic IID or simultaneous comparison guarantee",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text())


class Sources:
    """Hash only bounded original labels/models/returns; never giant inputs."""
    def __init__(self):
        self.files = {}

    def digest(self, path, expected=None):
        p = Path(path)
        if str(p) not in self.files:
            before = p.stat()
            require(before.st_size <= 64 * 1024 * 1024,
                    f"refuse large hash (base/index must remain stat-only): {p}")
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            after = p.stat()
            require(stat4(before) == stat4(after), f"source changed during hash: {p}")
            self.files[str(p)] = {"sha256": h.hexdigest(), "stat4": stat4(after)}
        actual = self.files[str(p)]["sha256"]
        require(expected is None or actual == expected, f"SHA mismatch: {p}")
        return actual

    def adopt_stat_only(self, path, expected_sha, expected_stat, preflight):
        # Registered preflight full SHA + current frozen metadata. No query
        # vector bytes (original fvecs or derived f32) are opened here.
        p = Path(path)
        record = preflight["registered_input_files"][str(p)]
        require(record["sha256"] == expected_sha and len(expected_sha) == 64,
                f"registered preflight full-SHA closure: {p}")
        current = stat4(p.stat())
        require(current == expected_stat, f"stat-only input identity: {p}")
        require(str(p) not in self.files or self.files[str(p)]["sha256"] == expected_sha,
                f"consistent source identity: {p}")
        self.files[str(p)] = {"sha256": expected_sha, "stat4": current,
                             "verification_scope": "actual preflight full SHA plus current stat4; not rehashed by independent audit"}

    def stable(self):
        for name, record in self.files.items():
            require(stat4(Path(name).stat()) == record["stat4"],
                    f"source changed during audit: {name}")


def stat4(s):
    return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns]


def ints(path, typecode, count, sources, expected=None):
    sources.digest(path, expected)
    data = array.array(typecode)
    require(data.itemsize == {"i": 4, "I": 4, "q": 8, "Q": 8}[typecode],
            "registered fixed integer ABI")
    require(Path(path).stat().st_size == count * data.itemsize, f"raw size: {path}")
    with Path(path).open("rb") as f:
        data.fromfile(f, count)
    if sys.byteorder != "little":
        data.byteswap()
    return data


def official_GT_prefix(path, n, container_n):
    # Decode only existing official GT ID labels, not vectors or distances.
    # Its full source SHA was verified by preflight and stat-bound above.
    p = Path(path)
    require(p.stat().st_size == container_n * 101 * 4, "official GT100 ivecs container size")
    values = array.array("i")
    require(values.itemsize == 4, "official ivecs little-endian i32 ABI")
    with p.open("rb") as f:
        values.fromfile(f, n * 101)
    if sys.byteorder != "little":
        values.byteswap()
    require(all(values[i * 101] == 100 for i in range(n)),
            "each selected original ivecs row header remains100")
    return [tuple(values[i * 101 + 1:(i + 1) * 101]) for i in range(n)]

def close(a, b, label):
    require(math.isfinite(float(a)) and math.isfinite(float(b)) and
            math.isclose(float(a), float(b), rel_tol=2e-12, abs_tol=1e-9),
            f"numeric mismatch {label}: {a!r} != {b!r}")


def field_equal(actual, expected, field):
    require(field in actual, f"missing field {field}")
    if isinstance(expected, float):
        close(actual[field], expected, field)
    elif isinstance(expected, list):
        value = actual[field]
        if isinstance(value, str):
            value = json.loads(value)
        require(len(value) == len(expected), f"list length {field}")
        for x, y in zip(value, expected):
            close(x, y, field)
    elif isinstance(expected, dict):
        value = actual[field]
        if isinstance(value, str):
            value = json.loads(value)
        require(value == expected, f"dictionary mismatch {field}")
    elif isinstance(expected, bool):
        value = actual[field]
        if isinstance(value, str):
            require(value in ("True", "False", "true", "false"), f"bool {field}")
            value = value.lower() == "true"
        require(value is expected, f"boolean mismatch {field}")
    elif isinstance(expected, int):
        require(str(actual[field]) == str(expected), f"integer mismatch {field}")
    else:
        require(actual[field] == expected, f"field mismatch {field}")


def administrative_gate(root, sources):
    """Only JSON/source hashes/stat operations; no raw GT/return decoding here."""
    state = load(root / "run_state.json")
    require(state.get("status") == "NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION"
            and state.get("active") is None, "native-complete + active=None required")
    completed = state.get("completed", [])
    require(len(completed) == 2 and all(x.get("exit_code") == 0 for x in completed),
            "two successful native exits required before GT")
    require({(x["role"], x["dataset"]) for x in completed} ==
            {(r, d) for r in ROLES for d in DATASETS}, "two unique native jobs")
    require(all(x["max_threads_observed"] == 1 for x in completed), "actual native threads")
    require(state["planned_points"] == 80 and state["planned_timed_batches"] == 240
            and state["training_increment_seconds"] == 0, "frozen native scope")
    lock = load(root / "parameter_lock.json")
    require(lock["no_new_TRAIN"] and lock["no_adaptive_cancel_or_selection"]
            and lock["primary_method"] == "M5REG96" and len(lock["jobs"]) == 2,
            "parameter lock and 0-fit scope")
    require(load(root / "reviews/data_preflight.json")["status"].startswith("PASS")
            and load(root / "reviews/preexecution_acceptance.json")["status"].startswith("PASS")
            and load(root / "reviews/benchmark_source_review.json")["status"] ==
            "PASS_INDEPENDENT_COMPOSED_STATIC_NATIVE_REVIEW", "identity/preexecution/full-source gates")
    sources.digest(root / "protocol.md", lock["protocol_sha256"])
    native_review_path = root / "reviews/benchmark_source_review.json"
    sources.digest(native_review_path)
    native_review = load(native_review_path)
    for relative in ("src/benchmark.cpp", "src/native.hpp", "src/runtime.hpp", "src/region.hpp"):
        sources.digest(root / relative, native_review["source_identity"][relative])
    require(native_review["source_identity"]["protocol.md_at_review"] == lock["protocol_sha256"],
            "composed static native review bound to current frozen protocol/source")
    execution = load(root / "execution_lock.json")
    for path, digest in execution["source_and_binary_sha256"].items():
        sources.digest(path, digest)
    for path, expected in execution["input_stats"].items():
        require(stat4(Path(path).stat()) == expected, f"current input stat identity: {path}")
    configs, receipts, total_rounds = [], {}, 0
    seen_jobs = set()
    for job, expected in lock["jobs"].items():
        sources.digest(job, expected)
        c = load(job)
        key = c["role"], c["dataset"]
        require(key not in seen_jobs, "duplicate frozen job")
        seen_jobs.add(key)
        completed_job = next(x for x in completed if (x["role"], x["dataset"]) == key)
        require(completed_job["job_sha256"] == expected, "executed frozen job SHA")
        names = METHODS
        require(tuple(x["name"] for x in c["methods"]) == names, "frozen method order")
        by_name = {m["name"]: m for m in c["methods"]}
        require(all(not m["first_seed"] and m["extra_cap"] == (96 if m["name"] == "M5REG96" else 0)
                    for m in c["methods"]), "fixed query-best seed and0/96 extra caps")
        require(not by_name["NSG"]["table"] and not by_name["GT"]["table"]
                and by_name["M5"]["table"] == by_name["M5REG96"]["table"]
                and by_name["M5"]["table"]
                and by_name["M5"]["table_sha256"] == by_name["M5REG96"]["table_sha256"],
                "NSG/GT no posting; original M5 table shared unchanged with region")
        require(tuple(c["L"]) == L_VALUES
                and c["K_values"] == [1, 100], "prelocked five L and real K")
        require(c["n"] == 10000 and c["threads"] == 1 and c["cpu"] == 15
                and c["no_training"] and c["timing_repeats"] == 3
                and c["warmup_batches"] == 1 and c["warmup_n"] == 256
                and c["audit_n"] == 256 and c["GT_dtype"] == "<i4"
                and c["GT_width"] == 100 and c["query_first"] == 0
                and c["query_format"] == "raw" and c["GT_format"] == "raw"
                and c["source_window_first"] == 0 and c["source_window_n"] == N_QUERY,
                "full frozen job receipt scope")
        out = Path(c["out"])
        require(load(out / "job.json") == c, "actual saved config differs from lock")
        complete = load(out / "complete.json")
        require(complete["status"] == "PASS_E175_BUDGET_CURVE_NATIVE_FULL_PLAIN_REPLAY_SAMPLED_COUNT_ORACLES"
                and not complete["smoke_only"] and complete["no_GT_read"]
                and complete["no_training"] and complete["count_audit_n"] == 256
                and complete["full_plain_return_n"] == 10000
                and complete["full_independent_replay_n"] == 10000,
                "formal native full replay receipt")
        rounds = complete["formal_order"]
        require(len(rounds) == len(names) * len(c["K_values"]) * len(c["L"]) * 3 == complete["wall_rounds"],
                "full job timed matrix")
        require(load(out / "timing_progress.json") == rounds, "timing progress/completion identity")
        require(len(complete["results"]) == len(names) * len(c["K_values"]) * len(c["L"]), "full point matrix")
        require(complete["native_calls"] == len(names) * len(c["K_values"]) * len(c["L"]) * (2 * 256 + 5 * 10000),
                "complete warm/timed/plain/replay/count native call accounting")
        ordinal, ri = 0, 0
        for K in c["K_values"]:
            for L in c["L"]:
                for round_id in range(3):
                    for offset in range(len(names)):
                        row = rounds[ri]
                        ri += 1
                        name = names[(ordinal + round_id + offset) % len(names)]
                        require((row["K"], row["L"], row["method"], row["round"])
                                == (K, L, name, round_id), "fixed rotation identity")
                        require(row["n"] == 10000 and row["threads"] == 1
                                and row["cpu"] == 15 and math.isfinite(row["seconds"])
                                and row["seconds"] > 0, "formal timing row")
                        close(row["qps"], 10000 / row["seconds"], "round QPS=n/wall")
                for method in c["methods"]:
                    name = method["name"]
                    folder = out / f"k{K}" / f"{name}_L{L}"
                    p = load(folder / "complete.json")
                    pk = (c["role"], c["dataset"], K, L, name)
                    require(pk not in receipts and p["method"] == name and p["K"] == K
                            and p["L"] == L and p["n"] == 10000 and not p["smoke_only"],
                            "unique formal point identity")
                    require(p["table"] == (method["table"] or "") and
                            p["extra_cap"] == method["extra_cap"] and
                            p["first_seed"] == method["first_seed"], "frozen candidate method")
                    require(p["threads"] == 1 and p["cpu"] == 15
                            and p["full_plain_return_n"] == 10000
                            and p["full_plain_independent_replay_bits_equal"]
                            and p["full_plain_independent_replay_n"] == 10000
                            and p["plain_count_bits_equal"] and p["count_audit_n"] == 256
                            and p["original_GT_route_words_unchanged"] is (name != "NSG")
                            and p["original_NSG_constant_route_words_checked"] is (name == "NSG")
                            and p["main_entry_mode"] == ("original_NSG_enterpoint" if name == "NSG" else "original_GT_top3")
                            and p["normal_output_release_before_stop"]
                            and not p["timed_output_retained"], "parity + normal lifetime scope")
                    require(p["route_schema"] == ("[enterpoint,-1,-1]; profile words +0; route NDC 0"
                            if name == "NSG" else "actual GT maxheap-pop top3 IDs/profile words"),
                            "method-specific serialized route schema")
                    require(p["plain_count_parity_scope"] == "fixed uniform query sample only"
                            and p["stats_scope"] == "fixed uniform count-audit queries only, not full NDC",
                            "no full-NDC/timed-bits overclaim")
                    require(p["independent_region_linear_oracle"] == (method["extra_cap"] > 0)
                            and p["independent_original_linear_merge"] ==
                            (method["table"] is not None and method["extra_cap"] == 0)
                            and p["linear_merge_audit_n"] == (10000 if method["table"] else 0),
                            "full independent oracle scope")
                    wall = p["timing_seconds"]
                    require(len(wall) == 3 and all(math.isfinite(x) and x > 0 for x in wall),
                            "three point timings before GT")
                    expected_wall = [x["seconds"] for x in rounds
                                     if x["K"] == K and x["L"] == L and x["method"] == name]
                    require(wall == expected_wall, "point vs rotation wall receipt")
                    require(p in complete["results"], "job/point receipt equality")
                    receipts[pk] = (c, method, folder, p)
                ordinal += 1
        env = load(out / "native_environment.json")
        require(env["threads"] == 1 and env["no_GT_read"] and env["no_training"]
                and not env["smoke_only"] and env["loaded_base_words_checked"]
                and env["graph_N"] == c["base_n"] and env["graph_degree"] > 0,
                "actual loaded native environment")
        require(0 <= env["enterpoint"] < c["base_n"], "actual main graph NSG enterpoint")
        require(all(p["NSG_enterpoint"] == env["enterpoint"]
                    for pk, (job_c, method, folder, p) in receipts.items()
                    if pk[:2] == key and pk[-1] == "NSG"),
                "every NSG point bound to actual loaded graph enterpoint")
        total_rounds += len(rounds)
        configs.append(c)
    require(len(receipts) == 80 and total_rounds == 240,
            "all80 receipts and240 formal timings BEFORE ANY GT decode")
    require(seen_jobs == {(r, d) for r in ROLES for d in DATASETS}, "exact frozen role/dataset jobs")
    return configs, receipts, execution


def posting(path, expected, sources, base_n):
    sources.digest(path, expected)
    b = Path(path).read_bytes()
    require(b[:8] == b"M5POST1\0" and len(b) >= 40, "original posting magic")
    version, H, width, hn, pairs, N, z0, z1 = struct.unpack_from("<8I", b, 8)
    require(version == 1 and H > 0 and width == 8 and N == base_n and z0 == z1 == 0
            and hn >= 2 * H and hn & (hn - 1) == 0 and len(b) == 40 + 45 * H + 8 * hn,
            "complete frozen posting header (H includes empty rows)")
    labels = struct.unpack_from(f"<{H}i", b, 40)
    counts = b[40 + 4 * H:40 + 5 * H]
    targets = struct.unpack_from(f"<{8 * H}i", b, 40 + 5 * H)
    require(len(set(labels)) == H and all(0 <= x < base_n for x in labels), "posting labels")
    rows, U = {}, set()
    for i, label in enumerate(labels):
        count = counts[i]
        row = list(targets[8 * i:8 * i + count])
        require(count <= 8 and len(set(row)) == count and all(0 <= x < base_n for x in row)
                and all(x == -1 for x in targets[8 * i + count:8 * (i + 1)]), "posting row")
        rows[label] = row
        U.update(row)
    require(sum(counts) == pairs, "posting pair count")
    return rows, U


def candidate_plan(rows, route, returned):
    result, seen = [], set(returned)
    for label in route:
        if label not in rows:
            return []
        for target in rows[label]:
            if target not in seen:
                result.append(target)
                seen.add(target)
    return result


def point_key(p):
    return p["role"], p["dataset"], int(p["K"]), int(p["L"]), p["method"]


def comparison_key(p):
    return point_key(p) + (int(p["reference_L"]), p["reference"])


def read_packet(c, method, folder, receipt, gt, sources):
    n, K, base_n = c["n"], receipt["K"], c["base_n"]
    raw = folder / "raw"
    ids = ints(raw / "ids.i32", "i", n * K, sources)
    words = ints(raw / "distances.f32", "I", n * K, sources)
    entries = ints(raw / "entry_ids.i32", "i", n * 3, sources)
    profiles = ints(raw / "profile_distances.f32", "I", n * 3, sources)
    route = ints(raw / "route_ndc.u64", "Q", 256, sources)
    graph = ints(raw / "graph_ndc.u64", "Q", 256, sources)
    audit_ids = ints(raw / "audit_query_ids.i32", "i", 256, sources)
    expected_audit = [i * (n - 1) // 255 for i in range(256)]
    require(list(audit_ids) == expected_audit, "uniform256 audit row alignment")
    if method["name"] == "NSG":
        ep = receipt["NSG_enterpoint"]
        require(isinstance(ep, int) and 0 <= ep < base_n, "actual NSG enterpoint domain")
        require(all(list(entries[i * 3:(i + 1) * 3]) == [ep, -1, -1] for i in range(n))
                and all(x == 0 for x in profiles) and all(x == 0 for x in route),
                "NSG has constant entry sentinel, +0 profile words and zero route NDC")
    else:
        require(receipt["NSG_enterpoint"] == -1 and all(0 <= x < base_n for x in entries),
                "GT route ID domain, no NSG fixed-entry claim")
        require(all(len(set(entries[i * 3:(i + 1) * 3])) == 3 for i in range(n)),
                "actual three distinct router labels")
    members, hits = [], []
    for i in range(n):
        valid, padding, previous = set(), False, -math.inf
        for j in range(K):
            id_, word = ids[i * K + j], words[i * K + j]
            value = struct.unpack("<f", struct.pack("<I", word))[0]
            require(math.isfinite(value), "finite returned scalar score")
            if id_ == -1:
                require(word == 0x7f7fffff, "exact FLT_MAX padding word")
                padding = True
            else:
                require(not padding and 0 <= id_ < base_n and id_ not in valid,
                        "ordered padding, returned domain and uniqueness")
                require(value >= previous, "returned lower-is-better score order")
                previous = value
                valid.add(id_)
        mask = 0
        for rank, target in enumerate(gt[i][:K]):
            if target in valid:
                mask |= 1 << rank
        hit = len(valid.intersection(gt[i][:K]))
        require(hit == mask.bit_count(), "independent set/member-bit hit identity")
        hits.append(hit)
        members.append(mask)
    wall = receipt["timing_seconds"]
    qps = [n / x for x in wall]
    p = {"role": c["role"], "dataset": c["dataset"], "K": K, "L": receipt["L"],
         "method": method["name"], "n": n, "matched_GT_members": sum(hits),
         "recall_pct": 100 * sum(hits) / (n * K), "qps_rounds": qps,
         "qps_median": statistics.median(qps), "qps_min": min(qps), "qps_max": max(qps),
         "wall_seconds": wall, "graph_ndc_sample_mean": sum(graph) / 256,
         "route_ndc_sample_mean": sum(route) / 256,
         "count_audit_n": 256, "count_scope": LIMITS["count_scope"],
         "stats": receipt["stats"], "source_complete": str(folder / "complete.json")}
    return {"point": p, "ids": ids, "words": words, "entries": entries,
            "profiles": profiles, "route": route, "graph": graph,
            "hits": hits, "members": members, "audit_ids": expected_audit,
            "receipt": receipt, "method": method, "folder": folder}


def compare(a, b):
    p, ref = a["point"], b["point"]
    rescue = damage = improved = damaged = 0
    deltas = []
    for ma, mb, ha, hb in zip(a["members"], b["members"], a["hits"], b["hits"]):
        plus, minus = (ma & ~mb).bit_count(), (mb & ~ma).bit_count()
        delta = ha - hb
        require(delta == plus - minus, "per-query rescue - damage = net hits")
        rescue += plus
        damage += minus
        improved += delta > 0
        damaged += delta < 0
        deltas.append(delta)
    ratios = [x / y for x, y in zip(p["qps_rounds"], ref["qps_rounds"])]
    median = statistics.median(ratios)
    require(sum(deltas) == rescue - damage == p["matched_GT_members"] - ref["matched_GT_members"],
            "total integer member delta")
    result = {"role": p["role"], "dataset": p["dataset"], "K": p["K"], "L": p["L"],
              "method": p["method"], "reference_L": ref["L"], "reference": ref["method"],
              "n": p["n"], "recall_delta_pp": 100 * (rescue - damage) / (p["n"] * p["K"]),
              "rescue_members": rescue, "damage_members": damage,
              "queries_net_improved": improved, "queries_net_damaged": damaged,
              "paired_qps_ratio_rounds": ratios, "paired_qps_ratio_median": median,
              "paired_qps_change_pct": (median - 1) * 100,
              "qps_ratio_pairing_scope": LIMITS["same_pair"] if p["L"] == ref["L"] else LIMITS["cross_pair"],
              "speed_ranges_separated": min(p["qps_rounds"]) > max(ref["qps_rounds"]),
              "all_rounds_faster": all(x > 1 for x in ratios),
              "observed_joint_gain": rescue > damage and median > 1}
    return result


def comparison_pairs(configs, packets):
    # Explicit independently frozen list; no evaluator import or interpolated L.
    same_L = (("GT", "NSG"), ("M5", "GT"), ("M5", "NSG"),
              ("M5REG96", "GT"), ("M5REG96", "M5"), ("M5REG96", "NSG"))
    pairs = []
    for c in configs:
        role, ds = c["role"], c["dataset"]
        for K in (1, 100):
            for L in L_VALUES:
                for method, reference in same_L:
                    pairs.append((packets[(role, ds, K, L, method)],
                                  packets[(role, ds, K, L, reference)]))
            for si, small in enumerate(L_VALUES):
                for big in L_VALUES[si + 1:]:
                    for method in ("M5", "M5REG96"):
                        pairs.append((packets[(role, ds, K, small, method)],
                                      packets[(role, ds, K, big, "GT")]))
    require(len(pairs) == 200 and len({comparison_key(a["point"] | {
        "reference_L": b["point"]["L"], "reference": b["point"]["method"]})
        for a, b in pairs}) == 200,
        "frozen120 same-L plus80 actual small<big cross-L comparisons")
    return pairs


def trace_audit(packet, baseline, gt_packet, gt, rows, U, teacher, sources):
    p = packet["point"]
    n, K = p["n"], p["K"]
    raw = packet["folder"] / "raw"
    schema = load(raw / "region_trace_schema.json")
    require(schema["n"] == n and schema["words_per_query"] == 128
            and schema["bytes"] == n * 512 and schema["C_offset"] == 8
            and schema["C_capacity"] == 24 and schema["X_offset"] == 32
            and schema["X_capacity"] == 96 and schema["K"] == K
            and schema["extra_cap"] == packet["method"]["extra_cap"]
            and schema["metadata_offsets"] == {"seed0": 0, "seed1": 1, "seed2": 2,
                 "nC": 3, "nX": 4, "nSeeds": 5, "m5_committed": 6, "extension_aborted": 7},
            "complete ID trace schema")
    sources.digest(raw / "region_trace_schema.json")
    t = ints(raw / "region_trace.i32", "i", n * 128, sources)
    stats = load(packet["folder"] / "full_region_audit_stats.json")
    require(stats["n"] == n and stats["scope"] == "full untimed region replay only; not timed/full NDC",
            "full region stats remain separate from sampled count")
    sources.digest(packet["folder"] / "full_region_audit_stats.json")
    totals = {"role": p["role"], "dataset": p["dataset"], "K": K, "L": p["L"],
              "method": p["method"], "n": n, "C_total": 0, "X_total": 0,
              "selected_seeds_total": 0, "queries_with_X": 0,
              "X_outside_original_M5_U": 0, "X_outside_original_TRAIN_GT100_U": 0,
              "new_rescues_vs_M5": 0, "new_rescues_outside_original_M5_U": 0,
              "new_rescues_outside_original_TRAIN_GT100_U": 0,
              "new_damage_vs_M5": 0, "new_damage_outside_original_M5_U": 0,
              "new_damage_outside_original_TRAIN_GT100_U": 0, "extension_aborted": 0}
    detail = {"trace_queries": n, "C_gt_members": 0, "X_gt_members": 0,
              "X_gt_missing_from_original_M5": 0, "actual_true_rescue_vs_GT": 0,
              "actual_true_damage_vs_GT": 0, "actual_true_damage_vs_M5": 0,
              "X_first_GT_rank_1": 0, "X_GT_rank_2_10": 0, "X_GT_rank_11_100": 0,
              "m5_commits": 0, "extension_commits": 0}
    c_hist, x_hist, seed_hist = [0] * 25, [0] * 97, [0] * 4
    base_n = packet["base_n"]
    sampled_x = sampled_c = sampled_seeds = full_finite_post_dots = 0
    sampled_rows = {qi: j for j, qi in enumerate(packet["audit_ids"])}
    count = packet["receipt"]["stats"]
    for i in range(n):
        row = t[i * 128:(i + 1) * 128]
        nc, nx, ns, committed, aborted = row[3:8]
        require(0 <= nc <= 24 and 0 <= nx <= packet["method"]["extra_cap"]
                and 0 <= ns <= 3 and committed in (0, 1) and aborted in (0, 1), "trace budgets/status")
        C, X, S = list(row[8:8 + nc]), list(row[32:32 + nx]), list(row[:ns])
        Cset, Xset = set(C), set(X)
        require(all(x == -1 for x in row[ns:3]) and all(x == -1 for x in row[8 + nc:32])
                and all(x == -1 for x in row[32 + nx:128]), "trace inactive padding")
        require(len(set(C)) == nc and len(set(X)) == nx and len(set(S)) == ns
                and all(0 <= x < base_n for x in C + X + S), "full trace domain/unique")
        R = {x for x in gt_packet["ids"][i * K:(i + 1) * K] if x >= 0}
        expected_C = candidate_plan(rows, gt_packet["entries"][i * 3:(i + 1) * 3], R)
        require(C == expected_C[:nc], "independent C arrival prefix reconstruction")
        if committed:
            require(C == expected_C, "successful original M5 retains entire C")
        else:
            require(nx == ns == aborted == 0, "no X/seeds before successful M5 stage")
        require(set(S) <= set(C) and not (set(C) & R)
                and not (set(X) & (R | set(C))), "seeds in C and R/C/X disjoint")
        actual = {x for x in packet["ids"][i * K:(i + 1) * K] if x >= 0}
        original_m5 = {x for x in baseline["ids"][i * K:(i + 1) * K] if x >= 0}
        require(actual <= R | set(C) | set(X), "actual return generated by original R/C/X")
        if not committed:
            require(packet["ids"][i * K:(i + 1) * K] == gt_packet["ids"][i * K:(i + 1) * K]
                    and packet["words"][i * K:(i + 1) * K] == gt_packet["words"][i * K:(i + 1) * K],
                    "failed or empty original stage retains exact original GT packet")
        truth = set(gt[i][:K])
        new_true = (actual - original_m5) & truth
        damage_m5 = (original_m5 - actual) & truth
        totals["new_damage_vs_M5"] += len(damage_m5)
        totals["new_damage_outside_original_M5_U"] += len(damage_m5 - U)
        totals["new_damage_outside_original_TRAIN_GT100_U"] += len(damage_m5 - teacher)
        if p["method"].startswith("M5"):
            require(new_true <= set(X), "M5 new true rescues arise from X")
            if aborted:
                require(packet["ids"][i * K:(i + 1) * K] == baseline["ids"][i * K:(i + 1) * K] and
                        packet["words"][i * K:(i + 1) * K] ==
                        baseline["words"][i * K:(i + 1) * K], "X failure exact original M5 fallback")
            totals["new_rescues_vs_M5"] += len(new_true)
            totals["new_rescues_outside_original_M5_U"] += len(new_true - U)
            totals["new_rescues_outside_original_TRAIN_GT100_U"] += len(new_true - teacher)
        totals["C_total"] += nc
        totals["X_total"] += nx
        totals["selected_seeds_total"] += ns
        totals["queries_with_X"] += nx > 0
        totals["X_outside_original_M5_U"] += len(set(X) - U)
        totals["X_outside_original_TRAIN_GT100_U"] += len(set(X) - teacher)
        totals["extension_aborted"] += aborted
        detail["m5_commits"] += committed
        detail["extension_commits"] += nx > 0 and not aborted
        full_finite_post_dots += len(R) + nc if nc else 0
        detail["C_gt_members"] += len(Cset & truth)
        detail["X_gt_members"] += len(Xset & truth)
        detail["X_gt_missing_from_original_M5"] += len(Xset & (truth - original_m5))
        detail["actual_true_rescue_vs_GT"] += len((actual - R) & truth)
        detail["actual_true_damage_vs_GT"] += len((R - actual) & truth)
        detail["actual_true_damage_vs_M5"] += len(damage_m5)
        for rank, target in enumerate(gt[i]):
            if target in Xset:
                detail["X_first_GT_rank_1" if rank == 0 else
                       "X_GT_rank_2_10" if rank < 10 else "X_GT_rank_11_100"] += 1
        c_hist[nc] += 1
        x_hist[nx] += 1
        seed_hist[ns] += 1
        if i in sampled_rows:
            sampled_x += nx
            sampled_c += nc
            sampled_seeds += ns
            if count["domain_fallbacks"] == count["nonfinite_failures"] == 0:
                j = sampled_rows[i]
                paid = (len(R) + nc if nc else 0) + nx
                require(packet["graph"][j] - gt_packet["graph"][j] == paid,
                        "per sampled query natural main + R/C + X physical fee")
    for name in ("C", "X", "selected_seeds"):
        totals[name + "_mean"] = totals[name + "_total"] / n
    full = stats["stats"]
    require(full["new_distances"] == totals["X_total"] and full["seeds_selected"] == totals["selected_seeds_total"]
            and full["extension_nonfinite_failures"] == totals["extension_aborted"]
            and full["commits"] == detail["m5_commits"]
            and full["extension_commits"] == detail["extension_commits"], "physical full trace fees/status")
    require(full["graph_slots"] == full["new_distances"] + full["main_seen_skips"]
            + full["c_duplicate_skips"] + full["x_duplicate_skips"] + full["invalid_neighbor_skips"],
            "full region physical slot classification; separate from full main NDC")
    if full["domain_fallbacks"] == 0 and full["nonfinite_failures"] == 0:
        require(full["candidate_count"] == totals["C_total"] and full["post_dots"] == full_finite_post_dots,
                "full finite C and original R/C re-score count identity")
    summary = load(packet["folder"] / "trace_summary.json")
    sources.digest(packet["folder"] / "trace_summary.json")
    for field, value in {"queries": n, "c_words": totals["C_total"], "x_words": totals["X_total"],
                         "extension_aborts": totals["extension_aborted"], "c_count_histogram": c_hist,
                         "x_count_histogram": x_hist, "seed_count_histogram": seed_hist}.items():
        require(summary[field] == value, f"independent trace summary: {field}")
    require(count["new_distances"] == sampled_x and count["seeds_selected"] == sampled_seeds,
            "256 sample scalar/seed count vs full trace at frozen rows")
    if count["domain_fallbacks"] == 0 and count["nonfinite_failures"] == 0:
        require(count["candidate_count"] == sampled_c, "256 finite C count")
    return totals, detail


def csv_rows(path):
    with Path(path).open(newline="") as f:
        return list(csv.DictReader(f))


def match_rows(actual_rows, expected_rows, key, name):
    actual = {key(row): row for row in actual_rows}
    require(len(actual) == len(actual_rows) == len(expected_rows), f"{name} exact rows/unique keys")
    for expected in expected_rows:
        require(key(expected) in actual, f"{name} missing key")
        for field, value in expected.items():
            field_equal(actual[key(expected)], value, field)


def save_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--analysis", type=Path, default=ROOT / "analysis/final_v1")
    parser.add_argument("--out", type=Path, default=ROOT / "reviews/independent_result_audit")
    args = parser.parse_args()
    require(not args.out.exists(), "preserve independent audit output")
    sources = Sources()
    configs, receipts, execution = administrative_gate(args.root, sources)
    # Only beyond this line may saved GT/return/trace IDs be decoded.
    measured = load(args.analysis / "metrics.json")
    require(measured["status"] == "COMPLETE_E175_FROZEN_80_POINT_EVALUATION"
            and len(measured["points"]) == 80 and measured["training_increment_seconds"] == 0
            and measured["default_replacement"] is False and measured["primary_method"] == "M5REG96",
            "finished saved analysis scope; native receipt is not evaluation")
    inventory = load(args.root / "reviews/inventory.json")
    preflight = load(args.root / "reviews/data_preflight.json")
    table_cache, support, gts, packets = {}, {}, {}, {}
    required_provenance = set()
    for c in configs:
        ds, role, n, N = c["dataset"], c["role"], c["n"], c["base_n"]
        sources.digest(c["GT"], c["GT_sha256"])
        sources.digest(c["rows"], c["rows_sha256"])
        required_provenance.update((c["GT"], c["rows"]))
        for path_key, sha_key in (("queries", "query_sha256"),
                                  ("source_query_fvecs", "source_query_sha256"),
                                  ("source_GT_ivecs", "source_GT_sha256")):
            path, expected_sha = c[path_key], c[sha_key]
            sources.adopt_stat_only(path, expected_sha, execution["input_stats"][path], preflight)
            require(measured["source_sha256"].get(path) == expected_sha,
                    "evaluator must register raw/original public source SHA")
            required_provenance.add(path)
        require(Path(c["queries"]).stat().st_size == n * c["dimension"] * 4,
                "derived raw query window size without vector read")
        container_n = 10000 if ds == DATASETS[0] else 100000
        require(Path(c["source_query_fvecs"]).stat().st_size == container_n * (c["dimension"] + 1) * 4,
                "original public fvecs container size, stat-only")
        source_rows = ints(c["rows"], "q", n, sources, c["rows_sha256"])
        require(list(source_rows) == list(range(n)), "exact source rows0..9999; preserve duplicates/order")
        values = ints(c["GT"], "i", n * 100, sources)
        gt = [tuple(values[i * 100:(i + 1) * 100]) for i in range(n)]
        require(all(len(set(row)) == 100 and all(0 <= x < N for x in row) for row in gt),
                "existing exact GT100 ID domain/uniqueness")
        require(gt == official_GT_prefix(c["source_GT_ivecs"], n, container_n),
                "derived raw GT IDs exactly copy original official public first10K GT100")
        gts[(role, ds)] = gt
        for method in c["methods"]:
            if method["table"] and method["table"] not in table_cache:
                table_cache[method["table"]] = posting(method["table"], method["table_sha256"], sources, N)
        if ds not in support:
            old = inventory["datasets"][ds]
            manifest = load(old["compile_manifest"])
            sources.digest(old["compile_manifest"])
            matches = [(p, s) for p, s in manifest["input_sha256"].items() if p.endswith("/fit/gt.i64")]
            require(len(matches) == 1, "unique original legal FIT0 GT100 source")
            teacher_path, teacher_sha = matches[0]
            original = ints(teacher_path, "q", 20000 * 100, sources, teacher_sha)
            require(all(0 <= x < N for x in original), "old TRAIN ID domain")
            support[ds] = (table_cache[old["m5"]["path"]][1], set(original), teacher_path, teacher_sha)
            required_provenance.update((old["m5"]["path"], teacher_path))
    for key, (c, method, folder, receipt) in receipts.items():
        sources.digest(folder / "complete.json")
        required_provenance.add(str(folder / "complete.json"))
        packet = read_packet(c, method, folder, receipt, gts[(c["role"], c["dataset"])], sources)
        packet["base_n"] = c["base_n"]
        packets[key] = packet
        for raw_path in (folder / "raw").iterdir():
            if raw_path.is_file():
                sources.digest(raw_path)
                required_provenance.add(str(raw_path))
    for key, packet in packets.items():
        role, ds, K, L, name = key
        ref = packets[(role, ds, K, L, "GT")]
        stats = packet["receipt"]["stats"]
        require(all(isinstance(x, int) and x >= 0 for x in stats.values()),
                "nonnegative physical count integers")
        if name == "NSG":
            require(not packet["method"]["table"] and packet["method"]["extra_cap"] == 0
                    and not packet["method"]["first_seed"] and all(x == 0 for x in stats.values()),
                    "original NSG has no M5/region work or route/post costs")
            continue
        require(packet["entries"] == ref["entries"] and packet["profiles"] == ref["profiles"]
                and packet["route"] == ref["route"], "GT/post full route/profile + sampled route count retained")
        require(all(x >= y for x, y in zip(packet["graph"], ref["graph"])), "main scalar calls retained")
        stats = packet["receipt"]["stats"]
        require(all(isinstance(x, int) and x >= 0 for x in stats.values()), "nonnegative physical count integers")
        require(sum(packet["graph"]) - sum(ref["graph"]) == stats["post_dots"] + stats["new_distances"]
                == stats["additional_scalar_calls"], "sampled main + R/C + X raw scalar fee identity")
        if name == "GT":
            require(stats["additional_scalar_calls"] == stats["domain_checks"] == 0, "original GT no post")
        elif stats["domain_fallbacks"] == stats["nonfinite_failures"] == 0:
            rows = table_cache[packet["method"]["table"]][0]
            paid = 0
            for qi in packet["audit_ids"]:
                R = {x for x in ref["ids"][qi * K:(qi + 1) * K] if x >= 0}
                C = candidate_plan(rows, ref["entries"][qi * 3:(qi + 1) * 3], R)
                paid += len(R) + len(C) if C else 0
            require(stats["post_dots"] == paid, "independent sampled original R/C paid-dot count")
        require(stats["graph_slots"] == stats["new_distances"] + stats["main_seen_skips"]
                + stats["c_duplicate_skips"] + stats["x_duplicate_skips"] + stats["invalid_neighbor_skips"],
                "every physical graph slot classified exactly once")
    points = [x["point"] for x in packets.values()]
    comparisons = [compare(a, b) for a, b in comparison_pairs(configs, packets)]
    mechanisms, mechanism_details = [], []
    for key, packet in packets.items():
        if packet["method"]["extra_cap"]:
            role, ds, K, L, name = key
            rows, ignored_U = table_cache[packet["method"]["table"]]
            U, teacher, ignored_path, ignored_sha = support[ds]
            m, detail = trace_audit(packet, packets[(role, ds, K, L, "M5")],
                                    packets[(role, ds, K, L, "GT")], gts[(role, ds)],
                                    rows, U, teacher, sources)
            mechanisms.append(m)
            mechanism_details.append(dict(m, **detail))
    require(len(mechanisms) == 20, "all20 full region traces, all primary M5REG96 points")
    match_rows(measured["points"], points, point_key, "metrics.json points")
    match_rows(measured["comparisons"], comparisons, comparison_key, "metrics.json comparisons")
    match_rows(measured["mechanisms"], mechanisms, point_key, "metrics.json mechanisms")
    for csv_name in ("points.csv", "metrics.csv"):
        path = args.analysis / csv_name
        if path.exists():
            match_rows(csv_rows(path), points, point_key, csv_name)
            sources.digest(path)
    require((args.analysis / "points.csv").exists() or (args.analysis / "metrics.csv").exists(), "point CSV present")
    match_rows(csv_rows(args.analysis / "comparisons.csv"), comparisons, comparison_key, "comparisons.csv")
    match_rows(csv_rows(args.analysis / "mechanisms.csv"), mechanisms, point_key, "mechanisms.csv")
    # CI metadata/scope is audited; its stochastic endpoint computation is a
    # disclosed separate gate, not falsely covered by deterministic ID checks.
    for row in measured["comparisons"]:
        key = f'{row["role"]}|{row["dataset"]}|{row["K"]}|{row["L"]}|{row["method"]}|{row["reference_L"]}|{row["reference"]}'
        expected_seed = (20261010 + int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], "little")) % 2**32
        ci = row["delta_ci"]
        require(ci["seed"] == expected_seed and ci["repeats"] == 2000 and ci["scope"] == LIMITS["bootstrap"]
                and math.isfinite(ci["low_pp"]) and math.isfinite(ci["high_pp"])
                and -100 <= ci["low_pp"] <= ci["high_pp"] <= 100, "descriptive CI seed/count/scope")
    sources.digest(args.analysis / "metrics.json")
    sources.digest(Path(__file__))
    sources.digest(args.analysis / "comparisons.csv")
    sources.digest(args.analysis / "mechanisms.csv")
    measured_sources = measured["source_sha256"]
    require(required_provenance <= measured_sources.keys(),
            "saved evaluator must register every role GT/row, original M5/TRAIN support, point receipt/raw")
    for path, record in sources.files.items():
        if path in measured_sources:
            require(record["sha256"] == measured_sources[path], f"saved evaluator/current raw bytes: {path}")
    json_comparisons = {comparison_key(row): row for row in measured["comparisons"]}
    for row in csv_rows(args.analysis / "comparisons.csv"):
        require(json.loads(row["delta_ci"]) == json_comparisons[comparison_key(row)]["delta_ci"],
                "comparison CSV/JSON CI metadata and endpoint identity")
    sources.stable()
    for path, expected in execution["input_stats"].items():
        require(stat4(Path(path).stat()) == expected, f"original input changed after audit: {path}")
    state_after = load(args.root / "run_state.json")
    require(state_after["status"] == "NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION"
            and state_after.get("active") is None, "native completion remained stable")
    report = {"status": "PASS_INDEPENDENT_80_POINT_INTEGER_WALL_TRACE_AUDIT",
              "independent_of_evaluate_import": True, "point_count": len(points),
              "formal_timed_batches": 240, "comparison_count": len(comparisons),
              "full_region_trace_points": len(mechanisms), "primary_full_region_trace_points": 20,
              "all_role_GT_decoded_only_after_full_native_gate": True,
              "new_training_seconds": 0, "base_or_query_vector_values_read": False,
              "new_distance_or_GT_generated": False, "default_replacement": False,
              "teacher_support_sources": {ds: {"M5_U_size": len(x[0]), "old_TRAIN_GT100_U_size": len(x[1]),
                                               "path": x[2], "sha256": x[3]} for ds, x in support.items()},
              "source_sha256_and_stat4": sources.files,
              "public_source_GT_prefix_ID_copy_checked": True,
              "public_source_rows_exact_first10K_checked": True,
              "query_original_and_derived_value_read": False,
              "stat_only_source_bindings": [p for p, v in sources.files.items() if "verification_scope" in v],
              "limits": ["Saved full plain/replay receipts; timed packets not retained.",
                         "NDC/counts cover fixed256 queries only; full trace fees remain separate.",
                         "Raw C IDs independently reconstructed from original posting and original GT R.",
                         "Seed score-minimum and ordered graph/visited X generation are verified by prior full native scalar oracle, not recalculated here; graph/base/vector values are not read.",
                         "Member sets use existing frozen GT tie membership, not new distances or tie-adjusted GT.",
                         "Public source GT100 ivecs first10K rows are decoded as existing IDs and compared exactly with derived raw GT; original/queryraw SHA is adopted from actual preflight and current stat, not rehashed or vector-decoded here.",
                         "Paired bootstrap seed/count/scope checked; numeric stochastic CI endpoints not independently regenerated by this deterministic audit.",
                         "Five prelocked L per dataset, single historically exposed public10K role; no independent holdout replication, semantic IID or causal multimodal benefit."]}
    args.out.mkdir(parents=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    save_csv(args.out / "independent_points.csv", points)
    save_csv(args.out / "independent_comparisons.csv", comparisons)
    save_csv(args.out / "independent_mechanisms.csv", mechanism_details)
    print(json.dumps({"status": report["status"], "points": len(points),
                      "comparisons": len(comparisons), "trace_points": len(mechanisms)}))


if __name__ == "__main__":
    main()
