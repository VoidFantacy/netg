from common import *
import copy
import numpy as np

def models(ds):
    return [policy(ds,'gt10_hard')]+[policy(ds,cell,O/'models'/ds/cell/'W.f32') for cell in CELLS]

def points(policies,ls,exact=False,components=False):
    result=[]
    for L in ls:
        for p in policies:
            m=copy.deepcopy(p)
            m.update(L=L,exact=exact,name=p['model_name']+('_exact' if exact else '_hnsw')+f'_L{L}',
                     component_wall=components and L==128 and p['model_name'] in ['gt10_hard']+CELLS)
            result.append(m)
    return result

def verify_outputs(dest,c,result):
    n=c['num_queries']
    gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
    rows=np.fromfile(c['row_ids'],np.int64)
    assert np.array_equal(rows,np.fromfile(dest/'row_ids.i64',np.int64))
    thread=read(dest/'thread_contract.json')
    assert thread['process_threads']==thread['actual_openmp_threads']==1 and thread['cpu']==15
    assert result['GT_opened_after_all_raw_search'] and result['threads']==1
    for m in result['methods']:
        d=dest/m['name']
        ids=np.fromfile(d/'ids.i32',np.int32).reshape(n,10)
        found=(ids[:,:,None]==gt[:,None,:]).any(1)
        assert (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
        hits=found.sum(1)
        assert np.array_equal(hits,np.fromfile(d/'hits.u8',np.uint8))
        assert np.array_equal((found*(1<<np.arange(10))).sum(1),np.fromfile(d/'hitmask.u16',np.uint16))
        assert int(hits.sum())==m['total_hits'] and abs(hits.mean()/10-m['recall_at_10'])<1e-12
        assert m['repeated_output_parity'] and m['original_kernel_parity_queries']==16
    dump(dest/'independent_verification.json',dict(status='PASS',points=len(result['methods']),query_outputs=n*len(result['methods']),GT_rescore_all=True,threads=1))

def run(ds,stage,methods,split,reps=0):
    assert shutil.disk_usage(O).free>10*(1<<30)
    used=sum(p.stat().st_size for p in O.rglob('*') if p.is_file())
    assert used+(128<<20)<1<<30
    c=read(O/'inputs'/ds/split/'config.json')
    c.update(methods=methods,timing_repeats=reps,dataset_order=DS.index(ds),threads=1,query_cpu=15)
    n=c['num_queries']
    cap=sum((7 if reps else 2)*n+16+(2*n if m.get('component_wall') else 0) for m in methods)
    c['real_call_cap']=cap
    dest=O/'results'/f'{stage}_{ds}'
    cfg=O/'inputs'/ds/f'eval_{stage}.json'
    assert not dest.exists() and not cfg.exists()
    dump(cfg,c)
    logpath=O/'logs/evaluation_jobs.json'
    jobs=read(logpath) if logpath.exists() else []
    assert sum(j['reserved_calls'] for j in jobs)+cap<=NORMAL_CAP
    assert sum(j.get('seconds',0) for j in jobs)<3600
    argv=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)]
    env=os.environ.copy()
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    rec=dict(dataset=ds,stage=stage,argv=argv,reserved_calls=cap,status='RUNNING',start=time.time(),config=identity(cfg),rss_peak_kib=0)
    jobs.append(rec);dump(logpath,jobs)
    with (O/'logs'/f'{ds}.{stage}.log').open('w') as log:
        proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(O/'state.json',dict(status=stage.upper()+'_RUNNING',dataset=ds,pid=proc.pid,heldout_access=False))
        try:
            while proc.poll() is None:
                if time.time()-rec['start']>1200:
                    raise RuntimeError('job wall limit')
                if time.time()-rec['start']+sum(j.get('seconds',0) for j in jobs)>3600:
                    raise RuntimeError('total query wall limit')
                status=Path(f'/proc/{proc.pid}/status')
                if status.exists():
                    for line in status.read_text().splitlines():
                        if line.startswith('VmRSS:'):
                            rec['rss_peak_kib']=max(rec['rss_peak_kib'],int(line.split()[1]))
                    if rec['rss_peak_kib']>40*(1<<20):
                        raise RuntimeError('RSS limit')
                try:proc.wait(timeout=2)
                except subprocess.TimeoutExpired:pass
            rc=proc.returncode
        except BaseException:
            proc.kill();proc.wait()
            rec.update(status='FAILED',seconds=time.time()-rec['start'],exit_code=proc.returncode)
            dump(logpath,jobs)
            raise
    rec.update(exit_code=rc,seconds=time.time()-rec['start'],status='COMPLETE' if rc==0 else 'FAILED')
    dump(logpath,jobs)
    assert rc==0,(ds,stage)
    result=read(dest/'results.json')
    assert result['physical_graph_calls']==cap
    verify_outputs(dest,c,result)
    assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<1<<30
    print(ds,stage,'COMPLETE',cap,flush=True)

if __name__=='__main__':
    assert read(O/'reviews/model_verification.json')['status']=='PASS'
    check_freeze(O/'models/frozen_before_development.json')
    files=[O/'protocol.md',O/'bin/evaluate']+[O/'src'/s for s in ['common.py','run_evaluation.py','verify_models.py']]
    files += [p for p in (O/'models').glob('*/*/W.f32')]
    for ds in DS:
        files += [Path(p['W']) for p in models(ds)]
        files += [Path(read(E24/'models'/ds/'selection.json')['selected_families'][f]['W']) for f in ['gt1_soft','gt10_soft']]
        files += [E28/'models'/ds/'mlp_r10/W.f32']
    freeze(O/'reviews/evaluation_start_freeze.json',sorted(set(files)))
    for ds in DS:
        for stage,pts,split in [
            ('fit',points(models(ds),[128]),'fit'),
            ('cal',points(models(ds),[64,128]),'cal'),
            ('audit',points(models(ds),[64,128])+points(models(ds),[128],exact=True),'audit')]:
            check_freeze(O/'reviews/evaluation_start_freeze.json')
            run(ds,stage,pts,split)
    freeze(O/'models/frozen_before_validation.json',sorted(set(files)))
    for ds in DS:
        check_freeze(O/'models/frozen_before_validation.json')
        old=read(E23/'inputs'/ds/'validation/config.json')
        fast=copy.deepcopy(next(m for m in old['methods'] if m['family']=='fast30k_3'))
        assert fast['hnsw_seed']==100 and fast['legacy_heap_order'] and not fast['canonical_entry_order']
        fast.update(model_name='fast30k',component_wall=False)
        selected=read(E24/'models'/ds/'selection.json')['selected_families']
        mods=[dict(name='nsg',model_name='nsg',family='nsg',seed=20260828,k=1),fast,policy(ds,'gt1_hard'),policy(ds,'gt10_hard')]
        mods += [policy(ds,f,selected[f]['W']) for f in ['gt1_soft','gt10_soft']]
        mods += [policy(ds,'e28_mlp',E28/'models'/ds/'mlp_r10/W.f32')]
        mods += [policy(ds,cell,O/'models'/ds/cell/'W.f32') for cell in CELLS]
        run(ds,'validation',points(mods,[64,128,256,400,800],components=True),'validation',3)
    jobs=read(O/'logs/evaluation_jobs.json')
    assert len(jobs)==8 and sum(j['reserved_calls'] for j in jobs)==NORMAL_CAP
    dump(O/'state.json',dict(status='EVALUATION_COMPLETE_ANALYSIS_PENDING',real_search_calls=NORMAL_CAP,training_runs=8,heldout_access=False))
