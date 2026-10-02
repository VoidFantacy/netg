import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info
from common import unit,assignment,dump,ident

def sha(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()

def median_gap(base,target_ids,h):
    z=unit(np.array(base[target_ids],dtype='f4'));parts=[]
    for lo in range(0,len(z),4096):
        s=z[lo:lo+4096]@h.T;top=np.partition(s,-2,axis=1)[:,-2:];parts.append((top.max(1)-top.min(1)).astype('f8'))
    gaps=np.concatenate(parts);return max(float(np.median(gaps)),1e-4),gaps

def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());p=Path(c['output']);n,d=c['fit_n'],c['dimension'];method=c['method']
    base=np.memmap(c['base'],'<f4',mode='r',shape=(c['base_n'],d+1))[:,1:]
    ids=np.fromfile(p/'ids.i32','<i4');h=unit(np.array(base[ids],dtype='f4'));q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8')
    initial=np.fromfile(p/'exact_rows.i32','<i4');temp=None;approx_hash=None;gaps=None;t=time.perf_counter()
    if method=='Default':
        assert np.array_equal(initial,np.arange(n));gt=np.fromfile(p/'fit20000.ids.i64','<i8').reshape(n,11)
        if c['soft']:temp,gaps=median_gap(base,gt[:,0],h)
        temperature_seconds=time.perf_counter()-t;t=time.perf_counter();a=assignment(base,gt,h,temp);exact_n=n;approx_n=0
    elif method=='Uniform':
        rows=initial;assert len(rows)==2048;gt=np.fromfile(p/'selected2048.ids.i64','<i8').reshape(2048,11)
        rest=np.fromfile(p/'approx_rows.i32','<i4');assert np.array_equal(np.sort(np.r_[rows,rest]),np.arange(n))
        if c['soft']:
            ap=np.fromfile(p/'labels/ids.i32','<i4').reshape(n,11);temp,gaps=median_gap(base,ap[:,0],h)
            temperature_seconds=time.perf_counter()-t;t=time.perf_counter();a=assignment(base,ap,h,temp);approx_hash=sha(a);a[rows]=assignment(base,gt,h,temp);approx_n=n
        else:
            ap=np.fromfile(p/'labels/ids.i32','<i4').reshape(len(rest),11);targets=np.empty((n,11),dtype='i8');targets[rows]=gt;targets[rest]=ap
            temperature_seconds=time.perf_counter()-t;t=time.perf_counter();a=assignment(base,targets,h,None);approx_n=len(rest)
        exact_n=2048
    else:
        assert method=='EnergyTree';out=p/'selection'
        for path,v in json.loads((out/'selection_frozen.json').read_text())['files'].items():assert ident(path)==v
        sel=json.loads((out/'selection.json').read_text());temp=sel['temperature'];rows=np.fromfile(out/'selected_rows.i32','<i4');added=np.fromfile(out/'added_rows.i32','<i4')
        assert np.array_equal(rows,np.r_[initial,added]) and len(np.unique(rows))==2048
        gt=np.r_[np.fromfile(p/'pilot1024.ids.i64','<i8').reshape(1024,11),np.fromfile(out/'additional1024.ids.i64','<i8').reshape(1024,11)]
        ap=np.fromfile(p/'labels/ids.i32','<i4').reshape(n,11);temperature_seconds=time.perf_counter()-t;t=time.perf_counter()
        a=assignment(base,ap,h,temp);approx_hash=sha(a);assert approx_hash==sel['approx_assignment_sha256'];a[rows]=assignment(base,gt,h,temp);exact_n=2048;approx_n=n
    v=h.astype('f8')+a.T@q;w=unit(v).astype('<f4');assert np.isfinite(w).all();np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13)
    w.tofile(p/'W.f32');aggregation_seconds=time.perf_counter()-t
    if gaps is not None:gaps.tofile(p/'temperature_gaps.f64')
    dump(p/'profile_complete.json',{'status':'COMPLETE_UNVALIDATED','method':method,'seconds':time.perf_counter()-start,'temperature':temp,
        'temperature_seconds':temperature_seconds,'assignment_and_profile_seconds':aggregation_seconds,'profile_sha256':sha(w),
        'assignment_sha256':sha(a),'resultant_sha256':sha(v),'approx_assignment_sha256':approx_hash,'new_profiles':1,
        'exact_labels_consumed':exact_n,'approx_labels_generated_and_read':approx_n,'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min()),
        'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),'resultant_persisted':False,'stored_target_prefix':11})
    print(c['case'],'PROFILE',time.perf_counter()-start,flush=True)

if __name__=='__main__':main()
