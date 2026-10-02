import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

R=Path(__file__).resolve().parent;ROOT=R.parents[3]
C=json.loads((R/'config.locked.json').read_text())
OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
started=time.perf_counter();jobs={}

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')

frozen=json.loads((R/'reviews/prepare_inputs.json').read_text())
for path,value in frozen['files'].items():assert ident(path)==value,path
sources=[R/'protocol.md',R/'config.locked.json']+list(R.glob('*.py'))+[p for p in (R/'src').rglob('*') if p.is_file()]
dump(R/'reviews/run_frozen.json',{'files':{str(p):ident(p) for p in sources},'unix':time.time()})
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_DYNAMIC='FALSE',NUMEXPR_NUM_THREADS='1')

def run(name,argv,cpu_check=False):
    assert time.time()<C['deadline_unix'] and shutil.disk_usage(R).free>=6*2**30
    t0=time.perf_counter();maxthreads=0;maxrss=0;checked=0
    with (R/'logs'/(name+'.log')).open('x') as f:
        proc=subprocess.Popen(argv,env=env,stdout=f,stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                try:
                    status=Path(f'/proc/{proc.pid}/status').read_text()
                    kv={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in status.splitlines() if ':' in s}
                    threads=int(kv['Threads']);maxthreads=max(maxthreads,threads)
                    maxrss=max(maxrss,int(kv.get('VmRSS','0 kB').split()[0])*1024)
                    command=Path(f'/proc/{proc.pid}/cmdline').read_bytes().split(b'\0')[0].decode()
                    if cpu_check and command.startswith(str(R/'bin')):
                        assert threads==1 and kv['Cpus_allowed_list']=='15';checked+=1
                except FileNotFoundError:pass
                assert time.time()<C['deadline_unix'] and time.perf_counter()-started<C['seconds_cap']
                assert shutil.disk_usage(R).free>=6*2**30
                time.sleep(.5)
            code=proc.wait(timeout=10)
        except BaseException:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
            raise
    record={'exit_code':code,'seconds':time.perf_counter()-t0,'max_threads':maxthreads,'maxrss_bytes':maxrss,
            'affinity_thread_samples':checked,'argv':argv}
    jobs[name]=record;dump(R/'reviews'/(name+'.job.json'),record)
    assert code==0,name
    if cpu_check:assert checked>0,name
    print(name,'PASS',round(record['seconds'],3),flush=True)

for name in ['evaluate','build_router']:
    argv=json.loads((OLD/'reviews'/('compile_'+name+'.job.json')).read_text())['argv']
    argv=[x.replace(str(OLD),str(R)) for x in argv]
    run('compile_'+name,argv)
run('profiles',[str(ROOT/'.venv_cpu/bin/python'),str(R/'profiles.py')])
for ds,dc in C['datasets'].items():
    for name in dc['new_methods']:
        run(ds+'_'+name+'_router',['taskset','-c','0-7',str(R/'bin/build_router'),str(R/'inputs'/ds/(name+'.build.json')),str(R/'models'/ds/name/'router_build.json')])
models=[Path(m[k]) for dc in C['datasets'].values() for m in dc['evaluate']['methods'] for k in ['W','graph','ids']]
dump(R/'reviews/models_frozen_before_evaluation.json',{'files':{str(p):ident(p) for p in models},'unix':time.time()})
for ds in C['datasets']:
    (R/'results'/ds).mkdir()
    run(ds+'_evaluate',['taskset','-c','15',str(R/'bin/evaluate'),str(R/'inputs'/ds/'evaluate.json'),str(R/'results'/ds/'evaluation')],True)
totals=[json.loads((R/'results'/ds/'evaluation/complete.json').read_text()) for ds in C['datasets']]
calls=sum(x['search_calls'] for x in totals);ann=sum(x['router_calls'] for x in totals)
assert calls==327936 and ann==327680 and calls<=C['max_NSG'] and ann<=C['max_ANN']
for path,value in frozen['files'].items():assert ident(path)==value,path
for path,value in frozen['large_stat_only'].items():
    st=Path(path).stat();assert st.st_size==value['bytes'] and st.st_mtime_ns==value['mtime_ns'],path
dump(R/'reviews/jobs_complete.json',{'status':'PASS','seconds':time.perf_counter()-started,'jobs':jobs,
    'new_NSG_calls':calls,'new_ANN_calls':ann,'new_profiles':4,'new_graphs':4,'new_GT':0,
    'complete_wall_points':16,'wall_rounds':48,'default_changed':False})
print('COMPLETE',flush=True)
