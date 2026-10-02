from pathlib import Path
import os, sys, json, time, hashlib, shutil, resource
import numpy as np
sys.dont_write_bytecode = True
O = Path(__file__).resolve().parents[1]
C = O.parent
R = Path('/data/netg/ACSG')
D = R / 'entry_method_exploration'
E24 = D / '20260910_gt_topk_profiles_v1'
E37 = D / '20260912_offline_profile_rl_v1'
E46 = D / '20260912_exact_feedback_cache_v1'
E53 = D / '20260912_feedback_step_rl_v1'
E57 = D / '20260912_expanded_final_comparison_v1'
DS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
SEEDS = [20260921, 20260922]
FIELDS = ['ids', 'distances', 'entries', 'route_ndc', 'graph_ndc']
DTYPES = [np.int32, np.float32, np.int32, np.uint32, np.uint32]
QUERY_STOP = 1789264800  # 2026-09-13 10:00 Asia/Shanghai
LATEST_LAUNCH = 1789264200  # 09:50

def read(p): return json.loads(Path(p).read_text())
def dump(p, data):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    tmp.replace(p)
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for a in iter(lambda: f.read(8 << 20), b''): h.update(a)
    return h.hexdigest()
def digest(a): return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def identity(p):
    p = Path(p); s = p.stat()
    return dict(path=str(p), bytes=s.st_size, mtime_ns=s.st_mtime_ns, sha256=sha(p))
def save(p, **arrays):
    p = Path(p); assert not p.exists(), p
    p.parent.mkdir(parents=True, exist_ok=True); np.savez_compressed(p, **arrays)
def raw_digest(out):
    h = hashlib.sha256()
    for k in FIELDS: h.update(k.encode()); h.update(np.ascontiguousarray(out[k]).tobytes())
    return h.hexdigest()
def equal(a, b):
    for k in FIELDS:
        assert a[k].shape == b[k].shape and a[k].dtype == b[k].dtype and a[k].tobytes() == b[k].tobytes(), k
def score(ids, gt): return (ids[..., None] == gt[:, None, :10]).any(-2).sum(-1).astype(np.uint8)
def threads(cpu=15):
    assert os.sched_getaffinity(0) == {cpu}
    for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS']:
        assert os.environ[k] == '1', k
    assert next(int(x.split(':')[1]) for x in Path('/proc/self/status').read_text().splitlines() if x.startswith('Threads:')) == 1
def resources():
    assert shutil.disk_usage('/data').free >= 7 * (1 << 30), 'free <7GiB'
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file()) <= 384 * (1 << 20), 'stage output >384MiB'
def row_profile(p, b, scale, z):
    if not np.any(z): return p.copy()
    y = p.astype(float) + .0625 * scale * (np.tanh(z) @ b.T)
    return (y / np.linalg.norm(y)).astype(np.float32)
def utility(out, base):
    h = out['hits'].astype(float); h0 = base['hits'].astype(float)
    total = out['route_ndc'].astype(float) + out['graph_ndc']; t0 = base['route_ndc'].astype(float) + base['graph_ndc']
    return h-h0-.1*(total/t0-1)-.1*((h==0).astype(float)-(h0==0).astype(float))
def check_freeze():
    for x in read(O/'reviews/prequery_freeze.json')['files']:
        assert sha(x['path']) == x['sha256'], x['path']
