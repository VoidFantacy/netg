#!/usr/bin/env python3
import os
import subprocess
import time
from common import DATASETS, RUN, dump, read, sha

assert read(RUN/'state.json')['status']=='VALIDATION_PREPARED_MODELS_FROZEN'
frozen=read(RUN/'models/frozen_before_validation.json')
for x in frozen['files']:assert sha(x['path'])==x['sha256'],x['path']
env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
jobs=[]
for dataset in DATASETS:
    config=RUN/'inputs'/dataset/'validation/config.json'
    command=[str(RUN/'bin/evaluate_v2'),str(config),str(RUN/'results'/dataset)]
    started=time.monotonic()
    with (RUN/'logs'/f'validation_{dataset}.log').open('w') as log:
        process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(RUN/'state.json',{'status':'VALIDATION_RUNNING','dataset':dataset,'pid':process.pid,
                              'argv':command,'started_unix':time.time(),'completed_jobs':jobs})
        code=process.wait()
    jobs.append({'dataset':dataset,'argv':command,'exit_code':code,'process_seconds':time.monotonic()-started})
    dump(RUN/'results/jobs.json',jobs)
    assert code==0,f'validation failed for {dataset}'
    assert read(RUN/'results'/dataset/'results.json')['status']=='COMPLETE'
    print(dataset,'VALIDATION_COMPLETE',flush=True)
dump(RUN/'state.json',{'status':'VALIDATION_COMPLETE_ANALYSIS_PENDING','jobs':jobs,'protocol_sha256':sha(RUN/'protocol.md')})
