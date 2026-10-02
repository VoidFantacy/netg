"""Independent raw-result and deployable decision checks. Does not run searches."""
from pathlib import Path
import numpy as np
from common import read,dump

def arrays(folder,m,n):
    p=Path(folder)/m['name']
    return {'ids':np.fromfile(p/'ids.i32',dtype='<i4').reshape(n,10),
            'distances':np.fromfile(p/'distances.f32',dtype='<f4').reshape(n,10),
            'entries':np.fromfile(p/'entry_ids.i32',dtype='<i4').reshape(n,3),
            'hits':np.fromfile(p/'hits.u8',dtype='u1').astype('int16'),
            'mask':np.fromfile(p/'hitmask.u16',dtype='<u2'),
            'route_ndc':np.fromfile(p/'route_ndc.u32',dtype='<u4'),
            'graph_ndc':np.fromfile(p/'graph_ndc.u32',dtype='<u4'),
            'choose':np.fromfile(p/'choose_new.u8',dtype='u1'),
            'logit':np.fromfile(p/'logits.f64',dtype='<f8'),
            'feature_dots':np.fromfile(p/'feature_dots.u32',dtype='<u4'),
            'base_calls':np.fromfile(p/'base_route_calls.u32',dtype='<u4'),
            'new_calls':np.fromfile(p/'new_route_calls.u32',dtype='<u4')}

def predict(x,model):
    beta=np.asarray(model['beta']);z=np.full(len(x),model['bias'],dtype=np.float64)
    norm=np.clip((x[:,:len(beta)]-np.asarray(model['mean']))/np.asarray(model['scale']),-6,6)
    for j in range(len(beta)):z+=beta[j]*norm[:,j]
    return z,z>=model['threshold']

