#!/usr/bin/env python3
"""Durable, sequential CPU label controller. Existing outputs are never replaced."""
import hashlib,json,os,signal,subprocess,time,shutil
from datetime import datetime,timezone
from pathlib import Path

OUT=Path(__file__).resolve().parents[1]
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
child=None
def now():return datetime.now(timezone.utc).isoformat()
def save(state):
    state['updated_utc']=now();p=OUT/'state.tmp';p.write_text(json.dumps(state,indent=2)+'\n');p.replace(OUT/'state.json')
def mem_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
    raise RuntimeError('missing MemAvailable')
def stop(signum,frame):
    if child is not None and child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
    raise RuntimeError('controller interrupted by signal '+str(signum))
def main():
    global child
    state=json.loads((OUT/'state.json').read_text())
    state.update(status='LABELS_RUNNING',controller_pid=os.getpid(),controller_started_utc=now(),completed_datasets=[])
    for label in ['webvid','yandex']:
        assert json.loads((OUT/f'reviews/parity_{label}/parity.json').read_text())['status']=='PASS'
    assert json.loads((OUT/'reviews/synthetic_parity.json').read_text())['status']=='PASS'
    locked=json.loads((OUT/'config.locked.json').read_text())
    assert hashlib.sha256((OUT/'protocol.md').read_bytes()).hexdigest()==locked['protocol_sha256']
    hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUT/'bin/labels',*sorted((OUT/'src').glob('*'))] if p.is_file()}
    (OUT/'reviews/label_execution_hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
    try:
        for ds in DATASETS:
            assert shutil.disk_usage(OUT).free>10*1024**3 and mem_available()>12*1024**3,'resource floor'
            cmd=[str(OUT/'bin/labels'),str(OUT/'inputs'/ds/'runner_config.json'),str(OUT/'labels'/ds)]
            assert not (OUT/'labels'/ds).exists(),'output already exists; inspect before any manual resume'
            log=OUT/'logs'/f'labels_{ds}.log'
            env={**os.environ,'OMP_NUM_THREADS':'16','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
            with log.open('x') as f:
                child=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
                state.update(active_dataset=ds,active_process=child.pid,command=cmd,active_log=str(log));save(state)
                while child.poll() is None:
                    time.sleep(10)
                    state['resource']={'disk_free_bytes':shutil.disk_usage(OUT).free,'mem_available_bytes':mem_available()}
                    if state['resource']['disk_free_bytes']<10*1024**3 or state['resource']['mem_available_bytes']<12*1024**3:
                        os.killpg(child.pid,signal.SIGTERM);child.wait();raise RuntimeError('resource floor crossed')
                    prog=OUT/'labels'/ds/'progress.json'
                    if prog.exists():
                        try:state['label_progress']=json.loads(prog.read_text())
                        except json.JSONDecodeError:pass
                    save(state)
                assert child.returncode==0,f'child exited {child.returncode}; see {log}'
            done=json.loads((OUT/'labels'/ds/'complete.json').read_text());assert done['status']=='COMPLETE'
            state['completed_datasets'].append({'dataset':ds,**done});state['active_process']=None;save(state)
        state.update(status='LABELS_COMPLETE_TRAINING_PENDING',active_dataset=None,next='Verify full labels; train locked low-rank models and controls; freeze before validation/held-out');save(state)
    except BaseException as e:
        if child is not None and child.poll() is None:os.killpg(child.pid,signal.SIGTERM);child.wait()
        state.update(status='LABELS_STOPPED_REQUIRES_INSPECTION',error=repr(e),active_process=None);save(state);raise

if __name__=='__main__':
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);main()
