import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def gaps(base,ids,h):
    target=unit(np.array(base[ids],dtype='f4'));res=[]
    for lo in range(0,len(ids),4096):
        s=target[lo:lo+4096]@h.T;top=np.partition(s,-2,axis=1)[:,-2:];res.append((top.max(1)-top.min(1)).astype('f8'))
    return np.concatenate(res)
def temperature(label,paired,all_proxy,mode):
    if mode=='HybridApproxMedian':return max(float(np.median(all_proxy)),1e-4),None
    assert mode=='HybridRectifiedCDF';n=len(all_proxy);m=len(label);grid=np.unique(np.r_[label,all_proxy])
    countall=np.searchsorted(np.sort(all_proxy),grid,side='right').astype('i8');countlabel=np.searchsorted(np.sort(label),grid,side='right').astype('i8')
    countpaired=np.searchsorted(np.sort(paired),grid,side='right').astype('i8');numer=m*countall+n*(countlabel-countpaired)
    residue=np.abs(2*numer-n*m);i=int(np.argmin(residue))
    return max(float(grid[i]),1e-4),{'grid_n':len(grid),'grid_index':i,'numerator':int(numer[i]),'denominator':n*m,'abs_twice_residual':int(residue[i])}
def assignment(base,targets,h,temp):
    a=np.zeros((len(targets),len(h)))
    for rank in range(10):
        z=unit(np.array(base[targets[:,rank]],dtype='f4'))
        for lo in range(0,len(targets),4096):
            hi=min(lo+4096,len(targets));s=(z[lo:hi]@h.T).astype('f8');s-=s.max(1,keepdims=True);s/=temp;np.exp(s,out=s);s/=s.sum(1,keepdims=True);a[lo:hi]+=s/10
    np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13);return a
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());mode=sys.argv[2];out=Path(c['output']);dest=out/mode;dest.mkdir()
    n,d=c['fit_n'],c['dimension'];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    ids=np.fromfile(out/'ids.i32','<i4');h=unit(np.array(base[ids],dtype='f4'));q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8')
    rows=np.fromfile(out/'selected_rows.i32','<i4');gt=np.fromfile(out/'selected2048.ids.i64','<i8').reshape(len(rows),100)
    ap=np.fromfile(out/'labels/ids.i32','<i4').reshape(n,100);assert len(rows)==2048
    t=time.perf_counter();allg=gaps(base,ap[:,0],h);trueg=gaps(base,gt[:,0],h);temp,details=temperature(trueg,allg[rows],allg,mode)
    allg.tofile(dest/'proxy_gaps.f64');trueg.tofile(dest/'sample_true_gaps.f64');temperature_seconds=time.perf_counter()-t
    a=assignment(base,ap,h,temp);a[rows]=assignment(base,gt,h,temp);v=h.astype('f8')+a.T@q;w=unit(v).astype('f4')
    assert np.isfinite(w).all();w.tofile(dest/'W.f32');v.tofile(dest/'v.f64')
    result={'status':'COMPLETE_UNVALIDATED','mode':mode,'seconds':time.perf_counter()-start,'temperature':temp,'temperature_seconds':temperature_seconds,
        'temperature_details':details,'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest(),'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),
        'exact_labels_consumed':2048,'approx_labels_for_profile':17952,'approx_labels_for_temperature':20000,'new_profiles':1,
        'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min()),'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info()}
    with (dest/'profile_complete.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(mode,result,flush=True)
if __name__=='__main__':main()
