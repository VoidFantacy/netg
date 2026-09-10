#!/usr/bin/env python3
"""Frozen P3 post-NOGO descriptive fit/pilot target support diagnosis.

No ANN, fitting, query/base vectors, original graph, validation or heldout reads.
The only parent GT read is the audited physical pilot prefix. Never hash that
whole parent file: its remaining records are outside this diagnostic read scope.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

PROTOCOL_SHA = '4bdd1cd92b42d85f89bd69aec980068c9bed0d5aee90917d5ce2ad8db9823959'
P3_PROTOCOL_SHA = 'fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f'
DATASET_N = {'webvid2_5m_light_v1': 2505000, 'yandex_t2i_official10M_ip_v1': 10000000}
NQ, NFIT, K, REGIONS = 10000, 20000, 10, 256
LS = (64, 128)
MODELS = ('lambda0_frequency3', 'lambda1_frequency3', 'lambda0_greedy3', 'lambda1_greedy3')
METHODS = ('oracle_unified', 'oracle_probability')
STRUCTURES = ('common_initial', 'lambda0_final', 'lambda1_final')
COUNTERS = ('routing_ndc', 'graph_ndc', 'total_ndc', 'routing_mac', 'graph_mac', 'total_mac',
            'expanded', 'rejected', 'evicted_unexpanded')
CONTRASTS = (
    ('structure_under_frequency3', 'lambda1_frequency3', 'oracle_probability', 'lambda0_frequency3', 'oracle_probability'),
    ('structure_under_greedy3', 'lambda1_greedy3', 'oracle_probability', 'lambda0_greedy3', 'oracle_probability'),
    ('portals_under_lambda0', 'lambda0_greedy3', 'oracle_probability', 'lambda0_frequency3', 'oracle_probability'),
    ('portals_under_lambda1', 'lambda1_greedy3', 'oracle_probability', 'lambda1_frequency3', 'oracle_probability'),
) + tuple(('protection_'+name, name, 'oracle_probability', name, 'oracle_unified') for name in MODELS) + (
    ('structure_unified_under_frequency3', 'lambda1_frequency3', 'oracle_unified', 'lambda0_frequency3', 'oracle_unified'),
    ('structure_unified_under_greedy3', 'lambda1_greedy3', 'oracle_unified', 'lambda0_greedy3', 'oracle_unified'),
)
SOFT_DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deadline():
    require(time.time() < SOFT_DEADLINE, 'P3 diagnostic soft deadline reached')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def desc(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def read_json(path):
    return json.loads(Path(path).read_text())


def write_new(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def bound_path(binding):
    path = Path(binding['path']).resolve()
    require(sha(path) == binding['sha256'], 'SHA256 mismatch: '+str(path))
    return path


def bound_json(binding):
    return read_json(bound_path(binding))


def expect(obj, fields, context):
    for key, value in fields.items():
        require(obj.get(key) == value, context+' mismatch: '+key)


def dataset_map(obj):
    rows = obj['datasets']
    require(len(rows) == len(DATASET_N) and {d['dataset'] for d in rows} == set(DATASET_N),
            'Missing, duplicate or unexpected dataset')
    return {d['dataset']: d for d in rows}


def validate_gt10(gt, rows, nodes):
    require(gt.shape == (rows, K) and np.issubdtype(gt.dtype, np.signedinteger), 'GT10 integer shape mismatch')
    require(int(gt.min()) >= 0 and int(gt.max()) < nodes, 'GT10 ID outside frozen base')
    require(np.all(np.diff(np.sort(gt, axis=1), axis=1) != 0), 'Duplicate GT10 target in a query')


def read_pilot_prefix(audit_ds, rows, nodes):
    """One bounded read; no EOF probe, parent hash, memmap, seek or fit suffix."""
    fmeta = audit_ds['files']['drl_train_gt_path']
    header = fmeta['header']
    require(header['n'] == NQ+NFIT and header['d'] == 100 and
            header['bytes'] == header['n']*404, 'P0 GT parent shape mismatch')
    require(rows == NQ and audit_ds['pilot']['row_range'] == [0, rows] and
            audit_ds['pilot']['n'] == rows, 'P0 pilot range mismatch')
    path = Path(fmeta['path']).resolve()
    require(path.stat().st_size == header['bytes'], 'GT parent size changed')
    physical_bytes = rows*404
    with path.open('rb', buffering=0) as f:
        raw = f.read(physical_bytes)
    require(len(raw) == physical_bytes, 'Short pilot GT prefix read')
    records = np.frombuffer(raw, dtype='<i4').reshape(rows, 101)
    require(np.all(records[:, 0] == 100), 'Invalid pilot per-record GT header')
    values = np.ascontiguousarray(records[:, 1:])
    actual_hash = hashlib.sha256(values.tobytes()).hexdigest()
    require(actual_hash == audit_ds['pilot']['gt_values_sha256'], 'P0 full pilot top100 value SHA mismatch')
    gt = values[:, :K].copy()
    validate_gt10(gt, rows, nodes)
    return gt, {'path': str(path), 'physical_records_read': [0, rows], 'physical_bytes_read': physical_bytes,
                'parent_bytes_stat_only': header['bytes'], 'parent_file_rehashed': False,
                'all_record_headers_verified': True, 'all_top100_values_sha256': actual_hash,
                'used_ranks': [0, K], 'fit_suffix_read': False}


def read_fit_gt10(binding, fit, audit_ds, nodes):
    path = Path(fit['gt10_file']).resolve()
    require(path.stat().st_size == NFIT*K*4, 'Extracted fit GT10 byte shape mismatch')
    require(sha(path) == fit['gt10_sha256'], 'Extracted fit GT10 SHA mismatch')
    gt = np.fromfile(path, dtype='<i4').reshape(NFIT, K)
    validate_gt10(gt, NFIT, nodes)
    require(fit['fit_gt_values_sha256'] == audit_ds['fit']['gt_values_sha256'], 'Fit full top100 identity mismatch')
    return gt, {'fit_manifest': binding, 'gt10': {'path': str(path), 'sha256': fit['gt10_sha256']},
                'physical_bytes_read_values': NFIT*K*4, 'additional_hash_read_bytes': NFIT*K*4,
                'row_range': [NQ, NQ+NFIT], 'full_top100_fit_values_sha256_from_audited_manifest': fit['fit_gt_values_sha256'],
                'full_fit_parent_GT_read': False, 'unique_10_targets_each_row': True}


def oracle_metrics(labels, gt, seen):
    """The same global GT top4 defines full/seen/unseen coverage."""
    nq = len(gt)
    leaves = labels[gt]
    counts = np.zeros((nq, REGIONS), dtype=np.int16)
    np.add.at(counts, (np.arange(nq)[:, None], leaves), 1)
    top4 = np.argsort(-counts, axis=1, kind='stable')[:, :4].astype(np.uint16)
    topcounts = np.take_along_axis(counts, top4, axis=1)
    covered = topcounts.sum(axis=1).astype(np.int16)
    selected = np.any(leaves[:, :, None] == top4[:, None, :], axis=2)
    require(np.array_equal(selected.sum(axis=1), covered), 'Top4 absolute coverage reconstruction failed')
    subset = np.zeros_like(counts)
    np.add.at(subset, (np.arange(nq)[:, None], leaves), seen.astype(np.int16))
    covered_seen = (selected & seen).sum(axis=1).astype(np.int16)
    covered_unseen = (selected & ~seen).sum(axis=1).astype(np.int16)
    require(np.array_equal(covered_seen+covered_unseen, covered), 'Coverage support contributions fail exact decomposition')
    return {'D': np.count_nonzero(counts, axis=1).astype(np.int16), 'covered': covered,
            'covered_seen': covered_seen, 'covered_unseen': covered_unseen,
            'D_seen': np.count_nonzero(subset, axis=1).astype(np.int16),
            'D_unseen': np.count_nonzero(counts-subset, axis=1).astype(np.int16),
            'top4': top4, 'conditional_weights': topcounts/covered[:, None]}


def mean_or_null(values):
    return float(np.mean(values)) if len(values) else None


def ratio_or_null(numerator, denominator):
    return numerator/denominator if denominator else None


def histogram(values, lo, hi):
    require(np.all((values >= lo) & (values <= hi)), 'Histogram value outside fixed bins')
    return [{'value': i, 'queries': int(np.count_nonzero(values == i))} for i in range(lo, hi+1)]


def metric_summary(metrics, seen_count, mask):
    nq = int(np.count_nonzero(mask))
    seen_slots = int(seen_count[mask].sum())
    unseen_slots = K*nq-seen_slots
    c, cs, cu = (metrics[k][mask] for k in ('covered', 'covered_seen', 'covered_unseen'))
    d = metrics['D'][mask]
    require(int(cs.sum()+cu.sum()) == int(c.sum()), 'Aggregate M4 decomposition failed')
    return {'queries': nq, 'seen_target_slots': seen_slots, 'unseen_target_slots': unseen_slots,
            'mean_distinct_leaves': mean_or_null(d), 'mean_normalized_fragmentation': mean_or_null((d-1)/9),
            'mean_M4_absolute': mean_or_null(c/K), 'mean_M4_seen_contribution': mean_or_null(cs/K),
            'mean_M4_unseen_contribution': mean_or_null(cu/K),
            'seen_conditional_target_coverage': ratio_or_null(int(cs.sum()), seen_slots),
            'unseen_conditional_target_coverage': ratio_or_null(int(cu.sum()), unseen_slots),
            'mean_D_seen_queries_with_seen_targets': mean_or_null(metrics['D_seen'][mask & (seen_count > 0)]),
            'mean_D_unseen_queries_with_unseen_targets': mean_or_null(metrics['D_unseen'][mask & (seen_count < K)]),
            'distinct_leaf_histogram': histogram(d, 1, K), 'covered_target_count_histogram': histogram(c, 0, K)}


def signed_summary(values):
    return {'mean_candidate_minus_reference': mean_or_null(values),
            'positive_queries': int(np.count_nonzero(values > 0)),
            'negative_queries': int(np.count_nonzero(values < 0)),
            'equal_queries': int(np.count_nonzero(values == 0))}


def metric_delta(candidate, reference, seen_count, mask):
    result = {'queries': int(mask.sum())}
    for key in ('D', 'covered', 'covered_seen', 'covered_unseen', 'D_seen', 'D_unseen'):
        result[key] = signed_summary((candidate[key]-reference[key])[mask])
    result['mean_M4_delta'] = mean_or_null((candidate['covered']-reference['covered'])[mask]/K)
    result['mean_normalized_fragmentation_delta'] = mean_or_null((candidate['D']-reference['D'])[mask]/9)
    cs = int((candidate['covered_seen']-reference['covered_seen'])[mask].sum())
    cu = int((candidate['covered_unseen']-reference['covered_unseen'])[mask].sum())
    result['seen_conditional_target_coverage_delta'] = ratio_or_null(cs, int(seen_count[mask].sum()))
    result['unseen_conditional_target_coverage_delta'] = ratio_or_null(cu, int((K-seen_count[mask]).sum()))
    return result


def structure_summaries(metrics, seen_count):
    allq = np.ones(len(seen_count), dtype=bool)
    paired = (('lambda0_final', 'common_initial'), ('lambda1_final', 'common_initial'),
              ('lambda1_final', 'lambda0_final'))
    result = {'structures': {s: metric_summary(metrics[s], seen_count, allq) for s in STRUCTURES},
              'contrasts': [{'candidate': c, 'reference': r, **metric_delta(metrics[c], metrics[r], seen_count, allq)}
                            for c, r in paired]}
    result['k_seen_strata'] = []
    for k in range(K+1):
        mask = seen_count == k
        result['k_seen_strata'].append({'k_seen': k, 'queries': int(mask.sum()),
            'structures': {s: metric_summary(metrics[s], seen_count, mask) for s in STRUCTURES},
            'contrasts': [{'candidate': c, 'reference': r, **metric_delta(metrics[c], metrics[r], seen_count, mask)}
                          for c, r in paired]})
    require(sum(x['queries'] for x in result['k_seen_strata']) == len(seen_count), 'Strata lost queries')
    return result


def movement_flags(labels):
    initial = labels['common_initial']
    for lam in (0, 1):
        first, final = labels[f'lambda{lam}_pass1'], labels[f'lambda{lam}_final']
        yield f'lambda{lam}_final_leaf_changed_from_initial', final != initial
        yield f'lambda{lam}_any_pass_leaf_changed', (first != initial) | (final != first)
        yield f'lambda{lam}_final_coarse_changed_from_initial', final//16 != initial//16
        yield f'lambda{lam}_any_pass_coarse_changed', (first//16 != initial//16) | (final//16 != first//16)
    yield 'final_lambda1_vs_lambda0_leaf_difference', labels['lambda1_final'] != labels['lambda0_final']
    yield 'final_lambda1_vs_lambda0_coarse_difference', labels['lambda1_final']//16 != labels['lambda0_final']//16


def population_summary(labels, frequency, pilot_gt):
    seen = frequency > 0
    pseen = seen[pilot_gt]
    populations = {'all': len(seen), 'seen': int(seen.sum()), 'unseen': int((~seen).sum())}
    slots = {'all': int(pilot_gt.size), 'seen': int(pseen.sum()), 'unseen': int((~pseen).sum())}
    result = {'definition': 'Unique base nodes and pilot GT10 target slots have separate denominators.',
              'unique_node_denominators': populations, 'pilot_target_slot_denominators': slots,
              'sum_fit_target_occurrences': int(frequency.sum()), 'maximum_fit_query_occurrences_of_one_node': int(frequency.max()),
              'movements': {}}
    require(int(frequency.sum()) == NFIT*K, 'Fit support occurrence total mismatch')
    for name, flag in movement_flags(labels):
        deadline()
        node_counts = {'all': int(flag.sum()), 'seen': int(np.count_nonzero(flag & seen)),
                       'unseen': int(np.count_nonzero(flag & ~seen))}
        pf = flag[pilot_gt]
        slot_counts = {'all': int(pf.sum()), 'seen': int(np.count_nonzero(pf & pseen)),
                       'unseen': int(np.count_nonzero(pf & ~pseen))}
        require(node_counts['seen']+node_counts['unseen'] == node_counts['all'] and
                slot_counts['seen']+slot_counts['unseen'] == slot_counts['all'], 'Movement support decomposition failed')
        result['movements'][name] = {
            'unique_nodes': {g: {'changed': node_counts[g], 'denominator': populations[g],
                                 'rate': ratio_or_null(node_counts[g], populations[g])} for g in populations},
            'pilot_target_slots': {g: {'changed': slot_counts[g], 'denominator': slots[g],
                                       'rate': ratio_or_null(slot_counts[g], slots[g])} for g in slots}}
    return result


def route_signature(row):
    return (row['fast_anchor_id'], row['shared_seed'], row['actual_entry_count'],
            tuple(row['entry_ids']), tuple(row['regions']), tuple(row['weights']))


def parse_oracle_batch(batch, gt, seen, expected_oracle, nodes):
    require(batch['method'] in METHODS and batch['round'] == 0 and batch['search_L'] in LS,
            'Not a registered oracle count cell')
    rows = batch['per_query']
    require(len(rows) == len(gt) and [r['query_id'] for r in rows] == list(range(len(gt))), 'Count query alignment mismatch')
    ids = np.empty((len(rows), K), dtype=np.int64)
    counters = {key: np.empty(len(rows), dtype=np.int64) for key in COUNTERS}
    routes = []
    for q, row in enumerate(rows):
        if q % 1024 == 0:
            deadline()
        require(isinstance(row['result_ids'], list) and len(row['result_ids']) == K and
                all(type(v) is int and -1 <= v < nodes for v in row['result_ids']), 'Invalid saved top10 result IDs')
        valid = [v for v in row['result_ids'] if v >= 0]
        require(len(valid) == len(set(valid)), 'Duplicate saved valid result ID')
        ids[q] = row['result_ids']
        require(row['regions'] == expected_oracle['top4'][q].tolist(), 'Saved oracle regions differ from full GT10 counts/order')
        weights = np.asarray(row['weights'], dtype=float)
        require(weights.shape == (4,) and np.all(np.isfinite(weights)) and
                np.allclose(weights, expected_oracle['conditional_weights'][q], rtol=0, atol=1e-12),
                'Saved oracle conditional top4 weights differ')
        for key in COUNTERS:
            require(type(row[key]) is int and row[key] >= 0, 'Invalid measured oracle counter: '+key)
            counters[key][q] = row[key]
        require(row['total_ndc'] == row['routing_ndc']+row['graph_ndc'] and
                row['total_mac'] == row['routing_mac']+row['graph_mac'], 'Counter additive identity differs')
        routes.append(route_signature(row))
    hits = np.any(gt[:, :, None] == ids[:, None, :], axis=2)
    total = hits.sum(axis=1).astype(np.int16)
    saved_recall = np.asarray([r['recall'] for r in rows], dtype=float)
    require(np.all(np.isfinite(saved_recall)) and np.allclose(saved_recall, total/K, rtol=0, atol=1e-12),
            'Saved Recall differs from actual GT10/result ID intersection')
    require(abs(batch['mean_recall']-float(np.mean(total/K))) < 1e-10, 'Batch mean Recall differs from reconstructed hits')
    hs, hu = (hits & seen).sum(axis=1).astype(np.int16), (hits & ~seen).sum(axis=1).astype(np.int16)
    require(np.array_equal(hs+hu, total), 'Seen/unseen saved hits fail exact decomposition')
    return {'hits': total, 'hits_seen': hs, 'hits_unseen': hu, **counters}, routes


def search_delta(candidate, reference, seen_count, mask):
    nq = int(mask.sum())
    diffs = {k: candidate[k]-reference[k] for k in ('hits', 'hits_seen', 'hits_unseen')}
    require(np.array_equal(diffs['hits_seen']+diffs['hits_unseen'], diffs['hits']), 'Paired hit decomposition failed')
    seen_slots, unseen_slots = int(seen_count[mask].sum()), int((K-seen_count[mask]).sum())
    d = diffs['hits'][mask]
    result = {'queries': nq, 'seen_target_slots': seen_slots, 'unseen_target_slots': unseen_slots,
              'recall_delta_pp': mean_or_null(d*100/K),
              'seen_recall_contribution_delta_pp': mean_or_null(diffs['hits_seen'][mask]*100/K),
              'unseen_recall_contribution_delta_pp': mean_or_null(diffs['hits_unseen'][mask]*100/K),
              'seen_conditional_target_hit_delta': ratio_or_null(int(diffs['hits_seen'][mask].sum()), seen_slots),
              'unseen_conditional_target_hit_delta': ratio_or_null(int(diffs['hits_unseen'][mask].sum()), unseen_slots),
              'query_improved': int(np.count_nonzero(d > 0)), 'query_harmed': int(np.count_nonzero(d < 0)),
              'query_equal': int(np.count_nonzero(d == 0)),
              'counter_attribution': 'Oracle per-query counters; none allocated to seen/unseen target groups.'}
    result['mean_counter_deltas'] = {key: mean_or_null((candidate[key]-reference[key])[mask]) for key in COUNTERS}
    for field in ('hits_seen', 'hits_unseen'):
        result[field+'_query_signs'] = signed_summary(diffs[field][mask])
    return result


def summarize_search(records, seen_count, main_ds):
    allq = np.ones(len(seen_count), dtype=bool)
    main = {(r['L'], r['contrast']): r for r in main_ds['fixed_comparisons']}
    require(len(main) == 8*len(LS), 'Completed main comparison coverage differs')
    result = []
    for idx, (name, cm, method, rm, refmethod) in enumerate(CONTRASTS):
        for l in LS:
            c, r = records[(cm, method, l)], records[(rm, refmethod, l)]
            overall = search_delta(c, r, seen_count, allq)
            if idx < 8:
                saved = main[(l, name)]
                expect(saved, {'candidate_model': cm, 'candidate_method': method, 'reference_model': rm,
                               'reference_method': refmethod}, 'Original fixed contrast identity')
                require(abs(saved['recall_delta_pp']-overall['recall_delta_pp']) < 1e-10,
                        'Reconstructed original paired mean differs from completed P3 analysis')
                for key in ('query_improved', 'query_harmed', 'query_equal'):
                    require(saved[key] == overall[key], 'Original fixed contrast query signs differ')
                for key in ('graph_ndc', 'total_ndc', 'total_mac'):
                    require(abs(saved['mean_'+key+'_delta']-overall['mean_counter_deltas'][key]) < 1e-7,
                            'Original fixed contrast counter mean differs')
            result.append({'contrast': name, 'L': l, 'candidate_model': cm, 'candidate_method': method,
                           'reference_model': rm, 'reference_method': refmethod,
                           'scope': 'ORIGINAL_FIXED_P3_CONTRAST' if idx < 8 else 'PREREGISTERED_POST_NOGO_DESCRIPTIVE_UNIFIED_CONTRAST',
                           'overall': overall,
                           'k_seen_strata': [{'k_seen': k, **search_delta(c, r, seen_count, seen_count == k)} for k in range(K+1)]})
    require(len(result) == 10*len(LS), 'Post-NOGO contrast coverage differs')
    return result


def preflight(protocol_path, audit_path):
    """Only bound JSON metadata, before any GT, labels, or count-file reads."""
    require(sha(protocol_path) == PROTOCOL_SHA, 'Diagnostic protocol differs from frozen preregistration')
    protocol = read_json(protocol_path)
    expect(protocol, {'stage': 'P3_POST_NOGO_DIAGNOSIS',
                      'status': 'PREREGISTERED_BEFORE_DIAGNOSTIC_IMPLEMENTATION_AND_NEW_DATA_READS',
                      'datasets': list(DATASET_N), 'fit_range': [NQ, NQ+NFIT], 'pilot_range': [0, NQ],
                      'structures': list(STRUCTURES), 'method_revision_increment': 0, 'P4_authorized': False,
                      'new_model_or_auxgraph_authorized': False}, 'Frozen diagnostic protocol')
    require(protocol['P3_protocol']['sha256'] == P3_PROTOCOL_SHA, 'Upstream P3 protocol identity differs')
    bound_json(protocol['P3_protocol'])
    gate = bound_json(protocol['upstream_P3'])
    expect(gate, {'stage': 'P3', 'status': 'NOPASS', 'decision': 'NO_GO_P3_SEARCH_TRANSFER',
                  'P4_P8_authorized': False, 'validation_heldout_authorized': False}, 'Upstream P3 NOPASS gate')
    require(gate['protocol'] == protocol['P3_protocol'] and protocol['analysis'] in gate['evidence'] and
            protocol['structure_analysis'] in gate['evidence'], 'Diagnostic inputs not bound to NOPASS evidence')
    main, structure = bound_json(protocol['analysis']), bound_json(protocol['structure_analysis'])
    require(main['status'] == structure['status'] == 'COMPLETE', 'Both completed analyses required')
    audit_binding = desc(audit_path)
    audit = read_json(audit_path)
    expect(audit, {'status': 'PASS_INPUT_CONTRACT', 'heldout_accessed': False}, 'P0 audit')
    main_map, structure_map, audit_map = map(dataset_map, (main, structure, audit))
    prepared = {}
    for dataset, nodes in DATASET_N.items():
        deadline()
        md, sd, ad = main_map[dataset], structure_map[dataset], audit_map[dataset]
        ev = md['evidence']
        require(ev['audit'] == audit_binding and ev['protocol'] == protocol['P3_protocol'], 'Dataset analysis audit/protocol binding differs')
        require(ad['graph']['header']['n'] == nodes and ad['fit']['row_range'] == [NQ, NQ+NFIT] and ad['fit']['n'] == NFIT,
                'P0 frozen base or fit range differs')
        require(set(ev['models']) == set(MODELS), 'Exactly four frozen model families required')
        top = bound_json(sd['partition_manifest'])
        expect(top, {'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset, 'nodes': nodes, 'regions': REGIONS,
                     'protocol_sha256': P3_PROTOCOL_SHA, 'input_audit_sha256': audit_binding['sha256']}, 'Partition metadata')
        labels_desc = {'common_initial': top['initialization']['labels']}
        for lam in (0, 1):
            branch = top[f'lambda{lam}']
            require(branch['status'] == 'COMPLETE' and len(branch['passes']) == 2 and
                    branch['initial_labels_sha256'] == top['initial_labels_sha256'], 'Branch/common initialization differs')
            labels_desc[f'lambda{lam}_pass1'] = branch['passes'][0]['labels']
            labels_desc[f'lambda{lam}_final'] = branch['passes'][1]['labels']
        require(top['initial_labels_sha256'] == sd['common_initial_labels_sha256'] == ev['common_initial_labels_sha256'] ==
                labels_desc['common_initial']['sha256'], 'Common initialization SHA differs across analyses')
        audited_labels = {(str(Path(x['path']).resolve()), x['sha256'], x['rows'], x['regions']) for x in sd['saved_label_evidence']}
        for name, label in labels_desc.items():
            expect(label, {'rows': nodes, 'bytes': 2*nodes, 'dtype': 'little-endian uint16', 'header': False}, 'Label descriptor '+name)
            require((str(Path(label['path']).resolve()), label['sha256'], nodes, REGIONS) in audited_labels,
                    'Label is absent from completed structure audit')
            require(Path(label['path']).resolve().is_relative_to(Path(sd['partition_manifest']['path']).resolve().parent),
                    'Label escapes bound partition tree')
        models, fit_bindings = {}, []
        for name in MODELS:
            item = ev['models'][name]
            model = bound_json(item['model'])
            branch, rule = name.split('_', 1)
            expected = {'schema_version': 2, 'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset, 'model_name': name,
                        'lambda': int(branch[-1]), 'portal_rule': rule, 'oracle_diagnostic_only': True, 'region_count': REGIONS,
                        'coarse_count': 16, 'leaves_per_coarse': 16, 'active_regions': 4, 'portals_per_region': 3,
                        'total_portals': 768, 'fit_range': [NQ, NQ+NFIT], 'fit_count': NFIT, 'cpu_only': True,
                        'pilot_accessed': False, 'validation_accessed': False, 'heldout_accessed': False,
                        'base_nodes': nodes, 'protocol_sha256': P3_PROTOCOL_SHA, 'input_audit_sha256': audit_binding['sha256'],
                        'graph_sha256': ad['graph']['sha256'], 'fit_query_values_sha256': ad['fit']['query_values_sha256'],
                        'fit_gt_values_sha256': ad['fit']['gt_values_sha256']}
            expect(model, expected, 'Frozen model '+name)
            require(model['protocol'] == protocol['P3_protocol'] and model['audit'] == audit_binding, 'Explicit model audit/protocol binding differs')
            lab = labels_desc[branch+'_final']
            require(Path(model['labels_file']).resolve() == Path(lab['path']).resolve() and
                    model['labels_sha256'] == lab['sha256'] and item['labels'] == {'path': lab['path'], 'sha256': lab['sha256']},
                    'Model final label identity differs')
            require(item['partition_manifest'] == model['partition_manifest'] and
                    bound_json(model['partition_manifest']) == top[branch], 'Model branch manifest differs from top-level partition')
            models[name] = model
            fit_bindings.append(model['fit_manifest'])
        require(all(x == fit_bindings[0] for x in fit_bindings), 'Models do not share frozen fit extraction')
        fit = bound_json(fit_bindings[0])
        expect(fit, {'status': 'COMPLETE', 'stage': 'P3', 'dataset': dataset, 'fit_range': [NQ, NQ+NFIT],
                     'fit_count': NFIT, 'pilot_accessed': False, 'heldout_accessed': False,
                     'input_audit_sha256': audit_binding['sha256'], 'protocol_sha256': P3_PROTOCOL_SHA,
                     'fit_gt_values_sha256': ad['fit']['gt_values_sha256']}, 'Fit extraction manifest')
        require(top['fit_manifest_sha256'] == fit_bindings[0]['sha256'] and
                all(model['gt10_sha256'] == fit['gt10_sha256'] for model in models.values()), 'Partition/model fit extraction identity differs')
        prepared[dataset] = {'main': md, 'structure': sd, 'audit': ad, 'top': top, 'labels': labels_desc,
                             'models': models, 'fit_binding': fit_bindings[0], 'fit': fit}
    return protocol, audit_binding, prepared


def load_labels(prepared, nodes):
    labels, evidence = {}, {}
    for name, binding in prepared['labels'].items():
        deadline()
        path = bound_path(binding)
        require(path.stat().st_size == 2*nodes, 'Saved label byte shape mismatch')
        arr = np.fromfile(path, dtype='<u2')
        require(len(arr) == nodes and int(arr.max()) < REGIONS, 'Saved label ID outside fixed hierarchy')
        sizes = np.bincount(arr, minlength=REGIONS)
        require(int(sizes.min()) >= 3 and int(sizes.max()) <= 6*nodes//(5*REGIONS) and
                int(sizes.reshape(16, 16).sum(axis=1).max()) <= 6*nodes//(5*16), 'Saved labels violate frozen capacities or minimum3')
        labels[name] = arr
        evidence[name] = {'path': str(path), 'sha256': binding['sha256'], 'rows': nodes, 'bytes': 2*nodes}
    return labels, evidence


def load_search(prepared, pilot_gt, seen, metrics, nodes):
    records, evidence = {}, {}
    for name in MODELS:
        deadline()
        model = prepared['models'][name]
        binding = prepared['main']['evidence']['models'][name]
        artifact = bound_json(binding['count'])
        expected = {'status': 'COMPLETE', 'stage': 'P3', 'dataset': model['dataset'], 'split': 'pilot',
                    'source_query_type': 'drl_train', 'source_query_range': [0, NQ], 'num_queries': NQ,
                    'measurement': 'count', 'cpu_only': True, 'threads': 16, 'metric': 'ip', 'top_k': K,
                    'search_Ls': list(LS), 'rounds': 1, 'heldout_accessed': False, 'oracle_is_deployment': False,
                    'region_count': REGIONS, 'portals_per_region': 3, 'base_nodes': nodes,
                    'model_manifest': model, 'model_sha256': binding['model']['sha256']}
        expect(artifact, expected, 'Saved count '+name)
        require(Path(artifact['model_file']).resolve() == Path(binding['model']['path']).resolve(), 'Saved count model path differs')
        require(Path(artifact['index_file']).resolve() == Path(prepared['audit']['graph']['path']).resolve(), 'Saved count graph path differs')
        batches = {(b['search_L'], b['method'], b['round']): b for b in artifact['results']}
        require(len(batches) == len(artifact['results']) == 6 and set(batches) ==
                {(l, m, 0) for l in LS for m in ('fast',)+METHODS}, 'Saved count cell coverage differs')
        expected_oracle = metrics[name.split('_', 1)[0]+'_final']
        routes_ref = None
        for l in LS:
            for method in METHODS:
                values, routes = parse_oracle_batch(batches[(l, method, 0)], pilot_gt, seen, expected_oracle, nodes)
                if routes_ref is None:
                    routes_ref = routes
                else:
                    require(routes == routes_ref, 'Same-model queue/L controls change actual route')
                records[(name, method, l)] = values
        evidence[name] = {'model': binding['model'], 'count': binding['count'], 'labels': binding['labels'],
                          'oracle_rows_verified': NQ*4, 'actual_routes_equal_across_queue_and_L': True,
                          'full_GT_top4_regions_conditional_weights_verified': True, 'Fast_rows_analyzed': False}
        del artifact, batches, routes_ref
    return records, evidence


def save_npz(path, arrays):
    with Path(path).open('xb') as f:
        np.savez_compressed(f, **arrays)
    return {**desc(path), 'bytes': Path(path).stat().st_size, 'arrays': list(arrays), 'raw_GT_or_result_ID_arrays': False}


def diagnose_dataset(dataset, prepared, output):
    started = time.monotonic()
    nodes = DATASET_N[dataset]
    labels, label_evidence = load_labels(prepared, nodes)
    fit_gt, fit_evidence = read_fit_gt10(prepared['fit_binding'], prepared['fit'], prepared['audit'], nodes)
    pilot_gt, pilot_evidence = read_pilot_prefix(prepared['audit'], NQ, nodes)
    frequency = np.bincount(fit_gt.ravel(), minlength=nodes).astype(np.uint32)
    fit_seen, pilot_seen = frequency[fit_gt] > 0, frequency[pilot_gt] > 0
    require(np.all(fit_seen), 'Fit targets must all be seen by definition')
    fit_metrics = {s: oracle_metrics(labels[s], fit_gt, fit_seen) for s in STRUCTURES}
    pilot_metrics = {s: oracle_metrics(labels[s], pilot_gt, pilot_seen) for s in STRUCTURES}
    # Independently recheck fit fragmentation against the saved full-recomputation evidence.
    objectives = {'common_initial': prepared['top']['initial_objective'],
                  'lambda0_final': prepared['top']['lambda0']['passes'][1]['objective'],
                  'lambda1_final': prepared['top']['lambda1']['passes'][1]['objective']}
    for name, obj in objectives.items():
        require(int((fit_metrics[name]['D']-1).sum()) == obj['S_fit_distinct_leaf_minus_one'],
                'Reconstructed fit fragmentation differs from accepted full structure recomputation')
    population = population_summary(labels, frequency, pilot_gt)
    records, search_evidence = load_search(prepared, pilot_gt, pilot_seen, pilot_metrics, nodes)
    fit_seen_count, pilot_seen_count = fit_seen.sum(axis=1), pilot_seen.sum(axis=1)
    searches = summarize_search(records, pilot_seen_count, prepared['main'])
    arrays = {'query_id': np.arange(NQ, NQ+NFIT, dtype=np.int32), 'k_seen': fit_seen_count.astype(np.int16)}
    for s in STRUCTURES:
        for field in ('D', 'covered', 'covered_seen', 'covered_unseen', 'D_seen', 'D_unseen'):
            arrays[s+'__'+field] = fit_metrics[s][field]
    fit_npz = save_npz(output/'fit_metrics.npz', arrays)
    arrays = {'query_id': np.arange(NQ, dtype=np.int32), 'k_seen': pilot_seen_count.astype(np.int16)}
    for s in STRUCTURES:
        for field in ('D', 'covered', 'covered_seen', 'covered_unseen', 'D_seen', 'D_unseen'):
            arrays[s+'__'+field] = pilot_metrics[s][field]
    for (model, method, l), values in records.items():
        for field, value in values.items():
            arrays[f'{model}__{method}__L{l}__{field}'] = value
    pilot_npz = save_npz(output/'pilot_metrics_and_search.npz', arrays)
    return {'schema_version': 1, 'status': 'COMPLETE', 'stage': 'P3_POST_NOGO_TARGET_GENERALIZATION', 'dataset': dataset,
            'nodes': nodes, 'fit_queries': NFIT, 'pilot_queries': NQ,
            'support_definition': 'f(u)=number of fit GT10 query rows containing u; seen iff f(u)>0. Each row has unique10 IDs.',
            'support_denominator_caution': 'Unique base nodes, query means and target-slot ratios are reported separately. Fit unseen targets cannot exist.',
            'coverage_definition': 'Absolute M4=covered GT10 targets/10; seen/unseen use this same full-GT top4. Saved weights condition on selected4.',
            'subset_distinct_count_caution': 'D_seen and D_unseen may overlap in leaves and are not additive; compare only with group target counts.',
            'paired_direction': 'Every delta is candidate minus reference. Smaller D/fragmentation and larger M4/Recall have opposite favorable signs.',
            'fit': structure_summaries(fit_metrics, fit_seen_count), 'pilot': structure_summaries(pilot_metrics, pilot_seen_count),
            'node_population_and_pilot_target_slots': population, 'search_contrasts': searches,
            'evidence': {'partition_manifest': prepared['structure']['partition_manifest'], 'saved_labels_rehashed': label_evidence,
                         'fit_GT': fit_evidence, 'pilot_GT': pilot_evidence, 'search': search_evidence,
                         'fit_fragmentation_recomputed_matches_saved_full_objective': True},
            'artifacts': {'fit_per_query': fit_npz, 'pilot_per_query': pilot_npz},
            'no_new_CI_or_gate': True, 'P3_gate_status_unchanged': 'NOPASS', 'wall_seconds': time.monotonic()-started}


def run(args):
    started = time.monotonic()
    deadline()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    invocation = {'schema_version': 1, 'status': 'INCOMPLETE', 'stage': 'P3_POST_NOGO_TARGET_GENERALIZATION',
                  'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv,
                  'script': desc(__file__), 'protocol': desc(args.protocol), 'audit': desc(args.audit),
                  'cpu_only': True, 'output': str(output)}
    write_new(output/'invocation.json', invocation)
    try:
        protocol, audit_binding, prepared = preflight(args.protocol, args.audit)
        results = []
        for dataset in DATASET_N:
            deadline()
            directory = output/dataset
            directory.mkdir()
            result = diagnose_dataset(dataset, prepared[dataset], directory)
            write_new(directory/'diagnosis.json', result)
            results.append(result)
            print(json.dumps({'dataset': dataset, 'status': 'COMPLETE', 'wall_seconds': result['wall_seconds']}), flush=True)
        result = {**invocation, 'status': 'COMPLETE', 'protocol': desc(args.protocol), 'audit': audit_binding,
                  'upstream_P3': protocol['upstream_P3'], 'analysis': protocol['analysis'],
                  'structure_analysis': protocol['structure_analysis'], 'datasets': results,
                  'scope': 'Frozen post-NOGO descriptive target generalization; no new CI, selection, refit, gate reopening or connectivity claim.',
                  'limitations': protocol['interpretation_limits']+[
                      'Observed support differences are not evidence of query leakage; fit and pilot queries remain disjoint.',
                      'Fit-target support correlates with density/popularity; subgroup differences do not isolate a causal effect.',
                      'This is oracle routing, not a learned predictor; no prediction-generalization diagnosis is available.',
                      'Seen/unseen shares use full-GT top4 and additive target-slot contributions; no independently selected subgroup oracle.',
                      'Original graph and query/base vectors were not read. Label capacity and fit fragmentation were rechecked; graph cut inherited from bound completed structure audit.'],
                  'access': {'pilot_GT_prefix_only': True, 'existing_fit_GT10_only': True, 'validation': False, 'heldout': False,
                             'query_vectors': False, 'base_vectors': False, 'original_graph': False, 'ANN': False, 'refit': False},
                  'P3_gate_status_unchanged': 'NOPASS', 'new_CI_computed': False, 'automatic_GO': False,
                  'P4_authorized': False, 'wall_seconds': time.monotonic()-started}
        write_new(output/'diagnosis.json', result)
        write_new(output/'complete.json', {'status': 'COMPLETE', 'diagnosis': desc(output/'diagnosis.json'),
                                          'datasets': list(DATASET_N), 'P3_gate_status_unchanged': 'NOPASS'})
        return 0
    except BaseException as exc:
        write_new(output/'failure.json', {'status': 'INCOMPLETE', 'error_type': type(exc).__name__, 'error': str(exc),
                                         'wall_seconds': time.monotonic()-started, 'P3_gate_status_unchanged': 'NOPASS'})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', required=True, help='Frozen p3/diagnosis_protocol_v1.json')
    parser.add_argument('--audit', required=True, help='P0 full_audit/audit.json bound by completed P3 analysis')
    parser.add_argument('--output', required=True, help='New directory; never overwrites prior artifacts')
    return run(parser.parse_args())


if __name__ == '__main__':
    raise SystemExit(main())
