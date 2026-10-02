import os,json,hashlib,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];OLD=ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1';C=json.loads((R/'config.locked.json').read_text());start=time.perf_counter();jobs={}
assert json.loads((P/'research/target_budget_fullH_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
assert json.loads((R/'reviews/prepare_complete.json').read_text())['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):assert not p.exists(),p;p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
for p,v in json.loads((R/'reviews/prepare_inputs.json').read_text()).items():assert ident(Path(p))==v,p
big={}
for c in C['datasets'].values():
    for k in ['index','base']:
        p=Path(c['original'][k]);st=p.stat();big[str(p)]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
files=[R/'protocol.md',R/'theory.md',R/'config.locked.json']+[p for p in (R/'src').rglob('*') if p.is_file()]
dump(R/'reviews/run_frozen.json',{'files':{str(p):ident(p) for p in files},'large_stat_only':big,'unix':time.time()})
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',OMP_DYNAMIC='FALSE',NUMEXPR_NUM_THREADS='1')
def run(name,argv,cpu_check=False):
    assert time.time()<C['deadline_unix'] and shutil.disk_usage(R).free>=6*2**30
    t=time.perf_counter();maxthreads=0;maxrss=0
    with (R/'logs'/f'{name}.log').open('x') as f:
        p=subprocess.Popen(argv,env=env,stdout=f,stderr=subprocess.STDOUT)
        while p.poll() is None:
            try:
                st=Path(f'/proc/{p.pid}/status').read_text();kv={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in st.splitlines() if ':' in s};th=int(kv['Threads']);maxthreads=max(maxthreads,th);maxrss=max(maxrss,int(kv.get('VmRSS','0 kB').split()[0])*1024)
                exe=Path(f'/proc/{p.pid}/cmdline').read_bytes().split(b'\0')[0].decode()
                if cpu_check and exe.startswith(str(R/'bin')):assert th==1 and kv['Cpus_allowed_list']=='15'
            except FileNotFoundError:pass
            if time.time()>=C['deadline_unix'] or time.perf_counter()-start>2700 or shutil.disk_usage(R).free<6*2**30:p.terminate();break
            time.sleep(.5)
        code=p.wait(timeout=10)
    job={'exit_code':code,'seconds':time.perf_counter()-t,'max_threads':maxthreads,'maxrss_bytes':maxrss,'argv':argv};jobs[name]=job;dump(R/'reviews'/f'{name}.job.json',job);assert code==0,name;print(name,'PASS',job['seconds'],flush=True)
baseargv=json.loads((OLD/'reviews/build.json').read_text())['argv']
for name in ['labels','evaluate','build_router']:
    argv=[str(R/'src'/f'{name}.cpp') if x==str(OLD/'src/evaluate.cpp') else str(R/'bin'/name) if x==str(OLD/'bin/evaluate') else '-I'+str(R/'src/common') if x=='-I'+str(OLD/'src/common') else x for x in baseargv];run('compile_'+name,argv)
for ds in C['datasets']:
    (R/'results'/ds).mkdir();run(ds+'_labels',['taskset','-c','15',str(R/'bin/labels'),str(R/'inputs'/ds/'labels.json'),str(R/'results'/ds/'labels')],True)
run('profiles',[str(ROOT/'.venv_cpu/bin/python'),str(R/'src/profiles.py')])
for ds in C['datasets']:run(ds+'_router',['taskset','-c','0-7',str(R/'bin/build_router'),str(R/'inputs'/ds/'evaluate.json'),str(R/'models'/ds/'router_build.json')])
dump(R/'reviews/models_frozen_before_evaluation.json',{'files':{str(p):ident(p) for p in (R/'models').rglob('*') if p.is_file()},'unix':time.time()})
for ds in C['datasets']:run(ds+'_evaluate',['taskset','-c','15',str(R/'bin/evaluate'),str(R/'inputs'/ds/'evaluate.json'),str(R/'results'/ds/'evaluation')],True)
calls=sum(json.loads((R/'results'/ds/'labels/complete.json').read_text())['new_NSG_calls']+json.loads((R/'results'/ds/'evaluation/complete.json').read_text())['search_calls'] for ds in C['datasets']);assert calls==531968 and calls<=C['max_new_NSG']
for p,v in big.items():st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
dump(R/'reviews/jobs_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'jobs':jobs,'new_NSG_calls':calls,'new_ANN_calls':491520,'candidate_profile_fits':2,'candidate_graph_builds':2,'exact_control_profile_reconstructions':2,'complete_wall_points':24,'wall_rounds':72,'new_exact_GT':0,'new_source_payloads':0,'default_changed':False})
print('ALL COMPLETE',flush=True)
