import os
os.sched_setaffinity(0,{14})
import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    assert json.loads((R/'reviews/run_complete.json').read_text())['status']=='BUILT_PENDING_IDENTITY_AUDIT'
    cfg=json.loads((R/'config.locked.json').read_text());refs=json.loads((R/'reviews/validation_references.json').read_text());env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    dump(R/'reviews/native_audit_frozen.json',{'unix':time.time(),'binary_sha256':hashlib.sha256(Path(cfg['audit_binary']).read_bytes()).hexdigest(),'reused_unchanged_auditor':True})
    for ds,c in cfg['datasets'].items():
        out=Path(c['output']);new={'name':'DefaultDemandQGT','ids':str(out/'ids.i32'),'W':str(out/'W.f32'),'graph':str(out/'router.hnsw')}
        dump(out/'router_audit.config.json',{'old':refs[ds]['model'],'new':new,'queries':c['fit_queries'],'dimension':c['dimension']})
        started=time.perf_counter()
        with (R/'logs'/f'{ds}_router_audit.log').open('x') as log:
            ret=subprocess.run(['taskset','-c','15',cfg['audit_binary'],str(out/'router_audit.config.json'),str(out/'router_audit.json')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60)
        dump(R/'reviews'/f'{ds}_native_audit_job.json',{'exit_code':ret.returncode,'seconds':time.perf_counter()-started});assert ret.returncode==0,ds
    ret=subprocess.run([str(ROOT/'.venv_cpu/bin/python'),str(R/'audit.py')],env=env,timeout=120);assert ret.returncode==0
    print('DEFAULT AUDIT COMPLETE',flush=True)
if __name__=='__main__':main()
