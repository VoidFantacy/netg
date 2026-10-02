"""Budgeted single-process execution, failed reservations remain charged."""
import os,shutil,subprocess,time
from pathlib import Path
from common import ROOT,RUN,check_lock,read,dump,sha,identity,update_state

def planned_calls(c):
    n=c['num_queries'];r=c.get('timing_repeats',0)
    return sum(((2*r+1) if r else 2)*n+16+(2*n if m.get('component_wall',False) else 0) for m in c['methods'])
def folder_bytes(p):return sum(x.stat().st_size for x in Path(p).rglob('*') if x.is_file())
def run_job(name,config,output,synthetic=False,repair=False):
    lock=check_lock();ledger_path=RUN/'reviews'/('synthetic_jobs.json' if synthetic else 'search_jobs.json')
    ledger=read(ledger_path) if ledger_path.exists() else []
    assert not any(x['status']=='RUNNING' for x in ledger)
    assert not any(x['name']==name for x in ledger)
    calls=planned_calls(config);used=sum(x['reserved_calls'] for x in ledger)
    assert used+calls<=lock['synthetic_call_cap' if synthetic else 'total_real_call_cap']
    if not synthetic:
        used_kind=sum(x['reserved_calls'] for x in ledger if x.get('repair',False)==repair)
        assert used_kind+calls<=lock['repair_real_call_cap' if repair else 'normal_real_call_cap']
    assert folder_bytes(RUN)<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    for asset in read(RUN/'reviews/protected_before.json'):
        st=Path(asset['path']).stat()
        assert st.st_size==asset['bytes'] and st.st_mtime_ns==asset['mtime_ns'], 'protected upstream asset changed: '+asset['path']
    c={**config,'threads':1,'query_cpu':lock['query_cpu'],'real_call_cap':calls,'protocol_sha256':lock['protocol_sha256']}
    path=RUN/'configs'/f'{name}.json';assert not path.exists();dump(path,c)
    binary=RUN/'bin/evaluate';build=read(RUN/'bin/evaluate.build.json')
    assert sha(binary)==build['binary']['sha256']
    for src in build['sources']:assert sha(src['path'])==src['sha256'],src['path']
    argv=['taskset','-c',str(lock['query_cpu']),str(binary),str(path),str(output)]
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','MKL_DYNAMIC':'FALSE','NUMEXPR_NUM_THREADS':'1'}
    record={'name':name,'argv':argv,'reserved_calls':calls,'synthetic':synthetic,'repair':repair,'status':'RUNNING',
            'start_unix':time.time(),'config':identity(path),'binary_sha256':sha(binary)}
    ledger.append(record);dump(ledger_path,ledger);max_rss=0;max_threads=0;reason=None;start=time.monotonic()
    with (RUN/'logs'/f'{name}.log').open('w') as log:
        proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
        record['pid']=proc.pid;dump(ledger_path,ledger);update_state(status='SEARCH_RUNNING',active_job=record)
        while proc.poll() is None:
            try:
                fields={k:v.strip() for k,v in (x.split(':',1) for x in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in x)}
                rss=int(fields.get('VmRSS','0 kB').split()[0])*1024;threads=int(fields.get('Threads','0'))
                max_rss=max(max_rss,rss);max_threads=max(max_threads,threads)
                if rss>lock['rss_limit_bytes']:reason='RSS_LIMIT'
                if threads>1:reason='THREAD_CONTRACT'
            except (FileNotFoundError,ProcessLookupError):pass
            elapsed=time.monotonic()-start
            if elapsed>lock['job_timeout_seconds']:reason='JOB_TIME_LIMIT'
            if sum(x.get('process_seconds',0) for x in ledger)+elapsed>lock['total_search_seconds']:reason='TOTAL_QUERY_TIME_LIMIT'
            if reason:
                proc.terminate()
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:proc.kill();proc.wait()
                break
            time.sleep(.2)
        rc=proc.wait()
    record.update(exit_code=rc,process_seconds=time.monotonic()-start,max_observed_rss_bytes=max_rss,
                  max_observed_process_threads=max_threads,stop_reason=reason,status='COMPLETE' if rc==0 else 'FAILED_RESERVED_CALLS_RETAINED')
    dump(ledger_path,ledger);update_state(active_job=None,status=record['status'],last_job=name)
    assert rc==0,f'{name} failed, reservation and output retained'
    r=read(Path(output)/'results.json');assert r['status']=='COMPLETE' and r['physical_graph_calls']==calls
    assert max_threads==1 and read(Path(output)/'thread_contract.json')['process_threads']==1
    record['actual_calls']=calls;record['results']=identity(Path(output)/'results.json');dump(ledger_path,ledger)
    assert folder_bytes(RUN)<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
    print(name,'COMPLETE',calls,'calls',round(record['process_seconds'],2),'s',flush=True)
    return r
