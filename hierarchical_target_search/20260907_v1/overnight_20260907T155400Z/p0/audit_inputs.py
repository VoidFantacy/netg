#!/usr/bin/env python3
"""Read-only P0 input audit. Full mode must run under the overnight supervisor.

No held-out query/GT file is opened. Header parsing matches IndexACSG.cpp v1.
Output roots must not exist; all datasets are processed sequentially.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import struct
import time

import numpy as np

ROOT = Path('/data/netg/ACSG')
DATASETS = ('webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1')
DEADLINE = 1788822000  # 2026-09-07T23:00:00Z


def check_deadline():
    if time.time() >= DEADLINE:
        raise RuntimeError('research deadline reached; no further input audit work')


def sha256(path):
    h = hashlib.sha256()
    started = previous = time.perf_counter()
    done = 0
    size = Path(path).stat().st_size
    with Path(path).open('rb') as f:
        while True:
            check_deadline()
            chunk = f.read(16 << 20)
            if not chunk:
                return h.hexdigest()
            h.update(chunk)
            done += len(chunk)
            now = time.perf_counter()
            if now - previous >= 10:
                rate = done / max(now - started, 1e-9)
                print('CHECKSUM_PROGRESS', str(path),
                      f'{done}/{size} bytes {rate/(1<<20):.1f} MiB/s ETA={(size-done)/rate:.1f}s', flush=True)
                previous = now


def graph_header(path):
    """Parse only header/length metadata, seeking over large payloads."""
    with Path(path).open('rb') as f:
        def read(fmt):
            size = struct.calcsize('<' + fmt)
            data = f.read(size)
            if len(data) != size:
                raise ValueError('truncated graph header')
            values = struct.unpack('<' + fmt, data)
            return values[0] if len(values) == 1 else values
        version = read('i')
        if version != 1:
            raise ValueError(f'only audited v1 binary graph accepted, got {version}')
        n, d, metric, trained, built, build_type = read('qiibbB')
        alpha, beta, rho, lam, iterations, rejection, search_l, degree, entry, ants = read('ffffiiiiiq')
        pheromone_size = read('Q')
        if pheromone_size != n:
            raise ValueError('pheromone row count mismatch')
        f.seek(pheromone_size * 4, 1)
        weight_size = read('Q')
        if weight_size != n:
            raise ValueError('weight row count mismatch')
        f.seek(weight_size * 4, 1)
        graph_k, neighbor_count = read('iQ')
        adjacency_offset = f.tell()
        if graph_k != degree or neighbor_count != n * degree:
            raise ValueError('adjacency shape mismatch')
        f.seek(neighbor_count * 4, 1)
        vector_count = read('Q')
        vector_offset = f.tell()
        expected_bytes = vector_offset + vector_count * 4
    if vector_count != n * d or expected_bytes != Path(path).stat().st_size:
        raise ValueError('embedded vector shape/file size mismatch')
    if metric != 0 or not trained or not built or not (0 <= entry < n):
        raise ValueError('graph metric/build/entry contract mismatch')
    return dict(format='IndexACSG native little-endian binary v1', version=version,
                n=n, d=d, metric_enum=metric, degree=degree, enterpoint=entry,
                adjacency_offset=adjacency_offset, neighbor_count=neighbor_count,
                vector_offset=vector_offset, vector_count=vector_count,
                bytes=expected_bytes, padding=-1)


def vecs_header(path):
    with Path(path).open('rb') as f:
        d, = struct.unpack('<i', f.read(4))
    size = Path(path).stat().st_size
    if d <= 0 or size % (4 * (d + 1)):
        raise ValueError('invalid vecs shape')
    return dict(n=size // (4 * (d + 1)), d=d, bytes=size)


def vecs(path, dtype):
    h = vecs_header(path)
    rows = np.memmap(path, mode='r', dtype='<i4', shape=(h['n'], h['d'] + 1))
    if not np.all(rows[:, 0] == h['d']):
        raise ValueError('inconsistent vecs row headers')
    values = rows[:, 1:].view(dtype)
    return values


def array_hash(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()


def overlaps(arrays):
    fingerprints = {}
    for name, arr in arrays.items():
        check_deadline()
        fingerprints[name] = {hashlib.sha256(np.ascontiguousarray(row).tobytes()).digest() for row in arr}
    return dict(duplicates={k: len(arrays[k]) - len(v) for k, v in fingerprints.items()},
                pairs={a+'__'+b: len(fingerprints[a] & fingerprints[b])
                       for a, b in itertools.combinations(fingerprints, 2)})


def audit_dataset(dataset, full):
    check_deadline()
    settings_path = ROOT / 'benches/datasets/settings.json'
    settings = json.loads(settings_path.read_text())
    cfg = settings['datasets'][dataset]
    data = ROOT / settings['root_dir'] / cfg['dataset_dir']
    mp = data / 'manifest.json'
    manifest = json.loads(mp.read_text())
    old_protocol_path = ROOT / 'target_basin_formalization/20260907_v1/protocol.json'
    old = next(x for x in json.loads(old_protocol_path.read_text())['datasets'] if x['key'] == dataset)
    graph = ROOT / 'indices' / (dataset+'_index') / 'acosp_nsg.json'
    ip = Path(str(graph) + '.info')
    info = json.loads(ip.read_text())
    gh = graph_header(graph)
    for k in ('metric', 'normalization', 'artifact_version'):
        if not (cfg[k] == manifest[k] == info[k]):
            raise ValueError(f'{dataset} {k} contract differs')
    if gh['n'] != cfg['nvecs'] or gh['degree'] != 64:
        raise ValueError('graph row/degree contract differs')
    if info['parameters']['L_build'] != 100 or info['parameters']['C'] != 512:
        raise ValueError('frozen graph parameters differ')
    if sha256(mp) != old['manifest_sha256'] or sha256(ip) != old['graph_info_sha256']:
        raise ValueError('manifest/graph-info checksum differs from frozen protocol')
    if gh['bytes'] != old['graph_bytes']:
        raise ValueError('graph byte count differs from frozen protocol')
    result = dict(dataset=dataset, metric=cfg['metric'], normalization=cfg['normalization'],
                  artifact_version=cfg['artifact_version'], configuration=cfg,
                  settings_sha256=sha256(settings_path), manifest=dict(path=str(mp), sha256=sha256(mp)),
                  graph=dict(path=str(graph), info_path=str(ip), info_sha256=sha256(ip),
                             expected_sha256=old['graph_sha256'], header=gh), files={},
                  heldout_accessed=False,
                  heldout_isolation_evidence='Inherited unchanged dataset manifest zero-overlap records; held-out files not opened',
                  fit=dict(parent_split='router_train', row_range=[10000,30000], n=20000),
                  pilot=dict(parent_split='router_train', row_range=[0,10000], n=10000,
                             historical_development=True))
    expected_rows = dict(base_path=cfg['nvecs'], acpg_query_path=5000, acpg_gt_path=5000,
                         drl_train_query_path=30000, drl_train_gt_path=30000,
                         validation_query_path=10000, validation_gt_path=10000)
    for role, n in expected_rows.items():
        p = data / cfg[role]
        h = vecs_header(p)
        expected_d = 100 if 'gt_path' in role else gh['d']
        if h['n'] != n or h['d'] != expected_d or h['bytes'] != manifest['files'][p.name]['bytes']:
            raise ValueError(f'{role} shape mismatch: {h}')
        entry = dict(path=str(p), header=h, expected_sha256=manifest['files'][p.name]['sha256'])
        if full:
            before = time.perf_counter()
            entry['sha256'] = sha256(p)
            entry['checksum_wall_seconds'] = time.perf_counter()-before
            if entry['sha256'] != entry['expected_sha256']:
                raise ValueError(f'{p} checksum differs')
        result['files'][role] = entry
    if full:
        before = time.perf_counter()
        result['graph']['sha256'] = sha256(graph)
        result['graph']['checksum_wall_seconds'] = time.perf_counter()-before
        if result['graph']['sha256'] != old['graph_sha256']:
            raise ValueError('graph checksum differs')
        adjacency = np.memmap(graph, mode='r', dtype='<i4', offset=gh['adjacency_offset'], shape=(gh['n'], gh['degree']))
        invalid = padding = edges = self_edges = 0
        for start in range(0, gh['n'], 65536):
            check_deadline()
            a = adjacency[start:start+65536]
            invalid += int(np.count_nonzero((a < -1) | (a >= gh['n'])))
            padding += int(np.count_nonzero(a == -1))
            edges += int(np.count_nonzero(a >= 0))
            self_edges += int(np.count_nonzero(a == np.arange(start, start+len(a))[:, None]))
        result['graph']['adjacency_scan'] = dict(invalid_edges=invalid, padding=padding,
                                               valid_edges=edges, self_edges=self_edges)
        if invalid:
            raise ValueError('graph has non-padding invalid IDs')
        query = {k: vecs(data/cfg[v], '<f4') for k,v in
                 dict(qgt='acpg_query_path', router='drl_train_query_path', validation='validation_query_path').items()}
        split_arrays = dict(qgt=query['qgt'], pilot=query['router'][:10000],
                            fit=query['router'][10000:30000], validation=query['validation'])
        ov = overlaps(split_arrays)
        result['query_overlap'] = ov
        if any(ov['pairs'].values()) or any(ov['duplicates'].values()):
            raise ValueError('query split overlap/duplicates')
        for name, a in split_arrays.items():
            if not np.isfinite(a).all():
                raise ValueError('nonfinite query value')
        gt = vecs(data/cfg['drl_train_gt_path'], '<i4')
        for role in ('acpg_gt_path', 'drl_train_gt_path', 'validation_gt_path'):
            g = vecs(data/cfg[role], '<i4')
            if g.min() < 0 or g.max() >= gh['n']:
                raise ValueError('GT node outside base')
            if np.any(np.diff(np.sort(g,axis=1),axis=1) == 0):
                raise ValueError('duplicate IDs within GT row')
        for name, lo, hi in [('pilot',0,10000), ('fit',10000,30000)]:
            result[name].update(query_values_sha256=array_hash(query['router'][lo:hi]),
                                gt_values_sha256=array_hash(gt[lo:hi]),
                                parent_row_ids_sha256=array_hash(np.arange(lo,hi,dtype='<i4')))
    # Raw QGT reuse only. Old 30K prototypes are metadata-listed, never loaded.
    raw_sources = []
    base = None
    if full:
        bh = vecs_header(data/cfg['base_path'])
        base = np.memmap(data/cfg['base_path'],mode='r',dtype='<i4',shape=(bh['n'],bh['d']+1))
    for seed in (20260828,20260829,20260830):
        vp = ROOT / 'fast_entry_variants' / f'{dataset}_seed{seed}' / 'manifest.json'
        m = json.loads(vp.read_text()); v = m['variants']['qgt_cover']
        if m['dataset'] != dataset or m['artifact_version'] != cfg['artifact_version'] or not m['qgt_only']:
            raise ValueError('QGT source contract mismatch')
        for a, b in [('aco_queries_sha256','acpg_query_path'),('aco_gt_sha256','acpg_gt_path')]:
            if m['sources'][a] != manifest['files'][cfg[b]]['sha256']:
                raise ValueError('QGT source checksum mismatch')
        hp, ids_path = ROOT/v['hubs_file'], ROOT/v['ids_file']
        if sha256(hp) != v['hubs_sha256'] or sha256(ids_path) != v['ids_sha256']:
            raise ValueError('QGT output checksum mismatch')
        ids = np.fromfile(ids_path,dtype='<i4'); hubs=np.fromfile(hp,dtype='<f4')
        if len(ids) != old['hub_budget'] or hubs.size != len(ids)*gh['d'] or len(np.unique(ids)) != len(ids):
            raise ValueError('QGT shape/unique ID mismatch')
        if ids.min() < 0 or ids.max() >= gh['n'] or not np.isfinite(hubs).all():
            raise ValueError('invalid QGT values')
        record = dict(seed=seed, manifest_path=str(vp), manifest_sha256=sha256(vp),
                      hubs_path=str(hp), hubs_sha256=v['hubs_sha256'], ids_path=str(ids_path),
                      ids_sha256=v['ids_sha256'], hub_count=len(ids),
                      old_prototype_fit_queries=m['variants']['qgt_gt_basin_prototype']['train_queries'],
                      old_prototype_permitted_as_new_model_input=False)
        if full:
            selected=base[ids]
            if not np.all(selected[:,0] == gh['d']) or not np.array_equal(selected[:,1:].view('<f4'),hubs.reshape(len(ids),gh['d'])):
                raise ValueError('raw hubs differ from base vectors')
            record['raw_hubs_byte_equal_base']=True
        raw_sources.append(record)
    result['qgt_raw_hubs']=raw_sources
    result['status']='PASS_INPUT_CONTRACT' if full else 'LIGHT_CHECKS_PASS_FULL_CHECKS_REQUIRED'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['light','full'],required=True)
    p.add_argument('--dataset',choices=['both',*DATASETS],default='both')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); check_deadline()
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(schema_version=1,stage='P0',mode=args.mode,started_unix=time.time(),
                status='INCOMPLETE',heldout_accessed=False,datasets=[],
                research_performance_gate_passed=False,
                deadline_utc='2026-09-07T23:00:00Z',script_sha256=sha256(Path(__file__)))
    out=args.output/'audit.json'
    def save():
        tmp=out.with_suffix('.json.partial');tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,out)
    save()
    try:
        for dataset in DATASETS if args.dataset=='both' else [args.dataset]:
            print('AUDIT_START',dataset,args.mode,flush=True)
            report['datasets'].append(audit_dataset(dataset,args.mode=='full'));save()
            print('AUDIT_DONE',dataset,flush=True)
        report['status']='PASS_INPUT_CONTRACT' if args.mode=='full' else 'LIGHT_CHECKS_PASS_FULL_CHECKS_REQUIRED'
    except BaseException as exc:
        report['error']=repr(exc);save();raise
    finally:
        report['finished_unix']=time.time();report['wall_seconds']=report['finished_unix']-report['started_unix'];save()
    print(json.dumps(dict(status=report['status'],wall_seconds=report['wall_seconds'],output=str(out))),flush=True)


if __name__=='__main__':
    main()
