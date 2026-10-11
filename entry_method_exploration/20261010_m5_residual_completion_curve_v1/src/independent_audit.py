#!/usr/bin/env python3
"""Independent E176 dynamic ID/set, wall, receipt and trace audit, AFTER all native jobs.

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
METHODS = ()
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


def comparison_pairs(configs, packets):
    pairs=[]
    for c in configs:
        names=[m['name'] for m in c['methods']]
        order=[x for x in names if x!='M5RES12']+(['M5RES12'] if 'M5RES12' in names else [])
        candidates=[m['name'] for m in c['methods'] if m['family']!='base']
        role,ds=c['role'],c['dataset']
        for K in c['K_values']:
            for L in c['L']:
                for i,a in enumerate(order):
                    for b in order[:i]:pairs.append((packets[(role,ds,K,L,a)],packets[(role,ds,K,L,b)]))
            for i,small in enumerate(c['L']):
                for big in c['L'][i+1:]:
                    for name in candidates:pairs.append((packets[(role,ds,K,small,name)],packets[(role,ds,K,big,'GT')]))
    keys=[point_key(a['point'])+(b['point']['L'],b['point']['method']) for a,b in pairs]
    require(len(keys)==len(set(keys)), 'unique predeclared all-pair comparisons')
    return pairs


def administrative_gate(root,sources):
    state=load(root/'run_state.json'); lock=load(root/'parameter_lock.json')
    require(state['status']=='NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None,'all native jobs finished before decoding')
    require(len(lock['jobs'])==len(state['completed'])==2 and all(x['exit_code']==0 and x['max_threads_observed']==1 for x in state['completed']),'two actual T1 exit0 jobs')
    require(lock['no_adaptive_cancel_or_selection'],'no adaptive public-test selection')
    fit=load(root/'fit_state.json');sources.digest(root/'fit_state.json')
    require(fit['status']=='FIT_COMPLETE_ALL_MODELS_FROZEN' and fit.get('active') is None and len(fit['completed'])==2 and {x['dataset'] for x in fit['completed']}==set(DATASETS),'complete both actual FIT phases')
    for x in fit['completed']:
        require(x['status']=='PASS_ADDITIONAL_FIT_COMPLETE_WITHIN_900S' and x['model_eligible'] and x['cap_seconds']==900 and 0<x['elapsed_seconds']<=900 and x['historical_cost_reset'] is False and x['full_process_lifecycle_included'],'actual additional FIT cap/eligibility/prior debt')
        close(x['cumulative_TRAIN_with_this_increment_seconds'],x['historical_TRAIN_seconds']+x['elapsed_seconds'],'actual cumulative TRAIN debt')
    close(state['training_increment_seconds'],sum(x['elapsed_seconds'] for x in fit['completed']),'actual FIT whole stage sum')
    sources.digest(root/'protocol.md',lock['protocol_sha256'])
    preflight=load(root/'reviews/data_preflight.json'); require(preflight['status'].startswith('PASS'),'input/model preflight')
    require(load(root/'reviews/preexecution_acceptance.json')['status'].startswith('PASS'),'execution eligibility')
    review=load(root/'reviews/native_qualification.json')
    require(review['status']=='PASS_E176_N16_ORACLES_AND_FROZEN_ORIGINAL_WORD_REGRESSION','native qualification')
    sources.digest(root/'reviews/native_qualification.json')
    for path,digest in review['source_identity'].items():
        if path=='protocol.md_at_review':require(digest==lock['protocol_sha256'],'review protocol identity')
        else:sources.digest(Path(path) if Path(path).is_absolute() else root/path,digest)
    execution=load(root/'execution_lock.json')
    for path,digest in execution['source_and_binary_sha256'].items():sources.digest(path,digest)
    for path,expected in execution['input_stats'].items():require(stat4(Path(path).stat())==expected,'all frozen inputs current metadata')
    configs=[]; receipts={}; total_rounds=0; seen=set()
    for job,digest in lock['jobs'].items():
        sources.digest(job,digest);c=load(job);key=c['role'],c['dataset']
        require(key not in seen and c['role']=='public_test','two unique public roles');seen.add(key)
        completed=next(x for x in state['completed'] if (x['role'],x['dataset'])==key)
        require(completed['job_sha256']==digest,'executed frozen job bytes')
        names=[m['name'] for m in c['methods']]
        require(len(set(names))==len(names) and {'NSG','GT','M5'}<=set(names),'dynamic unique methods with fixed controls')
        by_name={m['name']:m for m in c['methods']}
        require(c['n']==10000 and c['threads']==1 and c['cpu']==15 and c['no_training'] and c['timing_repeats']==3 and c['audit_n']==256 and c['warmup_n']==256 and c['warmup_batches']==1,'full n/T1/warm/count scope')
        require(c['K_values']==[1,100] and tuple(c['L'])==L_VALUES and c['GT_dtype']=='<i4' and c['GT_width']==100 and c['query_first']==0 and c['source_window_first']==0 and c['source_window_n']==c['n'],'fixed five budgets and administrative GT window')
        require(c['query_format']==c['GT_format']=='raw','raw input format')
        for m in c['methods']:
            require(m['family'] in ('base','post','reg','opt','opt_reg','bank','route_bank') and not m['first_seed'],'frozen method family/query-best policy')
            expected_cap=96 if m['family'] in ('reg','opt_reg') else 12 if m['family'] in ('bank','route_bank') else 0
            require(m['extra_cap']==expected_cap and bool(m['table'])==(m['family']!='base'),'family cap/posting contract')
            require(m['optimized']==(m['family'] in ('opt','opt_reg','bank','route_bank')),'frozen cache family flag')
            if m['table']:require(m['table']==by_name['M5']['table'] and m['table_sha256']==by_name['M5']['table_sha256'],'old M5 retained unchanged')
            if m['family'] in ('bank','route_bank'):require(m['completion_family']==('pair' if m['family']=='bank' else 'route'),'condition-key family')
        out=Path(c['out']);require(load(out/'job.json')==c,'actual config identity')
        comp=load(out/'complete.json'); count=len(names)*len(c['K_values'])*len(c['L'])
        require(comp['status']=='PASS_E176_FROZEN_CURVE_NATIVE_FULL_WORD_ORACLES_SAMPLED_COUNT' and not comp['smoke_only'] and comp['no_GT_read'] and comp['no_training'] and comp['count_audit_n']==256 and comp['full_plain_return_n']==c['n'],'formal full native completion')
        rounds=comp['formal_order'];require(rounds==load(out/'timing_progress.json') and len(rounds)==3*count==comp['wall_rounds'] and len(comp['results'])==count,'all frozen rotation batches')
        require(comp['native_calls']==count*(4*c['n']+c['warmup_n']+c['audit_n']),'all actual main search calls, no second full replay')
        ordinal=0;ri=0
        for K in c['K_values']:
            for L in c['L']:
                for round_id in range(3):
                    for offset in range(len(names)):
                        row=rounds[ri];ri+=1;name=names[(ordinal+round_id+offset)%len(names)]
                        require((row['K'],row['L'],row['method'],row['round'])==(K,L,name,round_id) and row['n']==c['n'] and row['threads']==1 and row['cpu']==15 and math.isfinite(row['seconds']) and row['seconds']>0,'actual fixed round identity')
                        close(row['qps'],c['n']/row['seconds'],'native round n/wall')
                for m in c['methods']:
                    name=m['name'];folder=out/f'k{K}'/f'{name}_L{L}';p=load(folder/'complete.json');pk=key+(K,L,name)
                    require(pk not in receipts and p in comp['results'] and (p['method'],p['K'],p['L'],p['n'])==(name,K,L,c['n']),'unique point identity')
                    require(p['table']==(m['table'] or '') and p['extra_cap']==m['extra_cap'] and p['first_seed']==m['first_seed'],'method receipt parameters')
                    require(not p['smoke_only'] and p['threads']==1 and p['cpu']==15 and p['plain_count_bits_equal'] and p['count_audit_n']==256 and p['full_plain_return_n']==c['n'] and p['normal_output_release_before_stop'] and not p['timed_output_retained'],'complete normal lifetime and fixed count parity')
                    require(p['full_plain_independent_replay_bits_equal'] is False and p['full_plain_independent_replay_n']==0,'no second full native replay')
                    require(p['full_plain_independent_scalar_linear_oracle'] is bool(m['table']) and p['original_scalar_main_kernel'] is True and p['main_packet_words_equal_fresh_GT'] is (name!='NSG'),'original kernel and scalar oracle scope')
                    require(p['original_NSG_constant_route_words_checked'] is (name=='NSG') and p['original_GT_route_words_unchanged'] is (name!='NSG'),'route-specific binding')
                    require(p['plain_count_parity_scope']=='fixed uniform query sample only' and p['stats_scope']=='fixed uniform count-audit queries only, not full NDC','sample count scope')
                    if m['optimized'] or m['family'] in ('bank','route_bank'):
                        require(p['cached_main_R_fresh_score_words_equal'] is True and p['cached_R_word_check_n']==c['n']*K,'full fresh cached R word proof')
                    if m['family'] in ('opt','opt_reg'):
                        require(p['optimized_reference_method']==('M5' if m['family']=='opt' else 'M5REG96') and p['optimized_reference_packet_bits_equal'] is True,'full original reference packet identity')
                    if m['family'] in ('bank','route_bank'):require(p['shared_cost_baseline']=='M5OPT','bank cost baseline')
                    expected_wall=[r['seconds'] for r in rounds if (r['K'],r['L'],r['method'])==(K,L,name)]
                    require(p['timing_seconds']==expected_wall,'point vs job actual wall')
                    receipts[pk]=(c,m,folder,p)
                ordinal+=1
        env=load(out/'native_environment.json')
        require(env['threads']==1 and env['no_GT_read'] and env['no_training'] and not env['smoke_only'] and env['loaded_base_words_checked'] and env['graph_N']==c['base_n'] and 0<=env['enterpoint']<c['base_n'],'loaded original native environment')
        for pk,(cc,mm,ff,p) in receipts.items():
            if pk[:2]==key and mm['name']=='NSG':require(p['NSG_enterpoint']==env['enterpoint'],'NSG actual graph enterpoint')
        total_rounds+=len(rounds);configs.append(c)
    require(seen=={('public_test',ds) for ds in DATASETS} and state['planned_points']==len(receipts) and state['planned_timed_batches']==total_rounds==3*len(receipts),'all dynamic matrix gated BEFORE GT')
    return configs,receipts,execution


def completion_qualification(c,root,sources,preflight,execution):
    if not any(m['family'] in ('bank','route_bank') for m in c['methods']):return None
    path=Path(c.get('completion_manifest',root/'models'/c['dataset']/'compile_manifest.json'))
    registered=preflight['registered_input_files'][str(path)]
    sources.digest(path,registered['sha256']);require(stat4(path.stat())==execution['input_stats'][str(path)],'qualified manifest stat')
    manifest=load(path)
    require(manifest['status']=='FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS' and manifest['role']=='fit' and manifest['n']==20000 and manifest['point_count']==10 and manifest['public_test_read'] is False and manifest['old_train_debt_reset'] is False and manifest['train_budget_is_not_zero'] is True and set(manifest['models'])=={f'k{K}_L{L}' for K in c['K_values'] for L in c['L']},'all ten fixed TRAIN residual models qualified')
    for key in manifest['models']:
        for family in ('pair','route'):
            value=c['completion_models'][key][family];model=Path(value['path'] if isinstance(value,dict) else value);record=manifest['models'][key][family]
            require(record['path']==str(model) and record['bytes']==model.stat().st_size and record['sha256']==preflight['registered_input_files'][str(model)]['sha256'],'model compiler/job/frozen bytes closure')
    return str(path)


def completion_model(c,K,L,family,sources,preflight,execution):
    value=c['completion_models'][f'k{K}_L{L}'][family];path=Path(value['path'] if isinstance(value,dict) else value)
    expected=preflight['registered_input_files'][str(path)]['sha256']
    require(stat4(path.stat())==execution['input_stats'][str(path)],'qualified completion current stat')
    sources.digest(path,expected);require(path.stat().st_size%28==0,'Nx7 raw model')
    values=ints(path,'i',path.stat().st_size//4,sources);table={};previous=None
    for i in range(0,len(values),7):
        row=values[i:i+7];h,w,n=row[:3];key=h,w
        require(previous is None or key>previous,'strict unique completion keys')
        require(0<=h<c['base_n'] and (w==-1 if family=='route' else 0<=w<c['base_n']) and 0<=n<=4,'completion key domain')
        targets=list(row[3:3+n]);require(len(set(targets))==n and all(0<=x<c['base_n'] for x in targets) and all(x==-1 for x in row[3+n:]),'completion targets and padding')
        table[key]=targets;previous=key
    return table,str(path)


def trace_audit(packet,baseline,gt_packet,gt,rows,U,teacher,sources,completion=None):
    p=packet['point'];n,K=p['n'],p['K'];light=packet['method']['family'] in ('bank','route_bank')
    width,offset,cap=(20,8,12) if light else (128,32,96)
    path=packet['folder']/'raw'/('completion_trace.i32' if light else 'region_trace.i32');t=ints(path,'i',n*width,sources)
    totals={k:p[k] for k in ('role','dataset','K','L','method','n')}
    totals.update(dict(C_total=0,X_total=0,selected_seeds_total=0,queries_with_X=0,X_outside_original_M5_U=0,X_outside_original_TRAIN_GT100_U=0,new_rescues_vs_M5=0,new_rescues_outside_original_M5_U=0,new_rescues_outside_original_TRAIN_GT100_U=0,new_damage_vs_M5=0,new_damage_outside_original_M5_U=0,new_damage_outside_original_TRAIN_GT100_U=0,extension_aborted=0))
    detail=dict(trace_queries=n,C_gt_members=0,X_gt_members=0,X_gt_missing_from_original_M5=0,actual_true_rescue_vs_GT=0,actual_true_damage_vs_GT=0,actual_true_damage_vs_M5=0,X_first_GT_rank_1=0,X_GT_rank_2_10=0,X_GT_rank_11_100=0,m5_commits=0,extension_commits=0)
    sample=set(packet['audit_ids']);sx=sc=ss=0
    for qi in range(n):
        row=t[qi*width:(qi+1)*width];nc,nx,ns,committed,aborted=row[3:8]
        require(0<=nc<=24 and 0<=nx<=cap and 0<=ns<=3 and committed in (0,1) and aborted in (0,1),'trace status and budgets')
        R={x for x in gt_packet['ids'][qi*K:(qi+1)*K] if x>=0};route=list(gt_packet['entries'][qi*3:(qi+1)*3]);expected_C=candidate_plan(rows,route,R)
        C=expected_C[:nc] if light else list(row[8:8+nc]);X=list(row[offset:offset+nx]);winners=list(row[:3])
        require(C==expected_C[:nc] and (not committed or C==expected_C),'original C complete or legitimate prefix')
        require(len(set(C))==nc and len(set(X))==nx and all(0<=x<packet['base_n'] for x in C+X) and not set(C)&R and not set(X)&(R|set(C)),'C/X domains unique and disjoint')
        require(all(x==-1 for x in row[offset+nx:]),'unused trace X padding')
        if not committed:require(nx==ns==aborted==0,'no extension before successful M5')
        if light:
            require(sum(w>=0 for w in winners)==ns,'independent route winner count; repeats allowed')
            for h,w in zip(route,winners):require(w==-1 or (w in C and w in rows.get(h,[])),'original row C winner membership')
            plan=[];seen=R|set(C)
            if committed:
                for h,w in zip(route,winners):
                    if packet['method']['completion_family']=='pair' and w<0:continue
                    key=(h,w if packet['method']['completion_family']=='pair' else -1)
                    for x in completion.get(key,[]):
                        if x not in seen:plan.append(x);seen.add(x)
            require(X==plan[:nx] and (aborted or X==plan),'row0/1/2 bank arrival with R/C/X filtering; no pair fallback')
        else:
            require(all(x==-1 for x in row[8+nc:32]) and all(w==-1 for w in winners[ns:]) and len(set(winners[:ns]))==ns and set(winners[:ns])<=set(C),'old REG seed uniqueness and C padding')
        actual={x for x in packet['ids'][qi*K:(qi+1)*K] if x>=0};original={x for x in baseline['ids'][qi*K:(qi+1)*K] if x>=0}
        require(actual<=R|set(C)|set(X),'actual support closure')
        if aborted:require(packet['ids'][qi*K:(qi+1)*K]==baseline['ids'][qi*K:(qi+1)*K] and packet['words'][qi*K:(qi+1)*K]==baseline['words'][qi*K:(qi+1)*K],'failed extension exact M5 fallback')
        if not committed:require(packet['ids'][qi*K:(qi+1)*K]==gt_packet['ids'][qi*K:(qi+1)*K] and packet['words'][qi*K:(qi+1)*K]==gt_packet['words'][qi*K:(qi+1)*K],'uncommitted M5 exact GT fallback')
        truth=set(gt[qi][:K]);plus=(actual-original)&truth;minus=(original-actual)&truth;require(plus<=set(X),'true new rescues arise from X')
        for prefix,values in [('new_rescues',plus),('new_damage',minus)]:
            totals[prefix+'_vs_M5']+=len(values);totals[prefix+'_outside_original_M5_U']+=len(values-U);totals[prefix+'_outside_original_TRAIN_GT100_U']+=len(values-teacher)
        totals['C_total']+=nc;totals['X_total']+=nx;totals['selected_seeds_total']+=ns;totals['queries_with_X']+=nx>0;totals['extension_aborted']+=aborted
        totals['X_outside_original_M5_U']+=len(set(X)-U);totals['X_outside_original_TRAIN_GT100_U']+=len(set(X)-teacher)
        detail['C_gt_members']+=len(set(C)&truth);detail['X_gt_members']+=len(set(X)&truth);detail['X_gt_missing_from_original_M5']+=len(set(X)&(truth-original))
        detail['actual_true_rescue_vs_GT']+=len((actual-R)&truth);detail['actual_true_damage_vs_GT']+=len((R-actual)&truth);detail['actual_true_damage_vs_M5']+=len(minus);detail['m5_commits']+=committed;detail['extension_commits']+=nx>0 and not aborted
        for rank,target in enumerate(gt[qi]):
            if target in X:detail['X_first_GT_rank_1' if rank==0 else 'X_GT_rank_2_10' if rank<10 else 'X_GT_rank_11_100']+=1
        if qi in sample:sx+=nx;sc+=nc;ss+=ns
    for key in ('C','X','selected_seeds'):totals[key+'_mean']=totals[key+'_total']/n
    counts=packet['receipt']['stats'];require(counts['new_distances']==sx and counts['seeds_selected']==ss,'fixed256 sample X/winner trace parity')
    if counts['domain_fallbacks']==counts['nonfinite_failures']==0:require(counts['candidate_count']==sc,'fixed256 sample C parity')
    return totals,detail


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--analysis',type=Path,default=ROOT/'analysis/final_v1');parser.add_argument('--out',type=Path,default=ROOT/'reviews/independent_result_audit');args=parser.parse_args()
    require(args.root.is_absolute() and args.analysis.is_absolute() and args.out.is_absolute() and not args.out.exists(),'absolute fresh independent output')
    sources=Sources();configs,receipts,execution=administrative_gate(args.root,sources)
    # This line is the first boundary permitting existing saved GT/packet IDs.
    measured=load(args.analysis/'metrics.json');lock=load(args.root/'parameter_lock.json')
    require(measured['status']=='COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION' and measured['test_no_training'] is True and measured['default_replacement'] is False and measured['primary_method']==lock['primary_method'],'completed evaluation scope')
    require(measured['training_increment_seconds']==load(args.root/'run_state.json').get('training_increment_seconds'),'separate actual FIT cost retained')
    inventory=load(args.root/'reviews/inventory.json');preflight=load(args.root/'reviews/data_preflight.json')
    table_cache={};supports={};gts={};packets={};required=set()
    for c in configs:
        ds,role,n,N=c['dataset'],c['role'],c['n'],c['base_n']
        qualified=completion_qualification(c,args.root,sources,preflight,execution)
        if qualified:required.add(qualified)
        for pk,hk in [('queries','query_sha256'),('source_query_fvecs','source_query_sha256'),('source_GT_ivecs','source_GT_sha256')]:
            sources.adopt_stat_only(c[pk],c[hk],execution['input_stats'][c[pk]],preflight);required.add(c[pk])
        sources.digest(c['GT'],c['GT_sha256']);sources.digest(c['rows'],c['rows_sha256']);required.update((c['GT'],c['rows']))
        require(Path(c['queries']).stat().st_size==n*c['dimension']*4,'query bytes only; no query vector decode')
        container_n=10000 if ds==DATASETS[0] else 100000
        require(Path(c['source_query_fvecs']).stat().st_size==container_n*(c['dimension']+1)*4,'original public query stat-only container')
        require(list(ints(c['rows'],'q',n,sources))==list(range(n)),'exact public source rows0..9999')
        labels=ints(c['GT'],'i',n*100,sources);gt=[tuple(labels[i*100:(i+1)*100]) for i in range(n)]
        require(all(len(set(row))==100 and all(0<=x<N for x in row) for row in gt) and gt==official_GT_prefix(c['source_GT_ivecs'],n,container_n),'original frozen official GT ID copy exact')
        gts[(role,ds)]=gt
        for method in c['methods']:
            if method['table'] and method['table'] not in table_cache:table_cache[method['table']]=posting(method['table'],method['table_sha256'],sources,N)
        old=inventory['datasets'][ds];manifest=load(old['compile_manifest']);sources.digest(old['compile_manifest'])
        matches=[(p,s) for p,s in manifest['input_sha256'].items() if p.endswith('/fit/gt.i64')];require(len(matches)==1,'unique legal historical TRAIN GT100 source')
        tp,ts=matches[0];teacher=ints(tp,'q',20000*100,sources,ts);require(all(0<=x<N for x in teacher),'historical teacher domain')
        supports[ds]=(table_cache[old['m5']['path']][1],set(teacher),tp,ts);required.update((old['m5']['path'],old['compile_manifest'],tp))
    for key,(c,m,folder,r) in receipts.items():
        sources.digest(folder/'complete.json');required.add(str(folder/'complete.json'))
        p=read_packet(c,m,folder,r,gts[(c['role'],c['dataset'])],sources);p['base_n']=c['base_n'];packets[key]=p
        for path in (folder/'raw').iterdir():
            if path.is_file():sources.digest(path);required.add(str(path))
        if m['table']:
            f=folder/'full_oracle_stats.json';sources.digest(f);required.add(str(f));full=load(f)
            require(full['cachedmain_R_word_mismatches']==0,'no full cached R word mismatch')
            if m['optimized']:require(full['cachedmain_valid_R_checks']==c['n']*r['K'],'all valid saved cached R words checked')
            require(full['n']==c['n'] and full['scope']=='single full normal plain run counters; helper audit callbacks included; separate independent fresh-DC oracle calls not included','full oracle count scope separate from timed/count')
    for key,p in packets.items():
        role,ds,K,L,name=key;ref=packets[(role,ds,K,L,'GT')];s=p['receipt']['stats'];m=p['method']
        require(all(isinstance(x,int) and x>=0 for x in s.values()),'nonnegative physical count fields')
        if name=='NSG':require(all(x==0 for x in s.values()),'NSG no route/post work');continue
        require(p['entries']==ref['entries'] and p['profiles']==ref['profiles'] and p['route']==ref['route'],'unchanged GT route words')
        require(all(a>=b for a,b in zip(p['graph'],ref['graph'])) and sum(p['graph'])-sum(ref['graph'])==s['post_dots']+s['new_distances']==s['additional_scalar_calls'],'sample actual scalar fee')
        if m['family'] in ('opt','opt_reg'):
            original=packets[(role,ds,K,L,'M5' if m['family']=='opt' else 'M5REG96')]
            require(p['ids']==original['ids'] and p['words']==original['words'] and p['entries']==original['entries'] and p['profiles']==original['profiles'],'optimized full saved packet exact original identity')
        if m['table'] and s['domain_fallbacks']==s['nonfinite_failures']==0 and s.get('r_cache_fallback_queries',0)==0:
            paid=0;rows=table_cache[m['table']][0]
            for qi in p['audit_ids']:
                R={x for x in ref['ids'][qi*K:(qi+1)*K] if x>=0};C=candidate_plan(rows,ref['entries'][qi*3:(qi+1)*3],R)
                if C:paid+=len(C)+(0 if m['optimized'] or m['family'] in ('bank','route_bank') else len(R))
            require(s['post_dots']==paid,'independent sampled C and cached/fresh R fee')
        if m['family'] in ('reg','opt_reg'):
            require(s['graph_slots']==s['new_distances']+s['main_seen_skips']+s['c_duplicate_skips']+s['x_duplicate_skips']+s['invalid_neighbor_skips'],'physical neighbor slot exhaustive classification')
    points=[p['point'] for p in packets.values()];comparisons=[compare(a,b) for a,b in comparison_pairs(configs,packets)];mechanisms=[];details=[]
    for key,p in packets.items():
        if p['method']['family'] not in ('reg','bank','route_bank'):continue
        role,ds,K,L,name=key;c=receipts[key][0];U,teacher,_,_=supports[ds];completion=None
        if p['method']['family'] in ('bank','route_bank'):
            completion,path=completion_model(c,K,L,p['method']['completion_family'],sources,preflight,execution);required.add(path)
        m,d=trace_audit(p,packets[(role,ds,K,L,'M5')],packets[(role,ds,K,L,'GT')],gts[(role,ds)],table_cache[p['method']['table']][0],U,teacher,sources,completion)
        mechanisms.append(m);details.append(dict(m,**d))
    expected_mech=sum(sum(m['family'] in ('reg','bank','route_bank') for m in c['methods'])*len(c['K_values'])*len(c['L']) for c in configs)
    require(len(mechanisms)==expected_mech and measured['scope']==dict(points=len(points),formal_timed_batches=3*len(points),comparisons=len(comparisons),mechanisms=expected_mech,same_L_all_unique_pairs=True),'dynamic measured scope exact')
    match_rows(measured['points'],points,point_key,'metrics points');match_rows(measured['comparisons'],comparisons,comparison_key,'metrics comparisons');match_rows(measured['mechanisms'],mechanisms,point_key,'metrics mechanisms')
    for name,rows,key in [('points.csv',points,point_key),('comparisons.csv',comparisons,comparison_key),('mechanisms.csv',mechanisms,point_key)]:
        match_rows(csv_rows(args.analysis/name),rows,key,name);sources.digest(args.analysis/name)
    cmp_json={comparison_key(r):r for r in measured['comparisons']}
    for r in measured['comparisons']:
        key=f"{r['role']}|{r['dataset']}|{r['K']}|{r['L']}|{r['method']}|{r['reference_L']}|{r['reference']}";ci=r['delta_ci'];seed=(20261010+int.from_bytes(hashlib.sha256(key.encode()).digest()[:4],'little'))%2**32
        require(ci['seed']==seed and ci['repeats']==2000 and ci['scope']==LIMITS['bootstrap'] and math.isfinite(ci['low_pp']) and math.isfinite(ci['high_pp']) and -100<=ci['low_pp']<=ci['high_pp']<=100,'descriptive CI metadata; endpoints not regenerated')
    for r in csv_rows(args.analysis/'comparisons.csv'):require(json.loads(r['delta_ci'])==cmp_json[comparison_key(r)]['delta_ci'],'CI CSV/JSON exact')
    require(required<=measured['source_sha256'].keys(),'all label/model/packet provenance registered')
    for path,record in sources.files.items():
        if path in measured['source_sha256']:require(record['sha256']==measured['source_sha256'][path],'evaluator and independent source bytes')
    sources.digest(args.analysis/'metrics.json');sources.digest(Path(__file__));sources.stable()
    for path,s in execution['input_stats'].items():require(stat4(Path(path).stat())==s,'frozen input stable after audit')
    final=load(args.root/'run_state.json');require(final['status']=='NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and final.get('active') is None,'completion gate stable')
    report=dict(status='PASS_E176_INDEPENDENT_DYNAMIC_INTEGER_WALL_TRACE_AUDIT',independent_of_evaluate_import=True,point_count=len(points),formal_timed_batches=3*len(points),comparison_count=len(comparisons),full_region_trace_points=sum(p['method']['family']=='reg' for p in packets.values()),completion_trace_points=sum(p['method']['family'] in ('bank','route_bank') for p in packets.values()),mechanism_count=len(mechanisms),optimized_packet_identity_points=sum(p['method']['family'] in ('opt','opt_reg') for p in packets.values()),all_role_GT_decoded_only_after_full_native_gate=True,test_no_training=True,training_increment_seconds=measured['training_increment_seconds'],default_replacement=False,base_or_query_vector_values_read=False,new_distance_or_GT_generated=False,source_sha256_and_stat4=sources.files,public_source_GT_prefix_ID_copy_checked=True,query_original_and_derived_value_read=False,limits=['One full normal untimed native oracle pass, no second full native replay; timed output packets not retained.','NDC statistics fixed256 only; candidate ID traces full10K for saved families.','OldREG seed score minima and graph arrival, BANK row winner score minima and fresh merge words rely full frozen native oracle; no graph/vector/distance reads in independent audit.','BANK row key repetitions legal; independent table arrival and C/X/GT rescue/damage sets checked.','Paired CI seed/count/scope and CSV endpoints checked; stochastic CI endpoints not regenerated.','Historical exposed public10K role, no new confirmation; actual FIT phase costs separate, prior TRAIN debt retained.'])
    args.out.mkdir(parents=True);(args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');save_csv(args.out/'independent_points.csv',points);save_csv(args.out/'independent_comparisons.csv',comparisons);save_csv(args.out/'independent_mechanisms.csv',details)
    print(json.dumps({k:report[k] for k in ('status','point_count','formal_timed_batches','comparison_count','mechanism_count')}))

if __name__=='__main__':main()
