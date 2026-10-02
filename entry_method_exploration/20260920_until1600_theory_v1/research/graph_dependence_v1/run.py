import os,json,time,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
TB=R.parents[1]
ROOT=TB.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ident(p):return dict(path=str(p),sha256=sha(p),bytes=Path(p).stat().st_size)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (R/'lock.json').exists()
cfg=json.loads((TB/'config.locked.json').read_text())
assert time.time()+120<cfg['no_new_search_after_unix']
kernel=TB/'stages/e107_initialization_factorial/src'
before=[ident(p) for p in kernel.rglob('*') if p.is_file() and '__pycache__' not in str(p)]
dump(R/'lock.json',dict(created_unix=time.time(),scope='Four synthetic kernel executions only; no real data search, new labels, training, or graph construction.',source=ident(R/'verify.cpp'),runner=ident(Path(__file__)),dependencies=before,expected_returns=[2,3,3,2],expected_synthetic_calls=4,threads=1,cpu=15,deadline_unix=cfg['no_new_search_after_unix']))
original=json.loads((ROOT/'entry_method_exploration/20260920_gt10_conditional_mechanism_v1/reviews/build.json').read_text())['argv']
argv=[str(R/'verify.cpp') if a.endswith('/src/evaluate.cpp') else str(R/'verify') if a.endswith('/bin/evaluate') else a for a in original]
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
jobs=[]
for kind,command,seconds in [('build',['taskset','-c','15']+argv,100),('synthetic',['taskset','-c','15',str(R/'verify'),str(R/'results.json')],10)]:
  start=time.time();job=dict(kind=kind,argv=command,started_unix=start);jobs.append(job);dump(R/'jobs.json',jobs)
  with (R/(kind+'.log')).open('x') as log:
    p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env);job['pid']=p.pid;dump(R/'jobs.json',jobs)
    try:code=p.wait(timeout=seconds)
    except subprocess.TimeoutExpired:p.kill();p.wait();raise
  job.update(exit_code=code,finished_unix=time.time(),seconds=time.time()-start);dump(R/'jobs.json',jobs);assert code==0
result=json.loads((R/'results.json').read_text());assert result['status']=='PASS' and result['threads']==1 and result['cpu']==15
assert [x['returned'] for x in result['observations']]==[2,3,3,2]
assert all(sha(x['path'])==x['sha256'] for x in before)
dump(R/'complete.json',dict(status='PASS',results=ident(R/'results.json'),source=ident(R/'verify.cpp'),binary=ident(R/'verify'),NSG_calls=0,synthetic_calls=4,seconds=sum(x['seconds'] for x in jobs),frozen_dependencies_unchanged=len(before),scope=result['scope']))
state=json.loads((TB/'state.json').read_text());assert state['synthetic_calls']==2 and state['completed_NSG_calls']==2797056
state['synthetic_calls']=6;state['stage']='Theoretical graph-dependence fixture complete; evidence synthesis';dump(TB/'state.json',state)
print(json.dumps(json.loads((R/'complete.json').read_text()),indent=2))
