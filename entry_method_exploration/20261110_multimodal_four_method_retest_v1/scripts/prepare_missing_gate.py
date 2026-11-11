from pathlib import Path
import sys,os,json,time,subprocess,traceback
RUN=Path(__file__).resolve().parents[1];sys.path.insert(0,str(RUN/'src'))
from common import dump,sha,resource_check
env=dict(os.environ,OPENBLAS_NUM_THREADS='16',OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',NUMEXPR_NUM_THREADS='16',PYTHONHASHSEED='0')
receipts=[];started=time.time();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
try:
    for ds in ['coco','flickr30k']:
        for name,cmd in [('features',[sys.executable,str(RUN/'scripts/prepare_gate.py'),ds]),('labels',[str(RUN/'bin/labels'),str(RUN/'inputs'/ds),str(RUN/'inputs'/ds/'labels')]),('train',[sys.executable,str(RUN/'src/train_gate.py'),ds])]:
            resource_check();log=RUN/'logs'/f'{ds}_{name}.log';assert not log.exists(),'preserve previous stage attempt'
            t=time.time()
            with log.open('x') as f:
                p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
                dump(RUN/'state.json',{'status':'PREPARING_GATES','dataset':ds,'stage':name,'orchestrator_pid':os.getpid(),'child_pid':p.pid,'boot_id':boot,'started_unix':t,'log':str(log),'formal_completed':0})
                print('START',ds,name,p.pid,flush=True);code=p.wait()
            rec={'dataset':ds,'stage':name,'command':cmd,'exit_code':code,'seconds':time.time()-t,'log':str(log)}
            receipts.append(rec);dump(RUN/'reviews/gate_preparation_costs.json',receipts)
            if code:raise RuntimeError(f'{ds} {name} failed: {log}')
            print('DONE',ds,name,rec['seconds'],flush=True)
    dump(RUN/'reviews/missing_gates_ready.json',{'status':'PASS','seconds':time.time()-started,'models':{ds:json.loads((RUN/'models'/ds/'gate_disjoint_labels_v1/complete.json').read_text()) for ds in ['coco','flickr30k']}})
    dump(RUN/'state.json',{'status':'GATE_ASSETS_READY','formal_completed':0,'formal_pending':640,'orchestrator_pid':os.getpid(),'boot_id':boot})
except BaseException as e:
    dump(RUN/'reviews/gate_preparation_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'seconds':time.time()-started})
    dump(RUN/'state.json',{'status':'PREPARATION_FAILED','error':repr(e),'formal_completed':0,'orchestrator_pid':os.getpid(),'boot_id':boot});raise
