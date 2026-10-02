"""Sequential, hard-capped supplement. Never launches training or parallel evaluators."""
import os
import shutil
import subprocess
import time
from common import *
from prepare_supplement import SUP,calls,ident

def size():return sum(p.stat().st_size for p in SUP.rglob('*') if p.is_file())

def verify_result(job):
    folder=Path(job['output']);r=read(folder/'results.json');c=read(folder/'config.json');n=c['num_queries']
    tc=read(folder/'thread_contract.json');assert tc['process_threads']==tc['actual_openmp_threads']==r['threads']==1
    assert tc['cpu']==15 and r['GT_opened_after_all_raw_search']
    gt=arr(c['gt_file'],'<i8',(n,100));rr=arr(c['row_ids'],'<i8');assert np.array_equal(rr,arr(folder/'row_ids.i64','<i8'))
    checks=[]
    for m in r['methods']:
        z=load_point(folder,m,n);mask=np.zeros(n,'<u2')
        for rank in range(10):mask|=((z['ids']==gt[:,rank,None]).any(1).astype('<u2')<<rank)
        hh=np.array([int(x).bit_count() for x in mask],dtype='u1')
        assert np.array_equal(mask,z['masks']) and np.array_equal(hh,z['hits'])
        assert np.isfinite(z['bits'].view('<f4')).all() and (np.diff(np.sort(z['ids'],1),axis=1)>0).all()
        assert (z['ids']>=0).all() and (z['ids']<c['base_count']).all()
        assert (np.diff(z['entries'],axis=1)>0).all()
        hubs=arr(m['configuration']['mapping'],'<i4');assert np.isin(z['entries'],hubs).all()
        assert hh.sum()==m['total_hits'] and abs(m['recall_at_10']-hh.mean()/10)<1e-12
        assert abs(z['r'].mean()-m['mean_route_ndc'])<1e-12 and abs(z['g'].mean()-m['mean_graph_ndc'])<1e-12
        if c['timing_repeats']:
            assert len(m['qps_runs'])==len(m['end_to_end_seconds'])==3
            assert np.allclose(m['qps_runs'],n/np.array(m['end_to_end_seconds']),rtol=0,atol=1e-9)
        else:assert m['qps'] is None and not m['qps_runs']
        if job['stage'] in ['recovery','repeat']:
            oldfolder=VERSIONS[24]/('diagnostics' if job['stage']=='recovery' else 'results')/c['dataset']
            if job['stage']=='recovery':oldfolder/='cal'
            old=read(oldfolder/'results.json')
            oldm=next(x for x in old['methods'] if x['family']==m['family'] and x['L']==m['L'] and x['configuration']['exact']==m['configuration']['exact'])
            oldz=load_point(oldfolder,oldm,old['queries'])
            for key in z:assert np.array_equal(z[key],oldz[key][:n]),(job['name'],m['name'],key)
        checks.append({'method':m['name'],'queries':n,'status':'PASS'})
    dump(SUP/'reviews'/f"{job['name']}_verified.json",{'status':'PASS','checks':checks,'independently_scored':sum(x['queries'] for x in checks)})

