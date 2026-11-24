"""Freeze the fitted gate and the untouched training-role holdout for online testing."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
X=ROOT.parent
E231=X/'20261123_b64_far_depth_sweep_v1'
E226=X/'20261122_b32_b64_two_tower_v1'
E213=X/'20261121_span4_gt10_b32_nsg_gate_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import ENV,N,RAW,digest,lock,read,verify,write

DATASET='webvid2_5m_light_v1'
WINDOWS=('confirmation',)
GRIDS={w:(96,112,128,144,156,168,176,184,192,200,208,216,224,232,244,256,288) for w in WINDOWS}
ARMS=('B32','B64-old','More64','Mixed64','B56-equal')
TARGETS=(78,79,80,81,82,83,84,85,86,87)
POINTS=sum(len(g)*len(ARMS) for g in GRIDS.values()); BATCHES=2*POINTS
assert POINTS==85


def config(w): return ROOT/'configs'/f'{w}.json'


def sealed(p,scope,archive):
    assert digest(p)==archive[str(p.relative_to(scope))]['sha256'],p
    return p


def prepare():
    e231=read(E231/'seal.json')['files']
    train=ROOT.parent/'20261123_b64_multibudget_training_v1'
    archived=read(train/'seal.json')['files']
    more=train/'models/more'; mixed=train/'models/mixed'
    banks=[sealed(d/f,train,archived) for d in (more,mixed)
           for f in ('B64.ids.i32','B64.counts.i8','complete.json')]
    files=[ROOT/'protocol.md',ROOT/'src/benchmark.cpp',Path(__file__).resolve(),E231/'seal.json',
           train/'seal.json',*banks]
    for w in WINDOWS:
        saved=sealed(E231/'configs'/f'{w}.json',E231,e231)
        c=read(saved); files.extend([saved,sealed(Path(c['rows']),E231,e231)])
        c.update(grid=GRIDS[w],output_dir=str(ROOT/'data'/w),more_pool=str(more),mixed_pool=str(mixed)); c.pop('archive_main',None)
        write(config(w),c)
    write(ROOT/'configs/targets.json',{'K':1,'recall_pct':TARGETS})
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
    write(ROOT/'timing_complete.json',{'status':'PASS_E246_TIMING','windows':WINDOWS,'points':POINTS,'batches':BATCHES})


if __name__=='__main__': {'prepare':prepare,'formal':formal}[sys.argv[1]]()
