#!/usr/bin/env python3
"""P3 fit-only extraction and deterministic portal plans; no ANN search or GT fitting on pilot."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

RUN = Path(__file__).resolve().parents[1]
SOFT_CLOSE = dt.datetime(2026, 9, 7, 22, 59, tzinfo=dt.timezone.utc).timestamp()
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def deadline():
    require(time.time() < SOFT_CLOSE, 'P3 research has reached its soft deadline')


def read_json(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def binding(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path)}


def write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def write_raw(path, values):
    with Path(path).open('xb') as f:
        f.write(np.ascontiguousarray(values).tobytes())


def verify_audit_link(gate, audit_path, run_root=RUN):
    p0_path = run_root / 'gates/P0.json'
    links = [e for e in gate['evidence'] if Path(e['path']).resolve() == p0_path.resolve()]
    require(len(links) == 1 and links[0]['sha256'] == sha(p0_path), 'P2 does not bind the current P0 gate')
    p0 = read_json(p0_path)
    require(p0['stage'] == 'P0' and p0['status'] == 'PASS', 'Bound P0 gate not passed')
    matches = []
    for evidence in p0['evidence']:
        path = Path(evidence['path'])
        if not path.is_absolute():
            path = run_root / path
        if path.resolve() == Path(audit_path).resolve():
            matches.append(evidence)
    require(len(matches) == 1 and matches[0]['sha256'] == sha(audit_path),
            'Supplied audit does not match P0 evidence inherited by P2')


def verify_fit_fingerprints(fit, ds):
    require(fit['queries_sha256'] == fit['fit_query_values_sha256'] == ds['fit']['query_values_sha256'],
            'Raw fit query fingerprint differs from P0 values')
    require(fit['fit_gt_values_sha256'] == ds['fit']['gt_values_sha256'], 'Full fit GT fingerprint differs from P0')
    require(fit['graph_sha256'] == ds['graph']['sha256'], 'Fit frozen graph fingerprint differs from P0')


def verify_control(protocol_path, gate_path, audit_path):
    deadline()
    protocol, gate, audit = map(read_json, (protocol_path, gate_path, audit_path))
    require(protocol['stage'] == 'P3' and protocol['cpu_only'] is True, 'P3 CPU protocol required')
    require(protocol['status'] == 'PREREGISTERED_BEFORE_IMPLEMENTATION_AND_DATA', 'Unrecognized P3 protocol state')
    require(protocol['fit_range'] == [10000, 30000] and protocol['fit_count'] == 20000, 'Fit range changed')
    require(protocol['validation_heldout_allowed'] is False, 'P3 cannot permit validation or heldout')
    require(gate['stage'] == 'P2' and gate['status'] == 'PASS', 'P2 PASS required')
    require(protocol['upstream_P2'] == binding(gate_path), 'P3 protocol not bound to supplied P2 gate')
    verify_audit_link(gate, audit_path)
    require(audit['stage'] == 'P0' and audit['status'] == 'PASS_INPUT_CONTRACT' and audit['heldout_accessed'] is False,
            'Full P0 input contract required')
    require(set(protocol['datasets']) == set(DATASETS), 'Dataset registration changed')
    return protocol, gate, audit


def read_vec_suffix(info, begin, count, value_dtype, expected_value_sha):
    """Physically read only the registered row suffix, retaining exact value bits."""
    path = Path(info['path'])
    n, width, nbytes = (info['header'][k] for k in ('n', 'd', 'bytes'))
    record_bytes = (width + 1) * 4
    require(path.stat().st_size == nbytes == n * record_bytes, 'Parent vec shape/bytes changed')
    require(0 <= begin < n and 0 < count <= n - begin, 'Invalid source suffix')
    with path.open('rb') as f:
        f.seek(begin * record_bytes)
        raw = f.read(count * record_bytes)
    require(len(raw) == count * record_bytes, 'Short vec suffix read')
    words = np.frombuffer(raw, dtype='<i4').reshape(count, width + 1)
    require(np.all(words[:, 0] == width), 'Vec record header mismatch within fit rows')
    values = np.ascontiguousarray(words[:, 1:]).view(value_dtype)
    digest = hashlib.sha256(values.tobytes()).hexdigest()
    require(digest == expected_value_sha, 'Fit value SHA differs from P0')
    return values, {'path': str(path.resolve()), 'parent_sha256_inherited_from_P0': info['sha256'],
                    'parent_fully_read_or_rehashed': False, 'read_parent_row_range': [begin, begin + count],
                    'read_byte_range': [begin * record_bytes, (begin + count) * record_bytes],
                    'bytes_read': count * record_bytes, 'fit_values_sha256': digest}


def audit_dataset(audit, dataset):
    matches = [d for d in audit['datasets'] if d['dataset'] == dataset]
    require(len(matches) == 1, 'Missing/duplicate audited dataset')
    return matches[0]


def extract_inputs(args, protocol, audit):
    ds = audit_dataset(audit, args.dataset)
    fit = ds['fit']
    require(fit['row_range'] == [10000, 30000] and fit['n'] == 20000, 'P0 fit contract differs')
    started = time.perf_counter()
    queries, query_provenance = read_vec_suffix(ds['files']['drl_train_query_path'], 10000, 20000,
                                               '<f4', fit['query_values_sha256'])
    gt100, gt_provenance = read_vec_suffix(ds['files']['drl_train_gt_path'], 10000, 20000,
                                         '<i4', fit['gt_values_sha256'])
    n, dim = ds['graph']['header']['n'], ds['graph']['header']['d']
    require(queries.shape == (20000, dim) and np.isfinite(queries).all(), 'Invalid fit queries')
    require(gt100.shape == (20000, 100), 'Expected exact GT100')
    require(int(gt100.min()) >= 0 and int(gt100.max()) < n, 'GT ID outside base')
    require(not np.any(np.diff(np.sort(gt100, axis=1), axis=1) == 0), 'Duplicate GT IDs in a fit row')
    validation_seconds = time.perf_counter() - started
    deadline()
    gt10 = np.ascontiguousarray(gt100[:, :10])
    query_file = args.output / 'queries.f32'
    gt_file = args.output / 'gt10.i32'
    write_begin = time.perf_counter()
    write_raw(query_file, queries)
    write_raw(gt_file, gt10)
    write_seconds = time.perf_counter() - write_begin
    manifest = {
        'schema_version': 1, 'stage': 'P3', 'status': 'COMPLETE', 'dataset': args.dataset,
        'cpu_only': True, 'fit_range': [10000, 30000], 'fit_count': 20000,
        'heldout_accessed': False, 'pilot_accessed': False, 'validation_accessed': False,
        'dim': dim, 'base_nodes': n, 'queries_file': str(query_file.resolve()), 'queries_sha256': sha(query_file),
        'gt10_file': str(gt_file.resolve()), 'gt10_sha256': sha(gt_file),
        'fit_query_values_sha256': fit['query_values_sha256'], 'fit_gt_values_sha256': fit['gt_values_sha256'],
        'query_dtype': '<f4', 'gt10_dtype': '<i4', 'gt10_shape': [20000, 10],
        'input_audit_path': str(args.audit.resolve()), 'input_audit_sha256': sha(args.audit),
        'protocol_path': str(args.protocol.resolve()), 'protocol_sha256': sha(args.protocol),
        'p2_gate': binding(args.gate), 'graph_file': ds['graph']['path'], 'graph_sha256': ds['graph']['sha256'],
        'base_sha256': ds['files']['base_path']['sha256'],
        'query_provenance': query_provenance, 'gt_provenance': gt_provenance,
        'fit_extraction_seconds': time.perf_counter() - started,
        'cost_seconds': {'read_validate': validation_seconds, 'write': write_seconds,
                         'exact_GT_from_scratch': None},
        'exact_GT_cost_reason': 'Existing exact GT reused; historical creation wall unavailable',
        'source': binding(__file__), 'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    require(manifest['queries_sha256'] == manifest['fit_query_values_sha256'], 'Raw query extraction changed bits')
    write_json(args.output / 'manifest.json', manifest)
    return manifest


def candidate_lists(labels, gt10, region_count=256, limit=8):
    """Frequency order first, then smallest unselected real region members for fallback."""
    nodes, counts = np.unique(gt10, return_counts=True)
    regions = labels[nodes]
    order = np.lexsort((nodes, -counts, regions))
    result, fallback = [], []
    for region in range(region_count):
        chosen = nodes[order[regions[order] == region]][:limit].astype(int).tolist()
        real_count = len(chosen)
        if len(chosen) < limit:
            taken = set(chosen)
            for node in np.flatnonzero(labels == region):
                if int(node) not in taken:
                    chosen.append(int(node))
                    if len(chosen) == limit:
                        break
        require(len(chosen) >= 3 and len(set(chosen)) == len(chosen), 'Each leaf requires three distinct real candidates')
        require(all(int(labels[x]) == region for x in chosen), 'Candidate is outside its leaf')
        result.append(chosen)
        fallback.append(len(chosen) - real_count)
    return result, fallback


def selected_query_ids(dataset, leaf, eligible_global_ids, seed=2026090711, limit=128):
    ranked = [(hashlib.sha256(f'{dataset}|{seed}|{int(q)}|{leaf}'.encode('utf-8')).digest(), int(q))
              for q in eligible_global_ids]
    ranked.sort()
    return [q for _, q in ranked[:limit]]


def make_plan(args, protocol, audit):
    started = time.perf_counter()
    fit = read_json(args.fit_manifest)
    partition = read_json(args.partition)
    ds = audit_dataset(audit, args.dataset)
    for key, val in [('status', 'COMPLETE'), ('stage', 'P3'), ('dataset', args.dataset),
                     ('fit_range', [10000, 30000]), ('fit_count', 20000),
                     ('heldout_accessed', False), ('pilot_accessed', False)]:
        require(fit.get(key) == val, 'Invalid fit manifest field: ' + key)
    require(fit['input_audit_sha256'] == sha(args.audit) and fit['protocol_sha256'] == sha(args.protocol),
            'Fit manifest has different audit or protocol')
    for key, val in [('status', 'COMPLETE'), ('stage', 'P3'), ('dataset', args.dataset),
                     ('regions', 256), ('coarse_count', 16), ('leaves_per_coarse', 16),
                     ('protocol_sha256', sha(args.protocol)), ('input_audit_sha256', sha(args.audit)),
                     ('fit_manifest_sha256', sha(args.fit_manifest)),
                     ('fit_gt_values_sha256', ds['fit']['gt_values_sha256'])]:
        require(partition.get(key) == val, 'Invalid partition manifest field: ' + key)
    require(partition['lambda'] in (0, 1), 'Only registered lambda0/1 permitted')
    n, dim = fit['base_nodes'], fit['dim']
    require(n == partition['nodes'] == ds['graph']['header']['n'] and dim == ds['graph']['header']['d'],
            'Partition/fit/audit shape mismatch')
    verify_fit_fingerprints(fit, ds)
    require(partition['input_graph_sha256'] == ds['graph']['sha256'], 'Partition graph fingerprint differs from P0')
    labels_file = Path(partition['labels_file'])
    require(labels_file.is_absolute(), 'Absolute final labels path required')
    require(labels_file.stat().st_size == 2*n and sha(labels_file) == partition['labels_sha256'], 'Labels SHA/size mismatch')
    labels = np.memmap(labels_file, dtype='<u2', mode='r', shape=(n,))
    require(int(labels.max()) < 256, 'Label outside256')
    sizes = np.bincount(labels, minlength=256)
    require(int(sizes.min()) >= 3 and int(sizes.max()) <= 6*n//(5*256), 'Leaf count/capacity invalid')
    require(int(sizes.reshape(16, 16).sum(axis=1).max()) <= 6*n//(5*16), 'Coarse capacity invalid')
    gt_file = Path(fit['gt10_file'])
    require(gt_file.stat().st_size == 20000*10*4 and sha(gt_file) == fit['gt10_sha256'], 'Fit GT10 SHA/shape mismatch')
    gt10 = np.fromfile(gt_file, dtype='<i4').reshape(20000, 10)
    require(int(gt10.min()) >= 0 and int(gt10.max()) < n, 'Invalid GT10 IDs')
    require(not np.any(np.diff(np.sort(gt10, axis=1), axis=1) == 0), 'Duplicate GT10 IDs')
    candidates, fallback = candidate_lists(labels, gt10)
    gt_regions = labels[gt10]
    regions = []
    for leaf in range(256):
        eligible = np.flatnonzero(np.any(gt_regions == leaf, axis=1)) + 10000
        qids = selected_query_ids(args.dataset, leaf, eligible)
        regions.append({'region': leaf, 'candidate_ids': candidates[leaf], 'query_ids': qids,
                        'eligible_fit_query_count': len(eligible), 'fallback_candidate_count': fallback[leaf],
                        'zero_query_fallback': not bool(qids)})
    deadline()
    index = Path(ds['graph']['path'])
    require(index.stat().st_size == ds['graph']['header']['bytes'], 'Audited index size changed')
    source_bindings = [binding(x) for x in args.source_binding]
    require(source_bindings, 'At least one frozen prober source binding required')
    query_file = Path(fit['queries_file'])
    require(query_file.stat().st_size == 20000*dim*4 and sha(query_file) == fit['queries_sha256'], 'Fit query SHA/shape changed')
    plan = {
        'schema_version': 1, 'stage': 'P3', 'status': 'COMPLETE', 'dataset': args.dataset,
        'cpu_only': True, 'structure_lambda': partition['lambda'], 'dim': dim, 'n_base': n,
        'fit_range': [10000, 30000], 'fit_count': 20000, 'region_count': 256, 'seed': 2026090711,
        'heldout_accessed': False, 'pilot_accessed': False,
        'protocol': binding(args.protocol), 'audit': binding(args.audit), 'gate': binding(args.gate),
        'fit_manifest': binding(args.fit_manifest), 'partition_manifest': binding(args.partition),
        'index': {'path': str(index.resolve()), 'sha256': ds['graph']['sha256'], 'bytes': index.stat().st_size,
                  'sha256_inherited_from_P0': True, 'fully_rehashed_by_this_planner': False},
        'queries': binding(query_file), 'gt10': binding(gt_file), 'labels': binding(labels_file),
        'regions': regions, 'source_binding': source_bindings,
        'upstream_cost_seconds': {'fit_extraction': fit['fit_extraction_seconds'],
                                  'candidate_query_selection': time.perf_counter() - started},
        'actual_probe_call_count': sum(len(x['candidate_ids'])*len(x['query_ids']) for x in regions),
        'candidate_query_contract': protocol['portals'], 'planner_source': binding(__file__),
        'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    require(plan['actual_probe_call_count'] <= 262144, 'Registered probe bound exceeded')
    write_json(args.output / 'plan.json', plan)
    return plan


def selftest(output):
    output.mkdir(parents=True, exist_ok=False)
    # Deliberately malformed pilot headers prove extraction never examines the prefix.
    records = np.asarray([[-99, 100, 101], [-99, 102, 103], [2, 104, 105], [2, 106, 107]], dtype='<i4')
    parent = output / 'synthetic.ivecs'
    write_raw(parent, records)
    expected = records[2:, 1:].copy()
    info = {'path': str(parent), 'header': {'n': 4, 'd': 2, 'bytes': records.nbytes}, 'sha256': sha(parent)}
    got, provenance = read_vec_suffix(info, 2, 2, '<i4', hashlib.sha256(expected.tobytes()).hexdigest())
    require(np.array_equal(got, expected) and provenance['read_byte_range'] == [24, 48], 'Suffix boundary failure')
    rejected = []
    for name, expected_sha in [('wrong_sha', '0'*64)]:
        try:
            read_vec_suffix(info, 2, 2, '<i4', expected_sha)
        except ValueError:
            rejected.append(name)
    bad = records.copy(); bad[2, 0] = 3
    bad_path = output / 'bad_header.ivecs'; write_raw(bad_path, bad)
    try:
        read_vec_suffix(dict(info, path=str(bad_path)), 2, 2, '<i4', hashlib.sha256(expected.tobytes()).hexdigest())
    except ValueError:
        rejected.append('bad_fit_header')
    labels = np.repeat(np.arange(3, dtype='<u2'), 5)
    gt = np.asarray([[1, 2, 5], [2, 1, 5], [2, 3, 7]], dtype='<i4')
    candidate, fallback = candidate_lists(labels, gt, 3, 5)
    require(candidate == [[2, 1, 3, 0, 4], [5, 7, 6, 8, 9], [10, 11, 12, 13, 14]], 'Frequency/tie/fallback wrong')
    require(fallback == [2, 3, 5], 'Fallback count wrong')
    ids = [10000, 10001, 10002, 10003]
    one = selected_query_ids('synthetic', 2, ids, limit=3)
    two = selected_query_ids('synthetic', 2, ids[::-1], limit=3)
    require(one == two and len(set(one)) == 3, 'Query sampling depends on input iteration order')
    require(selected_query_ids('synthetic', 2, [], limit=128) == [], 'Empty leaf query fallback')
    require(set(rejected) == {'wrong_sha', 'bad_fit_header'}, 'Required bad inputs not rejected')
    chain = output / 'synthetic_chain'
    (chain / 'gates').mkdir(parents=True)
    audit_path = chain / 'audit.json'; write_json(audit_path, {'synthetic': True})
    p0_path = chain / 'gates/P0.json'
    write_json(p0_path, {'stage': 'P0', 'status': 'PASS', 'evidence': [binding(audit_path)]})
    p2 = {'evidence': [binding(p0_path)]}
    verify_audit_link(p2, audit_path, chain)
    audit_path.write_text('{"synthetic": "changed"}\n')
    try:
        verify_audit_link(p2, audit_path, chain)
    except ValueError:
        rejected.append('changed_audit_chain')
    fake_ds = {'fit': {'query_values_sha256': 'q', 'gt_values_sha256': 'g'}, 'graph': {'sha256': 'index'}}
    fake_fit = {'queries_sha256': 'q', 'fit_query_values_sha256': 'q', 'fit_gt_values_sha256': 'g', 'graph_sha256': 'index'}
    verify_fit_fingerprints(fake_fit, fake_ds)
    for key in ('queries_sha256', 'fit_gt_values_sha256', 'graph_sha256'):
        try:
            verify_fit_fingerprints(dict(fake_fit, **{key: 'changed'}), fake_ds)
        except ValueError:
            rejected.append('wrong_' + key)
    require(len(rejected) == 6, 'Provenance chain/fingerprint rejection missing')
    result = {'status': 'PASS', 'physical_suffix_range': provenance['read_byte_range'],
              'malformed_pilot_prefix_ignored': True, 'invalid_cases_rejected': rejected,
              'candidate_frequency_ID_ties_fallback': True, 'query_hash_order_stable': True,
              'real_data_accessed': False, 'source': binding(__file__)}
    write_json(output / 'result.json', result)
    print(json.dumps(result))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='mode', required=True)
    st = sub.add_parser('selftest'); st.add_argument('--output', type=Path, required=True)
    for name in ('inputs', 'plan'):
        c = sub.add_parser(name)
        c.add_argument('--dataset', choices=DATASETS, required=True)
        c.add_argument('--protocol', type=Path, required=True)
        c.add_argument('--gate', type=Path, required=True)
        c.add_argument('--audit', type=Path, required=True)
        c.add_argument('--output', type=Path, required=True)
        if name == 'plan':
            c.add_argument('--fit-manifest', type=Path, required=True)
            c.add_argument('--partition', type=Path, required=True)
            c.add_argument('--source-binding', type=Path, action='append', required=True)
    args = p.parse_args()
    deadline()
    if args.mode == 'selftest':
        selftest(args.output)
        return
    protocol, gate, audit = verify_control(args.protocol, args.gate, args.audit)
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / 'started.json', {'status': 'INCOMPLETE', 'mode': args.mode,
                                            'argv': sys.argv, 'source': binding(__file__)})
    try:
        result = extract_inputs(args, protocol, audit) if args.mode == 'inputs' else make_plan(args, protocol, audit)
        write_json(args.output / 'complete.json', {'status': 'COMPLETE', 'mode': args.mode})
        print(json.dumps({'status': result['status'], 'mode': args.mode, 'dataset': args.dataset,
                          'output': str(args.output)}))
    except BaseException as error:
        write_json(args.output / 'failure.json', {'status': 'INCOMPLETE', 'error': repr(error)})
        raise


if __name__ == '__main__':
    main()
