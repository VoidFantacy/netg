"""Prepare frozen E226 inputs and execute native stages in sequence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
E183=ROOT.parent/'20261017_gt10_residual_comprehensive_v1'
E222=ROOT.parent/'20261122_joint_residual_tail_v1'
E223=ROOT.parent/'20261122_group_residual_rerank_v1'
E219=ROOT.parent/'20261121_bucket_id_reranking_v1'
DATASETS=('coco','webvid2_5m_light_v1')
N,K,D,DIM=3072,100,512,32
OFF=(176,184,200,224)
LGRID=(176,184,188,192,196,200,208,224,232,236,244)
RAW=('ids.i32','distances.f32','entry_ids.i32','profile_distances.f32')
SHORT=('PCA-B32','TT-B32','PCA-B64','TT-B64')
ARMS=('B32','B64',*SHORT)
ENV=dict(os.environ,**dict.fromkeys(('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
  'BLIS_NUM_THREADS','NUMEXPR_NUM_THREADS'),'1'),OMP_DYNAMIC='FALSE',PYTHONDONTWRITEBYTECODE='1')


def read(file):
    return json.loads(Path(file).read_text())


def write(file,obj):
    with Path(file).open('x') as f:
        json.dump(obj,f,indent=2,ensure_ascii=False,allow_nan=False)
        f.write('\n')


def digest(file):
    h=hashlib.sha256()
    with Path(file).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def identity(path):
    p=Path(path)
    stat=p.stat()
    data=dict(size=stat.st_size,mtime_ns=stat.st_mtime_ns,resolved=str(p.resolve()))
    if stat.st_size<256*1024**2:
        data['sha256']=digest(p)
    return data


def lock(path,items):
    write(path,{str(p):identity(p) for p in sorted(set(items))})


def verify(path):
    for f,ref in read(path).items():
        assert identity(f)==ref,f


def cfg(ds,stage):
    return ROOT/'configs'/f'{ds}.{stage}.json'


def vectors(spec):
    off=int(spec['format']=='fvecs')
    assert spec['format'] in ('fvecs','raw_f32')
    raw=np.memmap(spec['path'],'<f4','r').reshape(-1,spec['d']+off)
    if off:
        assert (raw[:,0].view('<i4')==spec['d']).all()
    start=spec.get('row_start',0)
    result=raw[start:start+spec['n'],off:]
    assert result.shape==(spec['n'],spec['d'])
    return result


def truth(ds,start,n,formal=False):
    spec=read(E219/'gt_eval.json')[ds]
    if formal:
        assert digest(spec['path'])==spec['expected_sha256']
    if spec['format']=='ivecs':
        a=np.memmap(spec['path'],'<i4','r').reshape(-1,K+1)[start:start+n]
        assert (a[:,0]==100).all()
        result=a[:,1:]
    else:
        assert spec['format']=='raw_i64'
        result=np.memmap(spec['path'],'<i8','r').reshape(-1,K)[start:start+n]
    assert result.shape==(n,K)
    return result


def split_roles(ds,c):
    generator=np.random.default_rng(226)
    if ds=='coco':
        path=Path(c['queries']['path']).parent
        src=np.fromfile(path/'source_group_ids.i64','<i8')
        query=src[np.fromfile(path/'test.source_rows.i64','<i8')]
        assert len(set(query.tolist()))==len(query)
        old=[src[np.fromfile(path/f'{role}.source_rows.i64','<i8')] for role in ('profile','qgt','residual')]
        assert not set(query[:N*2]).intersection(*[set(np.concatenate(old))])
        kind='frozen source identities'
    else:
        q=dict(c['queries'],row_start=0,n=N*2)
        vv=vectors(q)
        query=np.array([hashlib.sha256(a.tobytes()).hexdigest() for a in vv])
        declared=read(E183/'configs'/f'{ds}.teacher.json')['queries']
        old=[hashlib.sha256(a.tobytes()).hexdigest() for a in vectors(declared)]
        assert not set(query[:N*2]).intersection(old)
        kind='exact query bytes and distinct official train/test provenance'
    seen=set(query[:N])
    eligible=[]
    dropped=[]
    for i in range(N):
        value=query[N+i]
        if value in seen:
            dropped.append(N+i)
        else:
            seen.add(value)
            eligible.append(i)
    order=generator.permutation(eligible)
    fit,cal=np.sort(order[:2048]),np.sort(order[2048:])
    roles={'fit':(fit+N).tolist(),'cal':(cal+N).tolist(),'holdout':list(range(N))}
    parts=[set(query[v]) for v in roles.values()]
    assert all(a.isdisjoint(b) for i,a in enumerate(parts) for b in parts[i+1:])
    path=ROOT/'models'/ds
    path.mkdir()
    fit.astype('<i4').tofile(path/'fit.i32')
    cal.astype('<i4').tofile(path/'cal.i32')
    write(ROOT/'configs'/f'{ds}.roles.json',{'kind':kind,'rows':roles,'distinct_identity_counts':list(map(len,parts)),
        'dropped_prior_rows':dropped})


def prepare():
    old=read(E222/'seal.json')['files']
    files=[ROOT/'protocol.md',*ROOT.glob('src/*'),Path(__file__).resolve()]
    for ds in DATASETS:
        frozen=E222/'configs'/f'{ds}.formal.json'
        assert digest(frozen)==old[str(frozen.relative_to(E222))]['sha256']
        c=read(frozen)
        for k in ('model_dir','fit_table','bucket_dir','code_dir','bounds','short_model','neighbor','focus','width'):
            c.pop(k,None)
        assert c['queries']['row_start']==N and tuple(c['dense_L'])==LGRID
        family='hard' if ds=='coco' else 'soft'
        compiled=Path(c['table']).parent.parent
        cm=read(compiled/'compile_manifest.json')
        assert cm['name']==family
        teacher=Path(cm['teacher_dir'])
        table_out=ROOT/'models'/ds/'pool'
        split_roles(ds,c)
        write(cfg(ds,'compile64'),{'base_n':c['base']['n'],'table':c['table'],
            'token_source':str(compiled/'source'),'teacher_root':str(teacher),'output_dir':str(table_out),
            'old_covered':cm['models']['JOINT32']['training_integer_coverage']})
        files+=list(compiled.joinpath('source').glob('token_*.i32'))
        files += [compiled/'compile_manifest.json',teacher/'raw/entry_ids.i32',Path(c['table'])]
        oldroot=Path(c['output_dir'])
        for l in OFF:
            for arm in ('GT10','B32'):
                for name in RAW:
                    file=oldroot/f'K100_L{l}'/arm/'raw'/name
                    assert digest(file)==old[str(file.relative_to(E222))]['sha256'],file
                    files.append(file)
        c.update(pool_dir=str(table_out),model_dir=str(ROOT/'models'/ds),offline_L=OFF,K=K,
            teacher_cache=str(oldroot),cal_rows=str(ROOT/'models'/ds/'cal.i32'),output_dir=str(ROOT/'data'/ds/'replay'))
        write(cfg(ds,'replay'),c)
        c.update(output_dir=str(ROOT/'data'/ds/'formal'))
        c['queries']['row_start']=0
        write(cfg(ds,'formal'),c)
        files.extend(Path(c[k]['path']) for k in ('base','queries'))
        files.append(Path(c['index']))
        files.extend(Path(c['router'][k]) for k in ('ids','W','graph'))
    argv=read(E223/'bin/build.json')['argv']
    argv=[w.replace(str(E223),str(ROOT)) if w.startswith(str(E223)) else w for w in argv]
    write(ROOT/'bin/build.json',{'argv':argv})
    with (ROOT/'logs/build.log').open('x') as f:
        subprocess.run(argv,check=True,stdout=f,stderr=subprocess.STDOUT)
    files+=list(ROOT.glob('configs/*'))+list(ROOT.glob('bin/*'))
    files.extend(p for p in ROOT.glob('models/*/*') if p.is_file())
    files.extend(Path(w) for w in argv if w.endswith('.a'))
    lock(ROOT/'input_freeze.json',files)


def launch(ds,stage):
    name=ROOT/'logs'/f'{ds}.{stage}.log'
    with name.open('x') as log:
        subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),stage,str(cfg(ds,stage))],
                       env=ENV,stdout=log,stderr=subprocess.STDOUT,check=True)
    directory=Path(read(cfg(ds,stage))['output_dir'])
    ack=read(directory/'complete.json')
    print(ds,stage,{k:v for k,v in ack.items() if k!='binding'},flush=True)


if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='prepare':
        prepare()
        for ds in DATASETS:
            launch(ds,'compile64')
        verify(ROOT/'input_freeze.json')
        lock(ROOT/'pools_freeze.json',list(ROOT.glob('models/*/pool/*')))
    elif stage in ('replay','formal'):
        for kind in ('input','pools','models'):
            verify(ROOT/f'{kind}_freeze.json')
        for ds in DATASETS:
            launch(ds,stage)
        for kind in ('input','pools','models'):
            verify(ROOT/f'{kind}_freeze.json')
