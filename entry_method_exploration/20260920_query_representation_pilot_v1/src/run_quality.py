from common import *
import subprocess,signal

def run():
    frozen=read(RUN/'reviews/models_frozen.json');assert frozen['status']=='FROZEN'
    for x in frozen['all_files']+[frozen['source']]:assert sha(x['path'])==x['sha256'],x['path']
    impl=read(RUN/'reviews/quality_source_lock.json')
    for x in impl['sources']+[impl['binary']]:assert sha(x['path'])==x['sha256'],x['path']
    charged=sum(x['charged_main_calls'] for x in read(RUN/'logs/label_jobs.json'))
    jobs=[]
    for ds in DS:
        c=read(RUN/'inputs'/ds/'fit/config.json')
        c['splits']=[dict(name=s,n=LOCK[s+'_n'],queries=str(RUN/'inputs'/ds/s/'queries.f32')) for s in ['fit','cal']]
        c['models']=[dict(family='Identity',rank=16,W=c['routers'][0]['W'])]
        for family in ['QLinear','QMLP','WFree']:c['models'].append(read(RUN/'models'/ds/family/'model.json'))
        cfg=RUN/'inputs'/ds/'quality.json';assert not cfg.exists();dump(cfg,c)
        reserve=2560*4*2*2;assert charged+reserve<=LOCK['max_main_search_calls'];charged+=reserve
        out=RUN/'results'/ds/'quality';assert not out.exists()
        cmd=['taskset','-c','15',str(RUN/'bin/quality'),str(cfg),str(out)]
        log=RUN/'logs'/f'{ds}.quality.log';t=time.time()
        job=dict(dataset=ds,argv=cmd,config=identity(cfg),reserve_main_calls=reserve,started=t,status='RUNNING',
                 runner=identity(Path(__file__)));jobs.append(job);dump(RUN/'logs/quality_jobs.json',jobs)
        with log.open('x') as f:
            p=subprocess.Popen(cmd,cwd=ROOT,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            job['pid']=p.pid;dump(RUN/'logs/quality_jobs.json',jobs)
            dump(RUN/'state.json',dict(status='QUALITY_RUNNING',dataset=ds,pid=p.pid,training_runs=6,
                                      charged_main_calls=charged,heldout_access=False))
            try:rc=p.wait(timeout=max(1,LOCK['created_unix']+7200-time.time()))
            except subprocess.TimeoutExpired:
                os.killpg(p.pid,signal.SIGTERM)
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
                rc=124
        job.update(exit_code=rc,wall_seconds=time.time()-t,status='FINISHED' if rc==0 else 'FAILED');dump(RUN/'logs/quality_jobs.json',jobs)
        assert rc==0,f'inspect preserved {log}'
        result=read(out/'complete.json');assert result['status']=='PASS' and result['main_search_calls']==reserve
        job['result']=result;dump(RUN/'logs/quality_jobs.json',jobs);print(json.dumps(result),flush=True)
    for x in frozen['all_files']:assert sha(x['path'])==x['sha256'],'frozen model changed'
    dump(RUN/'state.json',dict(status='QUALITY_SEARCH_COMPLETE',training_runs=6,main_search_calls=charged,heldout_access=False))

if __name__=='__main__':run()
