"""Bind tables and run the frozen E229 matrix on CPU 15, one dataset at a time."""
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
X=ROOT.parent
E213=X/'20261121_span4_gt10_b32_nsg_gate_v1'
E226=X/'20261122_b32_b64_two_tower_v1'
E228=X/'20261122_b64_full_confirmation_v1'
sys.path.insert(0,str(E226/'scripts'))
from run import E183,ENV,N,RAW,digest,lock,read,vectors,verify,write

DATASETS=('coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1')
COCO,FLICKR,WEBVID,YANDEX=DATASETS
NAMES=dict(zip(DATASETS,('COCO','Flickr30k','WebVid 2.5M','Yandex first10M')))
CORE1=(64,80,100,128,160,184,200,224,256,320)
CORE100=(100,128,152,168,176,184,192,200,208,216,224,256,320,400)
WEB_LOW=(120,136,140,144,148,156,160,164,172)
GRID={(ds,1): CORE1+((400,480) if ds in (WEBVID,YANDEX) else ()) for ds in DATASETS}
GRID.update({(ds,100):tuple(sorted(CORE100+(WEB_LOW if ds==WEBVID else ()))) for ds in DATASETS})
TARGETS={(COCO,1):(97,98,98.5,99,99.25),(COCO,100):(93,95,96,96.4,97,97.2,98,99),
    (FLICKR,1):(98.5,99,99.25,99.5,99.75),(FLICKR,100):(93,95,96,97,97.5,98,99),
    (WEBVID,1):(73,76,80,83,85,88,90),(WEBVID,100):(68,70,71,72,73,74,74.5,75.5,76,77,78,80,82),
    (YANDEX,1):(85,88,90,92,94,95,96),(YANDEX,100):(82,85,87.5,88,89,90,92,93,94)}
POINTS=2*sum(map(len,GRID.values())); BATCHES=POINTS*2
assert POINTS==218 and BATCHES==436


def config(ds):
    return ROOT/'configs'/f'{ds}.json'


def sealed(path,experiment,entries):
    assert digest(path)==entries[str(path.relative_to(experiment))]['sha256'],path
    return path


def hash_rows(matrix):
    return [sha256(row.tobytes()).digest() for row in matrix]


def prepare_rows(ds,c,archive,gt_spec):
    c['queries'].update(n=gt_spec['n'],row_start=0,total_n=gt_spec['n'])
    if ds in (COCO,WEBVID):
        former=E228/'configs'/f'{ds}.rows.i32'
        rows=np.fromfile(sealed(former,E228,archive),'<i4')
        files=[former,sealed(E228/'configs'/f'{ds}.roles.json',E228,archive)]
        origin='E228'
    else:
        rows=np.arange(N,dtype='<i4'); files=[]; origin='E213'
    assert rows.shape==(N,) and len(np.unique(rows))==N and rows[0]>=0 and rows[-1]<gt_spec['n']
    if ds in (COCO,FLICKR):
        p=Path(c['queries']['path']).parent
        roles=[p/f'{r}.source_rows.i64' for r in ('test','profile','qgt','residual')]
        source=p/'source_group_ids.i64'
        values=np.fromfile(source,'<i8')
        queries=values[np.fromfile(roles[0],'<i8')[rows]]
        fit=set(np.concatenate([values[np.fromfile(f,'<i8')] for f in roles[1:]]))
        files.extend([source,*roles]); kind='prepared source group ids'
    else:
        teacher=E183/'configs'/f'{ds}.teacher.json'
        spec=read(teacher)['queries']; assert 'total_n' in spec
        queries=hash_rows(vectors(c['queries'])[rows])
        fit=set(hash_rows(vectors(dict(spec,n=spec['total_n'],row_start=0))))
        files.extend([teacher,Path(spec['path'])]); kind='exact 512D or 200D vector bytes and official train roles'
    assert not set(queries).intersection(fit)
    row_path=ROOT/'configs'/f'{ds}.rows.i32'
    rows.astype('<i4').tofile(row_path)
    c['rows']=str(row_path)
    write(ROOT/'configs'/f'{ds}.roles.json',{'source':origin,'identity':kind,'count':len(rows),
        'distinct_identities':len(set(queries)),'matching_fit':0,'first':int(rows[0]),'last':int(rows[-1])})
    return files


