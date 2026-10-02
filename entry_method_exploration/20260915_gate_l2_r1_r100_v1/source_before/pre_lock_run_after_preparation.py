"""Continue the authorized run through test evaluation and plotting."""
from common import *
from pipeline import stage, PY
import subprocess

while not (RUN/'preparation.complete.json').exists():
    s=json.loads((RUN/'state.json').read_text())
    if s['status']=='FAILED':raise RuntimeError('Preparation failed; inspect preserved stage log before resuming')
    time.sleep(5)
stage('freeze_models',[PY,RUN/'src/freeze_models.py'])
dump(RUN/'state.json',dict(status='FROZEN_BEFORE_TEST',unix=time.time()))
# Let the lightweight offline-only resource observer exit before query timing.
time.sleep(6)
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
t=time.time()
subprocess.run([str(PY),str(RUN/'src/pipeline.py'),'formal'],check=True,env=env)
dump(RUN/'reviews/driver_formal.json',dict(status='PASS',seconds=time.time()-t,accounting='inclusive wrapper; use individual stage costs, do not add this again'))
stage('analysis',[PY,RUN/'src/analyze.py'])
dump(RUN/'state.json',dict(status='PLOTS_READY_PENDING_VISUAL_CHECK',unix=time.time()))
print('PLOTS_READY_PENDING_VISUAL_CHECK',flush=True)
