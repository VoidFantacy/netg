#!/usr/bin/env python3
"""Frozen P3 portal-exposure diagnosis from saved metadata/count rows only.

No raw GT, labels, vectors, graph, ANN, fitting, new CI, or stage-gate decision.
The root runs actual data serially; --self-test uses generated tiny fixtures only.
"""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import time

import numpy as np

RUN = Path(__file__).resolve().parents[1]
P3 = RUN / 'p3'
PROTOCOL_SHA = '4bdd1cd92b42d85f89bd69aec980068c9bed0d5aee90917d5ce2ad8db9823959'
P3_HELPER_SHA = 'a840b060a61061df6e60ae6166cd9a090570ef6ec0002a3ec7c7deea14e4e03e'
INTERPRETATION_SHA = 'e39e4a3056365ff708808fd57906b0c02a5715916b4662b6b848e71a87689402'
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
SHAPES = {DATASETS[0]: (2505000, 512), DATASETS[1]: (10000000, 200)}
LS, NQ = (64, 128), 10000
METRICS = ('routing_ndc', 'graph_ndc', 'total_ndc', 'routing_mac', 'graph_mac', 'total_mac',
           'expanded', 'rejected', 'evicted_unexpanded')
ROUTE_CLASSES = ('same_ordered_actual_entries', 'same_entry_set_changed_order', 'changed_entry_set')
RAW_SIGNS = ('negative', 'zero', 'positive')
WEIGHTED_SIGNS = RAW_SIGNS + ('undefined',)
# These exact existing verification hashes were recorded before this diagnosis in
# interpretation_limits_v1.md, itself bound by the frozen upstream P3 gate.
VERIFICATION_SHAS = {
    (DATASETS[0], 0): '0c3f5610ee27723045da645e6295f0fe9c18408ac6561c3e7e2e05943668d033',
    (DATASETS[0], 1): '2329594de0a72d9eac433d21fee7656ddc0d1513be5ee1ba09f6835bdc7c75b1',
    (DATASETS[1], 0): '5f306373f208377361efda41acee86d64abd616df22cdc00184f77b459e37a23',
    (DATASETS[1], 1): 'f38a098473ca73eabd3725b53ab55be0643342cac0fa3681c9225fc30942a4e9',
}
SOFT_CLOSE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deadline():
    require(time.time() < SOFT_CLOSE, 'P3 diagnosis closed at registered soft deadline')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def binding(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def write_json(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write('\n')


def checked_path(desc, *, root=RUN, suffix='.json', size=None):
    path = Path(desc['path']).resolve()
    require(path.is_relative_to(root.resolve()) and path.suffix == suffix,
            'Read boundary rejects artifact path/type: ' + str(path))
    require(type(desc['sha256']) is str and len(desc['sha256']) == 64,
            'Invalid artifact digest')
    require(path.stat().st_size <= 512 * 1024 * 1024, 'Oversized saved artifact')
    if size is not None:
        require(path.stat().st_size == size, 'Artifact byte shape differs')
    require(sha(path) == desc['sha256'], 'Saved artifact SHA256 mismatch: ' + str(path))
    return path


def read_bound(desc, **kwargs):
    path = checked_path(desc, **kwargs)
    return json.loads(path.read_text())


def helpers():
    path = P3 / 'analyze_p3.py'
    require(sha(path) == P3_HELPER_SHA, 'Frozen P3 artifact helper changed')
    spec = importlib.util.spec_from_file_location('frozen_p3_portal_diagnosis_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, module.import_p2()


def uint(value, name):
    require(type(value) is int and value >= 0, 'Invalid nonnegative integer: ' + name)
    return value


def sign(value):
    return 'negative' if value < 0 else 'positive' if value > 0 else 'zero'


def actual_order(row):
    # RegionalSearch.h initializes the shared default first, then route.entries.
    return ([row['shared_seed']] if row['shared_seed'] >= 0 else []) + row['entry_ids']


def route_key(row):
    return (row['fast_anchor_id'], row['shared_seed'], row['actual_entry_count'],
            tuple(row['entry_ids']), tuple(row['regions']),
            tuple(struct.pack('<d', x) for x in row['weights']))


def validate_proxy(report, frequency, greedy):
    rows = report['regions']
    require(len(rows) == 256 and [r['region'] for r in rows] == list(range(256)),
            'Proxy needs all 256 ordered leaves')
    for r, row in enumerate(rows):
        support = uint(row['eligible_target_support'], 'target support')
        queries = uint(row['query_count'], 'fit query count')
        require(queries <= 128 and queries <= support <= 10 * queries,
                'Invalid per-leaf selected-query/target support')
        require(row['no_fit_query_evidence'] is (queries == 0), 'No-fit evidence flag differs')
        require(3 <= uint(row['candidate_count'], 'candidate count') <= 8 and
                row['probe_calls'] == row['candidate_count'] * queries, 'Proxy call count differs')
        require(row['frequency_portals'] == frequency[r].tolist() and
                row['greedy_portals'] == greedy[r].tolist(), 'Proxy portals differ from bound model array')
        for field in ('frequency_union_hits', 'greedy_union_hits'):
            require(uint(row[field], field) <= support, 'Union hits exceed target support')
        gains = row['greedy_gains']
        require(len(gains) == 3 and all(type(x) is int and x >= 0 for x in gains) and
                sum(gains) == row['greedy_union_hits'], 'Greedy marginal sum differs')
        delta = row['greedy_union_hits'] - row['frequency_union_hits']
        require(type(row['greedy_minus_frequency_hits']) is int and
                row['greedy_minus_frequency_hits'] == delta, 'Cached proxy delta differs')
        if support == 0:
            require(delta == 0 and row['frequency_portals'] == row['greedy_portals'],
                    'Empty-fit leaf must retain the frequency fallback')
    deltas = [r['greedy_minus_frequency_hits'] for r in rows]
    stats = report['fit_proxy_description']
    expected = {
        'sum_frequency_union_hits': sum(r['frequency_union_hits'] for r in rows),
        'sum_greedy_union_hits': sum(r['greedy_union_hits'] for r in rows),
        'sum_greedy_minus_frequency_hits': sum(deltas),
        'negative_leaves': sum(x < 0 for x in deltas), 'zero_leaves': sum(x == 0 for x in deltas),
        'positive_leaves': sum(x > 0 for x in deltas),
        'no_fit_query_leaves': sum(r['no_fit_query_evidence'] for r in rows),
        'delta_min': min(deltas), 'delta_max': max(deltas),
    }
    require(all(stats[k] == v for k, v in expected.items()), 'Aggregate fit proxy differs from all leaves')
    require(stats['population_or_online_inference_allowed'] is False, 'Proxy cannot become population Recall')
    return rows


def validate_count_cells(artifact, portals, n, dim, p3, p2, nq=NQ):
    p3.check_schedule(artifact, 'count')
    groups = p3.cell_groups(artifact, 'count')
    result = {}
    default = groups[(64, 'oracle_probability', 0)]['per_query'][0]['shared_seed']
    require(type(default) is int and 0 <= default < n, 'Invalid fixed default seed')
    for l in LS:
        cell = groups[(l, 'oracle_probability', 0)]
        rows = cell['per_query']
        require(len(rows) == nq and [r['query_id'] for r in rows] == list(range(nq)) and
                all(type(r['query_id']) is int for r in rows), 'Missing/reordered pilot query IDs')
        require(p2.fingerprint_rows(rows) == (cell['result_hash_fnv1a64'], cell['route_hash_fnv1a64']),
                'Saved result/route fingerprint differs')
        require(cell['oracle'] is True and cell['top_k'] == 10 and cell['round'] == 0 and
                cell['qps'] is None and cell['batch_wall_us'] is None and cell['timing_publishable'] is False and
                cell['repeated_routes_results_stable'] is True, 'Invalid oracle count cell semantics')
        for row in rows:
            p3.check_route(row, 'oracle_probability', portals, n, default)
            recall = row['recall']
            require(type(recall) in (int, float) and math.isfinite(recall) and 0 <= recall <= 1 and
                    abs(10 * recall - round(10 * recall)) < 1e-10, 'Invalid Recall@10')
            for field in METRICS:
                uint(row[field], field)
            require(row['total_ndc'] == row['routing_ndc'] + row['graph_ndc'] and
                    row['graph_mac'] == dim * row['graph_ndc'] and
                    row['routing_mac'] == dim * row['routing_ndc'] and
                    row['total_mac'] == row['graph_mac'] + row['routing_mac'], 'NDC/MAC accounting mismatch')
        require(abs(sum(r['recall'] for r in rows) / nq - cell['mean_recall']) < 1e-10,
                'Count Recall mean differs')
        for field in METRICS[:6]:
            require(abs(sum(r[field] for r in rows) / nq - cell['mean_' + field]) < 1e-7,
                    'Count metric mean differs: ' + field)
        result[l] = cell
    require(all(route_key(a) == route_key(b) for a, b in
                zip(result[64]['per_query'], result[128]['per_query'])), 'L changed actual route')
    return result


def pair_rows(reference, candidate, proxy):
    require(len(reference) == len(candidate), 'Unequal paired query count')
    rows = []
    for index, (a, b) in enumerate(zip(reference, candidate)):
        if index % 1024 == 0:
            deadline()
        require(a['query_id'] == b['query_id'] == index, 'Paired query alignment differs')
        require(a['regions'] == b['regions'] and
                [struct.pack('<d', x) for x in a['weights']] == [struct.pack('<d', x) for x in b['weights']] and
                a['shared_seed'] == b['shared_seed'] and a['fast_anchor_id'] == b['fast_anchor_id'],
                'Same-lambda portal contrast changed oracle/default/anchor context')
        entries_a, entries_b = actual_order(a), actual_order(b)
        klass = ROUTE_CLASSES[0] if entries_a == entries_b else ROUTE_CLASSES[1] if set(entries_a) == set(entries_b) else ROUTE_CLASSES[2]
        same_route = route_key(a) == route_key(b)
        require(same_route == (klass == ROUTE_CLASSES[0]), 'Complete route/ordered-entry class mismatch')
        if same_route:
            require(a['result_ids'] == b['result_ids'] and a['recall'] == b['recall'] and
                    all(a[k] == b[k] for k in METRICS),
                    'INTEGRITY_FAILURE: identical complete ordered route changed results/Recall/oracle counters')
        leaves = [proxy[r] for r in a['regions']]
        delta = [r['greedy_minus_frequency_hits'] for r in leaves]
        support = [r['eligible_target_support'] for r in leaves]
        ratios = [d / s if s else None for d, s in zip(delta, support)]
        missing_weight = math.fsum(w for w, s in zip(a['weights'], support) if s == 0)
        missing_positive = sum(w > 0 and s == 0 for w, s in zip(a['weights'], support))
        # Zero-weight unsupported leaves contribute nothing. Positive-weight
        # unsupported leaves make the whole score undefined; never renormalize.
        weighted = None if missing_positive else math.fsum(w * ratio for w, ratio in zip(a['weights'], ratios) if ratio is not None)
        hit_a, hit_b = round(10 * a['recall']), round(10 * b['recall'])
        row = {'query_id': index, 'route_class': klass, 'complete_ordered_route_equal': same_route,
               'actual_entry_count_reference': a['actual_entry_count'], 'actual_entry_count_candidate': b['actual_entry_count'],
               'result_order_equal': a['result_ids'] == b['result_ids'],
               'result_set_equal': set(x for x in a['result_ids'] if x >= 0) == set(x for x in b['result_ids'] if x >= 0),
               'reference_hit_count': hit_a, 'candidate_hit_count': hit_b, 'delta_recall_pp': 10 * (hit_b - hit_a),
               'active_leaves': list(a['regions']), 'conditional_weights': list(a['weights']),
               'leaf_proxy_deltas': delta, 'leaf_target_support': support, 'leaf_proxy_ratios': ratios,
               'sum_proxy_delta': sum(delta), 'sum_proxy_delta_sign': sign(sum(delta)),
               'weighted_proxy_score': weighted, 'weighted_proxy_score_sign': 'undefined' if weighted is None else sign(weighted),
               'missing_support_weight': missing_weight, 'missing_support_leaf_count': support.count(0),
               'missing_positive_weight_support_leaf_count': missing_positive}
        for field in METRICS:
            row[field + '_reference'] = a[field]
            row[field + '_candidate'] = b[field]
            row[field + '_delta'] = b[field] - a[field]
        rows.append(row)
    return rows


def aggregate(rows):
    n = len(rows)
    scores = [r['weighted_proxy_score'] for r in rows if r['weighted_proxy_score'] is not None]
    out = {'query_count': n,
           'same_result_order': sum(r['result_order_equal'] for r in rows),
           'same_result_set': sum(r['result_set_equal'] for r in rows),
           'changed_result_order': sum(not r['result_order_equal'] for r in rows),
           'changed_result_set': sum(not r['result_set_equal'] for r in rows),
           'same_result_set_changed_order': sum(r['result_set_equal'] and not r['result_order_equal'] for r in rows),
           'recall_wins': sum(r['delta_recall_pp'] > 0 for r in rows),
           'recall_losses': sum(r['delta_recall_pp'] < 0 for r in rows),
           'recall_equal': sum(r['delta_recall_pp'] == 0 for r in rows),
           'equal_recall_but_changed_result_order': sum(r['delta_recall_pp'] == 0 and not r['result_order_equal'] for r in rows),
           'equal_recall_but_changed_result_set': sum(r['delta_recall_pp'] == 0 and not r['result_set_equal'] for r in rows),
           'mean_delta_recall_pp': sum(r['delta_recall_pp'] for r in rows) / n if n else None,
           'complete_ordered_route_equal_queries': sum(r['complete_ordered_route_equal'] for r in rows),
           'weighted_score_defined_queries': len(scores), 'weighted_score_undefined_queries': n - len(scores),
           'mean_weighted_proxy_score_among_defined': math.fsum(scores) / len(scores) if scores else None,
           'mean_sum_proxy_delta': sum(r['sum_proxy_delta'] for r in rows) / n if n else None,
           'mean_missing_support_weight': math.fsum(r['missing_support_weight'] for r in rows) / n if n else None}
    for field in METRICS:
        out['mean_' + field + '_reference'] = sum(r[field + '_reference'] for r in rows) / n if n else None
        out['mean_' + field + '_candidate'] = sum(r[field + '_candidate'] for r in rows) / n if n else None
        out['mean_' + field + '_delta'] = sum(r[field + '_delta'] for r in rows) / n if n else None
    require(out['recall_wins'] + out['recall_losses'] + out['recall_equal'] == n, 'Recall partition failed')
    return out


def summarize_cell(rows):
    out = {'overall': aggregate(rows), 'by_route_class': [], 'by_sum_proxy_delta_sign': [],
           'by_weighted_proxy_score_sign': [], 'by_route_and_sum_delta_sign': [], 'by_route_and_weighted_score_sign': []}
    for klass in ROUTE_CLASSES:
        chosen = [r for r in rows if r['route_class'] == klass]
        out['by_route_class'].append({'route_class': klass, **aggregate(chosen)})
        for field, signs, key in (('sum_proxy_delta_sign', RAW_SIGNS, 'by_route_and_sum_delta_sign'),
                                  ('weighted_proxy_score_sign', WEIGHTED_SIGNS, 'by_route_and_weighted_score_sign')):
            for s in signs:
                out[key].append({'route_class': klass, field: s, **aggregate([r for r in chosen if r[field] == s])})
    for field, signs, key in (('sum_proxy_delta_sign', RAW_SIGNS, 'by_sum_proxy_delta_sign'),
                              ('weighted_proxy_score_sign', WEIGHTED_SIGNS, 'by_weighted_proxy_score_sign')):
        for s in signs:
            out[key].append({field: s, **aggregate([r for r in rows if r[field] == s])})
    for key in out:
        if key != 'overall':
            require(sum(g['query_count'] for g in out[key]) == len(rows), 'Grouping omitted/duplicated queries: ' + key)
    out['identical_route_invariance'] = {'status': 'PASS',
        'queries_checked': out['overall']['complete_ordered_route_equal_queries'],
        'mismatches': 0, 'note': 'No same-route queries means a vacuous check, not evidence of invariance.'}
    return out


def save_rows(path, rows):
    require(rows, 'Cannot save an empty dataset diagnosis')
    arrays = {}
    for key in rows[0]:
        vals = [r[key] for r in rows]
        if key == 'route_class':
            arrays[key] = np.asarray([ROUTE_CLASSES.index(v) for v in vals], dtype=np.uint8)
        elif key in ('sum_proxy_delta_sign', 'weighted_proxy_score_sign'):
            arrays[key] = np.asarray([{'negative': -1, 'zero': 0, 'positive': 1, 'undefined': 2}[v] for v in vals], dtype=np.int8)
        elif key in ('weighted_proxy_score', 'leaf_proxy_ratios'):
            arrays[key] = np.asarray(vals, dtype=np.float64)  # None -> NaN, explicitly described in schema.
        elif key in ('conditional_weights', 'missing_support_weight'):
            arrays[key] = np.asarray(vals, dtype=np.float64)
        elif type(vals[0]) is bool:
            arrays[key] = np.asarray(vals, dtype=np.bool_)
        else:
            arrays[key] = np.asarray(vals, dtype=np.int64)
    with path.open('xb') as f:
        np.savez_compressed(f, **arrays)
    return {'file': binding(path), 'rows': len(rows), 'arrays': {k: {'dtype': str(v.dtype), 'shape': list(v.shape)} for k, v in arrays.items()},
            'route_class_codes': dict(enumerate(ROUTE_CLASSES)), 'sign_codes': {'-1': 'negative', '0': 'zero', '1': 'positive', '2': 'undefined'},
            'undefined_floats': 'NaN only for weighted_proxy_score and unsupported leaf_proxy_ratios; not zero.',
            'unit': 'One row per dataset/lambda/L/pilot query; repeated query IDs across four cells are not independent samples.'}


def load_model(evidence, name, dataset, lam, rule, protocol):
    desc = evidence['models'][name]
    model = read_bound(desc['model'])
    n, dim = SHAPES[dataset]
    expected = {'schema_version': 2, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset,
                'model_name': name, 'lambda': lam, 'portal_rule': rule, 'base_nodes': n, 'dim': dim,
                'region_count': 256, 'coarse_count': 16, 'leaves_per_coarse': 16, 'portals_per_region': 3,
                'total_portals': 768, 'active_regions': 4, 'fit_range': [10000, 30000], 'fit_count': 20000,
                'cpu_only': True, 'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
                'oracle_diagnostic_only': True, 'independent_cache_verification': 'PASS_ALL_256_LEAVES'}
    require(all(model.get(k) == v for k, v in expected.items()), 'Frozen model metadata differs: ' + name)
    require(model['protocol'] == protocol['P3_protocol'] and model['audit'] == evidence['audit'] and
            model['protocol_sha256'] == protocol['P3_protocol']['sha256'], 'Model protocol/audit differs')
    require(model['partition_manifest'] == desc['partition_manifest'] and model['probe_complete'] == desc['probe_complete'] and
            Path(model['labels_file']).resolve() == Path(desc['labels']['path']).resolve() and
            model['labels_sha256'] == desc['labels']['sha256'], 'Model inherited label/partition/probe binding differs')
    portal_path = checked_path(desc['portals'], root=P3 / 'models', suffix='.i32', size=3072)
    require(Path(model['portals_file']).resolve() == portal_path and model['portals_sha256'] == desc['portals']['sha256'],
            'Model small portal-array binding differs')
    portals = np.fromfile(portal_path, dtype='<i4').reshape(256, 3)
    require(int(portals.min()) >= 0 and int(portals.max()) < n and all(len(set(r)) == 3 for r in portals), 'Invalid portal IDs')
    return model, portals


def load_count(desc, model, dataset_summary, p3, p2):
    artifact = read_bound(desc['count'])
    expected = {'schema_version': 1, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': model['dataset'],
                'split': 'pilot', 'source_query_type': 'drl_train', 'source_query_range': [0, NQ], 'num_queries': NQ,
                'measurement': 'count', 'threads': 16, 'cpu_only': True, 'metric': 'ip', 'top_k': 10, 'fast_m': 3,
                'search_Ls': list(LS), 'rounds': 1, 'warmup_queries': 128, 'heldout_accessed': False,
                'oracle_is_deployment': False, 'schedule_prerecorded': True, 'aligned_rows_round': 0,
                'trace_mode': False, 'region_count': 256, 'portals_per_region': 3,
                'base_nodes': model['base_nodes'], 'dim': model['dim']}
    require(all(artifact.get(k) == v for k, v in expected.items()), 'Count metadata differs from frozen pilot')
    require(artifact['model_manifest'] == model and artifact['model_sha256'] == desc['model']['sha256'] and
            Path(artifact['model_file']).resolve() == Path(desc['model']['path']).resolve(), 'Count model binding differs')
    return artifact


def diagnose_dataset(dataset_summary, protocol, out, p3, p2):
    dataset = dataset_summary['dataset']
    evidence = dataset_summary['evidence']
    require(dataset_summary['audit_status'] == 'PASS' and evidence['protocol'] == protocol['P3_protocol'], 'Prior dataset audit did not pass')
    cells, saved_rows, inputs = [], [], []
    for lam in (0, 1):
        deadline()
        models, portals, counts = {}, {}, {}
        for rule in ('frequency3', 'greedy3'):
            name = f'lambda{lam}_{rule}'
            models[rule], portals[rule] = load_model(evidence, name, dataset, lam, rule, protocol)
        require(models['frequency3']['labels_sha256'] == models['greedy3']['labels_sha256'] and
                models['frequency3']['labels_file'] == models['greedy3']['labels_file'] and
                models['frequency3']['partition_manifest'] == models['greedy3']['partition_manifest'] and
                models['frequency3']['plan'] == models['greedy3']['plan'] and
                models['frequency3']['probe_complete'] == models['greedy3']['probe_complete'], 'Portal comparison changed fitted structure/cache')
        vpath = P3 / 'models' / dataset / f'lambda{lam}' / 'verification.json'
        vdesc = {'path': str(vpath), 'sha256': VERIFICATION_SHAS[(dataset, lam)]}
        verification = read_bound(vdesc)
        require(verification['status'] == 'COMPLETE' and verification['stage'] == 'P3_PORTAL_FINALIZATION' and
                verification['dataset'] == dataset and verification['lambda'] == lam and verification['complete_leaves'] == 256 and
                verification['pilot_accessed'] is False and verification['validation_accessed'] is False and
                verification['heldout_accessed'] is False and verification['model_choice_based_on_pilot'] is False and
                verification['protocol'] == protocol['P3_protocol'], 'Frozen proxy verification scope differs')
        for rule in ('frequency3', 'greedy3'):
            model = models[rule]; name = model['model_name']; desc = evidence['models'][name]
            require(verification['models'][rule] == desc['model'] and verification['partition_manifest'] == model['partition_manifest'] and
                    verification['probe_complete'] == model['probe_complete'] and verification['plan'] == model['plan'] and
                    verification['source'] == model['finalizer_source'], 'Verification not bound to both evaluated models')
        proxy = validate_proxy(verification, portals['frequency3'], portals['greedy3'])
        for rule in ('frequency3', 'greedy3'):
            model = models[rule]; desc = evidence['models'][model['model_name']]
            artifact = load_count(desc, model, dataset_summary, p3, p2)
            counts[rule] = validate_count_cells(artifact, portals[rule], model['base_nodes'], model['dim'], p3, p2)
            del artifact
            for l in LS:
                c = counts[rule][l]
                saved = [m for m in dataset_summary['measurements'] if m['model'] == model['model_name'] and m['method'] == 'oracle_probability' and m['L'] == l]
                require(len(saved) == 1 and saved[0]['result_hash'] == c['result_hash_fnv1a64'] and
                        saved[0]['route_hash'] == c['route_hash_fnv1a64'] and abs(saved[0]['recall'] - c['mean_recall']) < 1e-10,
                        'Fresh count rows disagree with frozen analysis')
        inputs.append({'lambda': lam, 'verification': vdesc, 'frequency_model': evidence['models'][f'lambda{lam}_frequency3'],
                       'greedy_model': evidence['models'][f'lambda{lam}_greedy3'],
                       'fit_proxy': verification['fit_proxy_description'],
                       'fit_leaf_query_pairs': sum(r['query_count'] for r in proxy),
                       'fit_target_support': sum(r['eligible_target_support'] for r in proxy)})
        for l in LS:
            deadline()
            rows = pair_rows(counts['frequency3'][l]['per_query'], counts['greedy3'][l]['per_query'], proxy)
            summary = summarize_cell(rows)
            previous = [c for c in dataset_summary['fixed_comparisons'] if c['L'] == l and c['contrast'] == f'portals_under_lambda{lam}']
            require(len(previous) == 1, 'Missing fixed portal comparison in prior analysis')
            prior, overall = previous[0], summary['overall']
            require(abs(prior['recall_delta_pp'] - overall['mean_delta_recall_pp']) < 1e-10 and
                    prior['query_improved'] == overall['recall_wins'] and prior['query_harmed'] == overall['recall_losses'] and
                    prior['query_equal'] == overall['recall_equal'] and
                    abs(prior['mean_total_ndc_delta'] - overall['mean_total_ndc_delta']) < 1e-7,
                    'Portal-pair summary differs from frozen analysis')
            cells.append({'dataset': dataset, 'lambda': lam, 'L': l, 'method': 'oracle_probability',
                          'contrast': 'greedy3_minus_frequency3', **summary})
            for row in rows:
                row.update(structure_lambda=lam, search_L=l)
            saved_rows.extend(rows)
    require([(c['lambda'], c['L']) for c in cells] == [(x, l) for x in (0, 1) for l in LS] and
            all(c['overall']['query_count'] == NQ for c in cells), 'Incomplete fixed four-cell dataset diagnosis')
    arrays = save_rows(out / f'{dataset}.per_query.npz', saved_rows)
    record = {'schema_version': 1, 'status': 'COMPLETE', 'dataset': dataset, 'scope': 'P3_POST_NOGO_PORTAL_EXPOSURE_ONLY',
              'prior_analysis': protocol['analysis'], 'input_evidence': inputs, 'cells': cells, 'per_query': arrays,
              'raw_GT_labels_vectors_graph_read': False, 'ANN_calls': 0, 'new_confidence_intervals': False,
              'stage_gate_reopened': False, 'model_selection_or_tuning': False,
              'label_identity': 'Inherited exact saved labels/partition hashes from accepted models; label files are not opened here.',
              'cache_identity': 'Fresh fixed verification JSON hash and portal-array hash checks; cached masks and fit rows are not reopened.'}
    path = out / f'{dataset}.json'
    write_json(path, record)
    return {'dataset': dataset, 'summary': binding(path), 'per_query': arrays['file'], 'cells': len(cells),
            'same_ordered_route_queries_checked': sum(c['identical_route_invariance']['queries_checked'] for c in cells)}


def synthetic(p3, p2, out):
    """Tiny generated fixtures; no production count/model/verification inputs."""
    tests = []
    artifacts, portals, n, dim, nq, seed = p3.synthetic_artifacts(p2)
    count = artifacts['count']
    valid = validate_count_cells(count, portals, n, dim, p3, p2, nq)
    tests.append('tiny count cell hashes, route consumption, count metrics and L invariance')
    def reject(name, fn):
        try:
            fn()
        except (ValueError, KeyError, IndexError):
            tests.append(name)
        else:
            raise AssertionError('Bad synthetic fixture accepted: ' + name)
    for label, change in (
        ('missing cell', lambda x: x['results'].pop()),
        ('reordered query', lambda x: x['results'][-1]['per_query'].reverse()),
        ('changed hash', lambda x: x['results'][-1].__setitem__('route_hash_fnv1a64', 0)),
        ('counter boolean', lambda x: x['results'][-1]['per_query'][0].__setitem__('expanded', True)),
        ('recall outside range', lambda x: x['results'][-1]['per_query'][0].__setitem__('recall', -0.1)),
    ):
        bad = copy.deepcopy(count); change(bad)
        reject(label, lambda bad=bad: validate_count_cells(bad, portals, n, dim, p3, p2, nq))
    frequency = np.arange(768, dtype='<i4').reshape(256, 3)
    greedy = frequency.copy()
    for q in range(3, 6):
        greedy[q * 4] = greedy[q * 4][::-1]
    for q in range(6, 9):
        greedy[q * 4, -1] += 1000
    proxy = []
    for r in range(256):
        proxy.append({'region': r, 'query_count': 10, 'candidate_count': 8, 'probe_calls': 80,
                      'eligible_target_support': 100, 'no_fit_query_evidence': False,
                      'frequency_portals': frequency[r].tolist(), 'greedy_portals': greedy[r].tolist(),
                      'frequency_union_hits': 50, 'greedy_union_hits': 50, 'greedy_gains': [50, 0, 0],
                      'greedy_minus_frequency_hits': 0})
    patterns = ([-2, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0], [-2, 0, 0, 0], [0, 0, 0, 0],
                [-9, 10, 0, 0], [10, -11, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0])
    for q, ds in enumerate(patterns):
        for r, delta in zip(range(q * 4, q * 4 + 4), ds):
            proxy[r].update(greedy_union_hits=50 + delta, greedy_minus_frequency_hits=delta, greedy_gains=[50 + delta, 0, 0])
    for r in (29, 35):
        proxy[r].update(query_count=0, probe_calls=0, eligible_target_support=0, no_fit_query_evidence=True,
                        frequency_union_hits=0, greedy_union_hits=0, greedy_gains=[0, 0, 0])
    deltas = [r['greedy_minus_frequency_hits'] for r in proxy]
    report = {'regions': proxy, 'fit_proxy_description': {
        'sum_frequency_union_hits': sum(r['frequency_union_hits'] for r in proxy),
        'sum_greedy_union_hits': sum(r['greedy_union_hits'] for r in proxy), 'sum_greedy_minus_frequency_hits': sum(deltas),
        'negative_leaves': sum(x < 0 for x in deltas), 'zero_leaves': sum(x == 0 for x in deltas),
        'positive_leaves': sum(x > 0 for x in deltas), 'no_fit_query_leaves': 2,
        'delta_min': min(deltas), 'delta_max': max(deltas), 'population_or_online_inference_allowed': False}}
    validate_proxy(report, frequency, greedy)
    tests.append('all 256 fit proxy rows, selected portal arrays and aggregate identity')
    bad = copy.deepcopy(report); bad['regions'][0]['eligible_target_support'] = 0
    reject('unsupported leaf cannot retain nonzero proxy hits', lambda: validate_proxy(bad, frequency, greedy))
    template = valid[64]['per_query'][0]
    reference, candidate = [], []
    for q in range(9):
        a = copy.deepcopy(template); a['query_id'] = q; a['regions'] = list(range(q * 4, q * 4 + 4))
        if q == 8:
            a['weights'] = [.5, .5, 0., 0.]
        a['entry_ids'] = [a['fast_anchor_id']] + [int(x) for r in a['regions'] for x in frequency[r]]
        b = copy.deepcopy(a)
        b['entry_ids'] = [b['fast_anchor_id']] + [int(x) for r in b['regions'] for x in greedy[r]]
        if q == 3:
            b['result_ids'].reverse()
        if q == 4:
            b['result_ids'][-1] = 1000  # Same Recall, a different returned set.
        if q == 5:
            b['recall'] = .6
        if q == 6:
            b['recall'] = .4
        for row, array in ((a, frequency), (b, greedy)):
            p3.check_route(row, 'oracle_probability', array, n, seed)
        reference.append(a); candidate.append(b)
    paired = pair_rows(reference, candidate, proxy)
    result = summarize_cell(paired)
    require([g['query_count'] for g in result['by_route_class']] == [3, 3, 3] and
            all(g['query_count'] == 1 for g in result['by_route_and_sum_delta_sign']), 'Nine route/raw-sign bins incorrect')
    require(paired[5]['sum_proxy_delta_sign'] == 'positive' and paired[5]['weighted_proxy_score_sign'] == 'negative' and
            paired[6]['sum_proxy_delta_sign'] == 'negative' and paired[6]['weighted_proxy_score_sign'] == 'positive', 'Two exposure signs conflated')
    require(paired[7]['weighted_proxy_score'] is None and paired[7]['missing_support_weight'] == .3 and
            paired[8]['weighted_proxy_score'] == .005 and paired[8]['missing_support_leaf_count'] == 1,
            'Positive/zero weight unsupported-leaf rule differs')
    require(result['overall']['equal_recall_but_changed_result_order'] == 2 and
            result['overall']['equal_recall_but_changed_result_set'] == 1 and result['overall']['recall_wins'] == 1 and
            result['overall']['recall_losses'] == 1 and result['overall']['mean_delta_recall_pp'] == 0,
            'Equal Recall incorrectly treated as identical outputs')
    require(any(g['query_count'] == 0 and g['mean_delta_recall_pp'] is None for g in result['by_route_and_weighted_score_sign']),
            'Empty bins were dropped or zero-filled')
    tests.append('nine route/raw-sign combinations, separate weighted signs, unsupported weights and empty bins')
    for field, value in [('result_ids', list(range(1, 11))), ('recall', .6)] + [(field, 999) for field in METRICS]:
        bad = copy.deepcopy(candidate); bad[0][field] = value
        reject('identical route integrity rejects changed ' + field, lambda bad=bad: pair_rows(reference, bad, proxy))
    bad = copy.deepcopy(candidate); bad[1]['fast_anchor_id'] = 901
    reject('fixed oracle/anchor context cannot change', lambda: pair_rows(reference, bad, proxy))
    for r in paired:
        r.update(structure_lambda=0, search_L=64)
    saved = save_rows(out / 'synthetic.per_query.npz', paired)
    with np.load(saved['file']['path'], allow_pickle=False) as arrays:
        require(np.isnan(arrays['weighted_proxy_score'][7]) and arrays['route_class'].tolist() == [0] * 3 + [1] * 3 + [2] * 3 and
                arrays['query_id'].tolist() == list(range(9)), 'Compact output roundtrip differs')
    tests.append('compact NPZ roundtrip including explicit undefined NaN')
    tiny = out / 'read_boundary.json'; write_json(tiny, {'generated': True})
    desc = binding(tiny); require(read_bound(desc, root=out) == {'generated': True}, 'Tiny bound read failed')
    bad_desc = {**desc, 'sha256': '0' * 64}
    reject('bound file hash drift', lambda: read_bound(bad_desc, root=out))
    reject('outside generated read boundary', lambda: read_bound(desc, root=out / 'inside_only'))
    write_json(out / 'synthetic_summary.json', result)
    record = {'status': 'PASS', 'source': binding(__file__), 'tests': tests, 'test_count': len(tests),
              'fixture_queries': 9, 'actual_data_read': False, 'ANN_calls': 0, 'per_query': saved}
    write_json(out / 'selftest.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    require(args.self_test or args.protocol is not None, '--protocol is required for actual saved-output diagnosis')
    deadline()
    args.output.mkdir(parents=True, exist_ok=False); args.output = args.output.resolve()
    source = binding(__file__)
    write_json(args.output / 'invocation.json', {'status': 'STARTED', 'source': source, 'argv': sys.argv,
               'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'self_test': args.self_test,
               'scope': 'PORTAL_EXPOSURE_ONLY', 'raw_GT_labels_vectors_graph_allowed': False})
    completed = []
    started = time.perf_counter()
    try:
        p3, p2 = helpers()
        if args.self_test:
            record = synthetic(p3, p2, args.output)
            write_json(args.output / 'complete.json', {'status': 'PASS_SELF_TEST', 'selftest': binding(args.output / 'selftest.json')})
            print(json.dumps({'status': 'PASS_SELF_TEST', 'test_count': record['test_count']}))
            return
        require(sha(args.protocol) == PROTOCOL_SHA, 'Frozen diagnosis protocol SHA differs')
        protocol = json.loads(args.protocol.read_text())
        require(protocol['status'] == 'PREREGISTERED_BEFORE_DIAGNOSTIC_IMPLEMENTATION_AND_NEW_DATA_READS' and
                protocol['stage'] == 'P3_POST_NOGO_DIAGNOSIS' and protocol['datasets'] == list(DATASETS) and
                protocol['P4_authorized'] is False and protocol['new_model_or_auxgraph_authorized'] is False,
                'Invalid bounded diagnosis authorization')
        gate = read_bound(protocol['upstream_P3'])
        require(gate['status'] == 'NOPASS' and gate['decision'] == 'NO_GO_P3_SEARCH_TRANSFER' and
                gate['protocol'] == protocol['P3_protocol'] and protocol['analysis'] in gate['evidence'] and
                any(x['sha256'] == INTERPRETATION_SHA for x in gate['evidence']), 'Upstream failed branch/binding differs')
        analysis = read_bound(protocol['analysis'])
        require(analysis['status'] == 'COMPLETE' and analysis['automatic_P3_GO'] is False and
                analysis['primary_search_condition']['all_four_lower_bounds_positive'] is False and
                [d['dataset'] for d in analysis['datasets']] == list(DATASETS), 'Frozen complete failed P3 analysis required')
        for dataset_summary in analysis['datasets']:
            deadline()
            completed.append(diagnose_dataset(dataset_summary, protocol, args.output, p3, p2))
            print(json.dumps({'dataset': completed[-1]['dataset'], 'status': 'COMPLETE', 'cells': 4}), flush=True)
        require(len(completed) == 2 and sum(d['cells'] for d in completed) == 8, 'Exactly all eight portal cells required')
        record = {'schema_version': 1, 'status': 'COMPLETE', 'stage': 'P3_POST_NOGO_PORTAL_EXPOSURE',
                  'source': source, 'protocol': binding(args.protocol), 'upstream_P3': protocol['upstream_P3'],
                  'prior_analysis': protocol['analysis'], 'P3_helper': binding(P3 / 'analyze_p3.py'),
                  'datasets': completed, 'wall_seconds': time.perf_counter() - started,
                  'normalization': 'Per-leaf delta/support; conditional-weighted sum without renormalization. Any positive-weight unsupported leaf => undefined; zero-weight unsupported leaf contributes nothing.',
                  'raw_sum': 'All four active leaves, including leaves whose saved conditional weight is zero; raw-sum and weighted-score signs are separate.',
                  'limitations': ['Cached fit hits are correlated regional proxy counts, not population Recall.',
                                  'Same Recall does not imply identical top10 IDs or trajectories.',
                                  'Only saved oracle_probability counters are used; Fast unmeasured zero sentinels are excluded.',
                                  'Identical-route integrity is conditional on inherited frozen graph/labels and verified saved evaluator outputs.',
                                  'Post-hoc descriptive groups do not reopen P3, select a model, establish connectivity failure or authorize an auxiliary graph.'],
                  'raw_GT_labels_query_base_graph_read': False, 'ANN_calls': 0, 'new_confidence_intervals': False,
                  'stage_gate_reopened': False, 'P4_authorized': False, 'model_or_auxgraph_change_authorized': False}
        write_json(args.output / 'analysis.json', record)
        write_json(args.output / 'complete.json', {'status': 'COMPLETE', 'analysis': binding(args.output / 'analysis.json'), 'datasets': completed})
    except BaseException as e:
        write_json(args.output / 'failure.json', {'status': 'INCOMPLETE', 'error': repr(e), 'source': source,
                   'completed_datasets': completed, 'wall_seconds': time.perf_counter() - started,
                   'meaning': 'Integrity/diagnosis failure; no scientific gate or model decision is changed.'})
        raise


if __name__ == '__main__':
    main()
