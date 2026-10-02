from common import *
import subprocess,sys,signal

def run(mode,split):
    assert mode in ('parity','labels') and split in ('fit','cal')
    frozen=read(RUN/'reviews/label_source_lock.json')
    for x in frozen['sources']+[frozen['binary'],frozen['protocol'],frozen['lock']]+frozen['libraries']:
        assert sha(x['path'])==x['sha256'],x['path']
    if mode=='labels':
        assert read(RUN/'reviews/parity_gate.json')['status']=='PASS'
    finite_deadline()
    jobs_path=RUN/'logs/label_jobs.json'
    jobs=read(jobs_path) if jobs_path.exists() else []
    results=[]
    for ds in DS:
        cfg=RUN/'inputs'/ds/split/'config.json';c=read(cfg)
        dest=RUN/('reviews' if mode=='parity' else 'labels')/ds/(split+'_'+mode)
        assert not dest.exists(),'Never overwrite/restart a job implicitly'
        reserve=len(c['parity_rows'])*2*7 if mode=='parity' else c['n']*56*2
        assert sum(x['charged_main_calls'] for x in jobs)+reserve<=LOCK['max_main_search_calls']
        log=RUN/'logs'/f'{ds}.{split}.{mode}.log'
        cmd=['taskset','-c','15',str(RUN/'bin/label'),mode,str(cfg),str(dest)]
        env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
        t=time.time();deadline=LOCK['created_unix']+LOCK['prepare_label_train_seconds'];assert deadline-t>60
        record=dict(dataset=ds,split=split,mode=mode,argv=cmd,output=str(dest),started=t,
                    status='RUNNING',charged_main_calls=reserve,log=str(log),runner=identity(Path(__file__)))
        jobs.append(record);dump(jobs_path,jobs)
        with log.open('x') as f:
            p=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            record['pid']=p.pid;dump(jobs_path,jobs)
            dump(RUN/'state.json',dict(status=mode.upper()+'_RUNNING',dataset=ds,split=split,pid=p.pid,
                 started=t,main_search_calls_charged=sum(x['charged_main_calls'] for x in jobs),heldout_access=False))
            try:rc=p.wait(timeout=max(1,deadline-time.time()))
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                rc=124
        record.update(exit_code=rc,wall_seconds=time.time()-t,status='FINISHED' if rc==0 else 'FAILED');dump(jobs_path,jobs)
        assert rc==0,f'Failed; inspect preserved {log}'
        result=read(dest/'complete.json');assert result['main_search_calls']==reserve
        record.update(result_status=result['status'],actual_main_calls=result['main_search_calls'],router_calls=result['router_calls']);dump(jobs_path,jobs)
        results.append(result);print(json.dumps(result),flush=True)
    gate='PASS' if all(x['status']=='PASS' for x in results) else 'STOP_PARITY'
    dump(RUN/'reviews'/f'{mode}_gate.json',dict(status=gate,datasets=results)) if mode=='parity' else None
    dump(RUN/'state.json',dict(status='STOP_PARITY' if gate!='PASS' else mode.upper()+'_COMPLETE',split=split,
         main_search_calls=sum(x['charged_main_calls'] for x in jobs),router_calls=sum(x.get('router_calls',0) for x in jobs),heldout_access=False))
    assert gate=='PASS','Frozen parity stop gate reached; no labels or training'

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
