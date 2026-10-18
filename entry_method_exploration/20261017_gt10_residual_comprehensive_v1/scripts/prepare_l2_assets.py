#!/usr/bin/env python3
"""Read-only E97/E103 asset audit; write only the E183 reference manifest.

No ANN search, GT generation, data copying, model training, or benchmark runs.
Large immutable files retain their historical digest with current stat and sampled
layout checks. --hash-large upgrades them to a current full SHA256 verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import time

import numpy as np

ROOT = Path('/data/netg/ACSG')
CAMPAIGN = Path(__file__).resolve().parents[1]
E97 = ROOT / 'entry_method_exploration/20260915_gate_l2_r1_r100_v1'
E103 = ROOT / 'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1'
DATASETS = ['deep10m_l2_v1', 'sift10m_bigann_l2_v1', 'gist1m_l2_v1']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    return json.loads(Path(path).read_text())


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def view_hash(array):
    h = hashlib.sha256()
    for start in range(0, len(array), 4096):
        h.update(np.ascontiguousarray(array[start:start + 4096]).tobytes())
    return h.hexdigest()


def raw(path, rows, columns, dtype='<f4'):
    require(Path(path).stat().st_size == rows * columns * np.dtype(dtype).itemsize,
            f'raw shape: {path}')
    return np.memmap(path, mode='r', dtype=dtype, shape=(rows, columns))


def vecs(path, rows, columns, dtype='<f4', all_headers=True):
    a = raw(path, rows, columns + 1, dtype)
    headers = a[:, 0].view('<i4')
    if all_headers:
        require(np.all(headers == columns), f'vecs header: {path}')
    return a[:, 1:]


def graph_layout(path):
    with Path(path).open('rb') as f:
        def get(fmt):
            return struct.unpack('<' + fmt, f.read(struct.calcsize('<' + fmt)))
        version, n, d, metric, trained, built, build_type = get('iqii??c')
        require(version in (1, 2) and metric == 1 and trained and built,
                f'NSG header: {path}')
        alpha, beta, rho, lam, iterations, threads, build_l, radius, ep, ants = get('ffffiiiiiq')
        for _ in range(2):
            count, = get('Q')
            require(count == n, f'NSG state count: {path}')
            f.seek(count * 4, 1)
        width, count = get('iQ')
        require(count == n * width, f'NSG adjacency shape: {path}')
        adjacency_offset = f.tell()
        f.seek(count * 4, 1)
        vector_count, = get('Q')
        require(vector_count == n * d, f'NSG base shape: {path}')
        vector_offset = f.tell()
    require(Path(path).stat().st_size == vector_offset + n * d * 4,
            f'NSG trailing length: {path}')
    return dict(version=version, n=n, d=d, metric_id=metric, width=width,
                entrypoint=ep, adjacency_offset=adjacency_offset,
                adjacency_row_stride_bytes=width * 4, vector_offset=vector_offset,
                vector_row_stride_bytes=d * 4, vector_dtype='<f4', adjacency_dtype='<i4')


def audit_hnsw(path, ids, profiles):
    data = Path(path).read_bytes()
    fmt = '<6QiI3QdQ'
    header_size = struct.calcsize(fmt)
    (off0, capacity, n, stride, label_offset, vector_offset, maxlevel,
     entry, max_m, max_m0, m, mult, ef_construction) = struct.unpack_from(fmt, data)
    d = profiles.shape[1]
    require(n == len(ids) == 800 and capacity >= n and off0 == 0,
            f'router count: {path}')
    require(m == max_m == 16 and max_m0 == 32 and ef_construction == 200,
            f'router build parameters: {path}')
    require(0 <= entry < n and vector_offset + d * 4 == label_offset
            and label_offset + 8 == stride, f'router layout: {path}')
    for i in range(n):
        off = header_size + i * stride
        label, = struct.unpack_from('<Q', data, off + label_offset)
        require(label == int(ids[i]), f'router label {i}: {path}')
        require(data[off + vector_offset:off + label_offset] == profiles[i].tobytes(),
                f'router profile bits {i}: {path}')
        degree, = struct.unpack_from('<I', data, off)
        require(degree <= max_m0, f'router base degree {i}: {path}')
        neighbors = np.frombuffer(data, '<u4', count=degree, offset=off + 4)
        require(np.all(neighbors < n), f'router base neighbor {i}: {path}')
    off = header_size + n * stride
    layer_stride = 4 + max_m * 4
    max_seen = 0
    for i in range(n):
        size, = struct.unpack_from('<I', data, off)
        off += 4
        require(size % layer_stride == 0, f'router upper layer length {i}: {path}')
        max_seen = max(max_seen, size // layer_stride)
        for level_offset in range(off, off + size, layer_stride):
            degree, = struct.unpack_from('<I', data, level_offset)
            require(degree <= max_m, f'router upper degree {i}: {path}')
            neighbors = np.frombuffer(data, '<u4', count=degree, offset=level_offset + 4)
            require(np.all(neighbors < n), f'router upper neighbor {i}: {path}')
        off += size
    require(off == len(data) and max_seen == maxlevel, f'router tail: {path}')
    return dict(status='PASS', all_vector_and_label_bytes_match=True,
                all_neighbor_ids_valid=True, n=n, M=m, ef_construction=ef_construction,
                ef_search=10, serialized_metric='not stored; use InnerProductSpace',
                header_bytes=header_size, data_stride_bytes=stride)


def build(hash_large=False):
    started = time.perf_counter()
    freeze_path = E97 / 'reviews/frozen_models.json'
    frozen = read_json(freeze_path)
    protected = frozen['protected']
    require(frozen['status'] == 'PASS', 'E97 frozen models did not pass')
    identities = {}

    def identity(path, large=False):
        path = Path(path).resolve()
        key = str(path)
        if key in identities:
            return key
        stat = path.stat()
        previous = protected.get(key)
        record = dict(path=key, bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
        if previous:
            require(stat.st_size == previous['bytes'], f'inherited size drift: {path}')
            require(stat.st_mtime_ns == previous['mtime_ns'], f'inherited mtime drift: {path}')
            record.update(inherited_sha256=previous['sha256'],
                          inherited_digest_source=str(freeze_path), stat_matches_E97=True)
        if large and not hash_large:
            require(previous is not None, f'large asset lacks inherited digest: {path}')
            record.update(sha256=previous['sha256'], sha256_scope='inherited_E97_not_rehashed_this_run')
        else:
            digest = sha256(path)
            if previous:
                require(digest == previous['sha256'], f'inherited digest drift: {path}')
            record.update(sha256=digest, sha256_scope='current_full_file')
        identities[key] = record
        return key

    output = dict(schema='E183_L2_ASSETS_V1', status='PASS',
                  preparation_kind='read_only_identity_and_layout_audit',
                  copied_vector_or_graph_bytes=0, new_gt_queries=0, new_ann_queries=0,
                  source_freeze=identity(freeze_path), source_E97=str(E97), source_E103=str(E103),
                  dataset_order=DATASETS, datasets={}, identities=identities)
    for dataset in DATASETS:
        inp = E97 / 'inputs' / dataset
        model = E97 / 'models' / dataset
        manifest_path = inp / 'manifest.json'
        manifest = read_json(manifest_path)
        n, d = manifest['shape']
        require(manifest['metric_id'] == 1 and manifest['metric'] == 'squared_L2'
                and manifest['normalization'] == 'none; preserve supplied vectors',
                f'L2 metric contract: {dataset}')
        base_path = Path(manifest['paths']['base_path'])
        index_path = Path(manifest['paths']['index'])
        identity(manifest_path)
        identity(base_path, large=True)
        identity(index_path, large=True)
        layout = graph_layout(index_path)
        require((layout['n'], layout['d']) == (n, d), 'NSG/manifest shape mismatch')
        base = vecs(base_path, n, d, all_headers=False)
        stored = np.memmap(index_path, mode='r', dtype='<f4',
                           offset=layout['vector_offset'], shape=(n, d))
        hub_path = inp / 'gt10.ids.i32'
        ids = np.fromfile(hub_path, '<i4')
        require(len(ids) == 800 and np.all(np.diff(ids) > 0)
                and np.all((ids >= 0) & (ids < n)), 'hub ID validity')
        identity(hub_path)
        rng = np.random.default_rng(20261017)
        probe = np.unique(np.concatenate(([0, n - 1], ids, rng.choice(n, 32, replace=False))))
        require(np.array_equal(base[probe].view('<u4'), stored[probe].view('<u4'))
                and np.isfinite(base[probe]).all(), 'sampled base/NSG vector equality')
        ds = dict(dataset=dataset, n=n, d=d, metric_id=1, metric='squared_L2',
                  normalization='none', index=str(index_path), base_fvecs=str(base_path),
                  base=dict(path=str(base_path), format='fvecs', n=n, d=d),
                  base_raw_view=dict(path=str(index_path), format='raw_f32', n=n, d=d,
                                     byte_offset=layout['vector_offset']),
                  graph_layout=layout, hub_ids=str(hub_path), H=800, profiles={}, routers=[], roles={},
                  sampled_base_graph_equality=dict(status='PASS', rows=probe.tolist(),
                                                   all_base_rows_rechecked=False),
                  source_manifest=str(manifest_path), provenance=manifest['sources'],
                  historical_results=str(E103 / 'results' / dataset),
                  public_test_exposure='already scored in E97 and E103; not blind confirmation')
        for short, old, displayed in [('hard', 'gt10_hard', 'GT10-hard'),
                                      ('soft', 'gt10_soft_t1', 'GT10-soft-t1')]:
            w_path = model / old / 'W.f32'
            w = raw(w_path, 800, d)
            require(np.isfinite(w).all() and np.allclose(np.linalg.norm(w, axis=1), 1,
                                                       rtol=0, atol=2e-6), 'unit profiles')
            router_path = E97 / 'results' / dataset / 'k100' / (displayed + '.hnsw')
            k1_path = E97 / 'results' / dataset / 'k1' / (displayed + '.hnsw')
            identity(w_path)
            identity(model / old / 'complete.json')
            identity(router_path)
            identity(k1_path)
            require(identities[str(router_path)]['sha256'] == identities[str(k1_path)]['sha256'],
                    'K1/K100 micro graph mismatch')
            check = audit_hnsw(router_path, ids, w)
            ds['profiles'][short] = dict(W=str(w_path), router_hnsw=str(router_path),
                                        entry_order='ascending_real_id', audit=check)
            ds['routers'].append(dict(name=short, ids=str(hub_path), W=str(w_path),
                                      graph=str(router_path), route_order='sorted_ids'))

        if dataset.startswith('deep'):
            learn_path = E97 / 'sources/deep.learn.prefix.fbin'
            learn = np.memmap(learn_path, mode='r', offset=8, dtype='<f4', shape=(50000, d))
            learn_description = dict(path=str(learn_path), format='fbin_prefix', n=50000, d=d)
        elif dataset.startswith('sift'):
            learn_path = E97 / 'sources/bigann.learn.100M.u8bin'
            learn = np.memmap(learn_path, mode='r', offset=8, dtype='u1', shape=(50000, d))
            learn_description = dict(path=str(learn_path), format='u8bin_prefix', n=50000, d=d)
        else:
            learn_path = ROOT / 'benches/datasets/GIST1M/gist_learn.fvecs'
            learn_n = learn_path.stat().st_size // ((d + 1) * 4)
            learn = vecs(learn_path, learn_n, d)
            learn_description = dict(path=str(learn_path), format='fvecs', n=learn_n, d=d)
        identity(learn_path)
        ds['learn_source'] = learn_description
        query_sets, source_sets = {}, {}
        for role, rows in [('qgt', 5000), ('fit', 20000), ('gate_monitor', 1024),
                           ('cal', 1024), ('test', manifest['test_rows'])]:
            query_path, query_vecs_path = inp / (role + '.f32'), inp / (role + '.fvecs')
            gt_path, gt_vecs_path = inp / (role + '.gt.i32'), inp / (role + '.gt.ivecs')
            q, qv = raw(query_path, rows, d), vecs(query_vecs_path, rows, d)
            gt, gtv = raw(gt_path, rows, 100, '<i4'), vecs(gt_vecs_path, rows, 100, '<i4')
            require(np.isfinite(q).all() and np.all(np.linalg.norm(q, axis=1) > 0), 'query finite/nonzero')
            require(np.array_equal(q.view('<u4'), qv.view('<u4')), f'raw/fvecs query: {role}')
            require(np.array_equal(gt, gtv), f'raw/ivecs GT: {role}')
            require(np.all((gt >= 0) & (gt < n))
                    and np.all(np.diff(np.sort(gt, axis=1), axis=1) > 0), 'GT valid unique IDs')
            complete_path = inp / (role + '.gt') / 'complete.json'
            complete = read_json(complete_path)
            require(complete['status'] == 'PASS' and complete['n'] == rows
                    and complete['metric'] == 'squared_L2' and complete['k'] == 100
                    and complete['base_sha256'] == manifest['identities']['base_path']['sha256'],
                    f'GT provenance: {dataset}/{role}')
            for path in (query_path, query_vecs_path, gt_path, gt_vecs_path, complete_path):
                identity(path)
            require(identities[str(gt_vecs_path)]['sha256'] == complete['gt_sha256'], 'GT complete digest')
            descriptor = dict(query_raw=str(query_path), query_fvecs=str(query_vecs_path),
                              queries=dict(path=str(query_path), format='raw_f32', n=rows, d=d, total_n=rows),
                              gt_raw=str(gt_path), gt_ivecs=str(gt_vecs_path), gt_k=100,
                              rows=rows, container_rows=rows, row_start=0,
                              query_byte_offset=0, gt_byte_offset=0,
                              gt_provenance=str(complete_path),
                              existing_gt_full_base_computation_verified_by_metadata=True,
                              new_exact_gt_recomputation=False)
            row_hashes = [hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest() for x in q]
            query_sets[role] = set(row_hashes)
            if role != 'test':
                require(len(query_sets[role]) == rows, f'within-role query duplicates: {role}')
                source_path = inp / (role + '.source_rows.i64')
                source_rows = np.fromfile(source_path, '<i8')
                require(len(source_rows) == rows and np.all(source_rows >= 0)
                        and np.all(source_rows < len(learn)) and len(set(source_rows.tolist())) == rows,
                        f'learn source rows: {role}')
                require(np.array_equal(np.asarray(learn[source_rows], '<f4').view('<u4'), q.view('<u4')),
                        f'query does not match original learn source rows: {role}')
                identity(source_path)
                descriptor.update(source_rows_raw=str(source_path), source_rows_byte_offset=0,
                                  source_namespace=str(learn_path), matches_original_learn_rows=True)
                source_sets[role] = set(source_rows.tolist())
            else:
                descriptor.update(source_namespace=str(manifest['sources']['test']),
                                  source_rows='identity public test row numbers; no copied row file')
            ds['roles'][role] = descriptor
        role_names = list(query_sets)
        for i, left in enumerate(role_names):
            for right in role_names[i + 1:]:
                require(not (query_sets[left] & query_sets[right]), f'cross-role query overlap: {left}/{right}')
                if left in source_sets and right in source_sets:
                    require(not (source_sets[left] & source_sets[right]), 'cross-role source row overlap')
        ds['role_independence'] = dict(status='PASS', exact_query_overlap_across_primary_roles=0,
                                       learn_source_row_overlap_across_primary_roles=0,
                                       primary_roles=role_names,
                                       test_internal_duplicate_count=manifest['test_rows'] - len(query_sets['test']))
        fit = ds['roles']['fit']
        for name, start, count, purpose in [
                ('residual_fit', 0, 16000, 'residual training; shared with GT10 profile-fit20K'),
                ('diagnostic_fit_tail', 16000, 4000, 'not residual-fit; already seen by GT10 profile training')]:
            descriptor = dict(fit)
            descriptor.update(rows=count, row_start=start, query_byte_offset=start * d * 4,
                              gt_byte_offset=start * 100 * 4, source_rows_byte_offset=start * 8,
                              purpose=purpose, shared_with_profile_training=True,
                              queries=dict(path=fit['query_raw'], format='raw_f32', n=count,
                                           d=d, total_n=20000, row_start=start))
            descriptor['query_view_sha256'] = view_hash(raw(fit['query_raw'], 20000, d)[start:start + count])
            descriptor['gt_view_sha256'] = view_hash(raw(fit['gt_raw'], 20000, 100, '<i4')[start:start + count])
            ds['roles'][name] = descriptor
        ds['roles']['profile_fit'] = dict(fit, purpose='existing GT10 profile fitting; frozen20K')
        ds['roles']['gate_monitor']['purpose'] = 'disjoint learn rows; historically used for GATE monitoring'
        ds['roles']['cal']['purpose'] = 'disjoint calibration learn rows; not asserted to be newly blind'
        output['datasets'][dataset] = ds
        audit_rng = np.random.default_rng(20261017)
        ds['gt_audit_plan'] = dict(status='PREPARED_NOT_EXECUTED', seed=20261017,
                                  residual_fit_rows=sorted(audit_rng.choice(16000, 16, replace=False).tolist()),
                                  test_rows=sorted(audit_rng.choice(manifest['test_rows'], 16, replace=False).tolist()),
                                  total_queries=32, metric='full_base_squared_L2',
                                  note='Indices fixed here; exact compute is delegated to the serial controller.')
        print(f'ASSETS_PASS {dataset}: n={n} d={d} fit=16000 test={manifest["test_rows"]}', flush=True)
    output.update(seconds=time.perf_counter() - started,
                  generated_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  script_sha256=sha256(Path(__file__)), full_large_asset_hashing=hash_large,
                  limitations=['Public test queries have historical exposure.',
                               'Residual-fit16K is a subset of existing GT10 profile-fit20K.',
                               'GIST original download checksum is unavailable.',
                               'Inherited large-file hashes are not new full hashes unless explicitly enabled.'])
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hash-large', action='store_true')
    parser.add_argument('--check', action='store_true', help='Reaudit without writing a second manifest.')
    args = parser.parse_args()
    out = CAMPAIGN / 'l2_assets.json'
    if out.exists() and not args.check:
        raise SystemExit(f'Refusing to overwrite frozen manifest: {out}; use --check')
    result = build(args.hash_large)
    if args.check:
        old = read_json(out)
        require(old['datasets'] == result['datasets'], 'Dataset audit differs from frozen manifest')
        print('MANIFEST_RECHECK_PASS', flush=True)
    else:
        with out.open('x') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(out, flush=True)


if __name__ == '__main__':
    main()
