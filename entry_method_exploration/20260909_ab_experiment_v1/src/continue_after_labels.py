#!/usr/bin/env python3
"""Observe the known label controller, then finish the authorized pipeline once."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parents[1];PY=OUT.parents[1]/'.venv_cpu/bin/python'
def save(j):
    j['updated_utc']=datetime.now(timezone.utc).isoformat();p=OUT/'pipeline_supervisor.tmp';p.write_text(json.dumps(j,indent=2)+'\n');p.replace(OUT/'pipeline_supervisor.json')
def start_ticks(pid):
    try:
        fields=Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()
        return None if fields[0]=='Z' else fields[19]
    except FileNotFoundError:return None
def main():
    ready=json.loads((OUT/'reviews/implementation_ready.json').read_text());assert ready['status']=='PASS'
    for rel,h in ready['execution_sha256'].items():assert hashlib.sha256((OUT/rel).read_bytes()).hexdigest()==h,rel
    s=json.loads((OUT/'state.json').read_text());assert s['status']=='LABELS_RUNNING'
    pid=s['controller_pid'];ticks=start_ticks(pid);assert ticks is not None,'label controller not alive at registration'
    j={'status':'WAITING_FOR_REGISTERED_LABEL_CONTROLLER','supervisor_pid':os.getpid(),'observed_controller_pid':pid,'observed_start_ticks':ticks}
    save(j)
    try:
        while start_ticks(pid)==ticks:
            time.sleep(10);s=json.loads((OUT/'state.json').read_text());j['observed_state']=s['status'];j['observed_active_process']=s.get('active_process');save(j)
        s=json.loads((OUT/'state.json').read_text());assert s['status']=='LABELS_COMPLETE_TRAINING_PENDING','label process stopped without complete state; no restart'
        # Code must still match the reviewed implementation at phase transition.
        for rel,h in ready['execution_sha256'].items():assert hashlib.sha256((OUT/rel).read_bytes()).hexdigest()==h,rel
        with (OUT/'logs/controller_models_eval.log').open('x') as log:
            p=subprocess.Popen([str(PY),str(OUT/'src/run_models_eval.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            j.update(status='MODEL_EVAL_CONTROLLER_RUNNING',active_process=p.pid);save(j)
            while p.poll() is None:time.sleep(10);save(j)
            assert p.returncode==0,'model/eval controller failed; inspect saved state'
        s=json.loads((OUT/'state.json').read_text());assert s['status']=='EVALUATION_COMPLETE_ANALYSIS_PENDING'
        with (OUT/'logs/analyze.log').open('x') as log:
            env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MPLCONFIGDIR':str(OUT/'logs/matplotlib_cache')}
            p=subprocess.Popen([str(PY),str(OUT/'src/analyze.py')],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            j.update(status='ANALYSIS_RUNNING',active_process=p.pid);save(j)
            while p.poll() is None:time.sleep(10);save(j)
            assert p.returncode==0,'analysis failed; inspect log'
        j.update(status='MEASUREMENTS_AND_ANALYSIS_COMPLETE_ROOT_REVIEW_PENDING',active_process=None);save(j)
    except BaseException as e:
        j.update(status='STOPPED_REQUIRES_INSPECTION',error=repr(e));save(j);raise
if __name__=='__main__':main()
