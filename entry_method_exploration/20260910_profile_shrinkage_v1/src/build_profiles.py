"""Three locked normalized interpolations; no query labels or query data are used."""
import shutil
import time
import numpy as np
from common import RUN,DATASETS,ALPHAS,NAMES,read,dump,identity,sha,check_lock,update_state


def mix(w0,w1,alpha):
    assert w0.shape==w1.shape and np.isfinite(w0).all() and np.isfinite(w1).all()
    if alpha==0:return w0.copy()
    if alpha==1:return w1.copy()
    assert alpha in ALPHAS
    merged=(1-alpha)*w0.astype('float64')+alpha*w1.astype('float64')
    norm=np.linalg.norm(merged,axis=1)
    assert np.isfinite(norm).all() and np.all(norm>1e-12),'degenerate mixed profile; no silent fallback'
    return (merged/norm[:,None]).astype('<f4')


def selftest():
    w0=np.asarray([[1,0,0],[0,0,1]],dtype='<f4')
    w1=np.asarray([[0,1,0],[0,1,0]],dtype='<f4')
    assert np.array_equal(mix(w0,w1,0).view('<u4'),w0.view('<u4'))
    assert np.array_equal(mix(w0,w1,1).view('<u4'),w1.view('<u4'))
    assert np.allclose(mix(w0,w1,.25)[0],np.asarray([3,1,0])/np.sqrt(10),atol=3e-8)
    for alpha in ALPHAS:
        current=mix(w0,w1,alpha)
        assert np.allclose(np.linalg.norm(current,axis=1),1,atol=1e-7)
        assert np.allclose(current[0,1]/current[0,0],alpha/(1-alpha),rtol=1e-6)
    rejected=False
    try:mix(w0,-w0,.5)
    except AssertionError:rejected=True
    assert rejected
    return {'status':'PASS','bit_exact_endpoints':True,'analytical_intermediate_direction':True,
            'unit_norms':True,'antipodal_degeneracy_rejected':True}


def main():
    lock=check_lock();assert read(RUN/'bin/evaluate.build.json')['exit_code']==0
    assert not (RUN/'models/frozen_before_cal.json').exists()
    dump(RUN/'reviews/profile_math_selftest.json',selftest())
    files=[];costs=[]
    for ds in DATASETS:
        start=time.monotonic();endpoints=read(RUN/'inputs'/ds/'endpoints.json')
        p0=endpoints['A0'];p1=endpoints['A1'];h=p0['hub_count'];d=p0['dim']
        w0=np.fromfile(p0['W'],dtype='<f4').reshape(h,d);w1=np.fromfile(p1['W'],dtype='<f4').reshape(h,d)
        assert np.max(np.abs(np.linalg.norm(w0,axis=1)-1))<2e-6 and np.max(np.abs(np.linalg.norm(w1,axis=1)-1))<2e-6
        ids=RUN/'inputs'/ds/'hub_ids.i32'
        assert sha(ids)==sha(p0['mapping'])==sha(p1['mapping'])
        common={**p0,'mapping':str(ids),'tie_ids':str(ids)}
        common.pop('name',None);common.pop('family',None)
        profiles={};geometry=[]
        for name,alpha in [('fast20k',0.),*zip(NAMES,ALPHAS),('e24',1.)]:
            out=RUN/'models'/ds/name;out.mkdir(parents=True,exist_ok=False)
            w=mix(w0,w1,alpha)
            if alpha in [0,1]:
                shutil.copy2(p0['W'] if alpha==0 else p1['W'],out/'W.f32')
                assert sha(out/'W.f32')==sha(p0['W'] if alpha==0 else p1['W'])
            else:w.tofile(out/'W.f32')
            assert np.isfinite(w).all() and np.max(np.abs(np.linalg.norm(w,axis=1)-1))<2e-6
            norms=np.linalg.norm(w.astype('float64'),axis=1)
            base_norms=np.linalg.norm(w0.astype('float64'),axis=1)
            cosine=np.sum(w.astype('float64')*w0,axis=1)/(norms*base_norms)
            angle=np.arccos(np.clip(cosine,-1,1))*180/np.pi
            distance=np.linalg.norm(w.astype('float64')-w0,axis=1)
            unnorm=(1-alpha)*w0.astype('float64')+alpha*w1.astype('float64')
            formula=(1-alpha)**2*np.sum(w0.astype('float64')**2,axis=1)+alpha**2*np.sum(w1.astype('float64')**2,axis=1)+2*alpha*(1-alpha)*np.sum(w0.astype('float64')*w1,axis=1)
            assert np.max(np.abs(np.sum(unnorm**2,axis=1)-formula))<2e-15
            current={**common,'family':name,'model_name':name,'alpha':alpha,'W':str(out/'W.f32')}
            profiles[name]=current
            record={'dataset':ds,'name':name,'alpha':alpha,'W':identity(out/'W.f32'),
                'source_W0':identity(p0['W']),'source_W1':identity(p1['W']),
                'angle_degrees_from_A0_quantiles':np.quantile(angle,[0,.25,.5,.75,1]).tolist(),
                'max_score_shift_per_unit_query_bound_quantiles':np.quantile(distance,[0,.25,.5,.75,1]).tolist(),
                'mixed_unnormalized_norm_min':float(np.linalg.norm(unnorm,axis=1).min()),
                'stored_unit_norm_max_error':float(np.max(np.abs(norms-1))),
                'new_training_labels_used':False,'new_query_data_read':False}
            dump(out/'manifest.json',record);geometry.append(record);files.extend([out/'W.f32',out/'manifest.json'])
        dump(RUN/'models'/ds/'profiles.json',profiles);dump(RUN/'models'/ds/'geometry.json',geometry)
        files.extend([RUN/'models'/ds/'profiles.json',RUN/'models'/ds/'geometry.json'])
        costs.append({'dataset':ds,'construction_and_artifact_seconds':time.monotonic()-start,'new_alpha_profiles':3,'endpoint_bit_copies':2})
        files.extend([p for p in (RUN/'inputs'/ds).rglob('*') if p.is_file()])
    dump(RUN/'models/construction_costs.json',costs)
    files.extend([RUN/p for p in ['models/construction_costs.json','protocol.md','config.locked.json','reviews/protocol_lock.json',
        'reviews/protected_before.json','reviews/profile_math_selftest.json','bin/evaluate','bin/evaluate.build.json','src/build_profiles.py']])
    files.extend([p for p in (RUN/'src').iterdir() if p.suffix in ['.cpp','.hpp']])
    dump(RUN/'models/frozen_before_cal.json',{'status':'FROZEN_BEFORE_NEW_CAL_SEARCHES','frozen_unix':time.time(),
        'protocol_sha256':lock['protocol_sha256'],'files':[identity(p) for p in files],
        'new_profiles':6,'endpoint_copies':4,'new_query_or_GT_labels_used':False})
    update_state(status='PROFILES_FROZEN_BEFORE_CAL')
    print('ALL_ALPHA_PROFILES_FROZEN',flush=True)


if __name__=='__main__':main()
