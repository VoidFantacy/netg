#!/usr/bin/env python3
import time
import numpy as np
from common import DATASETS, OLD, RUN, dump, identity, read, sha

cfg = read(RUN / 'config.locked.json')
assert cfg['protocol_sha256'] == sha(RUN / 'protocol.md')
for di, dataset in enumerate(DATASETS):
    started = time.monotonic()
    old = OLD / 'inputs' / dataset
    meta = read(old / 'runner_config.json')
    seed = read(old / 'seed20260828/config.json')
    d, n, h = meta['dim'], meta['num_queries'], seed['hub_count']
    dest = RUN / 'inputs' / dataset
    assert not dest.exists(); dest.mkdir()
    q = np.memmap(meta['queries_file'], dtype='<f4', mode='r', shape=(n, d))
    gt = np.memmap(meta['gt_file'], dtype='<i8', mode='r', shape=(n, 100))
    rows = np.fromfile(meta['row_ids'], dtype='<i8')
    assert np.array_equal(rows[:20000], np.arange(10000, 30000))
    assert np.array_equal(rows[20000:21024], np.arange(1024))
    assert np.array_equal(rows[21024:], np.arange(1024, 2048))
    p = np.fromfile(seed['prototypes'], dtype='<f4').reshape(h, d)
    hubs = np.fromfile(seed['hub_ids'], dtype='<i4')
    cols = np.fromfile(seed['union_columns'], dtype='<i4')
    single_hits = np.memmap(OLD / 'labels' / dataset / 'L128/hitcount.u8', dtype='u1', mode='r', shape=(n, meta['hub_count']))
    single_ndc = np.memmap(OLD / 'labels' / dataset / 'L128/ndc.u32', dtype='<u4', mode='r', shape=(n, meta['hub_count']))
    p.tofile(dest / 'P0.f32'); hubs.tofile(dest / 'hub_ids.i32')
    assert np.unique(hubs).size == h and np.isfinite(p).all()
    for split, start, stop in [('fit', 0, 20000), ('fit_probe', 0, 1024),
                               ('cal', 20000, 21024), ('audit', 21024, 22048)]:
        part = dest / split; part.mkdir()
        q[start:stop].tofile(part / 'queries.f32'); gt[start:stop].tofile(part / 'gt.i64')
        rows[start:stop].tofile(part / 'row_ids.i64')
        dump(part / 'config.json', {'dataset': dataset, 'split': split, 'dim': d,
             'num_queries': stop-start, 'gt_k': 100, 'index_path': meta['index_path'],
             'queries_file': str(part / 'queries.f32'), 'gt_file': str(part / 'gt.i64'),
             'row_ids': str(part / 'row_ids.i64'), 'hub_ids': str(dest / 'hub_ids.i32'),
             'hub_count': h, 'threads': 1, 'L': 128})
    # Only the fit partition participates in geometric and single-utility proposals.
    scores = np.asarray(q[:20000]) @ p.T
    id_order = np.argsort(hubs, kind='stable')
    geo = id_order[np.argsort(-scores[:, id_order], axis=1, kind='stable')]
    tau = max(float(np.median(scores[np.arange(20000), geo[:, 0]]-
                              scores[np.arange(20000), geo[:, 7]])), 1e-6)
    triples = np.empty((20000, 4, 6, 3), dtype='<i4')
    options = np.empty((20000, 4, 6), dtype='<i4')
    contexts = np.empty((20000, 4, 2), dtype='<i4')
    logical_unique = 0
    for i in range(20000):
        geom = geo[i].tolist(); base = geom[:3]
        hits = np.asarray(single_hits[i, cols], dtype='int16')
        ndc = np.asarray(single_ndc[i, cols], dtype='int64')
        utility = np.lexsort((hubs, -scores[i], ndc, -hits)).tolist()
        outside_geo = next(e for e in geom if e not in base)
        outside_util = next(e for e in utility if e not in base and e != outside_geo)
        ts = [(base[1], base[2]), (base[0], base[2]), (base[0], base[1]), (outside_geo, outside_util)]
        rng = np.random.default_rng(np.random.SeedSequence([cfg['seed'], di, int(rows[i])]))
        for ci, t in enumerate(ts):
            chosen = [next(e for e in base if e not in t)]
            for ordering in [geom, geom, utility, utility]:
                chosen.append(next(e for e in ordering if e not in t and e not in chosen))
            allowed = np.array([e for e in range(h) if e not in t and e not in chosen])
            chosen.append(int(rng.choice(allowed)))
            contexts[i, ci] = t; options[i, ci] = chosen
            for ai, a in enumerate(chosen):
                # Canonical real-ID order makes each set's label independent of proposal position.
                triples[i, ci, ai] = sorted([*t, a], key=lambda e: int(hubs[e]))
        logical_unique += len({tuple(x) for x in triples[i].reshape(-1, 3)})
    assert (np.diff(np.sort(triples, axis=-1), axis=-1) != 0).all()
    triples.tofile(dest / 'fit/triples.i32')
    options.tofile(dest / 'fit/options.i32'); contexts.tofile(dest / 'fit/contexts.i32')
    label_config = read(dest / 'fit/config.json')
    label_config.update({'threads': 16, 'contexts': 4, 'options': 6,
        'triples_file': str(dest / 'fit/triples.i32'), 'logical_call_cap': 480000,
        'protocol_sha256': cfg['protocol_sha256']})
    dump(dest / 'fit/labels_config.json', label_config)
    dump(dest / 'prepared.json', {'status': 'PREPARED', 'dataset': dataset, 'H': h, 'dim': d,
        'tau': tau, 'fit_queries': 20000, 'logical_triples': 480000,
        'unique_ordered_triples': logical_unique, 'seconds': time.monotonic()-started,
        'files': [identity(x) for x in sorted(dest.rglob('*')) if x.is_file()],
        'single_labels_usage': 'fit-only proposal ordering, not joint reward',
        'validation_opened': False, 'heldout_opened': False})
    print(dataset, 'PREPARED', logical_unique, 'physical label calls', flush=True)
