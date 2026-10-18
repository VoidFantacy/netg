#!/usr/bin/env python3
"""Read-only E183 numerical diagnosis after all formal runs and main analysis.

Scores only vectors involved in reported boundary cases. No graph traversal,
model fitting, GT changes, result rewriting, or additional query timing.
Native distances are used only when retained in an actual timed packet, or
explicitly inferred from byte-identical vectors scored by the same callback.
Python/NumPy float32 dot products are never presented as native scalar scores.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

ROOT = Path(__file__).resolve().parents[1]


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


class Inputs:
    def __init__(self, frozen):
        self.frozen = frozen
        self.records = {}

    def remember(self, path, large_source=False):
        path = Path(path).resolve()
        before = path.stat()
        stat = {"bytes": before.st_size, "mtime_ns": before.st_mtime_ns}
        if large_source:
            expected = self.frozen.get(str(path))
            require(expected is not None, "source must be bound in the full suite input freeze: " + str(path))
            require(stat == {k: expected[k] for k in stat}, "frozen source identity changed: " + str(path))
            value = {**stat, "sha256": expected["sha256"],
                     "verification": "inherited full-suite SHA256 plus unchanged size/mtime; no repeated full-base scan"}
        else:
            value = {**stat, "sha256": sha(path), "verification": "fresh full SHA256"}
        after = path.stat()
        require((after.st_size, after.st_mtime_ns) == (before.st_size, before.st_mtime_ns), "input changed while binding")
        if str(path) in self.records:
            old = self.records[str(path)]
            require(all(old[k] == value[k] for k in ("bytes", "mtime_ns", "sha256")), "consumed input drift")
        else:
            self.records[str(path)] = value
        return path

    def json(self, path):
        return json.loads(self.remember(path).read_text())

    def unchanged(self):
        for path, old in self.records.items():
            now = Path(path).stat()
            require((now.st_size, now.st_mtime_ns) == (old["bytes"], old["mtime_ns"]), "input changed during diagnosis: " + path)


class Matrix:
    """Exact container/window validation; fvecs headers checked on rows read."""
    def __init__(self, descriptor, inputs, integer=False, source=False):
        import numpy as np
        self.np = np
        self.path = inputs.remember(descriptor["path"], large_source=source)
        self.format = descriptor["format"]
        self.n = int(descriptor["n"])
        self.width = int(descriptor.get("d", descriptor.get("width", descriptor.get("k", 100))))
        self.start = int(descriptor.get("row_start", 0))
        require(self.n > 0 and self.width > 0 and self.start >= 0, "nonnegative matrix dimensions/window")
        header = 0
        if self.format in ("fvecs", "ivecs"):
            dtype, stride = "<i4", (self.width + 1) * 4
        elif self.format in ("fbin", "ibin"):
            dtype, stride, header = ("<i4" if integer else "<f4"), self.width * 4, 8
        else:
            dtype = {"raw_f32": "<f4", "raw_i32": "<i4", "raw_i64": "<i8"}.get(self.format)
            require(dtype is not None, "registered matrix format")
            stride = self.width * np.dtype(dtype).itemsize
        size = self.path.stat().st_size
        require(size >= header and (size-header) % stride == 0, "complete matrix byte layout")
        self.total = (size-header)//stride
        require(self.start+self.n <= self.total, "consumed matrix window within container")
        if "total_n" in descriptor:
            require(self.total == descriptor["total_n"], "full declared container size")
        if header:
            with self.path.open("rb") as stream:
                require(struct.unpack("<2I", stream.read(8)) == (self.total, self.width), "binary matrix header")
        columns = self.width+1 if self.format in ("fvecs", "ivecs") else self.width
        self.raw = np.memmap(self.path, mode="r", dtype=dtype, offset=header, shape=(self.total, columns))
        self.integer = integer

    def row(self, index):
        require(0 <= index < self.n, "matrix row domain")
        values = self.raw[self.start+index]
        if self.format in ("fvecs", "ivecs"):
            require(int(values[0]) == self.width, "consumed vecs row header")
            values = values[1:]
            if not self.integer:
                values = values.view("<f4")
        if not self.integer:
            require(bool(self.np.isfinite(values).all()), "finite consumed vector")
        return values


def raw_packet(path, n, k, inputs):
    import numpy as np
    out = {}
    for key, name, dtype, width in (("ids", "ids.i32", "<i4", k),
                                    ("distances", "distances.f32", "<f4", k),
                                    ("entries", "entry_ids.i32", "<i4", 3)):
        p = inputs.remember(path/name)
        require(p.stat().st_size == n*width*4, "actual timed packet shape")
        out[key] = np.memmap(p, mode="r", dtype=dtype, shape=(n, width))
    return out


def lower_distance(query, vector, metric):
    q, x = list(map(float, query)), list(map(float, vector))
    if metric == 0:
        terms = [a*b for a, b in zip(q, x)]
        value = -math.fsum(terms)
        amplitude = math.fsum(abs(v) for v in terms)
    else:
        require(metric == 1, "IP=0/L2=1")
        value = math.fsum((a-b)*(a-b) for a, b in zip(q, x))
        # Expanded operand scale, not merely the possibly-cancelled distance.
        amplitude = math.fsum((abs(a)+abs(b))**2 for a, b in zip(q, x))
    u = 2.0**-24
    operations = 4*len(q)+8
    gamma = operations*u/(1-operations*u)
    return {"float64_fsum_lower_distance": value,
            "conservative_float32_arithmetic_scale": gamma*amplitude,
            "bound_scope": "contextual normal-arithmetic scale, not a proof of this native SIMD reduction implementation"}


def exact_gap(query, target, other, metric):
    """Exact dyadic-rational difference on the original float32 coordinates."""
    total = Fraction(0)
    for q, a, b in zip(query, target, other):
        q, a, b = (Fraction.from_float(float(v)) for v in (q, a, b))
        total += q*(b-a) if metric == 0 else (b-a)*(2*q-a-b)
    return {"exact_sign": (total > 0)-(total < 0), "exact_gap_as_float64": float(total),
            "exact_gap_numerator": str(total.numerator), "exact_gap_denominator": str(total.denominator),
            "scope": "target lower-is-better distance minus comparator distance; exact rational metric of stored coordinates"}


def f32_bits(value):
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def ulp_distance(a, b):
    def key(value):
        word = f32_bits(value)
        return 0x80000000-(word & 0x7fffffff) if word & 0x80000000 else 0x80000000+word
    return abs(key(a)-key(b))


def classify(event):
    """Separate proven byte/score relations from an unproven rounding cause."""
    if event.get("identical_vectors_retained_native_consistent") is False:
        return "IDENTICAL_VECTOR_NATIVE_SCORE_CONTRADICTION_REQUIRES_REVIEW", False
    if event["identical_vector_final_ids_at_boundary"]:
        return "EXACT_DUPLICATE_VECTOR_BOUNDARY_TIE", True
    target_native = event["target_native_distance"]
    if target_native is not None and target_native < event["actual_boundary_native_distance"]:
        return "NATIVE_ORDER_CONTRADICTION_REQUIRES_REVIEW", False
    inversions = [p for p in event["comparisons"] if p["exact_geometry"]["exact_sign"] < 0
                  and p["target_native_distance"] is not None
                  and p["target_native_distance"] >= p["comparator_native_distance"]]
    if inversions:
        if any(p["target_native_distance"] > p["comparator_native_distance"] for p in inversions):
            return "OBSERVED_NATIVE_ORDER_INVERSION_VS_EXACT_GEOMETRY", True
        return "OBSERVED_NATIVE_TIE_VS_EXACT_GEOMETRY", True
    if any(p["exact_geometry"]["exact_sign"] == 0 for p in event["comparisons"]):
        return "EXACT_METRIC_TIE_DIFFERENT_IDS_NATIVE_CAUSE_NOT_PROVEN", False
    if any(p["within_float32_arithmetic_scale"] for p in event["comparisons"]):
        return ("NEAR_BOUNDARY_CANDIDATE_NATIVE_SCORE_NOT_RETAINED" if target_native is None else
                "NEAR_BOUNDARY_NO_PROVEN_NATIVE_INVERSION"), False
    if all(p["exact_geometry"]["exact_sign"] > 0 for p in event["comparisons"]):
        return "STORED_GT_VS_EXACT_VECTOR_ORDER_DIFFERENCE", False
    return "UNEXPLAINED_BOUNDARY_GAP_REQUIRES_REVIEW", False


def selftest():
    q, a, b = [1.0, .5], [1.0, 2.0], [2.0, 1.0]
    require(exact_gap(q, a, b, 0)["exact_sign"] == 1, "exact IP ordering")
    require(exact_gap(q, a, b, 1)["exact_sign"] == 1, "exact L2 ordering")
    require(exact_gap(q, a, a, 0)["exact_sign"] == 0, "identical vector exact tie")
    require(ulp_distance(1.0, struct.unpack("<f", struct.pack("<I", 0x3f800001))[0]) == 1, "one positive ULP")
    require(ulp_distance(-1.0, struct.unpack("<f", struct.pack("<I", 0xbf800001))[0]) == 1, "one negative ULP")
    require(ulp_distance(-0.0, 0.0) == 0, "zero numerical tie")
    duplicate = {"identical_vector_final_ids_at_boundary": [9]}
    require(classify(duplicate) == ("EXACT_DUPLICATE_VECTOR_BOUNDARY_TIE", True), "duplicate classification")
    near = {"identical_vector_final_ids_at_boundary": [], "target_native_distance": None,
            "actual_boundary_native_distance": 1.0,
            "comparisons": [{"exact_geometry": {"exact_sign": -1}, "target_native_distance": None,
                             "comparator_native_distance": 1.0, "within_float32_arithmetic_scale": True}]}
    require(classify(near)[0] == "NEAR_BOUNDARY_CANDIDATE_NATIVE_SCORE_NOT_RETAINED" and not classify(near)[1], "do not invent absent native scores")
    return {"status": "PASS_BOUNDARY_DIAGNOSTIC_SELFTEST", "scientific_inputs_read": False, "ANN_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis-dir", type=Path, default=ROOT/"analysis/final_v1")
    parser.add_argument("--catalogue", type=Path, default=ROOT/"reviews/dataset_catalogue.json")
    parser.add_argument("--output-json", type=Path, default=ROOT/"reviews/boundary_diagnostics.json")
    parser.add_argument("--output-md", type=Path, default=ROOT/"reviews/boundary_diagnostics.md")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest()))
        return
    require(not args.output_json.exists() and not args.output_md.exists(), "preserve previous boundary diagnosis outputs")
    for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[variable] = "1"
    if 14 in os.sched_getaffinity(0):
        os.sched_setaffinity(0, {14})
    started = time.monotonic()
    frozen = json.loads((ROOT/"reviews/input_freeze.json").read_text())["files"]
    inputs = Inputs(frozen)
    inputs.remember(__file__)
    inputs.remember(ROOT/"reviews/input_freeze.json")
    catalogue = inputs.json(args.catalogue)
    datasets = catalogue["datasets"]
    # Check every formal job before mapping/scoring any scientific vector.
    configs = {}
    for dataset, entry in datasets.items():
        cfg = inputs.json(entry["benchmark_config"])
        complete = inputs.json(Path(cfg["output_dir"])/"complete.json")
        require(complete["status"] == "PASS_E183_FORMAL_FULL_TIMED_OUTPUT_ORACLES" and complete["dataset"] == dataset
                and complete["config"] == cfg and complete["full_merge_oracle_passed"] and complete["all_round_bits_equal"], "all formal jobs and complete merge oracles must pass first")
        configs[dataset] = cfg
    summary = inputs.json(args.analysis_dir/"summary.json")
    require(summary["status"] == "PASS_E183_RETAINED_OUTPUT_ANALYSIS" and summary["dataset_count"] == len(datasets), "complete main analysis required")
    manifest = inputs.json(args.analysis_dir/"analysis_receipt.json")
    case_path = args.analysis_dir/"boundary_cases.csv"
    registered = manifest["outputs"].get(str(case_path.resolve()))
    require(registered is not None and sha(case_path) == registered["sha256"], "boundary CSV bound by finished analysis receipt")
    with inputs.remember(case_path).open(newline="", encoding="utf-8") as stream:
        cases = list(csv.DictReader(stream))
    require(summary["boundary_cases"] == len(cases), "declared exact boundary row count")
    import numpy as np
    mapped, packet_cache, table_cache, geometry_cache, exact_cache = {}, {}, {}, {}, {}
    events = []
    for case in cases:
        dataset, method, baseline = case["dataset"], case["method"], case["reference_method"]
        K, L, qi = (int(case[key]) for key in ("K", "L", "query_row"))
        cfg, entry = configs[dataset], datasets[dataset]
        require(K in (1, 100) and L in cfg["K_L"][str(K)], "registered boundary point")
        if dataset not in mapped:
            mapped[dataset] = (Matrix(entry["base"], inputs, source=True), Matrix(entry["test_queries"], inputs, source=True), Matrix(entry["test_gt"], inputs, integer=True))
        base, queries, truth = mapped[dataset]
        require(queries.n == truth.n == cfg["queries"]["n"] and 0 <= qi < queries.n, "query/GT domain")
        GT = list(map(int, truth.row(qi)[:K]))
        require(len(set(GT)) == K and all(0 <= t < base.n for t in GT), "unique strict-ID GT domain")
        gt_set = set(GT)
        query = queries.row(qi)
        def packet(name):
            key = (dataset, K, L, name)
            if key not in packet_cache:
                folder = Path(cfg["output_dir"])/f"k{K}"/f"{name}_L{L}"
                result = inputs.json(folder/"result.json")
                require(result["status"] == "PASS_E183_POINT" and result["all_round_bits_equal"] and result["full_merge_oracle_passed"], "point passed actual packet checks")
                packet_cache[key] = raw_packet(folder/"raw", queries.n, K, inputs)
            return packet_cache[key]
        reference, actual = packet(baseline), packet(method)
        rid, fid = list(map(int, reference["ids"][qi])), list(map(int, actual["ids"][qi]))
        require(len(set(rid)) == K and len(set(fid)) == K and all(0 <= t < base.n for t in rid+fid), "unique actual packet ID domain")
        for prefix, p in (("reference", reference), ("actual", actual)):
            require(int(case[prefix+"_boundary_id"]) == int(p["ids"][qi, -1]), "CSV boundary ID agrees with actual packet")
            require(f32_bits(float(case[prefix+"_boundary_native_distance"])) == f32_bits(p["distances"][qi, -1]), "CSV boundary native word agrees")
        rscore = dict(zip(rid, map(float, reference["distances"][qi])))
        fscore = dict(zip(fid, map(float, actual["distances"][qi])))
        require(all(math.isfinite(v) for v in list(rscore.values())+list(fscore.values())), "finite native scores")
        for t in set(rid)&set(fid):
            require(f32_bits(rscore[t]) == f32_bits(fscore[t]), "same native ID score unchanged")
        descriptor = next(m for m in cfg["methods"] if m["name"] == method)
        require(descriptor["family"] == "POST" and descriptor["baseline"] == baseline, "registered POST baseline")
        table_key = (dataset, method)
        if table_key not in table_cache:
            router = next(r for r in cfg["routers"] if r["name"] == descriptor["router"])
            lp = inputs.remember(router["ids"])
            labels = list(map(int, np.fromfile(lp, dtype="<i4")))
            rows = inputs.json(Path(descriptor["table"]).with_suffix(".rows.json"))
            require(len(labels) == len(rows) and len(set(labels)) == len(labels), "table row labels")
            table_cache[table_key] = dict(zip(labels, map(set, rows)))
        route = list(map(int, reference["entries"][qi]))
        require(route == list(map(int, actual["entries"][qi])), "identical actual POST route")
        union = set().union(*(table_cache[table_key][r] for r in route))
        require(set(fid).issubset(set(rid)|union), "actual post output in candidate union")
        def geometry(t):
            key = (dataset, qi, t)
            if key not in geometry_cache:
                geometry_cache[key] = lower_distance(query, base.row(t), cfg["metric_id"])
            return geometry_cache[key]
        for kind, field in (("candidate_available_not_returned", "candidate_available_but_not_returned_GT_ids"), ("member_damage", "damaged_GT_ids")):
            targets = list(map(int, json.loads(case[field])))
            for target in targets:
                require(target in gt_set and target not in fscore, "strict GT member absent in actual return")
                require((target in rscore) if kind == "member_damage" else (target not in rscore and target in union), "independently reconstructed event kind")
                vector = base.row(target)
                vector_bytes = vector.tobytes()
                duplicate_ids = [t for t in fid if base.row(t).tobytes() == vector_bytes]
                boundary = fid[-1]
                duplicate_boundary = [t for t in duplicate_ids if fscore[t] == fscore[boundary]]
                if target in rscore:
                    target_native, native_scope = rscore[target], "actual retained baseline packet"
                elif duplicate_ids:
                    values = {f32_bits(fscore[t]) for t in duplicate_ids}
                    require(len(values) == 1, "identical final vectors have same native score word")
                    target_native, native_scope = fscore[duplicate_ids[0]], "inferred from byte-identical final vector and unchanged deterministic scalar callback; not a retained target score"
                else:
                    target_native, native_scope = None, "target scalar native score was not retained and has not been recomputed"
                nongt = [t for t in fid if t not in gt_set]
                require(nongt, "missing true member implies at least one non-GT final ID")
                worst_exact_nongt = max(nongt, key=lambda t: geometry(t)["float64_fsum_lower_distance"])
                compare_ids = list(dict.fromkeys([boundary, worst_exact_nongt, *duplicate_ids]))
                comparisons = []
                target_geometry = geometry(target)
                for other in compare_ids:
                    other_geometry = geometry(other)
                    gap = target_geometry["float64_fsum_lower_distance"]-other_geometry["float64_fsum_lower_distance"]
                    scale = target_geometry["conservative_float32_arithmetic_scale"]+other_geometry["conservative_float32_arithmetic_scale"]
                    exact_key = (dataset, qi, target, other)
                    if exact_key not in exact_cache:
                        exact_cache[exact_key] = exact_gap(query, vector, base.row(other), cfg["metric_id"])
                    exact = exact_cache[exact_key]
                    comparisons.append({"comparator_id": other, "comparator_is_GT_member": other in gt_set,
                                        "comparator_is_actual_boundary": other == boundary,
                                        "byte_identical_vectors": other in duplicate_ids,
                                        "target_native_distance": target_native, "comparator_native_distance": fscore[other],
                                        "native_score_ULP_distance": None if target_native is None else ulp_distance(target_native, fscore[other]),
                                        "target_geometry": target_geometry, "comparator_geometry": other_geometry,
                                        "float64_fsum_gap": gap, "pair_float32_arithmetic_scale": scale,
                                        "within_float32_arithmetic_scale": abs(gap) <= scale, "exact_geometry": exact})
                event = {"dataset": dataset, "metric_id": cfg["metric_id"], "method": method, "reference_method": baseline,
                         "K": K, "L": L, "query_row": qi, "kind": kind, "target_GT_id": target,
                         "target_GT_rank_one_based": GT.index(target)+1,
                         "target_vector_sha256": hashlib.sha256(vector_bytes).hexdigest(),
                         "target_native_distance": target_native, "target_native_distance_scope": native_scope,
                         "identical_vectors_retained_native_consistent":
                             all(f32_bits(rscore[target]) == f32_bits(fscore[t]) for t in duplicate_ids) if target in rscore and duplicate_ids else None,
                         "actual_boundary_id": boundary, "actual_boundary_native_distance": fscore[boundary],
                         "identical_vector_final_ids": duplicate_ids, "identical_vector_final_ids_at_boundary": duplicate_boundary,
                         "comparisons": comparisons}
                category, proved = classify(event)
                event.update(category=category, stated_numeric_relation_verified=proved,
                             strict_ID_recall_preserved=True, GT_changed=False, returned_packet_changed=False)
                events.append(event)
    counts = Counter(e["category"] for e in events)
    unresolved = [e for e in events if "REQUIRES_REVIEW" in e["category"]]
    inputs.unchanged()
    result = {"status": "PASS_BOUNDARY_DIAGNOSTICS_COMPLETED" if not unresolved else "BOUNDARY_DIAGNOSTICS_COMPLETED_WITH_UNRESOLVED_CASES",
              "analysis_dir": str(args.analysis_dir.resolve()), "boundary_query_point_rows": len(cases), "member_events": len(events),
              "unique_dataset_query_target_kind_events": len({(e["dataset"], e["query_row"], e["target_GT_id"], e["kind"]) for e in events}),
              "unique_dataset_queries": len({(e["dataset"], e["query_row"]) for e in events}), "category_counts": dict(counts),
              "unresolved_member_events": len(unresolved), "events": events, "inputs": inputs.records,
              "elapsed_seconds": time.monotonic()-started, "threads": 1, "cpu_affinity": sorted(os.sched_getaffinity(0)),
              "scope": "Only actual timed boundary IDs and their relevant stored base vectors. No full-base search, ANN, GT rewriting, query remeasurement, or native-score substitution.",
              "exact_geometry": "Python Fraction computes exact rational pair-distance differences on stored float32 coordinates. This is distinct from the original float32 native/GT scoring definition.",
              "near_tie_limit": "The arithmetic scale only flags a plausible rounding-sensitive region. Without retained or identical-vector-inferred target native scores, native rounding causation is not proven.",
              "repeated_cases": "The same query/target at several K/L/method points is not independent confirmation.",
              "scientific_outputs_changed": False, "additional_ANN_calls": 0, "additional_timed_points": 0}
    lines = ["# E183 数值边界诊断", "",
             f"已完成 {len(cases)} 个查询工作点、{len(events)} 个遗漏/损伤成员事件的离线诊断；涉及 {result['unique_dataset_queries']} 条不同数据集查询。原 GT、严格 ID Recall 和实际计时返回全部保留。", "",
             "同一查询或成员在多个方法/预算中重复出现，不能当作多份独立确认。相同向量的字节证据、已保存的原生距离和精确有理数几何排序分开记录；未保存的候选原生分数不使用 NumPy 点积冒充。", "",
             "| 分类 | 成员事件数 |", "| --- | ---: |"]
    lines.extend(f"| {category} | {count} |" for category, count in sorted(counts.items()))
    if not counts:
        lines.append("| 没有候选可用未返回或成员损伤事件 | 0 |")
    lines += ["", f"仍需进一步核查的事件：{len(unresolved)}。完整逐例证据在同名 JSON 中；`stated_numeric_relation_verified=false` 表示该分类没有宣称原生数值因果已证明。", "",
              "| 数据集 | 查询行 | K / L | 方法 | 类型 | GT ID | 分类 |", "| --- | ---: | --- | --- | --- | ---: | --- |"]
    for event in events:
        lines.append(f"| {event['dataset']} | {event['query_row']} | {event['K']} / {event['L']} | {event['method']} | {event['kind']} | {event['target_GT_id']} | {event['category']} |")
    lines += ["", "精确有理数计算使用已保存 float32 坐标的数学距离；它不是重新定义项目原有 float32 GT。近并列尺度仅供诊断，不能据此重新打分、删除异常查询或上调正式 Recall。", ""]
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    with args.output_json.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    with args.output_md.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines))
    print(json.dumps({key: result[key] for key in ("status", "boundary_query_point_rows", "member_events", "category_counts", "elapsed_seconds")}))


if __name__ == "__main__":
    main()