def verify_folder(folder):
    folder=Path(folder);c=read(folder/'config.json');r=read(folder/'results.json');n=c['num_queries']
    assert r['status']=='COMPLETE' and r['threads']==1 and r['GT_opened_after_all_raw_search']
    assert np.array_equal(np.fromfile(c['row_ids'],dtype='<i8'),np.fromfile(folder/'row_ids.i64',dtype='<i8'))
    gt=np.fromfile(c['gt_file'],dtype='<i8').reshape(n,100)[:,:10]
    data={};gate_checks=[]
    for m in r['methods']:
        a=arrays(folder,m,n);data[m['name']]=a
        assert np.isfinite(a['distances']).all() and (a['ids']>=0).all()
        assert np.all(np.diff(np.sort(a['ids'],axis=1),axis=1)>0)
        mask=np.zeros(n,dtype='<u2')
        for j in range(10):mask|=(a['ids']==gt[:,j,None]).any(axis=1).astype('<u2')<<j
        hits=np.asarray([int(v).bit_count() for v in mask],dtype='u1')
        assert np.array_equal(mask,a['mask']) and np.array_equal(hits,a['hits'])
        assert int(hits.sum())==m['total_hits'] and int((hits==0).sum())==m['failed_queries']
        assert abs(a['route_ndc'].mean()-m['mean_route_ndc'])<1e-9
        assert abs(a['graph_ndc'].mean()-m['mean_graph_ndc'])<1e-9
        if m['kind']!='nsg':
            assert (np.diff(np.sort(a['entries'],axis=1),axis=1)>0).all()
        if m['kind'] not in ['fast30k','nsg']:assert (np.diff(a['entries'],axis=1)>0).all()
        if r['timing_repeats']:
            assert len(m['qps_runs'])==3 and np.allclose(m['qps_runs'],n/np.asarray(m['end_to_end_seconds']),rtol=1e-12)
            assert m['qps']==float(np.median(m['qps_runs']))
    for m in r['methods']:
        if m['kind'] not in ['base_gate','dual_gate']:continue
        a=data[m['name']]
        bases=[x for x in r['methods'] if x['kind']=='fast20k' and x['L']==m['L']]
        news=[x for x in r['methods'] if x['kind']=='e24' and x['L']==m['L']]
        assert len(bases)==len(news)==1
        b=data[bases[0]['name']];v=data[news[0]['name']];choose=a['choose'].astype(bool)
        if m['configuration'].get('force') is not None:assert np.all(choose==bool(m['configuration']['force']))
        for key in ['ids','entries','hits','mask','graph_ndc']:
            expected=np.where(choose[:,None],v[key],b[key]) if a[key].ndim==2 else np.where(choose,v[key],b[key])
            assert np.array_equal(a[key],expected),(m['name'],key)
        expected=np.where(choose[:,None],v['distances'],b['distances'])
        assert np.array_equal(a['distances'].view('<u4'),expected.view('<u4'))
        if m['kind']=='base_gate':
            assert np.all(a['feature_dots']==3) and np.all(a['base_calls']==1) and np.array_equal(a['new_calls'],choose)
            expected_r=b['route_ndc']+np.where(choose,v['route_ndc'],0)+3
        else:
            assert np.all(a['feature_dots']==6) and np.all(a['base_calls']==1) and np.all(a['new_calls']==1)
            expected_r=b['route_ndc']+v['route_ndc']+6
        assert np.array_equal(a['route_ndc'],expected_r),(m['name'],'routing charge')
        gate_checks.append({'name':m['name'],'queries':n,'selected_policy_bits_and_graph_ndc':'PASS','all_route_and_feature_cost':'PASS'})
    features_check=None
    if (folder/'features.f64').exists():
        q=np.fromfile(c['queries_file'],dtype='<f4').reshape(n,c['dim'])
        x=np.fromfile(folder/'features.f64',dtype='<f8').reshape(n,13)
        shared=c['policies'];ids=np.fromfile(shared['A0']['mapping'],dtype='<i4');idx={int(v):i for i,v in enumerate(ids)}
        p0=np.fromfile(shared['A0']['W'],dtype='<f4').reshape(len(ids),c['dim']);p1=np.fromfile(shared['A1']['W'],dtype='<f4').reshape(len(ids),c['dim'])
        hub=np.fromfile(shared['hub_features'],dtype='<f8').reshape(len(ids),3)
        a0=np.fromfile(folder/'feature_base_entries.i32',dtype='<i4').reshape(n,3);a1=np.fromfile(folder/'feature_new_entries.i32',dtype='<i4').reshape(n,3)
        qnorm=np.linalg.norm(q.astype(np.float64),axis=1);calc=np.zeros_like(x);calc[:,0]=np.log1p(qnorm)
        i0=np.asarray([[idx[int(v)] for v in row] for row in a0]);i1=np.asarray([[idx[int(v)] for v in row] for row in a1])
        # Float64 scalar reference checks the feature definition independently of the SIMD reduction order.
        s0=np.sort(np.sum(q[:,None,:].astype('float64')*p0[i0].astype('float64'),axis=2)/np.maximum(qnorm[:,None],1e-12),axis=1)[:,::-1]
        s1=np.sort(np.sum(q[:,None,:].astype('float64')*p1[i1].astype('float64'),axis=2)/np.maximum(qnorm[:,None],1e-12),axis=1)[:,::-1]
        calc[:,1]=s0[:,0];calc[:,2]=s0[:,0]-s0[:,1];calc[:,3]=s0[:,0]-s0[:,2]
        calc[:,4]=hub[i0,0].mean(axis=1);calc[:,5]=hub[i0,0].min(axis=1);calc[:,6]=hub[i0,2].mean(axis=1)
        calc[:,7]=s1[:,0]-s0[:,0];calc[:,8]=s1[:,0]-s1[:,1];calc[:,9]=s1[:,0]-s1[:,2]
        calc[:,10]=hub[i1,1].mean(axis=1);calc[:,11]=hub[i1,1].min(axis=1)
        calc[:,12]=np.asarray([len(set(a)&set(b))/3 for a,b in zip(a0,a1)])
        errors=np.max(np.abs(calc-x),axis=0);assert np.all(errors<4e-6),errors
        for m in r['methods']:
            if m['kind'] in ['base_gate','dual_gate'] and 'model_path' in m['configuration']:
                model=read(m['configuration']['model_path']);z,choose=predict(x,model);a=data[m['name']]
                assert np.max(np.abs(z-a['logit']))<1e-11 and np.array_equal(choose,a['choose'])
        features_check={'status':'PASS','max_abs_error_by_feature':errors.tolist(),'independent_float64_definition':True,'rows':n}
    check={'status':'PASS','points':len(r['methods']),'independently_scored_outputs':n*len(r['methods']),
           'gate_checks':gate_checks,'feature_check':features_check}
    dump(folder/'independent_verification.json',check)
    return check