def main():
    lock=read(SUP/'config.locked.json')
    assert sha(SUP/'protocol.md')==lock['protocol_sha256']
    assert sha(RUN/'existing_report.md')==lock['existing_report_sha256']
    assert sha(SUP/'config.locked.json')==read(SUP/'reviews/protocol_lock.json')['sha256']
    frozen=read(SUP/'reviews/frozen_before_search.json')['files']
    for x in frozen:assert sha(x['path'])==x['sha256'],x['path']
    build=read(SUP/'bin/evaluate.build.json')
    dump(SUP/'reviews/controller_before_search.json',{'files':[ident(Path(__file__)),ident(RUN/'src/common.py'),ident(RUN/'src/prepare_supplement.py')]})
    plan=read(SUP/'reviews/plan.json');ledger_path=SUP/'reviews/search_jobs.json'
    assert not ledger_path.exists(),'refuse restarting ledger; failed reservations must remain charged'
    ledger=[];protected=read(SUP/'reviews/upstream.json')['files']
    for job in plan:
        if job['stage']!='recovery':
            for ds in DATASETS:assert read(SUP/'reviews'/f'recovery_{ds}_verified.json')['status']=='PASS'
        c=read(job['config']);reservation=calls(c);assert reservation==c['real_call_cap']==job['reserved_calls']
        assert sum(j['reserved_calls'] for j in ledger)+reservation<=lock['normal_real_call_cap']
        assert not Path(job['output']).exists()
        assert size()<lock['output_limit_bytes'] and shutil.disk_usage(ROOT).free>=lock['min_free_bytes']
        for x in protected:
            st=Path(x['path']).stat();assert st.st_size==x['bytes'] and st.st_mtime_ns==x['mtime_ns'],x['path']
        for x in build['sources']+[build['binary']]:assert sha(x['path'])==x['sha256']
        argv=['taskset','-c','15',str(SUP/'bin/evaluate'),job['config'],job['output']]
        env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1',
             'OMP_DYNAMIC':'FALSE','MKL_DYNAMIC':'FALSE'}
        rec={**job,'argv':argv,'status':'RUNNING','started_unix':time.time(),'binary_sha256':build['binary']['sha256'],
             'config_identity':ident(job['config'])};ledger.append(rec);dump(ledger_path,ledger)
        dump(RUN/'state.json',{'status':'SUPPLEMENT_RUNNING','active_job':job['name'],'reserved_calls':sum(x['reserved_calls'] for x in ledger)})
        started=time.monotonic();peak=0;threads=0;reason=None;last_disk=started
        with (SUP/'logs'/f"{job['name']}.log").open('w') as log:
            proc=subprocess.Popen(argv,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            rec['pid']=proc.pid;dump(ledger_path,ledger)
            while proc.poll() is None:
                try:
                    fields={k:v.strip() for k,v in (line.split(':',1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line)}
                    peak=max(peak,int(fields.get('VmRSS','0 kB').split()[0])*1024);threads=max(threads,int(fields.get('Threads','0')))
                except (FileNotFoundError,ProcessLookupError):pass
                elapsed=time.monotonic()-started
                if peak>lock['rss_limit_bytes']:reason='RSS_LIMIT'
                if threads>1:reason='THREAD_CONTRACT'
                if elapsed>lock['job_timeout_seconds']:reason='JOB_TIME_LIMIT'
                if sum(x.get('process_seconds',0) for x in ledger)+elapsed>lock['total_search_seconds']:reason='TOTAL_TIME_LIMIT'
                if time.monotonic()-last_disk>5:
                    if size()>lock['output_limit_bytes'] or shutil.disk_usage(ROOT).free<lock['min_free_bytes']:reason='DISK_LIMIT'
                    last_disk=time.monotonic()
                if reason:
                    proc.terminate()
                    try:proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
                    break
                time.sleep(.2)
            rc=proc.wait()
        rec.update(status='COMPLETE' if rc==0 else 'FAILED_RESERVATION_RETAINED',exit_code=rc,stop_reason=reason,
            process_seconds=time.monotonic()-started,max_observed_rss_bytes=peak,max_observed_process_threads=threads)
        dump(ledger_path,ledger)
        assert rc==0 and reason is None,job['name']
        result=read(Path(job['output'])/'results.json');assert result['physical_graph_calls']==reservation and threads==1
        rec['actual_calls']=reservation;rec['result_identity']=ident(Path(job['output'])/'results.json');dump(ledger_path,ledger)
        verify_result(job)
        print(job['name'],'COMPLETE',reservation,'calls',round(rec['process_seconds'],2),'seconds',flush=True)
    assert sum(x['actual_calls'] for x in ledger)==lock['normal_real_call_cap']
    dump(SUP/'reviews/execution_complete.json',{'status':'COMPLETE','real_calls':sum(x['actual_calls'] for x in ledger),
       'process_seconds':sum(x['process_seconds'] for x in ledger),'max_RSS_bytes':max(x['max_observed_rss_bytes'] for x in ledger),
       'jobs':len(ledger),'threads':1,'repair_calls':0,'synthetic_calls':0,'output_bytes':size()})
    dump(RUN/'state.json',{'status':'SUPPLEMENT_EXECUTION_COMPLETE_ANALYSIS_PENDING','real_search_calls':lock['normal_real_call_cap'],
                          'heldout_access':False})
    print('SUPPLEMENT_EXECUTION_COMPLETE',flush=True)

if __name__=='__main__':main()
