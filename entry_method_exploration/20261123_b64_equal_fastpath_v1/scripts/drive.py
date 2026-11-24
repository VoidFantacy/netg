"""Freeze the fitted gate and the untouched training-role holdout for online testing."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
X=ROOT.parent
E231=X/'20261123_b64_far_depth_sweep_v1'
E226=X/'20261122_b32_b64_two_tower_v1'
E213=X/'20261121_span4_gt10_b32_nsg_gate_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import E183,ENV,N,RAW,digest,lock,read,vectors,verify,write

DATASET='webvid2_5m_light_v1'
WINDOWS=('validation',)
GRIDS={w:(156,168,176,184,188,192,196,200,204,208,216,224,232,244,288,368) for w in WINDOWS}
ARMS=('B32','B64-old','Visited64','Budget40','VisitedBudget40','Mixed64','VisitedMixed64')
TARGETS=(72,74,74.5,75,75.5,76,76.5,77,78,80,82,84)
POINTS=sum(len(g)*len(ARMS) for g in GRIDS.values()); BATCHES=2*POINTS
assert POINTS==112


def config(w): return ROOT/'configs'/f'{w}.json'


def sealed(p,scope,archive):
    assert digest(p)==archive[str(p.relative_to(scope))]['sha256'],p
    return p


def prepare():
    e231=read(E231/'seal.json')['files']
    ranks=X/'20261123_b64_rank_budget_v1'
    trained=X/'20261123_b64_multibudget_training_v1'
    first=X/'20261123_b64_external_validation_v1'
    trained_manifest=read(trained/'seal.json')['files']
    score=sealed(ranks/'models/policies.json',ranks,read(ranks/'seal.json')['files'])
    mixed=trained/'models/mixed'
    banks=[sealed(mixed/f,trained,trained_manifest) for f in ('B64.ids.i32','B64.counts.i8','complete.json')]
    extra_train=sealed(trained/'models/train/queries.f32',trained,trained_manifest)
    taken=sealed(first/'configs/validation.rows.i32',first,read(first/'seal.json')['files'])
    old=sealed(E231/'configs/confirmation.json',E231,e231)
    c=read(old)
    public=c['queries']
    folder=Path(public['path']).parent
    catalogue=folder/'manifest.json'
    meta=read(catalogue)
    verify_q=folder/'query.validation.seed20260826.fvecs'
    verify_gt=folder/'gt.validation.seed20260826.ip.ivecs'
    for p in (verify_q,verify_gt):
        assert digest(p)==meta['files'][p.name]['sha256'] and p.stat().st_size==meta['files'][p.name]['bytes']
    assert meta['ground_truth']['metric']=='exact_inner_product' and meta['ground_truth']['k']==100
    val=dict(public,path=str(verify_q),n=10000,total_n=10000)
    teach=E183/'configs'/f'{DATASET}.teacher.json'
    train=read(teach)['queries']
    blocked={sha256(q.tobytes()).digest() for q in vectors(dict(train,n=train['total_n'],row_start=0))}
    blocked.update(sha256(q.tobytes()).digest() for q in vectors(public))
    blocked.update(sha256(q.tobytes()).digest() for q in np.memmap(extra_train,'<f4','r').reshape(-1,public['d']))
    validation=vectors(val)
    blocked.update(sha256(validation[i].tobytes()).digest() for i in np.fromfile(taken,'<i4'))
    rows=[]; excluded=0
    for i in range(4096,len(validation)):
        q=validation[i]
        key=sha256(q.tobytes()).digest()
        if key in blocked:
            excluded+=1
            continue
        blocked.add(key); rows.append(i)
        if len(rows)==N: break
    assert len(rows)==N
    selection=ROOT/'configs/validation.rows.i32'
    np.asarray(rows,'<i4').tofile(selection)
    write(ROOT/'configs/roles.json',dict(query=str(verify_q),gt=str(verify_gt),gt_sha256=digest(verify_gt),
          n=N,physical_span=[rows[0],rows[-1]],excluded=excluded,identity='exact vector bytes',
          disjoint_roles=['E183 complete profile fit','E243 full train','WebVid public 10K','E237 validation window','validation duplicates']))
    files=[ROOT/'protocol.md',ROOT/'src/benchmark.cpp',Path(__file__).resolve(),E231/'seal.json',old,
           catalogue,teach,Path(train['path']),Path(public['path']),verify_q,score,*banks,extra_train,taken]
    for w in WINDOWS:
        c.update(grid=GRIDS[w],rows=str(selection),queries=val,output_dir=str(ROOT/'data'/w),
                 model=str(score),mixed_pool=str(mixed))
        c.pop('archive_main',None)
        write(config(w),c)
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
    write(ROOT/'timing_complete.json',{'status':'PASS_E244_TIMING','windows':WINDOWS,'points':POINTS,'batches':BATCHES})


if __name__=='__main__': {'prepare':prepare,'formal':formal}[sys.argv[1]]()
