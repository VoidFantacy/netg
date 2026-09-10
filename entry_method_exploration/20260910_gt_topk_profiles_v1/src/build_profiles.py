"""Closed-form profiles from fit GT only, with a separate recovery-first stage."""
import argparse
import hashlib
import importlib.util
import time
from pathlib import Path
import numpy as np
from common import DATASETS, ROOT, RUN, check_lock, dump, identity, read

spec = importlib.util.spec_from_file_location('reference_fast', ROOT/'benches/run/build_fast_entry_variants.py')
reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)


def describe(x):
    a = np.asarray(x, dtype='float64')
    return {'min':float(a.min()), 'median':float(np.median(a)), 'mean':float(a.mean()),
            'p90':float(np.quantile(a,.9)), 'max':float(a.max())}


def profile_from_weights(a, q, raw):
    sums = raw.astype('float64') + a.T @ q.astype('float64')
    return (sums / np.maximum(np.linalg.norm(sums,axis=1,keepdims=True),1e-12)).astype('float32')


def support_stats(a):
    mass = a.sum(axis=0); squares = (a*a).sum(axis=0)
    ess = np.divide(mass*mass,squares,out=np.zeros_like(mass),where=squares>0)
    entropy = -(a*np.log(np.maximum(a,np.finfo('float64').tiny))).sum(axis=1)
    assert np.max(np.abs(a.sum(axis=1)-1)) < 1e-12 and a.min() >= 0
    return {'mass':mass, 'squared_mass':squares, 'ess':ess,
            'query_entropy':entropy, 'query_effective_hubs':np.exp(entropy),
            'query_max_weight':a.max(axis=1), 'query_inverse_concentration':1/(a*a).sum(axis=1)}


def save_model(dataset, name, family, kgt, temperature, a, p, seconds, numerical=None):
    folder = RUN/'models'/dataset/name; assert not folder.exists(); folder.mkdir(parents=True)
    assert np.isfinite(p).all()
    p.tofile(folder/'W.f32')
    stats = support_stats(a)
    np.savez_compressed(folder/'support.npz',**stats)
    # Per-hub/query statistics and the exact matrix digest are retained; dense weights
    # are reproducible from fit and deliberately not all materialized under the 2 GiB cap.
    assignment_digest=hashlib.sha256(memoryview(np.ascontiguousarray(a))).hexdigest()
    p0 = np.fromfile(RUN/'inputs'/dataset/'P0_reference.f32',dtype='<f4').reshape(p.shape)
    cosine = np.sum(p.astype('float64')*p0.astype('float64'),axis=1)
    rec = {'name':name,'family':family,'K_gt':kgt,'temperature':temperature,'W':str(folder/'W.f32'),
           'W_identity':identity(folder/'W.f32'),'assignments_sha256':assignment_digest,
           'assignments_shape':list(a.shape),'assignments_storage':'statistics and exact float64 digest; recomputable from fit',
           'profile_seconds':seconds,'support':{key:describe(value) for key,value in stats.items()},
           'hubs_with_positive_mass':int((stats['mass']>0).sum()),
           'prior_fraction':describe(1/(1+stats['mass'])),
           'cosine_to_P0':describe(np.clip(cosine,-1,1)),
           'max_abs_to_P0':float(np.abs(p-p0).max()),'numerical_control':numerical,
           'fit_only':True,'requires_search_labels':False,'requires_gradient_training':False}
    dump(folder/'manifest.json',rec)
    print(dataset,name,'BUILT',round(seconds,3),flush=True)
    return rec


