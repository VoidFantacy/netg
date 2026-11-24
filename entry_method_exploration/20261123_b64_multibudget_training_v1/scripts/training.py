"""Build larger WebVid omission event streams for the unchanged B64 compiler."""
from hashlib import sha256
from pathlib import Path
import subprocess

import numpy as np

from drive import E183,E226,ENV,ROOT,config,digest,lock,read,vectors,verify,write

LS=(176,192,200,208)
TRAIN=ROOT/'models/train'


def prepare(c):
    source=Path(c['queries']['path']).parent
    dataset=source/'manifest.json'
    manifest=read(dataset)
    fvecs=source/'query.router_train.seed20260826.fvecs'
    truth=source/'gt.router_train.seed20260826.ip.ivecs'
    validation=source/'query.validation.seed20260826.fvecs'
    for p in (fvecs,truth,validation):
        ref=manifest['files'][p.name]
        assert p.stat().st_size==ref['bytes'] and digest(p)==ref['sha256']
    assert manifest['ground_truth']=={'k':100,'metric':'exact_inner_product','test_source_k':500}
    table=Path(c['table'])
    original=read(table.parent.parent/'compile_manifest.json')['train_gt']
    teacher=E183/'configs'/f'{c["dataset"]}.teacher.json'
    q=read(teacher)['queries']
    oldq=vectors(q)
    oldgt=np.memmap(original['path'],'<i8','r').reshape(original['total_n'],100)[:q['n']]
    assert oldq.shape==(16000,512) and oldgt.shape==(16000,100)
    seen={sha256(x.tobytes()).digest() for x in vectors(dict(q,n=q['total_n']))}
    public=c['queries']
    source_validation=dict(public,path=str(validation))
    for blocked in (vectors(public),vectors(source_validation)):
        seen.update(sha256(x.tobytes()).digest() for x in blocked)
    candidate=vectors(dict(public,path=str(fvecs),n=30000,total_n=30000))
    extra=[]
    for i,row in enumerate(candidate):
        d=sha256(row.tobytes()).digest()
        if d in seen: continue
        seen.add(d); extra.append(i)
        if len(extra)==8192: break
    TRAIN.mkdir()
    rows=TRAIN/'added_source_rows.i32'
    np.asarray(extra,dtype='<i4').tofile(rows)
    write(TRAIN/'roles.json',dict(original=len(oldq),extra=len(extra),n=len(oldq)+len(extra),need=4096,
          identity='exact vector bytes',excluded=['full E183/GT10 fit','public test10K','seed validation10K']))
    assert len(extra)>=4096,'frozen additional sample floor'
    v=np.memmap(truth,'<i4','r').reshape(30000,101)[extra]
    assert (v[:,0]==100).all()
    targets=np.concatenate((oldgt,v[:,1:]),axis=0)
    assert targets.min()>=0 and targets.max()<c['base']['n']
    assert (np.diff(np.sort(targets,axis=1),axis=1)>0).all()
    np.concatenate((oldq,candidate[extra]),axis=0).astype('<f4').tofile(TRAIN/'queries.f32')
    targets.astype('<i4').tofile(TRAIN/'gt.i32')
    return [dataset,fvecs,truth,validation,teacher,Path(q['path']),Path(original['path']),
            table.parent.parent/'compile_manifest.json',rows,TRAIN/'roles.json',TRAIN/'queries.f32',TRAIN/'gt.i32']


def omissions(gt,main):
    offset=np.arange(len(gt),dtype=np.int64)[:,None]*(1<<32)
    found=(np.sort(main,axis=1)+offset).ravel()
    seek=gt+offset
    index=np.minimum(np.searchsorted(found,seek),len(found)-1)
    return found[index]!=seek


