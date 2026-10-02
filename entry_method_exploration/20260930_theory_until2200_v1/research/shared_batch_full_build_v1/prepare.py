import os
os.sched_setaffinity(0,range(8))
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
import hashlib,json,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parents[3];CAMP=R.parents[1]
D=R.parent/'default_demand_full_build_v1';E=R.parent/'energy_full_build_v1';U=R.parent/'demand_qgt_full_build_v1';T=R.parent/'temperature_full_build_v1'
F=R.parent/'hybrid_temperature_factorial_v1';P=R.parent/'exact_label_dispatch_v1'
OLD=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()

def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':sha(p)}

def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def main():
    started=time.time();assert started<1790773200
    assert json.loads((P/'reviews/seal.json').read_text())['status']=='AUDITED_COMPLETE'
    pa=json.loads((P/'reviews/independent_audit.json').read_text());assert pa['status']=='PASS' and pa['main_cost_gate_pass']
    for p in [D,E,U,T]:assert json.loads((p/'reviews/independent_audit.json').read_text())['status']=='PASS'
    assert ident(R/'lazy_gt.py')==ident(E/'lazy_gt.py')
    assert shutil.disk_usage(R).free>=6*(1<<30)
    assert sum(p.stat().st_size for p in CAMP.rglob('*') if p.is_file())+42*(1<<20)<=1<<30
    for part in ['inputs','results','reviews','logs']:(R/part).mkdir()
    old=json.loads((E/'config.locked.json').read_text());online=json.loads((R.parent/'energy_fresh_transfer_v1/config.locked.json').read_text())
    cfg={'cases':{},'order':[],'fit_batch':1024,'returned_k':100,'stored_prefix':11,'seconds_cap':3600,'per_build_seconds_cap':1800,
        'stage_started_unix':started,'deadline_unix':1790776800,'latest_start_unix':1790773200,
        'max_new_bytes':42*(1<<20),'max_campaign_bytes':1<<30,'min_free_bytes':6*(1<<30),
        'expected_GT_calls':53100,'max_GT_calls':60000,'expected_NSG_calls':78080,'max_NSG_calls':78080,
        'expected_ANN_calls':3072,'max_ANN_calls':3072,'float64_audit_cap_per_dataset':64,
        'teacher_binary':str(R/'labels_prefix'),'router_binary':old['router_binary'],'audit_binary':old['audit_binary']}
    refs={};small=[];large={};budget=[]
    for di,(ds,c0) in enumerate(old['datasets'].items()):
        methods=['Default','Uniform','EnergyTree'] if di==0 else ['EnergyTree','Uniform','Default']
        for method in methods:
            name=ds+'__'+method;c={**c0,'method':method,'case':name,'output':str(R/'results'/name)}
            cfg['cases'][name]=c;cfg['order'].append(name);dump(R/'inputs'/(name+'.json'),c)
            om=next(x for x in online['datasets'][ds]['methods'] if x['name']==('GT10-soft-t1' if c['soft'] else 'GT10-hard')) if method=='Default' else next(x for x in online['datasets'][ds]['methods'] if x['name']==method)
            rootref=(D/'results'/ds if method=='Default' else (E/'results'/ds/'EnergyTree' if method=='EnergyTree' else (T/'results'/ds/'HybridApproxMedian' if c['soft'] else U/'results'/ds)))
            refs[name]={'profile_root':str(rootref),'model':om,'full_default':str(D/'results'/ds),
                'teacher_ids':str(OLD/'results'/ds/'labels/ids.i32'),'teacher_distances':str(OLD/'results'/ds/'labels/distances.f32')}
            teacher_n=0 if method=='Default' else (17952 if method=='Uniform' and not c['soft'] else 20000)
            exact_n=20000 if method=='Default' else 2048
            budget.append({'case':name,'H_W_graph_bytes':sum(Path(om[k]).stat().st_size for k in ['ids','W','graph']),
                'exact_prefix_bytes':exact_n*11*12,'teacher_prefix_bytes':teacher_n*11*8,'QGT_full_bytes':c['H']*(100*12+4),
                'allowance_small_arrays_metadata_audit':500000})
            small += [Path(c[k]) for k in ['qgt_queries','fit_queries','selector_source']]
        for key in ['base','index']:
            p=Path(c0[key]);st=p.stat();prior=json.loads((E/'reviews/preparation.json').read_text())['large_stat_only'][str(p)]
            assert {'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}==prior
            large[str(p)]={**prior,'verification':'same stat as audited156'}
        base=Path(c0['base']);manifest=base.parent/'manifest.json';m=json.loads(manifest.read_text())
        assert sha(base)==m['files'][base.name]['sha256'];large[str(base)]['sha256']=m['files'][base.name]['sha256'];small.append(manifest)
    assert len(cfg['order'])==6
    predicted=sum(sum(v for k,v in row.items() if k!='case') for row in budget)+5000000
    assert predicted<cfg['max_new_bytes'];dump(R/'reviews/output_budget.json',{'predicted_bytes_including_5MB_code_binary_allowance':predicted,'cap':cfg['max_new_bytes'],'cases':budget})
    # Only output/row-selection/budget wrappers may differ; native search body is unchanged.
    a=(OLD/'src/labels_without_router.cpp').read_text();b=(R/'labels_prefix.cpp').read_text()
    a=a[a.index(' void search('):a.index('\n};')];b=b[b.index(' void search('):b.index('\n};')]
    assert a==b.replace('require(calls<cap,"teacher call cap");','')
    teacher_text=(R/'labels_prefix.cpp').read_text();fixture_text=(R/'sha_fixture.cpp').read_text()
    helper=teacher_text[teacher_text.index('static std::string sha256_bytes'):teacher_text.index('struct Teacher {')]
    assert helper in fixture_text
    argv_fixture=['g++','-O2','-std=c++17',str(R/'sha_fixture.cpp'),'-o',str(R/'sha_fixture')]
    t=time.perf_counter()
    with (R/'logs/sha_fixture_compile.log').open('x') as log:
        fixture_compile=subprocess.run(['taskset','-c','0-7',*argv_fixture],stdout=log,stderr=subprocess.STDOUT,timeout=30)
    assert fixture_compile.returncode==0
    fixture_run=subprocess.run(['taskset','-c','14',str(R/'sha_fixture')],text=True,capture_output=True,timeout=20)
    expected=[hashlib.sha256(x).hexdigest() for x in [b'',b'abc',bytes(range(256))*16]]
    assert fixture_run.returncode==0 and fixture_run.stdout.splitlines()==expected
    dump(R/'reviews/sha_fixture.json',{'status':'PASS','argv':argv_fixture,'seconds':time.perf_counter()-t,
        'tested_lengths':[0,3,4096],'sha256':expected,'helper_sha256':hashlib.sha256(helper.encode()).hexdigest(),'GT_calls':0,'NSG_calls':0})
    argv=json.loads((OLD/'reviews/compile_labels.job.json').read_text())['argv'];argv[argv.index(str(OLD/'src/labels.cpp'))]=str(R/'labels_prefix.cpp');argv[-1]=str(R/'labels_prefix')
    t=time.perf_counter()
    with (R/'logs/compile.log').open('x') as log:ret=subprocess.run(['taskset','-c','0-7',*argv],stdout=log,stderr=subprocess.STDOUT,timeout=120)
    dump(R/'reviews/compile.json',{'argv':argv,'exit_code':ret.returncode,'seconds':time.perf_counter()-t});assert ret.returncode==0
    # The pipe uses the installed sha256sum; freeze its executable with all actual libraries.
    import faiss
    from threadpoolctl import threadpool_info
    import sys
    faiss.omp_set_num_threads(8);assert faiss.__version__=='1.15.0' and faiss.cvar.distance_compute_blas_threshold==128000
    libraries={str(Path(m.__file__)) for name,m in list(sys.modules.items()) if name.startswith('faiss') and getattr(m,'__file__',None) and '.so' in m.__file__}
    libraries.update(p['filepath'] for p in threadpool_info());libraries.add('/usr/bin/sha256sum')
    for binary in ['teacher_binary','router_binary','audit_binary']:small.append(Path(cfg[binary]))
    small.append(R/'sha_fixture')
    for group in [OLD/'src',F/'src']:
        small.extend(p for p in group.rglob('*') if p.is_file())
    dump(R/'config.locked.json',cfg);dump(R/'reviews/validation_references.json',refs)
    small += [R/'protocol.md',R/'source_adaptation.json',R/'config.locked.json',R/'reviews/validation_references.json',
              R.parent/'energy_temperature_clean_v1/common.py',OLD/'config.locked.json',
              *R.glob('*.py'),*R.glob('*.cpp'),*list((R/'inputs').glob('*.json'))]
    dump(R/'reviews/preparation.json',{'status':'PREPARED','unix':time.time(),'seconds':time.time()-started,
        'inputs':{str(p):ident(p) for p in dict.fromkeys(small)},'large':large,'libraries':{p:ident(p) for p in sorted(libraries)},
        'native_search_body_identical_after_removing_budget_guard':True,'GT_calls':0,'NSG_calls':0,
        'runtime':{'faiss_version':faiss.__version__,'blas_threshold':faiss.cvar.distance_compute_blas_threshold,'query_block':faiss.cvar.distance_compute_blas_query_bs,
                   'database_block':faiss.cvar.distance_compute_blas_database_bs,'reservoir_k':faiss.cvar.distance_compute_min_k_reservoir}})
    print('SHARED BATCH BUILD PREPARED',predicted,flush=True)

if __name__=='__main__':main()
