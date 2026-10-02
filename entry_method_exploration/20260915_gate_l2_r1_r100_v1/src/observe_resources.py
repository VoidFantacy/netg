"""Low-frequency offline process observation; never run during formal timings."""
from common import *
import sys
records={}
while True:
    s=json.loads((RUN/'state.json').read_text())
    if s['status'] not in ['RUNNING_OFFLINE']:break
    key=s['stage'];pid=s['pid'];r=records.setdefault(key,dict(pid=pid,first_observed_unix=time.time(),rss_peak_bytes=0,vmhwm_peak_bytes=0,observed_process_threads_max=0,samples=0))
    try:
        fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path(f'/proc/{pid}/status').read_text().splitlines() if ':' in line}
        r['rss_peak_bytes']=max(r['rss_peak_bytes'],int(fields['VmRSS'].split()[0])*1024)
        r['vmhwm_peak_bytes']=max(r['vmhwm_peak_bytes'],int(fields['VmHWM'].split()[0])*1024)
        r['observed_process_threads_max']=max(r['observed_process_threads_max'],int(fields['Threads']));r['samples']+=1
        r['last_observed_unix']=time.time();r['disk_free_bytes']=__import__('shutil').disk_usage(RUN).free
        dump(RUN/'reviews/offline_resource_observations.json',records)
        assert r['vmhwm_peak_bytes']<=96*1024**3 and r['disk_free_bytes']>=2*1024**3
    except FileNotFoundError:pass
    time.sleep(5)
print('RESOURCE_OBSERVER_STOP',s['status'],flush=True)
