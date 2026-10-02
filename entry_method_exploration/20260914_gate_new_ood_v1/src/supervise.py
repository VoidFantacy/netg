"""Serial E96 offline stages and single-thread formal comparison; restart-aware markers."""
from common import *
import subprocess, sys, signal, fcntl

def run_stage(key,args,done,formal=False):
    if Path(done).exists():
        print('reuse completed',key,flush=True);return
    resource_check();env=os.environ.copy();env.update(OMP_NUM_THREADS='1' if formal else '16',OPENBLAS_NUM_THREADS='16' if key.startswith(('features_','profiles_')) and not formal else '1',MKL_NUM_THREADS='1' if formal else '16',PYTHONHASHSEED='0')
    cmd=(['taskset','-c','15'] if formal else [])+list(map(str,args));t=time.time();log=RUN/'logs'/(key+'.log')
    # Attempts and errors remain inspectable; a failed stage never becomes complete.
    if log.exists():log=log.with_name(log.stem+f'.attempt{int(t)}.log')
    state=json.loads((RUN/'state.json').read_text());state.update(status='RUNNING',active_stage=key,stage_started_unix=t,supervisor_pid=os.getpid(),command=cmd,log=str(log));dump(RUN/'state.json',state)
    print('START',key,flush=True)
    with log.open('w') as f:
        child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT);state['child_pid']=child.pid;dump(RUN/'state.json',state);rc=child.wait()
    rec=dict(stage=key,command=cmd,exit_code=rc,seconds=time.time()-t,log=str(log));dump(RUN/'reviews'/('stage_'+key+'.json'),rec)
    assert rc==0 and Path(done).exists(),f'{key} failed; inspect {log}'
    state=json.loads((RUN/'state.json').read_text());state['completed_stages']=list(dict.fromkeys(state['completed_stages']+[key]));state.update(status='BETWEEN_STAGES',child_pid=None);dump(RUN/'state.json',state);print('DONE',key,rec['seconds'],flush=True)

def main():
    py=ROOT/'.venv_cpu/bin/python';src=RUN/'src'
    for ds in DATASETS:
        inp=RUN/'inputs'/ds;model=RUN/'models'/ds
        run_stage('features_'+ds,[py,src/'prepare.py','features',ds],inp/GATE_FEATURE_READY)
        run_stage('labels_'+ds,[RUN/'bin/labels',inp,inp/'labels'],inp/'labels/complete.json')
        run_stage('train_'+ds,[py,src/'train_gate.py',ds],model/GATE_MODEL/'complete.json')
        if ds.startswith('laion'):
            run_stage('profiles_'+ds,[py,src/'profiles.py','build',ds],model/'cal_config.json')
            run_stage('cal_'+ds,[RUN/'bin/evaluate',model/'cal_config.json',model/'cal_results'],model/'cal_results/complete.json',True)
            run_stage('selection_'+ds,[py,src/'profiles.py','select',ds],model/'gt10_selection.json')
    for ds in DATASETS:
        inp=RUN/'inputs'/ds;model=RUN/'models'/ds
        run_stage('hnsw_'+ds,[RUN/'bin/build_hnsw',inp,model/'hnsw'],model/'hnsw/complete.json')
    # All offline work ends before any public-test performance comparison.
    run_stage('preflight',[py,src/'verify.py','preflight'],RUN/'reviews/preflight.json')
    locked=json.loads((RUN/'config.locked.json').read_text())
    for i,ds in enumerate(DATASETS):
        inp=RUN/'inputs'/ds;model=RUN/'models'/ds;c=json.loads((inp/'manifest.json').read_text());paths=c['paths'];h=model/'hnsw'
        config=dict(formal=True,threads=1,dataset_order=i,n=10000,L=locked['L'],index=paths['index'],queries=paths['query_path'],base=paths['base_path'],hnsw_topology=str(h/'full.topology.gz'),hnsw_complete=str(h/'complete.json'),methods=[dict(name='NSG'),dict(name='GT10',W=str(inp/'gt10.W.f32'),ids=str(inp/'gt10.ids.i32')),dict(name='GATE',W=str(model/GATE_MODEL/'W.f32'),ids=str(inp/'gate.ids.i32')),dict(name='HNSW')])
        p=RUN/'inputs'/ds/'formal_config.json';dump(p,config)
        run_stage('formal_'+ds,[RUN/'bin/evaluate',p,RUN/'results'/ds],RUN/'results'/ds/'complete.json',True)
    run_stage('analysis',[py,src/'analyze.py'],RUN/'results/analysis_complete.json')
    state=json.loads((RUN/'state.json').read_text());state.update(status='READY_FOR_FINAL_AUDIT',active_stage=None);dump(RUN/'state.json',state)

if __name__=='__main__':
    # Reject duplicate supervisors before they can mutate state or launch a stage.
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
        try:cmd=(proc/'cmdline').read_bytes().split(b'\0')
        except (OSError,ProcessLookupError):continue
        if any(arg.endswith(b'20260914_gate_new_ood_v1/src/supervise.py') for arg in cmd[1:]):
            raise RuntimeError(f'existing E96 supervisor PID {proc.name}')
    lock=(RUN/'reviews/supervisor.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:main()
    except Exception as e:
        state=json.loads((RUN/'state.json').read_text());state.update(status='STAGE_FAILED',error=repr(e),failure_unix=time.time());dump(RUN/'state.json',state);raise
