import os,json,hashlib,time,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];OLD=ROOT/'entry_method_exploration/20260921_comparison_direction_pilot_v1';C=json.loads((R/'config.locked.json').read_text())
assert (P/'research/gt_inclusive_build_cost_v1/reviews/rebuild_complete.json').exists(),'GT worker must have ended'
assert json.loads((R/'reviews/prepare_complete.json').read_text())['status']=='PASS'
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2)+'\n')
for name,v in json.loads((R/'reviews/prepare_inputs.json').read_text()).items():assert ident(Path(name))==v,name
big_inputs={}
for dc in C['datasets'].values():
    for key in ['base','index']:
        pp=Path(dc[key]);st=pp.stat();big_inputs[str(pp)]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
dump(R/'reviews/large_inputs_before.json',{'stat_only':big_inputs,'not_a_new_full_file_hash':True,'native_base_graph_vector_byte_checks_per_dataset':32})
files=[R/'protocol.md',R/'config.locked.json']+[p for p in (R/'src').rglob('*') if p.is_file()]+[p for p in (R/'inputs_v2').rglob('*') if p.is_file()]
dump(R/'reviews/run_frozen.json',{'files':{str(p):ident(p) for p in files},'unix':time.time(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()})
argv=json.loads((OLD/'reviews/build.json').read_text())['argv'];argv=[str(R/'src/measure.cpp') if x==str(OLD/'src/experiment.cpp') else str(R/'bin/measure') if x==str(OLD/'bin/experiment') else '-I'+str(R/'src/common') if x=='-I'+str(OLD/'src/common') else x for x in argv]
buildstart=time.perf_counter()
with (R/'logs/build.log').open('x') as f:res=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT)
dump(R/'reviews/build.json',{'argv':argv,'seconds':time.perf_counter()-buildstart,'exit_code':res.returncode});assert res.returncode==0
start=time.perf_counter();jobs={};env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',OMP_DYNAMIC='FALSE')
for ds,dc in C['datasets'].items():
    assert shutil.disk_usage(R).free>=6*2**30;assert time.time()<C['deadline_unix'];cp=R/'inputs_v2'/ds/'config.json';out=R/'results'/ds;cmd=['taskset','-c','15',str(R/'bin/measure'),str(cp),str(out)];begin=time.perf_counter();maxrss=0;maxthreads=0;stop=None
    with (R/'logs'/f'{ds}.log').open('x') as log:
        proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT);dump(R/'reviews'/f'{ds}.pid.json',{'pid':proc.pid,'argv':cmd,'unix':time.time()})
        while proc.poll() is None:
            try:
                s=Path(f'/proc/{proc.pid}/status').read_text();kv={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in s.splitlines() if ':' in x};threads=int(kv['Threads']);maxthreads=max(maxthreads,threads);maxrss=max(maxrss,int(kv.get('VmRSS','0 kB').split()[0])*1024)
                executable=Path(f'/proc/{proc.pid}/cmdline').read_bytes().split(b'\0')[0].decode()
                if executable==str(R/'bin/measure'):
                    assert threads==1,'child must remain one thread';assert kv['Cpus_allowed_list']=='15','CPU15 affinity'
            except FileNotFoundError:pass
            if time.time()>=C['deadline_unix'] or time.perf_counter()-start>=3600 or shutil.disk_usage(R).free<6*2**30:
                stop='frozen resource or time cap';proc.terminate();break
            time.sleep(1)
        code=proc.wait(timeout=10)
    job={'argv':cmd,'exit_code':code,'seconds':time.perf_counter()-begin,'max_process_threads':maxthreads,'max_observed_rss_bytes':maxrss,'stop_reason':stop};jobs[ds]=job;dump(R/'reviews'/f'{ds}.job.json',job)
    assert code==0 and stop is None,ds
    print(ds,'COMPLETE',job['seconds'],flush=True)
for pp,v in big_inputs.items():
    st=Path(pp).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns'],pp
dump(R/'reviews/jobs_complete.json',{'status':'PASS','seconds':time.perf_counter()-start,'jobs':jobs,'single_thread_CPU15_serial':True,'large_inputs_stat_unchanged':True,'QPS_measured':False});print('ALL_COMPLETE',flush=True)
