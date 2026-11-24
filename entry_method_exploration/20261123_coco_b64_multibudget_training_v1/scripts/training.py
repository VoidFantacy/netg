"""Build larger WebVid omission event streams for the unchanged B64 compiler."""
from hashlib import sha256
from pathlib import Path
import subprocess

import numpy as np

from drive import E183,E226,E213,E229,ENV,ROOT,config,digest,lock,read,vectors,verify,write

LS=(176,192,200,208)
TRAIN=ROOT/'models/train'


def prepare(c):
    public=c['queries']
    source=Path(public['path']).parent
    roles=[source/f'{r}.source_rows.i64' for r in ('test','profile','qgt','residual')]
    groups_path=source/'source_group_ids.i64'
    groups=np.fromfile(groups_path,'<i8')
    public_group=groups[np.fromfile(roles[0],'<i8')]
    fitting={int(v) for path in roles[1:] for v in groups[np.fromfile(path,'<i8')]}
    confirmation=Path(c['rows'])
    assert digest(confirmation)==read(E229/'seal.json')['files'][str(confirmation.relative_to(E229))]['sha256']
    test=np.fromfile(confirmation,'<i4')
    confirmed=set(map(int,public_group[test]))
    assert len(confirmed)==len(test)==3072 and not (confirmed&fitting)
    test_queries=vectors(public)
    blocked=confirmed|fitting
    train_roles=[source/f'{r}.f32' for r in ('profile','qgt','residual')]
    seen={sha256(test_queries[i].tobytes()).digest() for i in test}
    for path in train_roles:
        seen.update(sha256(q.tobytes()).digest() for q in np.memmap(path,'<f4','r').reshape(-1,public['d']))
    selected=[]
    for i in range(6144):
        group=int(public_group[i])
        query=sha256(test_queries[i].tobytes()).digest()
        if group in blocked or query in seen: continue
        blocked.add(group);seen.add(query);selected.append(i)
        if len(selected)==4096: break
    table=Path(c['table'])
    compiler=table.parent.parent/'compile_manifest.json'
    original=read(compiler)['train_gt']
    teacher=E183/'configs'/f'{c["dataset"]}.teacher.json'
    spec=read(teacher)['queries']
    oldq=vectors(spec)
    oldgt=np.memmap(original['path'],'<i8','r').reshape(original['n'],100)
    assert oldq.shape==(16000,512) and oldgt.shape==(16000,100)
    info=read(E213/'gt_eval.json')['coco']
    truth=Path(info['path'])
    assert digest(truth)==info['expected_sha256'] and info['format']=='raw_i64'
    gt=np.memmap(truth,'<i8','r').reshape(info['n'],100)[selected]
    TRAIN.mkdir()
    rows=TRAIN/'added_source_rows.i32'
    np.asarray(selected,dtype='<i4').tofile(rows)
    write(TRAIN/'roles.json',dict(original=len(oldq),extra=len(selected),n=len(oldq)+len(selected),need=3072,
          identity='source group and exact query bytes',excluded=['profile','qgt','residual','E229 confirmation']))
    assert len(selected)>=3072,'frozen additional sample floor'
    out=np.concatenate((oldgt,gt))
    assert out.min()>=0 and out.max()<c['base']['n']
    assert (np.diff(np.sort(out,axis=1),axis=1)>0).all()
    np.concatenate((oldq,test_queries[selected])).astype('<f4').tofile(TRAIN/'queries.f32')
    out.astype('<i4').tofile(TRAIN/'gt.i32')
    return [*roles,*train_roles,groups_path,confirmation,truth,teacher,Path(original['path']),
            compiler,rows,TRAIN/'roles.json',TRAIN/'queries.f32',TRAIN/'gt.i32']


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
    assert report['status']=='PASS_E245_TRAIN_MAIN' and report['points']==len(LS)
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
