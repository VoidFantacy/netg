#!/usr/bin/env python3
"""Full current SHA of all actual suite inputs, once before training/timing."""
import hashlib
import json
from pathlib import Path
import time
ROOT=Path(__file__).resolve().parents[1]


def paths(v):
    if isinstance(v,dict):return set().union(*(paths(x) for x in v.values())) if v else set()
    if isinstance(v,list):return set().union(*(paths(x) for x in v)) if v else set()
    return {v} if isinstance(v,str) and v.startswith('/') and Path(v).is_file() else set()


def main():
    out=ROOT/'reviews/input_freeze.json';assert not out.exists();started=time.monotonic()
    cat=ROOT/'reviews/dataset_catalogue.json';c=json.loads(cat.read_text());ps=paths(c)|{str(cat),str(ROOT/'protocol.md')}
    for p in c['configs']:ps.update(paths(json.loads(Path(p).read_text())))
    expected={}
    for fn in ('l2_assets.json','ip_assets.json'):
        for p,v in json.loads((ROOT/fn).read_text()).get('identities',{}).items():
            if v.get('sha256'):expected[p]=v['sha256']
    for ds in ('coco','flickr30k'):
        old=ROOT.parents[1]/'entry_method_exploration/20261016_m5_multimodal_transfer_v1'
        cfg=json.loads((old/'inputs'/ds/'experiment_config.json').read_text())
        expected.update(cfg['input_sha256'])
        for stage in ('index','profiles','train_gt','eval_gt'):
            receipt=old/'models'/ds/'receipts'/f'{stage}.json'
            if receipt.exists():
                for p,v in json.loads(receipt.read_text()).get('outputs',{}).items():expected[p]=v['sha256']
    result={}
    for p in sorted(ps):
        x=Path(p);s=x.stat();h=hashlib.sha256()
        with x.open('rb') as f:
            for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
        t=x.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns)
        if p in expected:assert h.hexdigest()==expected[p],f'Current source does not match historical SHA: {p}'
        result[p]={'sha256':h.hexdigest(),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,
                   'historical_expected_SHA_checked':p in expected}
        if s.st_size>1024**3:print(json.dumps({'file':p,'bytes':s.st_size,'sha256':h.hexdigest()}),flush=True)
    out.write_text(json.dumps({'status':'FROZEN_FULL_CURRENT_SOURCE_SHA_BEFORE_TRAINING','files':result,
        'elapsed_seconds':time.monotonic()-started,'created_unix':time.time(),
        'scope':'All existing actual configuration inputs and current source manifests. Later generated tables/binaries are bound in per-stage execution locks.'},indent=2)+'\n')
    print(json.dumps({'files':len(result),'elapsed_seconds':time.monotonic()-started}),flush=True)


if __name__=='__main__':main()
