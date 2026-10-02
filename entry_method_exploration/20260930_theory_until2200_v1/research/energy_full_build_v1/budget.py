import json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent
def guard(c,start):
    assert time.time()<c['deadline_unix'] and time.perf_counter()-start<c['seconds_cap']
    assert shutil.disk_usage(R).free>=c['min_free_bytes']
def reserve_gt(c,n,phase):
    p=R/'reviews/gt_ledger.json';x=json.loads(p.read_text()) if p.exists() else {'reserved':0,'completed':0,'batches':[]}
    assert x['reserved']==x['completed'] and x['reserved']+n<=c['max_exact_queries']
    x['reserved']+=n;x['batches'].append({'n':n,'phase':phase,'unix':time.time()});p.write_text(json.dumps(x,indent=2)+'\n')
def commit_gt(n):
    p=R/'reviews/gt_ledger.json';x=json.loads(p.read_text());x['completed']+=n;assert x['reserved']==x['completed'];p.write_text(json.dumps(x,indent=2)+'\n')
