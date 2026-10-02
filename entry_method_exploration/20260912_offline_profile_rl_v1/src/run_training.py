from common import *
assert read(O/'reviews/preflight.json')['status']=='PASS'
assert not (O/'reviews/before_training.json').exists(),'training launch is single use'
freeze(O/'reviews/before_training.json',[O/'protocol.md',O/'config.locked.json',O/'reviews/preflight.json',O/'bin/environment.so']+list((O/'src').glob('*.*'))+[p for p in (O/'inputs').rglob('*') if p.is_file()]+[O/'results'/ds/'baseline.npz' for ds in DS])
processes=[];all_start=time.time()
for ds in DS:
 c=read(O/'inputs'/ds/'config.json');resources();argv=['taskset','-c','15',str(R/'.venv_cpu/bin/python'),str(O/'src/train.py'),ds]
 rec=dict(dataset=ds,argv=argv,status='RUNNING',start=time.time(),peak_RSS_KiB=0,peak_threads=0)
 with (O/'logs'/f'training_{ds}.log').open('x') as log:
  proc=subprocess.Popen(argv,env=env(),stdout=log,stderr=subprocess.STDOUT);rec['pid']=proc.pid;processes.append(rec)
  try:
   while proc.poll() is None:
    assert time.time()-rec['start']<7200 and time.time()-all_start<14400,'training time cap'
    try:
     values=dict(s.split(':',1) for s in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in s)
     rec['peak_RSS_KiB']=max(rec['peak_RSS_KiB'],int(values.get('VmRSS','0 kB').split()[0]));rec['peak_threads']=max(rec['peak_threads'],int(values['Threads']))
    except FileNotFoundError:pass
    assert rec['peak_RSS_KiB']<32*(1<<20) and rec['peak_threads']<=1,'training resource cap'
    resources();dump(O/'logs/training_processes.json',processes)
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   assert proc.returncode==0,'see '+str(log.name)
  except BaseException:
   if proc.poll() is None:proc.kill();proc.wait()
   rec.update(status='FAILED',exit_code=proc.returncode,seconds=time.time()-rec['start']);dump(O/'logs/training_processes.json',processes);raise
 rec.update(status='COMPLETE',seconds=time.time()-rec['start'],exit_code=0);dump(O/'logs/training_processes.json',processes)
 assert read(O/'results'/ds/'training_complete.json')['status']=='PASS'
 print('DATASET_TRAINING_COMPLETE',ds,rec['seconds'],flush=True)
freeze(O/'reviews/models_after_training.json',[p for p in (O/'models').rglob('*') if p.is_file()])
dump(O/'state.json',dict(status='TRAINING_COMPLETE_VERIFICATION_PENDING',training_runs=8,optimizer_updates=1600,seconds=time.time()-all_start))
