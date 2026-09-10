#!/usr/bin/env python3
"""Bounded P2 selection diagnosis: saved count/model plus audited pilot GT only.

No ANN search, model fitting, base/graph/query-vector/validation/held-out access.
Actual pilot GT mass is computed from IDs, never inferred from renormalized
oracle route weights. Main analysis must first confirm positive oracle queue
protection intervals on both datasets at both fixed L values.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time

import numpy as np

DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
LS = (64, 128)
METHODS = ('geom_unified', 'geom_uniform', 'geom_probability', 'oracle_unified', 'oracle_probability')
BIN_EDGES = (0.0, 0.25, 0.5, 0.75, 1.0)
NQ = 10000
SOFT_DEADLINE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()


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
    by_dataset = {d['dataset']: d for d in rows}
    require(len(rows) == len(by_dataset) == 2 and set(by_dataset) == set(DATASETS),
            'Main analysis must contain exactly both registered datasets')
    evidence = []
    for dataset in DATASETS:
        ds = by_dataset[dataset]
        require(ds.get('audit_status') == 'PASS', 'Main analysis input audit must pass')
        selected = [r for r in ds['fixed_comparisons'] if r['contrast'] == 'oracle_protection']
        require(len(selected) == 2 and {r['L'] for r in selected} == set(LS),
                'Require oracle_protection at both fixed L64/128, without duplicates')
        for row in selected:
            require(row['candidate'] == 'oracle_probability' and row['reference'] == 'oracle_unified',
                    'Oracle protection contrast identity mismatch')
            ci = row['paired_query_bootstrap95_pp']
            require(len(ci) == 2 and all(math.isfinite(x) for x in ci) and 0 < ci[0] <= ci[1],
                    f'{dataset} L{row["L"]}: positive paired95% lower bound required before deeper diagnosis')
            evidence.append({'dataset': dataset, 'L': row['L'], 'contrast': row['contrast'],
                             'paired_query_bootstrap95_pp': ci})
    return by_dataset, evidence


def route_signature(row):
    return tuple(json.dumps(row[k], sort_keys=True) for k in
                 ('entry_ids', 'fast_anchor_id', 'shared_seed', 'actual_entry_count', 'regions', 'weights'))


def read_pilot_gt(ds, nq=NQ, parent_rows=30000):
    """Read only the leading pilot records; never hash/read the fit GT suffix."""
    info = ds['files']['drl_train_gt_path']
    path = Path(info['path'])
    with path.open('rb') as f:
        k, = struct.unpack('<i', f.read(4))
        require(k == 100, 'Expected audited exact top100 GT')
        record_bytes = (k + 1) * 4
        require(path.stat().st_size == parent_rows * record_bytes == info['header']['bytes'],
                'GT parent shape differs from P0')
        f.seek(0)
        data = f.read(nq * record_bytes)
    require(len(data) == nq * record_bytes, 'Truncated pilot GT prefix')
    rows = np.frombuffer(data, dtype='<i4').reshape(nq, k + 1)
    require(np.all(rows[:, 0] == k), 'Pilot GT record headers inconsistent')
    values = np.ascontiguousarray(rows[:, 1:])
    digest = hashlib.sha256(values.tobytes()).hexdigest()
    require(digest == ds['pilot']['gt_values_sha256'], 'Pilot GT values differ from P0 fingerprint')
    require(int(values.min()) >= 0 and int(values.max()) < ds['graph']['header']['n'], 'GT ID outside audited base range')
    require(not np.any(np.diff(np.sort(values, axis=1), axis=1) == 0), 'Duplicate GT IDs within a row')
    return values[:, :10], {'path': str(path.resolve()), 'parent_sha256_inherited_from_P0': info['sha256'],
                           'parent_file_fully_read_or_rehashed': False, 'read_parent_row_range': [0, nq],
                           'bytes_read': nq * record_bytes + 4, 'pilot_gt_values_sha256': digest,
                           'used_gt_ranks': [0, 10]}


def selection_metrics(gt_regions, geometry_regions, oracle_regions, oracle_weights):
    nq = len(gt_regions)
    require(gt_regions.shape == (nq, 10), 'Need GT10 region IDs')
    require(geometry_regions.shape == oracle_regions.shape == (nq, 4), 'Need actual top4 route regions')
    require(np.all((gt_regions >= 0) & (gt_regions < 64)), 'GT region outside64')
    for selected in (geometry_regions, oracle_regions):
        require(np.all((selected >= 0) & (selected < 64)), 'Invalid route region ID')
        require(not np.any(np.diff(np.sort(selected, axis=1), axis=1) == 0), 'Duplicate selected region')
    counts = np.zeros((nq, 64), dtype=np.int16)
    np.add.at(counts, (np.repeat(np.arange(nq), 10), gt_regions.reshape(-1)), 1)
    expected_oracle = np.argsort(-counts, axis=1, kind='stable')[:, :4]
    require(np.array_equal(expected_oracle, oracle_regions), 'Saved oracle regions differ from actual GT10 top4 with region-ID tie break')
    gcount = np.take_along_axis(counts, geometry_regions, axis=1).sum(axis=1)
    ocounts = np.take_along_axis(counts, oracle_regions, axis=1)
    ocount = ocounts.sum(axis=1)
    expected_weights = ocounts / ocount[:, None]
    require(np.allclose(expected_weights, oracle_weights, rtol=0, atol=1e-12),
            'Oracle conditional weights do not match actual pilot GT')
    overlap = (geometry_regions[:, :, None] == oracle_regions[:, None, :]).any(axis=1)
    overlap_mass_counts = (ocounts * overlap).sum(axis=1)
    require(np.all(gcount <= ocount), 'Geometric mass cannot exceed oracle top4 maximum')
    return {'geometry_absolute_gt10_mass': gcount.astype(np.float64) / 10,
            'oracle_absolute_gt10_mass': ocount.astype(np.float64) / 10,
            'absolute_mass_gap': (ocount - gcount).astype(np.float64) / 10,
            'gt10_distinct_regions': np.count_nonzero(counts, axis=1),
            'top4_overlap_count': overlap.sum(axis=1),
            'intersection_absolute_gt10_mass': overlap_mass_counts.astype(np.float64) / 10,
            'intersection_fraction_of_oracle_top4_mass': overlap_mass_counts / ocount}


def bin_index(mass):
    require(np.all((mass >= 0) & (mass <= 1)), 'Mass outside[0,1]')
    return np.minimum(np.searchsorted(np.asarray(BIN_EDGES), mass, side='right') - 1, 3)


def describe(values):
    return {'mean': float(np.mean(values)), 'min': float(np.min(values)), 'max': float(np.max(values)),
            'q25': float(np.quantile(values, .25)), 'median': float(np.median(values)), 'q75': float(np.quantile(values, .75))}


def verify_and_diagnose(dataset, paths, analysis_ds, audit_ds, output, audit_sha256):
    count_path, model_path = map(Path, paths)
    for name, path in [('count', count_path), ('model', model_path)]:
        e = analysis_ds['evidence'][name]
        require(path.resolve() == Path(e['path']).resolve() and sha(path) == e['sha256'],
                f'{dataset}: {name} differs from completed main analysis')
    count, model = read_json(count_path), read_json(model_path)
    require(count.get('status') == model.get('status') == 'COMPLETE', 'Count/model not complete')
    require(count.get('dataset') == model.get('dataset') == dataset, 'Dataset mismatch')
    require(count.get('stage') == model.get('stage') == 'P2', 'Expected P2 artifacts')
    require(count.get('split') == 'pilot' and count.get('source_query_type') == 'drl_train', 'Only pilot drl_train permitted')
    require(count.get('source_query_range') == [0, NQ] and count.get('num_queries') == NQ,
            'Require the exact first10000 pilot query IDs')
    require(count.get('measurement') == 'count' and count.get('top_k') == 10 and count.get('rounds') == 1,
            'Independent K10 single-round count required')
    require(count.get('heldout_accessed') is False and model.get('heldout_accessed') is False,
            'Held-out artifact not permitted')
    require(count.get('model_manifest') == model and Path(count['model_file']).resolve() == model_path.resolve(),
            'Count does not embed the current model manifest')
    require(model.get('fit_range') == [10000, 30000] and model.get('pilot_labels_used_for_fit') is False,
            'Model fit isolation invalid')
    require(model.get('input_audit_sha256') == audit_sha256, 'Model is bound to a different P0 audit file')
    for name in ('query', 'gt'):
        require(model[f'fit_{name}_values_sha256'] == audit_ds['fit'][name+'_values_sha256'], 'Fit identity differs from P0')
    require(model['graph_sha256'] == audit_ds['graph']['sha256'], 'Model graph identity differs from P0')
    require(model['base_sha256'] == audit_ds['files']['base_path']['sha256'], 'Model base identity differs from P0')
    require(audit_ds['pilot']['row_range'] == [0, NQ] and audit_ds['pilot']['n'] == NQ, 'P0 pilot range differs')
    for key in ('metric', 'normalization', 'artifact_version'):
        require(count[key] == audit_ds[key], 'Count data contract differs from P0: '+key)
    labels_path = Path(model['labels_file'])
    if not labels_path.is_absolute():
        labels_path = model_path.parent / labels_path
    n = audit_ds['graph']['header']['n']
    require(labels_path.stat().st_size == 2*n and sha(labels_path) == model['labels_sha256'], 'Region labels identity mismatch')
    labels = np.memmap(labels_path, dtype='<u2', mode='r', shape=(n,))
    gt, gt_evidence = read_pilot_gt(audit_ds)
    gt_regions = np.asarray(labels[gt], dtype=np.int16)
    batches = {}
    for r in count['results']:
        if r['method'] in METHODS:
            key = (r['search_L'], r['method'])
            require(key not in batches and r['round'] == 0 and r['top_k'] == 10, 'Duplicate or unexpected count batch')
            rows = r['per_query']
            require(len(rows) == NQ and [x['query_id'] for x in rows] == list(range(NQ)), 'Count query IDs not aligned0..9999')
            batches[key] = rows
    require(set(batches) == {(l, m) for l in LS for m in METHODS}, 'Missing required fixed-L method batches')
    summary = {'dataset': dataset, 'status': 'COMPLETE_DATASET_DIAGNOSIS', 'query_range': [0, NQ],
               'GT_absolute_mass_computed_from_ids': True, 'no_oracle_mass_inference_from_weights': True,
               'fit_data_changed': False, 'evidence': {'count': analysis_ds['evidence']['count'],
               'model': analysis_ds['evidence']['model'], 'pilot_GT_prefix': gt_evidence,
               'labels': {'path': str(labels_path.resolve()), 'sha256': model['labels_sha256']}}, 'by_L': []}
    fields = ['query_id', 'L', 'geometry_absolute_gt10_mass', 'oracle_absolute_gt10_mass', 'absolute_mass_gap',
              'gt10_distinct_regions', 'top4_overlap_count', 'intersection_absolute_gt10_mass',
              'intersection_fraction_of_oracle_top4_mass', 'geometry_mass_bin',
              'geom_uniform_minus_unified_recall_pp', 'geom_probability_minus_unified_recall_pp',
              'oracle_probability_minus_unified_recall_pp', 'oracle_unified_minus_geom_unified_recall_pp']
    csv_path = output / f'per_query_{dataset}.csv'
    previous_routes = None
    with csv_path.open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for l in LS:
            check_deadline()
            rows = {m: batches[l, m] for m in METHODS}
            for q in range(NQ):
                gsig, osig = route_signature(rows['geom_unified'][q]), route_signature(rows['oracle_unified'][q])
                require(gsig == route_signature(rows['geom_uniform'][q]) == route_signature(rows['geom_probability'][q]), 'Geometric queue controls change actual route')
                require(osig == route_signature(rows['oracle_probability'][q]), 'Oracle queue controls change actual route')
            current_routes = ([route_signature(r) for r in rows['geom_unified']], [route_signature(r) for r in rows['oracle_unified']])
            if previous_routes is not None:
                require(current_routes == previous_routes, 'Routing unexpectedly depends on L')
            previous_routes = current_routes
            geometry = np.asarray([r['regions'] for r in rows['geom_unified']], dtype=np.int16)
            oracle = np.asarray([r['regions'] for r in rows['oracle_unified']], dtype=np.int16)
            weights = np.asarray([r['weights'] for r in rows['oracle_unified']], dtype=np.float64)
            metrics = selection_metrics(gt_regions, geometry, oracle, weights)
            bins = bin_index(metrics['geometry_absolute_gt10_mass'])
            recalls = {m: np.asarray([r['recall'] for r in rows[m]], dtype=np.float64) for m in METHODS}
            require(all(np.isfinite(v).all() and np.all((v >= 0) & (v <= 1)) for v in recalls.values()), 'Invalid saved Recall')
            delta = {'geom_uniform_minus_unified_recall_pp': 100*(recalls['geom_uniform']-recalls['geom_unified']),
                     'geom_probability_minus_unified_recall_pp': 100*(recalls['geom_probability']-recalls['geom_unified']),
                     'oracle_probability_minus_unified_recall_pp': 100*(recalls['oracle_probability']-recalls['oracle_unified']),
                     'oracle_unified_minus_geom_unified_recall_pp': 100*(recalls['oracle_unified']-recalls['geom_unified'])}
            grouped = []
            for b in range(4):
                mask = bins == b; size = int(mask.sum())
                grouped.append({'geometry_absolute_mass_bin': [BIN_EDGES[b], BIN_EDGES[b+1]],
                                'interval': '[low,high]' if b == 3 else '[low,high)', 'query_count': size,
                                'mean_geometry_absolute_mass': float(metrics['geometry_absolute_gt10_mass'][mask].mean()) if size else None,
                                'mean_oracle_absolute_mass': float(metrics['oracle_absolute_gt10_mass'][mask].mean()) if size else None,
                                'mean_distinct_GT10_regions': float(metrics['gt10_distinct_regions'][mask].mean()) if size else None,
                                'mean_recall_deltas_pp': {name: float(v[mask].mean()) if size else None for name, v in delta.items()},
                                'causal_interpretation_allowed': False, 'confidence_intervals': None,
                                'reason_no_bin_CI': 'Fixed descriptive stratification; no new significance or gate claim'})
            summary['by_L'].append({'L': l, 'selection_metrics': {name: describe(v) for name, v in metrics.items()},
                                    'bins_by_actual_geometry_absolute_mass': grouped,
                                    'overall_recall_deltas_pp': {name: float(v.mean()) for name, v in delta.items()}})
            for q in range(NQ):
                record = {'query_id': q, 'L': l, 'geometry_mass_bin': int(bins[q])}
                record.update({name: v[q].item() for name, v in metrics.items()})
                record.update({name: float(v[q]) for name, v in delta.items()}); writer.writerow(record)
    summary['per_query_csv'] = {'path': str(csv_path.resolve()), 'sha256': sha(csv_path)}
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--analysis', type=Path, required=True)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--input', action='append', nargs=3, metavar=('DATASET', 'COUNT_JSON', 'MODEL_JSON'), required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); check_deadline()
    supplied = {x[0]: x[1:] for x in a.input}
    require(len(a.input) == len(supplied) == 2 and set(supplied) == set(DATASETS), 'Require exactly both datasets')
    analysis = read_json(a.analysis)
    analysis_ds, gate_evidence = positive_oracle_gate(analysis)  # before reading any GT/labels
    audit = read_json(a.audit)
    require(audit.get('status') == 'PASS_INPUT_CONTRACT', 'Completed P0 audit required')
    audit_ds = {d['dataset']: d for d in audit['datasets']}
    require(set(DATASETS).issubset(audit_ds), 'P0 misses a dataset')
    a.output.mkdir(parents=True, exist_ok=False)
    record = {'schema_version': 1, 'status': 'INCOMPLETE', 'scope': 'P2_PILOT_SELECTION_DIAGNOSIS',
              'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'argv': sys.argv,
              'script_sha256': sha(__file__), 'analysis': {'path': str(a.analysis.resolve()), 'sha256': sha(a.analysis)},
              'P0_audit': {'path': str(a.audit.resolve()), 'sha256': sha(a.audit)}, 'oracle_precondition': gate_evidence,
              'fixed_geometry_mass_bins': list(BIN_EDGES), 'bin_convention': '[0,.25),[.25,.5),[.5,.75),[.75,1]',
              'reads_pilot_GT_prefix_only': True, 'reads_base_graph_queryvectors_validation_heldout': False,
              'model_training_or_search_run': False, 'P2_or_formal_performance_gate_passed': False,
              'datasets': [], 'limitations': [
                  'Bins describe associations in historically used development pilot; not randomized strata or causal effects.',
                  'Positive pointwise95% oracle-protection intervals authorize this bounded diagnosis, not P2 GO or formal performance gain.',
                  'Oracle/geometric selection changes selected portals, order and possibly deduplicated entry count; their gap does not isolate portal quality or connectivity.',
                  'Absolute top4 target mass is not an upper bound on search Recall because cross-region graph edges remain traversable.',
                  'GT file prefix fingerprint is freshly checked; full parent GT checksum and query-vector identity are inherited from P0 and aligned count provenance.',
                  'No fit samples, model, partition, thresholds or parameters are modified; no new confidence claim is made from bins.']}
    write_new(a.output/'invocation.json', {k: v for k, v in record.items() if k != 'datasets'})
    started = time.perf_counter()
    try:
        for dataset in DATASETS:
            check_deadline()
            ds = verify_and_diagnose(dataset, supplied[dataset], analysis_ds[dataset], audit_ds[dataset], a.output, record['P0_audit']['sha256'])
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
