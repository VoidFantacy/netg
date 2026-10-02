from pathlib import Path
import json,os,time,signal,shutil
r=Path('/data/netg/ACSG/entry_method_exploration/20260920_entry_id_pilot_v1'); records={}; started=time.time(); root_pid=json.loads((r/'state.json').read_text())['runner_pid']; controller=Path('/proc')/str(root_pid); breaches=[]
while controller.exists():
 jobs=json.loads((r/'reviews/jobs.json').read_text())
 for j in jobs:
  if 'exit_code' in j:continue
  pid=j.get('pid');p=Path('/proc')/str(pid)
  if not pid or not p.exists():continue
  try:
   cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert str(r/'bin/experiment') in cmd
   s=dict((x.split(':',1)[0],x.split(':',1)[1].strip()) for x in (p/'status').read_text().splitlines() if ':' in x)
   if int(s['PPid'])!=root_pid:continue
   hwm=int(s['VmHWM'].split()[0]);free=shutil.disk_usage(r).free
   rec=records.setdefault(str(pid),{'pid':pid,'kind':j['kind'],'dataset':j['dataset'],'maxrss_kib':0,'observations':0})
   rec.update(maxrss_kib=max(rec['maxrss_kib'],hwm),observations=rec['observations']+1,threads=int(s['Threads']),cpu=s['Cpus_allowed_list'])
   if hwm>40*1024*1024 or free<6*1024**3 or s['Threads']!='1' or s['Cpus_allowed_list']!='15':
    breaches.append({'pid':pid,'status':s,'free':free});assert os.getpgid(pid)==j['pgid'];os.killpg(j['pgid'],signal.SIGTERM)
  except FileNotFoundError:pass
 tmp=r/'reviews/resource_observations.json.tmp';tmp.write_text(json.dumps({'started_unix':started,'updated_unix':time.time(),'records':records,'breaches':breaches,'controller_pid':root_pid},indent=2)+'\n');tmp.replace(r/'reviews/resource_observations.json')
 time.sleep(1)
