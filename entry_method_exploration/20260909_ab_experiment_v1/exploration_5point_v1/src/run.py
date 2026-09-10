#!/usr/bin/env python3
import json,os,signal,subprocess,time,shutil,hashlib
from pathlib import Path
from datetime import datetime,timezone
RUN=Path(__file__).resolve().parents[1];OUT=RUN.parent;PY=OUT.parents[1]/'.venv_cpu/bin/python'
state={};child=None
def save():
    state['updated_utc']=datetime.now(timezone.utc).isoformat();tmp=RUN/'state.tmp';tmp.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n');tmp.replace(RUN/'state.json')
def stop(sig,frame):
    if child and child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
    raise RuntimeError('interrupted '+str(sig))
def command(name,args):
    global child
    env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','BLIS_NUM_THREADS':'1','OMP_DYNAMIC':'FALSE','MPLCONFIGDIR':str(RUN/'logs/mpl_cache')}
    log=RUN/'logs'/f'{name}.log'
    with log.open('x') as f:
        child=subprocess.Popen([str(x) for x in args],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        state.update(active_stage=name,active_process=child.pid,active_log=str(log));save();started=time.monotonic()
        while child.poll() is None:
            time.sleep(5)
            memory=next(int(x.split()[1])*1024 for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))
            if shutil.disk_usage(RUN).free<10*1024**3 or memory<12*1024**3:
                os.killpg(child.pid,signal.SIGTERM);child.wait();raise RuntimeError('resource floor crossed')
        assert child.returncode==0, f'{name}: exit {child.returncode}; {log}'
        state['completed'].append({'stage':name,'seconds':time.monotonic()-started,'log':str(log)});state['active_process']=None;save()
def main():
    global state
    assert json.loads((RUN/'reviews/synthetic_acceptance.json').read_text())['status']=='PASS'
    prep=json.loads((RUN/'inputs/manifest.json').read_text());assert prep['status']=='PREPARED'
    state={'status':'EXPLORATION_RUNNING','controller_pid':os.getpid(),'threads':1,'completed':[],
           'L':[64,128,256,400,800],'queries_per_dataset':2000,'one_fixed_joint_router_per_dataset':True,
           'execution_sha256':{str(p.relative_to(RUN)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((RUN/'src').glob('*')),RUN/'bin/quick',RUN/'protocol.md'] if p.is_file()}}
    save()
    try:
        for config in prep['configs']:
            c=Path(config);command(c.parent.name,[RUN/'bin/quick',c,RUN/'results'/c.parent.name])
            assert json.loads((RUN/'results'/c.parent.name/'results.json').read_text())['status']=='COMPLETE'
        command('analyze',[PY,RUN/'src/analyze.py'])
        assert json.loads((RUN/'reviews/final_verification.json').read_text())['status']=='PASS'
        state.update(status='EXPLORATION_COMPLETE_REVIEW_PENDING',active_stage=None,active_process=None);save()
    except BaseException as error:
        if child and child.poll() is None:os.killpg(child.pid,signal.SIGTERM);child.wait()
        state.update(status='STOPPED_REQUIRES_INSPECTION',active_process=None,error=repr(error));save();raise
if __name__=='__main__':
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);main()