def self_test():
    # These tests address weight conservation, GT rank averaging, ties and support degeneracy.
    raw=np.array([[1,0],[0,1],[-1,0]],dtype='float32')
    q=np.array([[1,0],[0,1],[0,0]],dtype='float32')
    a=np.array([[1,0,0],[.5,.5,0],[0,0,1]],dtype='float64')
    got=profile_from_weights(a,q,raw)
    sums=np.array([[2,.5],[0,1.5],[-1,0]])
    expected=sums/np.linalg.norm(sums,axis=1,keepdims=True)
    assert np.allclose(got,expected,atol=1e-7)
    stat=support_stats(a);assert np.allclose(stat['ess'],[1.8,1,1])
    scores=np.array([[0.,0.,-1.],[1e4,0,-1e4]],dtype='float64')
    ex=np.exp((scores-scores.max(axis=1,keepdims=True))/.01)
    probs=ex/ex.sum(axis=1,keepdims=True)
    assert np.isfinite(probs).all() and np.allclose(probs.sum(axis=1),1)
    assert np.argmax(scores,axis=1).tolist()==[0,0]
    votes=np.eye(3)[np.array([[0,1],[2,2]])].mean(axis=1)
    assert np.allclose(votes,[[.5,.5,0],[0,0,1]])
    dump(RUN/'reviews/profile_self_test.json',{'status':'PASS','weight_conservation':True,
          'GT_rank_average':True,'stable_softmax_extreme_values':True,'ties_lowest_column_ID':True,
          'zero_query_prior_preservation':True,'ESS_independent_example':True})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['recover','candidates'])
    args=parser.parse_args();lock=check_lock();self_test()
    if args.stage=='candidates':
        assert read(RUN/'reviews/recovery_gate.json')['status']=='PASS'
    for dataset in DATASETS:
        started=time.monotonic()
        inp=RUN/'inputs'/dataset;meta=read(inp/'prepared.json');d,h=meta['dim'],meta['H']
        qraw=np.fromfile(inp/'fit/queries.f32',dtype='<f4').reshape(20000,d)
        gt=np.fromfile(inp/'fit/gt.i64',dtype='<i8').reshape(20000,100)
        raw=np.fromfile(inp/'raw_hubs.f32',dtype='<f4').reshape(h,d)
        q=reference.normalize(qraw);hn=reference.normalize(raw)
        base,bd=reference.fvecs_memmap(Path(meta['base_file']));assert bd==d
        target=np.asarray(base[gt[:,0],1:],dtype='float32')
        if args.stage=='recover':
            t=time.monotonic()
            p,details=reference.build_gt_basin_prototypes(qraw,gt,target,raw,1.)
            ref=np.fromfile(inp/'P0_reference.f32',dtype='<f4').reshape(h,d)
            check={'bit_equal':bool(np.array_equal(p.view('u4'),ref.view('u4'))),
                   'max_abs':float(np.abs(p-ref).max()),'reference_details':details}
            dump(RUN/'reviews'/f'{dataset}_P0_numeric.json',check)
            assert check['bit_equal'],'P0 recovery differs; preserve evidence and repair before cal'
            a=np.zeros((20000,h),dtype='float64');tn=reference.normalize(target)
            for start in range(0,20000,4096):
                stop=min(start+4096,20000);s=tn[start:stop]@hn.T
                a[np.arange(start,stop),np.argmax(s,axis=1)]=1
            pd=profile_from_weights(a,q,hn)
            check['float64_reduction_max_abs']=float(np.abs(pd-p).max())
            assert check['float64_reduction_max_abs']<=2e-6
            save_model(dataset,'gt1_hard','gt1_hard',1,None,a,p,time.monotonic()-t,check)
            dump(RUN/'reviews'/f'{dataset}_P0_numeric.json',check)
        else:
            # Each K reuses scores only within that K, all ranks have exactly 1/K mass.
            records=[read(RUN/'models'/dataset/'gt1_hard/manifest.json')]
            build_cost=[]
            for kgt in [1,10]:
                t=time.monotonic()
                # A maximum 4096-target score batch; no N*K*H tensor is kept.
                names=([('gt10_hard',None)] if kgt==10 else [])+[(f'gt{kgt}_soft_t{j}',temp) for j,temp in enumerate(lock['temperatures'][dataset])]
                weights={name:np.zeros((20000,h),dtype='float64') for name,_ in names}
                ranks_changed=[];target_norms=[];near_ties=0
                for rank in range(kgt):
                    tv=np.asarray(base[gt[:,rank],1:],dtype='float32')
                    target_norms.extend(np.linalg.norm(tv,axis=1).astype('float64'))
                    tn=reference.normalize(tv)
                    for start in range(0,20000,4096):
                        stop=min(start+4096,20000);s=tn[start:stop]@hn.T
                        best=np.argmax(s,axis=1)
                        near_ties+=int((np.sum(s==s.max(axis=1,keepdims=True),axis=1)>1).sum())
                        for name,temp in names:
                            if temp is None:
                                weights[name][np.arange(start,stop),best]+=1/kgt
                            else:
                                x=s.astype('float64');x-=x.max(axis=1,keepdims=True);x/=temp
                                np.exp(x,out=x);x/=x.sum(axis=1,keepdims=True)
                                weights[name][start:stop]+=x/kgt
                assignment_seconds=time.monotonic()-t
                for name,temp in names:
                    pstart=time.monotonic();p=profile_from_weights(weights[name],q,hn)
                    seconds=time.monotonic()-pstart
                    rec=save_model(dataset,name,'gt10_hard' if temp is None else f'gt{kgt}_soft',kgt,temp,
                                   weights[name],p,seconds)
                    records.append(rec)
                build_cost.append({'K_gt':kgt,'shared_target_assignment_seconds':assignment_seconds,
                                   'targets':kgt*20000,'target_norms':describe(target_norms),'exact_highest_score_ties':near_ties})
            assert len(records)==8
            dump(RUN/'models'/dataset/'complete.json',{'status':'ALL_EIGHT_PROFILES_BUILT_BEFORE_CAL',
                 'models':records,'total_stage_seconds':time.monotonic()-started,'shared_assignment_costs':build_cost,
                 'raw_hub_norms':describe(np.linalg.norm(raw,axis=1)),
                 'raw_query_norms':describe(np.linalg.norm(qraw,axis=1)),
                 'zero_queries':int((np.linalg.norm(qraw,axis=1)==0).sum()),
                 'protocol_sha256':lock['protocol_sha256']})
    print(args.stage.upper()+'_BUILD_COMPLETE',flush=True)


if __name__=='__main__':
    main()
