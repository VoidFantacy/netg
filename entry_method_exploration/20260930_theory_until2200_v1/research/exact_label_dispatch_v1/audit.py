import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
    os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits

R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())

def ident(path):
    p=Path(path);h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(16<<20),b''):h.update(block)
    return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}

def load(ds,setting):
    p=R/'results'/ds;n,k=C['n'],setting['k'];name=setting['name']
    return np.fromfile(p/(name+'.ids.i64'),'<i8').reshape(n,k),np.fromfile(p/(name+'.dist.f32'),'<f4').reshape(n,k)

def full_top11(base,query):
    count=len(query);best=np.full((count,11),-np.inf);ids=np.full((count,11),-1,dtype='i8')
    for lo in range(0,len(base),65536):
        score=query@np.array(base[lo:lo+65536],dtype='f8').T
        take=np.argpartition(score,-11,axis=1)[:,-11:]
        vals=np.take_along_axis(score,take,axis=1);take+=lo
        vv=np.concatenate([best,vals],axis=1);ii=np.concatenate([ids,take],axis=1)
        choose=np.argpartition(vv,-11,axis=1)[:,-11:]
        best=np.take_along_axis(vv,choose,axis=1);ids=np.take_along_axis(ii,choose,axis=1)
    order=np.lexsort((ids,-best),axis=1)
    return np.take_along_axis(ids,order,axis=1),np.take_along_axis(best,order,axis=1)

