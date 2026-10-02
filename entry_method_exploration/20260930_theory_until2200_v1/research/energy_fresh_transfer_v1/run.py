import os
os.sched_setaffinity(0,{14})
import hashlib,json,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
    sources=[R/'protocol.md',R/'config.locked.json',R/'compile.json',*R.glob('*.py'),*R.glob('src/**/*.cpp'),*R.glob('src/**/*.hpp')]
    models=json.loads((R/'reviews/models_before_source.json').read_text())
    for path,v in models['files'].items():assert ident(path)==v
    frozen={str(p):ident(p) for p in sources};dump(R/'reviews/frozen_before_source.json',{'unix':time.time(),'files':frozen})
    started=time.perf_counter();jobs={};env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'}
    def check():assert time.time()<C['deadline_unix'] and time.perf_counter()-started<C['seconds_cap'] and shutil.disk_usage(R).free>=C['min_free_bytes']
    def run(name,argv,performance=False):
        check();t=time.perf_counter();before=resource.getrusage(resource.RUSAGE_CHILDREN);samples=0;maxrss=0;maxthreads=0;affinity=set()
        with (R/'logs'/f'{name}.log').open('x') as log:
            p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
            (R/'reviews/active_process.json').write_text(json.dumps({'pid':p.pid,'name':name,'argv':argv,'unix':time.time()})+'\n')
            try:
                while p.poll() is None:
                    check()
                    try:
                        status=dict(s.split(':',1) for s in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in s)
                        threads=int(status['Threads']);maxthreads=max(maxthreads,threads);maxrss=max(maxrss,int(status.get('VmRSS','0 kB').split()[0])*1024);affinity.add(status['Cpus_allowed_list'].strip())
                        if performance and Path(f'/proc/{p.pid}/cmdline').read_bytes().startswith(str(R/'bin/evaluate').encode()):
                            assert threads==1 and status['Cpus_allowed_list'].strip()=='15';samples+=1
                    except FileNotFoundError:pass
                    time.sleep(.2)
                code=p.wait(timeout=5)
            except BaseException:
                if p.poll() is None:p.terminate();p.wait(timeout=10)
                raise
        after=resource.getrusage(resource.RUSAGE_CHILDREN);rec={'exit_code':code,'seconds':time.perf_counter()-t,'argv':argv,'maxrss_bytes':maxrss,
            'max_threads':maxthreads,'affinity_samples':sorted(affinity),'single_thread_samples':samples,
            'user_cpu_seconds':after.ru_utime-before.ru_utime,'system_cpu_seconds':after.ru_stime-before.ru_stime}
        jobs[name]=rec;dump(R/'reviews'/f'{name}.job.json',rec);assert code==0,name
        if performance:assert samples>0
        print(name,'PASS',rec['seconds'],flush=True)
    status='FAILED'
    try:
        run('compile',['taskset','-c','0-7',*json.loads((R/'compile.json').read_text())])
        dump(R/'reviews/binary_before_source.json',{'binary':ident(R/'bin/evaluate'),'unix':time.time()})
        run('prepare_inputs',['taskset','-c','14',str(ROOT/'.venv_cpu/bin/python'),str(R/'prepare_inputs.py')])
        run('exact_gt',['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/'exact_gt.py')])
        assert json.loads((R/'reviews/gt_complete.json').read_text())['status']=='PASS'
        for case,c in C['cases'].items():run(case,['taskset','-c','15',str(R/'bin/evaluate'),str(R/'inputs'/f'{case}.evaluate.json'),str(R/'results'/case)],True)
        total=sum(json.loads((R/'results'/case/'complete.json').read_text())['search_calls'] for case in C['cases'])
        assert total==C['expected_NSG'] and total<=C['max_NSG'];status='COMPUTED_PENDING_INDEPENDENT_AUDIT'
    finally:
        (R/'reviews/active_process.json').write_text(json.dumps({'pid':None,'status':status,'unix':time.time()})+'\n')
        dump(R/'reviews/run_complete.json',{'status':status,'seconds':time.perf_counter()-started,'jobs':jobs,'default_changed':False})
    for path,v in frozen.items():assert ident(path)==v
    for path,v in models['files'].items():assert ident(path)==v
    for path,v in models['large_stat_only'].items():
        s=Path(path).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns']
    assert ident(R/'bin/evaluate')==json.loads((R/'reviews/binary_before_source.json').read_text())['binary']
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=C['max_new_bytes']
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())<=C['max_campaign_bytes']
    print('ALL FOUR FROZEN CASES COMPLETE',flush=True)
if __name__=='__main__':main()
