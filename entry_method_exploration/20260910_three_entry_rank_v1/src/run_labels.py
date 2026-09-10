#!/usr/bin/env python3
import os
import subprocess
import time
from common import DATASETS, RUN, dump, read, sha

assert read(RUN/'reviews/synthetic_check.json')['status']=='PASS'
assert read(RUN/'reviews/trainer_self_test.json')['status']=='PASS'
cfg=read(RUN/'config.locked.json');assert cfg['protocol_sha256']==sha(RUN/'protocol.md')
env={**os.environ,'OMP_NUM_THREADS':'16','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
jobs=[]
for ds in DATASETS:
    started=time.monotonic()
    command=[str(RUN/'bin/label_triples'),str(RUN/'inputs'/ds/'fit/labels_config.json'),str(RUN/'labels'/ds)]
    dump(RUN/'state.json',{'status':'LABELS_RUNNING','dataset':ds,'controller_pid':os.getpid(),
                           'completed_jobs':jobs,'protocol_sha256':cfg['protocol_sha256']})
    with (RUN/'logs'/f'labels_{ds}.log').open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(RUN/'labels'/f'{ds}.process.json',{'pid':proc.pid,'controller_pid':os.getpid(),'argv':command,'started_unix':time.time()})
        code=proc.wait()
    job={'dataset':ds,'argv':command,'exit_code':code,'process_seconds':time.monotonic()-started}
    jobs.append(job);dump(RUN/'labels/jobs.json',jobs)
    assert code==0,f'label generation failed for {ds}'
    complete=read(RUN/'labels'/ds/'complete.json')
    assert complete['logical_calls']==480000
    assert complete['physical_calls']==read(RUN/'inputs'/ds/'prepared.json')['unique_ordered_triples']
    print(ds,'LABELS_COMPLETE',flush=True)
dump(RUN/'state.json',{'status':'LABELS_COMPLETE_TRAINING_PENDING','jobs':jobs,
                       'protocol_sha256':cfg['protocol_sha256']})
