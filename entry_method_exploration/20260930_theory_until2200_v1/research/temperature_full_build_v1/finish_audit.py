import os,json,hashlib,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=R.parent/'hybrid_temperature_factorial_v1'
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    assert json.loads((R/'reviews/run_complete.json').read_text())['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    cfg=json.loads((R/'config.locked.json').read_text());c=cfg['datasets']['webvid2_5m_light_v1'];p=Path(c['output'])
    argv=json.loads((P/'reviews/compile_evaluate.job.json').read_text())['argv'];argv[argv.index(str(P/'src/evaluate.cpp'))]=str(R/'audit_router.cpp');argv[-1]=str(R/'audit_router')
    dump(R/'reviews/native_audit_frozen.json',{'argv':argv,'source_sha256':hashlib.sha256((R/'audit_router.cpp').read_bytes()).hexdigest(),'unix':time.time()})
    t=time.perf_counter()
    with (R/'logs/audit_compile.log').open('x') as out:ret=subprocess.run(argv,stdout=out,stderr=subprocess.STDOUT,timeout=120)
    dump(R/'reviews/audit_compile.json',{'exit_code':ret.returncode,'seconds':time.perf_counter()-t});assert ret.returncode==0
    methods=[{'name':name,'ids':str(p/'ids.i32'),'W':str(p/name/'W.f32'),'graph':str(p/name/'router.hnsw')} for name in [cfg['primary'],cfg['control']]]
    dump(p/'router_audit.config.json',{'dimension':c['dimension'],'queries':c['fit_queries'],'methods':methods})
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    with (R/'logs/router_audit.log').open('x') as out:ret=subprocess.run(['taskset','-c','15',str(R/'audit_router'),str(p/'router_audit.config.json'),str(p/'router_audit.json')],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=60)
    assert ret.returncode==0
    ret=subprocess.run([str(ROOT/'.venv_cpu/bin/python'),str(R/'audit.py')],env=env,timeout=120);assert ret.returncode==0
    print('ALL AUDIT PASS',flush=True)
if __name__=='__main__':main()
