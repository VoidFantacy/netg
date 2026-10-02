"""Inventory and isolate sources/configuration before reading new response statistics."""
from common import *
import shutil

assert not (RUN/'config.locked.json').exists(), 'Preserve this version'
start = time.monotonic()
oldlock = read(OLD/'config.locked.json')
for folder in ['reviews','logs','results','bin','analysis']:
    (RUN/folder).mkdir(exist_ok=True)
for source in (OLD/'src').rglob('*'):
    if source.suffix not in ['.cpp','.hpp']:
        continue
    dest = RUN/'src'/source.relative_to(OLD/'src')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
for name in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
    dest = RUN/'source_before'/name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/name, dest)

lock = dict(experiment='E120', created_unix=time.time(), seed=20260922, n=4096,
    threads=1, cpu=15, max_NSG_calls=335232, planned_NSG_calls=331136,
    job_seconds_cap=1800, total_search_seconds_cap=3600, max_rss_gib=40,
    max_new_bytes=1<<30, min_free_gib=6,
    actions=['DefaultANN','UnitHub1','UnitHub3','GT11','GT13','GT101','GT103'],
    datasets={}, bootstrap_reps=5000, oracle_gain_gate=.0025, transfer_retention_gate=.8,
    info_folds=4, info_neighbors=55, information_methods=['TargetKNN','LowKNN','TargetFixed','ShuffleKNN'])
paths = {OLD/'config.locked.json', OLD/'protocol.md', OLD/'reviews/jobs.json',
         OLD/'reviews/numeric_verification.json', OLD/'results/aligned_hits.npz'}
paths.update(p for p in (OLD/'src').rglob('*') if p.suffix in ['.cpp','.hpp','.py'])
paths.update(Path(x) for x in read(OLD/'reviews/jobs.json')[0]['argv'] if x.endswith('.a'))
paths.update((ROOT/p) for p in ['ACSG/IndexACSG.h','ACSG/ACSG.h','ACSG/detail/CandidatePool.h'])
for ds, cfg in oldlock['datasets'].items():
    oldconfig = OLD/'results'/('main_'+ds)/'config.json'
    native = read(oldconfig)
    paths.add(oldconfig)
    web = ds.startswith('webvid')
    missing = {'1':[640], '100':[1120,1250]} if web else {'1':[96], '100':[200]}
    target = {'1':[640,800], '100':[1120,1250]} if web else {'1':[96,128], '100':[200,256]}
    lock['datasets'][ds] = dict(native=native, missing=missing, target=target,
                               old_K_L=oldlock['K_L'], manifest=cfg['evaluation_manifest'])
    for key in ['queries','GT','rows','hub_ids']:
        paths.add(Path(native[key]))
    for method in native['methods']:
        paths.update(Path(method[key]) for key in ['W','graph','ids'] if key in method)
    paths.add(Path(cfg['evaluation_manifest']))
    # Record the exact old response files used by the future paired analysis.
    paths.update(p for p in (OLD/'results'/('main_'+ds)).rglob('*') if p.is_file())
    meta = read(cfg['evaluation_manifest'])
    assert sha(meta['base']) == meta['base_sha256']
    assert sha(native['queries']) == meta['query_sha256']
    assert sha(native['GT']) == meta['GT_sha256']
    for K, Ls in missing.items():
        for L in Ls:
            ref = Path(native['reference'])/f'k{K}'/(native['reference_method']+f'_L{L}')
            for name in ['ids.i32','distances.f32','entry_ids.i32','graph_ndc.u64','route_ndc.u64']:
                p = ref/name
                assert p.exists(), p
                paths.add(p)
    q = np.fromfile(native['queries'], '<f4').reshape(4096,native['dimension'])
    assert np.isfinite(q).all() and (np.linalg.norm(q,axis=1)>0).all()
    assert len(np.unique(np.fromfile(native['rows'],'<i8'))) == 4096
    assert len({row.tobytes() for row in q}) == 4096
    print('VALIDATED',ds,flush=True)
dump(RUN/'config.locked.json',lock)
dump(RUN/'reviews/protected_before.json',dict(files=[identity(p) for p in sorted(paths)],
    base_hashes_revalidated=True, full_graph_hash_revalidated=False))
dump(RUN/'inventory.json',dict(all_H_labels='E118 L128 only; not target-budget all-H labels',
    E107=dict(queries_per_dataset=4096, methods=8, K_L=oldlock['K_L'], reuse_points=144),
    E118=dict(queries_per_dataset=4096, same_query_set_as_E107=False, max_L=800,
              scope='Context only, not joined to E107 query responses'),
    E103=dict(scope='Already exposed aggregate operating-region guide, not E107 action labels'),
    supplement_points=40, supplement_calls=331136, new_GT=0, new_profiles=0,
    new_graphs=0, formal_QPS=False, preparation_seconds=time.monotonic()-start))
dump(RUN/'state.json',dict(status='PREPARED_SOURCE_ADAPTATION_PENDING',completed=False,
    pending=['L_cap_only_patch','freeze_build','native_smoke','missing_points','response_analysis',
             'conditional_information_control','audit_report_docs'],default_changed=False))
print('PREPARED', len(paths), 'protected files', flush=True)
