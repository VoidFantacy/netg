import json, shutil, time
from pathlib import Path
R=Path(__file__).resolve().parent

def guard(c, start):
    assert time.time()<c['deadline_unix']
    assert time.time()-c['stage_started_unix']<c['seconds_cap']
    assert time.perf_counter()-start<c['per_build_seconds_cap']
    assert shutil.disk_usage(R).free>=c['min_free_bytes']

def ledger(kind):
    p=R/'reviews'/(kind+'_ledger.json')
    return p, json.loads(p.read_text()) if p.exists() else {'reserved':0,'completed':0,'reservations':[]}

def save(p, x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)

def reserve(c, kind, n, phase):
    assert isinstance(n,int) and n>0
    p,x=ledger(kind);assert x['reserved']==x['completed']
    assert x['reserved']+n<=c['max_'+kind+'_calls']
    x['reserved']+=n;x['reservations'].append({'phase':phase,'n':n,'unix':time.time()});save(p,x)

def commit(kind,n):
    p,x=ledger(kind);assert 0<n<=x['reserved']-x['completed'];x['completed']+=n;save(p,x)
