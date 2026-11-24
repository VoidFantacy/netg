"""Compile same-data single-depth controls using stored native states."""
from pathlib import Path
import subprocess

import numpy as np

from drive import E226,E245,ENV,ROOT,digest,lock,read,sealed,write

DEPTHS=(176,192,208)


def prepare():
    source=read(E245/'seal.json')['files']
    train=sealed(E245/'configs/teacher.json',E245,source)
    c=read(train)
    n=c['train_n']
    base=Path(c['table'])
    raw=base.read_bytes()
    _,h,width=map(int,np.frombuffer(raw,'<u4',count=3,offset=8))
    assert width==32
    labels=np.frombuffer(raw,'<i4',count=h,offset=40)
    counts=np.frombuffer(raw,'u1',count=h,offset=40+4*h)
    ids=np.frombuffer(raw,'<i4',count=h*32,offset=40+5*h).reshape(h,32)
    rows={int(key):set(map(int,v[:m])) for key,v,m in zip(labels,ids,counts)}
    labels_path=sealed(E245/'models/train/gt.i32',E245,source)
    gt=np.fromfile(labels_path,'<i4').reshape(n,100)
    offset=np.arange(n,dtype=np.int64)[:,None]*(1<<32)
    probe=gt+offset
    compiler=sealed(E226/'bin/benchmark',E226,read(E226/'seal.json')['files'])
    files=[Path(__file__).resolve(),train,base,labels_path,compiler]
    base_manifest=base.parent.parent/'compile_manifest.json'
    old=read(base_manifest)
    old_n=old['residual_n']
    replay={}
    for name in ('ids.i32','distances.f32','entry_ids.i32','profile_distances.f32'):
        historical=Path(old['teacher_dir'])/'raw'/name
        reproduced=sealed(E245/'data/teacher/K100_L200/raw'/name,E245,source)
        before=np.fromfile(historical,'<u4').reshape(old_n,-1)
        now=np.fromfile(reproduced,'<u4').reshape(n,before.shape[1])[:old_n]
        difference=int(np.count_nonzero(np.any(before!=now,axis=1)))
        replay[name]=dict(identical_queries=old_n-difference,different_queries=difference)
        files.extend((historical,reproduced))
    recovery=ROOT/'analysis/original_training_l200_parity.json'
    write(recovery,dict(old_queries=old_n,fields=replay))
    files.extend((base_manifest,recovery))
    for l in DEPTHS:
        parent=E245/'data/teacher'/f'K100_L{l}'/'raw'
        main_path=sealed(parent/'ids.i32',E245,source)
        route_path=sealed(parent/'entry_ids.i32',E245,source)
        main=np.fromfile(main_path,'<i4').reshape(n,100)
        routes=np.fromfile(route_path,'<i4').reshape(n,3)
        keys=(np.sort(main,axis=1)+offset).ravel()
        at=np.minimum(np.searchsorted(keys,probe),len(keys)-1)
        missed=keys[at]!=probe
        for row in np.linspace(0,n-1,128,dtype=int):
            assert set(map(int,gt[row][missed[row]]))==set(map(int,gt[row]))-set(map(int,main[row]))
        qi,rank=np.nonzero(missed)
        val=gt[qi,rank]
        union=[rows[a]|rows[b]|rows[d] for a,b,d in routes]
        covered=sum(int(v) in union[q] for q,v in zip(qi,val))
        out=ROOT/'models'/f'tokens_{l}'
        (out/'raw').mkdir(parents=True)
        qi.astype('<i4').tofile(out/'token_queries.i32')
        val.astype('<i4').tofile(out/'token_targets.i32')
        routes.tofile(out/'raw/entry_ids.i32')
        cp=ROOT/'configs'/f'l{l}.json'
        target=ROOT/'models'/f'bank_{l}'
        write(cp,dict(base_n=c['base']['n'],table=str(base),token_source=str(out),teacher_root=str(out),
                      old_covered=covered,output_dir=str(target)))
        with (ROOT/'logs'/f'compile_l{l}.log').open('x') as log:
            subprocess.run(['taskset','-c','15',str(compiler),'compile64',str(cp)],env=ENV,
                           check=True,stdout=log,stderr=subprocess.STDOUT)
        stats=read(target/'complete.json')
        assert stats['status']=='PASS_E226_B64' and stats['teacher']==n and stats['tokens']==len(val)
        print(l,stats,flush=True)
        files.extend((cp,main_path,route_path))
    files.extend(p for p in (ROOT/'models').rglob('*') if p.is_file())
    lock(ROOT/'compiled.json',files)


if __name__=='__main__':
    prepare()
