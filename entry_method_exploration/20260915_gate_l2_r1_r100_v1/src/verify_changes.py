from common import *
from prepare_data import write_vecs
import ast, subprocess, sys

def run(cmd,log,env=None,ok=True):
    with log.open('w') as f:r=subprocess.run(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env=env)
    assert (r.returncode==0)==ok,(cmd,r.returncode,log)

out=RUN/'reviews/synthetic_v1';out.mkdir(parents=True,exist_ok=True)
tree=ast.parse((RUN/'src/train_gate.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='release_samples')
ns={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),'release_samples','exec'),ns)
rows=np.full((5,512),999,dtype='i4');rows[0,:10]=1;rows[1,:]=3;rows[2,:20]=0;rows[2,20:120]=4;rows[4,:100]=2;rows[4,100:400]=6
pos,neg=ns['release_samples'](rows)
assert all(not set(p)&set(n) for p,n in zip(pos,neg))
assert neg[0]==[] and neg[1]==[] and neg[3]==[] and len(neg[2])==100 and len(neg[4])==300
label=dict(status='PASS',minimal_overlap_fixture=True,all_fail_filtered=True,all_ties_filtered=True,ordinary_hard_negatives_retained=True)
dump(out/'labels.json',label)
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
offline=os.environ.copy();offline.update(OMP_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',MKL_NUM_THREADS='16')
checks=[]
for metric in [0,1]:
    folder=out/('ip' if metric==0 else 'l2');folder.mkdir(exist_ok=True)
    rng=np.random.default_rng(97+metric);base=rng.normal(size=(768,32)).astype('f4');q=rng.normal(size=(128,32)).astype('f4')
    # Non-unit vectors ensure accidentally substituting cosine/IP for L2 is detectable.
    base*=rng.uniform(.25,4,size=(768,1)).astype('f4')
    write_vecs(folder/'base.fvecs',base);q.tofile(folder/'cal.f32');q[:48].tofile(folder/'queries.f32')
    manifest=dict(metric_id=metric,paths=dict(base_path=str(folder/'base.fvecs')),identities=dict(base_path=dict(sha256=sha(folder/'base.fvecs'))))
    dump(folder/'manifest.json',manifest)
    if not (folder/'nsg/complete.json').exists():run([RUN/'bin/build_nsg',folder/'manifest.json',folder/'nsg'],folder/'build_nsg.log',offline)
    if not (folder/'hnsw/complete.json').exists():run([RUN/'bin/build_hnsw',folder,folder/'hnsw'],folder/'build_hnsw.log',offline)
    ids=np.arange(512,dtype='i4');ids.tofile(folder/'router.ids.i32');unit(base[ids]).tofile(folder/'W.f32')
    methods=[dict(name=n,ids=str(folder/'router.ids.i32'),W=str(folder/'W.f32')) if n not in ['NSG','HNSW'] else dict(name=n) for n in ['NSG','GT10-hard','GT10-soft-t1','GATE','HNSW']]
    for k in [1,100]:
        c=dict(index=str(folder/'nsg/graph.nsg'),base=str(folder/'base.fvecs'),queries=str(folder/'queries.f32'),hnsw_complete=str(folder/'hnsw/complete.json'),hnsw_topology=str(folder/'hnsw/full.topology.gz'),n=48,K=k,metric_id=metric,threads=1,formal=False,L=[100,768] if k==100 else [32,768],methods=methods)
        cfg=folder/f'k{k}.json';dump(cfg,c);result=folder/f'k{k}'
        run(['taskset','-c','15',RUN/'bin/evaluate',cfg,result],folder/f'k{k}.log',env)
        exact=((q[:48].astype('f8')[:,None,:]-base.astype('f8')[None,:,:])**2).sum(axis=2) if metric==1 else -q[:48].astype('f8')@base.astype('f8').T
        gt=np.argsort(exact,axis=1)[:,:k]
        for name in [m['name'] for m in methods]:
            p=result/(name+'_L768');returned=np.fromfile(p/'ids.i32','i4').reshape(48,k);dist=np.fromfile(p/'distances.f32','f4').reshape(48,k)
            assert np.all(np.sort(returned,axis=1)==np.sort(gt,axis=1)),(metric,k,name,'exact return')
            expected=np.take_along_axis(exact,returned,axis=1)+(1 if metric==0 and name=='HNSW' else 0)
            np.testing.assert_allclose(dist,expected,rtol=3e-5,atol=1e-4)
            assert json.loads((p/'complete.json').read_text())['plain_count_bit_parity']
            checks.append(dict(metric_id=metric,K=k,method=name,exact_recall=1.,plain_count_bit_parity=True))
        if k==100:
            bad=c|dict(L=[99]);dump(folder/'bad.json',bad)
            run(['taskset','-c','15',RUN/'bin/evaluate',folder/'bad.json',folder/'bad'],folder/'bad.log',env,False)
            assert 'L bounds' in (folder/'bad.log').read_text()
dump(RUN/'reviews/changes_verified.json',dict(status='PASS',label=label,native=checks,low_L_rejected=True,code={p.name:sha(p) for p in (RUN/'src').iterdir() if p.suffix in ['.cpp','.hpp','.py']}))
print('CHANGES_VERIFIED',flush=True)
