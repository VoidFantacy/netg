import hashlib,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];E=R.parent/'energy_temperature_clean_v1';D=R.parent/'demand_qgt_full_build_v1';F=R.parent/'default_demand_full_build_v1';P=R.parent/'hybrid_temperature_factorial_v1'
OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    assert json.loads((E/'results/summary.json').read_text())['gate_pass']
    for p in [E,D,F]:assert json.loads((p/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((D/'reviews/fixture.json').read_text())['status']=='PASS' and ident(R/'lazy_gt.py')==ident(D/'lazy_gt.py')
    for part in ['inputs','results','reviews','logs']:(R/part).mkdir()
    c0=json.loads((D/'config.locked.json').read_text());e125=json.loads((OLD/'config.locked.json').read_text())
    cfg={'datasets':{},'seconds_cap':1800,'per_dataset_seconds_cap':900,'deadline_unix':1790775000,'max_new_bytes':85*(1<<20),
        'max_campaign_bytes':1<<30,'min_free_bytes':6*(1<<30),'expected_exact_queries':7780,'max_exact_queries':10000,
        'expected_teacher_calls':40064,'expected_audit_ANN':2048,'primary':'EnergyTree','control':'ShuffledEnergyTree',
        'teacher_binary':c0['teacher_binary'],'router_binary':c0['router_binary'],'audit_binary':str(R/'audit_router')}
    refs={};paths=[R/'protocol.md',Path(__file__),E/'results/summary.json',E/'reviews/independent_audit.json',D/'reviews/fixture.json',D/'config.locked.json'];large={}
    for di,(ds,old) in enumerate(c0['datasets'].items()):
        c=dict(old);c.update(pilot_n=1024,shuffle_seed=2026093015+di,output=str(R/'results'/ds));cfg['datasets'][ds]=c;dump(R/'inputs'/f'{ds}.json',c)
        original=e125['datasets'][ds]['original'];refs[ds]={'demand_build':str(D/'results'/ds),'full_default':str(F/'results'/ds),
            'fit_gt':original['fit_source']['gt_file'],'approx_ids':str(OLD/'results'/ds/'labels/ids.i32'),
            'approx_distances':str(OLD/'results'/ds/'labels/distances.f32'),'simulation_npz':str(E/'models'/f'{ds}.npz'),
            'simulation_json':str(E/'models'/f'{ds}.json'),'default_cost_summary':str(F/'results/cost_summary.json')}
        paths += [Path(c[k]) for k in ['qgt_queries','fit_queries','selector_source']]
        for k in ['base','index']:
            p=Path(c[k]);s=p.stat();large[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
    argv=json.loads((P/'reviews/compile_evaluate.job.json').read_text())['argv'];argv[argv.index(str(P/'src/evaluate.cpp'))]=str(R/'audit_router.cpp');argv[-1]=str(R/'audit_router')
    t=time.perf_counter()
    with (R/'logs/audit_compile.log').open('x') as log:ret=subprocess.run(['taskset','-c','0-7',*argv],stdout=log,stderr=subprocess.STDOUT,timeout=120)
    dump(R/'reviews/audit_compile.json',{'argv':argv,'exit_code':ret.returncode,'seconds':time.perf_counter()-t});assert ret.returncode==0
    paths += [Path(cfg[k]) for k in ['teacher_binary','router_binary','audit_binary']]+list((P/'src').rglob('*.*'))
    dump(R/'config.locked.json',cfg);dump(R/'reviews/validation_references.json',refs)
    paths += [R/'config.locked.json',R/'reviews/validation_references.json',*R.glob('*.py'),R/'audit_router.cpp',*list((R/'inputs').glob('*.json'))]
    dump(R/'reviews/preparation.json',{'unix':time.time(),'inputs':{str(p):ident(p) for p in dict.fromkeys(paths)},'large_stat_only':large,
        'lazy_helper_unchanged_fixture_already_PASS':True,'no_builder_old_label_temperature_W_inputs':True,'new_GT':0,'new_NSG':0})
    print('PREPARED ENERGY BUILD',flush=True)
if __name__=='__main__':main()
