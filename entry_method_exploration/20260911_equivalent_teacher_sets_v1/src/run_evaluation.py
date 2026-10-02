from common import *
import copy
import numpy as np

def models(ds):
    return [policy(ds,'gt10_hard'),policy(ds,'e29_cost_margin',E29/'models'/ds/'cost_margin/W.f32')]+new_policies(ds)

def points(policies,ls,exact=False,components=False):
    result=[]
    for L in ls:
        for p in policies:
            m=copy.deepcopy(p)
            m.update(L=L,exact=exact,name=p['model_name']+('_exact' if exact else '_hnsw')+f'_L{L}',
                component_wall=components and L==128 and p['model_name'] in ['gt10_hard','single','multi','single_matched','multi_matched'])
            result.append(m)
    return result

def formal_models(ds):
    old=read(E29/'results'/f'validation_{ds}'/'results.json')
    want=['nsg','fast30k','gt1_hard','gt10_hard','gt1_soft','gt10_soft','e28_mlp','cost_ce','cost_margin']
    result=[]
    for key in want:
        p=copy.deepcopy(next(m['configuration'] for m in old['methods'] if m['model_name']==key and m['L']==64))
        name='e29_'+key if key in ['cost_ce','cost_margin'] else key
        p.update(name=name,model_name=name,component_wall=False)
        if key=='fast30k':assert p['hnsw_seed']==100 and p['legacy_heap_order'] and not p['canonical_entry_order']
        result.append(p)
    return result+new_policies(ds)

def verify_outputs(dest,c,result):
    n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
    assert np.array_equal(np.fromfile(c['row_ids'],np.int64),np.fromfile(dest/'row_ids.i64',np.int64))
    thread=read(dest/'thread_contract.json')
    assert thread['process_threads']==thread['actual_openmp_threads']==1 and thread['cpu']==15
    assert result['GT_opened_after_all_raw_search'] and result['threads']==1
    for m in result['methods']:
        d=dest/m['name'];ids=np.fromfile(d/'ids.i32',np.int32).reshape(n,10)
        assert (ids>=0).all() and (ids<c['base_count']).all()
        found=(ids[:,:,None]==gt[:,None,:]).any(1)
        assert (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
        hits=found.sum(1)
        assert np.array_equal(hits,np.fromfile(d/'hits.u8',np.uint8))
        assert np.array_equal((found*(1<<np.arange(10))).sum(1),np.fromfile(d/'hitmask.u16',np.uint16))
        assert int(hits.sum())==m['total_hits'] and abs(hits.mean()/10-m['recall_at_10'])<1e-12
        assert m['repeated_output_parity'] and m['original_kernel_parity_queries']==16
        if c['timing_repeats']:
            qps=np.array(m['qps_runs']);seconds=np.array(m['end_to_end_seconds'])
            assert len(qps)==len(seconds)==5 and np.allclose(qps,n/seconds,rtol=1e-12)
            assert abs(m['qps']-np.median(qps))<1e-8
        else:assert m['qps'] is None and not m['qps_runs']
    dump(dest/'independent_verification.json',dict(status='PASS',points=len(result['methods']),query_outputs=n*len(result['methods']),GT_rescore_all=True,threads=1))

def run(ds,stage,methods,split,reps=0):
    assert shutil.disk_usage(O).free>10*(1<<30)
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())+(128<<20)<1<<30
    c=read(O/'inputs'/ds/split/'config.json')
    c['base_count']=read(E24/'inputs'/ds/'prepared.json')['base_rows']
    c.update(methods=methods,timing_repeats=reps,dataset_order=DS.index(ds),threads=1,query_cpu=15)
    n=c['num_queries'];cap=sum(((2*reps+1) if reps else 2)*n+16+(2*n if m.get('component_wall') else 0) for m in methods)
    c['real_call_cap']=cap;dest=O/'results'/f'{stage}_{ds}';cfg=O/'inputs'/ds/f'eval_{stage}.json'
    assert not dest.exists() and not cfg.exists()
    dump(cfg,c);logpath=O/'logs/evaluation_jobs.json';jobs=read(logpath) if logpath.exists() else []
    assert sum(j['reserved_calls'] for j in jobs)+cap<=NORMAL_CAP
    assert sum(j.get('seconds',0) for j in jobs)<5400
    argv=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)]
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    rec=dict(dataset=ds,stage=stage,argv=argv,reserved_calls=cap,status='RUNNING',start=time.time(),config=identity(cfg),rss_peak_kib=0)
    jobs.append(rec);dump(logpath,jobs)
    with (O/'logs'/f'{ds}.{stage}.log').open('w') as log:
        proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(O/'state.json',dict(status=stage.upper()+'_RUNNING',dataset=ds,pid=proc.pid,training_runs=4,heldout_access=False))
        try:
            while proc.poll() is None:
                elapsed=time.time()-rec['start']
                if elapsed>2000:raise RuntimeError('job wall limit')
                if elapsed+sum(j.get('seconds',0) for j in jobs)>5400:raise RuntimeError('total query wall limit')
                status=Path(f'/proc/{proc.pid}/status')
                if status.exists():
                    for line in status.read_text().splitlines():
                        if line.startswith('VmRSS:'):rec['rss_peak_kib']=max(rec['rss_peak_kib'],int(line.split()[1]))
                    if rec['rss_peak_kib']>40*(1<<20):raise RuntimeError('RSS limit')
                try:proc.wait(timeout=2)
                except subprocess.TimeoutExpired:pass
            rc=proc.returncode
        except BaseException:
            proc.kill();proc.wait();rec.update(status='FAILED',seconds=time.time()-rec['start'],exit_code=proc.returncode)
            dump(logpath,jobs);raise
    rec.update(exit_code=rc,seconds=time.time()-rec['start'],status='COMPLETE' if rc==0 else 'FAILED');dump(logpath,jobs)
    assert rc==0,(ds,stage)
    result=read(dest/'results.json');assert result['physical_graph_calls']==cap
    verify_outputs(dest,c,result)
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<1<<30
    print(ds,stage,'COMPLETE',cap,flush=True)

