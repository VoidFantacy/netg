#!/usr/bin/env python3
"""Audit complete P2 pilot artifacts and summarize fixed exploratory comparisons.

No evaluator, training, graph building, query/GT loading or stage advancement occurs.
The three queue contrasts are primary P2 diagnostics, not P5/P6 performance tests.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np

ROOT = Path('/data/netg/ACSG')
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
METHODS = ('fast', 'geom_unified', 'geom_uniform', 'geom_probability',
           'oracle_unified', 'oracle_probability')
ALIASES = {'fast_legacy': 'fast', 'geom_weighted': 'geom_probability',
           'oracle_weighted': 'oracle_probability'}
LS = (64, 128)
SEED = 2026090711
REPS = 10000
CONTRASTS = (
    ('uniform_protection', 'geom_uniform', 'geom_unified', 'primary_queue'),
    ('probability_protection', 'geom_probability', 'geom_unified', 'primary_queue'),
    ('oracle_protection', 'oracle_probability', 'oracle_unified', 'primary_queue'),
    ('oracle_selection_unified', 'oracle_unified', 'geom_unified', 'diagnostic_route_portal'),
    ('oracle_selection_protected', 'oracle_probability', 'geom_probability', 'diagnostic_route_portal'),
    ('geometric_bundle_vs_fast', 'geom_unified', 'fast', 'diagnostic_bundle'),
    ('oracle_bundle_vs_fast', 'oracle_unified', 'fast', 'diagnostic_bundle'),
)
MASK = (1 << 64) - 1


def check(condition, message):
    if not condition:
        raise ValueError(message)


def load_json(path):
    with Path(path).open() as f:
        return json.load(f)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def resolve(value, parent=ROOT):
    p = Path(value)
    return (p if p.is_absolute() else parent / p).resolve()


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def canon(name):
    return ALIASES.get(name, name)


def fingerprint_rows(rows):
    """Recompute evaluator's exact integer-word FNV hashes, including float bits."""
    ih = rh = 1469598103934665603
    for row in rows:
        for x in row['result_ids']:
            ih = ((ih ^ (int(x) & MASK)) * 1099511628211) & MASK
        route = [row['fast_anchor_id'], row['shared_seed'], len(row['entry_ids']), len(row['regions'])]
        route.extend(row['entry_ids'])
        for region, weight in zip(row['regions'], row['weights']):
            route += [region, struct.unpack('<Q', struct.pack('<d', weight))[0]]
        for x in route:
            rh = ((rh ^ (int(x) & MASK)) * 1099511628211) & MASK
    return ih, rh


def route_signature(row):
    return (row['fast_anchor_id'], row['shared_seed'], row['actual_entry_count'],
            tuple(row['entry_ids']), tuple(row['regions']), tuple(row['weights']))


def groups(artifact, measurement):
    result = {}
    for row in artifact['results']:
        key = (int(row['search_L']), canon(row['method']), int(row['round']))
        check(key not in result, f'duplicate result {key}')
        result[key] = row
    rounds = range(1 if measurement == 'count' else 5)
    expected = {(l, method, r) for l in LS for method in METHODS for r in rounds}
    check(set(result) == expected, f'{measurement} must contain all six methods at L64/128 and exact required rounds')
    return result


