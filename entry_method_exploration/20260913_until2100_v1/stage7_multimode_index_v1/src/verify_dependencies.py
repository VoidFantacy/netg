from common import *
threads();resources();old=read(C/'stage2_missing_targets_v1/reviews/prebuild_freeze.json');by_path={x['path']:x for x in old['files']};records=[]
for x in read(O/'reviews/base_graph_stat.json')['sources']:
    original=by_path[x['path']];st=Path(x['path']).stat()
    assert st.st_size==x['bytes']==original['bytes'] and st.st_mtime_ns==x['mtime_ns']==original['mtime_ns']
    records.append(dict(x,inherited_sha256=original['sha256'],stat_matches_original_verified_manifest=True))
norms=[]
for ds in DS:
    d=read(O/'inputs'/ds/'construction.json')['dim']
    for model in ['duplicate3P','mode3P']:
        w=np.fromfile(O/'models'/ds/model/'W.f32',np.float32).reshape(-1,d);error=float(np.max(np.abs(np.linalg.norm(w.astype(float),axis=1)-1)))
        assert np.isfinite(w).all() and error<1e-6;norms.append(dict(dataset=ds,model=model,max_unit_norm_error=error))
dump(O/'reviews/dependency_stat_verification.json',dict(status='PASS',epoch=time.time(),sources=records,profile_norms=norms,
    note='Size and mtime match historical full hash records; this is not a new full hash of base/NSG.'))
print('DEPENDENCY_STAT_AND_UNIT_NORM_PASS',flush=True)
