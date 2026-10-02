import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1'
os.sched_setaffinity(0,range(8))
import hashlib,json,resource,shutil,sys,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info

R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
faiss.omp_set_num_threads(8)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(16<<20),b''):h.update(block)
    return h.hexdigest()

def ident(path):
    p=Path(path);return {'bytes':p.stat().st_size,'sha256':sha(p)}

def dump(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def main():
    start=time.perf_counter();assert time.time()<C['latest_start_unix']
    for prior in ['energy_fresh_transfer_v1','energy_routing_bridge_v1']:
        assert json.loads((R.parent/prior/'reviews/seal.json').read_text())['status']=='AUDITED_COMPLETE'
    assert json.loads((R.parent/'energy_fresh_transfer_v1/reviews/active_process.json').read_text())['pid'] is None
    assert shutil.disk_usage(R).free>=C['min_free_bytes']
    assert sum(p.stat().st_size for p in R.parents[1].rglob('*') if p.is_file())+C['max_new_bytes']<=C['max_campaign_bytes']
    (R/'results').mkdir();(R/'reviews').mkdir(exist_ok=True)
    sources=[R/'protocol.md',R/'source_reasoning.md',R/'config.locked.json',*R.glob('*.py')]
    for c in C['datasets'].values():
        sources += [Path(c['fit_queries']),Path(c['output'])/'fit20000.ids.i64',Path(c['output'])/'fit20000.dist.f32']
    libraries={str(Path(m.__file__)) for name,m in list(sys.modules.items()) if name.startswith('faiss') and getattr(m,'__file__',None) and '.so' in m.__file__}
    libraries.update(p['filepath'] for p in threadpool_info())
    frozen={str(p):ident(p) for p in dict.fromkeys(sources)}
    params={'version':faiss.__version__,'blas_threshold':faiss.cvar.distance_compute_blas_threshold,
        'query_block':faiss.cvar.distance_compute_blas_query_bs,'database_block':faiss.cvar.distance_compute_blas_database_bs,
        'min_k_reservoir':faiss.cvar.distance_compute_min_k_reservoir,'compile_options':faiss.get_compile_options()}
    assert params['version']=='1.15.0' and params['blas_threshold']==128000 and params['min_k_reservoir']==100
    dump(R/'reviews/frozen.json',{'unix':time.time(),'files':frozen,'libraries':{p:ident(p) for p in sorted(libraries)},'runtime':params})
    calls=0;reserved=0;records={}
    def check():
        assert time.perf_counter()-start<C['seconds_cap'] and time.time()<C['deadline_unix']
        assert shutil.disk_usage(R).free>=C['min_free_bytes']
    def ledger(ds,setting,phase,rows):
        (R/'reviews/progress.json').write_text(json.dumps({'dataset':ds,'config':setting,'phase':phase,'rows':rows,
            'completed_exact_queries':calls,'reserved_exact_queries':reserved,'unix':time.time()})+'\n')
    for ds,c in C['datasets'].items():
        dsstart=time.perf_counter();check();out=R/'results'/ds;out.mkdir()
        d,n=c['dimension'],C['n'];basepath=Path(c['base']);manifest=json.loads((basepath.parent/'manifest.json').read_text())
        t=time.perf_counter();base_sha=sha(basepath);assert base_sha==manifest['files'][basepath.name]['sha256'];base_identity_seconds=time.perf_counter()-t
        q=np.memmap(c['fit_queries'],'<f4',mode='r',shape=(c['fit_n'],d))[:n].copy();assert np.isfinite(q).all()
        oldids=np.memmap(Path(c['output'])/'fit20000.ids.i64','<i8',mode='r',shape=(c['fit_n'],100))[:n]
        olddist=np.memmap(Path(c['output'])/'fit20000.dist.f32','<f4',mode='r',shape=(c['fit_n'],100))[:n]
        raw=np.memmap(basepath,'<f4',mode='r',shape=(c['base_n'],d+1));index=faiss.IndexFlatIP(d)
        t=time.perf_counter()
        for lo in range(0,c['base_n'],100000):
            check();block=raw[lo:lo+100000];assert np.all(block[:,0].view('<i4')==d)
            index.add(np.ascontiguousarray(block[:,1:]))
        load_seconds=time.perf_counter()-t;assert index.ntotal==c['base_n']
        references={};times={s['name']:[] for s in C['configs']};warm={};rounds=[]
        def execute(setting,phase):
            nonlocal calls,reserved
            name,k,batch=setting['name'],setting['k'],setting['batch'];check()
            assert time.perf_counter()-dsstart<C['per_dataset_seconds_cap']
            assert reserved==calls and calls+n<=C['exact_query_cap']
            # Guard and reserve before the measured loop. No logging or hashing inside the loop.
            reserved+=n;ledger(ds,name,phase,0)
            t=time.perf_counter();ids=np.empty((n,k),dtype='i8');dist=np.empty((n,k),dtype='f4')
            for lo in range(0,n,batch):
                hi=min(lo+batch,n);assert calls+hi-lo<=reserved<=C['exact_query_cap']
                dd,ii=index.search(q[lo:hi],k);calls+=hi-lo;ids[lo:hi]=ii;dist[lo:hi]=dd
            elapsed=time.perf_counter()-t;ledger(ds,name,phase,n)
            assert np.isfinite(dist).all() and np.all(ids>=0) and np.all(ids<c['base_n'])
            assert np.all(np.diff(dist,axis=1)<=0) and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
            rec={'seconds':elapsed,'ids_sha256':hashlib.sha256(ids.tobytes()).hexdigest(),'dist_sha256':hashlib.sha256(dist.tobytes()).hexdigest()}
            if phase=='warm':
                references[name]=(ids,dist);ids.tofile(out/(name+'.ids.i64'));dist.tofile(out/(name+'.dist.f32'));warm[name]=rec
                if name=='Batch256K100':
                    np.testing.assert_array_equal(ids,oldids);np.testing.assert_array_equal(dist.view('u4'),olddist.view('u4'))
            else:
                ii,dd=references[name];np.testing.assert_array_equal(ids,ii);np.testing.assert_array_equal(dist.view('u4'),dd.view('u4'))
                times[name].append(elapsed)
            print(ds,name,phase,'PASS',elapsed,flush=True);return rec
        for setting in C['configs']:execute(setting,'warm')
        for round_index in range(C['timed_repeats']):
            order=[(i+round_index)%len(C['configs']) for i in range(len(C['configs']))];items=[]
            for index_id in order:
                setting=C['configs'][index_id];items.append({'name':setting['name'],**execute(setting,f'timed{round_index}')})
            rounds.append({'round':round_index,'order':[C['configs'][i]['name'] for i in order],'runs':items})
        baseids,basedist=references['Batch256K100'];comparisons=[]
        for setting in C['configs']:
            name=setting['name'];ii,dd=references[name];first=ii[:,:10];bits=dd[:,:10].view('u4');bad=first!=baseids[:,:10]
            comparisons.append({'name':name,'mean_search_loop_seconds':float(np.mean(times[name])),'timed_seconds':times[name],
                'mean_seconds_ratio_to_original':float(np.mean(times[name])/np.mean(times['Batch256K100'])),
                'paired_round_seconds_ratios':[a/b for a,b in zip(times[name],times['Batch256K100'])],
                'first10_order_changed_queries':int(np.any(bad,axis=1).sum()),'first10_order_changed_cells':int(bad.sum()),
                'first10_set_changed_queries':int(np.any(np.sort(first,axis=1)!=np.sort(baseids[:,:10],axis=1),axis=1).sum()),
                'first10_distance_bit_changed_cells':int(np.sum(bits!=basedist[:,:10].view('u4'))),
                'first10_max_distance_difference':float(np.max(np.abs(dd[:,:10].astype('f8')-basedist[:,:10]))),
                'inferred_kernel_path':'blas' if setting['batch']*d>=params['blas_threshold'] else 'sequential_query_parallel',
                'inferred_result_handler':'heap' if setting['k']<params['min_k_reservoir'] else 'reservoir'})
        records[ds]={'dataset':ds,'n':n,'source_rows':[0,n],'base_sha256':base_sha,'base_identity_seconds':base_identity_seconds,
            'flat_load_seconds':load_seconds,'warm':warm,'rounds':rounds,'comparisons':comparisons,
            'complete_dataset_seconds':time.perf_counter()-dsstart,'new_exact_queries':n*len(C['configs'])*(1+C['timed_repeats']),
            'actual_affinity':sorted(os.sched_getaffinity(0)),'faiss_threads':faiss.omp_get_max_threads(),'threadpools':threadpool_info(),
            'resident_threads':len(list(Path('/proc/self/task').iterdir()))}
        assert records[ds]['actual_affinity']==list(range(8)) and records[ds]['faiss_threads']==8
        assert all(pool['num_threads']<=8 for pool in records[ds]['threadpools'])
        dump(out/'complete.json',records[ds]);del index,raw,references,q,oldids,olddist
    assert calls==reserved==C['exact_query_cap']
    for p,v in frozen.items():assert ident(p)==v
    dump(R/'results/summary.json',{'status':'COMPUTED_PENDING_AUDIT','datasets':records,'seconds':time.perf_counter()-start,
        'new_exact_GT_queries':calls,'new_NSG':0,'new_ANN':0,'new_models':0,'new_graphs':0,'default_changed':False,
        'maxrss_GiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,
        'timing_scope':'8-thread offline exact-label search loop; index load, base identity, disk output and audits separate; not ANN QPS'})
    assert sum(p.stat().st_size for p in R.rglob('*') if p.is_file())<=C['max_new_bytes']
    print('ALL FIXED FOUR-CELL RUNS COMPLETE',flush=True)

if __name__=='__main__':main()
