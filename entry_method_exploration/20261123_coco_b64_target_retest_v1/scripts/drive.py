"""Freeze the fitted gate and the untouched training-role holdout for online testing."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
X=ROOT.parent
E231=X/'20261123_b64_far_depth_sweep_v1'
E229=X/'20261122_b64_formal_four_dataset_v1'
E245=X/'20261123_coco_b64_multibudget_training_v1'
E248=X/'20261123_coco_b64_teacher_depth_ablation_v1'
E226=X/'20261122_b32_b64_two_tower_v1'
E213=X/'20261121_span4_gt10_b32_nsg_gate_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import E183,ENV,N,RAW,digest,lock,read,vectors,verify,write

DATASET='coco'
WINDOWS=('confirmation',)
GRIDS={w:(192,196,198,200,202,204,208,216) for w in WINDOWS}
ARMS=('B32','B64-old','Single176','Single192','Mixed64')
TARGETS=(96.8,96.9,97,97.1,97.2)
POINTS=sum(len(g)*len(ARMS) for g in GRIDS.values()); BATCHES=2*POINTS
assert POINTS==40


def config(w): return ROOT/'configs'/f'{w}.json'


def sealed(p,scope,archive):
    assert digest(p)==archive[str(p.relative_to(scope))]['sha256'],p
    return p


def prepare():
    reference=read(E248/'seal.json')['files']
    e231=read(E231/'seal.json')['files']
    copied=sealed(E248/'configs/confirmation.json',E248,reference)
    roles=sealed(E248/'configs/roles.json',E248,reference)
    proof=sealed(E248/'analysis/original_training_l200_parity.json',E248,reference)
    (ROOT/'analysis/original_training_l200_parity.json').write_bytes(proof.read_bytes())
    write(ROOT/'configs/roles.json',read(roles))
    c=read(copied)
    banks={tag:Path(c['pools'][tag]) for tag in ARMS[1:]}
    rows=sealed(Path(c['rows']),E229,read(E229/'seal.json')['files'])
    files=[ROOT/'protocol.md',ROOT/'src/benchmark.cpp',Path(__file__).resolve(),E248/'seal.json',
           E231/'seal.json',copied,roles,rows,proof]
    for w in WINDOWS:
        c.update(grid=GRIDS[w],output_dir=str(ROOT/'data'/w),pools={tag:str(p) for tag,p in banks.items()})
        for stale in ('more_pool','mixed_pool','cutoff_model'):
            c.pop(stale,None)
        write(config(w),c)
    files.extend(banks[a]/f for a in ARMS[1:] for f in ('B64.ids.i32','B64.counts.i8','complete.json'))
    write(ROOT/'configs/targets.json',{'K':100,'recall_pct':TARGETS})
    build=sealed(E231/'bin/build.json',E231,e231)
    argv=[a.replace(str(E231),str(ROOT)) if a.startswith(str(E231)) else a for a in read(build)['argv']]
    write(ROOT/'bin/build.json',{'argv':argv})
    with (ROOT/'logs/build.log').open('x') as log:
        subprocess.run(argv,check=True,stdout=log,stderr=subprocess.STDOUT)
    files.extend([Path(c[x]['path']) for x in ('base','queries')]+[Path(c[x]) for x in ('table','index')])
    files.extend([Path(c['router'][x]) for x in ('ids','W','graph')]+[Path(a) for a in argv if a.endswith('.a')])
    files.extend(Path(c['pool_dir'])/f for f in ('B64.ids.i32','B64.counts.i8','complete.json'))
    files.extend([X/'20261120_span4_production_default_v1/source_tested/ACSG/ACSG.cpp', X/'20261120_residual_budget_matched_table_v1/src/common.inc', X/'20261121_neighbor_residual_online_v1/src/residual.hpp'])
    files+=list(ROOT.glob('bin/*'))+list(ROOT.glob('configs/*'))
    lock(ROOT/'inputs.json',files)


def formal():
    verify(ROOT/'inputs.json')
    for w in WINDOWS:
        with (ROOT/'logs'/f'{w}.log').open('x') as log:
            subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),str(config(w))],
                       check=True,stdout=log,stderr=subprocess.STDOUT,env=ENV)
        r=read(ROOT/'data'/w/'complete.json')
        print(w,{k:v for k,v in r.items() if k!='binding'},flush=True)
    verify(ROOT/'inputs.json')
    write(ROOT/'timing_complete.json',{'status':'PASS_E250_TIMING','windows':WINDOWS,'points':POINTS,'batches':BATCHES})


if __name__=='__main__': {'prepare':prepare,'formal':formal}[sys.argv[1]]()
