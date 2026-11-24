"""Fit query/candidate encoders on frozen residual labels, with no holdout GT access."""
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from run import DATASETS, D, DIM, K, N, OFF, ROOT, cfg, lock, read, truth, vectors, verify, write

SEED = 226
BATCH = 64
EPOCHS = 6
LR = 0.0004
TEMPERATURE = 0.04
POSITIVE_WEIGHT = 0.55


def read_pools(table, pool):
    raw = Path(table).read_bytes()
    assert raw[:7] == b'M5POST1'
    header = np.frombuffer(raw, '<u4', count=8, offset=8)
    h, width = map(int, header[1:3])
    assert width == 32
    route = np.frombuffer(raw, '<i4', count=h, offset=40)
    original_counts = np.frombuffer(raw, 'u1', count=h, offset=40 + 4*h)
    original = np.frombuffer(raw, '<i4', count=h*32, offset=40 + 5*h).reshape(h, 32)
    wide = np.fromfile(pool/'B64.ids.i32', '<i4').reshape(h, 64)
    counts = np.fromfile(pool/'B64.counts.i8', 'u1')
    assert (counts >= original_counts).all()
    assert (wide[:, :32][np.arange(32) < original_counts[:, None]] ==
            original[np.arange(32) < original_counts[:, None]]).all()
    return dict(zip(map(int, route), range(h))), {32: (original, original_counts), 64: (wide, counts)}


def states(teacher_root, fit, gt, routes, tables, bank_ids):
    queries = np.tile(fit, len(OFF))
    result = {w: (np.full((queries.size, w*3), -1, dtype=np.int32),
                  np.zeros((queries.size, w*3), dtype=bool)) for w in tables}
    for offset, l in enumerate(OFF):
        p = teacher_root/f'K100_L{l}'/'GT10'/'raw'
        entered = np.fromfile(p/'entry_ids.i32', '<i4').reshape(N, 3)
        main = np.fromfile(p/'ids.i32', '<i4').reshape(N, K)
        for j, index in enumerate(fit):
            row = offset*fit.size + j
            wanted = set(map(int, gt[index]))
            slots = [routes[int(i)] for i in entered[index]]
            for w, (ids, counts) in tables.items():
                seen = set(map(int, main[index]))
                candidates = []
                for slot in slots:
                    for item in ids[slot, :counts[slot]]:
                        v = int(item)
                        if v in seen:
                            continue
                        seen.add(v)
                        candidates.append(v)
                codes, positive = result[w]
                if candidates:
                    codes[row, :len(candidates)] = np.searchsorted(bank_ids, candidates)
                    assert (bank_ids[codes[row, :len(candidates)]] == candidates).all()
                    positive[row, :len(candidates)] = [i in wanted for i in candidates]
    return queries, result


def emit(path, query, items, bank):
    path.mkdir()
    np.ascontiguousarray(query, dtype='<f4').tofile(path/'query.f32')
    np.ascontiguousarray(items, dtype='<f4').tofile(path/'candidate_weights.f32')
    np.ascontiguousarray(bank @ items.T, dtype='<f4').tofile(path/'codes.f32')