def tokens(c,phases):
    n=c['train_n']; native=Path(c['output_dir'])
    gt=np.fromfile(TRAIN/'gt.i32','<i4').reshape(n,100)
    model=c['table']; data=Path(model).read_bytes()
    _,h,width=map(int,np.frombuffer(data,'<u4',count=3,offset=8))
    assert width==32
    labels=np.frombuffer(data,'<i4',count=h,offset=40)
    count=np.frombuffer(data,'u1',count=h,offset=40+4*h)
    ids=np.frombuffer(data,'<i4',count=h*32,offset=40+5*h).reshape(h,32)
    prefix={int(key):set(map(int,row[:m])) for key,row,m in zip(labels,ids,count)}
    q=[]; t=[]; route=[]; base_covered=0
    for i,l in enumerate(phases):
        path=native/f'K100_L{l}'/'raw'
        main=np.fromfile(path/'ids.i32','<i4').reshape(n,100)
        trace=np.fromfile(path/'entry_ids.i32','<i4').reshape(n,3)
        assert main.min()>=0 and main.max()<c['base']['n'] and (np.diff(np.sort(main,axis=1),axis=1)>0).all()
        miss=omissions(gt,main)
        for j in np.linspace(0,n-1,128,dtype=int):
            assert set(map(int,gt[j][miss[j]]))==set(map(int,gt[j]))-set(map(int,main[j]))
        qi,rank=np.nonzero(miss)
        targets=gt[qi,rank]
        candidate_union=[prefix[a]|prefix[b]|prefix[d] for a,b,d in trace]
        base_covered+=sum(int(v) in candidate_union[j] for j,v in zip(qi,targets))
        q.append(qi+i*n); t.append(targets); route.append(trace)
    name='more' if len(phases)==1 else 'mixed'
    folder=ROOT/'models'/f'{name}_tokens'; folder.mkdir()
    (folder/'raw').mkdir()
    np.concatenate(q).astype('<i4').tofile(folder/'token_queries.i32')
    np.concatenate(t).astype('<i4').tofile(folder/'token_targets.i32')
    np.concatenate(route).astype('<i4').tofile(folder/'raw/entry_ids.i32')
    print(name,'events',sum(map(len,q)),'original B32 covered',base_covered,flush=True)
    work=dict(base_n=c['base']['n'],table=model,token_source=str(folder),teacher_root=str(folder),
              old_covered=base_covered,output_dir=str(ROOT/'models'/name))
    return work


def run():
    verify(ROOT/'teacher_inputs.json')
    c=read(config('teacher'))
    with (ROOT/'logs/teacher.log').open('x') as f:
        subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),str(config('teacher'))],
            check=True,stdout=f,stderr=subprocess.STDOUT,env=ENV)
    report=read(ROOT/'data/teacher/complete.json')
    assert report['status']=='PASS_E243_TRAIN_MAIN' and report['points']==len(LS)
    assert report['n']==c['train_n'] and report['threads']==1 and not report['GT_read']
    lock(ROOT/'teacher_outputs.json',sorted(p for p in (ROOT/'data/teacher').rglob('*') if p.is_file()))
    spec=read(E226/'seal.json')['files']
    binary=E226/'bin/benchmark'
    assert digest(binary)==spec[str(binary.relative_to(E226))]['sha256']
    for name,ls in [('more',(200,)),('mixed',(176,192,208))]:
        path=ROOT/'configs'/f'{name}_compiler.json'
        write(path,tokens(c,ls))
        with (ROOT/'logs'/f'{name}_compiler.log').open('x') as f:
            subprocess.run(['taskset','-c','15',str(binary),'compile64',str(path)],check=True,
                           stdout=f,stderr=subprocess.STDOUT,env=ENV)
        stats=read(ROOT/'models'/name/'complete.json')
        assert stats['status']=='PASS_E226_B64' and stats['teacher']==c['train_n']*len(ls)
        print(name,stats,flush=True)
    files=sorted(p for p in (ROOT/'models').rglob('*') if p.is_file())
    lock(ROOT/'trained_banks.json',[*files,binary,ROOT/'teacher_outputs.json',ROOT/'configs/more_compiler.json',
                                  ROOT/'configs/mixed_compiler.json'])


if __name__=='__main__':
    run()
