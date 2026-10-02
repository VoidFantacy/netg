from pathlib import Path
import json, hashlib, shutil, time, os, subprocess

R = Path('/data/netg/ACSG')
O = R / 'entry_method_exploration/20260911_teacher_objective_alignment_v1'
E28 = R / 'entry_method_exploration/20260911_gt10_shared_transform_v1'
E24 = R / 'entry_method_exploration/20260910_gt_topk_profiles_v1'
E23 = R / 'entry_method_exploration/20260910_three_entry_rank_v1'
DS = ['webvid2_5m_light_v1', 'yandex_t2i_official10M_ip_v1']
CELLS = ['cost_ce', 'keep_ce', 'cost_margin', 'keep_margin']
NORMAL_CAP = 2085120
HARD_CAP = 2095120

def dump(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + '\n')

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()

def identity(path):
    path = Path(path)
    s = path.stat()
    return dict(path=str(path), bytes=s.st_size, mtime_ns=s.st_mtime_ns, sha256=sha(path))

def freeze(path, files):
    assert not Path(path).exists(), path
    dump(path, dict(timestamp=time.time(), files=[identity(p) for p in files], heldout_access=False))

def check_freeze(path):
    for item in read(path)['files']:
        assert identity(item['path']) == item, item['path']

def policy(ds, name, w=None):
    p = read(E24 / 'inputs' / ds / 'prepared.json')
    ids = str(E24 / 'inputs' / ds / 'hub_ids.i32')
    return dict(name=name, family='profile', model_name=name,
                W=str(w or E24 / 'models' / ds / name / 'W.f32'), mapping=ids,
                tie_ids=ids, hub_count=p['H'], dim=p['dim'], k=3,
                seed=20260828, hnsw_seed=20260828, slot_labels=False,
                canonical_entry_order=True)
