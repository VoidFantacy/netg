import hashlib,json,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];P=R.parent/'hybrid_temperature_factorial_v1';T=R.parent/'temperature_full_build_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
    for previous in [P,T]:assert json.loads((previous/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert shutil.disk_usage(R).free>=6*2**30
    for name in ['inputs','results','reviews','logs','bin','src']:(R/name).mkdir()
    shutil.copytree(P/'src/common',R/'src/common');shutil.copy2(P/'src/kernels.hpp',R/'src/kernels.hpp')
    source=(P/'src/evaluate.cpp').read_text();needle='if(m<2){auto old=fs::path(c["baseline_reference"]'
    assert source.count(needle)==1;source=source.replace(needle,'if(m<2&&c.contains("baseline_reference")){auto old=fs::path(c["baseline_reference"]')
    (R/'src/evaluate.cpp').write_text(source)
    old=json.loads((P/'config.locked.json').read_text());cases={};datasets={};models={};large={};source_order=[]
    for di,(ds,dc) in enumerate(old['datasets'].items()):
        ec=dc['evaluate'];dsdir='WebVid2.5M_light_v1' if di==0 else 'YandexT2I_official10M_ip_v1';base=ROOT/'benches/datasets'/dsdir
        methods=[ec['methods'][0],ec['methods'][1],next(x for x in ec['methods'] if x['name']==('HybridPilotTemperature' if di==0 else 'HybridFixedTemperature'))]
        if di==0:
            for name in ['HybridRectifiedCDF','HybridApproxMedian']:
                out=T/'results'/ds;methods.append({'name':name,'ids':str(out/'ids.i32'),'W':str(out/name/'W.f32'),'graph':str(out/name/'router.hnsw')})
        for method in methods:
            for k in ['ids','W','graph']:models[method[k]]=ident(method[k])
        extras=[ROOT/'entry_method_exploration/20260920_wfree_frozen_replication_v1/inputs'/ds/'candidate_source.f32',Path(dc['profiles']['queries'])]
        if di==0:extras.append(ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_web_fresh_check_v1/inputs'/ds/'candidate_source.f32')
        datasets[ds]={'dataset_dir':str(base),'dimension':ec['dimension'],'base':ec['base'],'base_n':ec['base_n'],
            'excluded_extra_files':[str(p) for p in extras],'methods':methods,
            'starts':[2410000,2430000] if di==0 else [2020000,2040000],
            'source_kind':'local' if di==0 else 'HTTP_Range',
            'source':str(base/'source/webvid.query.train.2.5M.fbin') if di==0 else 'https://storage.yandexcloud.net/yandex-research/ann-datasets/T2I/query.learn.50M.fbin'}
        for key in ['base','index']:
            p=Path(ec[key]);s=p.stat();large[str(p)]={'bytes':s.st_size,'mtime_ns':s.st_mtime_ns}
        for batch in range(2):
            name=f'{ds}_b{batch}';inp=R/'inputs'/name
            cfg={k:ec[k] for k in ['dataset','base','base_n','dimension','index','points']}
            cfg.update(n=4096,queries=str(inp/'queries.f32'),gt=str(inp/'gt.i32'),formal=True,threads=1,repeats=3,normalize_anchor=False,
                dataset_order=di+2*batch,methods=methods,max_search_calls=210000 if di==0 else 130000,seconds_cap=1200,batch=batch,
                source_start=datasets[ds]['starts'][batch],candidate_count=20000)
            dump(R/'inputs'/f'{name}.evaluate.json',cfg);cases[name]=cfg
    ordered={}
    for batch in range(2):
        for ds in datasets:ordered[f'{ds}_b{batch}']=cases[f'{ds}_b{batch}']
    config={'cases':ordered,'datasets':datasets,'n':4096,'repeats':3,'GT_threads':8,'GT_seconds_cap':1800,
        'deadline_unix':1790775000,'seconds_cap':5400,'max_new_bytes':320*2**20,'max_campaign_bytes':2**30,'min_free_bytes':6*2**30,
        'max_NSG':660000,'expected_NSG':655872,'expected_ANN':655360,'new_exact_GT':16384,'bootstrap_replicates':20000,'bootstrap_seed':2026093011}
    dump(R/'config.locked.json',config);dump(R/'reviews/models_before_source.json',{'status':'FROZEN_BEFORE_NEW_SOURCE','unix':time.time(),'files':models,'large_stat_only':large})
    argv=json.loads((P/'reviews/compile_evaluate.job.json').read_text())['argv'];argv=[x.replace(str(P/'src/common'),str(R/'src/common')).replace(str(P/'src/evaluate.cpp'),str(R/'src/evaluate.cpp')) for x in argv];argv[-1]=str(R/'bin/evaluate')
    dump(R/'compile.json',argv);dump(R/'reviews/source_change.json',{'old_source':ident(P/'src/evaluate.cpp'),'new_source':ident(R/'src/evaluate.cpp'),
        'only_change':'baseline_reference cache check is conditional on config field; kernel and all E99/warm/count/thread checks unchanged'})
    print('PREPARED',flush=True)
if __name__=='__main__':main()
