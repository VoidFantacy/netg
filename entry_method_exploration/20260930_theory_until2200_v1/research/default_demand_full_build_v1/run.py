import os
os.sched_setaffinity(0,{14})
import hashlib,json,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    prep=json.loads((R/'reviews/preparation.json').read_text())
    for p,v in prep['inputs'].items():assert ident(p)==v
    frozen={str(p):ident(p) for p in [R/'config.locked.json',R/'protocol.md',*R.glob('*.py')]}
    dump(R/'reviews/run_frozen.json',{'unix':time.time(),'inputs':frozen})
    started=time.perf_counter();dataset_start=started;jobs={};datasets={};env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'}
    def check():
        assert time.time()<C['deadline_unix'] and time.perf_counter()-started<C['seconds_cap'] and time.perf_counter()-dataset_start<C['per_dataset_seconds_cap']
        assert shutil.disk_usage(R).free>=C['min_free_bytes']
    def run(name,argv):
        check();t=time.perf_counter();ru=resource.getrusage(resource.RUSAGE_CHILDREN);maxrss=maxthreads=0;affinity=set()
        with (R/'logs'/f'{name}.log').open('x') as log:
            p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
            (R/'reviews/active_process.json').write_text(json.dumps({'pid':p.pid,'name':name,'argv':argv,'unix':time.time()})+'\n')
            try:
                while p.poll() is None:
                    check()
                    try:
                        status=dict(x.split(':',1) for x in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in x)
                        maxthreads=max(maxthreads,int(status['Threads']));maxrss=max(maxrss,int(status.get('VmRSS','0 kB').split()[0])*1024);affinity.add(status['Cpus_allowed_list'].strip())
                    except FileNotFoundError:pass
                    time.sleep(.2)
                code=p.wait(timeout=5)
            except BaseException:
                if p.poll() is None:p.terminate();p.wait(timeout=10)
                raise
        after=resource.getrusage(resource.RUSAGE_CHILDREN);record={'exit_code':code,'seconds':time.perf_counter()-t,'argv':argv,'maxrss_bytes':maxrss,'max_threads':maxthreads,
            'affinity_samples':sorted(affinity),'user_cpu_seconds':after.ru_utime-ru.ru_utime,'system_cpu_seconds':after.ru_stime-ru.ru_stime}
        jobs[name]=record;dump(R/'reviews'/f'{name}.job.json',record);assert code==0,name;print(name,'PASS',record['seconds'],flush=True)
    status='FAILED'
    try:
        for ds,c in C['datasets'].items():
            dataset_start=time.perf_counter();names=[];cfg=R/'inputs'/f'{ds}.json';out=Path(c['output'])
            for stage in ['exact','profile']:
                name=ds+'_'+stage;run(name,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/f'{stage}.py'),str(cfg)]);names.append(name)
            method={'name':'DefaultDemandQGT','W':str(out/'W.f32'),'ids':str(out/'ids.i32'),'graph':str(out/'router.hnsw')}
            dump(out/'router.config.json',{'dimension':c['dimension'],'methods':[method,method]})
            name=ds+'_router';run(name,['taskset','-c','0-7',C['router_binary'],str(out/'router.config.json'),str(out/'router_complete.json')]);names.append(name)
            datasets[ds]={'complete_build_wall_seconds':time.perf_counter()-dataset_start,'job_seconds_sum':sum(jobs[k]['seconds'] for k in names),'jobs':names}
            dump(out/'build_complete.json',{'status':'BUILT_PENDING_IDENTITY_AUDIT',**datasets[ds]});print(ds,'FULL BUILD',datasets[ds]['complete_build_wall_seconds'],flush=True)
        count=sum(json.loads((Path(c['output'])/'exact_complete.json').read_text())['new_GT'] for c in C['datasets'].values());assert count<=C['max_exact_queries']
        status='BUILT_PENDING_IDENTITY_AUDIT'
    finally:
        (R/'reviews/active_process.json').write_text(json.dumps({'pid':None,'status':status,'unix':time.time()})+'\n')
        dump(R/'reviews/run_complete.json',{'status':status,'seconds':time.perf_counter()-started,'jobs':jobs,'datasets':datasets,'default_changed':False})
    for p,v in {**prep['inputs'],**frozen}.items():assert ident(p)==v
    for p,v in prep['large_stat_only'].items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=C['max_new_bytes']
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())<=C['max_campaign_bytes']
    print('BUILT BOTH DEFAULTS',flush=True)
if __name__=='__main__':main()
