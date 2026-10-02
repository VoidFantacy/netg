from common import *
import subprocess
threads();resources();ds,split=sys.argv[1:];assert ds in DS and split in ['preflight','aux'];limit=read(O/'config.locked.json');assert time.time()<limit['latest_aux_launch'];check(O/'reviews/prequery_freeze.json')
if split=='aux':assert read(O/'reviews'/('preflight_'+ds+'.json'))['status']=='PASS'
cpath=O/'inputs'/ds/(split+'.json');c=read(cpath);jp=O/'logs/jobs.json';jobs=read(jp)
assert all(j['status']=='COMPLETE' for j in jobs) and not any(j['dataset']==ds and j['split']==split for j in jobs)
assert sum(j['reserved_NSG'] for j in jobs)+c['real_call_cap']<=limit['NSG_hard_cap']
out=O/'results'/ds/split;assert not out.exists();t=time.time();job=dict(dataset=ds,split=split,status='RUNNING',reserved_NSG=c['real_call_cap'],started_at=t,peak_threads=0,peak_RSS_KiB=0);jobs.append(job);dump(jp,jobs)
with (O/'logs'/(ds+'_'+split+'.native.log')).open('x') as log:
 proc=subprocess.Popen([str(E73/'bin/evaluate'),str(cpath),str(out)],stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),preexec_fn=lambda:os.sched_setaffinity(0,{15}));job['pid']=proc.pid
 state=read(C/'state.json');state.update(status='E90_NATIVE_RUNNING',native_pids=[proc.pid],dataset=ds,stage='E90_'+split);dump(C/'state.json',state)
 try:
  while proc.poll() is None:
   try:
    st=dict(line.split(':',1) for line in Path(f'/proc/{proc.pid}/status').read_text().splitlines() if ':' in line)
    job['peak_threads']=max(job['peak_threads'],int(st['Threads']));job['peak_RSS_KiB']=max(job['peak_RSS_KiB'],int(st.get('VmRSS','0 kB').split()[0]));job['affinity']=sorted(os.sched_getaffinity(proc.pid));assert job['affinity']==[15] and job['peak_threads']<=1
   except FileNotFoundError:pass
   resources();assert time.time()<limit['query_hard_stop'] and time.time()-t<600 and job['peak_RSS_KiB']<32*(1<<20)
   dump(O/'logs/active.json',job)
   try:proc.wait(timeout=2)
   except subprocess.TimeoutExpired:pass
  assert proc.returncode==0,'native failure '+str(log.name)
  result=read(out/'results.json');assert result['physical_graph_calls']==c['real_call_cap'];assert not list(out.glob('*.hnsw'))
  job.update(status='COMPLETE',actual_NSG=result['physical_graph_calls'],seconds=time.time()-t,completed_at=time.time(),returncode=0)
 except BaseException as ex:
  if proc.poll() is None:proc.kill();proc.wait()
  job.update(status='FAILED_RESERVED_RETAINED',error=repr(ex),returncode=proc.returncode,seconds=time.time()-t);raise
 finally:
  dump(jp,jobs);state=read(C/'state.json');state.update(status='E90_NATIVE_SAFE_BOUNDARY',native_pids=[],last_native_status=job['status']);dump(C/'state.json',state)
print('E90_COMPLETE',ds,split,json.dumps(job),flush=True)
