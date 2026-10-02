from common import *
import subprocess
ds=sys.argv[1];assert ds in DS;threads();resources();check(O/'reviews/prequery_freeze.json');assert time.time()<1789270800
cpath=O/'inputs'/ds/'config.json';c=read(cpath);jp=O/'logs/jobs.json';jobs=read(jp) if jp.exists() else []
assert not any((j['dataset']==ds and j['status']=='COMPLETE') or j['status']=='RUNNING' for j in jobs);assert sum(j['reserved_NSG'] for j in jobs)+c['real_call_cap']<=800000

out=O/'results'/ds;assert not out.exists();t=time.time();job=dict(dataset=ds,status='RUNNING',reserved_NSG=c['real_call_cap'],started_at=t,peak_threads=0,peak_RSS_KiB=0);jobs.append(job);dump(jp,jobs)
with (O/'logs'/('native_v2_'+ds+'.log')).open('x') as log:
    proc=subprocess.Popen([str(O/'bin/evaluate'),str(cpath),str(out)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),preexec_fn=lambda:os.sched_setaffinity(0,{15}));job['pid']=proc.pid
    state=read(C/'state.json');state.update(status='E67_NATIVE_RUNNING',native_pids=[proc.pid],dataset=ds);dump(C/'state.json',state)
    try:
        while proc.poll() is None:
            try:
                st=dict(line.split(':',1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line)
                job['peak_threads']=max(job['peak_threads'],int(st['Threads']));job['peak_RSS_KiB']=max(job['peak_RSS_KiB'],int(st.get('VmRSS','0 kB').split()[0]))
                job['affinity']=sorted(os.sched_getaffinity(proc.pid));assert job['affinity']==[15] and job['peak_threads']<=1
            except FileNotFoundError:pass
            resources();assert time.time()<1789272000 and time.time()-t<900 and job['peak_RSS_KiB']<32*(1<<20)
            dump(O/'logs/active.json',job)
            try:proc.wait(timeout=2)
            except subprocess.TimeoutExpired:pass
        assert proc.returncode==0,'native log '+str(log.name)
        result=read(out/'results.json');assert result['physical_graph_calls']==c['real_call_cap']
        job.update(status='COMPLETE',actual_NSG=result['physical_graph_calls'],seconds=time.time()-t,completed_at=time.time(),returncode=proc.returncode)
    except BaseException as exc:
        if proc.poll() is None:proc.kill();proc.wait()
        job.update(status='FAILED_RESERVED_RETAINED',error=repr(exc),returncode=proc.returncode,seconds=time.time()-t);raise
    finally:
        dump(jp,jobs);state=read(C/'state.json');state.update(status='E67_NATIVE_SAFE_BOUNDARY',native_pids=[],last_native_status=job['status']);dump(C/'state.json',state)
print('E67_DATASET_COMPLETE',ds,json.dumps(job),flush=True)
