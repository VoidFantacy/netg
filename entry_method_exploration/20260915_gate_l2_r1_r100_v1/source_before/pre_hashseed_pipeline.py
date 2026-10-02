"""Serial, restartable stages with actual process/log provenance."""
from common import *
import subprocess, sys, fcntl, traceback

PY=ROOT/'.venv_cpu/bin/python';lock=json.loads((RUN/'config.locked.json').read_text())
offline=os.environ.copy();offline.update(OMP_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16',MKL_NUM_THREADS='16',NUMEXPR_NUM_THREADS='16',PYTHONUNBUFFERED='1')

def stage(name,cmd,formal=False):
    rec=RUN/'reviews'/('stage_'+name+'.json')
    if rec.exists():
        assert json.loads(rec.read_text())['status']=='PASS';return
    resource_check();attempt=time.strftime('%Y%m%d_%H%M%S');log=RUN/'logs'/(name+'_'+attempt+'.log');t=time.time()
    env=offline.copy()
    if formal:env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    with log.open('w') as f:
        p=subprocess.Popen(list(map(str,cmd)),stdout=f,stderr=subprocess.STDOUT,env=env)
        state=dict(status='RUNNING_FORMAL' if formal else 'RUNNING_OFFLINE',stage=name,pid=p.pid,supervisor_pid=os.getpid(),started_unix=t,log=str(log),command=list(map(str,cmd)),boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
        dump(RUN/'state.json',state);print('STAGE_START',json.dumps(state),flush=True)
        code=p.wait()
    result=state|dict(status='PASS' if code==0 else 'FAILED',exit_code=code,seconds=time.time()-t,finished_unix=time.time())
    dump(rec if code==0 else RUN/'reviews'/(name+'_failed_'+attempt+'.json'),result)
    if code:
        dump(RUN/'state.json',result);raise RuntimeError(f'{name} exited {code}: {log}')
    print('STAGE_PASS',name,result['seconds'],flush=True)

def prepare():
    assert json.loads((RUN/'reviews/changes_verified.json').read_text())['status']=='PASS'
    for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        stage('reuse_'+ds,[PY,RUN/'src/reuse_ip.py',ds])
        stage('train_'+ds,[PY,RUN/'src/train_gate.py',ds])
    for ds in ['gist1m_l2_v1','deep10m_l2_v1','sift10m_bigann_l2_v1']:
        inp=RUN/'inputs'/ds;model=RUN/'models'/ds
        stage('acquire_'+ds,[PY,RUN/'src/prepare_data.py','acquire',ds])
        for role in ['qgt','fit','gate_monitor','cal']:
            stage('gt_'+role+'_'+ds,[PY,RUN/'src/prepare_data.py','gt',ds,role])
        stage('nsg_'+ds,[RUN/'bin/build_nsg',inp/'manifest.json',model/'nsg'])
        stage('features_'+ds,[PY,RUN/'src/prepare.py','features',ds])
        stage('labels_'+ds,[RUN/'bin/labels',inp,inp/'labels'])
        stage('profiles_'+ds,[PY,RUN/'src/build_profiles.py',ds])
        stage('train_'+ds,[PY,RUN/'src/train_gate.py',ds])
        stage('hnsw_'+ds,[RUN/'bin/build_hnsw',inp,model/'hnsw'])
    dump(RUN/'preparation.complete.json',dict(status='PASS',unix=time.time(),datasets=lock['datasets']))
    dump(RUN/'state.json',dict(status='PREPARATION_COMPLETE',unix=time.time()))

def formal():
    assert json.loads((RUN/'reviews/frozen_models.json').read_text())['status']=='PASS'
    for ds in ['gist1m_l2_v1','deep10m_l2_v1','sift10m_bigann_l2_v1']:
        stage('gt_test_'+ds,[PY,RUN/'src/prepare_data.py','gt',ds,'test'])
    stage('preflight',[PY,RUN/'src/preflight.py'])
    # All offline work and test GT complete before the first formal query round.
    for ds in lock['datasets']:
        for k in lock['K']:
            stage(f'formal_{ds}_k{k}',['taskset','-c','15',RUN/'bin/evaluate',RUN/'inputs'/ds/f'eval_k{k}.json',RUN/'results'/ds/f'k{k}'],formal=True)
    dump(RUN/'state.json',dict(status='EVALUATION_COMPLETE',unix=time.time()))

if __name__=='__main__':
    with (RUN/'pipeline.lock').open('w') as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        globals()[sys.argv[1]]()
