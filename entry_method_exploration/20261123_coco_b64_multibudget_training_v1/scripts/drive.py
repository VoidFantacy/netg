"""Freeze the fitted gate and the untouched training-role holdout for online testing."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
X=ROOT.parent
E231=X/'20261123_b64_far_depth_sweep_v1'
E229=X/'20261122_b64_formal_four_dataset_v1'
E226=X/'20261122_b32_b64_two_tower_v1'
E213=X/'20261121_span4_gt10_b32_nsg_gate_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import E183,ENV,N,RAW,digest,lock,read,vectors,verify,write

DATASET='coco'
WINDOWS=('confirmation',)
GRIDS={w:(168,176,184,188,192,196,200,204,208,212,216,220,224,232,244) for w in WINDOWS}
ARMS=('B32','B64-old','Far52','More64','Mixed64','Mixed52')
TARGETS=(96,96.3,96.5,96.7,97,97.2,97.4,97.6,98)
POINTS=sum(len(g)*len(ARMS) for g in GRIDS.values()); BATCHES=2*POINTS
assert POINTS==90


def config(w): return ROOT/'configs'/f'{w}.json'


def sealed(p,scope,archive):
    assert digest(p)==archive[str(p.relative_to(scope))]['sha256'],p
    return p


def prepare_teacher():
    from training import LS,TRAIN,prepare as choose
    e231=read(E231/'seal.json')['files']
    old=sealed(E229/'configs/coco.json',E229,read(E229/'seal.json')['files'])
    c=read(old)
    files=[ROOT/'protocol.md',ROOT/'src/benchmark.cpp',Path(__file__).resolve(),ROOT/'scripts/training.py',
           E231/'seal.json',old,*choose(c)]
    split=read(TRAIN/'roles.json')
    c.update(grid=LS,output_dir=str(ROOT/'data/teacher'),build_teacher=True,
             train_queries=str(TRAIN/'queries.f32'),train_n=split['n'])
    c.pop('grids',None)
    write(config('teacher'),c)
    build=sealed(E231/'bin/build.json',E231,e231)
    argv=[a.replace(str(E231),str(ROOT)) if a.startswith(str(E231)) else a for a in read(build)['argv']]
    write(ROOT/'bin/build.json',{'argv':argv})
    with (ROOT/'logs/build.log').open('x') as log:
        subprocess.run(argv,check=True,stdout=log,stderr=subprocess.STDOUT)
    files.extend([Path(c[x]['path']) for x in ('base','queries')]+[Path(c[x]) for x in ('table','index')])
    files.extend([Path(c['router'][x]) for x in ('ids','W','graph')]+[Path(a) for a in argv if a.endswith('.a')])
    files.extend(Path(c['pool_dir'])/f for f in ('B64.ids.i32','B64.counts.i8','complete.json'))
    files.extend([X/'20261120_span4_production_default_v1/source_tested/ACSG/ACSG.cpp', X/'20261120_residual_budget_matched_table_v1/src/common.inc', X/'20261121_neighbor_residual_online_v1/src/residual.hpp'])
    files+=list(ROOT.glob('bin/*'))+[config('teacher')]
    lock(ROOT/'teacher_inputs.json',files)


def prepare():
    verify(ROOT/'teacher_inputs.json')
    verify(ROOT/'trained_banks.json')
    e229=read(E229/'seal.json')['files']
    files=[ROOT/'teacher_inputs.json',ROOT/'trained_banks.json',ROOT/'bin/benchmark']
    for w in WINDOWS:
        old=sealed(E229/'configs/coco.json',E229,e229)
        c=read(old)
        files.extend([old,sealed(Path(c['rows']),E229,e229)])
        c.update(grid=GRIDS[w],output_dir=str(ROOT/'data'/w),more_pool=str(ROOT/'models/more'),
                 mixed_pool=str(ROOT/'models/mixed'))
        c.pop('grids',None)
        write(config(w),c)
    write(ROOT/'configs/targets.json',{'K':100,'recall_pct':TARGETS})
    lock(ROOT/'inputs.json',files+list(ROOT.glob('configs/*')))


def formal():
    verify(ROOT/'inputs.json')
    for w in WINDOWS:
        with (ROOT/'logs'/f'{w}.log').open('x') as log:
            subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),str(config(w))],
                       check=True,stdout=log,stderr=subprocess.STDOUT,env=ENV)
        r=read(ROOT/'data'/w/'complete.json')
        print(w,{k:v for k,v in r.items() if k!='binding'},flush=True)
    verify(ROOT/'inputs.json')
    write(ROOT/'timing_complete.json',{'status':'PASS_E245_TIMING','windows':WINDOWS,'points':POINTS,'batches':BATCHES})


if __name__=='__main__': {'prepare-teacher':prepare_teacher,'prepare':prepare,'formal':formal}[sys.argv[1]]()
