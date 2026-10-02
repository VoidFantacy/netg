from pathlib import Path
import sys,os,time,subprocess,shutil
O=Path(__file__).resolve().parents[1];C=O.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import read,dump,check,threads
threads();split=sys.argv[1];assert split in ['preflight','aux'];lock=read(O/'config.locked.json')
def guard():
 p=read(C/'session11_resource_protocol.json');used=sum(f.stat().st_size for q in p['stage_folders'] for f in Path(q).rglob('*') if f.is_file() and not f.is_symlink())
 assert used<p['output_cap_MiB']*2**20
 assert shutil.disk_usage('/data').free-(p['output_cap_MiB']*2**20-used)-8*2**20>6.45*2**30
guard();assert time.time()<lock['latest_aux_launch'];check(O/'reviews/prequery_freeze.json')
if split=='aux':assert read(O/'reviews/preflight.json')['status']=='PASS'
c=read(O/'inputs'/(split+'.json'));jobs=read(O/'logs/jobs.json');assert all(j['status']=='COMPLETE' for j in jobs) and not any(j['split']==split for j in jobs)
assert sum(j['reserved_NSG'] for j in jobs)+c['real_call_cap']<=lock['NSG_hard_cap']
out=O/'results'/split;assert not out.exists();j=dict(split=split,status='RUNNING',reserved_NSG=c['real_call_cap'],started_at=time.time(),peak_threads=0,peak_RSS_KiB=0);jobs.append(j);dump(O/'logs/jobs.json',jobs)
with (O/'logs'/(split+'.log')).open('x') as log:
 p=subprocess.Popen([str(C/'stage14_compact_modes_v1/bin/evaluate'),str(O/'inputs'/(split+'.json')),str(out)],stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:os.sched_setaffinity(0,{15}))
 j['pid']=p.pid;s=read(C/'state.json');s.update(status='E92_RUNNING',native_pids=[p.pid]);dump(C/'state.json',s)
 try:
  while p.poll() is None:
   try:
    st=dict(x.split(':',1) for x in Path(f'/proc/{p.pid}/status').read_text().splitlines() if ':' in x);j['peak_threads']=max(j['peak_threads'],int(st['Threads']));j['peak_RSS_KiB']=max(j['peak_RSS_KiB'],int(st.get('VmRSS','0 kB').split()[0]));j['affinity']=sorted(os.sched_getaffinity(p.pid));assert j['peak_threads']<=1 and j['affinity']==[15]
   except FileNotFoundError:pass
   guard();assert time.time()<lock['query_hard_stop'] and time.time()-j['started_at']<600 and j['peak_RSS_KiB']<32*2**20
   try:p.wait(timeout=1)
   except subprocess.TimeoutExpired:pass
  assert p.returncode==0 and j['peak_threads']==1
  result=read(out/'results.json');assert result['physical_graph_calls']==c['real_call_cap'];j.update(status='COMPLETE',actual_NSG=c['real_call_cap'],actual_HNSW=10*c['num_queries'],seconds=time.time()-j['started_at'],returncode=0,completed_at=time.time())
 except BaseException as ex:
  if p.poll() is None:p.kill();p.wait()
  j.update(status='FAILED_RESERVED_RETAINED',error=repr(ex),returncode=p.returncode);raise
 finally:
  dump(O/'logs/jobs.json',jobs);s=read(C/'state.json');s.update(status='E92_SAFE_BOUNDARY',native_pids=[]);dump(C/'state.json',s)
print(j,flush=True)
