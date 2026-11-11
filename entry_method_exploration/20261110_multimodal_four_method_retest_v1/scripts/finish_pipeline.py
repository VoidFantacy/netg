"""Observe the known preparation process, then continue the authorized task."""
from pathlib import Path
import os,sys,json,time,subprocess,traceback,argparse
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import dump
def alive(pid):
    p=Path(f'/proc/{pid}/stat')
    try:return p.read_text().split(') ',1)[1].split()[0]!='Z'
    except FileNotFoundError:return False
def main(pid):
    if alive(pid):assert b'prepare_missing_gate.py' in Path(f'/proc/{pid}/cmdline').read_bytes(),'PID no longer identifies expected preparation'
    dump(RUN/'pipeline.json',{'status':'WAITING_FOR_LIVE_PREPARATION','orchestrator_pid':os.getpid(),'preparation_pid':pid})
    while alive(pid):time.sleep(5)
    assert (RUN/'reviews/missing_gates_ready.json').exists(),'preparation ended without success; do not restart it'
    for stage in ['qualify','run_suite','analyze','audit']:
        log=RUN/'logs'/f'pipeline_{stage}.log';assert not log.exists(),'preserve earlier pipeline attempt'
        cmd=[sys.executable,'-u',str(RUN/'scripts'/f'{stage}.py')]
        with log.open('x') as f:
            t=time.time();p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1'))
            dump(RUN/'pipeline.json',{'status':'RUNNING','stage':stage,'orchestrator_pid':os.getpid(),'child_pid':p.pid,'started_unix':t,'log':str(log)})
            print('START_PIPELINE',stage,p.pid,flush=True);code=p.wait()
        dump(RUN/'reviews'/f'pipeline_{stage}_receipt.json',{'stage':stage,'exit_code':code,'seconds':time.time()-t,'command':cmd,'log':str(log)})
        assert code==0,(stage,log)
    dump(RUN/'pipeline.json',{'status':'NUMERICAL_WORK_COMPLETE_VISUAL_REPORT_REVIEW_PENDING','orchestrator_pid':os.getpid()})
    dump(RUN/'state.json',{'status':'AUDITED_VISUAL_REPORT_REVIEW_PENDING','formal_completed':640,'formal_batches':1280})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prep-pid',type=int,required=True);a=p.parse_args()
    try:main(a.prep_pid)
    except BaseException as e:
        f=RUN/'reviews'/f'pipeline_failure_{int(time.time())}.json';dump(f,{'error':repr(e),'traceback':traceback.format_exc()})
        dump(RUN/'pipeline.json',{'status':'FAILED_REVIEW_REQUIRED','error':repr(e),'failure':str(f),'orchestrator_pid':os.getpid()});raise
