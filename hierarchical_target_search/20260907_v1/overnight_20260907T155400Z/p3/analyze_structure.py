#!/usr/bin/env python3
"""Audit saved P3 hierarchy labels/objective evidence without graph or GT reads."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

import numpy as np

DATASET_N = {'webvid2_5m_light_v1': 2505000, 'yandex_t2i_official10M_ip_v1': 10000000}
FIT_COUNT = 20000
PROTOCOL_SHA256 = 'fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f'
PARTITION_SOURCE_SHA256 = '78cd134726c61fda5b722887262b33176989b1c40163e00af7a7bc52c76a81b5'
SOFT_DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()


def require(yes, message):
    if not yes:
        raise ValueError(message)


def check_deadline():
    require(time.time() < SOFT_DEADLINE, 'P3 evidence analysis closed at soft deadline')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_new(path, obj):
    with Path(path).open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def uint(value, name):
    require(type(value) is int and value >= 0, 'Invalid unsigned integer: '+name)
    return value


def sint(value, name):
    require(type(value) is int, 'Invalid signed integer: '+name)
    return value


def digest(value, name):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None,
            'Invalid SHA256: '+name)


def finite_seconds(value, name):
    require(isinstance(value, (int, float)) and math.isfinite(value) and value >= 0,
            'Invalid measured seconds: '+name)
    return float(value)


def close(actual, expected, name):
    require(isinstance(actual, (int, float)) and math.isfinite(actual) and
            math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-15), 'Derived value differs: '+name)


def inside(path, root):
    path = Path(path).resolve()
    require(path.is_relative_to(root.resolve()), 'Saved label/manifest path escapes this partition directory')
    return path


def load_label(record, rows, regions, root, evidence):
    require(record['dtype'] == 'little-endian uint16' and record['header'] is False and
            record['rows'] == rows and record['bytes'] == 2*rows, 'Label shape/dtype differs')
    digest(record['sha256'], 'labels')
    path = inside(record['path'], root)
    require(path.suffix == '.u16' and path.stat().st_size == 2*rows, 'Saved label file size/suffix mismatch')
    actual_sha = sha(path)
    require(actual_sha == record['sha256'], 'Saved label SHA256 mismatch: '+str(path))
    labels = np.fromfile(path, dtype='<u2')
    require(len(labels) == rows and int(labels.min()) >= 0 and int(labels.max()) < regions,
            'Saved label ID outside region count')
    evidence.append({'path': str(path), 'sha256': actual_sha, 'rows': rows, 'regions': regions})
    return labels


def canonical(labels, regions):
    minima = np.full(regions, len(labels), dtype=np.int64)
    np.minimum.at(minima, labels, np.arange(len(labels), dtype=np.int64))
    require(np.all(minima < len(labels)), 'Canonical mapping requires every region nonempty')
    order = np.argsort(minima, kind='stable')
    mapping = np.empty(regions, dtype=np.uint16)
    mapping[order] = np.arange(regions, dtype=np.uint16)
    return mapping[labels]


def label_structure(labels, n):
    require(len(labels) == n, 'Labels do not cover every base node')
    leaf = np.bincount(labels, minlength=256)
    require(len(leaf) == 256, 'Leaf count is not256')
    coarse = leaf.reshape(16, 16).sum(axis=1)
    leaf_cap, coarse_cap = 6*n//(5*256), 6*n//(5*16)
    require(int(leaf.min()) >= 3 and int(leaf.max()) <= leaf_cap and int(coarse.max()) <= coarse_cap,
            'Actual saved labels violate min3 or global leaf/coarse capacities')
    return {'all_nodes_covered': True, 'nodes': n, 'leaf_sizes': leaf.tolist(), 'coarse_sizes': coarse.tolist(),
            'leaf_capacity': leaf_cap, 'coarse_capacity': coarse_cap, 'minimum_leaf_nodes': 3,
            'minimum_actual_leaf_nodes': int(leaf.min()), 'maximum_actual_leaf_nodes': int(leaf.max()),
            'maximum_actual_coarse_nodes': int(coarse.max()), 'violations': [], 'capacity_and_minimum_pass': True}


def validate_structure(saved, actual):
    for key, value in actual.items():
        require(saved[key] == value, 'Saved structure differs from actual labels: '+key)


def validate_objective(obj, n, expected_M=None):
    M = uint(obj['M_original_directed_valid_nonself_slots'], 'M')
    C = uint(obj['C_leaf_directed_crossing_slots'], 'C')
    S = uint(obj['S_fit_distinct_leaf_minus_one'], 'S')
    Q = uint(obj['Q'], 'Q')
    coarse_C = uint(obj['coarse_crossing_slots_report_only'], 'coarse C')
    coarse_S = uint(obj['coarse_S_report_only'], 'coarse S')
    require(0 < M <= 64*n and 0 <= C <= M and Q == FIT_COUNT and 0 <= S <= 9*Q,
            'Original-directed/GT objective counts outside registered bounds')
    require(coarse_C <= C and coarse_S <= S, 'Coarse objective cannot exceed leaf objective')
    if expected_M is not None:
        require(M == expected_M, 'Original graph M changed across snapshots')
    num0, num1, denominator = C*9*Q, C*9*Q+S*M, M*9*Q
    require(obj['lambda0_exact_numerator'] == str(num0) and obj['lambda1_exact_numerator'] == str(num1) and
            obj['exact_common_denominator'] == str(denominator), 'Stored exact objective numerator/denominator mismatch')
    for key, value in {'leaf_cut_fraction': C/M, 'fit_leaf_fragmentation_normalized': S/(9*Q),
                       'mean_fit_distinct_leaf_regions': 1+S/Q, 'J_lambda0': C/M, 'J_lambda1': C/M+S/(9*Q),
                       'coarse_cut_fraction_report_only': coarse_C/M,
                       'mean_fit_distinct_coarse_regions_report_only': 1+coarse_S/Q}.items():
        close(obj[key], value, key)
    return {'M': M, 'C': C, 'S': S, 'Q': Q, 'coarse_C': coarse_C, 'coarse_S': coarse_S,
            'numerator0': num0, 'numerator1': num1, 'denominator': denominator}


def validate_metis(part, labels, cap, minimum, target_numerator, target_denominator):
    count = part['parts']
    require(count == 16 and part['seed'] == 2026090711 and part['ncuts'] == 1 and part['niter'] == 10 and
            part['numbering'] == 0 and part['metis_idx_bits'] == 64 and part['metis_real_bits'] == 32,
            'METIS parameters differ from preregistration')
    require(part['target_ub_rational'] == [target_numerator, target_denominator], 'METIS target rational differs')
    require(part['capacity'] == cap and part['minimum'] == minimum, 'METIS integer capacity/minimum differs')
    sizes = np.bincount(labels, minlength=count)
    require(sizes.tolist() == part['region_sizes'] and int(sizes.min()) >= minimum and int(sizes.max()) <= cap,
            'METIS actual saved region sizes violate registered bound')
    require(part['structure_pass'] is True and part['violations'] == [] and part['effective_bound_pass'] is True,
            'METIS saved structural/ub check failed')
    effective = part['effective_internal_ubfactor']
    require(math.isfinite(effective) and 1 < effective <= target_numerator/target_denominator and
            math.isfinite(part['input_ubvec']) and 1 < part['input_ubvec'] < effective,
            'METIS effective bound is not conservative')
    require(part['library_added_epsilon'] == .0000499, 'Unexpected library epsilon compensation')
    # Match the C library compound assignment: real_t(float64(input)+epsilon).
    require(float(np.float32(float(part['input_ubvec'])+.0000499)) == effective,
            'Saved effective METIS bound differs from library arithmetic')
    require(part['metis_edgecut'] == part['verified_undirected_edgecut'] and part['metis_return_code'] == 1,
            'Saved METIS cut verification/return code failed')
    finite_seconds(part['metis_and_verification_seconds'], 'METIS and cut verification')


def validate_initial(top, root, n, evidence):
    saved = read_json(root/'initial/manifest.json')
    for key, value in top['initialization'].items():
        require(saved[key] == value, 'Top-level and saved initial manifest differ: '+key)
    require(saved['status'] == 'COMPLETE' and saved['canonicalized_once_before_branches'] is True,
            'Common canonical initialization not complete')
    require(saved['regions'] == 256 and saved['coarse_count'] == saved['leaves_per_coarse'] == 16 and saved['nodes'] == n,
            'Common hierarchy dimensions differ')
    for key in ('protocol_sha256', 'input_audit_sha256', 'fit_manifest_sha256', 'source_sha256', 'binary_sha256'):
        require(saved[key] == top[key], 'Initial provenance differs: '+key)
    initial = load_label(saved['labels'], n, 256, root, evidence)
    require(saved['labels_file'] == saved['labels']['path'] and saved['labels_sha256'] == saved['labels']['sha256'] == top['initial_labels_sha256'],
            'Common initial label binding differs')
    actual = label_structure(initial, n); validate_structure(saved['structure'], actual)
    coarse_stats = saved['coarse_metis']
    require(read_json(root/'initial/coarse.json') == coarse_stats, 'Coarse manifest differs from embedded evidence')
    coarse_raw = load_label(coarse_stats['raw_labels'], n, 16, root, evidence)
    coarse = load_label(saved['coarse_canonical_labels'], n, 16, root, evidence)
    require(np.array_equal(coarse, canonical(coarse_raw, 16)), 'Coarse IDs are not canonical ascending minimum base IDs')
    coarse_cap, leaf_cap = 11*n//(10*16), 6*n//(5*256)
    require(saved['coarse_initial_integer_cap'] == coarse_cap, 'Coarse initial integer cap differs')
    validate_metis(coarse_stats, coarse_raw, coarse_cap, 48, 11, 10)
    require(np.array_equal(initial//16, coarse), 'Initial leaves do not belong to saved canonical coarse regions')
    children = saved['children']
    require(len(children) == 16 and [c['coarse_id'] for c in children] == list(range(16)), 'Missing/reordered coarse children')
    for c, child in enumerate(children):
        check_deadline()
        require(read_json(root/f'initial/child_{c:02d}.json') == child, 'Child manifest differs from embedded evidence')
        members = np.flatnonzero(coarse == c)
        child_raw = load_label(child['raw_local_labels'], len(members), 16, root, evidence)
        validate_metis(child, child_raw, leaf_cap, 3, 16*leaf_cap, len(members))
        require(np.array_equal(initial[members], c*16+canonical(child_raw, 16)),
                'Initial leaf IDs do not reconstruct from saved child METIS labels')
    obj = validate_objective(saved['objective'], n)
    require(saved['objective'] == top['initial_objective'], 'Initial full objective differs between saved manifests')
    return initial, obj, saved


def validate_branch(top, root, n, initial, initial_obj, lam, evidence):
    branch = read_json(root/f'lambda{lam}/manifest.json')
    require(branch == top[f'lambda{lam}'], 'Branch and top-level embedded manifest differ')
    require(branch['status'] == 'COMPLETE' and branch['stage'] == 'P3' and branch['lambda'] == lam and
            branch['passes_required'] == branch['passes_completed'] == 2, 'Exactly two completed branch passes required')
    for key in ('dataset','n','nodes','regions','coarse_count','leaves_per_coarse','protocol_sha256','input_audit_sha256',
                'fit_manifest_sha256','fit_gt_values_sha256','input_graph_sha256','source_sha256','binary_sha256','initial_labels_sha256'):
        require(branch[key] == top[key], 'Branch provenance differs: '+key)
    require(branch['same_initial_labels_sha256'] == branch['initial_state_copy_sha256'] == top['initial_labels_sha256'],
            'Lambda branches did not start from the identical saved initialization')
    require(branch['GT_used_for_move_candidates_or_decisions'] is bool(lam) and
            branch['GT_used_for_posthoc_full_structure_metrics'] is True, 'Lambda GT-use contract differs')
    require(branch['initial_objective'] == top['initial_objective'] and len(branch['passes']) == 2, 'Branch initial objective/pass list differs')
    previous, previous_labels = initial_obj, initial
    pass_results = []
    for number, p in enumerate(branch['passes'], 1):
        check_deadline()
        require(read_json(root/f'lambda{lam}/pass{number}.json') == p and p['pass'] == number,
                'Saved pass JSON differs from embedded evidence/order')
        labels = load_label(p['labels'], n, 256, root, evidence)
        structure = label_structure(labels, n); validate_structure(p['structure'], structure)
        current = validate_objective(p['objective'], n, initial_obj['M'])
        moved = uint(p['accepted_moves'], 'accepted moves'); crossed = uint(p['cross_coarse_moves'], 'cross-coarse moves')
        require(p['next_node_cursor'] == n and crossed <= moved <= n, 'Pass did not scan all nodes or invalid move counts')
        require(int(np.count_nonzero(labels != previous_labels)) == moved,
                'Ascending single-scan pass changed-node count differs from accepted moves')
        require(int(np.count_nonzero(labels//16 != previous_labels//16)) == crossed,
                'Actual changed coarse labels differ from cross-coarse move count')
        dc = sint(p['sum_delta_C'], 'sum deltaC')
        require(current['C'] == previous['C']+dc, 'Full C does not equal incremental delta evidence')
        verify = p['full_recompute']
        require(verify['C_matches_incremental'] is True and verify['exact_J_matches_incremental'] is True and
                verify['pass_strict_descent_if_any_move'] is True and p['all_moves_strictly_negative'] is True,
                'Pass independent full-recompute/descent checks did not pass')
        if lam:
            ds = sint(p['sum_delta_S'], 'sum deltaS')
            require(current['S'] == previous['S']+ds and p['GT_S_updated_during_moves'] is True and
                    verify['S_matches_incremental'] is True and verify['GT_per_query_region_counts_match'] is True and
                    verify['lambda0_S_posthoc_only'] is False, 'Lambda1 GT incremental/full evidence mismatch')
        else:
            ds = 0
            require(p['sum_delta_S'] is None and p['GT_S_updated_during_moves'] is False and
                    verify['S_matches_incremental'] is None and verify['GT_per_query_region_counts_match'] is None and
                    verify['lambda0_S_posthoc_only'] is True, 'Lambda0 unexpectedly maintained GT move state')
        exact_delta = dc*9*FIT_COUNT+lam*ds*initial_obj['M']
        require(p['sum_exact_delta_numerator'] == str(exact_delta) and
                current[f'numerator{lam}'] == previous[f'numerator{lam}']+exact_delta,
                'Exact integer objective change mismatch')
        require((moved > 0 and exact_delta < 0) or (moved == 0 and exact_delta == 0), 'Pass violates strict-improvement-only rule')
        pass_results.append({'pass': number, 'accepted_moves': moved, 'cross_coarse_moves': crossed,
                             'labels_sha256': p['labels']['sha256'], 'C': current['C'], 'S': current['S'],
                             'J_at_lambda1': current['numerator1']/current['denominator'],
                             'exact_delta_numerator': str(exact_delta),
                             'refinement_seconds': finite_seconds(p['wall_seconds'], 'pass refinement'),
                             'full_recompute_and_label_snapshot_seconds': finite_seconds(verify['wall_seconds'], 'pass full verification and snapshot')})
        previous, previous_labels = current, labels
    final = branch['passes'][-1]
    require(branch['labels_file'] == final['labels']['path'] and branch['labels_sha256'] == final['labels']['sha256'] and
            branch['labels'] == final['labels'] and branch['final_objective'] == final['objective'] and
            branch['structure'] == final['structure'], 'Final branch alias differs from final completed pass')
    return {'lambda': lam, 'final': previous, 'passes': pass_results,
            'wall_seconds': finite_seconds(branch['wall_seconds'], 'branch wall'),
            'final_labels_sha256': branch['labels_sha256']}


def cost_summary(top, initial, branches):
    csr = top['initializer_CSR']
    csr_cost = {key: finite_seconds(csr[key], key) for key in
                ('count_seconds','fill_seconds','sort_unique_seconds','compact_seconds')}
    coarse = finite_seconds(initial['coarse_metis']['metis_and_verification_seconds'], 'coarse METIS')
    children = [finite_seconds(c['metis_and_verification_seconds'], 'child METIS') for c in initial['children']]
    phases = {'symmetric_CSR_measured_subtotal': sum(csr_cost.values()), 'coarse_METIS_and_cut_verification': coarse,
              'children_METIS_and_cut_verification_sum': sum(children),
              'incoming_CSR': finite_seconds(top['incoming_CSR']['wall_seconds'], 'incoming CSR'),
              'fit_GT10_load_and_validation': finite_seconds(top['fit_gt10_load_validate_seconds'], 'fit GT10 load'),
              'initial_full_objective': finite_seconds(top['initial_objective_seconds'], 'initial full objective'),
              'lambda0_branch': branches[0]['wall_seconds'],
              'GT_incidence_build_for_lambda1': finite_seconds(top['GT_incidence_build_seconds'], 'GT incidence'),
              'lambda1_branch': branches[1]['wall_seconds']}
    total = finite_seconds(top['wall_seconds'], 'partition total')
    residual = total-sum(phases.values())
    require(residual >= -1e-6, 'Nonoverlapping measured phase totals exceed overall wall time')
    branch_detail = []
    for branch in branches:
        refinement = sum(p['refinement_seconds'] for p in branch['passes'])
        verification = sum(p['full_recompute_and_label_snapshot_seconds'] for p in branch['passes'])
        extra = branch['wall_seconds']-refinement-verification
        require(extra >= -1e-6, 'Pass subtotals exceed measured branch wall')
        branch_detail.append({'lambda': branch['lambda'], 'branch_wall_seconds': branch['wall_seconds'],
                              'refinement_seconds': refinement, 'full_recompute_and_label_snapshot_seconds': verification,
                              'other_branch_recording_seconds_by_subtraction': max(0, extra)})
    return {'total_partition_wall_seconds': total, 'peak_rss_kib': uint(top['peak_rss_kib'], 'peak RSS'),
            'nonoverlapping_measured_phase_seconds': phases, 'symmetric_CSR_detail_seconds': csr_cost,
            'child_METIS_and_cut_verification_seconds_in_coarse_ID_order': children, 'branch_detail': branch_detail,
            'full_initializer_wall_seconds': None,
            'full_initializer_missing_reason': 'Induced CSR construction, initial canonicalization and label/report writes were not separately timed.',
            'unitemized_total_seconds_by_subtraction': max(0, residual),
            'unitemized_includes': ['induced CSR construction','initial canonicalization/labels/JSON',
                                  'branch initial copies/hashes and lambda1 GT-count setup','metadata/source/binary IO and other setup'],
            'reused_exact_GT_cost_seconds': None, 'reused_exact_GT_cost_reason': 'Not measured by this partition invocation; not zero.',
            'complete_training_cost_claimed': False}


def analyze_partition(path, protocol_sha, p2_gate_sha):
    path = Path(path).resolve(); root = path.parent; top = read_json(path)
    require(top['status'] == 'COMPLETE' and top['stage'] == 'P3' and top['synthetic'] is False and
            top['hierarchy_correctness_pass'] is True, 'Actual completed P3 partition required')
    dataset = top['dataset']; require(dataset in DATASET_N, 'Unregistered dataset')
    n = DATASET_N[dataset]
    require(top['n'] == top['nodes'] == n and top['regions'] == 256 and top['coarse_count'] == top['leaves_per_coarse'] == 16,
            'P3 fixed dataset/hierarchy shape differs')
    require(top['cpu_only'] is True and top['heldout_accessed'] is False and top['pilot_accessed'] is False and
            top['base_or_graph_copied'] is False and top['search_graph_modified'] is False and top['CSR_saved_to_disk'] is False,
            'CPU/split/frozen-graph contract differs')
    require(top['protocol_sha256'] == protocol_sha and top['source_sha256'] == top['compile_time_source_sha256'] == PARTITION_SOURCE_SHA256,
            'Accepted protocol/compiled partition source binding differs')
    require(top['p2_gate_sha256'] == p2_gate_sha, 'P2 gate differs from the frozen P3 protocol binding')
    for key in ('input_audit_sha256','fit_manifest_sha256','fit_gt_values_sha256','input_graph_sha256',
                'binary_sha256','initial_labels_sha256','p2_gate_sha256','gt10_sha256'):
        digest(top[key], key)
    require(top['fit_range'] == [10000,30000] and top['fit_count'] == FIT_COUNT, 'Fit split differs')
    evidence = []
    initial, initial_obj, initial_manifest = validate_initial(top, root, n, evidence)
    incoming = top['incoming_CSR']; csr = top['initializer_CSR']
    require(incoming['duplicates_and_direction_preserved'] is True and incoming['directed_nonself_slots'] == initial_obj['M'] == csr['nonself_directed_slots'],
            'Original directed denominator differs across preprocessing/objective evidence')
    require(incoming['padding_slots']+incoming['self_slots']+initial_obj['M'] == csr['original_directed_slots'] == 64*n,
            'Stored original edge slot accounting mismatch')
    branches = [validate_branch(top, root, n, initial, initial_obj, lam, evidence) for lam in (0,1)]
    f0, f1 = (b['final'] for b in branches)
    require(f0['M'] == f1['M'] and f0['Q'] == f1['Q'], 'Final lambda objective denominators differ')
    delta_num, delta_s, delta_c = f1['numerator1']-f0['numerator1'], f1['S']-f0['S'], f1['C']-f0['C']
    condition = delta_num < 0 and delta_s < 0
    return {'dataset': dataset, 'status': 'PASS_SAVED_STRUCTURE_EVIDENCE_AUDIT', 'nodes': n,
            'partition_manifest': {'path': str(path), 'sha256': sha(path)},
            'common_initial_labels_sha256': top['initial_labels_sha256'], 'saved_label_evidence': evidence,
            'initial': initial_obj, 'branches': branches,
            'lambda1_minus_lambda0_final': {'exact_J_at_lambda1_numerator_difference': str(delta_num),
                'common_denominator': str(f0['denominator']), 'J_at_lambda1_difference': delta_num/f0['denominator'],
                'C_difference': delta_c, 'leaf_cut_fraction_difference': delta_c/f0['M'],
                'S_fit_fragmentation_difference': delta_s, 'normalized_fit_fragmentation_difference': delta_s/(9*f0['Q']),
                'mean_distinct_fit_leaf_regions_difference': delta_s/f0['Q'],
                'J_at_lambda1_strictly_lower': delta_num < 0, 'fit_fragmentation_strictly_lower': delta_s < 0,
                'registered_structure_condition_met': condition},
            'cost': cost_summary(top, initial_manifest, branches),
            'objective_full_graph_GT_recomputation_by_this_analyzer': False,
            'objective_recomputation_evidence': 'Verified saved independently recomputed C/S and exact incremental algebra; raw graph and GT are not opened.',
            'P3_gate_passed': False, 'search_gate_evaluated': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--partition-manifest', type=Path, action='append', required=True)
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); check_deadline()
    require(len(a.partition_manifest) == 2 and len({p.resolve() for p in a.partition_manifest}) == 2,
            'Require one partition manifest for each of both datasets')
    protocol_sha = sha(a.protocol); protocol = read_json(a.protocol)
    require(protocol_sha == PROTOCOL_SHA256 and protocol['status'] == 'PREREGISTERED_BEFORE_IMPLEMENTATION_AND_DATA' and
            protocol['stage'] == 'P3', 'Frozen P3 preregistration required')
    a.output.mkdir(parents=True, exist_ok=False)
    record = {'schema_version': 1, 'status': 'INCOMPLETE', 'scope': 'P3_SAVED_STRUCTURE_EVIDENCE',
              'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv, 'script_sha256': sha(__file__),
              'protocol': {'path': str(a.protocol.resolve()), 'sha256': protocol_sha}, 'datasets': [],
              'reads_graph_GT_base_queryvectors_pilot_validation_heldout': False,
              'performs_search_refit_or_parameter_selection': False, 'P3_gate_passed': False,
              'limitations': ['Raw C/S are not recomputed here; this audits saved full-recompute evidence and exact integer algebra.',
                              'Every initial/coarse/child/pass label is freshly hashed and its structural role is checked.',
                              'Source/binary/audit/fit/graph identities are inherited from the accepted partition manifests; this script does not reopen those inputs.',
                              'Structure conditions are necessary only; paired oracle search transfer remains required before P3 can pass.',
                              'No pilot/validation/held-out data, new CI, tuning or performance claim is used.']}
    write_new(a.output/'invocation.json', {k:v for k,v in record.items() if k!='datasets'})
    started = time.perf_counter()
    try:
        seen = set()
        for path in a.partition_manifest:
            check_deadline()
            ds = analyze_partition(path, protocol_sha, protocol['upstream_P2']['sha256'])
            require(ds['dataset'] not in seen, 'Duplicate dataset partition input')
            seen.add(ds['dataset']); record['datasets'].append(ds)
            write_new(a.output/(ds['dataset']+'.json'), ds)
            print(json.dumps({'dataset':ds['dataset'],'status':ds['status'],
                              'structure_condition_met':ds['lambda1_minus_lambda0_final']['registered_structure_condition_met']}),flush=True)
        require(seen == set(DATASET_N), 'Both datasets required')
        record['datasets'].sort(key=lambda d:list(DATASET_N).index(d['dataset']))
        record['both_datasets_structure_conditions_met'] = all(d['lambda1_minus_lambda0_final']['registered_structure_condition_met'] for d in record['datasets'])
        record['stage_interpretation'] = ('STRUCTURE_CONDITION_MET_SEARCH_PENDING' if record['both_datasets_structure_conditions_met']
                                          else 'STRUCTURE_CONDITION_NOT_MET_NO_AUTOMATIC_STAGE_DECISION')
        record['status'] = 'COMPLETE'; record['wall_seconds'] = time.perf_counter()-started
        write_new(a.output/'analysis.json', record)
        write_new(a.output/'complete.json', {'status':'COMPLETE','analysis_sha256':sha(a.output/'analysis.json')})
    except BaseException as e:
        write_new(a.output/'failure.json', {'status':'INCOMPLETE','error':repr(e),
                  'completed_datasets':[d['dataset'] for d in record['datasets']],
                  'meaning':'Evidence audit/analysis failure; does not imply a method NO_GO result'})
        raise


if __name__ == '__main__':
    main()
