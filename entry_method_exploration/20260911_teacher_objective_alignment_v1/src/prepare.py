from common import *
import numpy as np

def protect():
    assert read(E28 / 'state.json')['status'] == 'COMPLETE'
    assert read(E28 / 'reviews/final_audit.json')['status'] == 'PASS'
    old = read(E28 / 'reviews/protected_before.json')
    extra = E28 / 'reviews/extra_baseline_protection.json'
    if extra.exists():
        old += read(extra)
    protected = {x['path']: x for x in old}
    for x in protected.values():
        assert identity(x['path']) == x, x['path']
    for p in sorted(E28.rglob('*')):
        if p.is_file():
            protected[str(p)] = identity(p)
    dump(O / 'reviews/protected_before.json', list(protected.values()))
    for name in ['evaluate.cpp', 'benchmark_with_nsg.cpp', 'legacy_reference.cpp']:
        shutil.copy2(E28 / 'src' / name, O / 'src' / name)
    shutil.copy2(E28 / 'bin/evaluate', O / 'bin/evaluate')
    dump(O / 'bin/evaluate.provenance.json', dict(
        source_build=read(E28 / 'bin/evaluate.build.json'),
        original=identity(E28 / 'bin/evaluate'), copied=identity(O / 'bin/evaluate'),
        runtime_output_from_argv=True))
    assert sha(E28 / 'bin/evaluate') == sha(O / 'bin/evaluate')
    for ds in DS:
        for split in ['fit', 'cal', 'audit', 'validation']:
            c = read(E28 / 'inputs' / ds / split / 'config.json')
            c.update(protocol_sha256=sha(O / 'protocol.md'), query_cpu=15, threads=1)
            dump(O / 'inputs' / ds / split / 'config.json', c)
    dump(O / 'reviews/preflight.json', dict(status='PASS', protected_files=len(protected),
         free_bytes=shutil.disk_usage(O).free, original_kernel_unchanged=True))

def teachers(ds):
    c = read(O / 'inputs' / ds / 'fit/config.json')
    n, h, d = c['num_queries'], c['hub_count'], c['dim']
    old = E28 / 'labels' / ds
    assert read(old / 'complete.json')['status'] == 'COMPLETE'
    gt = np.fromfile(c['gt_file'], np.int64).reshape(n, 100)[:, :10]
    ids = np.memmap(old / 'ids.i32', np.int32, mode='r', shape=(n, 56, 10))
    hits = np.fromfile(old / 'hits.u8', np.uint8).reshape(n, 56)
    masks = np.fromfile(old / 'masks.u16', np.uint16).reshape(n, 56)
    ndc = np.fromfile(old / 'graph_ndc.u32', np.uint32).reshape(n, 56)
    for b in range(0, n, 256):
        found = (ids[b:b+256, :, :, None] == gt[b:b+256, None, None, :]).any(2)
        assert np.array_equal(found.sum(2), hits[b:b+256])
        assert np.array_equal((found * (1 << np.arange(10))).sum(2), masks[b:b+256])
        assert (np.diff(np.sort(ids[b:b+256], axis=2), axis=2) != 0).all()
    proposal = E28 / 'inputs' / ds / 'proposals'
    ts = np.fromfile(proposal / 'triples.i32', np.int32).reshape(n, 56, 3)
    bs = np.fromfile(proposal / 'baseline_triples.i32', np.int32).reshape(n, 2, 3)[:, 1]
    matches = (ts == bs[:, None, :]).all(2)
    assert (matches.sum(1) == 1).all()
    base_slot = matches.argmax(1)
    rows = np.arange(n)
    old_slot = np.fromfile(old / 'teacher_slot.i32', np.int32)
    t0 = np.fromfile(old / 'teacher.i32', np.int32).reshape(n, 3)
    assert np.array_equal(ts[rows, old_slot], t0)
    assert np.array_equal(hits[rows, old_slot], hits.max(1))
    assert np.array_equal(ndc[rows, old_slot], np.where(hits == hits.max(1, keepdims=True), ndc, np.iinfo(np.uint32).max).min(1))
    q = np.fromfile(c['queries_file'], np.float32).reshape(n, d).astype(np.float64)
    p = np.fromfile(E24 / 'models' / ds / 'gt10_hard/W.f32', np.float32).reshape(h, d).astype(np.float64)
    score = q @ p.T
    scores = np.take_along_axis(score[:, None, :], ts, axis=2).sum(2)
    assert np.array_equal(np.lexsort((-scores, ndc, -hits.astype(np.int16)), axis=1)[:, 0], old_slot)
    gain = hits.max(1) > hits[rows, base_slot]
    keep_slot = np.where(gain, old_slot, base_slot)
    t1 = ts[rows, keep_slot]
    assert np.array_equal(t1[gain], t0[gain]) and np.array_equal(t1[~gain], bs[~gain])
    assert np.array_equal(hits[rows, keep_slot], hits[rows, old_slot])
    dest = O / 'inputs' / ds / 'teachers'
    dest.mkdir()
    for name, data in [('cost.i32', t0), ('keep.i32', t1), ('cost_slot.i32', old_slot), ('keep_slot.i32', keep_slot), ('baseline.i32', bs), ('baseline_slot.i32', base_slot)]:
        data.astype(np.int32).tofile(dest / name)
    gain.astype(np.uint8).tofile(dest / 'headroom.u8')
    report = dict(status='PASS', dataset=ds, rows=n, logical_labels_verified=n*56,
                  original_hits=float(hits[rows, base_slot].mean()), teacher_hits=float(hits.max(1).mean()),
                  headroom_queries=int(gain.sum()), headroom_fraction=float(gain.mean()),
                  changed_teacher_queries=int((t0 != t1).any(1).sum()),
                  graph_ndc={key:float(ndc[rows, slot].mean()) for key,slot in [('baseline',base_slot),('cost',old_slot),('keep',keep_slot)]},
                  new_label_calls=0, teacher_files=[identity(p) for p in sorted(dest.iterdir())])
    dump(dest / 'verification.json', report)
    return report

if __name__ == '__main__':
    freeze(O / 'reviews/protocol_lock.json', [O / 'protocol.md', O / 'scope.md'])
    assert shutil.disk_usage(O).free > 10 * (1 << 30)
    protect()
    result = [teachers(ds) for ds in DS]
    dump(O / 'reviews/teacher_verification.json', dict(status='PASS', datasets=result))
    dump(O / 'state.json', dict(status='PREPARED_OBJECTIVE_TESTS_PENDING', training_runs=0, real_search_calls=0, heldout_access=False))
    print(json.dumps(result), flush=True)
