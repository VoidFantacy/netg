import os,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    assert json.loads((R/'reviews/run_complete.json').read_text())['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    cfg=json.loads((R/'config.locked.json').read_text());env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    start=time.perf_counter()
    for ds,c in cfg['datasets'].items():
        p=Path(c['output'])
        for method in [cfg['primary'],cfg['control']]:
            out=p/method;model={'name':method,'ids':str(p/'ids.i32'),'W':str(out/'W.f32'),'graph':str(out/'router.hnsw')}
            audit={'model':model,'queries':c['fit_queries'],'dimension':c['dimension']};dump(out/'router_audit.config.json',audit)
            with (R/'logs'/f'{ds}_{method}_audit.log').open('x') as log:
                ret=subprocess.run(['taskset','-c','15',cfg['audit_binary'],str(out/'router_audit.config.json'),str(out/'router_audit.json')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
            assert ret.returncode==0,(ds,method)
    ret=subprocess.run([str(ROOT/'.venv_cpu/bin/python'),str(R/'audit.py')],env=env,timeout=180);assert ret.returncode==0
    dump(R/'reviews/audit_outer_cost.json',{'seconds':time.perf_counter()-start,'new_ANN':2048,'new_GT':0,'new_NSG':0,'excluded_from_builder_wall':True})
    print('FULL AUDIT PASS',flush=True)
if __name__=='__main__':main()