def verify_input(dataset, paths, protocol_hash, p1):
    count_path, timing_path, model_path, fast_path = map(lambda p: resolve(p), paths)
    count, timing, model, fast = map(load_json, (count_path, timing_path, model_path, fast_path))
    for a, kind in ((count, 'count'), (timing, 'timing')):
        check(a.get('status') == 'COMPLETE', f'{dataset}: incomplete {kind} cannot support analysis')
        check(a.get('stage') == 'P2' and a.get('dataset') == dataset, f'{dataset}: wrong stage/dataset')
        check(a.get('split') == 'pilot' and a.get('source_query_type') == 'drl_train', 'only P2 pilot artifacts are accepted; no validation/heldout')
        check(a.get('heldout_accessed') is False and a.get('cpu_only') is True, 'CPU/no-heldout contract violated')
        check(a.get('measurement') == kind and not a.get('trace_mode'), 'wrong measurement type')
        check(a.get('metric') == 'ip' and a.get('top_k') == 10 and a.get('fast_m') == 3, 'raw-IP/K10/Fast3 contract violated')
        check(a.get('num_queries') == 10000 and a.get('source_query_range') == [0, 10000], 'complete fixed pilot10K required; partial pilots are not silently pooled')
        check(a.get('search_Ls') == list(LS) and a.get('warmup_queries') == 128, 'fixed L64/128 and warmup128 required')
        check(a.get('rounds') == (1 if kind == 'count' else 5), 'wrong repetition count')
        check(a.get('schedule_prerecorded') is True and a.get('aligned_rows_round') == 0, 'missing preregistered schedule/aligned round0')
        timer = a['timer_contract']
        for key in ('gt_scoring_inside', 'workspace_allocation_inside', 'output_allocation_inside', 'trace_inside', 'hash_inside', 'json_inside'):
            check(timer.get(key) is False, f'invalid timer boundary: {key}')
        for key in ('routing_inside', 'search_and_reset_inside', 'result_writes_inside'):
            check(timer.get(key) is True, f'missing online timing: {key}')
        hnsw = a['hnsw']
        check([hnsw.get(x) for x in ('M', 'ef_construction', 'ef_search', 'seed')] == [16, 200, 10, 100], 'HNSW router contract drift')
        parts = resolve(a['parts_directory'])
        check(load_json(parts / 'complete.json').get('status') == 'COMPLETE', 'parts completion marker missing')
        check(resolve(a['model_file']) == model_path and a.get('model_manifest') == model, 'embedded/runtime model manifest mismatch')
    for key in ('threads', 'index_file', 'index_bytes', 'base_nodes', 'dim', 'normalization', 'artifact_version', 'fast_hubs', 'fast_ids', 'cache_condition'):
        check(count.get(key) == timing.get(key), f'count/timing metadata mismatch: {key}')
    check(model.get('status') == 'COMPLETE' and model.get('stage') == 'P2' and model.get('dataset') == dataset, 'invalid model provenance')
    for key, expected in {'fit_range': [10000, 30000], 'region_count': 64, 'active_regions': 4,
                          'portals_per_region': 2, 'temperature': 1.0, 'seed': SEED,
                          'cpu_only': True, 'heldout_accessed': False, 'pilot_labels_used_for_fit': False}.items():
        check(model.get(key) == expected, f'model contract drift: {key}')
    check(model.get('protocol_sha256') == protocol_hash, 'model built against a different protocol hash')
    check(model['dim'] == count['dim'], 'model/evaluator dimension mismatch')
    check(fast.get('status') == 'COMPLETE' and fast.get('dataset') == dataset, 'invalid Fast20K manifest')
    check(fast.get('fit_range') == [10000, 30000] and fast.get('fit_queries') == 20000 and fast.get('pilot_queries_used') == 0,
          'paired Fast must fit exactly the same20K and no pilot labels')
    check(fast.get('cpu_only') is True and fast.get('heldout_accessed') is False, 'invalid paired Fast CPU/split contract')
    for key in ('fit_query_values_sha256', 'fit_gt_values_sha256', 'input_audit_sha256'):
        check(model.get(key) and model.get(key) == fast.get(key), f'paired fit/input identity mismatch: {key}')
    for eval_key, manifest_key, hash_key in (('fast_hubs', 'hubs_file', 'hubs_sha256'), ('fast_ids', 'ids_file', 'ids_sha256')):
        p = resolve(fast[manifest_key])
        check(resolve(count[eval_key]) == p and sha(p) == fast[hash_key], f'paired Fast artifact identity mismatch: {eval_key}')
    small_files = {}
    for key, digest in (('labels_file', 'labels_sha256'), ('prototypes_file', 'profiles_sha256'), ('portals_file', 'portals_sha256')):
        p = resolve(model[key], model_path.parent)
        check(sha(p) == model[digest], f'model artifact checksum mismatch: {key}')
        small_files[key] = {'path': str(p), 'sha256': model[digest]}
    check(p1.get('stage') == 'P1' and p1.get('status') == 'PASS', 'upstream P1 PASS required')
    crows, trows = groups(count, 'count'), groups(timing, 'timing')
    expected_queries = list(range(10000))
    for l in LS:
        # Check the actual recorded AB/BA order, not only a boolean claim.
        schedule = [x for x in timing['schedule'] if int(x['L']) == l]
        original = [canon(x['method']) for x in schedule if x['round'] == 0]
        check(len(original) == len(METHODS) and set(original) == set(METHODS), 'round0 schedule has missing/duplicate methods')
        expected_schedule = [(r, name) for r in range(5) for name in (original if r % 2 == 0 else original[::-1])]
        check([(x['round'], canon(x['method'])) for x in schedule] == expected_schedule, 'recorded AB/BA schedule mismatch')
        for method in METHODS:
            c = crows[(l, method, 0)]
            aligned = c['per_query']
            check([x['query_id'] for x in aligned] == expected_queries, 'count query IDs must remain aligned0..9999')
            ch = fingerprint_rows(aligned)
            check(ch == (c['result_hash_fnv1a64'], c['route_hash_fnv1a64']), 'count stored hash does not reconstruct from rows')
            recalls = np.asarray([x['recall'] for x in aligned], dtype=np.float64)
            check(np.isfinite(recalls).all() and ((recalls >= 0) & (recalls <= 1)).all(), 'invalid recall range')
            check(np.allclose(recalls * 10, np.rint(recalls * 10), atol=1e-10), 'Recall@10 must be multiples of0.1')
            check(abs(float(recalls.mean()) - c['mean_recall']) < 1e-10, 'count aligned mean mismatch')
            check(c['qps'] is None and c['timing_publishable'] is False, 'count QPS must be unavailable')
            for field in ('routing_ndc', 'graph_ndc', 'total_ndc', 'routing_mac', 'graph_mac', 'total_mac'):
                values = np.asarray([x[field] for x in aligned], dtype=np.float64)
                check(np.isfinite(values).all() and (values >= 0).all(), f'invalid {field}')
                check(abs(float(values.mean()) - c['mean_' + field]) < 1e-7, f'aligned mean mismatch: {field}')
            for row in aligned:
                check(row['total_ndc'] == row['routing_ndc'] + row['graph_ndc'] and row['total_mac'] == row['routing_mac'] + row['graph_mac'], 'NDC/MAC sum mismatch')
                ids = row['entry_ids'] + ([row['shared_seed']] if row['shared_seed'] >= 0 else [])
                check(len(ids) == len(set(ids)) == row['actual_entry_count'], 'actual/unique entry count mismatch')
                check(row['fast_anchor_id'] in ids, 'paired Fast rank0 anchor missing from consumed seeds')
                check(len(row['result_ids']) == 10 and len([x for x in row['result_ids'] if x >= 0]) == len(set(x for x in row['result_ids'] if x >= 0)), 'duplicate/result length violation')
            for r in range(5):
                t = trows[(l, method, r)]
                check(t.get('repeated_routes_results_stable') is True, 'missing repeatability assertion')
                check(ch == (t['result_hash_fnv1a64'], t['route_hash_fnv1a64']), 'count/plain or5-round IDs/routes differ')
                check(abs(c['mean_recall'] - t['mean_recall']) < 1e-10, 'Recall changed between measurements/rounds')
                check(t['batch_wall_us'] > 0 and np.isfinite(t['qps']) and t['qps'] > 0, 'invalid wall/QPS')
                check(abs(10000e6 / t['batch_wall_us'] - t['qps']) < 1e-6, 'QPS was not derived from batch wall')
                oracle = method.startswith('oracle_')
                check(t['oracle'] == oracle and t['timing_publishable'] == (not oracle), 'oracle deployment flag wrong')
                if r == 0:
                    plain = t['per_query']
                    check([x['query_id'] for x in plain] == expected_queries and fingerprint_rows(plain) == ch, 'plain round0 rows/hash/query order mismatch')
                    check(all(a['result_ids'] == b['result_ids'] and a['recall'] == b['recall'] and route_signature(a) == route_signature(b) for a, b in zip(aligned, plain)), 'actual count/plain aligned rows mismatch')
                else:
                    check('per_query' not in t and t.get('aligned_reference_round') == 0, 'timing repeats must reference one aligned Recall sample')
        for names in (('geom_unified', 'geom_uniform', 'geom_probability'), ('oracle_unified', 'oracle_probability')):
            reference = crows[(l, names[0], 0)]['per_query']
            for method in names[1:]:
                check(all(route_signature(a) == route_signature(b) for a, b in zip(reference, crows[(l, method, 0)]['per_query'])), 'queue controls have different real routes')
    # L changes search capacity only. It must not alter the route itself.
    for method in METHODS:
        check(crows[(64, method, 0)]['route_hash_fnv1a64'] == crows[(128, method, 0)]['route_hash_fnv1a64'], 'routing changes with L')
    evidence = {kind: {'path': str(path), 'sha256': sha(path)} for kind, path in
                (('count', count_path), ('timing', timing_path), ('model', model_path), ('paired_fast20k', fast_path))}
    evidence['model_files'] = small_files
    evidence['graph_sha256_from_audited_model'] = model['graph_sha256']
    evidence['graph_rehashed_by_analysis'] = False
    return count, timing, model, fast, crows, trows, evidence


