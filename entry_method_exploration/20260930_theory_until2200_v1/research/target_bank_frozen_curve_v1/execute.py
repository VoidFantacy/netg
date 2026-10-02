import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent;CAMP=R.parents[1];ROOT=R.parents[3];C=json.loads((R/'config.locked.json').read_text())
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
    with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
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
        s=Path(p).stat();assert (s.st_size,s.st_mtime_ns)==(v['bytes'],v['mtime_ns']),p
def build():
    guard();old=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';args=read(old/'reviews/build.json')['argv']
    args=[s.replace(str(old/'src/experiment.cpp'),str(R/'src/experiment.cpp')).replace(str(old/'bin/experiment'),str(R/'bin/experiment')).replace('-I'+str(old/'src/common'),'-I'+str(R/'src/common')) for s in args]
    args[1:1]=['-MMD','-MF',str(R/'bin/dependencies.d')];start=time.perf_counter()
    with (R/'logs/build.log').open('x') as f:p=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=C['compile_seconds_cap'])
    put(R/'reviews/build.json',{'argv':args,'seconds':time.perf_counter()-start,'exit_code':p.returncode,'compiler':subprocess.check_output(['g++','--version'],text=True).splitlines()[0],'source':{str(p):ident(p) for p in (R/'src').rglob('*') if p.is_file()}})
    assert p.returncode==0,'compile failure; preserve original';print('CURVE_COMPILE_PASS',flush=True)
def run():
    guard();check_inputs();build=read(R/'reviews/build.json');assert build['exit_code']==0
    for p,v in build['source'].items():assert ident(p)==v,p
    for p,v in read(R/'reviews/copied_source.json')['files'].items():assert ident(R/'src'/p)==v,p
    deps=(R/'bin/dependencies.d').read_text().replace('\\\n',' ').split(':',1)[1].split()
    files=[R/n for n in ['protocol.md','prepare.py','execute.py','config.locked.json','resource_amendment.json']]
    files += [p for name in ['src','inputs'] for p in (R/name).rglob('*') if p.is_file()]+[R/'bin/experiment']+[Path(p) for p in deps if Path(p).is_file()]+[Path(p) for p in build['argv'] if p.endswith('.a')]
    for c in C['datasets'].values():
        for p in c['points']:
            old=Path(c['old_results'])/f'k{p["K"]}'/f'{c["anchor"]["name"]}_L{p["L"]}'
            files += [old/n for n in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64']]
            for name in C['methods']:
                center=Path(c['previous_results'])/f'k{p["K"]}_L{p["L"]}'/name
                if center.exists():files += [center/n for n in ['ids.i32','distances.f32','entry_ids.i32','route_ndc.u64','graph_ndc.u64','route_slots.i32']]
    frozen={str(p):ident(p) for p in files};put(R/'reviews/run_frozen.json',{'unix':time.time(),'files':frozen,'reuses_165_frozen_models':True,'no_build_or_model_tuning':True})
    state=read(CAMP/'state.json');assert state['active_process'] is None
    state.update(stage='target_bank_frozen_curve_running',active_process={'wrapper_pid':os.getpid(),'stage':R.name},last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
    jobs=[];wall=0.;new_nsg=new_ann=0
    for ds,c in C['datasets'].items():
        guard();check_inputs();cmd=['taskset','-c','15',str(R/'bin/experiment'),str(R/'inputs'/ds/'native.json')];start=time.perf_counter();rss=0;maxt=0;stopped=None
        with (R/'logs'/f'{ds}.measure.log').open('x') as f:
            p=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT);put(R/'reviews'/f'{ds}.pid.json',{'pid':p.pid,'argv':cmd,'unix':time.time()})
            while p.poll() is None:
                try:
                    vals={s.split(':',1)[0]:s.split(':',1)[1].strip() for s in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in s}
                    exe=Path(f'/proc/{p.pid}/cmdline').read_bytes().split(b'\0')[0].decode();t=int(vals['Threads']);maxt=max(maxt,t);rss=max(rss,int(vals.get('VmRSS','0 kB').split()[0])*1024)
                    if exe==str(R/'bin/experiment'):assert t==1 and vals['Cpus_allowed_list']=='15','actual CPU15 one thread'
                    assert rss<=C['maxrss_bytes'];guard();assert wall+time.perf_counter()-start<=C['search_seconds_cap'],'search wall cap'
                except FileNotFoundError:pass
                except Exception as e:stopped=str(e);p.terminate();break
                time.sleep(1)
            code=p.wait(timeout=10)
        elapsed=time.perf_counter()-start;wall+=elapsed;j={'dataset':ds,'argv':cmd,'exit_code':code,'seconds':elapsed,'max_threads':maxt,'max_observed_rss':rss,'stopped':stopped};jobs.append(j);put(R/'reviews'/f'{ds}.job.json',j)
        assert code==0 and stopped is None,'preserve failure and audit before correction'
        done=read(R/'results'/ds/'complete.json');new_nsg+=done['new_NSG'];new_ann+=done['new_ANN'];assert new_nsg<=C['max_new_NSG'] and new_ann<=C['max_new_ANN'];print('CURVE_DATASET_COMPLETE',ds,elapsed,flush=True)
    guard();check_inputs()
    for p,v in frozen.items():assert ident(p)==v,p
    assert new_nsg==C['expected_NSG'] and new_ann==C['expected_ANN']
    put(R/'reviews/jobs_complete.json',{'status':'PASS','jobs':jobs,'compile_seconds':build['seconds'],'search_job_seconds':wall,'new_NSG':new_nsg,'new_ANN':new_ann,'new_graphs':0,'CPU15_actual1_serial':True,'all_sources_inputs_models_unchanged':True,'stage_bytes':total(R),'campaign_bytes':total(CAMP)})
    state=read(CAMP/'state.json');state['new_NSG_calls']+=new_nsg;state['new_ANN_calls']+=new_ann;state.update(stage='target_bank_frozen_curve_measured_pending_audit',active_process=None,last_updated_unix=time.time());(CAMP/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    print('ALL_CURVE_NATIVE_COMPLETE',new_nsg,new_ann,wall,flush=True)
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ['build','run'];globals()[sys.argv[1]]()
