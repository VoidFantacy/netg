#!/usr/bin/env python3
"""P2 saved-count diagnosis of integer capacities; no GT, graph or vector reads.

Reconstruct the frozen RegionalSearch.h allocator, verify that equal capacities
and equal routes produce identical saved outputs/counts, and describe geometric
and oracle concentration. This is not a new search, fit, CI or performance gate.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import numpy as np

DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
LS = (64, 128)
METHODS = ('geom_unified', 'geom_uniform', 'geom_probability', 'oracle_unified', 'oracle_probability')
NQ = 10000
SOURCE_SHA256 = '320e29c9407d5907ece7ef64113edeb8b2d5157fa8796aaf94e470eb6771e14e'
SOURCE_DEFAULT = Path(__file__).resolve().parents[4] / 'ACSG/RegionalSearch.h'
MANIFEST_DEFAULT = Path(__file__).resolve().parents[1] / 'p1/source_and_log_manifest.json'
SOFT_DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
EXACT_FIELDS = ('result_ids', 'recall', 'routing_ndc', 'graph_ndc', 'total_ndc',
                'routing_mac', 'graph_mac', 'total_mac', 'expanded', 'rejected', 'evicted_unexpanded')
COUNT_FIELDS = tuple(k for k in EXACT_FIELDS if k not in ('result_ids', 'recall'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_deadline():
    require(time.time() < SOFT_DEADLINE, 'Research diagnosis closed at soft deadline')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def positive_oracle_gate(analysis):
    require(analysis.get('status') == 'COMPLETE', 'Main P2 analysis must be COMPLETE')
    rows = analysis.get('datasets', [])
    datasets = {d['dataset']: d for d in rows}
    require(len(rows) == len(datasets) == 2 and set(datasets) == set(DATASETS),
            'Require exactly both registered datasets in main analysis')
    evidence = []
    for dataset in DATASETS:
        ds = datasets[dataset]
        require(ds.get('audit_status') == 'PASS', 'Main analysis input audit must pass')
        selected = [r for r in ds['fixed_comparisons'] if r['contrast'] == 'oracle_protection']
        require(len(selected) == 2 and {r['L'] for r in selected} == set(LS),
                'Require both fixed L64/128 oracle protection contrasts without duplicates')
        for row in selected:
            require(row['candidate'] == 'oracle_probability' and row['reference'] == 'oracle_unified',
                    'Oracle protection contrast identity mismatch')
            ci = row['paired_query_bootstrap95_pp']
            require(len(ci) == 2 and all(math.isfinite(v) for v in ci) and 0 < ci[0] <= ci[1],
                    'Positive oracle protection lower bound required before deeper diagnosis')
            evidence.append({'dataset': dataset, 'L': row['L'], 'paired_query_bootstrap95_pp': ci})
    return datasets, evidence


def allocate(regions, weights, l, region_count=64, regional=True, uniform=False):
    """Scalar binary64 operations match the frozen C++ allocator, including ties."""
    active = len(regions)
    require(active <= 4 and len(weights) == active and l >= 1 and 1 <= region_count <= 65536,
            'Invalid allocation dimensions')
    weight_sum = 0.0
    for i, (region, weight) in enumerate(zip(regions, weights)):
        require(isinstance(region, int) and 0 <= region < region_count and region not in regions[:i]
                and math.isfinite(weight) and weight >= 0, 'Invalid route region/weight')
        weight_sum += weight
    require(math.isfinite(weight_sum), 'Invalid weight sum')
    if not regional or region_count == 1 or active == 0:
        return [l]
    require(weight_sum > 0, 'Regional allocation requires positive weights')
    shared = l // 4
    remainder = l - shared - 4 * active
    require(shared >= 1 and remainder >= 0, 'L cannot satisfy queue minima')
    caps, fractions, used = [shared], [], 0
    for weight in weights:
        portion = remainder * (1.0 / active if uniform else weight / weight_sum)
        floor = math.floor(portion)
        caps.append(4 + floor); fractions.append(portion - floor); used += floor
    order = sorted(range(active), key=lambda i: (-fractions[i], regions[i]))
    leftover = remainder - used
    require(0 <= leftover <= active, 'Floating allocation remainder outside C++ contract')
    for i in range(leftover):
        caps[order[i] + 1] += 1
    require(sum(caps) == l, 'Capacity budget not conserved')
    return caps


def route_signature(row):
    return tuple(json.dumps(row[k], sort_keys=True) for k in
                 ('entry_ids', 'fast_anchor_id', 'shared_seed', 'actual_entry_count', 'regions', 'weights'))


def equality_checks(left, right, same_capacity):
    """Exact output/count equality follows from same route and capacity vector."""
    require(route_signature(left) == route_signature(right), 'Geometric controls changed the route')
    checks = {field: left[field] == right[field] for field in EXACT_FIELDS}
    if same_capacity:
        failed = [field for field, same in checks.items() if not same]
        require(not failed, 'Equal capacity/route changed saved outputs or counters: ' + ', '.join(failed))
    return checks


def concentration(values):
    # These are conditional on the selected four regions, not absolute GT mass.
    total = sum(values)
    require(total > 0 and all(math.isfinite(v) and v >= 0 for v in values), 'Invalid concentration values')
    probs = [v / total for v in values]
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    return {'max_probability': max(probs), 'entropy_bits': entropy,
            'normalized_entropy': entropy / math.log2(len(probs)) if len(probs) > 1 else 0.0,
            'herfindahl_index': sum(p * p for p in probs)}


def describe(values):
    values = np.asarray(values, dtype=np.float64)
    require(len(values) > 0 and np.isfinite(values).all(), 'Cannot summarize empty/nonfinite values')
    return {'mean': float(values.mean()), 'min': float(values.min()), 'max': float(values.max()),
            'q25': float(np.quantile(values, .25)), 'median': float(np.median(values)),
            'q75': float(np.quantile(values, .75))}


def validate_row(row, n, dim):
    require(len(row['regions']) == len(row['weights']) == 4, 'Expected actual top4 route')
    require(abs(sum(row['weights']) - 1.0) < 1e-12, 'Saved top4 weights must be conditional probabilities')
    require(len(row['result_ids']) == 10 and all(isinstance(i, int) and -1 <= i < n for i in row['result_ids']),
            'Invalid K10 result IDs')
    require(math.isfinite(row['recall']) and 0 <= row['recall'] <= 1, 'Invalid saved Recall')
    require(all(isinstance(row[k], int) and row[k] >= 0 for k in COUNT_FIELDS), 'Invalid saved counter')
    require(row['graph_ndc'] + row['routing_ndc'] == row['total_ndc'], 'NDC accounting mismatch')
    require(row['graph_mac'] == dim * row['graph_ndc'] and
            row['total_mac'] == row['graph_mac'] + row['routing_mac'], 'MAC accounting mismatch')


def verify_and_diagnose(dataset, paths, analysis_ds, output):
    count_path, model_path = map(Path, paths)
    for key, path in [('count', count_path), ('model', model_path)]:
        evidence = analysis_ds['evidence'][key]
        require(path.resolve() == Path(evidence['path']).resolve() and sha(path) == evidence['sha256'],
                f'{dataset}: {key} differs from completed main analysis')
    count, model = read_json(count_path), read_json(model_path)
    require(count.get('status') == model.get('status') == 'COMPLETE', 'Count/model not complete')
    require(count.get('dataset') == model.get('dataset') == dataset, 'Dataset mismatch')
    require(count.get('stage') == model.get('stage') == 'P2', 'Expected P2 artifacts')
    require(count.get('split') == 'pilot' and count.get('source_query_type') == 'drl_train' and
            count.get('source_query_range') == [0, NQ] and count.get('num_queries') == NQ,
            'Require aligned first10000 drl_train pilot queries')
    require(count.get('measurement') == 'count' and count.get('top_k') == 10 and count.get('rounds') == 1,
            'Require independent K10 single-round count')
    require(count.get('heldout_accessed') is False and model.get('heldout_accessed') is False,
            'Held-out data not permitted')
    require(count.get('model_manifest') == model and Path(count['model_file']).resolve() == model_path.resolve(),
            'Count must embed the same model manifest')
    require(model.get('region_count') == 64 and model.get('active_regions') == 4 and
            model.get('fit_range') == [10000, 30000] and model.get('pilot_labels_used_for_fit') is False,
            'Frozen model/split contract differs')
    batches = {}
    for batch in count['results']:
        if batch['method'] not in METHODS:
            continue
        key = batch['search_L'], batch['method']
        require(key not in batches and batch['round'] == 0 and batch['top_k'] == 10, 'Duplicate/unexpected count batch')
        rows = batch['per_query']
        require(len(rows) == NQ and [r['query_id'] for r in rows] == list(range(NQ)), 'Query IDs not aligned')
        for row in rows:
            validate_row(row, count['base_nodes'], count['dim'])
        batches[key] = rows
    require(set(batches) == {(l, m) for l in LS for m in METHODS}, 'Missing fixed-L method batches')
    summary = {'dataset': dataset, 'status': 'COMPLETE_DATASET_DIAGNOSIS', 'query_range': [0, NQ],
               'evidence': {k: analysis_ds['evidence'][k] for k in ('count', 'model')}, 'by_L': []}
    fields = ['query_id', 'L', 'geometry_regions', 'oracle_regions', 'uniform_capacity',
              'geometry_probability_capacity', 'oracle_probability_capacity',
              'geometry_uniform_probability_same_capacity', 'geometry_capacity_l1_distance_from_uniform',
              'oracle_capacity_l1_distance_from_uniform', 'same_result_ids', 'same_all_outputs_and_counts',
              'geometry_probability_minus_uniform_recall_pp', 'geometry_probability_minus_uniform_graph_ndc',
              'geometry_probability_minus_uniform_expanded']
    metric_fields = [f'{which}_{basis}_{name}' for which in ('geometry', 'oracle')
                     for basis in ('weights', 'regional_capacity') for name in concentration([1, 1, 1, 1])]
    fields += metric_fields
    csv_path = output / f'per_query_{dataset}.csv'
    previous_routes = None
    with csv_path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for l in LS:
            check_deadline()
            rows = {method: batches[l, method] for method in METHODS}
            routes = ([route_signature(r) for r in rows['geom_unified']],
                      [route_signature(r) for r in rows['oracle_unified']])
            if previous_routes is not None:
                require(routes == previous_routes, 'Saved routing unexpectedly depends on L')
            previous_routes = routes
            stats = {k: [] for k in metric_fields}
            cap_same = []; checks_by_field = {k: [] for k in EXACT_FIELDS}
            geometry_l1, oracle_l1, delta_recall, delta_ndc, delta_expanded = [], [], [], [], []
            max_capacity_histogram = {'geometry': {}, 'oracle': {}}
            for q in range(NQ):
                if q % 1024 == 0:
                    check_deadline()
                g, u, gp = (rows[m][q] for m in ('geom_unified', 'geom_uniform', 'geom_probability'))
                o, op = (rows[m][q] for m in ('oracle_unified', 'oracle_probability'))
                require(route_signature(g) == route_signature(u) == route_signature(gp),
                        'Geometry queue controls changed actual route')
                require(route_signature(o) == route_signature(op), 'Oracle queue controls changed actual route')
                uniform = allocate(g['regions'], g['weights'], l, uniform=True)
                geometry = allocate(g['regions'], g['weights'], l)
                oracle = allocate(o['regions'], o['weights'], l)
                oracle_uniform = allocate(o['regions'], o['weights'], l, uniform=True)
                same = uniform == geometry
                checks = equality_checks(u, gp, same)
                cap_same.append(same)
                for field, equal in checks.items():
                    checks_by_field[field].append(equal)
                gl1 = sum(abs(a-b) for a, b in zip(geometry, uniform))
                ol1 = sum(abs(a-b) for a, b in zip(oracle, oracle_uniform))
                dr = 100 * (gp['recall'] - u['recall'])
                dn = gp['graph_ndc'] - u['graph_ndc']; de = gp['expanded'] - u['expanded']
                geometry_l1.append(gl1); oracle_l1.append(ol1)
                delta_recall.append(dr); delta_ndc.append(dn); delta_expanded.append(de)
                record = {'query_id': q, 'L': l, 'geometry_regions': json.dumps(g['regions']),
                          'oracle_regions': json.dumps(o['regions']), 'uniform_capacity': json.dumps(uniform),
                          'geometry_probability_capacity': json.dumps(geometry),
                          'oracle_probability_capacity': json.dumps(oracle),
                          'geometry_uniform_probability_same_capacity': same,
                          'geometry_capacity_l1_distance_from_uniform': gl1,
                          'oracle_capacity_l1_distance_from_uniform': ol1,
                          'same_result_ids': checks['result_ids'], 'same_all_outputs_and_counts': all(checks.values()),
                          'geometry_probability_minus_uniform_recall_pp': dr,
                          'geometry_probability_minus_uniform_graph_ndc': dn,
                          'geometry_probability_minus_uniform_expanded': de}
                for which, route, caps in [('geometry', g, geometry), ('oracle', o, oracle)]:
                    maximum = max(caps[1:]); histogram = max_capacity_histogram[which]
                    histogram[maximum] = histogram.get(maximum, 0) + 1
                    for basis, values in [('weights', route['weights']), ('regional_capacity', caps[1:])]:
                        for key, value in concentration(values).items():
                            field = f'{which}_{basis}_{key}'; stats[field].append(value); record[field] = value
                writer.writerow(record)
            same = np.asarray(cap_same, dtype=bool)
            all_same = np.logical_and.reduce([np.asarray(v) for v in checks_by_field.values()])
            strata = []
            for flag in (True, False):
                mask = same == flag; n = int(mask.sum())
                strata.append({'identical_integer_capacities': flag, 'query_count': n,
                               'identical_outputs_and_counts_count': int(all_same[mask].sum()),
                               'mean_probability_minus_uniform_recall_pp': float(np.asarray(delta_recall)[mask].mean()) if n else None,
                               'mean_probability_minus_uniform_graph_ndc': float(np.asarray(delta_ndc)[mask].mean()) if n else None,
                               'mean_probability_minus_uniform_expanded': float(np.asarray(delta_expanded)[mask].mean()) if n else None})
            summary['by_L'].append({'L': l, 'shared_capacity': l // 4, 'total_regional_capacity': l-l//4,
                                    'query_count': NQ, 'identical_integer_capacities_count': int(same.sum()),
                                    'identical_integer_capacities_fraction': float(same.mean()),
                                    'identical_capacity_output_check': 'PASS', 'equal_capacity_mismatches': 0,
                                    'all_queries_identical_saved_field_fraction': {k: float(np.mean(v)) for k, v in checks_by_field.items()},
                                    'geometry_capacity_l1_distance_from_uniform': describe(geometry_l1),
                                    'oracle_capacity_l1_distance_from_uniform': describe(oracle_l1),
                                    'conditional_concentration': {k: describe(v) for k, v in stats.items()},
                                    'max_regional_capacity_histogram': max_capacity_histogram,
                                    'same_vs_different_capacity_descriptive_strata': strata})
    summary['per_query_csv'] = {'path': str(csv_path.resolve()), 'sha256': sha(csv_path)}
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--analysis', type=Path, required=True)
    p.add_argument('--input', action='append', nargs=3, metavar=('DATASET', 'COUNT_JSON', 'MODEL_JSON'), required=True)
    p.add_argument('--search-source', type=Path, default=SOURCE_DEFAULT)
    p.add_argument('--source-manifest', type=Path, default=MANIFEST_DEFAULT)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); check_deadline()
    supplied = {x[0]: x[1:] for x in a.input}
    require(len(a.input) == len(supplied) == 2 and set(supplied) == set(DATASETS), 'Require exactly both datasets')
    analysis = read_json(a.analysis)
    analysis_ds, gate_evidence = positive_oracle_gate(analysis)
    require(sha(a.search_source) == SOURCE_SHA256, 'Frozen allocator/scheduler source changed; diagnosis must be reviewed')
    source_manifest = read_json(a.source_manifest)
    require(source_manifest['files']['ACSG/RegionalSearch.h']['sha256'] == SOURCE_SHA256,
            'Frozen P1 source manifest differs from allocator/scheduler being reconstructed')
    a.output.mkdir(parents=True, exist_ok=False)
    record = {'schema_version': 1, 'status': 'INCOMPLETE', 'scope': 'P2_SAVED_CAPACITY_DIAGNOSIS',
              'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv,
              'script_sha256': sha(__file__), 'analysis': {'path': str(a.analysis.resolve()), 'sha256': sha(a.analysis)},
              'source': {'path': str(a.search_source.resolve()), 'sha256': SOURCE_SHA256},
              'source_manifest': {'path': str(a.source_manifest.resolve()), 'sha256': sha(a.source_manifest)},
              'oracle_precondition': gate_evidence,
              'allocator': {'shared': 'floor(L/4)', 'min_per_active_region': 4,
                            'remaining': 'largest remainder using binary64; tied fractions use ascending region ID',
                            'capacity_order': 'shared followed by saved selected-region order',
                            'scheduler_weight': 'integer queue capacity'},
              'reads_GT_base_graph_labels_queryvectors_validation_heldout': False,
              'model_training_or_search_run': False, 'confidence_intervals': None,
              'P2_or_formal_performance_gate_passed': False, 'datasets': [],
              'limitations': [
                  'All weight and regional-capacity probabilities are conditional on the selected four regions; they do not measure absolute GT mass.',
                  'Capacity concentration concerns retention and scheduler weights together and does not isolate their causal effects.',
                  'Oracle and geometric routes select different regions/portals; concentration differences alone do not identify a correct deployment calibration.',
                  'Equal-capacity equivalence is checked from saved outputs/counters; no search is replayed.',
                  'Main-analysis input identity is freshly checked; model arrays, GT, graph and vectors are not read or rehashed.',
                  'Fixed descriptive output only; no model, parameters, partitions, confidence intervals or gates are changed.']}
    write_new(a.output/'invocation.json', {k: v for k, v in record.items() if k != 'datasets'})
    started = time.perf_counter()
    try:
        for dataset in DATASETS:
            check_deadline()
            ds = verify_and_diagnose(dataset, supplied[dataset], analysis_ds[dataset], a.output)
            record['datasets'].append(ds); write_new(a.output/f'{dataset}.json', ds)
            print(json.dumps({'dataset': dataset, 'status': ds['status']}), flush=True)
        record['status'] = 'COMPLETE'; record['wall_seconds'] = time.perf_counter()-started
        write_new(a.output/'diagnosis.json', record)
        write_new(a.output/'complete.json', {'status': 'COMPLETE', 'diagnosis_sha256': sha(a.output/'diagnosis.json')})
    except BaseException as e:
        write_new(a.output/'failure.json', {'status': 'INCOMPLETE', 'error': repr(e),
                  'completed_datasets': [d['dataset'] for d in record['datasets']],
                  'meaning': 'Diagnosis input/execution failure; no method NO_GO inferred'})
        raise


if __name__ == '__main__':
    main()