def bootstrap_deltas(deltas, rng, chunk):
    """One paired query sample per replicate, shared across every fixed contrast."""
    contrasts, nq = deltas.shape
    out = np.empty((contrasts, REPS), dtype=np.float64)
    for start in range(0, REPS, chunk):
        size = min(chunk, REPS - start)
        indices = rng.integers(0, nq, size=(size, nq), dtype=np.int32)
        for c in range(contrasts):
            out[c, start:start+size] = deltas[c, indices].mean(axis=1)
    return out


def qps_pair(trows, l, candidate, reference):
    pairs = []
    for r in range(5):
        a, b = trows[(l, candidate, r)], trows[(l, reference, r)]
        pairs.append({'round': r, 'candidate_qps': a['qps'], 'reference_qps': b['qps'],
                      'candidate_batch_wall_us': a['batch_wall_us'], 'reference_batch_wall_us': b['batch_wall_us'],
                      'qps_ratio': a['qps'] / b['qps']})
    ratios = np.asarray([x['qps_ratio'] for x in pairs])
    return {'pairs': pairs, 'mean_paired_ratio': float(ratios.mean()), 'median_paired_ratio': float(np.median(ratios)),
            'min_paired_ratio': float(ratios.min()), 'max_paired_ratio': float(ratios.max()),
            'candidate_faster_rounds': int((ratios > 1).sum()),
            'ratio_of_mean_qps': float(np.mean([x['candidate_qps'] for x in pairs]) / np.mean([x['reference_qps'] for x in pairs])),
            'ratio_CI': None, 'ratio_CI_reason': 'Five timing rounds are reported directly; no unsupported latency confidence claim'}


