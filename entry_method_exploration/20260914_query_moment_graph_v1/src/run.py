from common import *
import sys
phase=sys.argv[1];assert phase in ['preflight','aux']
check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected_before.json')
for x in read(O/'reviews/large_asset_stat.json'):
    s=Path(x['path']).stat();assert (s.st_size,s.st_mtime_ns)==(x['bytes'],x['mtime_ns'])
if phase=='aux':assert read(O/'reviews/preflight_verification.json')['status']=='PASS'
for ds in DS:
    cfg=O/'inputs'/f'{ds}_{phase}.json';out=O/'results'/ds/phase;out.parent.mkdir(exist_ok=True)
    assert not out.exists();c=read(cfg)
    native('query',f'{phase}_{ds}',[O/'bin/evaluate',cfg,out],calls=c['real_call_cap'])
    r=read(out/'results.json');assert r['status']=='COMPLETE' and r['physical_graph_calls']==c['real_call_cap']
    dump(O/'state.json',dict(status=phase.upper()+'_IN_PROGRESS',last_dataset=ds,NSG_reserved=sum(x['reserved_NSG'] for x in read(O/'logs/jobs.json'))))
dump(O/'state.json',dict(status=phase.upper()+'_COMPLETE_PENDING_INDEPENDENT_VERIFY',NSG_reserved=sum(x['reserved_NSG'] for x in read(O/'logs/jobs.json'))))
