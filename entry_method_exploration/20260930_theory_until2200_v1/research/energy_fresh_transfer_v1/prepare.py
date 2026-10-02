import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=R.parent/'hybrid_temperature_factorial_v1';T=R.parent/'temperature_full_build_v1';F=R.parent/'fresh_transfer_v1';E=R.parent/'energy_full_build_v1';D=R.parent/'default_demand_full_build_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    for previous in [E,D,F]:assert json.loads((previous/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert json.loads((E/'results/cost_summary.json').read_text())['gate_pass']
    assert shutil.disk_usage(R).free>=6*(1<<30)
    size=sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file());assert size+225*(1<<20)<=1<<30
    for name in ['inputs','results','reviews','logs','bin','src']:(R/name).mkdir()
    shutil.copytree(F/'src/common',R/'src/common');shutil.copy2(F/'src/kernels.hpp',R/'src/kernels.hpp')
    source=(F/'src/evaluate.cpp').read_text();needle='require((M==3||M==5)&&names[1]=="ApproxTarget10","frozen factorial methods");'
    assert source.count(needle)==1
    source=source.replace(needle,'require(M==4&&(names[0]=="GT10-soft-t1"||names[0]=="GT10-hard")&&names[1]=="Uniform"&&names[2]=="ShuffledEnergyTree"&&names[3]=="EnergyTree","frozen energy methods");')
    needle='auto run=[&](int m,Batch&b,bool count){auto&router='
    assert source.count(needle)==1
    source=source.replace(needle,'auto run=[&](int m,Batch&b,bool count){require(calls+n<=c["max_search_calls"].get<uint64_t>(),"pre-search call cap");auto&router=')
    needle='for(size_t i=0;i<16;++i){ep.clear();'
    assert source.count(needle)==1
    source=source.replace(needle,'require(calls+16<=c["max_search_calls"].get<uint64_t>(),"pre-E99 call cap");for(size_t i=0;i<16;++i){ep.clear();')
    (R/'src/evaluate.cpp').write_text(source)
    old=json.loads((P/'config.locked.json').read_text());cases={};datasets={};models={};large={};aliases={}
    for di,(ds,dc) in enumerate(old['datasets'].items()):
        ec=dc['evaluate'];dsdir='WebVid2.5M_light_v1' if di==0 else 'YandexT2I_official10M_ip_v1';base=ROOT/'benches/datasets'/dsdir
        default={'name':'GT10-soft-t1' if di==0 else 'GT10-hard','ids':str(D/'results'/ds/'ids.i32'),'W':str(D/'results'/ds/'W.f32'),'graph':str(D/'results'/ds/'router.hnsw')}
        if di==0:
            path=T/'results'/ds;uniform={'name':'Uniform','ids':str(path/'ids.i32'),'W':str(path/'HybridApproxMedian/W.f32'),'graph':str(path/'HybridApproxMedian/router.hnsw')}
            alias='HybridApproxMedian'
        else:
            original=next(x for x in ec['methods'] if x['name']=='HybridFixedTemperature');uniform={**original,'name':'Uniform'};alias='HybridFixedTemperature'
        methods=[default,uniform]
        for name in ['ShuffledEnergyTree','EnergyTree']:
            out=E/'results'/ds;methods.append({'name':name,'ids':str(out/'ids.i32'),'W':str(out/name/'W.f32'),'graph':str(out/name/'router.hnsw')})
        aliases[ds]={'Uniform':alias,'total_exact_fit_labels_per_nondefault_model':2048,'fixed_replicate':'r0'}
        for m in methods:
            for key in ['ids','W','graph']:models[m[key]]=ident(m[key])
        extras=[ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/inputs'/ds/'candidate_source.f32',Path(dc['profiles']['queries'])]
        if di==0:extras.append(ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/inputs'/ds/'candidate_source.f32')
        extras += [F/'inputs'/f'{ds}_b{b}'/'candidate_source.f32' for b in range(2)]
        datasets[ds]={'dataset_dir':str(base),'dimension':ec['dimension'],'base':ec['base'],'base_n':ec['base_n'],
            'excluded_extra_files':[str(p) for p in extras],'methods':methods,'starts':[2370000,2390000] if di==0 else [2060000,2080000],
            'source_kind':'local' if di==0 else 'HTTP_Range',
            'source':str(base/'source/webvid.query.train.2.5M.fbin') if di==0 else 'https://storage.yandexcloud.net/yandex-research/ann-datasets/T2I/query.learn.50M.fbin'}
        for key in ['base','index']:
            p=Path(ec[key]);s=p.stat();large[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
        for batch in range(2):
            name=f'{ds}_b{batch}';inp=R/'inputs'/name;cfg={k:ec[k] for k in ['dataset','base','base_n','dimension','index','points']}
            cfg.update(n=4096,queries=str(inp/'queries.f32'),gt=str(inp/'gt.i32'),formal=True,threads=1,repeats=3,normalize_anchor=False,
                dataset_order=di+2*batch,methods=methods,max_search_calls=164000,seconds_cap=1200,batch=batch,
                source_start=datasets[ds]['starts'][batch],candidate_count=20000)
            dump(R/'inputs'/f'{name}.evaluate.json',cfg);cases[name]=cfg
    ordered={f'{ds}_b{batch}':cases[f'{ds}_b{batch}'] for batch in range(2) for ds in datasets}
    config={'cases':ordered,'datasets':datasets,'n':4096,'repeats':3,'GT_threads':8,'GT_seconds_cap':1800,
        'deadline_unix':1790775000,'seconds_cap':5400,'max_new_bytes':225*(1<<20),'max_campaign_bytes':1<<30,'min_free_bytes':6*(1<<30),
        'max_NSG':660000,'expected_NSG':655872,'expected_ANN':655360,'new_exact_GT':16384,'bootstrap_replicates':20000,'bootstrap_seed':2026093017,'small_gap_check_cap':64}
    dump(R/'config.locked.json',config);dump(R/'reviews/models_before_source.json',{'status':'FROZEN_BEFORE_NEW_SOURCE','unix':time.time(),'files':models,'large_stat_only':large,'aliases':aliases,'preparation_campaign_bytes':size})
    argv=json.loads((F/'compile.json').read_text());argv=[x.replace(str(F/'src/common'),str(R/'src/common')).replace(str(F/'src/evaluate.cpp'),str(R/'src/evaluate.cpp')) for x in argv];argv[-1]=str(R/'bin/evaluate')
    dump(R/'compile.json',argv);dump(R/'reviews/source_change.json',{'old_source':ident(F/'src/evaluate.cpp'),'new_source':ident(R/'src/evaluate.cpp'),
        'changes':['four named frozen methods constraint','call caps before measured batch and E99 check'],'search_kernel_and_all_E99_warm_count_checks_unchanged':True})
    dump(R/'reviews/historical_window_check.json',{'unix':time.time(),'old_web_E105':[2450000,2470000],'old_web_Sept22':[2470000,2490000],
        'old_record151':{'web':[[2410000,2430000],[2430000,2450000]],'yandex':[[2020000,2040000],[2040000,2060000]]},
        'new_windows':{ds:d['starts'] for ds,d in datasets.items()},'all_full_old_candidate_files_excluded':True,'current_batch0_full_candidate_excluded_from_batch1':True,'raw_new_source_read':False})
    print('PREPARED FOUR-MODEL ENERGY CONFIRMATION',flush=True)
if __name__=='__main__':main()
