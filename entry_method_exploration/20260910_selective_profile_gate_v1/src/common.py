import hashlib
import json
from pathlib import Path

RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[1]
E24=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
LS=[64,128,256,400,800]
FEATURES=['log1p_query_norm','base_best_cosine','base_gap12','base_gap13',
          'base_mean_log_ess','base_min_log_ess','base_mean_profile_shift',
          'new_minus_base_best_cosine','new_gap12','new_gap13',
          'new_mean_log_ess','new_min_log_ess','entry_overlap_fraction']

def read(path):return json.loads(Path(path).read_text())
def dump(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temp.replace(path)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def identity(path):
    path=Path(path).resolve();s=path.stat()
    return {'path':str(path),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(path)}
def check_lock():
    c=read(RUN/'config.locked.json')
    assert sha(RUN/'protocol.md')==c['protocol_sha256']
    assert sha(RUN/'config.locked.json')==read(RUN/'reviews/protocol_lock.json')['config_sha256']
    return c
def frozen_gate_check():
    record=read(RUN/'models/frozen_before_audit.json')
    for f in record['files']:assert sha(f['path'])==f['sha256'],f['path']
    return record
def update_state(**fields):
    p=RUN/'state.json';s=read(p) if p.exists() else {}
    s.update(fields);dump(p,s)
