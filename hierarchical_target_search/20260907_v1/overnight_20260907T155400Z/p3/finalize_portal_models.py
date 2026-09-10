#!/usr/bin/env python3
"""Verify frozen portal probe caches independently and finalize both fixed P3 models.

No ANN, query selection, parameter selection, or pilot/validation/heldout access.
Python set unions independently check the C++ bitwise greedy implementation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

SOFT_CLOSE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
FIT_BEGIN, FIT_COUNT, LEAVES, PORTALS = 10000, 20000, 256, 3
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deadline():
    require(time.time() < SOFT_CLOSE, 'P3 research soft deadline reached')


def read_json(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path)}


def resolve_bound(descriptor, parent):
    path = Path(descriptor['path'])
    return path.resolve() if path.is_absolute() else (Path(parent) / path).resolve()


def verified_path(descriptor, parent, expected_bytes=None):
    path = resolve_bound(descriptor, parent)
    digest = descriptor['sha256']
    require(isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest),
            'Invalid SHA256 descriptor')
    if expected_bytes is not None:
        require(path.stat().st_size == expected_bytes, 'Raw shape mismatch: ' + str(path))
    if 'bytes' in descriptor:
        require(path.stat().st_size == descriptor['bytes'], 'Descriptor byte count mismatch: ' + str(path))
    require(sha(path) == digest, 'SHA256 mismatch: ' + str(path))
    return path


def verified_json(descriptor, parent):
    return read_json(verified_path(descriptor, parent))


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def write_raw(path, values):
    with Path(path).open('xb') as f:
        f.write(np.ascontiguousarray(values).tobytes())
        f.flush()
        os.fsync(f.fileno())


def strict_int(value, message, minimum=0):
    require(type(value) is int and value >= minimum, message)
    return value


def validate_probe_header(probe):
    require(probe['status'] == 'COMPLETE' and probe['stage'] == 'P3_PORTAL_PROBES', 'Complete P3 probe required')
    require(probe['complete_leaves'] == 256 and len(probe['regions']) == 256, 'All 256 completed leaves required')
    require(probe['cpu_only'] is True and probe['pilot_accessed'] is False and
            probe['validation_accessed'] is False and probe['heldout_accessed'] is False,
            'Probe input isolation flags invalid')
    require(probe['online_QPS_publishable'] is False, 'Portal probes cannot publish online QPS')
    search = probe['search_contract']
    for key, value in {'K': 10, 'L': 32, 'single_portal': True, 'default_seed': False,
                       'Fast': False, 'GT_argument': False, 'raw_query_IP': True, 'score_after_search': True}.items():
        require(search[key] == value, 'Probe search contract mismatch: ' + key)


def validate_masks(masks, allowed_masks):
    require(masks.ndim == 2 and masks.shape[1] == len(allowed_masks), 'Mask/query shape mismatch')
    require(masks.dtype == np.dtype('<u2'), 'Expected little-endian uint16 masks')
    require(np.all(masks < 1024), 'Mask contains bits outside GT10')
    for q, allowed in enumerate(allowed_masks):
        require(all((int(value) & ~int(allowed)) == 0 for value in masks[:, q]),
                'Mask contains a GT target outside its leaf')


def recompute_selections(candidate_ids, masks):
    """Use sets of (query position, GT rank), independently of C++ bitwise gains."""
    require(3 <= len(candidate_ids) <= 8 and len(set(candidate_ids)) == len(candidate_ids),
            'Three to eight distinct candidate IDs required')
    require(masks.shape[0] == len(candidate_ids), 'Candidate/mask row mismatch')
    require(masks.ndim == 2 and np.all(masks < 1024), 'Invalid GT10 mask matrix')
    frequency = list(candidate_ids[:3])
    if masks.shape[1] == 0:
        return {'frequency_portals': frequency, 'greedy_portals': frequency,
                'greedy_gains': [0, 0, 0], 'greedy_union_hits': 0, 'frequency_union_hits': 0}
    coverage = {}
    for candidate, row in zip(candidate_ids, masks):
        coverage[candidate] = {(q, rank) for q, value in enumerate(row) for rank in range(10)
                               if int(value) & (1 << rank)}
    frequency_union = set().union(*(coverage[node] for node in frequency))
    current, chosen, gains = set(), [], []
    for _ in range(3):
        ranked = sorted(((-len(coverage[node] - current), node) for node in candidate_ids if node not in chosen))
        negative_gain, winner = ranked[0]
        gains.append(-negative_gain)
        chosen.append(winner)
        current.update(coverage[winner])
    require(sum(gains) == len(current), 'Internal set-greedy accounting failure')
    return {'frequency_portals': frequency, 'greedy_portals': chosen, 'greedy_gains': gains,
            'greedy_union_hits': len(current), 'frequency_union_hits': len(frequency_union)}


def load_contract(args):
    plan_path, probe_path = args.plan.resolve(), args.probe_complete.resolve()
    plan, probe = read_json(plan_path), read_json(probe_path)
    parent = plan_path.parent
    require(plan['schema_version'] == 1 and plan['status'] == 'COMPLETE' and plan['stage'] == 'P3' and
            plan['dataset'] in DATASETS and plan['cpu_only'] is True, 'Invalid frozen P3 plan')
    require(plan['fit_range'] == [10000, 30000] and plan['fit_count'] == FIT_COUNT and
            plan['region_count'] == LEAVES and plan['seed'] == 2026090711 and
            plan['pilot_accessed'] is False and plan['heldout_accessed'] is False, 'Plan fit/region/seed boundary mismatch')
    require(type(plan['structure_lambda']) is int and plan['structure_lambda'] in (0, 1), 'Unregistered structure lambda')
    validate_probe_header(probe)
    require(probe['plan_sha256'] == sha(plan_path) and Path(probe['plan']).resolve() == plan_path,
            'Probe was not generated from this exact plan')
    for key in ('protocol', 'fit_manifest', 'partition_manifest', 'audit', 'gate', 'source_binding'):
        require(probe[key] == plan[key], 'Probe/plan binding mismatch: ' + key)
    for key in ('queries', 'gt10', 'labels', 'index'):
        require(probe['inputs'][key] == plan[key], 'Probe raw input binding mismatch: ' + key)
    require(probe['dataset'] == plan['dataset'] and probe['structure_lambda'] == plan['structure_lambda'] and
            probe['fit_range'] == plan['fit_range'] and probe['fit_count'] == FIT_COUNT and probe['threads'] == 16,
            'Probe dataset/structure/fit/thread mismatch')
    protocol = verified_json(plan['protocol'], parent)
    gate = verified_json(plan['gate'], parent)
    audit = verified_json(plan['audit'], parent)
    fit = verified_json(plan['fit_manifest'], parent)
    partition = verified_json(plan['partition_manifest'], parent)
    require(protocol['stage'] == 'P3' and protocol['cpu_only'] is True and
            protocol['fit_range'] == plan['fit_range'] and protocol['validation_heldout_allowed'] is False and
            protocol['portals']['per_leaf'] == 3 and protocol['portals']['candidate_limit'] == 8 and
            protocol['portals']['query_limit_per_leaf'] == 128, 'P3 portal protocol mismatch')
    require(gate['stage'] == 'P2' and gate['status'] == 'PASS' and gate['decision'] == 'GO_P3_STRUCTURE_DIAGNOSTIC_ONLY' and
            protocol['upstream_P2']['sha256'] == plan['gate']['sha256'], 'P2 gate binding mismatch')
    require(audit['status'] == 'PASS_INPUT_CONTRACT', 'P0 contract required')
    datasets = [entry for entry in audit['datasets'] if entry['dataset'] == plan['dataset']]
    require(len(datasets) == 1, 'Missing/duplicate audited dataset')
    ds = datasets[0]
    n, dim = strict_int(plan['n_base'], 'Invalid node count', 768), strict_int(plan['dim'], 'Invalid dimension', 1)
    require(n == ds['graph']['header']['n'] and dim == ds['graph']['header']['d'] and
            plan['index']['sha256'] == ds['graph']['sha256'] and
            resolve_bound(plan['index'], parent) == Path(ds['graph']['path']).resolve(), 'Frozen graph provenance mismatch')
    for key, value in {'status': 'COMPLETE', 'stage': 'P3', 'dataset': plan['dataset'],
                       'fit_range': plan['fit_range'], 'fit_count': FIT_COUNT, 'cpu_only': True,
                       'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
                       'base_nodes': n, 'dim': dim, 'input_audit_sha256': plan['audit']['sha256'],
                       'protocol_sha256': plan['protocol']['sha256']}.items():
        require(fit[key] == value, 'Fit manifest mismatch: ' + key)
    require(fit['fit_query_values_sha256'] == ds['fit']['query_values_sha256'] and
            fit['fit_gt_values_sha256'] == ds['fit']['gt_values_sha256'], 'Audited fit value fingerprints differ')
    for key, value in {'status': 'COMPLETE', 'stage': 'P3', 'dataset': plan['dataset'], 'nodes': n,
                       'regions': LEAVES, 'coarse_count': 16, 'leaves_per_coarse': 16,
                       'lambda': plan['structure_lambda'], 'protocol_sha256': plan['protocol']['sha256'],
                       'input_audit_sha256': plan['audit']['sha256'], 'fit_manifest_sha256': plan['fit_manifest']['sha256'],
                       'fit_gt_values_sha256': ds['fit']['gt_values_sha256']}.items():
        require(partition[key] == value, 'Partition manifest mismatch: ' + key)
    require(plan['labels']['sha256'] == partition['labels_sha256'] and
            resolve_bound(plan['labels'], parent) == Path(partition['labels_file']).resolve(), 'Final leaf labels not bound to partition')
    require(plan['gt10']['sha256'] == fit['gt10_sha256'] and resolve_bound(plan['gt10'], parent) == Path(fit['gt10_file']).resolve(),
            'Fit GT10 extraction binding mismatch')
    require(plan['queries']['sha256'] == fit['queries_sha256'] == ds['fit']['query_values_sha256'] and
            resolve_bound(plan['queries'], parent) == Path(fit['queries_file']).resolve(), 'Fit query extraction binding mismatch')
    # The query values are only hashed for provenance; no query is used for fitting or ANN.
    verified_path(plan['queries'], parent, FIT_COUNT * dim * 4)
    gt_path = verified_path(plan['gt10'], parent, FIT_COUNT * 10 * 4)
    labels_path = verified_path(plan['labels'], parent, n * 2)
    gt = np.fromfile(gt_path, dtype='<i4').reshape(FIT_COUNT, 10)
    labels = np.memmap(labels_path, dtype='<u2', mode='r', shape=(n,))
    require(int(gt.min()) >= 0 and int(gt.max()) < n, 'Fit GT10 ID outside base')
    require(not np.any(np.diff(np.sort(gt, axis=1), axis=1) == 0), 'Duplicate fit GT10 IDs')
    require(int(labels.max()) < LEAVES, 'Label outside 256-leaf partition')
    sizes = np.bincount(labels, minlength=LEAVES)
    require(int(sizes.min()) >= 3 and int(sizes.max()) <= 6*n//(5*LEAVES) and
            int(sizes.reshape(16, 16).sum(axis=1).max()) <= 6*n//(5*16), 'P3 leaf/coarse capacity violation')
    require(len(plan['source_binding']) >= 4, 'Source/build/binary bindings required')
    source_paths = [verified_path(bound, parent) for bound in plan['source_binding']]
    binary_path = verified_path(probe['binary'], probe_path.parent)
    require(binary_path in source_paths, 'Probe binary is not one of the frozen source/build bindings')
    require(any(path.name == 'bench_hierarchical_portals.cpp' for path in source_paths) and
            any(path.name == 'RegionalSearch.h' for path in source_paths), 'Missing prober/kernel source provenance')
    require(len(plan['regions']) == LEAVES, 'Plan lacks complete leaf coverage')
    return plan, probe, fit, partition, gt, labels, labels_path


def verify_region(r, leaf, descriptor, probe, gt, labels, probe_parent):
    require(leaf['region'] == r and descriptor['region'] == r and descriptor['status'] == 'COMPLETE',
            'Leaf order, identity, or checkpoint status mismatch')
    region_path = verified_path(descriptor, probe_parent)
    region = read_json(region_path)
    require(region['schema_version'] == 1 and region['status'] == 'COMPLETE' and region['region'] == r,
            'Incomplete or wrongly identified region checkpoint')
    require(region['plan_sha256'] == probe['plan_sha256'] and region['binary_sha256'] == probe['binary']['sha256'],
            'Region source/plan identity differs from completed run')
    candidates, qids = leaf['candidate_ids'], leaf['query_ids']
    require(3 <= len(candidates) <= 8 and all(type(x) is int and 0 <= x < len(labels) for x in candidates) and
            len(set(candidates)) == len(candidates), 'Invalid portal candidates')
    require(all(int(labels[node]) == r for node in candidates), 'Candidate outside target leaf')
    require(len(qids) <= 128 and all(type(q) is int and FIT_BEGIN <= q < FIT_BEGIN + FIT_COUNT for q in qids) and
            len(set(qids)) == len(qids), 'Invalid fit query IDs')
    require(region['candidate_ids'] == candidates and region['query_ids'] == qids,
            'Checkpoint candidate/query order differs from frozen plan')
    gt_rows = gt[np.asarray(qids, dtype=np.int64) - FIT_BEGIN]
    require(region['GT10_order'] == gt_rows.tolist(), 'Saved GT10 order does not match fit source rows')
    gt_json = json.dumps(region['GT10_order'], separators=(',', ':')).encode('utf-8')
    require(digest_bytes(gt_json) == region['GT10_order_sha256'], 'Saved GT10-order checksum mismatch')
    allowed = [sum(1 << rank for rank, node in enumerate(row) if int(labels[node]) == r) for row in gt_rows]
    require(all(value > 0 for value in allowed), 'Selected query lacks a GT10 target in its leaf')
    calls = len(candidates) * len(qids)
    require(region['mask_shape'] == [len(candidates), len(qids)] and
            region['mask_layout'] == 'candidate-major/query-contiguous uint16 little-endian', 'Mask layout mismatch')
    require(region['calls_planned'] == calls == region['calls_completed'], 'Partial probe pairs cannot be finalized')
    require(region['no_fit_query_evidence'] is (len(qids) == 0), 'Empty-fit evidence flag mismatch')
    require(region.get('error') is None and 'completed_bitmap' not in region, 'Partial/errored checkpoint cannot be finalized')
    mask_path = verified_path(region['mask_file'], region_path.parent, calls * 2)
    masks = np.fromfile(mask_path, dtype='<u2').reshape(len(candidates), len(qids))
    validate_masks(masks, allowed)
    independent = recompute_selections(candidates, masks)
    for key, value in independent.items():
        require(region[key] == value, 'C++/Python selection mismatch at leaf ' + str(r) + ': ' + key)
    for key in ('frequency_portals', 'greedy_portals'):
        require(len(set(independent[key])) == 3 and all(int(labels[node]) == r for node in independent[key]),
                'Selected portals violate fixed count/leaf membership')
    potential = sum(int(value).bit_count() for value in allowed)
    require(independent['greedy_union_hits'] <= potential and independent['frequency_union_hits'] <= potential,
            'Proxy union hits exceed eligible target support')
    ndc = strict_int(region['ndc'], 'Invalid region NDC')
    expanded = strict_int(region['expanded'], 'Invalid region expansion count')
    require(ndc >= calls and calls <= expanded <= ndc, 'Probe counter bounds inconsistent')
    return {
        'region': r, 'checkpoint': binding(region_path), 'mask': binding(mask_path),
        'candidate_count': len(candidates), 'query_count': len(qids), 'probe_calls': calls,
        'eligible_target_support': potential, 'no_fit_query_evidence': not qids,
        **independent, 'greedy_minus_frequency_hits': independent['greedy_union_hits'] - independent['frequency_union_hits'],
        'ndc': ndc, 'expanded': expanded,
    }


def finalize(args):
    started = time.perf_counter()
    plan, probe, fit, partition, gt, labels, labels_path = load_contract(args)
    input_seconds = time.perf_counter() - started
    deadline()
    rows, seen = [], set()
    verify_start = time.perf_counter()
    for r, (leaf, descriptor) in enumerate(zip(plan['regions'], probe['regions'])):
        deadline()
        path = resolve_bound(descriptor, args.probe_complete.resolve().parent)
        require(path not in seen, 'Repeated checkpoint path')
        seen.add(path)
        rows.append(verify_region(r, leaf, descriptor, probe, gt, labels, args.probe_complete.resolve().parent))
    calls = sum(row['probe_calls'] for row in rows)
    ndc = sum(row['ndc'] for row in rows)
    expanded = sum(row['expanded'] for row in rows)
    require(calls == plan['actual_probe_call_count'] == probe['planned_calls'] == probe['calls_completed'] and calls <= 262144,
            'Aggregate probe call counts mismatch')
    require(ndc == probe['ndc'] and expanded == probe['expanded'] and probe['graph_MAC'] == ndc * plan['dim'],
            'Aggregate probe NDC/expansion/MAC mismatch')
    frequency = np.asarray([row['frequency_portals'] for row in rows], dtype='<i4')
    greedy = np.asarray([row['greedy_portals'] for row in rows], dtype='<i4')
    for key, expected in (('frequency_portals', frequency), ('greedy_portals', greedy)):
        path = verified_path(probe[key], args.probe_complete.resolve().parent, 256 * 3 * 4)
        got = np.fromfile(path, dtype='<i4').reshape(256, 3)
        require(np.array_equal(expected, got), 'Final C++ portal array differs from all independently checked leaves')
        require(digest_bytes(expected.tobytes()) == probe[key]['sha256'], 'Independent final portal byte fingerprint differs')
    verify_seconds = time.perf_counter() - verify_start
    deadline()
    report = {
        'schema_version': 1, 'status': 'COMPLETE', 'stage': 'P3_PORTAL_FINALIZATION',
        'dataset': plan['dataset'], 'lambda': plan['structure_lambda'], 'cpu_only': True,
        'fit_range': plan['fit_range'], 'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
        'ANN_calls_executed_by_finalizer': 0, 'selected_models': ['frequency3', 'greedy3'],
        'model_choice_based_on_pilot': False,
        'verification_scope': 'Frozen plan, checksums, GT-order/target-leaf mask semantics, exact set-based greedy/frequency recomputation and final array equality. Search itself is not rerun or reconstructed from masks.',
        'plan': binding(args.plan), 'probe_complete': binding(args.probe_complete), 'source': binding(__file__),
        'protocol': plan['protocol'], 'audit': plan['audit'], 'gate': plan['gate'],
        'fit_manifest': plan['fit_manifest'], 'partition_manifest': plan['partition_manifest'],
        'complete_leaves': len(rows), 'probe_calls_reused': calls, 'probe_NDC_reused': ndc,
        'probe_expanded_reused': expanded, 'regions': rows, 'models': {},
        'cost_seconds': {'input_read_hash_validate': input_seconds, 'independent_cache_and_selection_verification': verify_seconds},
        'input_probe_cost_seconds': probe['cost_seconds'],
        'cost_scope': 'Finalizer costs are added once per structure. The same probe cache serves both portal rules; frequency3 does not require ANN probe selection. Thread-second sums in the probe report are not wall time.',
        'exact_GT_from_scratch_seconds': None, 'exact_GT_cost_reason': probe['exact_GT_cost_reason'],
        'online_performance_improvement_confirmed': False,
    }
    deltas = np.asarray([row['greedy_minus_frequency_hits'] for row in rows], dtype=np.int64)
    report['fit_proxy_description'] = {
        'unit': 'Union hits across the frozen <=128 eligible fit queries per leaf',
        'sum_frequency_union_hits': sum(row['frequency_union_hits'] for row in rows),
        'sum_greedy_union_hits': sum(row['greedy_union_hits'] for row in rows),
        'sum_greedy_minus_frequency_hits': int(deltas.sum()),
        'negative_leaves': int(np.count_nonzero(deltas < 0)), 'zero_leaves': int(np.count_nonzero(deltas == 0)),
        'positive_leaves': int(np.count_nonzero(deltas > 0)), 'no_fit_query_leaves': sum(row['no_fit_query_evidence'] for row in rows),
        'delta_min': int(deltas.min()), 'delta_max': int(deltas.max()), 'delta_mean': float(deltas.mean()),
        'delta_quantiles': {str(q): float(np.quantile(deltas, q)) for q in (0, 0.25, 0.5, 0.75, 1)},
        'zero_greedy_marginal_steps': sum(gain == 0 for row in rows for gain in row['greedy_gains']),
        'population_or_online_inference_allowed': False,
        'limitation': 'Fit-selected single-portal L32 proxy, with overlapping queries across leaves. Descriptive counts are not independent query samples and do not establish joint multi-entry or online benefit.',
    }
    write_start = time.perf_counter()
    for rule, portals in (('frequency3', frequency), ('greedy3', greedy)):
        directory = args.output / rule
        directory.mkdir(exist_ok=False)
        portal_file = directory / 'portals.i32'
        write_raw(portal_file, portals)
        model = {
            'schema_version': 2, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': plan['dataset'],
            'model_name': f"lambda{plan['structure_lambda']}_{rule}", 'lambda': plan['structure_lambda'], 'portal_rule': rule,
            'oracle_diagnostic_only': True, 'parent_rule': 'leaf_id // 16',
            'region_count': LEAVES, 'coarse_count': 16, 'leaves_per_coarse': 16,
            'active_regions': 4, 'portals_per_region': PORTALS, 'total_portals': LEAVES * PORTALS,
            'dim': plan['dim'], 'base_nodes': plan['n_base'], 'fit_range': plan['fit_range'], 'fit_count': FIT_COUNT,
            'cpu_only': True, 'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
            'fit_query_values_sha256': fit['fit_query_values_sha256'], 'fit_gt_values_sha256': fit['fit_gt_values_sha256'],
            'gt10_sha256': fit['gt10_sha256'], 'fit_manifest': plan['fit_manifest'],
            'labels_file': str(labels_path.resolve()), 'labels_sha256': plan['labels']['sha256'],
            'portals_file': str(portal_file.resolve()), 'portals_sha256': sha(portal_file),
            'graph_file': plan['index']['path'], 'graph_sha256': plan['index']['sha256'], 'base_sha256': fit['base_sha256'],
            'input_audit_sha256': plan['audit']['sha256'], 'protocol_sha256': plan['protocol']['sha256'],
            'protocol': plan['protocol'], 'audit': plan['audit'], 'gate': plan['gate'],
            'partition_manifest': plan['partition_manifest'], 'plan': binding(args.plan), 'probe_complete': binding(args.probe_complete),
            'finalizer_source': binding(__file__), 'independent_cache_verification': 'PASS_ALL_256_LEAVES',
            'probe_cache_shared_between_portal_rules': True, 'ANN_probe_selection_required_by_this_rule': rule == 'greedy3',
            'online_performance_improvement_confirmed': False,
            'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        write_json(directory / 'model.json', model)
        report['models'][rule] = binding(directory / 'model.json')
    report['cost_seconds']['model_artifact_write_before_report'] = time.perf_counter() - write_start
    report['cost_seconds']['finalizer_wall_before_report'] = time.perf_counter() - started
    report['created_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    write_json(args.output / 'verification.json', report)
    write_json(args.output / 'complete.json', {'status': 'COMPLETE', 'stage': report['stage'],
                                              'verification': binding(args.output / 'verification.json'), 'models': report['models']})
    print(json.dumps({'status': 'COMPLETE', 'dataset': plan['dataset'], 'lambda': plan['structure_lambda'],
                      'models': report['models'], 'fit_proxy': report['fit_proxy_description']}))


def selftest(output):
    tested = []
    def rejects(name, fn):
        try:
            fn()
        except (ValueError, KeyError):
            tested.append(name)
        else:
            raise AssertionError('Required rejection did not occur: ' + name)
    candidates = [9, 2, 5, 7]
    masks = np.asarray([[1, 1], [2, 0], [3, 0], [0, 4]], dtype='<u2')
    got = recompute_selections(candidates, masks)
    require(got['greedy_portals'] == [5, 7, 9] and got['greedy_gains'] == [2, 1, 1] and
            got['greedy_union_hits'] == 4 and got['frequency_union_hits'] == 3, 'Set-greedy known example failed')
    zero = recompute_selections(candidates, np.zeros((4, 2), dtype='<u2'))
    require(zero['greedy_portals'] == [2, 5, 7] and zero['greedy_gains'] == [0, 0, 0], 'Zero-gain ID tie failed')
    empty = recompute_selections(candidates, np.zeros((4, 0), dtype='<u2'))
    require(empty['greedy_portals'] == candidates[:3] and empty['greedy_union_hits'] == 0, 'No-evidence frequency fallback failed')
    validate_masks(masks, [3, 5])
    rejects('out_of_target_leaf_bit', lambda: validate_masks(masks, [1, 5]))
    rejects('outside_GT10_bit', lambda: validate_masks(np.asarray([[1024]], dtype='<u2'), [1023]))
    rejects('query_mask_shape', lambda: validate_masks(masks, [3]))
    rejects('partial_probe', lambda: validate_probe_header({'status': 'INCOMPLETE', 'stage': 'P3_PORTAL_PROBES'}))
    rejects('missing_leaf', lambda: validate_probe_header({'status': 'COMPLETE', 'stage': 'P3_PORTAL_PROBES',
                                                         'complete_leaves': 255, 'regions': [None] * 255}))
    # Greedy3 can be worse than the frequency subset; retain negative proxy deltas.
    sets = [set(range(4)), set(range(4, 8)), set(range(8, 12)), {0, 1, 2, 4, 5, 6}]
    negative_masks = np.asarray([[sum(1 << (x % 10) for x in s if x // 10 == q) for q in range(2)] for s in sets], dtype='<u2')
    negative = recompute_selections([9, 10, 11, 1], negative_masks)
    require(negative['frequency_union_hits'] == 12 and negative['greedy_union_hits'] == 11, 'Negative proxy contrast was lost')
    result = {'status': 'PASS', 'real_data_accessed': False, 'ANN_calls': 0,
              'set_greedy_ties': True, 'zero_gain_fixed_count': True, 'empty_query_frequency_fallback': True,
              'negative_greedy_minus_frequency_preserved': True, 'rejected_cases': tested, 'source': binding(__file__)}
    write_json(output / 'selftest.json', result)
    print(json.dumps(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--probe-complete', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    deadline()
    require(args.self_test or (args.plan is not None and args.probe_complete is not None), 'Plan and complete probe required')
    require(not args.self_test or (args.plan is None and args.probe_complete is None), 'Self-test must not receive real input paths')
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'started.json', {'status': 'INCOMPLETE', 'source': binding(__file__),
                                             'plan': str(args.plan), 'probe_complete': str(args.probe_complete)})
    try:
        selftest(args.output) if args.self_test else finalize(args)
    except BaseException as error:
        write_json(args.output / 'failure.json', {'status': 'INCOMPLETE', 'error': repr(error)})
        raise


if __name__ == '__main__':
    main()