def evidence_sign(low, high):
    if low > 0:
        return 'POINTWISE_95_PERCENT_INTERVAL_POSITIVE'
    if high < 0:
        return 'POINTWISE_95_PERCENT_INTERVAL_NEGATIVE'
    if low == high == 0:
        return 'EXACT_ZERO_IN_OBSERVED_PAIRED_RECALL'
    return 'INTERVAL_INCLUDES_ZERO_NOT_AN_EQUIVALENCE_TEST'


def summarize(dataset, verified, out_dir, rng, chunk):
    count, timing, model, fast, crows, trows, evidence = verified
    rows, comparisons, boot_files = [], [], {}
    for l in LS:
        rec = {m: np.asarray([x['recall'] for x in crows[(l, m, 0)]['per_query']]) for m in METHODS}
        for method in METHODS:
            c = crows[(l, method, 0)]
            timings = [trows[(l, method, r)] for r in range(5)]
            qps = np.asarray([x['qps'] for x in timings])
            entries = np.asarray([x['actual_entry_count'] for x in c['per_query']])
            row = {'dataset': dataset, 'method': method, 'L': l, 'num_queries': 10000, 'recall': float(rec[method].mean()),
                   'qps_mean_of_five': float(qps.mean()), 'qps_median_of_five': float(np.median(qps)),
                   'qps_rounds': qps.tolist(), 'batch_wall_us_rounds': [x['batch_wall_us'] for x in timings],
                   'qps_pooled_queries_over_total_wall': 5 * 10000e6 / sum(x['batch_wall_us'] for x in timings),
                   'actual_entries_min': int(entries.min()), 'actual_entries_mean': float(entries.mean()), 'actual_entries_max': int(entries.max()),
                   'oracle_diagnostic_only': method.startswith('oracle_'), 'deployment_frontier_eligible': not method.startswith('oracle_'),
                   'result_hash': c['result_hash_fnv1a64'], 'route_hash': c['route_hash_fnv1a64']}
            for metric in ('routing_ndc', 'graph_ndc', 'total_ndc', 'routing_mac', 'graph_mac', 'total_mac'):
                row['mean_' + metric] = c['mean_' + metric]
            rows.append(row)
        deltas = np.stack([rec[a] - rec[b] for _, a, b, _ in CONTRASTS])
        draws = bootstrap_deltas(deltas, rng, chunk)
        for i, (name, candidate, reference, family) in enumerate(CONTRASTS):
            low, high = np.quantile(draws[i], [.025, .975]) * 100
            delta = float(deltas[i].mean()) * 100
            a, b = crows[(l, candidate, 0)], crows[(l, reference, 0)]
            record = {'dataset': dataset, 'L': l, 'contrast': name, 'family': family, 'candidate': candidate, 'reference': reference,
                      'recall_delta_pp': delta, 'paired_query_bootstrap95_pp': [float(low), float(high)],
                      'interval_scope': 'POINTWISE_EXPLORATORY_PILOT_UNADJUSTED', 'recall_evidence_sign': evidence_sign(low, high),
                      'query_improved': int((deltas[i] > 0).sum()), 'query_harmed': int((deltas[i] < 0).sum()), 'query_equal': int((deltas[i] == 0).sum()),
                      'qps_pairing': qps_pair(trows, l, candidate, reference),
                      'mean_graph_ndc_delta': a['mean_graph_ndc'] - b['mean_graph_ndc'],
                      'mean_total_ndc_delta': a['mean_total_ndc'] - b['mean_total_ndc'],
                      'oracle_involved': candidate.startswith('oracle_') or reference.startswith('oracle_'),
                      'matched_cost_or_recall_claim': False, 'p2_gate_automatically_passed': False}
            comparisons.append(record)
            boot_files[f'L{l}_{name}_recall_delta'] = draws[i]
    boot_path = out_dir / f'bootstrap_{dataset}.npz'
    with boot_path.open('xb') as f:
        np.savez_compressed(f, **boot_files)
    deployment = []
    real = [r for r in rows if not r['oracle_diagnostic_only']]
    for row in real:
        dominated = any(other['recall'] >= row['recall'] and other['qps_mean_of_five'] >= row['qps_mean_of_five'] and
                        (other['recall'] > row['recall'] or other['qps_mean_of_five'] > row['qps_mean_of_five']) for other in real)
        if not dominated:
            deployment.append({'method': row['method'], 'L': row['L'], 'recall': row['recall'], 'qps_mean_of_five': row['qps_mean_of_five']})
    return {'dataset': dataset, 'audit_status': 'PASS', 'evidence': evidence, 'measurements': rows, 'fixed_comparisons': comparisons,
            'bootstrap_draws': {'path': str(boot_path), 'sha256': sha(boot_path)},
            'observed_pilot_frontier': deployment,
            'frontier_interpretation': 'Descriptive measured pilot points only; no matched-cost bootstrap, no formal performance gate, no oracle points',
            'model_fit_diagnostics': model.get('fit_diagnostics'), 'model_region_sizes': model.get('region_sizes'),
            'cost': {'model': model.get('cost'), 'paired_fast20k': fast.get('offline_cost'),
                     'count_peak_rss_kib': count['peak_rss_kib'], 'timing_peak_rss_kib': timing['peak_rss_kib'],
                     'index_bytes': timing['index_bytes'], 'router_index_build_seconds': timing['hnsw']['build_seconds'],
                     'routing_only_plain': timing.get('routing_only'),
                     'partition': None, 'partition_reason': 'Read the checksum-bound model partition_report separately; this analysis does not invent missing offline timings'},
            'gate_assessment': {'status': 'REQUIRES_MECHANISM_REVIEW', 'automatic_GO': False,
                'candidate_protection_evidence': 'Read all three primary_queue contrasts at both fixed L values; signs concern same-L Recall only.',
                'structure_route_potential_evidence': 'Oracle selection and Fast bundle contrasts change selected portals/regions/seeds; they cannot by themselves isolate portal quality or graph connectivity.',
                'required_additional_evidence': ['Prespecified competition traces for mechanism interpretation', 'Localized prediction or portal bottleneck before oracle-only potential can justify a revision'],
                'P5_P6_P7_status': 'NOT_EVALUATED_BY_THIS_SCRIPT'}}