def main():
    start=time.perf_counter();s=json.loads((R/'results/summary.json').read_text())
    frozen=json.loads((R/'reviews/frozen.json').read_text());expected_calls=0;records={};checks=0
    for group in ['files','libraries']:
        for p,v in frozen[group].items():assert ident(p)==v
    progress=json.loads((R/'reviews/progress.json').read_text())
    assert progress['completed_exact_queries']==progress['reserved_exact_queries']==C['exact_query_cap']
    plans={}
    # Determine the complete audit query sets before starting any extra full-base pass.
    for ds,c in C['datasets'].items():
        original,_=load(ds,C['configs'][0]);changed=np.zeros(C['n'],dtype=bool)
        for setting in C['configs']:
            ids,_=load(ds,setting);changed |= np.any(ids[:,:10]!=original[:,:10],axis=1)
        selected=np.union1d(np.arange(0,C['n'],C['n']//16),np.flatnonzero(changed)).astype('i4')
        assert len(selected)<=C['float64_check_cap_per_dataset'],'STOP: prefix disagreement audit exceeds predeclared cap'
        plans[ds]={'selected':selected,'changed':changed}
    with threadpool_limits(8):
      for ds,c in C['datasets'].items():
        n,d=C['n'],c['dimension'];record=s['datasets'][ds];path=R/'results'/ds
        original,original_dist=load(ds,C['configs'][0]);loaded={x['name']:load(ds,x) for x in C['configs']}
        old=np.memmap(Path(c['output'])/'fit20000.ids.i64','<i8',mode='r',shape=(c['fit_n'],100))[:n]
        oldd=np.memmap(Path(c['output'])/'fit20000.dist.f32','<f4',mode='r',shape=(c['fit_n'],100))[:n]
        np.testing.assert_array_equal(original,old);np.testing.assert_array_equal(original_dist.view('u4'),oldd.view('u4'))
        assert record['actual_affinity']==list(range(8)) and record['faiss_threads']==8
        assert all(pool['num_threads']<=8 for pool in record['threadpools'])
        times={name:[] for name in loaded};hashes={}
        for setting in C['configs']:
            name=setting['name'];ii,dd=loaded[name]
            hashes[name]=(hashlib.sha256(ii.tobytes()).hexdigest(),hashlib.sha256(dd.tobytes()).hexdigest())
            warm=record['warm'][name];assert hashes[name]==(warm['ids_sha256'],warm['dist_sha256'])
            expected_calls+=n
        for r,round_record in enumerate(record['rounds']):
            order=[C['configs'][(i+r)%4]['name'] for i in range(4)]
            assert round_record['order']==order and [x['name'] for x in round_record['runs']]==order
            for run in round_record['runs']:
                name=run['name'];assert hashes[name]==(run['ids_sha256'],run['dist_sha256']);assert run['seconds']>0
                times[name].append(run['seconds']);expected_calls+=n
        for item in record['comparisons']:
            name=item['name'];ii,dd=loaded[name];prefix=ii[:,:10]
            assert item['timed_seconds']==times[name] and len(times[name])==3
            assert item['mean_search_loop_seconds']==float(np.mean(times[name]))
            assert item['mean_seconds_ratio_to_original']==float(np.mean(times[name])/np.mean(times['Batch256K100']))
            bad=prefix!=original[:,:10]
            assert item['first10_order_changed_queries']==int(np.any(bad,axis=1).sum())
            assert item['first10_order_changed_cells']==int(bad.sum())
            assert item['first10_set_changed_queries']==int(np.any(np.sort(prefix,axis=1)!=np.sort(original[:,:10],axis=1),axis=1).sum())
            assert item['first10_distance_bit_changed_cells']==int(np.sum(dd[:,:10].view('u4')!=original_dist[:,:10].view('u4')))
        query=np.memmap(c['fit_queries'],'<f4',mode='r',shape=(c['fit_n'],d))[:n].astype('f8')
        raw=np.memmap(c['base'],'<f4',mode='r',shape=(c['base_n'],d+1));base=raw[:,1:]
        distances={}
        for name,(ii,dd) in loaded.items():
            # All consumed distance cells, independently from the saved search outputs.
            vector=base[ii[:,:10]].astype('f8');actual=np.einsum('nkd,nd->nk',vector,query)
            np.testing.assert_allclose(actual,dd[:,:10],rtol=1e-5,atol=3e-5)
            distances[name]=actual;del vector
        selected=plans[ds]['selected'];t=time.perf_counter();bestids,best=full_top11(base,query[selected]);full_seconds=time.perf_counter()-t
        qchecks=[]
        for j,qi in enumerate(selected):
            threshold=float(best[j,9]);tol=2e-5*max(1.,abs(threshold));details={}
            for name,(ii,dd) in loaded.items():
                actual=distances[name][qi]
                assert actual.min()>=threshold-tol and actual[0]>=best[j,0]-tol
                details[name]={'consumed_ids':ii[qi,:10].tolist(),'float64_scores':actual.tolist(),
                    'same_first10_as_float64_representation':bool(np.array_equal(ii[qi,:10],bestids[j,:10])),
                    'top10_threshold_deficit':float(max(0.,threshold-actual.min()))}
            qchecks.append({'query_row':int(qi),'selected_for_prefix_disagreement':bool(plans[ds]['changed'][qi]),
                'float64_top11_ids':bestids[j].tolist(),'float64_top11_scores':best[j].tolist(),
                'rank10_11_gap':float(best[j,9]-best[j,10]),'numerical_threshold_tolerance':tol,'configs':details})
        checks+=len(selected);main=next(x for x in record['comparisons'] if x['name']=='Batch1024K100')
        records[ds]={'checks':qchecks,'independent_float64_full_base_queries':len(selected),'full_base_seconds':full_seconds,
            'prefix_changed_query_union':int(plans[ds]['changed'].sum()),'main_comparison_ratio':main['mean_seconds_ratio_to_original'],
            'main_each_round_faster':all(a<b for a,b in zip(times['Batch1024K100'],times['Batch256K100'])),
            'sample_consumed_ID_identity':main['first10_order_changed_queries']==0,
            'all_consumed_distance_cells_checked':n*10*4}
        print(ds,'AUDIT PASS',len(selected),'full-base queries',flush=True)
        del raw,base,query,distances,loaded,old,oldd
    assert expected_calls==s['new_exact_GT_queries']==C['exact_query_cap'] and checks<=128
    web=records['webvid2_5m_light_v1'];yan=records['yandex_t2i_official10M_ip_v1']
    gate={'Y_all_three_rounds_faster':yan['main_each_round_faster'],'Y_mean_at_least_10_percent_lower':yan['main_comparison_ratio']<=.90,
          'Web_mean_no_more_than_5_percent_slower':web['main_comparison_ratio']<=1.05}
    for group in ['files','libraries']:
        for p,v in frozen[group].items():assert ident(p)==v
    result={'status':'PASS','seconds':time.perf_counter()-start,'datasets':records,'additional_full_base_float64_checks':checks,
        'main_cost_gate':gate,'main_cost_gate_pass':all(gate.values()),
        'both_sample_consumed_ID_identity':web['sample_consumed_ID_identity'] and yan['sample_consumed_ID_identity'],
        'scope':'separate implementation by same agent; float64 top11 may contain an arbitrary valid subset when exactly tied at its boundary; tolerance is not ID parity',
        'new_exact_GT_labels':0,'new_NSG':0,'new_ANN':0,'default_changed':False}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print('ALL AUDITS PASS',result['seconds'],'COST GATE',result['main_cost_gate_pass'],flush=True)

if __name__=='__main__':main()
