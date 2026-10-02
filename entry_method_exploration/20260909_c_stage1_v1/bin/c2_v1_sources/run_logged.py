#!/usr/bin/env python3
"""Durable CPU-only single-child launcher; preserve argv, resource samples and failures."""
import datetime, json, os, subprocess, sys, time, signal
from pathlib import Path
V=Path(__file__).resolve().parents[1]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
label,*argv=sys.argv[1:]
assert argv and '/' not in label
path=V/'logs'/f'{label}.log'
assert not path.exists(),path
env=os.environ.copy()
limits={'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'}
env.update(limits)
record={'label':label,'argv':argv,'cwd':'/data/netg/ACSG','env_overrides':limits,'started_utc':now()}
with (V/'logs'/'commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
begin=time.monotonic(); peak=0; stop=None
with path.open('w') as log,(V/'logs'/f'{label}.resources.jsonl').open('w') as resource:
    p=subprocess.Popen(argv,cwd=record['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    record['pid']=p.pid
    while p.poll() is None:
        elapsed=time.monotonic()-begin
        try:
            status=Path(f'/proc/{p.pid}/status').read_text()
            rss=next(int(x.split()[1])*1024 for x in status.splitlines() if x.startswith('VmRSS:'))
            peak=max(peak,rss)
        except (OSError,StopIteration):rss=0
        resource.write(json.dumps({'utc':now(),'elapsed_seconds':elapsed,'rss_bytes':rss})+'\n');resource.flush()
        if elapsed>7200 or rss>32*1024**3:
            stop='wall' if elapsed>7200 else 'RSS';os.killpg(p.pid,signal.SIGTERM);break
        time.sleep(2)
    rc=p.wait()
record.update({'exit_code':rc,'finished_utc':now(),'wall_seconds':time.monotonic()-begin,'peak_rss_bytes':peak,'resource_stop':stop})
(V/'logs'/f'{label}.command.json').write_text(json.dumps(record,indent=2)+'\n')
with (V/'logs'/'commands.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
print(json.dumps(record),flush=True)
sys.exit(rc if not stop else 124)
