from common import *
started = time.perf_counter()
SCRATCH.mkdir(exist_ok=True)
roles = []
for ds in DS:
    c = read(OLD / 'configs' / f'{ds}.A.json')
    x = view(c['train_queries']); g = gt(c['train_gt'])
    public_c = read(R.parent / '20261028_seven_dataset_scoring_v1/configs' / f'{ds}.json')
    public = view(public_c['queries'])
    vector_hash = lambda a: hashlib.sha256(np.asarray(a, dtype='<f4').tobytes()).digest()
    excluded = set(vector_hash(a) for a in public)
    excluded.update(vector_hash(a) for a in x[:8000])
    order = np.random.Generator(np.random.PCG64(19720261101)).permutation(np.arange(8000, 16000))
    chosen = []
    for i in order:
        h = vector_hash(x[i])
        if h in excluded: continue
        chosen.append(int(i)); excluded.add(h)
        if len(chosen) == 3072: break
    assert len(chosen) == 3072, (ds, len(chosen))
    path = R / 'storage' / 'inputs' / ds; path.mkdir(parents=True)
    np.asarray(chosen, '<i4').tofile(path / 'source_rows.i32')
    np.asarray(x[chosen], '<f4').tofile(path / 'queries.f32')
    np.asarray(g[chosen], '<i4').tofile(path / 'gt.i32')
    prepared = dict(c, queries=dict(path=str(path / 'queries.f32'), format='raw_f32', n=3072, d=x.shape[1]),
                    test_gt=dict(path=str(path / 'gt.i32'), format='raw_i32', n=3072, k=100),
                    output_dir=str(R / 'storage' / 'labels' / ds),
                    q8_table=str(R / 'storage' / 'models' / ds / 'Q8-B32.bin'),
                    scratch=str(SCRATCH / ds), experiment_root=str(R))
    dump(R / 'configs' / f'{ds}.labels.json', prepared)
    for window in ['A', 'B']:
        old = read(OLD / 'configs' / f'{ds}.{window}.json')
        formal = dict(prepared, queries=old['queries'], test_gt=old['test_gt'], window=window,
                      output_dir=str(R / 'storage' / 'results' / ds / window))
        dump(R / 'configs' / f'{ds}.{window}.json', formal)
    role = dict(dataset=ds, table_fit_rows='original residual [0,8000)', selector_fit_rows=chosen[:2048],
                selector_cal_rows=chosen[2048:], public_windows='E195 exposed A/B',
                excluded_exact_vector_duplicates=True,
                files=[dict(path=str(p), sha256=sha(p)) for p in path.iterdir()],
                original_queries=c['train_queries'], original_GT=c['train_gt'],
                profile_supervision_overlap_disclosed=True)
    roles.append(role)
dump(R / 'role_freeze.json', dict(status='FROZEN_DISJOINT_NEW_TABLE_SELECTOR_ROLES',
    roles=roles, seed=19720261101, selector_fit_n=2048, selector_cal_n=1024,
    no_test_quality_used=True, seconds=time.perf_counter()-started))
print('PREPARED_ROLES', len(roles), flush=True)
