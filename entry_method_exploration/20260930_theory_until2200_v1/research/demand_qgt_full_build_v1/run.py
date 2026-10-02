import os,json,hashlib,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    assert json.loads((R/'reviews/fixture.json').read_text())['status']=='PASS'
    prep=json.loads((R/'reviews/preparation.json').read_text())
    for p,v in prep['inputs'].items():assert ident(p)==v,p
    sources=[R/'config.locked.json',R/'protocol.md',*R.glob('*.py')]
    dump(R/'reviews/run_frozen.json',{'inputs':{str(p):ident(p) for p in sources},'unix':time.time()})
    started=time.perf_counter();env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'};jobs={};datasets={}
    def check():
        assert time.time()<C['deadline_unix'] and time.perf_counter()-started<C['seconds_cap'] and shutil.disk_usage(R).free>=6*2**30
    def run(name,argv,single=False):
        check();t=time.perf_counter();ru=resource.getrusage(resource.RUSAGE_CHILDREN);maxthreads=maxrss=checks=0;affinities=set()
        with (R/'logs'/f'{name}.log').open('x') as out:
            p=subprocess.Popen(argv,env=env,stdout=out,stderr=subprocess.STDOUT)
            (R/'reviews/active_process.json').write_text(json.dumps({'pid':p.pid,'name':name,'argv':argv,'unix':time.time()})+'\n')
            try:
                while p.poll() is None:
                    check()
                    try:
                        kv=dict(x.split(':',1) for x in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in x)
                        count=int(kv['Threads']);maxthreads=max(count,maxthreads);maxrss=max(maxrss,int(kv.get('VmRSS','0 kB').split()[0])*1024)
                        affinities.add(kv['Cpus_allowed_list'].strip())
                        if single and Path(f'/proc/{p.pid}/cmdline').read_bytes().startswith(C['teacher_binary'].encode()):
                            assert count==1 and kv['Cpus_allowed_list'].strip()=='15';checks+=1
                    except FileNotFoundError:pass
                    time.sleep(.2)
                code=p.wait(timeout=5)
            except BaseException:
                if p.poll() is None:p.terminate();p.wait(timeout=10)
                raise
        elapsed=time.perf_counter()-t;after=resource.getrusage(resource.RUSAGE_CHILDREN)
        result={'exit_code':code,'seconds':elapsed,'max_threads':maxthreads,'maxrss_bytes':maxrss,'affinity_samples':sorted(affinities),
            'single_thread_samples':checks,'user_cpu_seconds':after.ru_utime-ru.ru_utime,'system_cpu_seconds':after.ru_stime-ru.ru_stime,'argv':argv}
        jobs[name]=result;dump(R/'reviews'/f'{name}.job.json',result);assert code==0,name
        if single:assert checks>0
        print(name,'PASS',round(elapsed,3),flush=True);return result
    status='FAILED'
    try:
      for ds,c in C['datasets'].items():
        check();t=time.perf_counter();out=Path(c['output']);cfg=R/'inputs'/f'{ds}.json';names=[]
        name=ds+'_exact';run(name,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/'exact.py'),str(cfg)]);names.append(name)
        label={k:c[k] for k in ['base','base_n','dimension','index','L']};label.update(n=17952,queries=str(out/'approx_queries.f32'),deadline_unix=C['deadline_unix'])
        dump(out/'labels.config.json',label)
        name=ds+'_teacher';run(name,['taskset','-c','15',C['teacher_binary'],str(out/'labels.config.json'),str(out/'labels')],True);names.append(name)
        name=ds+'_profile';run(name,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/'profile.py'),str(cfg)]);names.append(name)
        method={'name':'FrozenHybrid','W':str(out/'W.f32'),'ids':str(out/'ids.i32'),'graph':str(out/'router.hnsw')}
        dump(out/'router.config.json',{'dimension':c['dimension'],'methods':[method,method]})
        name=ds+'_router';run(name,['taskset','-c','0-7',C['router_binary'],str(out/'router.config.json'),str(out/'router_complete.json')]);names.append(name)
        seconds=time.perf_counter()-t
        datasets[ds]={'complete_build_wall_seconds':seconds,'job_seconds_sum':sum(jobs[k]['seconds'] for k in names),'jobs':names}
        dump(out/'build_complete.json',{'status':'BUILT_PENDING_IDENTITY_AUDIT',**datasets[ds]})
        print(ds,'FULL BUILD',seconds,flush=True)
      status='BUILT_PENDING_IDENTITY_AUDIT'
    finally:
        (R/'reviews/active_process.json').write_text(json.dumps({'pid':None,'status':status,'unix':time.time()})+'\n')
        dump(R/'reviews/run_complete.json',{'status':status,'seconds':time.perf_counter()-started,'jobs':jobs,'datasets':datasets,'default_changed':False})
    for p,v in prep['inputs'].items():assert ident(p)==v
    for p,v in prep['large_stat_only'].items():
        s=Path(p).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns']
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<C['max_new_bytes']
    print('BUILT BOTH',flush=True)
if __name__=='__main__':main()