def learn(q, bank, order, ids, positive, initial):
    start = time.monotonic()
    rng = np.random.default_rng(SEED)
    valid = np.flatnonzero((ids >= 0).any(axis=1))
    qw = torch.nn.Parameter(torch.from_numpy(initial.copy()))
    pw = torch.nn.Parameter(torch.from_numpy(initial.copy()))
    optimiser = torch.optim.AdamW([qw, pw], lr=LR, weight_decay=0.001)
    uniform_pos = []
    for epoch in range(EPOCHS):
        indices = rng.permutation(valid)
        metrics = []
        for i in range(0, len(indices), BATCH):
            ix = indices[i:i+BATCH]
            pool = torch.from_numpy(ids[ix])
            mask = pool >= 0
            target = torch.from_numpy(positive[ix])
            queries = q[order[ix]]
            candidates = bank[pool.clamp_min(0)]
            with torch.no_grad():
                exact = torch.bmm(candidates, queries.unsqueeze(-1)).squeeze(-1)
                teacher = (exact/TEMPERATURE).masked_fill(~mask, -1e4).softmax(dim=1)
            qr = F.linear(queries, qw)
            cr = F.linear(candidates, pw)
            predicted = torch.bmm(cr, qr.unsqueeze(-1)).squeeze(-1)
            log_probs = (predicted/TEMPERATURE).masked_fill(~mask, -1e4).log_softmax(dim=1)
            distilled = -(teacher*log_probs).sum(dim=1)
            pos_count = target.sum(dim=1)
            supervised = -(target*log_probs).sum(dim=1)/pos_count.clamp_min(1)
            weight = POSITIVE_WEIGHT*(pos_count > 0).float()
            loss = ((1-weight)*distilled + weight*supervised).mean()
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()
            metrics.append(float(loss.detach()))
        uniform_pos.append(float(np.mean(metrics)))
        print(f'  epoch {epoch+1} loss {uniform_pos[-1]:.5f}', flush=True)
    return (qw.detach().numpy(), pw.detach().numpy(),
            {'loss': uniform_pos, 'seconds': time.monotonic()-start, 'nonempty_states':len(valid),
             'positive_states':int(positive.any(axis=1).sum()), 'positive_tokens':int(positive.sum()),
             'candidate_tokens':int((ids >= 0).sum())})


def train(ds):
    start = time.monotonic()
    c = read(cfg(ds, 'replay'))
    path = Path(c['model_dir'])
    fit = np.fromfile(path/'fit.i32', '<i4')
    assert fit.size == 2048 and (fit < N).all()
    gt = truth(ds, N, N)
    route, tables = read_pools(c['table'], Path(c['pool_dir']))
    wide = tables[64][0]
    bank_ids = np.unique(wide[wide >= 0]).astype('<i4')
    bank_ids.tofile(path/'ids.i32')
    q = np.array(vectors(c['queries']), dtype='float32', order='C')
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-8)
    base = vectors(c['base'])
    bank = np.ascontiguousarray(base[bank_ids])
    assert q.shape == (N,D) and bank.shape == (bank_ids.size,D)
    fit_query = q[fit]
    _, eigen = np.linalg.eigh(fit_query.T @ fit_query)
    initial = np.ascontiguousarray(eigen[:, -DIM:][:, ::-1].T, dtype=np.float32)
    emit(path/'pca', initial, initial, bank)
    order, training = states(Path(c['teacher_cache']), fit, gt, route, tables, bank_ids)
    receipt = {}
    for width, (ids, pos) in training.items():
        print(ds, 'two towers', width, 'unique coded', bank_ids.size, flush=True)
        qw, cw, result = learn(torch.from_numpy(q), torch.from_numpy(bank), order, ids, pos, initial)
        emit(path/f'twin{width}', qw, cw, bank)
        result.update(query_shift=float(np.linalg.norm(qw-initial)), candidate_shift=float(np.linalg.norm(cw-initial)))
        receipt[str(width)] = result
    write(path/'training.json', {'dataset':ds,'seed':SEED,'batch':BATCH,'epochs':EPOCHS,'lr':LR,
        'optimizer':'AdamW', 'weight_decay':0.001,'temperature':TEMPERATURE,'positive_weight':POSITIVE_WEIGHT,
        'query_unit_norm_in_fit':True,'independent_linear_weights':True,'fit_queries':fit.size,'L':OFF,
        'bank_size':bank_ids.size,'holds_out_first_public_window':True,'training':receipt,
        'offline_wall_seconds':time.monotonic()-start})


if __name__ == '__main__':
    torch.set_num_threads(4)
    torch.set_num_interop_threads(1)
    torch.manual_seed(SEED)
    for kind in ('input','pools'):
        verify(ROOT/f'{kind}_freeze.json')
    for dataset in DATASETS:
        train(dataset)
    lock(ROOT/'models_freeze.json', [Path(__file__).resolve(), *(p for p in ROOT.glob('models/**/*') if p.is_file())])
