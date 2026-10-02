import os,json,hashlib,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    assert json.loads((R/'reviews/preparation.json').read_text())['lazy_helper_unchanged_fixture_already_PASS']
    os.sched_setaffinity(0,{14})
    prep=json.loads((R/'reviews/preparation.json').read_text())
    for p,v in prep['inputs'].items():assert ident(p)==v,p
    sources=[R/'config.locked.json',R/'protocol.md',*R.glob('*.py')]
    dump(R/'reviews/run_frozen.json',{'inputs':{str(p):ident(p) for p in sources},'unix':time.time()})
    started=time.perf_counter();env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'};jobs={};datasets={}
    def check():
        assert time.time()<C['deadline_unix'] and time.perf_counter()-started<C['seconds_cap'] and shutil.disk_usage(R).free>=C['min_free_bytes']
        assert dataset_started is None or time.perf_counter()-dataset_started<C['per_dataset_seconds_cap']
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
    status='FAILED';dataset_started=None
    try:
      for ds,c in C['datasets'].items():
        check();dataset_started=time.perf_counter();out=Path(c['output']);cfg=R/'inputs'/f'{ds}.json';names=[]
        name=ds+'_exact';run(name,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/'exact.py'),str(cfg)]);names.append(name)
        label={k:c[k] for k in ['base','base_n','dimension','index','L']};label.update(n=20000,queries=c['fit_queries'],deadline_unix=C['deadline_unix'])
        dump(out/'labels.config.json',label)
        name=ds+'_teacher';run(name,['taskset','-c','15',C['teacher_binary'],str(out/'labels.config.json'),str(out/'labels')],True);names.append(name)
        for method in [C['primary'],C['control']]:
            control_started=time.perf_counter();method_names=[]
            for stage in ['choose','additional','profile']:
                name=ds+'_'+method+'_'+stage
                run(name,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/(stage+'.py')),str(cfg),method]);method_names.append(name)
            model={'name':method,'W':str(out/method/'W.f32'),'ids':str(out/'ids.i32'),'graph':str(out/method/'router.hnsw')}
            dump(out/method/'router.config.json',{'dimension':c['dimension'],'methods':[model,model]})
            name=ds+'_'+method+'_router';run(name,['taskset','-c','0-7',C['router_binary'],str(out/method/'router.config.json'),str(out/method/'router_complete.json')]);method_names.append(name)
            if method==C['primary']:
                names+=method_names;seconds=time.perf_counter()-dataset_started
                datasets[ds]={'complete_build_wall_seconds':seconds,'job_seconds_sum':sum(jobs[k]['seconds'] for k in names),'jobs':names}
                dump(out/'build_complete.json',{'status':'BUILT_PENDING_IDENTITY_AUDIT',**datasets[ds]});print(ds,'FULL ENERGY BUILD',seconds,flush=True)
            else:
                datasets[ds]['control_incremental_wall_seconds']=time.perf_counter()-control_started
                datasets[ds]['control_jobs']=method_names
                dump(out/'control_complete.json',{'status':'BUILT_PENDING_IDENTITY_AUDIT','incremental_wall_seconds':datasets[ds]['control_incremental_wall_seconds'],'jobs':method_names,'shares_H_approx_labels_pilot':True})
        check();dataset_started=None
      status='BUILT_PENDING_IDENTITY_AUDIT'
    finally:
        (R/'reviews/active_process.json').write_text(json.dumps({'pid':None,'status':status,'unix':time.time()})+'\n')
        dump(R/'reviews/run_complete.json',{'status':status,'seconds':time.perf_counter()-started,'jobs':jobs,'datasets':datasets,'default_changed':False})
    for p,v in prep['inputs'].items():assert ident(p)==v
    for p,v in prep['large_stat_only'].items():
        s=Path(p).stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns']
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<C['max_new_bytes']
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())<C['max_campaign_bytes']
    print('BUILT BOTH',flush=True)
if __name__=='__main__':main()
