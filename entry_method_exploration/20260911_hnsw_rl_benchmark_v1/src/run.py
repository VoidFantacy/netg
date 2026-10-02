from common import *
assert read(O/'reviews/preflight.json')['status']=='PASS'
assert not (O/'logs/jobs.json').exists(),'refuse restarting frozen jobs'
jobs=[]
for ds in DS:
 check(O/'reviews/before_queries.json');check(O/'reviews/upstream.json',hashes=False);resources()
 cfg=O/'inputs'/ds/'config.json';c=read(cfg);dest=O/'results'/ds;assert not dest.exists()
 cap=c['real_call_cap'];assert sum(j['reserved_calls'] for j in jobs)+cap<=647104
 argv=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)]
 rec=dict(dataset=ds,reserved_calls=cap,actual_calls=None,status='RUNNING',argv=argv,start=time.time(),rss_peak_kib=0,process_threads_max=0)
 jobs.append(rec);dump(O/'logs/jobs.json',jobs)
 dump(O/'state.json',dict(status='EVALUATING',dataset=ds,optimizer_updates=0,heldout_access=False))
 with (O/'logs'/f'{ds}.log').open('x') as log:
  proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env());rec['pid']=proc.pid
  try:
   while proc.poll() is None:
    assert time.time()-rec['start']<1200 and time.time()-rec['start']+sum(j.get('seconds',0) for j in jobs)<2400
    resources();p=Path(f'/proc/{proc.pid}/status')
    if p.exists():
     for line in p.read_text().splitlines():
      if line.startswith('VmRSS:'):rec['rss_peak_kib']=max(rec['rss_peak_kib'],int(line.split()[1]));assert rec['rss_peak_kib']<40*(1<<20)
      if line.startswith('Threads:'):rec['process_threads_max']=max(rec['process_threads_max'],int(line.split()[1]));assert rec['process_threads_max']==1
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:pass
   assert proc.returncode==0,'see '+str(log.name)
  except BaseException:
   if proc.poll() is None:proc.kill();proc.wait()
   rec.update(status='FAILED',exit_code=proc.returncode,seconds=time.time()-rec['start']);dump(O/'logs/jobs.json',jobs);dump(O/'state.json',dict(status='FAILED',dataset=ds));raise
 r=read(dest/'results.json');assert r['physical_graph_calls']==cap and r['status']=='COMPLETE'
 rec.update(status='COMPLETE',actual_calls=cap,exit_code=0,seconds=time.time()-rec['start']);dump(O/'logs/jobs.json',jobs)
 print('EVALUATION_COMPLETE',ds,cap,flush=True)
dump(O/'state.json',dict(status='EVALUATION_COMPLETE_ANALYSIS_PENDING',points=45,wall_measurements=225,actual_NSG_calls=sum(j['actual_calls'] for j in jobs),optimizer_updates=0,heldout_access=False))
