import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,time
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;ROOT=R.parents[3]
E125=ROOT/'entry_method_exploration/20260922_until2200_improvement_v1/stages/e125_approximate_target_profiles_v1'
DS='webvid2_5m_light_v1';N=20000;M=2048
def ident(p):
    p=Path(p);return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def dump(p,x):
    with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def gaps(base,ids,h):
    target=unit(np.array(base[ids],dtype='f4'));result=[]
    for lo in range(0,len(target),4096):
        s=target[lo:lo+4096]@h.T;top=np.partition(s,-2,axis=1)[:,-2:];result.append((top.max(1)-top.min(1)).astype('f8'))
    return np.concatenate(result)
def cdf_quantile(label,paired,all_proxy):
    n,m=len(all_proxy),len(label);grid=np.unique(np.r_[label,all_proxy])
    c_all=np.searchsorted(np.sort(all_proxy),grid,side='right').astype('i8')
    c_y=np.searchsorted(np.sort(label),grid,side='right').astype('i8')
    c_z=np.searchsorted(np.sort(paired),grid,side='right').astype('i8')
    numerator=m*c_all+n*(c_y-c_z);residue=np.abs(2*numerator-n*m)
    pos=int(np.argmin(residue));temperature=max(float(grid[pos]),1e-4)
    return temperature,{'grid_n':len(grid),'selected_grid_index':pos,'selected_numerator':int(numerator[pos]),
        'integer_abs_twice_cdf_residual':int(residue[pos]),'denominator':n*m,
        'minimum_cdf':float(numerator.min()/(n*m)),'maximum_cdf':float(numerator.max()/(n*m)),
        'negative_jumps':int(np.sum(np.diff(numerator)<0)),'tied_minimizers':int(np.sum(residue==residue.min()))}
def main():
    assert json.loads((R.parent/'demand_qgt_full_build_v1/reviews/independent_audit.json').read_text())['status']=='PASS'
    start=time.perf_counter();(R/'results').mkdir();(R/'reviews').mkdir()
    config=json.loads((E125/'config.locked.json').read_text());c=config['datasets'][DS]['original'];d=c['dimension']
    hubfile=Path(c['anchor']['ids']);gtfile=Path(c['fit_source']['gt_file']);apfile=E125/'results'/DS/'labels/ids.i32'
    paths=[Path(__file__),R/'protocol.md',R/'theory.md',E125/'config.locked.json',hubfile,gtfile,apfile,R.parent/'partial_replacement_v1/results'/f'{DS}.npz']
    dump(R/'reviews/frozen.json',{'inputs':{str(p):ident(p) for p in paths},'unix':time.time(),'seed0':2026093002,'shuffled_seed':2026093006})
    base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    hubs=np.fromfile(hubfile,'<i4');h=unit(np.array(base[hubs],dtype='f4'))
    gt=np.fromfile(gtfile,'<i8').reshape(N,100)[:,0];approx=np.fromfile(apfile,'<i4').reshape(N,100)[:,0]
    y=gaps(base,gt,h);z=gaps(base,approx,h);prior=np.load(R.parent/'partial_replacement_v1/results'/f'{DS}.npz')
    assert np.array_equal(y,prior['gt1_gaps']);truth=max(float(np.median(y)),1e-4)
    shuffled=z[np.random.default_rng(2026093006).permutation(N)];allrecords=[];temps=[];rows_all=[]
    for rep in range(16):
        rows=np.random.default_rng(2026093002+1000*rep).permutation(N)[:M];assert np.array_equal(rows,prior['selected_rows'][rep])
        rect,rd=cdf_quantile(y[rows],z[rows],z);shuf,sd=cdf_quantile(y[rows],shuffled[rows],shuffled)
        values=[max(float(np.median(y[rows])),1e-4),max(float(np.median(z)),1e-4),rect,shuf]
        allrecords.append({'rep':rep,'seed':2026093002+1000*rep,'temperature':values,'RectifiedCDF':rd,'ShuffledRectifiedCDF':sd})
        temps.append(values);rows_all.append(rows)
    temps=np.array(temps);errors=temps-truth;names=['PilotMedian','ApproxMedian','RectifiedCDF','ShuffledRectifiedCDF'];metrics={}
    for j,name in enumerate(names):
        e=errors[:,j];metrics[name]={'MSE':float(np.mean(e**2)),'MAE':float(np.mean(np.abs(e))),'bias':float(np.mean(e)),
            'max_abs_error':float(np.max(np.abs(e))),'first8_MSE':float(np.mean(e[:8]**2)),'last8_MSE':float(np.mean(e[8:]**2)),
            'range':[float(temps[:,j].min()),float(temps[:,j].max())],'seed0':float(temps[0,j]),'seed0_relative_error':float(temps[0,j]/truth-1)}
    fixed=[]
    for label,proxy in [('paired',z),('shuffled',shuffled)]:
        iy=(y<=truth).astype('f8');iz=(proxy<=truth).astype('f8');r=iy-iz
        table=np.bincount((2*iy+iz).astype(int),minlength=4).reshape(2,2)
        vy=float(np.var(iy,ddof=1));vr=float(np.var(r,ddof=1));vp=float(np.var(iz,ddof=1));cov=float(np.cov(iy,iz,ddof=1)[0,1])
        fixed.append({'proxy':label,'table_true_rows_proxy_columns':table.tolist(),'true_CDF':float(iy.mean()),'proxy_CDF':float(iz.mean()),
            'residual_mean':float(r.mean()),'truth_indicator_variance':vy,'proxy_indicator_variance':vp,'indicator_covariance':cov,
            'residual_variance':vr,'CDF_variance_ratio':vr/vy,'CDF_design_variance':(1-M/N)*vr/M,
            'oracle_lambda_diagnostic':cov/vp,'gap_id_agreement':int(np.sum(gt==approx)) if label=='paired' else None})
    p=metrics['PilotMedian'];v=metrics['RectifiedCDF'];s=metrics['ShuffledRectifiedCDF']
    checks={'MSE_le_80pct_pilot':v['MSE']<=.8*p['MSE'],'first8_better':v['first8_MSE']<p['first8_MSE'],
        'last8_better':v['last8_MSE']<p['last8_MSE'],'better_than_shuffle':v['MSE']<s['MSE']}
    np.savez(R/'results/gaps_and_estimates.npz',exact=y,approx=z,shuffled=shuffled,selected_rows=np.array(rows_all,dtype='i4'),temperatures=temps)
    for path,value in json.loads((R/'reviews/frozen.json').read_text())['inputs'].items():assert ident(path)==value
    result={'status':'COMPUTED_PENDING_AUDIT','dataset':DS,'truth_temperature':truth,'methods':names,'metrics':metrics,'fixed_true_median_CDF':fixed,
        'all_replications':allrecords,'next_model_gate':checks,'next_model_gate_pass':all(checks.values()),'seconds':time.perf_counter()-start,
        'new_GT':0,'new_NSG':0,'new_ANN':0,'new_profiles':0,'new_graphs':0,'new_performance_points':0,'default_changed':False}
    assert result['seconds']<300;dump(R/'results/summary.json',result);print(json.dumps({k:result[k] for k in ['truth_temperature','metrics','fixed_true_median_CDF','next_model_gate','seconds']},indent=2),flush=True)
if __name__=='__main__':main()
