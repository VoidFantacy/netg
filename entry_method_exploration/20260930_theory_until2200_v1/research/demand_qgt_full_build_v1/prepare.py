import hashlib,json,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
P=R.parent/'hybrid_temperature_factorial_v1';OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1'
C=json.loads((P/'config.locked.json').read_text());PRE=json.loads((OLD/'research/gt_inclusive_build_cost_v1/reviews/preflight.json').read_text())
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    for name in ['inputs','results','reviews','logs']:(R/name).mkdir()
    config={'datasets':{},'seconds_cap':1800,'deadline_unix':1790775000,'max_new_bytes':250*2**20,'expected_total_exact_queries':5732,'total_teacher_calls':35968}
    refs={};paths=[R/'protocol.md',Path(__file__),P/'config.locked.json'];large={}
    for di,(ds,dc) in enumerate(C['datasets'].items()):
        e=dc['evaluate'];p=dc['profiles'];out=R/'results'/ds
        cfg={k:e[k] for k in ['dataset','base','base_n','dimension','index']}
        cfg.update(qgt_queries=PRE['datasets'][ds]['qgt_queries'],fit_queries=p['queries'],fit_n=20000,pilot_n=2048,
            pilot_seed=2026093002+di,H=815 if di==0 else 821,soft=(di==0),L=1250 if di==0 else 256,
            selector_source=str(ROOT/'benches/run/build_fast_entry_variants.py'),output=str(out))
        config['datasets'][ds]=cfg;dump(R/'inputs'/f'{ds}.json',cfg)
        refs[ds]={'qgt_gt':PRE['datasets'][ds]['qgt_GT'],'selected_rows':p['selected_rows'],'selected_gt':p['selected_gt'],
            'approx_ids':p['approx_ids'],'approx_distances':str(Path(p['approx_ids']).with_name('distances.f32')),
            'model':e['methods'][-1], 'full_build':str(R.parent/'hybrid_full_build_cost_v1/results'/ds), 'demand_trace':str(R.parent/'demand_qgt_v1/results'/f'{ds}.trace.json')}
        paths += [Path(cfg[k]) for k in ['qgt_queries','fit_queries','selector_source']]
        for k in ['base','index']:
            path=Path(cfg[k]);s=path.stat();large[str(path)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
    config['teacher_binary']=str(OLD/'stages/e125_approximate_target_profiles_v1/bin/labels_without_router')
    config['router_binary']=str(P/'bin/build_router')
    paths += [Path(config['teacher_binary']),Path(config['router_binary'])]
    dump(R/'config.locked.json',config);dump(R/'reviews/validation_references.json',refs)
    dump(R/'reviews/preparation.json',{'unix':time.time(),'inputs':{str(p):ident(p) for p in dict.fromkeys(paths)},'large_stat_only':large,
        'new_searches':0,'candidate_parameter_changes':0})
    print('PREPARED',flush=True)
if __name__=='__main__':main()
