import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ident(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def total(p):return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())
def guard():
    assert total(R)<C['max_stage_bytes'] and total(CAMP)<C['max_campaign_bytes'],'artifact cap'
    assert shutil.disk_usage(R).free>=C['min_free_bytes'],'disk reserve'
    assert time.time()<C['deadline_unix'],'deadline'
def check_inputs():
    for p,v in read(R/'reviews/consumed_inputs.json').items():assert ident(p)==v,p
    for p,v in read(R/'reviews/large_inputs_stat.json').items():
        st=Path(p).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns'],p
def build():
    guard();old=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';args=read(old/'reviews/build.json')['argv']
    args=[a.replace(str(old/'src/experiment.cpp'),str(R/'src/experiment.cpp')).replace(str(old/'bin/experiment'),str(R/'bin/experiment')).replace('-I'+str(old/'src/common'),'-I'+str(R/'src/common')) for a in args]
    args[1:1]=['-MMD','-MF',str(R/'bin/dependencies.d')];start=time.perf_counter()
    with (R/'logs/build.log').open('x') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=300)
    put(R/'reviews/build.json',{'argv':args,'seconds':time.perf_counter()-start,'exit_code':r.returncode,'source':{str(p):ident(p) for p in (R/'src').rglob('*') if p.is_file()},'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0]})
    assert r.returncode==0,'compile failure: preserve before correction';print('COMPILE_PASS',flush=True)
def run():
    guard();check_inputs();b=read(R/'reviews/build.json');assert b['exit_code']==0
    for p,v in b['source'].items():assert ident(p)==v,p
    deps=(R/'bin/dependencies.d').read_text().replace('\\\n',' ').split(':',1)[1].split()
    files=[R/n for n in ('protocol.md','theory.md','prepare.py','execute.py','config.locked.json','resource_amendment.json')]
    files += [p for folder in ('src','inputs') for p in (R/folder).rglob('*') if p.is_file()]+[R/'bin/experiment']
    files += [Path(p) for p in deps if Path(p).is_file()]+[Path(p) for p in b['argv'] if p.endswith('.a')]
    frozen={str(p):ident(p) for p in files};put(R/'reviews/run_frozen.json',{'unix':time.time(),'files':frozen})
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
    state=read(CAMP/'state.json');assert state['active_process'] is None
    state.update(stage='query_target_transfer_running',active_process={'wrapper_pid':os.getpid(),'stage':R.name},last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    jobs=[];build_seconds=b['seconds'];search_seconds=0.;new_nsg=0;new_ann=0
    for phase in ('build','measure'):
        if phase=='measure':
            put(R/'reviews/models_frozen.json',{'status':'PASS','unix':time.time(),'files':{str(p):ident(p) for p in (R/'models').rglob('*') if p.is_file()},'all_models_before_any_evaluation':True})
        for ds,c in C['datasets'].items():
            guard();check_inputs();cmd=['taskset','-c','15',str(R/'bin/experiment'),phase,str(R/'inputs'/ds/'native.json')]
            start=time.perf_counter();rss=0;maxthreads=0;stopped=None
            with (R/'logs'/f'{ds}.{phase}.log').open('x') as log:
                proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);put(R/'reviews'/f'{ds}.{phase}.pid.json',{'pid':proc.pid,'argv':cmd,'unix':time.time()})
                while proc.poll() is None:
                    try:
                        values={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line}
                        executable=Path(f'/proc/{proc.pid}/cmdline').read_bytes().split(b'\0')[0].decode();th=int(values['Threads']);maxthreads=max(maxthreads,th);rss=max(rss,int(values.get('VmRSS','0 kB').split()[0])*1024)
                        if executable==str(R/'bin/experiment'):assert th==1 and values['Cpus_allowed_list']=='15','CPU15 actual one thread'
                        assert rss<=C['maxrss_bytes'];guard()
                        if phase=='build':assert build_seconds+time.perf_counter()-start<=C['compile_and_build_seconds_cap'],'compile/build cap'
                        else:assert search_seconds+time.perf_counter()-start<=C['search_seconds_cap'],'search cap'
                    except FileNotFoundError:pass
                    except Exception as e:stopped=str(e);proc.terminate();break
                    time.sleep(1)
                code=proc.wait(timeout=10)
            elapsed=time.perf_counter()-start
            if phase=='build':build_seconds+=elapsed
            else:search_seconds+=elapsed
            j={'phase':phase,'dataset':ds,'argv':cmd,'exit_code':code,'seconds':elapsed,'max_threads':maxthreads,'max_observed_rss':rss,'stopped':stopped};jobs.append(j);put(R/'reviews'/f'{ds}.{phase}.job.json',j)
            assert code==0 and stopped is None,f'{phase}/{ds} failure: preserve logs'
            if phase=='measure':
                done=read(R/'results'/ds/'complete.json');new_nsg+=done['new_NSG'];new_ann+=done['new_ANN']
                assert new_nsg<=C['max_new_NSG'] and new_ann<=C['max_new_ANN']
            print('PHASE_COMPLETE',phase,ds,elapsed,flush=True)
    check_inputs()
    for p,v in frozen.items():assert ident(p)==v,p
    for p,v in read(R/'reviews/models_frozen.json')['files'].items():assert ident(p)==v,p
    assert new_nsg==C['expected_NSG'] and new_ann==C['expected_ANN'];guard()
    put(R/'reviews/jobs_complete.json',{'status':'PASS','jobs':jobs,'compile_and_build_seconds':build_seconds,'search_job_seconds':search_seconds,'new_NSG':new_nsg,'new_ANN':new_ann,'new_graphs':4,'CPU15_actual1_serial':True,'all_sources_inputs_models_unchanged':True,'stage_bytes':total(R),'campaign_bytes':total(CAMP)})
    state=read(CAMP/'state.json');state['new_NSG_calls']+=new_nsg;state['new_ANN_calls']+=new_ann;state['new_graphs']+=4
    state.update(stage='query_target_transfer_measured_pending_independent_audit',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print('ALL_NATIVE_COMPLETE',new_nsg,new_ann,search_seconds,flush=True)
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('build','run');globals()[sys.argv[1]]()
