"""Freeze the E228 retest matrix and execute the two native suites serially."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
E226=ROOT.parent/'20261122_b32_b64_two_tower_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import DATASETS, E183, ENV, K, N, RAW, digest, lock, read, truth, vectors, verify, write

LGRID=tuple(range(168,245,4))
START=6144
TOTAL=10000
HIST=(176,200,244)
TARGETS={DATASETS[0]:(96.2,96.4,96.6,96.8,97.0,97.2,97.4,97.6),
         DATASETS[1]:(72.,73.,74.,75.,75.5,76.,77.,78.)}


def config(ds):
    return ROOT/'configs'/f'{ds}.json'


def sealed(path, root, entries):
    assert digest(path)==entries[str(path.relative_to(root))]['sha256'],path
    return path


def freeze_rows(ds,c):
    if ds=='coco':
        parent=Path(c['queries']['path']).parent
        groups=parent/'source_group_ids.i64'
        sources=[parent/f'{role}.source_rows.i64' for role in ('test','profile','qgt','residual')]
        source_ids=np.fromfile(groups,'<i8')
        public=source_ids[np.fromfile(sources[0],'<i8')]
        official=set(np.concatenate([source_ids[np.fromfile(p,'<i8')] for p in sources[1:]]))
        dependencies=[groups,*sources]
        kind='prepared source group identifiers'
    else:
        old=E183/'configs'/f'{ds}.teacher.json'
        declared=read(old)['queries']
        public=[sha256(q.tobytes()).digest() for q in vectors(c['queries'])]
        official={sha256(q.tobytes()).digest() for q in vectors(declared)}
        dependencies=[old,Path(declared['path'])]
        kind='exact 512D vector bytes and official train/test provenance'
    assert len(public)==TOTAL
    earlier=set(public[:START])
    chosen=[]
    skipped=[]
    used=set()
    for row in range(START,TOTAL):
        ident=public[row]
        if ident in official or ident in earlier or ident in used:
            skipped.append({'row':row,'older_window':ident in earlier,'training':ident in official,'repeat':ident in used})
            continue
        used.add(ident)
        chosen.append(row)
        if len(chosen)==N:
            break
    assert len(chosen)==N and len(used)==N and not (used&earlier or used&official)
    rowfile=ROOT/'configs'/f'{ds}.rows.i32'
    np.asarray(chosen,dtype='<i4').tofile(rowfile)
    write(ROOT/'configs'/f'{ds}.roles.json',{'identity':kind,'n':N,'first':chosen[0],
        'last':chosen[-1],'skipped':skipped,'disjoint_from_first_6144_and_original_train':True})
    c['rows']=str(rowfile)
    return dependencies


def prepare():
    entries=read(E226/'seal.json')['files']
    files=[ROOT/'protocol.md',Path(__file__).resolve(),ROOT/'src/benchmark.cpp',E226/'seal.json']
    paths=sealed(E226/'bin/build.json',E226,entries)
    files.append(paths)
    for ds in DATASETS:
        cp=sealed(E226/'configs'/f'{ds}.formal.json',E226,entries)
        c=read(cp)
        assert c['queries']['row_start']==0 and c['queries']['n']==N and c['queries']['total_n']==TOTAL
        c['historical_queries']=dict(c['queries'],n=256)
        c['queries']['n']=TOTAL
        c['historical_output']=c['output_dir']
        c['output_dir']=str(ROOT/'data'/ds)
        c['dense_L']=LGRID
        c['K']=K
        for key in ('model_dir','offline_L','teacher_cache','cal_rows'):
            c.pop(key,None)
        files.extend(freeze_rows(ds,c))
        for f in ('B64.ids.i32','B64.counts.i8','complete.json'):
            files.append(sealed(Path(c['pool_dir'])/f,E226,entries))
        for l in HIST:
            for arm in ('B32','B64'):
                root=Path(c['historical_output'])/f'K100_L{l}'/arm/'raw'
                files.extend(sealed(root/f,E226,entries) for f in RAW)
        files += [cp,Path(c['table']),Path(c['index']),Path(c['base']['path']),Path(c['queries']['path'])]
        files += [Path(c['router'][name]) for name in ('ids','W','graph')]
        write(config(ds),c)
        print(ds,read(ROOT/'configs'/f'{ds}.roles.json'),flush=True)
    argv=[arg.replace(str(E226),str(ROOT)) if arg.startswith(str(E226)) else arg for arg in read(paths)['argv']]
    write(ROOT/'bin/build.json',{'argv':argv})
    with (ROOT/'logs/build.log').open('x') as log:
        subprocess.run(argv,check=True,stdout=log,stderr=subprocess.STDOUT)
    files += list(ROOT.glob('bin/*'))+list(ROOT.glob('configs/*'))
    files += [Path(arg) for arg in argv if arg.endswith('.a')]
    files += [E226.parent/'20261120_residual_budget_matched_table_v1/src/common.inc',
              E226.parent/'20261121_neighbor_residual_online_v1/src/residual.hpp']
    lock(ROOT/'inputs.json',files)


def run():
    verify(ROOT/'inputs.json')
    for ds in DATASETS:
        with (ROOT/'logs'/f'{ds}.formal.log').open('x') as log:
            subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),str(config(ds))],check=True,
                stdout=log,stderr=subprocess.STDOUT,env=ENV)
        receipt=read(ROOT/'data'/ds/'complete.json')
        print(ds,{k:v for k,v in receipt.items() if k!='binding'},flush=True)
    verify(ROOT/'inputs.json')


if __name__=='__main__':
    {'prepare':prepare,'formal':run}[sys.argv[1]]()
