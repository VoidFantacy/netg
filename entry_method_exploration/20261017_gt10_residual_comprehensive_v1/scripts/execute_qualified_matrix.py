#!/usr/bin/env python3
"""After verified offline completion, qualify and run the frozen matrix once."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    receipt=ROOT/'reviews/qualified_matrix_pipeline.json'
    launch=ROOT/'reviews/qualified_matrix_pipeline.launch.json'
    assert not receipt.exists() and not launch.exists(),'Preserve existing pipeline attempt'
    offline=json.loads((ROOT/'reviews/offline_suite.execution.json').read_text())
    assert offline['status']=='PASS_SUITE_STAGE' and len(offline['datasets'])==7
    launch.write_text(json.dumps({'pid':os.getpid(),'started_unix':time.time(),'stages':['qualification','formal']},indent=2)+'\n')
    started=time.monotonic();stages=[]
    for name,args in [('qualification',[str(ROOT/'scripts/qualify_and_regress.py')]),
                      ('formal',[str(ROOT/'scripts/run_suite.py'),'--stage','formal'])]:
        log=ROOT/'logs'/f'{name}_pipeline.log';assert not log.exists()
        stage_start=time.monotonic();argv=[sys.executable,*args]
        with log.open('x') as f:
            child=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps({'event':'pipeline_stage_launch','stage':name,'pid':child.pid,'log':str(log)}),flush=True)
            try:code=child.wait()
            except BaseException:
                if child.poll() is None:os.killpg(child.pid,signal.SIGTERM);child.wait()
                raise
        stages.append({'stage':name,'argv':argv,'exit_code':code,'elapsed_seconds':time.monotonic()-stage_start,'log':str(log)})
        if code:
            receipt.write_text(json.dumps({'status':'FAIL_PIPELINE_PRESERVE_ATTEMPT','stages':stages,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')
            raise RuntimeError('Pipeline stopped after failed '+name+'; inspect preserved log')
    receipt.write_text(json.dumps({'status':'PASS_QUALIFIED_FORMAL_MATRIX_ANALYSIS_PENDING','stages':stages,'elapsed_seconds':time.monotonic()-started},indent=2)+'\n')


if __name__=='__main__':main()
