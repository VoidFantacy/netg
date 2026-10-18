#!/usr/bin/env python3
"""Freeze zero-copy E24/E97/E103 WebVid/Yandex references for E183.

Uses the frozen GT10-fit20K prefix16K. Never trains on public tests, generates
GT, runs ANN, or copies vectors. IP GT labels retain their native int64 layout.
"""
import argparse
import json
from pathlib import Path
import struct
import time

import numpy as np

from prepare_l2_assets import (ROOT, CAMPAIGN, E97, E103, require, read_json,
                               sha256, raw, vecs, view_hash)

E24 = ROOT / 'entry_method_exploration/20260910_gt_topk_profiles_v1'
DATASETS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']


def graph_layout(path):
    with Path(path).open('rb') as f:
        def get(fmt):
            return struct.unpack('<' + fmt, f.read(struct.calcsize('<' + fmt)))
        version, n, d, metric, trained, built, build_type = get('iqii??c')
        require(version in (1, 2) and metric == 0 and trained and built, 'IP NSG header')
        alpha, beta, rho, lam, iterations, threads, build_l, radius, ep, ants = get('ffffiiiiiq')
        for _ in range(2):
            count, = get('Q')
            require(count == n, 'IP NSG state')
            f.seek(count * 4, 1)
        width, count = get('iQ')
        require(count == n * width, 'IP NSG adjacency')
        adjacency_offset = f.tell()
        f.seek(count * 4, 1)
        vc, = get('Q')
        require(vc == n * d, 'IP NSG vectors')
        vector_offset = f.tell()
    require(Path(path).stat().st_size == vector_offset + n * d * 4, 'IP NSG tail')
    return dict(version=version, n=n, d=d, metric_id=0, width=width, entrypoint=ep,
                adjacency_offset=adjacency_offset, adjacency_row_stride_bytes=width * 4,
                vector_offset=vector_offset, vector_row_stride_bytes=d * 4,
                vector_dtype='<f4', adjacency_dtype='<i4')


