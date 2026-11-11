from common import *
observed={};started=time.time()
while time.time()-started<7200 and not (R/'formal_complete.json').exists():
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
            if str(R/'storage/benchmark')+' formal ' not in cmd:continue
            status={a.split(':',1)[0]:a.split(':',1)[1].strip() for a in (proc/'status').read_text().splitlines() if ':' in a}
            pid=proc.name;v=observed.setdefault(pid,dict(pid=int(pid),command=cmd,samples=0,max_observed_VmHWM_kB=0,max_observed_threads=0,affinities=[]))
            v['samples']+=1;v['max_observed_VmHWM_kB']=max(v['max_observed_VmHWM_kB'],int(status['VmHWM'].split()[0]));v['max_observed_threads']=max(v['max_observed_threads'],int(status['Threads']))
            if status['Cpus_allowed_list'] not in v['affinities']:v['affinities'].append(status['Cpus_allowed_list'])
        except (OSError,KeyError,ValueError):pass
    dump(R/'reviews/live_process_observations.json',dict(scope='five-second proc observations, not guaranteed exact exit peak',processes=list(observed.values())))
    time.sleep(5)
print('MONITOR_FINISHED',len(observed),flush=True)
