"""Isolated cached diagnostic. Never imports an old experiment runner."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[key] = '8'
import hashlib
import json
import time
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260921_comparison_direction_pilot_v1'

def read(path):
    return json.loads(Path(path).read_text())

def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def identity(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))

def unit(x):
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-30)

def standardize(x, fitting=None):
    fit = x if fitting is None else x[fitting]
    mean = fit.mean(0)
    scale = fit.std(0)
    scale = np.where(scale > 1e-6, scale, 1)
    return ((x - mean) / scale).astype('f4'), mean, scale

def actions(scores, hubs):
    order = np.argsort(hubs, kind='stable')
    best = order[scores[:, order].argmax(axis=1)]
    value = scores[np.arange(len(scores)), best]
    return np.where(value > 0, best + 1, 0).astype('i4')

def selected(values, action):
    return values[np.arange(len(action)), action]

def load_data(ds):
    c = read(OLD / 'config.locked.json')['datasets'][ds]
    p = OLD / 'inputs' / ds / 'fit'
    q = np.fromfile(p / 'queries.f32', '<f4').reshape(4096, c['dimension'])
    rows = np.fromfile(p / 'row_ids.i64', '<i8')
    gt = np.fromfile(p / 'gt.i64', '<i8').reshape(4096, 100)
    hubs = np.fromfile(c['anchor']['ids'], '<i4')
    profiles = np.fromfile(c['anchor']['W'], '<f4').reshape(len(hubs), -1)
    base = np.memmap(c['base'], dtype='<f4', mode='r', shape=(c['base_n'], c['dimension'] + 1))
    assert np.all(base[hubs, 0].view('<i4') == c['dimension'])
    hv = base[hubs, 1:].copy()
    label_dir = OLD / 'results' / ds / 'labels'
    done = read(label_dir / 'complete.json')
    chunks = {k: [] for k in ['recall', 'seconds', 'masks']}
    for block in sorted(done['blocks'], key=lambda b: b['start']):
        b = label_dir / f"block_{block['start']}"
        n, a = block['n'], done['A']
        assert block['full_bit_parity']
        r1 = np.fromfile(b / 'hits1.u8', 'u1').reshape(n, a)
        r100 = np.fromfile(b / 'hits100.u8', 'u1').reshape(n, a)
        masks = np.fromfile(b / 'masks.u64', '<u8').reshape(n, a, 2)
        top1 = np.fromfile(b / 'top1_ids.i32', '<i4').reshape(n, a)
        sl = slice(block['start'], block['start'] + n)
        assert np.array_equal(r1, top1 == gt[sl, :1])
        counts = np.unpackbits(masks.view('u1'), axis=1).reshape(n, a, 128).sum(-1)
        assert np.array_equal(counts, r100)
        sec = np.fromfile(b / 'seconds.f64', '<f8').reshape(n, a, 2, 3)
        assert np.isfinite(sec).all() and (sec > 0).all()
        chunks['recall'].append(np.stack([r1, r100 / 100], -1).astype('f4'))
        chunks['seconds'].append(sec.mean(-1))
        chunks['masks'].append(masks)
    result = {k: np.concatenate(v) for k, v in chunks.items()}
    assert result['recall'].shape == (4096, len(hubs) + 1, 2)
    assert len(np.unique(rows)) == 4096 and np.isfinite(q).all()
    return dict(q=q, rows=rows, gt=gt, hubs=hubs, profiles=profiles, hv=hv, **result)

def targets(data, support):
    dr = data['recall'] - data['recall'][:, :1]
    tref = data['seconds'][support, 0].mean(0)
    dt = (data['seconds'] - data['seconds'][:, :1]) / tref
    utility = (dr - 0.1 * dt).astype('f4')
    return utility, dr, dt, tref
