import hashlib
import json
from pathlib import Path

RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[1]
E24=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'
E25=ROOT/'entry_method_exploration/20260910_selective_profile_gate_v1'
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
LS=[64,128,256,400,800]
ALPHAS=[.25,.50,.75]
NAMES=['alpha025','alpha050','alpha075']

def read(path):return json.loads(Path(path).read_text())
def dump(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_name(p.name+'.tmp');temp.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(p)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()
def identity(path):
    p=Path(path).resolve();s=p.stat();return {'path':str(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':sha(p)}
def check_lock():
    c=read(RUN/'config.locked.json')
    assert c['protocol_sha256']==sha(RUN/'protocol.md')
    assert read(RUN/'reviews/protocol_lock.json')['config_sha256']==sha(RUN/'config.locked.json')
    return c
def frozen_check(which):
    record=read(RUN/'models'/f'frozen_before_{which}.json')
    for item in record['files']:assert sha(item['path'])==item['sha256'],item['path']
    return record
def update_state(**fields):
    p=RUN/'state.json';s=read(p) if p.exists() else {};s.update(fields);dump(p,s)
