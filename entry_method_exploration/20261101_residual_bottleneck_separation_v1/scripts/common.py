import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
    os.environ[name] = '1'
import csv, hashlib, json, subprocess, sys, time
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[1]
REPO = R.parents[1]
OLD = R.parent / '20261101_residual_navigation_diagnosis_v1'
DESIGN = R.parent / '20261101_learned_residual_navigation_design_v1'
DS = ['coco', 'flickr30k', 'webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1',
      'deep10m_l2_v1', 'sift10m_bigann_l2_v1', 'gist1m_l2_v1']
SCRATCH = Path('/dev/shm/acsg-e197')
def read(p): return json.loads(Path(p).read_text())
def dump(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''): h.update(b)
    return h.hexdigest()
def csvwrite(p, rows):
    with Path(p).open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
sys.path.insert(0, str(R.parent / '20261028_seven_dataset_scoring_v1/scripts'))
from io_data import view, gt
