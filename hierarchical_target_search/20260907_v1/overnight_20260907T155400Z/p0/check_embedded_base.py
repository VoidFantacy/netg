#!/usr/bin/env python3
"""P0 fixed-point byte comparison of embedded graph vectors to external base."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from audit_inputs import ROOT, DATASETS, check_deadline, graph_header, sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--seed', type=int, default=2026090711)
    p.add_argument('--random-samples', type=int, default=64)
    a = p.parse_args()
    check_deadline()
    if a.output.exists():
        raise ValueError('Refusing existing output')
    if not 1 <= a.random_samples <= 256:
        raise ValueError('This is a bounded fixed-point audit, max256 random samples')
    audit = json.loads(a.audit.read_text())
    if audit['status'] != 'PASS_INPUT_CONTRACT':
        raise ValueError('Require completed full input audit')
    result = dict(schema_version=1, status='INCOMPLETE', seed=a.seed,
                  requested_random_samples=a.random_samples, datasets=[],
                  audit_path=str(a.audit.resolve()), audit_sha256=sha256(a.audit),
                  script_sha256=sha256(Path(__file__)), heldout_accessed=False,
                  limitation='Fixed-point sample supports graph/base agreement; not a full byte comparison')
    started = time.perf_counter()
    for ds in audit['datasets']:
        check_deadline()
        gh = graph_header(ds['graph']['path'])
        rng = np.random.default_rng(a.seed)
        sampled = rng.choice(gh['n'], size=a.random_samples, replace=False)
        ids = np.unique(np.r_[0, gh['n']-1, gh['n']//2, gh['enterpoint'], sampled]).astype('<i4')
        base = np.memmap(ds['files']['base_path']['path'], mode='r', dtype='<i4', shape=(gh['n'],gh['d']+1))
        embedded = np.memmap(ds['graph']['path'],mode='r',dtype='<i4',offset=gh['vector_offset'],shape=(gh['n'],gh['d']))
        selected = base[ids]
        expected = np.ascontiguousarray(selected[:,1:])
        actual = np.ascontiguousarray(embedded[ids])
        headers_ok = bool(np.all(selected[:,0] == gh['d']))
        matching = np.all(expected == actual,axis=1)
        record = dict(dataset=ds['dataset'],sample_count=len(ids),sample_indices=ids.tolist(),
                      sample_indices_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),
                      headers_valid=headers_ok, byte_equal=bool(matching.all()),
                      differing_ids=ids[~matching].tolist(),
                      external_sample_sha256=hashlib.sha256(expected.tobytes()).hexdigest(),
                      embedded_sample_sha256=hashlib.sha256(actual.tobytes()).hexdigest())
        result['datasets'].append(record)
        if not headers_ok or not matching.all():
            result['status']='FAIL';break
    else:
        result['status']='PASS_FIXED_POINT_BYTE_AGREEMENT'
    result['wall_seconds']=time.perf_counter()-started
    with a.output.open('x') as f:
        json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=result['status'],wall_seconds=result['wall_seconds'],output=str(a.output))))
    if result['status']=='FAIL':
        raise RuntimeError('Graph embedded vectors differ from external base')


if __name__=='__main__':
    main()
