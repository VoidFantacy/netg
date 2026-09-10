#!/usr/bin/env python3
"""Sequential training, freeze and evaluation. Start only after labels finish."""
import hashlib,json,os,signal,subprocess,time,shutil
from datetime import datetime,timezone
from pathlib import Path
OUT=Path(__file__).resolve().parents[1];ROOT=OUT.parents[1];PY=ROOT/'.venv_cpu/bin/python'
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];SEEDS=[20260828,20260829,20260830]
state={};child=None
def save():
    state['updated_utc']=datetime.now(timezone.utc).isoformat();t=OUT/'state.next.tmp';t.write_text(json.dumps(state,indent=2)+'\n');t.replace(OUT/'state.json')
def available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    return 0
def command(name,cmd,threads=16):
    global child
    logfile=OUT/'logs'/f'{name}.log';assert not logfile.exists(),'refuse overwriting '+str(logfile)
    env={**os.environ,'OMP_NUM_THREADS':str(threads),'OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':str(threads)}
    with logfile.open('x') as log:
        child=subprocess.Popen([str(x) for x in cmd],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
        state.update(active_stage=name,active_process=child.pid,command=[str(x) for x in cmd],active_log=str(logfile));save()
        start=time.monotonic()
        while child.poll() is None:
            time.sleep(10)
            state['resource']={'disk_free_bytes':shutil.disk_usage(OUT).free,'mem_available_bytes':available()}
            state['active_stage_seconds']=time.monotonic()-start
            if state['resource']['disk_free_bytes']<10*1024**3 or state['resource']['mem_available_bytes']<12*1024**3:
                os.killpg(child.pid,signal.SIGTERM);child.wait();raise RuntimeError('resource floor crossed')
            save()
        assert child.returncode==0,f'{name} failed {child.returncode}: {logfile}'
    state['completed_stages'].append({'stage':name,'seconds':time.monotonic()-start,'log':str(logfile)})
    state['active_process']=None;save()
def stop(sig,frame):
    if child and child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
    raise RuntimeError('interrupted '+str(sig))
def main():
    global state
    state=json.loads((OUT/'state.json').read_text());assert state['status']=='LABELS_COMPLETE_TRAINING_PENDING'
    for name in ['benchmark_acceptance.json','benchmark_acceptance_v2.json','trainer_self_test.json','trainer_e2e/acceptance.json']:
        assert json.loads((OUT/'reviews'/name).read_text())['status']=='PASS'
    state.update(status='TRAINING_RUNNING',controller_pid=os.getpid(),completed_stages=[],failure_definition='Strict Recall@10<0.1 (hits==0), historical plot code and user clarification; local NETG PDF draft does not state threshold',
                 ann_search_calls=sum(x['calls']+x['parity_calls'] for x in state['completed_datasets']),model_fits=0)
    hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((OUT/'src').glob('*')),OUT/'bin/benchmark',OUT/'config.locked.json'] if p.is_file()}
    (OUT/'reviews/model_eval_execution_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n');save()
    try:
        command('verify_full_labels',[PY,OUT/'src/verify_labels.py'],threads=1)
        for ds in DATASETS:
            for seed in SEEDS:
                for L in [64,128]:
                    command(f'train_{ds}_{seed}_L{L}',[PY,OUT/'src/train.py','--dataset',ds,'--seed',seed,'--L',L])
                    state['model_fits']+=1;save()
        state['status']='MODELS_FROZEN_EVALUATION_RUNNING';save()
        for split in ['calibration_check','audit','validation','heldout']:
            command(f'prepare_{split}',[PY,OUT/'src/prepare_eval.py','--split',split],threads=1)
            prep=json.loads((OUT/'inputs/evaluation'/split/'complete.json').read_text())
            for config in prep['configs']:
                p=Path(config);ds=p.parent.name;seed=p.stem
                out=OUT/'results'/split/ds/seed
                command(f'eval_{split}_{ds}_{seed}',[OUT/'bin/benchmark',p,out])
                r=json.loads((out/'results.json').read_text());assert r['status']=='COMPLETE'
        state.update(status='EVALUATION_COMPLETE_ANALYSIS_PENDING',active_stage=None,active_process=None,
                     next='Analyze all measured query-paired metrics and rotated full-batch timings; write report and synchronize source/spec/summary/history');save()
    except BaseException as e:
        if child and child.poll() is None:os.killpg(child.pid,signal.SIGTERM);child.wait()
        state.update(status='MODELS_OR_EVAL_STOPPED_REQUIRES_INSPECTION',error=repr(e),active_process=None);save();raise
if __name__=='__main__':
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);main()
