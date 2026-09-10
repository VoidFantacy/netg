#!/usr/bin/env python3
"""Verify original immutable artifacts and frozen models after all query jobs."""
from pathlib import Path
import time
import numpy as np
from common import DATASETS, ROOT, RUN, dump, identity, read, sha

started=time.monotonic();checks=[]
assert read(RUN/'reviews/result_verification.json')['status']=='PASS'
cfg=read(RUN/'config.locked.json');assert sha(RUN/'protocol.md')==cfg['protocol_sha256']
mutable_docs={str(ROOT/x) for x in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']}
for item in read(RUN/'reviews/protected_before.json'):
    path=Path(item['path'])
    if path.suffix!='.a':
        snap=RUN/'source_before'/path.relative_to(ROOT)
        assert sha(snap)==item['sha256'],f'snapshot changed: {path}'
    if str(path) not in mutable_docs:
        assert sha(path)==item['sha256'],f'original changed: {path}'
        checks.append({'path':str(path),'sha256':item['sha256'],'status':'UNCHANGED'})
for item in read(RUN/'inputs/preflight.json')['files']:
    assert sha(item['path'])==item['sha256'],f'original input changed: {item["path"]}'
    checks.append({'path':item['path'],'sha256':item['sha256'],'status':'INPUT_UNCHANGED'})
    if item['bytes']>1<<30:print('VERIFIED_LARGE_INPUT',item['path'],flush=True)
for item in read(RUN/'models/frozen_before_validation.json')['files']:
    assert sha(item['path'])==item['sha256'],f'frozen model changed: {item["path"]}'
for build in (RUN/'bin').glob('*.build.json'):
    b=read(build);assert b['exit_code']==0
    assert sha(b['binary']['path'])==b['binary']['sha256']
    for source in b['sources']:
        p=Path(source['path'])
        if sha(p)!=source['sha256']:
            retained=RUN/'bin/evaluate_v1_sources'/p.name
            assert retained.exists() and sha(retained)==source['sha256'],f'compiled source missing: {p}'
profiles=[]
for ds in DATASETS:
    inp=RUN/'inputs'/ds;prep=read(inp/'prepared.json');h,d=prep['H'],prep['dim']
    p=np.fromfile(inp/'P0.f32',dtype='<f4').reshape(h,d).astype('float64')
    complete=read(RUN/'models'/ds/'complete.json');assert len(complete['models'])==6
    assert not any(complete[k] for k in ['cal_used','audit_used','validation_used','heldout_used'])
    for model in complete['models']:
        path=Path(model['W']);delta=np.load(path.parent/'D.f64.npy')
        actual=np.fromfile(path,dtype='<f4').reshape(h,d)
        expected=(p+prep['tau']*delta).astype('<f4')
        assert np.array_equal(expected,actual),'folded model does not match optimized delta'
        report=read(path.parent/'training.json')
        if model['family']=='full':assert report['full_solver_certified_to_1e-6']
        else:
            factors=np.load(path.parent/'factors.npz')
            assert factors['V'].shape==(d,8) and factors['Z'].shape==(8,h)
            assert np.allclose((factors['V']@factors['Z']).T,delta,rtol=1e-12,atol=1e-12)
    cal=read(RUN/'diagnostics'/ds/'cal/results.json')
    by_name={x['configuration']['model_name']:x for x in cal['methods'] if not x['configuration']['exact']}
    selection=read(RUN/'models'/ds/'selection.json')
    for family in ['full','rank8']:
        group=[x for x in complete['models'] if x['family']==family]
        expected=min(group,key=lambda x:(-by_name[x['name']]['total_hits'],by_name[x['name']]['mean_graph_ndc'],-x['lambda']))
        assert selection['selected_new_candidates'][family]['name']==expected['name']
    for family in ['fast30k_3','fast20k_3','full','rank8']:
        hashes={sha(RUN/'results'/ds/f'{family}_L{L}.hnsw') for L in cfg['L']}
        assert len(hashes)==1,f'router graph differs across L: {ds} {family}'
        profiles.append({'dataset':ds,'family':family,'five_L_router_graph_sha256':next(iter(hashes))})
    rows=[np.fromfile(inp/sp/'row_ids.i64',dtype='<i8') for sp in ['fit','cal','audit']]
    assert all(not np.intersect1d(rows[i],rows[j]).size for i in range(3) for j in range(i+1,3))
    freeze=read(RUN/'models/frozen_before_validation.json')['created_unix']
    assert (inp/'validation/queries.f32').stat().st_mtime>=freeze
dump(RUN/'reviews/immutable_integrity.json',{'status':'PASS','seconds':time.monotonic()-started,
    'original_identity_checks':checks,'fixed_micrographs':profiles,'model_fold_and_rank_checks':12,
    'cal_selection_recomputed':True,'fit_cal_audit_row_disjoint':True,'validation_copy_after_model_freeze':True})
print('IMMUTABLE_INTEGRITY_PASS',flush=True)
