import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=R.parent/'hybrid_temperature_factorial_v1';D=R.parent/'demand_qgt_full_build_v1'
OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1';G=OLD/'research/gt_inclusive_build_cost_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    assert json.loads((D/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((D/'reviews/fixture.json').read_text())['status']=='PASS'
    assert ident(R/'lazy_gt.py')==ident(D/'lazy_gt.py')
    for part in ['inputs','results','reviews','logs']:(R/part).mkdir()
    previous=json.loads((P/'config.locked.json').read_text());qgt=json.loads((G/'reviews/preflight.json').read_text())
    sources=json.loads((OLD/'stages/e125_approximate_target_profiles_v1/config.locked.json').read_text())
    config={'datasets':{},'seconds_cap':3600,'per_dataset_seconds_cap':2700,'deadline_unix':1790775000,
        'max_new_bytes':100*(1<<20),'max_campaign_bytes':1<<30,'min_free_bytes':6*(1<<30),'expected_exact_queries':41636,'max_exact_queries':50000,
        'router_binary':str(P/'bin/build_router'),'audit_binary':str(D/'audit_router')}
    paths=[R/'protocol.md',Path(__file__),P/'config.locked.json',G/'reviews/preflight.json',D/'lazy_gt.py',D/'reviews/fixture.json',D/'reviews/independent_audit.json',Path(config['router_binary']),Path(config['audit_binary'])]
    references={};large={}
    for di,(ds,c) in enumerate(previous['datasets'].items()):
        e=c['evaluate'];profile=c['profiles'];dc={key:e[key] for key in ['dataset','base','base_n','dimension','index']}
        dc.update(qgt_queries=qgt['datasets'][ds]['qgt_queries'],fit_queries=profile['queries'],fit_n=20000,H=815 if di==0 else 821,
            soft=(di==0),selector_source=str(ROOT/'benches/run/build_fast_entry_variants.py'),output=str(R/'results'/ds))
        config['datasets'][ds]=dc;dump(R/'inputs'/f'{ds}.json',dc)
        references[ds]={'model':e['methods'][0],'fit_gt':sources['datasets'][ds]['original']['fit_source']['gt_file'],
            'full_gt_build':str(G/'results'/ds),'demand_build':str(D/'results'/ds),
            'profile_manifest':str(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/models'/ds/('gt10_soft_t1' if di==0 else 'gt10_hard')/'manifest.json')}
        paths += [Path(dc[k]) for k in ['qgt_queries','fit_queries','selector_source']]
        for k in ['base','index']:
            p=Path(dc[k]);st=p.stat();large[str(p)]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}
    dump(R/'config.locked.json',config);dump(R/'reviews/validation_references.json',references)
    dump(R/'reviews/preparation.json',{'unix':time.time(),'inputs':{str(p):ident(p) for p in dict.fromkeys(paths)},'large_stat_only':large,
        'lazy_helper_unchanged_and_fixture_already_PASS':True,'builder_reads_old_GT_temperature_or_model':False,'new_GT':0,'new_NSG':0})
    print('PREPARED DEFAULT REFERENCE',flush=True)
if __name__=='__main__':main()
