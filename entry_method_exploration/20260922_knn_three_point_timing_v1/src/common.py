import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key] = '1'
import json
import hashlib
import time
from pathlib import Path
import numpy as np

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT/'entry_method_exploration/20260922_target_budget_response_v1'
E107 = ROOT/'entry_method_exploration/20260920_until1600_theory_v1/stages/e107_initialization_factorial'
def read(path):
    return json.loads(Path(path).read_text())
def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    tmp.replace(path)
def identity(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):
            h.update(b)
    return dict(path=str(path),bytes=path.stat().st_size,sha256=h.hexdigest())
def preserve_check():
    for item in read(RUN/'reviews/inputs.json')['files']:
        assert identity(item['path']) == item, item['path']
    for item in read(OLD/'seal.json')['files']:
        assert identity(item['path']) == item, item['path']