def csv_new(path, rows):
    with path.open('x', newline='') as f:
        keys = list(rows[0]) if rows else []
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def markdown(report):
    lines = ['# P2 fixed pilot evidence', '',
             'These are historically used development pilot results at fixed L=64/128. Ordinary 95% paired-query intervals are exploratory and unadjusted. Five timing rounds measure timing variation and are not five Recall samples. This report does not automatically pass P2, evaluate the P5/P6/P7 substantial-performance thresholds, or claim matched-Recall/QPS improvement.', '']
    for ds in report['datasets']:
        lines += [f"## {ds['dataset']}", '', 'Count/plain, full route equality, five-round identity, schedule and paired20K provenance checks: PASS.', '',
                  '| Method | L | Recall@10 | Mean QPS | Median QPS | Route / graph / total NDC | Route MAC | Mean actual entries | Scope |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---|']
        for r in ds['measurements']:
            lines.append(f"| {r['method']} | {r['L']} | {r['recall']:.6f} | {r['qps_mean_of_five']:.2f} | {r['qps_median_of_five']:.2f} | {r['mean_routing_ndc']:.2f} / {r['mean_graph_ndc']:.2f} / {r['mean_total_ndc']:.2f} | {r['mean_routing_mac']:.1f} | {r['actual_entries_mean']:.3f} | {'oracle diagnostic' if r['oracle_diagnostic_only'] else 'pilot deployment measurement'} |")
        lines += ['', '| Fixed contrast (candidate minus reference) | L | Recall delta pp | Pointwise bootstrap95% pp | Mean paired QPS ratio | Raw ratios, rounds0..4 |',
                  '|---|---:|---:|---|---:|---|']
        for r in ds['fixed_comparisons']:
            ci, q = r['paired_query_bootstrap95_pp'], r['qps_pairing']
            ratios = ', '.join(f"{x['qps_ratio']:.4f}" for x in q['pairs'])
            lines.append(f"| {r['contrast']} | {r['L']} | {r['recall_delta_pp']:+.4f} | [{ci[0]:+.4f}, {ci[1]:+.4f}] | {q['mean_paired_ratio']:.4f} | {ratios} |")
        lines += ['', 'The first three contrasts hold the real route fixed and test queue changes. Oracle selection contrasts diagnose a region-selection plus selected-portal gap. Fast bundle contrasts also change entry count and shared-default seeding. A positive oracle selection gap does not prove that candidate protection is effective, and a same-L Recall/QPS tradeoff is not a matched-cost improvement.', '',
                  'Gate: **REQUIRES_MECHANISM_REVIEW**. Inspect the predefined competition traces and both L values on both datasets. Intervals crossing zero are inconclusive for direction, not proof of equivalence. Do not choose a favorable point and reuse its interval as a selected-best guarantee.', '',
                  'Input evidence: ' + ', '.join(f"[{k}]({ds['evidence'][k]['path']})" for k in ('count', 'timing', 'model', 'paired_fast20k')) + '.', '']
    lines += ['## Evidence limits and next decision', '',
              'No validation or heldout query/GT data were read. Region labels, model profiles/portals, and paired Fast files were checked by checksum. The frozen graph checksum is inherited from the audited model; this small analysis does not rescan the multi-gigabyte graph. The full query/GT-independent evaluator contract and upstream P0/P1 checks remain part of the evidence chain.', '',
              'The next decision belongs to the P2 gate review: separate fixed-route protection evidence from oracle/portal potential, inspect causal competition traces, then follow the preregistered failure action. P3/P4 learning cannot be authorized by this script. P5/P6/P7 require their original matched-point selection-inside-bootstrap, corrected intervals, two adjacent anchors and independent-build/frozen-test evidence.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', action='append', nargs=5, metavar=('DATASET', 'COUNT', 'TIMING', 'MODEL', 'FAST20K'), required=True)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--p1-gate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bootstrap-chunk', type=int, default=64)
    args = parser.parse_args()
    check(not args.output.exists(), 'output directory already exists; refusing overwrite')
    check(1 <= args.bootstrap_chunk <= 256, 'bootstrap chunk must be1..256')
    supplied = {x[0]: x[1:] for x in args.input}
    check(len(args.input) == len(supplied) == 2 and set(supplied) == set(DATASETS), 'exactly the two preregistered datasets are required')
    protocol, p1 = load_json(args.protocol), load_json(args.p1_gate)
    check(protocol['p2_preregistered']['search_Ls'] == list(LS) and protocol['p2_preregistered']['model_seed'] == SEED, 'protocol fixed-L/seed mismatch')
    check(protocol['data_contract']['fit']['row_range'] == [10000, 30000] and protocol['measurement']['pilot_validation_rounds'] == 5, 'protocol fit/timing mismatch')
    args.output.mkdir(parents=True, exist_ok=False)
    invocation = {'status': 'INCOMPLETE', 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv,
                  'script_sha256': sha(__file__), 'protocol': {'path': str(args.protocol.resolve()), 'sha256': sha(args.protocol)},
                  'p1_gate': {'path': str(args.p1_gate.resolve()), 'sha256': sha(args.p1_gate)},
                  'bootstrap_repetitions': REPS, 'seed': SEED, 'bootstrap_chunk': args.bootstrap_chunk,
                  'unit_of_resampling': 'paired pilot query IDs; same draws for all fixed contrasts within each dataset/L',
                  'comparison_selection': 'All7 fixed contrasts at L64/128 on both datasets; no winning-point selection',
                  'reads_query_GT_base_or_graph_vectors': False, 'heldout_or_validation_accessed': False}
    write_new(args.output / 'invocation.json', invocation)
    report = {'schema_version': 1, 'status': 'INCOMPLETE', 'scope': 'P2_PILOT_EXPLORATORY', 'stage_gate': 'REQUIRES_MECHANISM_REVIEW',
              'formal_performance_improvement_confirmed': False, 'bootstrap': {k: invocation[k] for k in ('bootstrap_repetitions', 'seed', 'bootstrap_chunk', 'unit_of_resampling', 'comparison_selection')},
              'datasets': []}
    rng = np.random.default_rng(SEED)
    try:
        for dataset in DATASETS:
            verified = verify_input(dataset, supplied[dataset], invocation['protocol']['sha256'], p1)
            summary = summarize(dataset, verified, args.output, rng, args.bootstrap_chunk)
            write_new(args.output / f'{dataset}.json', summary)
            report['datasets'].append(summary)
            del verified
            print(json.dumps({'dataset': dataset, 'audit': 'PASS', 'analysis': 'COMPLETE', 'gate': 'REQUIRES_MECHANISM_REVIEW'}), flush=True)
        report['status'] = 'COMPLETE'
        write_new(args.output / 'analysis.json', report)
        csv_new(args.output / 'measurements.csv', [r for d in report['datasets'] for r in d['measurements']])
        csv_new(args.output / 'comparisons.csv', [r for d in report['datasets'] for r in d['fixed_comparisons']])
        with (args.output / 'report.md').open('x') as f:
            f.write(markdown(report))
        write_new(args.output / 'complete.json', {'status': 'COMPLETE', 'stage_gate': 'REQUIRES_MECHANISM_REVIEW',
                  'analysis_sha256': sha(args.output/'analysis.json'), 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat()})
    except Exception as error:
        write_new(args.output / 'failure.json', {'status': 'INCOMPLETE', 'error': str(error), 'completed_datasets': [d['dataset'] for d in report['datasets']],
                  'interpretation': 'Input/integrity/analysis failure, not an algorithm NO_GO'})
        raise


if __name__ == '__main__':
    main()