def development_gate():
    records=[]
    for ds in DS:
        fit=read(O/'results'/f'fit_{ds}'/'results.json')['methods']
        by={x['model_name']:x for x in fit};base=by['gt10_hard'];multi=by['multi']
        dm=read(O/'models'/ds/'drift_match.json');aliases=dm['aliases']
        sm=aliases.get('single_matched','single_matched');mm=aliases.get('multi_matched','multi_matched')
        fit_gain=(multi['recall_at_10']-base['recall_at_10'])*100
        cost=(multi['mean_graph_ndc']/base['mean_graph_ndc']-1)*100
        matched_gain=(by[mm]['recall_at_10']-by[sm]['recall_at_10'])*100
        dev={}
        for split in ['cal','audit']:
            ms=read(O/'results'/f'{split}_{ds}'/'results.json')['methods']
            vals=[]
            for L in [64,128]:
                b=next(x for x in ms if x['model_name']=='gt10_hard' and x['L']==L and not x['configuration']['exact'])
                m=next(x for x in ms if x['model_name']=='multi' and x['L']==L and not x['configuration']['exact'])
                vals.append((m['recall_at_10']-b['recall_at_10'])*100)
            dev[split]=float(np.mean(vals))
        passes=dict(fit_effect=fit_gain>=.2-1e-12,fit_cost=cost<=1.,matched_effect=matched_gain>0.,cal_effect=dev['cal']>0.,audit_effect=dev['audit']>0.)
        records.append(dict(dataset=ds,fit_gain_pp=fit_gain,fit_graph_ndc_pct=cost,matched_multi_minus_single_pp=matched_gain,
            dev_mean_gain_pp=dev,conditions=passes,passed=all(passes.values()),fit_reference='GT10 hard',matched_methods=[sm,mm]))
    passed=all(r['passed'] for r in records)
    dump(O/'results/development_gate.json',dict(status='PASS_CONTINUATION_SIGNAL' if passed else 'STOP_FURTHER_MODEL_EXPANSION',datasets=records,
        formal_curves_still_required_by_user=True,additional_training_permitted_by_this_runner=False))
    print('DEVELOPMENT_GATE',json.dumps(records),flush=True)

if __name__=='__main__':
    assert read(O/'reviews/model_verification.json')['status']=='PASS'
    check_freeze(O/'models/frozen_before_development.json');check_freeze(O/'reviews/frozen_before_training.json')
    build=read(O/'bin/evaluate.build.json');assert build['exit_code']==0
    original=(E29/'src/evaluate.cpp').read_text()
    assert (O/'src/evaluate.cpp').read_text().replace('(reps==0 || reps==5)','(reps==0 || reps==3)')==original
    for n in ['benchmark_with_nsg.cpp','legacy_reference.cpp']:assert sha(O/'src'/n)==sha(E29/'src'/n)
    files=[O/'protocol.md',O/'bin/evaluate',O/'bin/evaluate.build.json']+[O/'src'/s for s in ['common.py','run_evaluation.py','verify_models.py','evaluate.cpp','benchmark_with_nsg.cpp','legacy_reference.cpp']]
    for ds in DS:
        files.append(E24/'inputs'/ds/'prepared.json')
        for p in formal_models(ds):
            files += [Path(p[k]) for k in ['W','mapping','tie_ids'] if k in p]
    freeze(O/'reviews/evaluation_start_freeze.json',files)
    dump(O/'reviews/evaluation_preflight.json',dict(status='PASS',five_repeat_only_source_change=True,threads=1,max_calls=NORMAL_CAP,new_models_frozen=True))
    for ds in DS:
        for stage,pts,split in [('fit',points(models(ds),[128]),'fit'),('cal',points(models(ds),[64,128]),'cal'),
                               ('audit',points(models(ds),[64,128])+points(models(ds),[128],exact=True),'audit')]:
            check_freeze(O/'reviews/evaluation_start_freeze.json');run(ds,stage,pts,split)
    development_gate()
    freeze(O/'models/frozen_before_validation.json',files+[O/'results/development_gate.json'])
    for ds in DS:
        check_freeze(O/'reviews/evaluation_start_freeze.json')
        run(ds,'validation',points(formal_models(ds),[64,128,256,400,800],components=True),'validation',5)
    jobs=read(O/'logs/evaluation_jobs.json');calls=sum(j['reserved_calls'] for j in jobs)
    assert len(jobs)==8 and calls<=NORMAL_CAP
    dump(O/'state.json',dict(status='EVALUATION_COMPLETE_ANALYSIS_PENDING',real_search_calls=calls,training_runs=4,heldout_access=False))
