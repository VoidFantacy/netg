#!/usr/bin/env python3
"""Prepare a fixed training-side Fast diagnosis; never opens validation/test data."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import time
import numpy as np

ROOT = Path('/data/netg/ACSG')
VERSION = ROOT / 'fast_router_diagnosis/20260908_v1'

def sha(path):
    h = hashlib.sha256(); start = last = time.monotonic(); done = 0
    path = Path(path); initial = path.stat()
    with path.open('rb') as f:
        while block := f.read(16 << 20):
            h.update(block); done += len(block)
            now = time.monotonic()
            if now - last >= 10:
                rate = done / (now-start)
                print('HASH', path.name, done, '/', initial.st_size,
                      f'{rate/2**20:.1f} MiB/s ETA {(initial.st_size-done)/rate:.1f}s', flush=True)
                last = now
    final = path.stat()
    if (initial.st_size,initial.st_mtime_ns) != (final.st_size,final.st_mtime_ns):
        raise ValueError('file changed while hashing: '+str(path))
    return {'sha256':h.hexdigest(),'seconds':time.monotonic()-start,'bytes':done,
            'mtime_ns':final.st_mtime_ns}

def array_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

def vecs(path, dtype):
    path = Path(path)
    with path.open('rb') as f: d, = struct.unpack('<i',f.read(4))
    if d <= 0 or path.stat().st_size % (4*(d+1)): raise ValueError('bad vecs: '+str(path))
    rows = np.memmap(path,dtype='<i4',mode='r').reshape(-1,d+1)
    if not np.all(rows[:,0] == d): raise ValueError('inconsistent header: '+str(path))
    return rows[:,1:].view(dtype)

def normalize(x):
    return x / np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)

def order(dataset, role, rows):
    prefix=dataset+'|fast_diagnosis_v1|'+role+'|'
    return sorted(rows,key=lambda i:(hashlib.sha256((prefix+str(i)).encode()).digest(),i))

def save_json(path, value):
    with Path(path).open('x') as f: json.dump(value,f,indent=2,ensure_ascii=False); f.write('\n')

def prepare(ds, base_output):
    started=time.monotonic(); dataset=ds['dataset']; d=ds['dimension']; H=ds['hub_count']
    out=base_output/dataset; out.mkdir(exist_ok=False)
    identities={}
    for role in ['base','graph','query_train','gt_train','prototypes','hub_ids','raw_hubs']:
        print('VERIFY',dataset,role,flush=True)
        rec=sha(ds[role]['path'])
        if rec['sha256'] != ds[role]['expected_sha256']: raise ValueError('identity mismatch '+role)
        identities[role]=dict(path=ds[role]['path'],**rec)
    save_json(out/'verified_identities.json',identities)
    q=np.asarray(vecs(ds['query_train']['path'],'<f4')).copy()
    gt=np.asarray(vecs(ds['gt_train']['path'],'<i4')).copy()
    if q.shape != (30000,d) or gt.shape != (30000,100): raise ValueError('training shape')
    if not np.isfinite(q).all() or np.any(np.linalg.norm(q,axis=1)==0): raise ValueError('bad query')
    if gt.min()<0 or gt.max()>=ds['base_count']: raise ValueError('GT range')
    if any(len(set(row))!=100 for row in gt): raise ValueError('GT duplicate')
    for role, arr in [('query',q[10000:30000]),('gt',gt[10000:30000])]:
        if array_sha(arr)!=ds['fit_values_sha_inherited'][role]: raise ValueError('fit values '+role)
    fingerprints=[hashlib.sha256(row.tobytes()).digest() for row in q]
    if len(set(fingerprints))!=len(q) or set(fingerprints[:10000]) & set(fingerprints[10000:]):
        raise ValueError('query duplicate/overlap')
    pilot=np.array(order(dataset,'pilot',range(10000))[:512],dtype='<i8')
    q64=normalize(q.astype(np.float64))
    similarity=q64[pilot[:128]] @ q64[10000:].T
    nearest=np.argmax(similarity,axis=1).astype(np.int64)+10000
    nearest_set=set(nearest.tolist())
    random_fit=np.array(order(dataset,'random_fit',[i for i in range(10000,30000) if i not in nearest_set])[:128],dtype='<i8')
    aux=np.array(sorted(nearest_set | set(random_fit.tolist())),dtype='<i8')
    row_ids=np.concatenate([pilot,aux]); N=len(row_ids)
    assert N<=768 and len(set(row_ids))==N
    by_row={int(row):i for i,row in enumerate(row_ids)}
    base=vecs(ds['base']['path'],'<f4')
    if base.shape != (ds['base_count'],d): raise ValueError('base shape')
    hub_ids=np.fromfile(ds['hub_ids']['path'],dtype='<i4')
    raw=np.fromfile(ds['raw_hubs']['path'],dtype='<f4').reshape(H,d)
    old=np.fromfile(ds['prototypes']['path'],dtype='<f4').reshape(H,d)
    if len(set(hub_ids.tolist()))!=H or np.any(hub_ids<0) or np.any(hub_ids>=len(base)):
        raise ValueError('invalid hub ids')
    if not np.array_equal(base[hub_ids],raw): raise ValueError('raw hub/base mismatch')
    if not np.isfinite(raw).all() or not np.isfinite(old).all(): raise ValueError('nonfinite model')
    build_path=ROOT/'benches/run/build_fast_entry_variants.py'
    spec=importlib.util.spec_from_file_location('audited_existing_builder',build_path)
    builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
    builder.faiss.omp_set_num_threads(16)
    fit_targets=np.asarray(base[gt[10000:,0]],dtype=np.float32)
    tick=time.monotonic()
    rebuilt,details=builder.build_gt_basin_prototypes(q[10000:],gt[10000:],fit_targets,raw,1.0)
    reconstruction={'seconds':time.monotonic()-tick,'byte_equal':np.array_equal(rebuilt,old),
                    'max_abs_error':float(np.max(np.abs(rebuilt-old))),
                    'rebuilt_values_sha256':array_sha(rebuilt),'details':details,
                    'purpose':'implementation verification only, no model parameter change'}
    save_json(out/'prototype_reconstruction.json',reconstruction)
    if not reconstruction['byte_equal']: raise ValueError('prototype reconstruction mismatch')
    rn=normalize(raw); qn=normalize(q)
    assignments=np.empty(20000,dtype='<i4'); tn=normalize(fit_targets)
    for start in range(0,20000,4096): assignments[start:start+4096]=np.argmax(tn[start:start+4096]@rn.T,axis=1)
    counts=np.bincount(assignments,minlength=H)
    sums=np.zeros_like(raw);np.add.at(sums,assignments,qn[10000:])
    concentration=np.linalg.norm(sums,axis=1)/np.maximum(counts,1)
    chosen_targets=np.asarray(base[gt[row_ids,0]],dtype=np.float32)
    basin=np.argmax(normalize(chosen_targets)@rn.T,axis=1).astype('<i4')
    cosine64=q64[row_ids] @ normalize(old.astype(np.float64)).T
    rawip64=q[row_ids].astype(np.float64) @ raw.astype(np.float64).T
    payloads={'queries.f32':q[row_ids].astype('<f4'),'gt.i64':gt[row_ids].astype('<i8'),
              'row_ids.i64':row_ids,'basin_label_local.i32':basin,
              'prototype_cosine_f64.f64':cosine64.astype('<f8'),'raw_hub_ip_f64.f64':rawip64.astype('<f8'),
              'fit_assignments.i32':assignments,'hub_fit_counts.i32':counts.astype('<i4'),
              'hub_concentration.f64':concentration.astype('<f8')}
    artifacts={}
    for name,arr in payloads.items():
        path=out/name
        with path.open('xb') as f: f.write(np.ascontiguousarray(arr).tobytes())
        artifacts[name]={'path':str(path),'shape':list(arr.shape),'dtype':str(arr.dtype),'sha256':array_sha(arr),'bytes':arr.nbytes}
    pairs=[]
    for i in range(128):
        a=int(nearest[i]);b=int(random_fit[i]);r=int(pilot[i])
        pairs.append({'pilot_local':i,'pilot_row':r,'nearest_fit_row':a,'nearest_fit_local':by_row[a],
                      'random_fit_row':b,'random_fit_local':by_row[b],
                      'nearest_query_cosine':float(similarity[i,a-10000]),
                      'random_query_cosine':float(q64[r]@q64[b]),
                      'nearest_gt10_overlap':len(set(gt[r,:10])&set(gt[a,:10])),
                      'random_gt10_overlap':len(set(gt[r,:10])&set(gt[b,:10]))})
    save_json(out/'sample_manifest.json',{'dataset':dataset,'pilot_count':512,'num_queries':N,
              'row_ids':row_ids.tolist(),'row_roles':['pilot']*512+['auxiliary_fit']*len(aux),
              'selection_rule':'protocol.md section 2; labels unseen at selection',
              'nearest_fit_reference_count':20000,'neighbor_pairs':pairs,
              'query_train_duplicates':0,'pilot_fit_overlap':0,'artifacts':artifacts,
              'base_hubs_byte_equal':True,'fit_values_sha_verified':True})
    config={'schema_version':1,'dataset':dataset,'dim':d,'num_queries':N,'pilot_count':512,
            'hub_count':H,'base_count':ds['base_count'],'gt_k':100,'top_k':10,'L':[64,128],
            'threads':16,'hnsw_seed':20260828,'legacy_hnsw_seed':100,'hnsw_m':16,'hnsw_ef_construction':200,'hnsw_ef':10,
            'index_path':ds['graph']['path'],'queries_file':str(out/'queries.f32'),
            'gt_file':str(out/'gt.i64'),'row_ids':str(out/'row_ids.i64'),
            'hub_ids':ds['hub_ids']['path'],'raw_hubs':ds['raw_hubs']['path'],
            'prototypes':ds['prototypes']['path'],'basin_label_local':str(out/'basin_label_local.i32'),
            'sample_manifest':str(out/'sample_manifest.json'),'verified_identities':str(out/'verified_identities.json')}
    save_json(out/'runner_config.json',config)
    elapsed=time.monotonic()-started
    save_json(out/'completion.json',{'status':'PASS_INPUTS_PREPARED','seconds':elapsed,
              'prototype_reconstruction':'BYTE_IDENTICAL','raw_validation_or_heldout_access':False,
              'search_calls':0,'new_model_parameters':False})
    print('PREPARED',dataset,'rows',N,'seconds',round(elapsed,2),flush=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-paths',type=Path,default=VERSION/'inputs/source_paths.json')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    sources=json.loads(args.source_paths.read_text())
    if any(x['dataset'] not in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'] for x in sources['datasets']): raise ValueError('dataset scope')
    for ds in sources['datasets']: prepare(ds,args.output)
    save_json(args.output/'completion.json',{'status':'PASS_ALL_INPUTS_PREPARED','datasets':[x['dataset'] for x in sources['datasets']]})

if __name__=='__main__':main()
