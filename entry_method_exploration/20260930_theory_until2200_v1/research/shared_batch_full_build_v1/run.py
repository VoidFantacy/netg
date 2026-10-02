import os
os.sched_setaffinity(0,{14})
import hashlib,json,resource,shutil,subprocess,time
from pathlib import Path
from budget import reserve,commit
R=Path(__file__).resolve().parent;ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())

def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}

def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def main():
    assert time.time()<C['latest_start_unix'];prep=json.loads((R/'reviews/preparation.json').read_text())
    for group in ['inputs','libraries']:
        for p,v in prep[group].items():assert ident(p)==v,p
    started=time.perf_counter();build_start=None;jobs={};cases={};status='FAILED'
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE'}
    def check():
        assert time.time()<C['deadline_unix'] and time.time()-C['stage_started_unix']<C['seconds_cap']
        assert build_start is None or time.perf_counter()-build_start<C['per_build_seconds_cap']
        assert shutil.disk_usage(R).free>=C['min_free_bytes']
    def check_size():
        assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=C['max_new_bytes']
        assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())<=C['max_campaign_bytes']
    def run(name,argv,single=False,require_external_samples=True):
        check();check_size();t=time.perf_counter();ru=resource.getrusage(resource.RUSAGE_CHILDREN);mt=mr=checks=0;aff=set()
        with (R/'logs'/(name+'.log')).open('x') as log:
            p=subprocess.Popen(argv,env=env,stdout=log,stderr=subprocess.STDOUT)
            (R/'reviews/active_process.json').write_text(json.dumps({'pid':p.pid,'name':name,'argv':argv,'unix':time.time()})+'\n')
            try:
                while p.poll() is None:
                    check()
                    try:
                        kv=dict(x.split(':',1) for x in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in x)
                        count=int(kv['Threads']);mt=max(mt,count);mr=max(mr,int(kv.get('VmRSS','0 kB').split()[0])*1024);aff.add(kv['Cpus_allowed_list'].strip())
                        if single and Path(f'/proc/{p.pid}/cmdline').read_bytes().startswith(argv[3].encode()):
                            assert count==1 and kv['Cpus_allowed_list'].strip()=='15';checks+=1
                    except FileNotFoundError:pass
                    time.sleep(.2)
                code=p.wait(timeout=5)
            except BaseException:
                if p.poll() is None:p.terminate();p.wait(timeout=10)
                raise
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        rec={'exit_code':code,'seconds':time.perf_counter()-t,'max_threads':mt,'maxrss_bytes':mr,'affinity_samples':sorted(aff),'single_thread_samples':checks,
             'user_cpu_seconds':after.ru_utime-ru.ru_utime,'system_cpu_seconds':after.ru_stime-ru.ru_stime,'argv':argv}
        jobs[name]=rec;dump(R/'reviews'/(name+'.job.json'),rec);assert code==0,name
        if single and require_external_samples:assert checks>0
        print(name,'PASS',round(rec['seconds'],3),flush=True);return rec
    def python(stage,case,cfg):return run(case+'_'+stage,['taskset','-c','0-7',str(ROOT/'.venv_cpu/bin/python'),str(R/(stage+'.py')),str(cfg)])
    try:
        for name in C['order']:
            c=C['cases'][name];cfg=R/'inputs'/(name+'.json');out=Path(c['output']);check();build_start=time.perf_counter();names=[]
            python('build_exact',name,cfg);names.append(name+'_build_exact')
            if c['method']!='Default':
                n=17952 if c['method']=='Uniform' and not c['soft'] else 20000
                label={k:c[k] for k in ['base','base_n','dimension','index','L']}
                label.update(n=n,source_n=20000,queries=c['fit_queries'],deadline_unix=C['deadline_unix'],max_NSG_calls=n+32)
                if n!=20000:label['query_rows']=str(out/'approx_rows.i32')
                dump(out/'labels.config.json',label);reserve(C,'NSG',n+32,name+':teacher')
                run(name+'_teacher',['taskset','-c','15',C['teacher_binary'],str(out/'labels.config.json'),str(out/'labels')],True)
                complete=json.loads((out/'labels/complete.json').read_text());assert complete['new_NSG_calls']==n+32 and complete['status']=='PASS';commit('NSG',n+32);names.append(name+'_teacher')
                if c['method']=='EnergyTree':
                    for stage in ['choose','additional']:
                        python(stage,name,cfg);names.append(name+'_'+stage)
            python('profile',name,cfg);names.append(name+'_profile')
            model={'name':c['method'],'ids':str(out/'ids.i32'),'W':str(out/'W.f32'),'graph':str(out/'router.hnsw')}
            dump(out/'router.config.json',{'dimension':c['dimension'],'methods':[model,model]})
            run(name+'_router',['taskset','-c','0-7',C['router_binary'],str(out/'router.config.json'),str(out/'router_complete.json')]);names.append(name+'_router')
            elapsed=time.perf_counter()-build_start;cases[name]={'dataset':c['dataset'],'method':c['method'],'complete_build_wall_seconds':elapsed,'jobs':names,
                'job_seconds_sum':sum(jobs[x]['seconds'] for x in names)}
            dump(out/'build_complete.json',{'status':'BUILT_PENDING_IDENTITY_AUDIT',**cases[name]});print(name,'FULL BUILD',elapsed,flush=True)
            build_start=None;check();check_size()
        status='BUILT_PENDING_IDENTITY_AUDIT'
        # Native router parity is an audit, outside every complete-build interval.
        for name in C['order']:
            c=C['cases'][name];out=Path(c['output']);model={'name':c['method'],'ids':str(out/'ids.i32'),'W':str(out/'W.f32'),'graph':str(out/'router.hnsw')}
            dump(out/'router_audit.config.json',{'dimension':c['dimension'],'queries':c['fit_queries'],'model':model})
            reserve(C,'ANN',512,name+':router_audit')
            run(name+'_router_audit',['taskset','-c','15',C['audit_binary'],str(out/'router_audit.config.json'),str(out/'router_audit.json')],True,False)
            a=json.loads((out/'router_audit.json').read_text());assert a['status']=='PASS' and a['new_ANN_calls']==512;commit('ANN',512)
        check_size()
    finally:
        (R/'reviews/active_process.json').write_text(json.dumps({'pid':None,'status':status,'unix':time.time()})+'\n')
        dump(R/'reviews/run_complete.json',{'status':status,'seconds':time.perf_counter()-started,'jobs':jobs,'cases':cases,'default_changed':False,'new_online_performance':False})
    for group in ['inputs','libraries']:
        for p,v in prep[group].items():assert ident(p)==v,p
    for p,v in prep['large'].items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
    print('ALL SIX BUILDS AND NATIVE ROUTER AUDITS COMPLETE',flush=True)

if __name__=='__main__':main()
