#!/usr/bin/env python3
"""Rebuild paired Fast prototype from strictly the 20K fit range on CPU."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import numpy as np

ROOT = Path('/data/netg/ACSG')
RUN = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8<<20), b''):
            h.update(b)
    return h.hexdigest()

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset', required=True, choices=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'])
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=20260828)
    a = p.parse_args()
    if time.time() >= dt.datetime(2026,9,7,22,59,tzinfo=dt.timezone.utc).timestamp():
        raise RuntimeError('Research deadline closed')
    audit = json.loads(a.audit.read_text())
    if audit['status'] != 'PASS_INPUT_CONTRACT':
        raise ValueError('Full P0 input audit required')
    ds = next(x for x in audit['datasets'] if x['dataset'] == a.dataset)
    source = next(x for x in ds['qgt_raw_hubs'] if x['seed'] == a.seed)
    code = ROOT/'benches/run/build_fast_entry_variants.py'
    spec = importlib.util.spec_from_file_location('existing_fast_builder', code)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.faiss.omp_set_num_threads(16)
    a.output.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    qpath = Path(ds['files']['drl_train_query_path']['path'])
    gpath = Path(ds['files']['drl_train_gt_path']['path'])
    q = m.read_fvecs(qpath)[10000:30000]
    gt = m.read_ivecs(gpath)[10000:30000]
    for role, values in [('query',q),('gt',gt)]:
        if hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest() != ds['fit'][role+'_values_sha256']:
            raise ValueError('20K fit split differs from audited values')
    hp = Path(source['hubs_path'])
    ids_path = Path(source['ids_path'])
    if sha(hp) != source['hubs_sha256'] or sha(ids_path) != source['ids_sha256']:
        raise ValueError('QGT raw source modified since P0')
    raw = np.fromfile(hp,dtype='<f4').reshape(source['hub_count'],ds['graph']['header']['d'])
    base, dim = m.fvecs_memmap(Path(ds['files']['base_path']['path']))
    selected = np.asarray(base[gt[:,0],1:],dtype=np.float32)
    loaded = time.perf_counter()
    prototype, details = m.build_gt_basin_prototypes(q,gt,selected,raw,1.0)
    finished = time.perf_counter()
    if prototype.shape != raw.shape or not np.isfinite(prototype).all():
        raise ValueError('Invalid rebuilt prototype')
    output = a.output/'prototype.f32'
    prototype.tofile(output)
    details['requires_aco_dpc'] = False
    record = {'schema_version':1,'status':'COMPLETE','dataset':a.dataset,'seed':a.seed,
              'fit_range':[10000,30000],'fit_queries':20000,'pilot_queries_used':0,
              'heldout_accessed':False,'metric':ds['metric'],'normalization':ds['normalization'],
              'hubs_file':str(output.resolve()),'ids_file':str(ids_path.resolve()),
              'hubs_sha256':sha(output),'ids_sha256':source['ids_sha256'],
              'source_raw_hubs':source,'input_audit':str(a.audit.resolve()),'input_audit_sha256':sha(a.audit),
              'fit_query_values_sha256':ds['fit']['query_values_sha256'],
              'fit_gt_values_sha256':ds['fit']['gt_values_sha256'],
              'builder_sha256':sha(code),'wrapper_sha256':sha(Path(__file__)),
              'build_details':details,'load_seconds':loaded-start,
              'prototype_compute_seconds':finished-loaded,'post_existing_GT_wall_seconds':time.perf_counter()-start,
              'offline_cost':{'exact_train_GT_seconds':None,'exact_train_GT_reason':'Compatible preexisting exact GT reused; historical compute time unavailable in this invocation',
                              'qgt_hub_seconds':None,'qgt_hub_reason':'Audited independent 5K QGT raw hubs reused',
                              'prototype_seconds':finished-loaded,'router_index_seconds':None,
                              'router_index_reason':'Measured separately by evaluator during index initialization'},
              'cpu_only':True,'threads':16,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    (a.output/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)

if __name__ == '__main__':
    main()
