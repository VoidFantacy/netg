import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
os.sched_setaffinity(0,range(8))
import hashlib,itertools,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;ROOT=R.parents[3];DS='webvid2_5m_light_v1'
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def main():
    start=time.perf_counter();summary=json.loads((R/'results/summary.json').read_text());a=np.load(R/'results/gaps_and_estimates.npz')
    y,z,shuf=a['exact'],a['approx'],a['shuffled'];n=len(y);m=2048
    assert np.array_equal(shuf,z[np.random.default_rng(2026093006).permutation(n)])
    assert np.median(y)==summary['truth_temperature'];scalar_checks=0
    for rep,record in enumerate(summary['all_replications']):
        rows=a['selected_rows'][rep];assert np.array_equal(rows,np.random.default_rng(2026093002+1000*rep).permutation(n)[:m])
        estimates=[max(float(np.median(y[rows])),1e-4),max(float(np.median(z)),1e-4)]
        for name,proxy in [('RectifiedCDF',z),('ShuffledRectifiedCDF',shuf)]:
            # Independent signed point-mass accumulation; no searchsorted ECDF counting.
            grid,inv=np.unique(np.r_[proxy,y[rows],proxy[rows]],return_inverse=True)
            mass=np.zeros(len(grid),dtype='i8');np.add.at(mass,inv[:n],m);np.add.at(mass,inv[n:n+m],n);np.add.at(mass,inv[n+m:],-n)
            numer=np.cumsum(mass);residue=np.abs(2*numer-n*m);k=int(np.argmin(residue));estimate=max(float(grid[k]),1e-4);estimates.append(estimate)
            rec=record[name];assert k==rec['selected_grid_index'] and len(grid)==rec['grid_n']
            assert numer[k]==rec['selected_numerator'] and residue[k]==rec['integer_abs_twice_cdf_residual']
            assert int(np.sum(np.diff(numer)<0))==rec['negative_jumps'] and int(np.sum(residue==residue.min()))==rec['tied_minimizers']
            for j in np.unique(np.r_[np.linspace(0,len(grid)-1,9,dtype=int),k]):
                t=grid[j];direct=m*int(np.count_nonzero(proxy<=t))+n*(int(np.count_nonzero(y[rows]<=t))-int(np.count_nonzero(proxy[rows]<=t)))
                assert direct==numer[j];scalar_checks+=1
        assert np.array_equal(estimates,a['temperatures'][rep]) and estimates==record['temperature']
    for j,name in enumerate(summary['methods']):
        error=a['temperatures'][:,j]-summary['truth_temperature'];rec=summary['metrics'][name]
        for key,val in [('MSE',float(sum(e*e for e in error)/16)),('MAE',float(sum(abs(e) for e in error)/16)),
            ('bias',float(sum(error)/16)),('first8_MSE',float(sum(e*e for e in error[:8])/8)),('last8_MSE',float(sum(e*e for e in error[8:])/8))]:
            np.testing.assert_allclose(val,rec[key],rtol=1e-13,atol=1e-20)
    # Exact finite-population enumeration checks unbiasedness and the finite-population factor.
    toy_y=np.array([.1,.2,.4,.6,.8,1.]);toy_z=np.array([.05,.3,.35,.7,.75,.9]);subsets=list(itertools.combinations(range(6),3));toy_checks=0
    for t in [.15,.35,.5,.75,.85,.95]:
        iy=(toy_y<=t).astype(float);iz=(toy_z<=t).astype(float);residual=iy-iz
        estimates=np.array([iz.mean()+residual[list(s)].mean() for s in subsets])
        np.testing.assert_allclose(estimates.mean(),iy.mean(),atol=1e-15)
        np.testing.assert_allclose(estimates.var(),(1-3/6)*residual.var(ddof=1)/3,atol=1e-15);toy_checks+=len(subsets)
    for rec,proxy in zip(summary['fixed_true_median_CDF'],[z,shuf]):
        t=summary['truth_temperature'];table=np.zeros((2,2),dtype='i8')
        for v,p in zip(y,proxy):table[int(v<=t),int(p<=t)]+=1
        assert table.tolist()==rec['table_true_rows_proxy_columns'];counts=table.ravel();vals=np.array([0.,-1.,1.,0.]);mu=float(np.dot(counts,vals)/n)
        variance=float(np.dot(counts,(vals-mu)**2)/(n-1));np.testing.assert_allclose(variance,rec['residual_variance'],rtol=1e-14)
    p=summary['metrics']['PilotMedian'];v=summary['metrics']['RectifiedCDF'];s=summary['metrics']['ShuffledRectifiedCDF']
    checks=[v['MSE']<=.8*p['MSE'],v['first8_MSE']<p['first8_MSE'],v['last8_MSE']<p['last8_MSE'],v['MSE']<s['MSE']]
    assert checks==list(summary['next_model_gate'].values()) and all(checks)==summary['next_model_gate_pass']
    # Approximate gap extraction independently uses a full score sort in the original block shapes.
    old=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
    c=json.loads((old/'config.locked.json').read_text())['datasets'][DS]['original'];d=c['dimension'];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    h=np.array(base[np.fromfile(c['anchor']['ids'],'<i4')],dtype='f4');h/=np.maximum(np.linalg.norm(h,axis=1,keepdims=True),1e-12)
    ap=np.fromfile(old/'results'/DS/'labels/ids.i32','<i4').reshape(n,100)[:,0];target=np.array(base[ap],dtype='f4');target/=np.maximum(np.linalg.norm(target,axis=1,keepdims=True),1e-12)
    for lo in range(0,n,4096):
        scores=np.sort(target[lo:lo+4096]@h.T,axis=1);gap=(scores[:,-1]-scores[:,-2]).astype('f8');assert np.array_equal(gap,z[lo:lo+4096])
    identities=0
    for path,v in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert ident(path)==v;identities+=1
    result={'status':'PASS','seconds':time.perf_counter()-start,'identities':identities,'signed_event_CDF_estimates':32,'scalar_CDF_checks':scalar_checks,
        'finite_population_subset_threshold_checks':toy_checks,'independent_fullsort_proxy_gaps':n,'source':ident(__file__),'new_GT':0,'new_NSG':0,'new_ANN':0}
    with (R/'reviews/independent_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(result,flush=True)
if __name__=='__main__':main()
