from setup import *
import os
if __name__=='__main__':
 assert json.loads((O/'reviews/objective_tests.json').read_text())['status']=='PASS'
 lock=json.loads((O/'reviews/protocol_lock.json').read_text());assert sha(O/'protocol.md')==lock['protocol']['sha256']
 dump(O/'reviews/frozen_before_search.json',dict(timestamp=time.time(),sources=[identity(p) for p in sorted((O/'src').glob('*')) if p.is_file()],binaries=[identity(O/'bin'/n) for n in ['evaluate','propose','label']],protocol=identity(O/'protocol.md')))
 records=[]
 for ds in DS:
  assert shutil.disk_usage(O).free>10*(1<<30)
  for stage in ['propose','label']:
   dest=O/('inputs' if stage=='propose' else 'labels')/ds
   if stage=='propose':dest=dest/'proposals'
   argv=[str(O/'bin'/stage),str(O/'inputs'/ds/f'{stage}.json'),str(dest)]
   env=os.environ.copy();env.update(OMP_NUM_THREADS='16' if stage=='label' else '1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
   with (O/'logs'/f'{ds}.{stage}.log').open('w') as f:
    start=time.time();proc=subprocess.Popen(argv,stdout=f,stderr=subprocess.STDOUT,env=env);dump(O/'state.json',dict(status=stage.upper()+'_RUNNING',dataset=ds,pid=proc.pid,started=start,heldout_access=False));rc=proc.wait()
   rec=dict(dataset=ds,stage=stage,argv=argv,exit_code=rc,seconds=time.time()-start);records.append(rec);dump(O/'logs/label_jobs.json',records);print(rec,flush=True)
   assert rc==0,(ds,stage,'inspect preserved log/output')
 dump(O/'state.json',dict(status='LABELS_COMPLETE',heldout_access=False))
