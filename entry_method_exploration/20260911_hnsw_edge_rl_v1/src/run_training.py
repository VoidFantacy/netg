from common import *
assert read(O/'reviews/router_preflight_v2.json')['status']=='PASS'
assert not (O/'logs/training_process.json').exists()
cmd=['taskset','-c','8',str(R/'.venv_cpu/bin/python'),str(O/'src/train_v2.py')]
started=time.time();record=dict(argv=cmd,start=started,status='RUNNING',rss_peak_kib=0,process_threads_max=0)
with (O/'logs/training.log').open('x') as f:
 p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env());record['pid']=p.pid;dump(O/'logs/training_process.json',record)
 try:
  while p.poll() is None:
   assert time.time()-started<3600,'training controller wall cap';resources()
   s=Path('/proc')/str(p.pid)/'status'
   if s.exists():
    for line in s.read_text().splitlines():
     if line.startswith('VmRSS:'):record['rss_peak_kib']=max(record['rss_peak_kib'],int(line.split()[1]));assert record['rss_peak_kib']<40*(1<<20)
     if line.startswith('Threads:'):record['process_threads_max']=max(record['process_threads_max'],int(line.split()[1]))
   time.sleep(1)
  assert p.returncode==0,'training exited; see training.log'
 except BaseException:
  if p.poll() is None:p.terminate();p.wait(timeout=5)
  record.update(status='FAILED',exit_code=p.returncode,seconds=time.time()-started);dump(O/'logs/training_process.json',record)
  if (O/'logs/jobs.json').exists():
   jobs=read(O/'logs/jobs.json')
   for j in jobs:
    if j['status']=='RUNNING':j.update(status='FAILED',actual_calls=None,reason='subprocess did not complete; entire reservation remains charged')
   dump(O/'logs/jobs.json',jobs)
  raise
record.update(status='COMPLETE',exit_code=p.returncode,seconds=time.time()-started);dump(O/'logs/training_process.json',record)
print('TRAINING_PROCESS_COMPLETE',record,flush=True)