def audit_router(path, ids, w):
    data = Path(path).read_bytes()
    fmt = '<6QiI3QdQ'
    header = struct.calcsize(fmt)
    off0, capacity, n, stride, label_off, vec_off, level, entry, maxm, maxm0, m, mult, ef = struct.unpack_from(fmt, data)
    require(n == len(ids) and capacity >= n and off0 == 0 and 0 <= entry < n, 'IP router shape')
    require(maxm == m == 16 and maxm0 == 32 and ef == 200, 'IP router parameters')
    require(vec_off + w.shape[1] * 4 == label_off and label_off + 8 == stride, 'IP router layout')
    for i in range(n):
        off = header + i * stride
        require(struct.unpack_from('<Q', data, off + label_off)[0] == ids[i], 'IP router labels')
        require(data[off + vec_off:off + label_off] == w[i].tobytes(), 'IP router W bits')
        degree = struct.unpack_from('<I', data, off)[0]
        require(degree <= maxm0 and np.all(np.frombuffer(data, '<u4', degree, off + 4) < n), 'IP router base edges')
    off = header + n * stride
    max_seen = 0
    for i in range(n):
        size = struct.unpack_from('<I', data, off)[0]
        off += 4
        layer_bytes = 4 + maxm * 4
        require(size % layer_bytes == 0, 'IP router upper length')
        max_seen = max(max_seen, size // layer_bytes)
        for p in range(off, off + size, layer_bytes):
            degree = struct.unpack_from('<I', data, p)[0]
            require(degree <= maxm and np.all(np.frombuffer(data, '<u4', degree, p + 4) < n), 'IP router upper edges')
        off += size
    require(off == len(data) and max_seen == level, 'IP router tail')
    return dict(status='PASS', n=n, all_vector_and_label_bytes_match=True,
                all_neighbor_ids_valid=True, M=m, ef_construction=ef, ef_search=10)


def build():
    started = time.perf_counter()
    freeze_path = E97 / 'reviews/frozen_models.json'
    frozen = read_json(freeze_path)
    identities = {}

    def identity(path, expected=None, large=False):
        p = Path(path).resolve()
        key = str(p)
        stat = p.stat()
        expected = expected or frozen['protected'].get(key)
        if key in identities:
            if expected:
                require(identities[key]['sha256'] == expected['sha256'], 'conflicting identity')
            return key
        r = dict(path=key, bytes=stat.st_size, mtime_ns=stat.st_mtime_ns)
        if expected:
            require(stat.st_size == expected['bytes'], f'size drift: {key}')
            if 'mtime_ns' in expected:
                require(stat.st_mtime_ns == expected['mtime_ns'], f'mtime drift: {key}')
            r.update(inherited_sha256=expected['sha256'], inherited_identity_verified=True)
        if large:
            require(expected and 'mtime_ns' in expected, 'large asset lacks stat identity')
            r.update(sha256=expected['sha256'], sha256_scope='inherited_E97_not_rehashed_this_run')
        else:
            r.update(sha256=sha256(p), sha256_scope='current_full_file')
            if expected:
                require(r['sha256'] == expected['sha256'], f'digest drift: {key}')
        identities[key] = r
        return key

    result = dict(schema='E183_IP_ASSETS_V1', status='PASS', datasets={}, identities=identities,
                  dataset_order=DATASETS, source_E24=str(E24), source_E97=str(E97), source_E103=str(E103),
                  source_freeze=identity(freeze_path), copied_vector_or_graph_bytes=0,
                  new_gt_queries=0, new_ann_queries=0)
    for dataset in DATASETS:
        inp, old = E97 / 'inputs' / dataset, E24 / 'inputs' / dataset
        manifest = read_json(inp / 'manifest.json')
        prepared = read_json(old / 'prepared.json')
        n, d = manifest['shape']
        base_path, index_path = Path(manifest['paths']['base_path']), Path(manifest['paths']['index'])
        for p in (inp / 'manifest.json', old / 'prepared.json'):
            identity(p)
        require(manifest['metric_id'] == 0 and manifest['metric'] == 'raw_inner_product', 'IP metric')
        require(prepared['fit_rows'] == [10000, 30000] and prepared['GT_width'] == 100, 'E24 fit role')
        identity(base_path, large=True)
        identity(index_path, large=True)
        layout = graph_layout(index_path)
        require((layout['n'], layout['d']) == (n, d), 'IP graph shape')
        base = vecs(base_path, n, d, all_headers=False)
        stored = np.memmap(index_path, mode='r', dtype='<f4', offset=layout['vector_offset'], shape=(n, d))
        ids_path = inp / 'gt10.ids.i32'
        ids = np.fromfile(ids_path, '<i4')
        identity(ids_path)
        require(len(ids) == prepared['H'] and np.all(np.diff(ids) > 0)
                and np.all((ids >= 0) & (ids < n)), 'IP real hub IDs')
        probe = np.unique(np.concatenate(([0, n - 1], ids, np.random.default_rng(20261017).choice(n, 32, replace=False))))
        require(np.array_equal(base[probe].view('<u4'), stored[probe].view('<u4')), 'IP base/graph sample')
        source_manifest_path = Path(manifest['paths']['manifest'])
        source_manifest = read_json(source_manifest_path)
        identity(source_manifest_path, manifest['identities']['manifest'])
        ds = dict(dataset=dataset, n=n, d=d, metric_id=0, metric='raw_inner_product',
                  normalization=source_manifest['normalization'], index=str(index_path),
                  base_fvecs=str(base_path), base=dict(path=str(base_path), format='fvecs', n=n, d=d),
                  base_raw_view=dict(path=str(index_path), format='raw_f32', n=n, d=d, byte_offset=layout['vector_offset']),
                  graph_layout=layout, H=len(ids), hub_ids=str(ids_path), profiles={}, routers=[], roles={},
                  historical_results=str(E103 / 'results' / dataset),
                  source_manifest=str(source_manifest_path),
                  sampled_base_graph_equality=dict(status='PASS', rows=probe.tolist(), all_base_rows_rechecked=False),
                  public_test_exposure='already exposed in multiple public-test experiments; not blind confirmation')
        for short, oldname, displayed in [('hard', 'gt10_hard', 'GT10-hard'), ('soft', 'gt10_soft_t1', 'GT10-soft-t1')]:
            w_path = E97 / 'models' / dataset / oldname / 'W.f32'
            w = raw(w_path, len(ids), d)
            require(np.isfinite(w).all() and np.allclose(np.linalg.norm(w, axis=1), 1, rtol=0, atol=2e-6), 'IP unit profiles')
            graph = E97 / 'results' / dataset / 'k100' / (displayed + '.hnsw')
            k1graph = E97 / 'results' / dataset / 'k1' / (displayed + '.hnsw')
            for p in (w_path, graph, k1graph):
                identity(p)
            require(identities[str(graph)]['sha256'] == identities[str(k1graph)]['sha256'], 'IP K1/K100 router identity')
            check = audit_router(graph, ids, w)
            ds['profiles'][short] = dict(W=str(w_path), router_hnsw=str(graph), entry_order='ascending_real_id', audit=check)
            ds['routers'].append(dict(name=short, ids=str(ids_path), W=str(w_path), graph=str(graph), route_order='sorted_ids'))
        trainq_path = Path(manifest['paths']['drl_train_query_path'])
        traingt_path = Path(manifest['paths']['drl_train_gt_path'])
        trainq, traingt = vecs(trainq_path, 30000, d), vecs(traingt_path, 30000, 100, '<i4')
        identity(trainq_path, manifest['identities']['drl_train_query_path'])
        identity(traingt_path, manifest['identities']['drl_train_gt_path'])
        fitq_path, fitgt_path, row_path = old / 'fit/queries.f32', old / 'fit/gt.i64', old / 'fit/row_ids.i64'
        fitq, fitgt = raw(fitq_path, 20000, d), raw(fitgt_path, 20000, 100, '<i8')
        row_ids = np.fromfile(row_path, '<i8')
        require(np.array_equal(row_ids, np.arange(10000, 30000)), 'E24 row IDs')
        require(np.array_equal(fitq.view('<u4'), trainq[10000:30000].view('<u4'))
                and np.array_equal(fitgt, traingt[10000:30000]), 'E24 raw fit/source parity')
        for p in (fitq_path, fitgt_path, row_path):
            identity(p)
        fit = dict(query_raw=str(fitq_path), gt_raw=str(fitgt_path), gt_dtype='<i8', gt_format='raw', gt_k=100,
                   rows=20000, container_rows=20000, row_start=0, query_byte_offset=0, gt_byte_offset=0,
                   queries=dict(path=str(fitq_path), format='raw_f32', n=20000, d=d, total_n=20000),
                   source_rows_raw=str(row_path), source_rows_byte_offset=0, source_namespace=str(trainq_path),
                   source_container_rows=[10000, 30000], query_view_sha256=view_hash(fitq), gt_view_sha256=view_hash(fitgt),
                   gt_provenance=str(source_manifest_path), new_exact_gt_recomputation=False)
        ds['roles']['fit'] = fit
        ds['roles']['profile_fit'] = dict(fit, purpose='frozen E24 profile fit20K')
        for role, start, rows, purpose in [('residual_fit', 0, 16000, 'shared with GT10 profile training'),
                                         ('diagnostic_fit_tail', 16000, 4000, 'not residual-fit; already used for GT10 profiles')]:
            ds['roles'][role] = dict(fit, rows=rows, row_start=start, query_byte_offset=start * d * 4,
                                    gt_byte_offset=start * 100 * 8, source_rows_byte_offset=start * 8,
                                    queries=dict(path=str(fitq_path), format='raw_f32', n=rows, d=d, total_n=20000, row_start=start),
                                    purpose=purpose, shared_with_profile_training=True,
                                    query_view_sha256=view_hash(fitq[start:start + rows]),
                                    gt_view_sha256=view_hash(fitgt[start:start + rows]))
        qgt_path, qgtgt_path = Path(manifest['paths']['acpg_query_path']), Path(manifest['paths']['acpg_gt_path'])
        test_path, testgt_path = Path(manifest['paths']['query_path']), Path(manifest['paths']['gt_path'])
        arrays = {'fit': fitq}
        gt_arrays = [fitgt]
        for role, qp, gp, count, qkey, gkey in [
                ('qgt', qgt_path, qgtgt_path, 5000, 'acpg_query_path', 'acpg_gt_path'),
                ('test', test_path, testgt_path, 10000, 'query_path', 'gt_path')]:
            q, gt = vecs(qp, count, d), vecs(gp, count, 100, '<i4')
            identity(qp, manifest['identities'][qkey])
            identity(gp, manifest['identities'][gkey])
            arrays[role], gt_arrays = q, gt_arrays + [gt]
            ds['roles'][role] = dict(query_fvecs=str(qp), queries=dict(path=str(qp), format='fvecs', n=count, d=d),
                                    gt_ivecs=str(gp), gt_dtype='<i4', gt_format='ivecs', gt_k=100,
                                    rows=count, container_rows=count, row_start=0, gt_provenance=str(source_manifest_path),
                                    new_exact_gt_recomputation=False)
        for role, start, count in [('cal', 0, 1024), ('gate_monitor', 2048, 1024)]:
            qp, gp = inp / (role + '.f32'), inp / (role + '.gt.i32')
            q, gt = raw(qp, count, d), raw(gp, count, 100, '<i4')
            require(np.array_equal(q.view('<u4'), trainq[start:start + count].view('<u4'))
                    and np.array_equal(gt, traingt[start:start + count]), 'IP aux source parity')
            identity(qp)
            identity(gp)
            arrays[role], gt_arrays = q, gt_arrays + [gt]
            ds['roles'][role] = dict(query_raw=str(qp), gt_raw=str(gp), gt_dtype='<i4', gt_format='raw', gt_k=100,
                                    queries=dict(path=str(qp), format='raw_f32', n=count, d=d),
                                    rows=count, container_rows=count, row_start=0, query_byte_offset=0, gt_byte_offset=0,
                                    source_namespace=str(trainq_path), source_container_rows=[start, start + count],
                                    purpose='historically used auxiliary rows; not newly blind', gt_provenance=str(source_manifest_path))
        import hashlib
        hashes = {}
        for role, q in arrays.items():
            require(np.isfinite(q).all() and np.all(np.linalg.norm(q, axis=1) > 0), 'IP query finite/nonzero')
            hashes[role] = {hashlib.sha256(np.ascontiguousarray(row).tobytes()).digest() for row in q}
            if role != 'test':
                require(len(hashes[role]) == len(q), 'IP training internal duplicate')
        for gt in gt_arrays:
            require(np.all((gt >= 0) & (gt < n)) and np.all(np.diff(np.sort(gt, axis=1), axis=1) > 0), 'IP GT valid IDs')
        names = list(hashes)
        for i, left in enumerate(names):
            for right in names[i + 1:]:
                require(not (hashes[left] & hashes[right]), f'IP cross-role query overlap {left}/{right}')
        ds['role_independence'] = dict(status='PASS', primary_roles=names, exact_query_overlap_across_primary_roles=0,
                                       test_internal_duplicate_count=10000 - len(hashes['test']),
                                       residual_fit_shared_with_profile_fit=True)
        audit_rng = np.random.default_rng(20261017)
        ds['gt_audit_plan'] = dict(status='PREPARED_NOT_EXECUTED', seed=20261017, total_queries=32,
                                  residual_fit_rows=sorted(audit_rng.choice(16000, 16, replace=False).tolist()),
                                  test_rows=sorted(audit_rng.choice(10000, 16, replace=False).tolist()),
                                  metric='full_base_raw_inner_product')
        result['datasets'][dataset] = ds
        print(f'IP_ASSETS_PASS {dataset}: fit16K raw i64 GT, test10K fvecs/ivecs', flush=True)
    result.update(seconds=time.perf_counter() - started, generated_at_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  script_sha256=sha256(__file__), imported_helper_sha256=sha256(Path(__file__).with_name('prepare_l2_assets.py')),
                  limitations=['Public tests and auxiliary roles were previously exposed.',
                               'Residual-fit16K is a prefix of frozen GT10-fit20K.',
                               'Large base/NSG SHA256 values are inherited, with current stat/layout checks.'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    out = CAMPAIGN / 'ip_assets.json'
    require(args.check or not out.exists(), f'Refusing overwrite: {out}')
    result = build()
    if args.check:
        require(read_json(out)['datasets'] == result['datasets'], 'IP manifest differs')
        print('IP_MANIFEST_RECHECK_PASS')
    else:
        with out.open('x') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(out)


if __name__ == '__main__':
    main()
