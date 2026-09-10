import hashlib
import json
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
E23 = ROOT / 'entry_method_exploration/20260910_three_entry_rank_v1'
E22 = ROOT / 'entry_method_exploration/20260909_ab_experiment_v1'
DATASETS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
LS = [64, 128, 256, 400, 800]


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def identity(path):
    path = Path(path).resolve()
    st = path.stat()
    return {'path': str(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns, 'sha256': sha(path)}


def check_lock():
    cfg = read(RUN / 'config.locked.json')
    assert cfg['protocol_sha256'] == sha(RUN / 'protocol.md')
    assert read(RUN / 'reviews/protocol_lock.json')['config_sha256'] == sha(RUN / 'config.locked.json')
    return cfg
