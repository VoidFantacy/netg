import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key] = '1'
import hashlib
import json
import time
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial'

def read(path):
    return json.loads(Path(path).read_text())

def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(16<<20), b''):
            h.update(block)
    return h.hexdigest()

def identity(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))

def protected_check():
    for item in read(RUN/'reviews/protected_before.json')['files']:
        assert identity(item['path']) == item, item['path']
    for ds, cfg in read(OLD/'config.locked.json')['datasets'].items():
        s = Path(cfg['index']).stat()
        assert s.st_size == cfg['index_stat']['bytes'] and s.st_mtime_ns == cfg['index_stat']['mtime_ns'], ds

def bootstrap(values, reps=5000):
    values = np.asarray(values, 'f8')
    rng = np.random.default_rng(20260922)
    draws = []
    for _ in range(reps//100):
        draws.append(values[rng.integers(len(values), size=(100,len(values)))].mean(1))
    return np.quantile(np.concatenate(draws), [.025,.975], axis=0).tolist()