def prepare():
    e213=read(E213/'seal.json')['experiment_files']
    e226=read(E226/'seal.json')['files']; e228=read(E228/'seal.json')['files']
    official=sealed(E213/'gt_eval.json',E213,e213)
    compiler=sealed(E226/'bin/benchmark',E226,e226)
    build=sealed(E226/'bin/build.json',E226,e226)
    gt=read(official)
    files=[ROOT/'protocol.md',ROOT/'src/benchmark.cpp',Path(__file__).resolve(),official,compiler,build]
    for ds in DATASETS:
        legacy=sealed(E213/'configs'/f'{ds}.json',E213,e213)
        c=read(legacy); c.pop('gate_router',None)
        c['output_dir']=str(ROOT/'data'/ds)
        c['grids']={str(k):GRID[ds,k] for k in (1,100)}
        files.extend(prepare_rows(ds,c,e228,gt[ds]))
        write(ROOT/'configs'/f'{ds}.targets.json',{str(k):TARGETS[ds,k] for k in (1,100)})
        if ds in (COCO,WEBVID):
            pool=Path(read(sealed(E228/'configs'/f'{ds}.json',E228,e228))['pool_dir'])
            files.extend(sealed(pool/n,E226,e226) for n in ('B64.ids.i32','B64.counts.i8','complete.json','growth.json'))
        else:
            pool=ROOT/'pools'/ds
            original=Path(c['table']).parent.parent
            manifest=original/'compile_manifest.json'; m=read(manifest)
            assert m['name']==c['router']['name'] and m['base_n']==c['base']['n']
            assert m['models']['JOINT32']['binary']==c['table']
            tokens=original/'source'; teachers=Path(m['teacher_dir'])
            files.extend([manifest,tokens/'token_queries.i32',tokens/'token_targets.i32',teachers/'raw/entry_ids.i32'])
            compile_config=ROOT/'configs'/f'{ds}.compile64.json'
            write(compile_config,{'base_n':c['base']['n'],'table':c['table'],'token_source':str(tokens),
                'teacher_root':str(teachers),'output_dir':str(pool),
                'old_covered':m['models']['JOINT32']['training_integer_coverage']})
            with (ROOT/'logs'/f'{ds}.compile64.log').open('x') as log:
                subprocess.run(['taskset','-c','15',str(compiler),'compile64',str(compile_config)],
                    stdout=log,stderr=subprocess.STDOUT,env=ENV,check=True)
            files.extend(pool.iterdir())
        certificate=read(pool/'complete.json')
        assert certificate['status']=='PASS_E226_B64' and certificate['appended_IDs']>0
        c['pool_dir']=str(pool)
        files.extend([legacy,Path(c['table']),Path(c['index']),Path(c['base']['path']),Path(c['queries']['path'])])
        files.extend(Path(c['router'][key]) for key in ('ids','W','graph'))
        write(config(ds),c)
        print(ds,certificate['covered_B32'],certificate['covered_B64'],certificate['appended_IDs'],flush=True)
    argv=[x.replace(str(E226),str(ROOT)) if x.startswith(str(E226)) else x for x in read(build)['argv']]
    write(ROOT/'bin/build.json',{'argv':argv})
    with (ROOT/'logs/build.log').open('x') as log:
        subprocess.run(argv,check=True,stderr=subprocess.STDOUT,stdout=log)
    files.extend(Path(x) for x in argv if x.endswith('.a'))
    files.extend([X/'20261120_residual_budget_matched_table_v1/src/common.inc',X/'20261121_neighbor_residual_online_v1/src/residual.hpp'])
    files += list(ROOT.glob('bin/*'))+list(ROOT.glob('configs/*'))
    lock(ROOT/'inputs.json',files)


def formal():
    verify(ROOT/'inputs.json')
    for ds in DATASETS:
        with (ROOT/'logs'/f'{ds}.formal.log').open('x') as f:
            subprocess.run(['taskset','-c','15',str(ROOT/'bin/benchmark'),str(config(ds))],
                stdout=f,stderr=subprocess.STDOUT,check=True,env=ENV)
        r=read(ROOT/'data'/ds/'complete.json')
        print(ds,{k:v for k,v in r.items() if k!='binding'},flush=True)
    verify(ROOT/'inputs.json')
    write(ROOT/'timing_complete.json',{'status':'PASS_E229_TIMING','datasets':DATASETS,'points':POINTS,'batches':BATCHES})


if __name__=='__main__':
    {'prepare':prepare,'formal':formal}[sys.argv[1]]()
