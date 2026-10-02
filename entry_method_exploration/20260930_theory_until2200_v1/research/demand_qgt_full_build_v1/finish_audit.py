import os,json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=R.parent/'hybrid_temperature_factorial_v1'
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    assert json.loads((R/'reviews/run_complete.json').read_text())['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    cfg=json.loads((R/'config.locked.json').read_text());refs=json.loads((R/'reviews/validation_references.json').read_text())
    a=json.loads((P/'reviews/compile_evaluate.job.json').read_text())['argv'];a[a.index(str(P/'src/evaluate.cpp'))]=str(R/'audit_router.cpp');a[-1]=str(R/'audit_router')
    dump(R/'reviews/native_audit_frozen.json',{'argv':a,'source_sha256':hashlib.sha256((R/'audit_router.cpp').read_bytes()).hexdigest(),'unix':time.time()})
    t=time.perf_counter()
    with (R/'logs/audit_compile.log').open('x') as out:result=subprocess.run(a,stdout=out,stderr=subprocess.STDOUT,timeout=120)
    dump(R/'reviews/audit_compile.json',{'exit_code':result.returncode,'seconds':time.perf_counter()-t});assert result.returncode==0
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    for ds,c in cfg['datasets'].items():
        p=Path(c['output']);new={'name':'FrozenHybrid','ids':str(p/'ids.i32'),'W':str(p/'W.f32'),'graph':str(p/'router.hnsw')}
        audit={'old':refs[ds]['model'],'new':new,'queries':c['fit_queries'],'dimension':c['dimension']}
        dump(p/'router_audit.config.json',audit)
        with (R/'logs'/f'{ds}_router_audit.log').open('x') as out:ret=subprocess.run(['taskset','-c','15',str(R/'audit_router'),str(p/'router_audit.config.json'),str(p/'router_audit.json')],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=60)
        assert ret.returncode==0,ds
    ret=subprocess.run([str(ROOT/'.venv_cpu/bin/python'),str(R/'audit.py')],env=env,timeout=120)
    assert ret.returncode==0;print('ALL AUDIT PASS',flush=True)
if __name__=='__main__':main()
