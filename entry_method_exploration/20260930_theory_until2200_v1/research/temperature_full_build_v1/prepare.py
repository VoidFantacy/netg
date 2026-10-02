import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent;OLD=R.parent/'demand_qgt_full_build_v1';DS='webvid2_5m_light_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
    assert json.loads((OLD/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((R.parent/'temperature_cdf_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
    for name in ['inputs','results','reviews','logs']:(R/name).mkdir()
    old=json.loads((OLD/'config.locked.json').read_text());c=dict(old['datasets'][DS]);c['output']=str(R/'results'/DS)
    config={k:v for k,v in old.items() if k not in ['datasets','expected_total_exact_queries','total_teacher_calls']}
    config.update(datasets={DS:c},expected_total_exact_queries=2863,total_teacher_calls=20032,
        primary='HybridRectifiedCDF',control='HybridApproxMedian')
    dump(R/'inputs'/f'{DS}.json',c);dump(R/'config.locked.json',config)
    refs=json.loads((OLD/'reviews/validation_references.json').read_text())[DS];refs['demand_build']=str(OLD/'results'/DS)
    refs['temperature_reference']=str(R.parent/'temperature_cdf_v1/results/summary.json')
    dump(R/'reviews/validation_references.json',{DS:refs})
    paths=[Path(__file__),R/'protocol.md',*[Path(c[k]) for k in ['qgt_queries','fit_queries','selector_source']],
        Path(config['teacher_binary']),Path(config['router_binary']),OLD/'reviews/fixture.json']
    for name in ['exact.py','lazy_gt.py']:
        assert (R/name).read_bytes()==(OLD/name).read_bytes();paths.append(OLD/name)
    large={}
    for key in ['base','index']:
        p=Path(c[key]);s=p.stat();large[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
    dump(R/'reviews/preparation.json',{'unix':time.time(),'inputs':{str(p):ident(p) for p in paths},'large_stat_only':large,
        'new_searches':0,'unchanged_lazy_oracle_fixture':str(OLD/'reviews/fixture.json')})
    print('PREPARED',flush=True)
if __name__=='__main__':main()
