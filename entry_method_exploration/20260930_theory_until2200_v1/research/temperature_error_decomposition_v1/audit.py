import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,{14})
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;P=R.parent/'hybrid_temperature_factorial_v1';T=R.parent/'temperature_full_build_v1';DS='webvid2_5m_light_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    start=time.perf_counter();s=json.loads((R/'results/summary.json').read_text());a=np.load(R/'results/decomposition.npz')
    truth=np.load(R.parent/'directional_error_v1/results'/f'{DS}.npz')['v'];fixed=np.load(P/'models'/DS/'HybridFixedTemperature/construction.npz')['v'];n,d=truth.shape
    models={'HybridPilotTemperature':np.load(P/'models'/DS/'HybridPilotTemperature/construction.npz')['v']}
    for name in ['HybridRectifiedCDF','HybridApproxMedian']:models[name]=np.fromfile(T/'results'/DS/name/'v.f64','<f8').reshape(n,d)
    maxerr=0.;checks=0
    for name,v in models.items():
        expected={key:np.zeros((4,n)) for key in ['raw','scaled','tangent']}
        for h in range(n):
            norm=float(np.sqrt(np.dot(truth[h],truth[h])));p=truth[h]/norm;x=fixed[h]-truth[h];y=v[h]-fixed[h]
            for key,xx,yy in [('raw',x,y),('scaled',x/norm,y/norm),('tangent',(x-np.dot(x,p)*p)/norm,(y-np.dot(y,p)*p)/norm)]:
                vals=[np.dot(xx,xx),np.dot(yy,yy),2*np.dot(xx,yy),np.dot(xx+yy,xx+yy)];expected[key][:,h]=vals;checks+=1
            fp=fixed[h]/np.sqrt(np.dot(fixed[h],fixed[h]));dv=a['dV_dlogT'][h];dw=(dv-np.dot(dv,fp)*fp)/np.linalg.norm(fixed[h])
            np.testing.assert_allclose(dw,a['dW_dlogT'][h],rtol=1e-12,atol=1e-13);assert abs(np.dot(dw,fp))<1e-12
        for key,arr in expected.items():
            maxerr=max(maxerr,float(np.max(np.abs(arr-a[f'{name}_{key}_energies']))));np.testing.assert_allclose(arr,a[f'{name}_{key}_energies'],rtol=2e-12,atol=1e-10)
            for i,term in enumerate(['label','temperature','cross','total']):np.testing.assert_allclose(arr[i].sum(),s['models'][name][key][term],rtol=1e-12,atol=1e-10)
    # Finite differences independently verify both softmax temperature and normalized resultant derivatives.
    rng=np.random.default_rng(2026093012);scores=rng.uniform(-.05,.05,(7,5));query=rng.normal(size=(7,4));query/=np.linalg.norm(query,axis=1,keepdims=True)
    prior=rng.normal(size=(5,4));prior/=np.linalg.norm(prior,axis=1,keepdims=True);tau=float(np.log(.02));eps=1e-6
    def evaluate(t):
        logits=scores/np.exp(t);logits-=logits.max(1,keepdims=True);p=np.exp(logits);p/=p.sum(1,keepdims=True);v=prior+p.T@query;w=v/np.linalg.norm(v,axis=1,keepdims=True);return p,v,w
    prob,v,w=evaluate(tau);plus=evaluate(tau+eps);minus=evaluate(tau-eps);logits=scores/np.exp(tau)
    dp=prob*(np.sum(prob*logits,axis=1,keepdims=True)-logits);dv=dp.T@query;dw=(dv-np.sum(dv*w,axis=1,keepdims=True)*w)/np.linalg.norm(v,axis=1,keepdims=True)
    errors=[]
    for j,derivative in enumerate([dp,dv,dw]):
        fd=(plus[j]-minus[j])/(2*eps);errors.append(float(np.max(np.abs(fd-derivative))));np.testing.assert_allclose(fd,derivative,rtol=1e-6,atol=1e-8)
    assert np.max(np.abs(dp).sum(1)-(scores.max(1)-scores.min(1))/(2*np.exp(tau)))<=1e-12
    identities=0
    for path,value in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert ident(path)==value;identities+=1
    result={'status':'PASS','seconds':time.perf_counter()-start,'identities':identities,'scalar_hub_measure_checks':checks,'max_energy_difference':maxerr,
        'finite_difference_max_abs_errors':errors,'source':ident(__file__),'new_GT':0,'new_NSG':0,'new_ANN':0,'new_profiles':0}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(result,flush=True)
if __name__=='__main__':main()
