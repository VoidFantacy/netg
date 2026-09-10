#!/usr/bin/env python3
"""Audit the complete preregistered P3 2x2 pilot and all eight fixed comparisons.

Read existing measurements and small model artifacts only. No ANN, query/GT/base/
graph-vector input, fitting, model selection, frontier, or automatic stage gate.
"""
from __future__ import annotations

import argparse
import copy
import csv
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path('/data/netg/ACSG')
RUN = Path(__file__).resolve().parents[1]
P2_HELPER = RUN / 'p2/analyze_p2.py'
P2_HELPER_SHA = '8219fc24ac771d585cc30f9ad628aa7d5c8e55025bfe60725511aafafb05acd8'
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
MODELS = ('lambda0_frequency3', 'lambda1_frequency3', 'lambda0_greedy3', 'lambda1_greedy3')
METHODS = ('fast', 'oracle_unified', 'oracle_probability')
LS = (64, 128)
REPS, SEED, NQ = 10000, 2026090711, 10000
METRICS = ('routing_ndc', 'graph_ndc', 'total_ndc', 'routing_mac', 'graph_mac', 'total_mac')
# Name, candidate model/method, reference model/method, inference family.
CONTRASTS = (
    ('structure_under_frequency3', 'lambda1_frequency3', 'oracle_probability', 'lambda0_frequency3', 'oracle_probability', 'cross_model_2x2'),
    ('structure_under_greedy3', 'lambda1_greedy3', 'oracle_probability', 'lambda0_greedy3', 'oracle_probability', 'cross_model_2x2'),
    ('portals_under_lambda0', 'lambda0_greedy3', 'oracle_probability', 'lambda0_frequency3', 'oracle_probability', 'cross_model_2x2'),
    ('portals_under_lambda1', 'lambda1_greedy3', 'oracle_probability', 'lambda1_frequency3', 'oracle_probability', 'cross_model_2x2'),
) + tuple(('protection_' + name, name, 'oracle_probability', name, 'oracle_unified', 'within_model_queue') for name in MODELS)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def bound(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def resolve(path, parent=ROOT):
    path = Path(path)
    return (path if path.is_absolute() else Path(parent) / path).resolve()


def bound_path(desc, parent=ROOT, expected_bytes=None):
    path = resolve(desc['path'], parent)
    require(sha(path) == desc['sha256'], 'SHA256 mismatch: ' + str(path))
    if expected_bytes is not None:
        require(path.stat().st_size == expected_bytes, 'Artifact byte shape mismatch: ' + str(path))
    return path


def bound_json(desc, parent=ROOT):
    return read(bound_path(desc, parent))


def write_json(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, indent=2, allow_nan=False)
        f.write('\n')


def import_p2():
    require(sha(P2_HELPER) == P2_HELPER_SHA, 'Audited P2 helper changed; refusing silent helper drift')
    spec = importlib.util.spec_from_file_location('frozen_p2_analysis_helpers', P2_HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.REPS == REPS, 'Bootstrap helper repetition count differs')
    return module


def cell_groups(artifact, kind):
    result = {}
    for row in artifact['results']:
        key = (row['search_L'], row['method'], row['round'])
        require(key not in result, 'Duplicate evaluator result cell')
        result[key] = row
    expected = {(l, method, r) for l in LS for method in METHODS for r in range(1 if kind == 'count' else 5)}
    require(set(result) == expected, 'Missing/extra methods, L values, or rounds: ' + kind)
    return result


def check_schedule(artifact, kind):
    rounds = 1 if kind == 'count' else 5
    expected = [(l, r, method, METHODS.index(method), 'BA' if r % 2 else 'AB')
                for l in LS for r in range(rounds)
                for method in (METHODS[::-1] if r % 2 else METHODS)]
    got = [(x['L'], x['round'], x['method'], x['method_index'], x['order']) for x in artifact['schedule']]
    require(got == expected, 'Recorded forward/reverse schedule differs from fixed order')


def check_route(row, method, portals, n, default_seed):
    ids = row['entry_ids']
    require(all(type(x) is int and 0 <= x < n for x in ids), 'Entry ID outside base')
    seed = row['shared_seed']
    entries = ids + ([seed] if seed >= 0 else [])
    require(len(entries) == len(set(entries)) == row['actual_entry_count'], 'Actual seed count/deduplication mismatch')
    require(row['fast_anchor_id'] in entries, 'Fast rank0 anchor absent from actual route')
    if method == 'fast':
        require(seed == -1 and len(ids) == 3 and row['actual_entry_count'] == 3 and
                row['regions'] == [] and row['weights'] == [] and row['fast_anchor_id'] == ids[0], 'Fast m3 route changed')
    else:
        regions, weights = row['regions'], row['weights']
        require(seed == default_seed and len(regions) == len(weights) == 4 and len(set(regions)) == 4 and
                all(type(r) is int and 0 <= r < 256 for r in regions), 'Invalid oracle leaf/default route')
        require(all(np.isfinite(w) and w >= 0 for w in weights) and abs(sum(weights) - 1) < 1e-12,
                'Invalid normalized oracle weights')
        require(list(zip(regions, weights)) == sorted(zip(regions, weights), key=lambda x: (-x[1], x[0])),
                'Oracle mass/leaf-ID order drift')
        submitted = [row['fast_anchor_id']] + [int(node) for r in regions for node in portals[r]]
        consumed = []
        for node in submitted:
            if node != seed and node not in consumed:
                consumed.append(node)
        require(ids == consumed and row['actual_entry_count'] <= 14, 'Not all twelve portals/anchor/default were actually consumed')
    returned = row['result_ids']
    require(len(returned) == 10 and all(type(x) is int and -1 <= x < n for x in returned), 'Invalid result IDs')
    valid = [x for x in returned if x >= 0]
    require(len(valid) == len(set(valid)) and returned == valid + [-1] * (10 - len(valid)), 'Duplicate results or nonterminal padding')
    require(row['recall'] <= len(valid) / 10 + 1e-12, 'Recall exceeds number of returned IDs')


def verify_batches(count, timing, portals, n, dim, default_seed, p2, nq=NQ):
    """Pure artifact integrity logic; nq override is used only by tiny self-tests."""
    check_schedule(count, 'count')
    check_schedule(timing, 'timing')
    crows, trows = cell_groups(count, 'count'), cell_groups(timing, 'timing')
    expected_queries = list(range(nq))
    for l in LS:
        for method in METHODS:
            c = crows[(l, method, 0)]
            aligned = c['per_query']
            require([row['query_id'] for row in aligned] == expected_queries, 'Count rows must align every pilot ID in order')
            identity = p2.fingerprint_rows(aligned)
            require(identity == (c['result_hash_fnv1a64'], c['route_hash_fnv1a64']), 'Count hash does not reconstruct')
            recall = np.asarray([row['recall'] for row in aligned], dtype=np.float64)
            require(np.isfinite(recall).all() and ((recall >= 0) & (recall <= 1)).all() and
                    np.allclose(recall * 10, np.rint(recall * 10), rtol=0, atol=1e-10), 'Invalid Recall@10 values')
            require(abs(float(recall.mean()) - c['mean_recall']) < 1e-10, 'Count aligned Recall mean mismatch')
            require(c['qps'] is None and c['batch_wall_us'] is None and c['timing_publishable'] is False and
                    c['oracle'] == (method != 'fast') and c['top_k'] == 10 and c['repeated_routes_results_stable'] is True,
                    'Count result measurement/oracle flags invalid')
            for field in METRICS:
                values = np.asarray([row[field] for row in aligned], dtype=np.float64)
                require(np.isfinite(values).all() and (values >= 0).all() and np.equal(values, np.floor(values)).all(), 'Invalid count metric: ' + field)
                require(abs(float(values.mean()) - c['mean_' + field]) < 1e-7, 'Aligned count mean mismatch: ' + field)
            for field, mean_field in (('routing_us_instrumented', 'mean_routing_us_instrumented'),
                                      ('graph_us_instrumented', 'mean_graph_us_instrumented')):
                values = np.asarray([row[field] for row in aligned], dtype=np.float64)
                require(np.isfinite(values).all() and (values >= 0).all() and abs(float(values.mean()) - c[mean_field]) < 1e-7,
                        'Instrumented explanatory time mismatch')
            for row in aligned:
                require(row['total_ndc'] == row['routing_ndc'] + row['graph_ndc'] and
                        row['total_mac'] == row['routing_mac'] + row['graph_mac'] and
                        row['graph_mac'] == row['graph_ndc'] * dim and row['routing_mac'] == row['routing_ndc'] * dim,
                        'Raw-IP NDC/MAC accounting mismatch')
                for field in ('expanded', 'rejected', 'evicted_unexpanded'):
                    require(type(row[field]) is int and row[field] >= 0, 'Invalid search counter')
                check_route(row, method, portals, n, default_seed)
            entries = [row['actual_entry_count'] for row in aligned]
            require(c['min_actual_entry_count'] == min(entries) and c['max_actual_entry_count'] == max(entries), 'Count actual-entry range mismatch')
            for round_id in range(5):
                t = trows[(l, method, round_id)]
                require(identity == (t['result_hash_fnv1a64'], t['route_hash_fnv1a64']) and
                        t['repeated_routes_results_stable'] is True, 'Count/plain or timing-round identities changed')
                require(abs(c['mean_recall'] - t['mean_recall']) < 1e-10, 'Recall changed across measurement rounds')
                require(t['top_k'] == 10 and t['oracle'] == (method != 'fast') and t['timing_publishable'] == (method == 'fast'), 'Timing result flags invalid')
                require(np.isfinite(t['qps']) and t['qps'] > 0 and np.isfinite(t['batch_wall_us']) and t['batch_wall_us'] > 0 and
                        abs(nq * 1e6 / t['batch_wall_us'] - t['qps']) < 1e-6, 'QPS/batch wall mismatch')
                require(all(t['mean_' + field] is None for field in METRICS), 'Timing output contains instrumented count means')
                require(t['min_actual_entry_count'] == min(entries) and t['max_actual_entry_count'] == max(entries), 'Timing actual-entry range mismatch')
                if round_id == 0:
                    plain = t['per_query']
                    require([row['query_id'] for row in plain] == expected_queries and p2.fingerprint_rows(plain) == identity, 'Plain round0 rows/hash mismatch')
                    require(all(a['result_ids'] == b['result_ids'] and a['recall'] == b['recall'] and
                                p2.route_signature(a) == p2.route_signature(b) for a, b in zip(aligned, plain)), 'Full count/plain aligned rows differ')
                    require(all('graph_ndc' not in row and 'routing_ndc' not in row for row in plain), 'Count instrumentation in plain aligned rows')
                else:
                    require('per_query' not in t and t['aligned_reference_round'] == 0, 'Repeated timing rows must reference one Recall sample')
        unified = crows[(l, 'oracle_unified', 0)]['per_query']
        protected = crows[(l, 'oracle_probability', 0)]['per_query']
        fast = crows[(l, 'fast', 0)]['per_query']
        require(all(p2.route_signature(a) == p2.route_signature(b) for a, b in zip(unified, protected)), 'Within-model oracle queue comparison changes route')
        require(all(a['fast_anchor_id'] == b['fast_anchor_id'] for a, b in zip(unified, fast)), 'Oracle route uses a different Fast rank0 anchor')
    for method in METHODS:
        require(all(p2.route_signature(a) == p2.route_signature(b) for a, b in
                    zip(crows[(64, method, 0)]['per_query'], crows[(128, method, 0)]['per_query'])), 'Changing L changed actual routing')
    return crows, trows


def validate_eval_metadata(artifact, kind, dataset, model, model_path, execution, audit_ds, fast, p1):
    expected = {'schema_version': 1, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset, 'split': 'pilot',
                'source_query_type': 'drl_train', 'source_query_range': [0, NQ], 'num_queries': NQ,
                'measurement': kind, 'threads': 16, 'cpu_only': True, 'metric': 'ip', 'top_k': 10, 'fast_m': 3,
                'search_Ls': list(LS), 'rounds': 1 if kind == 'count' else 5, 'warmup_queries': 128,
                'heldout_accessed': False, 'oracle_is_deployment': False, 'schedule_prerecorded': True,
                'aligned_rows_round': 0, 'trace_mode': False, 'region_count': 256, 'portals_per_region': 3}
    for key, value in expected.items():
        require(artifact.get(key) == value, 'Evaluator metadata mismatch: ' + kind + '/' + key)
    require(artifact['model_manifest'] == model and resolve(artifact['model_file']) == model_path and
            artifact['model_sha256'] == execution['models'][model['model_name']]['sha256'], 'Embedded/runtime model mismatch')
    for key, expected_value in (('dim', audit_ds['graph']['header']['d']), ('base_nodes', audit_ds['graph']['header']['n']),
                                ('index_bytes', audit_ds['graph']['header']['bytes'])):
        require(artifact[key] == expected_value, 'Frozen index shape mismatch: ' + key)
    require(resolve(artifact['index_file']) == resolve(audit_ds['graph']['path']), 'Evaluator used another graph path')
    for field, value in (('fast_hubs', fast['hubs_file']), ('fast_ids', fast['ids_file'])):
        require(resolve(artifact[field]) == resolve(value), 'Evaluator Fast artifact path mismatch')
    provenance = artifact['evaluator_provenance']
    require(provenance['source_sha256'] == p1['evaluator_source_sha256'] == execution['source']['sha256'] and
            provenance['binary_sha256'] == p1['evaluator_binary_sha256'] == execution['binary']['sha256'], 'Evaluator is not the accepted source/binary')
    require(resolve(provenance['source_path']) == resolve(execution['source']['path']) and
            resolve(provenance['binary_path']) == resolve(execution['binary']['path']), 'Evaluator source/binary path differs from execution')
    timer = artifact['timer_contract']
    for key in ('gt_scoring_inside', 'workspace_allocation_inside', 'output_allocation_inside', 'trace_inside', 'hash_inside', 'json_inside'):
        require(timer[key] is False, 'Forbidden operation inside pure wall timer: ' + key)
    for key in ('routing_inside', 'search_and_reset_inside', 'result_writes_inside', 'hnsw_internal_allocations_inside'):
        require(timer[key] is True, 'Required online operation missing from timer: ' + key)
    require(timer['fast_and_oracle_hnsw_query'] == 'unchanged raw query', 'Raw query metric boundary changed')
    require([artifact['hnsw'][k] for k in ('M', 'ef_construction', 'ef_search', 'seed')] == [16, 200, 10, 100], 'Paired Fast HNSW changed')
    parts = resolve(artifact['parts_directory'])
    marker = read(parts / 'complete.json')
    require(marker['status'] == 'COMPLETE' and marker['completed_batches'] == (6 if kind == 'count' else 30), 'Missing/incomplete evaluator parts marker')
    if kind == 'timing':
        routing = artifact['routing_only']
        require([row['method'] for row in routing] == list(METHODS), 'Routing-only method coverage mismatch')
        require(all(row['num_queries'] == NQ and np.isfinite(row['batch_wall_us']) and row['batch_wall_us'] > 0 for row in routing), 'Invalid routing-only plain wall')


def check_invocations(execution, directory):
    invocations = execution['invocations']
    expected = [(name, kind) for name in MODELS for kind in ('count', 'timing')]
    require([(x['model'], x['measurement']) for x in invocations] == expected, 'Execution model/measurement order changed')
    outputs = {}
    for invocation in invocations:
        name, kind = invocation['model'], invocation['measurement']
        require(invocation['status'] == 'COMPLETE' and invocation['returncode'] == 0, 'Failed or interrupted measurement')
        path = bound_path(invocation['output'], directory)
        require(path == (directory / name / (kind + '.json')).resolve(), 'Unexpected measurement output path')
        command = invocation['command']
        require(resolve(command[0]) == resolve(execution['binary']['path']) and len(command[1:]) % 2 == 0, 'Unexpected evaluator command')
        keys, values = command[1::2], command[2::2]
        require(len(set(keys)) == len(keys), 'Repeated evaluator command flag')
        flags = dict(zip(keys, values))
        expected_flags = {'--stage': 'P3', '--split': 'pilot', '--measurement': kind, '--rounds': '1' if kind == 'count' else '5',
                          '--dataset': execution['dataset'], '--fast-m': '3', '--search-ls': '64,128', '--top-k': '10',
                          '--query-offset': '0', '--hnsw-seed': '100', '--methods': ','.join(METHODS),
                          '--max-queries': '10000', '--threads': '16', '--warmup-queries': '128'}
        for key, value in expected_flags.items():
            require(flags.get(key) == value, 'Recorded evaluator invocation changed: ' + key)
        require(set(flags) == set(expected_flags) | {'--index-file', '--model', '--fast-hubs', '--fast-ids', '--output'},
                'Unexpected evaluator command options')
        require(resolve(flags['--model']) == resolve(execution['models'][name]['path']) and resolve(flags['--output']) == path,
                'Invocation model/output path differs from binding')
        for key, kind in (('--fast-hubs', 'hubs'), ('--fast-ids', 'ids')):
            require(resolve(flags[key]) == resolve(execution['fast_inputs'][kind]['path']), 'Command did not use frozen Fast raw file')
        outputs[(name, kind)] = path
    return outputs


def verify_dataset(dataset, directory, protocol_binding, p1_binding, p1, p2):
    directory = Path(directory).resolve()
    execution_path = directory / 'execution.json'
    execution = read(execution_path)
    require(execution['status'] == 'COMPLETE_DATASET_MEASUREMENTS' and execution['stage'] == 'P3' and
            execution['dataset'] == dataset and execution['cpu_only'] is True and execution['heldout_accessed'] is False and
            execution['validation_accessed'] is False, 'Incomplete/invalid dataset execution')
    require(execution['protocol'] == protocol_binding and execution['p1_gate'] == p1_binding and
            execution['model_order'] == list(MODELS) and execution['method_order'] == list(METHODS), 'Execution protocol/gate/family mismatch')
    require(set(execution['models']) == set(MODELS), 'Exactly four preregistered models required')
    for key in ('source', 'binary', 'runner'):
        bound_path(execution[key], directory)
    require(execution['source']['sha256'] == p1['evaluator_source_sha256'] and execution['binary']['sha256'] == p1['evaluator_binary_sha256'], 'Execution bypassed accepted evaluator')
    audit = bound_json(execution['audit'], directory)
    require(audit['status'] == 'PASS_INPUT_CONTRACT' and audit['heldout_accessed'] is False, 'P0 input contract required')
    matches = [row for row in audit['datasets'] if row['dataset'] == dataset]
    require(len(matches) == 1, 'Missing/duplicate audited dataset')
    ds = matches[0]
    fast_path = bound_path(execution['fast_manifest'], directory)
    fast = read(fast_path)
    require(execution['fast_inputs']['manifest'] == execution['fast_manifest'], 'Frozen Fast manifest binding differs from execution')
    for key, value in {'status': 'COMPLETE', 'dataset': dataset, 'fit_range': [10000, 30000], 'fit_queries': 20000,
                       'pilot_queries_used': 0, 'cpu_only': True, 'heldout_accessed': False,
                       'fit_query_values_sha256': ds['fit']['query_values_sha256'],
                       'fit_gt_values_sha256': ds['fit']['gt_values_sha256'], 'input_audit_sha256': execution['audit']['sha256']}.items():
        require(fast.get(key) == value, 'Fast20K provenance mismatch: ' + key)
    fast_files = {}
    for file_key, hash_key in (('hubs_file', 'hubs_sha256'), ('ids_file', 'ids_sha256')):
        path = resolve(fast[file_key], fast_path.parent); require(sha(path) == fast[hash_key], 'Fast20K small artifact changed')
        kind = file_key.split('_', 1)[0]
        require(execution['fast_inputs'][kind] == bound(path), 'Frozen Fast raw binding differs from paired manifest')
        fast_files[file_key] = bound(path)
        fast[file_key] = str(path)  # Normalize manifest-relative paths for metadata checks below.
    outputs = check_invocations(execution, directory)
    models, records, evidence, partitions = {}, {}, {}, {}
    for name in MODELS:
        model_path = bound_path(execution['models'][name], directory)
        model = read(model_path)
        branch, rule = name.split('_', 1)
        expected = {'schema_version': 2, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset,
                    'model_name': name, 'lambda': int(branch[-1]), 'portal_rule': rule, 'oracle_diagnostic_only': True,
                    'region_count': 256, 'coarse_count': 16, 'leaves_per_coarse': 16, 'parent_rule': 'leaf_id // 16',
                    'active_regions': 4, 'portals_per_region': 3, 'total_portals': 768, 'fit_range': [10000, 30000], 'fit_count': 20000,
                    'cpu_only': True, 'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
                    'dim': ds['graph']['header']['d'], 'base_nodes': ds['graph']['header']['n'],
                    'protocol_sha256': protocol_binding['sha256'], 'input_audit_sha256': execution['audit']['sha256'],
                    'graph_sha256': ds['graph']['sha256'], 'fit_query_values_sha256': fast['fit_query_values_sha256'],
                    'fit_gt_values_sha256': fast['fit_gt_values_sha256']}
        for key, value in expected.items():
            require(model.get(key) == value, 'Model contract mismatch: ' + name + '/' + key)
        require('prototypes_file' not in model, 'P3 oracle-only model unexpectedly includes query profiles')
        require(model['protocol'] == protocol_binding and model['audit'] == execution['audit'], 'Model explicit provenance differs')
        partition = bound_json(model['partition_manifest'], model_path.parent)
        require(partition['status'] == 'COMPLETE' and partition['stage'] == 'P3' and partition['dataset'] == dataset and
                partition['lambda'] == model['lambda'] and partition['protocol_sha256'] == protocol_binding['sha256'] and
                partition['labels_sha256'] == model['labels_sha256'], 'Model partition identity mismatch')
        labels = resolve(model['labels_file'], model_path.parent)
        portals_path = resolve(model['portals_file'], model_path.parent)
        require(labels.stat().st_size == 2 * model['base_nodes'] and sha(labels) == model['labels_sha256'], 'Model labels changed')
        require(portals_path.stat().st_size == 768 * 4 and sha(portals_path) == model['portals_sha256'], 'Model portals changed')
        portals = np.fromfile(portals_path, dtype='<i4').reshape(256, 3)
        require(int(portals.min()) >= 0 and int(portals.max()) < model['base_nodes'] and all(len(set(row)) == 3 for row in portals), 'Invalid fixed-count portal IDs')
        # These bound JSON records contain checksums and metadata, not query/GT values.
        probe = bound_json(model['probe_complete'], model_path.parent)
        require(probe['status'] == 'COMPLETE' and probe['complete_leaves'] == 256 and
                probe['dataset'] == dataset and probe['structure_lambda'] == model['lambda'] and
                probe['partition_manifest'] == model['partition_manifest'], 'Model lacks completed matching portal probes')
        count, timing = read(outputs[(name, 'count')]), read(outputs[(name, 'timing')])
        for artifact, kind in ((count, 'count'), (timing, 'timing')):
            validate_eval_metadata(artifact, kind, dataset, model, model_path, execution, ds, fast, p1)
        for key in ('threads', 'index_file', 'index_bytes', 'base_nodes', 'dim', 'normalization', 'artifact_version',
                    'fast_hubs', 'fast_ids', 'cache_condition'):
            require(count[key] == timing[key], 'Count/timing metadata differ: ' + key)
        crows, trows = verify_batches(count, timing, portals, model['base_nodes'], model['dim'], ds['graph']['header']['enterpoint'], p2)
        models[name], partitions[name] = model, partition
        records[name] = {'count': count, 'timing': timing, 'crows': crows, 'trows': trows, 'probe': probe}
        evidence[name] = {'model': execution['models'][name], 'count': bound(outputs[(name, 'count')]), 'timing': bound(outputs[(name, 'timing')]),
                          'labels': bound(labels), 'portals': bound(portals_path), 'partition_manifest': model['partition_manifest'], 'probe_complete': model['probe_complete']}
    for branch in ('lambda0', 'lambda1'):
        a, b = branch + '_frequency3', branch + '_greedy3'
        require(models[a]['labels_sha256'] == models[b]['labels_sha256'] and
                models[a]['partition_manifest'] == models[b]['partition_manifest'], 'Portal contrast changed structure')
        for l in LS:
            ra, rb = records[a]['crows'][(l, 'oracle_probability', 0)]['per_query'], records[b]['crows'][(l, 'oracle_probability', 0)]['per_query']
            require(all(x['regions'] == y['regions'] and x['weights'] == y['weights'] for x, y in zip(ra, rb)), 'Same-label portal contrast changed oracle leaf selection')
    initial = {name: part.get('initial_labels_sha256') for name, part in partitions.items()}
    if any(value is not None for value in initial.values()):
        require(all(isinstance(value, str) and len(value) == 64 for value in initial.values()) and len(set(initial.values())) == 1,
                'Branches do not share the same complete initial labels')
    baseline = records[MODELS[0]]
    for name in MODELS[1:]:
        for l in LS:
            a, b = baseline['crows'][(l, 'fast', 0)]['per_query'], records[name]['crows'][(l, 'fast', 0)]['per_query']
            require(all(x['result_ids'] == y['result_ids'] and x['recall'] == y['recall'] and p2.route_signature(x) == p2.route_signature(y) and
                        all(x[field] == y[field] for field in METRICS) for x, y in zip(a, b)), 'Fast results/routes/NDC vary across model cells')
    return records, {'execution': bound(execution_path), 'protocol': protocol_binding, 'p1_gate': p1_binding,
                      'audit': execution['audit'], 'fast_manifest': execution['fast_manifest'], 'fast_files': fast_files,
                      'models': evidence, 'common_initial_labels_sha256': next(iter(initial.values())),
                      'graph_sha256_inherited_from_P0': ds['graph']['sha256'], 'graph_rehashed': False}


def measurements(dataset, records):
    result = []
    for name in MODELS:
        record = records[name]
        routing = {row['method']: row for row in record['timing']['routing_only']}
        for l in LS:
            for method in METHODS:
                c = record['crows'][(l, method, 0)]
                times = [record['trows'][(l, method, r)] for r in range(5)]
                qps = np.asarray([row['qps'] for row in times])
                entries = np.asarray([row['actual_entry_count'] for row in c['per_query']])
                row = {'dataset': dataset, 'model': name, 'method': method, 'L': l, 'num_queries': NQ,
                       'recall': c['mean_recall'], 'qps_mean_of_five': float(qps.mean()), 'qps_median_of_five': float(np.median(qps)),
                       'qps_rounds': qps.tolist(), 'batch_wall_us_rounds': [x['batch_wall_us'] for x in times],
                       'qps_pooled_queries_over_total_wall': 5 * NQ * 1e6 / sum(x['batch_wall_us'] for x in times),
                       'actual_entries_min': int(entries.min()), 'actual_entries_mean': float(entries.mean()), 'actual_entries_max': int(entries.max()),
                       'routing_only_plain_batch_wall_us': routing[method]['batch_wall_us'], 'routing_only_plain_queries': NQ,
                       'routing_only_scope': 'One separate warmed routing-only batch per model/method, shared descriptive value across L; not five rounds or per-query latency',
                       'mean_routing_us_instrumented': c['mean_routing_us_instrumented'], 'mean_graph_us_instrumented': c['mean_graph_us_instrumented'],
                       'oracle_diagnostic_only': method != 'fast', 'online_improvement_claim': False,
                       'result_hash': c['result_hash_fnv1a64'], 'route_hash': c['route_hash_fnv1a64']}
                row.update({'mean_' + field: c['mean_' + field] for field in METRICS})
                for field in ('expanded', 'rejected', 'evicted_unexpanded'):
                    row['mean_' + field] = float(np.mean([x[field] for x in c['per_query']]))
                result.append(row)
    return result


def qps_comparison(records, l, candidate_model, candidate_method, reference_model, reference_method, p2):
    if candidate_model == reference_model:
        result = p2.qps_pair(records[candidate_model]['trows'], l, candidate_method, reference_method)
        result['scope'] = 'Within-model forward/reverse paired timing rounds; oracle diagnostic only'
        result['cross_model_paired_inference_allowed'] = False
        return result
    candidate = [records[candidate_model]['trows'][(l, candidate_method, r)]['qps'] for r in range(5)]
    reference = [records[reference_model]['trows'][(l, reference_method, r)]['qps'] for r in range(5)]
    return {'scope': 'DESCRIPTIVE_CROSS_MODEL_FIXED_ORDER_NOT_PAIRED_ABBA', 'candidate_qps_rounds': candidate,
            'reference_qps_rounds': reference, 'ratio_of_mean_qps': float(np.mean(candidate) / np.mean(reference)),
            'ratio_CI': None, 'paired_round_ratios': None, 'cross_model_paired_inference_allowed': False,
            'limitation': 'Each model ran in fixed listed order in a separate evaluator process; matching round indices does not create a between-model paired timing design'}


def summarize(dataset, records, evidence, out, rng, chunk, p2):
    compared, draws_to_save, primary = [], {}, []
    for l in LS:
        rec = {(name, method): np.asarray([row['recall'] for row in records[name]['crows'][(l, method, 0)]['per_query']], dtype=np.float64)
               for name in MODELS for method in METHODS}
        deltas = np.stack([rec[(cm, ct)] - rec[(rm, rt)] for _, cm, ct, rm, rt, _ in CONTRASTS])
        draws = p2.bootstrap_deltas(deltas, rng, chunk)
        for i, (name, cm, ct, rm, rt, family) in enumerate(CONTRASTS):
            low, high = np.quantile(draws[i], [.025, .975]) * 100
            a, b = records[cm]['crows'][(l, ct, 0)], records[rm]['crows'][(l, rt, 0)]
            item = {'dataset': dataset, 'L': l, 'contrast': name, 'family': family,
                    'candidate_model': cm, 'candidate_method': ct, 'reference_model': rm, 'reference_method': rt,
                    'recall_delta_pp': float(deltas[i].mean() * 100), 'paired_query_bootstrap95_pp': [float(low), float(high)],
                    'interval_scope': 'POINTWISE_ORDINARY_95_EXPLORATORY_UNADJUSTED', 'recall_evidence_sign': p2.evidence_sign(low, high),
                    'query_improved': int(np.count_nonzero(deltas[i] > 0)), 'query_harmed': int(np.count_nonzero(deltas[i] < 0)),
                    'query_equal': int(np.count_nonzero(deltas[i] == 0)),
                    'QPS_comparison': qps_comparison(records, l, cm, ct, rm, rt, p2),
                    'mean_graph_ndc_delta': a['mean_graph_ndc'] - b['mean_graph_ndc'],
                    'mean_total_ndc_delta': a['mean_total_ndc'] - b['mean_total_ndc'],
                    'mean_total_mac_delta': a['mean_total_mac'] - b['mean_total_mac'],
                    'same_actual_route_required': family == 'within_model_queue',
                    'oracle_diagnostic_only': True, 'matched_cost_claim': False, 'automatic_P3_GO': False}
            compared.append(item)
            draws_to_save[f'L{l}_{name}'] = draws[i]
            if name == 'structure_under_greedy3':
                primary.append({'dataset': dataset, 'L': l, 'contrast': name, 'recall_delta_pp': item['recall_delta_pp'],
                                'ordinary95_interval_pp': item['paired_query_bootstrap95_pp'], 'lower_bound_positive': bool(low > 0)})
    bootstrap_path = out / ('bootstrap_' + dataset + '.npz')
    with bootstrap_path.open('xb') as f:
        np.savez_compressed(f, **draws_to_save)
    cost = {name: {'count_peak_rss_kib': record['count']['peak_rss_kib'], 'timing_peak_rss_kib': record['timing']['peak_rss_kib'],
                   'count_router_index_build_seconds': record['count']['hnsw']['build_seconds'],
                   'timing_router_index_build_seconds': record['timing']['hnsw']['build_seconds'],
                   'portal_probe_cost_seconds': record['probe']['cost_seconds'], 'probe_cost_shared_between_portal_rules': True}
            for name, record in records.items()}
    return {'dataset': dataset, 'audit_status': 'PASS', 'evidence': evidence, 'measurements': measurements(dataset, records),
            'fixed_comparisons': compared, 'bootstrap_draws': bound(bootstrap_path), 'primary_search_condition_cells': primary,
            'cost': cost, 'cost_caution': 'Repeated cost pointers for frequency/greedy refer to one shared probe run per lambda; do not sum duplicated costs',
            'stage_gate': 'REQUIRES_ROOT_STRUCTURE_AND_SEARCH_REVIEW', 'automatic_GO': False,
            'frontier_constructed': False, 'online_performance_improvement_confirmed': False}


def csv_write(path, rows):
    with path.open('x', newline='') as f:
        keys = list(rows[0]) if rows else []
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def markdown(report):
    lines = ['# P3 固定 2×2 pilot 证据', '',
             '四个模型和全部八类预定对照均完整报告。每项区间是普通、未校正的 95% 配对查询 bootstrap，供开发阶段诊断；五轮计时不是五个 Recall 样本。本报告不自动通过 P3，不启动 P4，也不声称部署性能改善。', '']
    for ds in report['datasets']:
        lines += [f"## {ds['dataset']}", '', '完整性核验：PASS。包含 count/plain 全结果、完整实际 route、五轮身份、固定 AB/BA 顺序，以及四格一致的 Fast 控制。', '',
                  '| 模型 | 方法 | L | Recall@10 | 平均 QPS | 图 / 总 NDC | 平均实际入口数 |',
                  '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
        for row in ds['measurements']:
            lines.append(f"| {row['model']} | {row['method']} | {row['L']} | {row['recall']:.6f} | {row['qps_mean_of_five']:.2f} | {row['mean_graph_ndc']:.2f} / {row['mean_total_ndc']:.2f} | {row['actual_entries_mean']:.3f} |")
        lines += ['', '除 Fast 外均为 oracle 诊断。原始五轮 QPS/wall、路由 wall、NDC/MAC 和计数器完整保存在 JSON/CSV。路由单独计时来自额外的一次 warmed batch，不能与图时间相加重建整体 QPS。', '',
                  '| 固定对照（候选减参考） | L | Recall 差 pp | 普通 95% 区间 pp | QPS 均值比 | 计时范围 |',
                  '| --- | ---: | ---: | --- | ---: | --- |']
        for row in ds['fixed_comparisons']:
            lo, hi = row['paired_query_bootstrap95_pp']
            q = row['QPS_comparison']
            lines.append(f"| {row['contrast']} | {row['L']} | {row['recall_delta_pp']:+.4f} | [{lo:+.4f}, {hi:+.4f}] | {q['ratio_of_mean_qps']:.4f} | {'同模型 AB/BA' if row['family'] == 'within_model_queue' else '跨模型固定顺序，仅描述'} |")
        lines += ['', f"原始运行和模型绑定：[execution.json]({ds['evidence']['execution']['path']})。Bootstrap 差值样本：[NPZ]({ds['bootstrap_draws']['path']})。", '']
    condition = report['primary_search_condition']
    lines += ['## 主对照与解释边界', '',
              '主对照固定为 oracle_probability 下 λ1_greedy3 − λ0_greedy3；两个数据集的 L64/128 共四格都需普通 95% 下界大于零，才满足预定的搜索子条件。', '',
              f"当前四格下界均大于零：{condition['all_four_lower_bounds_positive']}。这只是搜索子条件的描述，结构目标、容量、完整重算和共同初始化仍由主控独立检查。P3 gate：REQUIRES_ROOT_STRUCTURE_AND_SEARCH_REVIEW。", '',
              '同 L 的 Recall 改变不等于同成本收益。跨模型没有交错 ABBA 调度，只报告 QPS 均值比和双方原始轮次；不能把相同轮次编号当作跨模型配对证据。所有固定对照均展示，不选择最好模型或最有利工作点。', '',
              '该分析不读取 query、GT、base 或图向量内容；读取既有评估行、JSON 元数据和小型模型/路由器 artifact，核验 checksum。原图 SHA 继承 P0，图本体不重复扫描。开发 pilot 曾用于研究，普通区间未经多重比较校正；不构造部署 frontier，不替代 P5/P6/P7 验收。', '']
    return '\n'.join(lines)


def synthetic_artifacts(p2):
    n, d, nq, seed = 2000, 8, 3, 1999
    portals = np.arange(768, dtype=np.int32).reshape(256, 3)
    artifacts = {}
    for kind in ('count', 'timing'):
        artifact = {'schedule': [], 'results': []}
        for l in LS:
            for r in range(1 if kind == 'count' else 5):
                for method in (METHODS[::-1] if r % 2 else METHODS):
                    artifact['schedule'].append({'L': l, 'round': r, 'method': method, 'method_index': METHODS.index(method), 'order': 'BA' if r % 2 else 'AB'})
                    rows = []
                    for q in range(nq):
                        row = {'query_id': q, 'recall': .5, 'result_ids': list(range(10)), 'fast_anchor_id': 900,
                               'shared_seed': -1 if method == 'fast' else seed, 'entry_ids': [900, 901, 902] if method == 'fast' else [900] + list(range(12)),
                               'regions': [] if method == 'fast' else [0, 1, 2, 3], 'weights': [] if method == 'fast' else [.4, .3, .2, .1],
                               'actual_entry_count': 3 if method == 'fast' else 14}
                        if kind == 'count':
                            row.update(routing_ndc=4, graph_ndc=20, total_ndc=24, routing_mac=32, graph_mac=160, total_mac=192,
                                       routing_us_instrumented=1., graph_us_instrumented=2., expanded=10, rejected=0, evicted_unexpanded=0)
                        rows.append(row)
                    ih, rh = p2.fingerprint_rows(rows)
                    cell = {'method': method, 'search_L': l, 'round': r, 'top_k': 10, 'mean_recall': .5,
                            'result_hash_fnv1a64': ih, 'route_hash_fnv1a64': rh, 'repeated_routes_results_stable': True,
                            'oracle': method != 'fast', 'timing_publishable': kind == 'timing' and method == 'fast',
                            'batch_wall_us': None if kind == 'count' else 100., 'qps': None if kind == 'count' else nq * 1e6 / 100,
                            'min_actual_entry_count': rows[0]['actual_entry_count'], 'max_actual_entry_count': rows[0]['actual_entry_count']}
                    cell.update({'mean_' + key: rows[0][key] if kind == 'count' else None for key in METRICS})
                    if kind == 'count':
                        cell.update(mean_routing_us_instrumented=1., mean_graph_us_instrumented=2.)
                    if r == 0:
                        cell['per_query'] = rows
                    else:
                        cell['aligned_reference_round'] = 0
                    artifact['results'].append(cell)
        artifacts[kind] = artifact
    return artifacts, portals, n, d, nq, seed


def selftest(output, p2):
    require(len(CONTRASTS) == len({x[0] for x in CONTRASTS}) == 8 and
            sum(x[-1] == 'cross_model_2x2' for x in CONTRASTS) == 4 and
            sum(x[-1] == 'within_model_queue' for x in CONTRASTS) == 4, 'Fixed eight-comparison family malformed')
    artifacts, portals, n, d, nq, seed = synthetic_artifacts(p2)
    verify_batches(artifacts['count'], artifacts['timing'], portals, n, d, seed, p2, nq=nq)
    rejected = []
    def rejects(name, fn):
        try:
            fn()
        except (ValueError, KeyError):
            rejected.append(name)
        else:
            raise AssertionError('Missing rejection: ' + name)
    bad = copy.deepcopy(artifacts['timing']); bad['results'].pop()
    rejects('missing_method_round', lambda: verify_batches(artifacts['count'], bad, portals, n, d, seed, p2, nq=nq))
    bad = copy.deepcopy(artifacts['timing']); bad['schedule'][0]['order'] = 'BA'
    rejects('wrong_schedule', lambda: verify_batches(artifacts['count'], bad, portals, n, d, seed, p2, nq=nq))
    bad = copy.deepcopy(artifacts['timing']); bad['results'][0]['per_query'][0]['recall'] = .6
    rejects('plain_recall_drift', lambda: verify_batches(artifacts['count'], bad, portals, n, d, seed, p2, nq=nq))
    bad = copy.deepcopy(artifacts['timing']); bad['results'][3]['result_hash_fnv1a64'] ^= 1
    rejects('repeat_identity_drift', lambda: verify_batches(artifacts['count'], bad, portals, n, d, seed, p2, nq=nq))
    invalid = copy.deepcopy(artifacts['count']['results'][1]['per_query'][0]); invalid['entry_ids'].pop(); invalid['actual_entry_count'] -= 1
    rejects('dropped_portal', lambda: check_route(invalid, 'oracle_unified', portals, n, seed))
    deltas = np.stack([np.asarray([-.1, 0, .1, .2])] * 2 + [np.zeros(4), np.full(4, .1)] + [np.full(4, -.1)] * 4)
    draws = p2.bootstrap_deltas(deltas, np.random.default_rng(SEED), 64)
    require(draws.shape == (8, REPS) and np.array_equal(draws[0], draws[1]) and np.all(draws[2] == 0) and
            np.allclose(draws[3], .1) and np.allclose(draws[4:], -.1), 'Shared bootstrap draw or constant-delta test failed')
    result = {'status': 'PASS', 'real_data_accessed': False, 'fixed_CI_family': 8, 'ordinary_pointwise_only': True,
              'shared_draws_within_dataset_L': True, 'rejected_cases': rejected, 'P2_helper': bound(P2_HELPER), 'source': bound(__file__)}
    write_json(output / 'selftest.json', result)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset-eval', action='append', nargs=2, metavar=('DATASET', 'EVAL_DIR'))
    parser.add_argument('--p1-gate', type=Path)
    parser.add_argument('--protocol', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bootstrap-chunk', type=int, default=64)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    require(1 <= args.bootstrap_chunk <= 256, 'Bootstrap chunk must be 1..256')
    p2 = import_p2()
    if args.self_test:
        require(not args.dataset_eval and args.p1_gate is None and args.protocol is None, 'Self-test must not receive real artifact paths')
        args.output.mkdir(parents=True, exist_ok=False)
        selftest(args.output, p2)
        return
    require(args.p1_gate is not None and args.protocol is not None, 'P3 protocol and accepted P1 gate required')
    supplied = {dataset: path for dataset, path in (args.dataset_eval or [])}
    require(len(args.dataset_eval or []) == len(supplied) == 2 and set(supplied) == set(DATASETS), 'Exactly both registered datasets required')
    protocol, p1 = read(args.protocol), read(args.p1_gate)
    require(protocol['stage'] == 'P3' and protocol['fit_range'] == [10000, 30000] and protocol['cpu_only'] is True and
            protocol['validation_heldout_allowed'] is False, 'P3 CPU/fit-only protocol required')
    require(protocol['evaluation']['models'] == list(MODELS) and protocol['evaluation']['methods'] == list(METHODS) and
            protocol['evaluation']['search_Ls'] == list(LS) and protocol['evaluation']['threads'] == 16 and
            protocol['evaluation']['warmup'] == 128 and protocol['evaluation']['count_rounds'] == 1 and
            protocol['evaluation']['timing_rounds'] == 5, 'Preregistered evaluation family/settings changed')
    require(protocol['analysis_and_gate']['bootstrap_repetitions'] == REPS and protocol['analysis_and_gate']['seed'] == SEED, 'Preregistered bootstrap changed')
    protocol_binding, p1_binding = bound(args.protocol), bound(args.p1_gate)
    require(p1['status'] == 'PASS' and p1['stage'] == 'P1_P3_REACCEPTANCE' and p1['protocol_sha256'] == protocol_binding['sha256'], 'P3 P1 reacceptance required')
    args.output.mkdir(parents=True, exist_ok=False)
    invocation = {'status': 'INCOMPLETE', 'argv': sys.argv, 'source': bound(__file__), 'P2_helper': bound(P2_HELPER),
                  'protocol': protocol_binding, 'p1_gate': p1_binding, 'bootstrap_repetitions': REPS, 'seed': SEED,
                  'bootstrap_chunk': args.bootstrap_chunk, 'rng_order': 'Fixed DATASETS order, then L64,L128; one RNG stream',
                  'unit_of_resampling': 'Paired pilot query IDs; every fixed comparison within one dataset/L uses the same query-index draws',
                  'bootstrap_npz_content': 'Replicate mean Recall differences, not raw index matrices; seed/RNG/chunk/helper hashes reproduce samples',
                  'comparison_selection': 'Exactly eight fixed contrasts per L per dataset; no winner/model/working-point selection',
                  'reads_query_GT_base_graph_contents': False, 'validation_or_heldout_accessed': False}
    write_json(args.output / 'invocation.json', invocation)
    report = {'schema_version': 1, 'status': 'INCOMPLETE', 'scope': 'P3_FIXED_2X2_ORACLE_PILOT_DIAGNOSTIC',
              'stage_gate': 'REQUIRES_ROOT_STRUCTURE_AND_SEARCH_REVIEW', 'automatic_P3_GO': False,
              'P4_authorized_by_script': False, 'online_performance_improvement_confirmed': False,
              'bootstrap': invocation, 'datasets': []}
    rng = np.random.default_rng(SEED)
    try:
        for dataset in DATASETS:
            records, evidence = verify_dataset(dataset, supplied[dataset], protocol_binding, p1_binding, p1, p2)
            summary = summarize(dataset, records, evidence, args.output, rng, args.bootstrap_chunk, p2)
            write_json(args.output / (dataset + '.json'), summary)
            report['datasets'].append(summary)
            del records
            print(json.dumps({'dataset': dataset, 'audit': 'PASS', 'analysis': 'COMPLETE', 'automatic_P3_GO': False}), flush=True)
        primary = [row for ds in report['datasets'] for row in ds['primary_search_condition_cells']]
        require(len(primary) == 4, 'Primary search condition must cover both L values on both datasets')
        report['primary_search_condition'] = {'comparison': 'lambda1_greedy3 oracle_probability minus lambda0_greedy3 oracle_probability',
            'cells': primary, 'all_four_lower_bounds_positive': all(row['lower_bound_positive'] for row in primary),
            'interpretation': 'Describes only the preregistered oracle search subcondition; structure/capacity/full-recompute/common-initialization gate remains separate',
            'automatic_stage_gate': False}
        report['status'] = 'COMPLETE'
        write_json(args.output / 'analysis.json', report)
        csv_write(args.output / 'measurements.csv', [row for ds in report['datasets'] for row in ds['measurements']])
        csv_write(args.output / 'comparisons.csv', [row for ds in report['datasets'] for row in ds['fixed_comparisons']])
        with (args.output / 'report.md').open('x') as f:
            f.write(markdown(report))
        write_json(args.output / 'complete.json', {'status': 'COMPLETE', 'analysis': bound(args.output / 'analysis.json'),
                                                  'stage_gate': report['stage_gate'], 'automatic_P3_GO': False})
    except BaseException as error:
        write_json(args.output / 'failure.json', {'status': 'INCOMPLETE', 'error': repr(error),
            'completed_datasets': [ds['dataset'] for ds in report['datasets']],
            'interpretation': 'Integrity/completeness/analysis failure, not an algorithmic P3 NOPASS decision'})
        raise


if __name__ == '__main__':
    main()
