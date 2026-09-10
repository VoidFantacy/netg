import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OLD = ROOT / 'entry_method_exploration/20260909_ab_experiment_v1'
DATASETS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
LS = [64, 128, 256, 400, 800]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + '\n')


def identity(path):
    path = Path(path)
    return {'path': str(path), 'bytes': path.stat().st_size,
            'mtime_ns': path.stat().st_mtime_ns, 'sha256': sha(path)}
