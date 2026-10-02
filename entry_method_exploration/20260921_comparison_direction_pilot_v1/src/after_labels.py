"""Wait for the live stage1 controller to finish, then run each dependent stage once."""
from common import *
import subprocess,fcntl

def live(pid,needle):
    p=Path(f'/proc/{pid}/cmdline')
    try:return p.exists() and needle.encode() in p.read_bytes()
    except FileNotFoundError:return False

def main():
    guard=(RUN/'reviews/continuation.lock').open('a+');fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
    first=read(RUN/'reviews/stage1_started.json');pid=first['pid']
    dump(RUN/'reviews/continuation_started.json',dict(pid=os.getpid(),unix=time.time(),waiting_for_stage1_pid=pid))
    while live(pid,str(RUN/'src/stage1.py')) or live(pid,'20260921_comparison_direction_pilot_v1/src/stage1.py'):
        dump(RUN/'reviews/continuation_progress.json',dict(status='WAITING_LIVE_STAGE1',unix=time.time(),stage1_pid=pid))
        time.sleep(15)
    assert (RUN/'reviews/stage1_complete.json').exists(),'stage1 ended without completion; diagnose before continuation'
    py=ROOT/'.venv_cpu/bin/python';records=[]
    for script in ('stage2.py','analyze.py','final_audit.py','report.py'):
        name=script.removesuffix('.py');log=RUN/'logs'/f'{name}_controller.log'
        assert not log.exists(),'inspect an earlier attempt before resuming'
        command=[str(py),'-u',str(RUN/'src'/script)]
        z=dict(stage=name,argv=command,started_unix=time.time());records.append(z);dump(RUN/'reviews/continuation_jobs.json',records)
        with log.open('x') as f:
            child=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,env=os.environ.copy());z['pid']=child.pid
            dump(RUN/'reviews/continuation_jobs.json',records);code=child.wait()
        z.update(exit_code=code,seconds=time.time()-z['started_unix']);dump(RUN/'reviews/continuation_jobs.json',records)
        assert code==0,(script,code,log.read_text()[-2000:])
    dump(RUN/'state.json',dict(status='RESULTS_AND_AUDITS_COMPLETE_REVIEW_PENDING',pending=['visual figure review','evidence interpretation and decision','root documentation and final completion audit'],active_processes=[]))
    dump(RUN/'reviews/continuation_complete.json',dict(status='PASS',unix=time.time(),records=records))

if __name__=='__main__':
    try:main()
    except BaseException as err:
        dump(RUN/'reviews/continuation_error.json',dict(status='EXECUTION_ERROR_REQUIRES_DIAGNOSIS',error=repr(err),unix=time.time(),method_conclusion=None));raise
