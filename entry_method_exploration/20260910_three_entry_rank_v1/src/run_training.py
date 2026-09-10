#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from common import DATASETS, RUN, dump, read, sha

assert read(RUN/'reviews/labels_verified.json')['status']=='PASS'
cfg=read(RUN/'config.locked.json');assert cfg['protocol_sha256']==sha(RUN/'protocol.md')
env={**os.environ,'OMP_NUM_THREADS':'16','OPENBLAS_NUM_THREADS':'16','MKL_NUM_THREADS':'16'}
jobs=[]
for dataset in DATASETS:
    command=[sys.executable,str(RUN/'src/train.py'),'--dataset',dataset]
    started=time.monotonic()
    with (RUN/'logs'/f'train_{dataset}.log').open('w') as log:
        proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(RUN/'state.json',{'status':'TRAINING_RUNNING','dataset':dataset,'pid':proc.pid,
            'controller_pid':os.getpid(),'argv':command,'started_unix':time.time(),'completed_jobs':jobs,
            'protocol_sha256':cfg['protocol_sha256']})
        code=proc.wait()
    jobs.append({'dataset':dataset,'argv':command,'exit_code':code,'process_seconds':time.monotonic()-started})
    dump(RUN/'models/jobs.json',jobs)
    assert code==0,f'training failed: {dataset}'
    assert read(RUN/'models'/dataset/'complete.json')['status']=='ALL_CANDIDATES_TRAINED_BEFORE_CAL'
    print(dataset,'TRAINED',flush=True)
dump(RUN/'state.json',{'status':'ALL_MODELS_TRAINED_CAL_PENDING','jobs':jobs,'protocol_sha256':cfg['protocol_sha256']})
