from common import *
import copy
import numpy as np

DEPLOY_CAP=800000
def policies(ds):
    fixed=read(E28/'inputs'/ds/'propose.json');hard=copy.deepcopy(fixed['policies'][1]);result=[hard]
    if ds==DS[0]:
        soft=copy.deepcopy(hard);soft.update(name='gt10_soft',model_name='gt10_soft',W=str(E24/'models'/ds/'gt10_soft/W.f32'));result.append(soft)
    for cell in CELLS:
        p=copy.deepcopy(hard);p.update(name=cell,model_name=cell,family='c8',W=str(O/'models'/ds/cell/'W.f32'),c8_anchor=fixed['anchor'],c8_policies=fixed['policies'])
        result.append(p)
    return result

def verify_outputs(dest,c,result):
    n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
    assert np.array_equal(np.fromfile(c['row_ids'],np.int64),np.fromfile(dest/'row_ids.i64',np.int64))
    thread=read(dest/'thread_contract.json');assert thread['process_threads']==thread['actual_openmp_threads']==1 and thread['cpu']==15
    assert result['GT_opened_after_all_raw_search'] and result['threads']==1
    for m in result['methods']:
        d=dest/m['name'];ids=np.fromfile(d/'ids.i32',np.int32).reshape(n,10)
        assert (ids>=0).all() and (ids<c['base_count']).all() and (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
        found=(ids[:,:,None]==gt[:,None,:]).any(1);hits=found.sum(1)
        assert np.array_equal(hits,np.fromfile(d/'hits.u8',np.uint8))
        assert np.array_equal((found*(1<<np.arange(10))).sum(1),np.fromfile(d/'hitmask.u16',np.uint16))
        assert int(hits.sum())==m['total_hits'] and abs(hits.mean()/10-m['recall_at_10'])<1e-12
        assert m['repeated_output_parity'] and m['original_kernel_parity_queries']==16
        gn=np.fromfile(d/'graph_ndc.u32',np.uint32);rn=np.fromfile(d/'route_ndc.u32',np.uint32)
        assert abs(gn.mean()-m['mean_graph_ndc'])<1e-10 and abs(rn.mean()-m['mean_route_ndc'])<1e-10
        assert abs(gn.mean()+rn.mean()-m['mean_total_ndc'])<1e-9
        if m['family']=='c8':
            candidates=np.fromfile(d/'candidates.i32',np.int32).reshape(n,8)
            assert (np.diff(candidates,axis=1)>0).all()
            slot=np.fromfile(d/'action_slots.i32',np.int32);assert ((slot>=0)&(slot<56)).all()
            mapping=np.fromfile(m['configuration']['mapping'],np.int32)
            import itertools
            triple=candidates[np.arange(n)[:,None],np.array(list(itertools.combinations(range(8),3)))[slot]]
            assert np.array_equal(mapping[triple],np.fromfile(d/'entry_ids.i32',np.int32).reshape(n,3))
            assert (rn>=c['hub_count']+8).all()
            if c['split']=='fit':
                cached=np.load(O/'results'/c['dataset']/(m['model_name']+'.npz'))
                assert np.array_equal(slot,cached['slot'])
                assert np.array_equal(hits,cached['hits']) and np.array_equal(gn,cached['ndc'])
                expected=np.fromfile(E28/'inputs'/c['dataset']/'proposals/candidates.i32',np.int32).reshape(n,8)
                assert np.array_equal(candidates,expected)
        if c['timing_repeats']:
            qps=np.array(m['qps_runs']);seconds=np.array(m['end_to_end_seconds'])
            assert len(qps)==len(seconds)==5 and np.allclose(qps,n/seconds,rtol=1e-12)
            assert abs(m['qps']-np.median(qps))<1e-8
        else:assert m['qps'] is None and not m['qps_runs']
    dump(dest/'independent_verification.json',dict(status='PASS',points=len(result['methods']),query_outputs=n*len(result['methods']),GT_rescore_all=True,
        fit_cache_parity=c['split']=='fit',threads=1))

def stage_config(ds,split,reps=0):
    source=O/'inputs'/ds/'fit/config.json' if split=='fit' else E30/'inputs'/ds/split/'config.json'
    c=read(source);c['base_count']=read(E24/'inputs'/ds/'prepared.json')['base_rows']
    methods=[]
    for L in ([64,128,256,400,800] if reps else [128]):
        for p in policies(ds):
            m=copy.deepcopy(p);m.update(L=L,name=p['model_name']+f'_L{L}',component_wall=False);methods.append(m)
    c.update(methods=methods,timing_repeats=reps,dataset_order=DS.index(ds),threads=1,query_cpu=15,protocol_sha256=sha(O/'protocol.md'))
    c['real_call_cap']=sum(((reps+2) if reps else 2)*c['num_queries']+16 for m in methods)
    return c

def run(c):
    assert read(O/'results/cache_gate.json')['status']=='PASS_REAL_DEVELOPMENT_ALLOWED'
    ds,stage=c['dataset'],c['split'];dest=O/'results'/f'{stage}_{ds}';cfg=O/'inputs'/ds/f'eval_{stage}.json'
    assert not dest.exists() and not cfg.exists()
    assert shutil.disk_usage(O).free>10*(1<<30)
    dump(cfg,c);logpath=O/'logs/evaluation_jobs.json';jobs=read(logpath) if logpath.exists() else []
    cap=c['real_call_cap'];assert sum(x['reserved_calls'] for x in jobs)+cap<=DEPLOY_CAP
    used=sum(x.get('seconds',0) for x in jobs);assert used<5400
    argv=['taskset','-c','15',str(O/'bin/evaluate'),str(cfg),str(dest)]
    env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
    rec=dict(dataset=ds,stage=stage,argv=argv,reserved_calls=cap,status='RUNNING',start=time.time(),config=identity(cfg),rss_peak_kib=0)
    jobs.append(rec);dump(logpath,jobs)
    with (O/'logs'/f'{ds}.{stage}.log').open('x') as log:
        proc=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env)
        dump(O/'state.json',dict(status=stage.upper()+'_RUNNING',dataset=ds,pid=proc.pid,training_runs=4,heldout_access=False))
        try:
            while proc.poll() is None:
                elapsed=time.time()-rec['start'];assert elapsed<min(2000,5400-used),'evaluation time cap'
                assert shutil.disk_usage(O).free>10*(1<<30)
                status=Path('/proc')/str(proc.pid)/'status'
                if status.exists():
                    for line in status.read_text().splitlines():
                        if line.startswith('VmRSS:'):rec['rss_peak_kib']=max(rec['rss_peak_kib'],int(line.split()[1]));assert rec['rss_peak_kib']<100*(1<<20)
                time.sleep(.5)
            assert proc.returncode==0,'evaluation failed; see log'
        except BaseException:
            if proc.poll() is None:proc.terminate();proc.wait(timeout=5)
            rec.update(status='FAILED',seconds=time.time()-rec['start'],exit_code=proc.returncode);dump(logpath,jobs);raise
    rec.update(status='COMPLETE',seconds=time.time()-rec['start'],exit_code=proc.returncode);dump(logpath,jobs)
    result=read(dest/'results.json');assert result['physical_graph_calls']==cap
    verify_outputs(dest,c,result);print('DEPLOYMENT_JOB_PASS',ds,stage,cap,flush=True);return result
