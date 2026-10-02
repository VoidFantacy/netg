import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());out=Path(c['output']);n,d=c['fit_n'],c['dimension']
    base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:];ids=np.fromfile(out/'ids.i32','<i4');h=unit(np.array(base[ids],dtype='f4'))
    q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8');targets=np.fromfile(out/'fit20000.ids.i64','<i8').reshape(n,100)
    assert np.array_equal(np.fromfile(out/'fit_rows.i32','<i4'),np.arange(n))
    t=time.perf_counter();temperature=None
    if c['soft']:
        z=unit(np.array(base[targets[:,0]],dtype='f4'));gaps=[]
        for lo in range(0,n,4096):
            score=z[lo:lo+4096]@h.T;top=np.partition(score,-2,axis=1)[:,-2:];gaps.append((top.max(1)-top.min(1)).astype('f8'))
        gaps=np.concatenate(gaps);gaps.tofile(out/'temperature_gaps.f64');temperature=max(float(np.median(gaps)),1e-4)
    temperature_seconds=time.perf_counter()-t;t=time.perf_counter();a=np.zeros((n,len(h)))
    for rank in range(10):
        z=unit(np.array(base[targets[:,rank]],dtype='f4'))
        for lo in range(0,n,4096):
            hi=min(lo+4096,n);scores=z[lo:hi]@h.T
            if temperature is None:a[np.arange(lo,hi),scores.argmax(1)]+=.1
            else:
                weights=scores.astype('f8');weights-=weights.max(1,keepdims=True);weights/=temperature;np.exp(weights,out=weights);weights/=weights.sum(1,keepdims=True);a[lo:hi]+=weights/10
    v=h.astype('f8')+a.T@q;w=unit(v).astype('f4');assert np.isfinite(w).all();np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13)
    w.tofile(out/'W.f32');v.tofile(out/'v.f64')
    record={'status':'COMPLETE_UNVALIDATED','seconds':time.perf_counter()-start,'temperature':temperature,'temperature_seconds':temperature_seconds,
        'assignment_and_profile_seconds':time.perf_counter()-t,'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest(),
        'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'new_profiles':1,'exact_labels_consumed':n,'approx_labels_consumed':0,
        'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min())}
    with (out/'profile_complete.json').open('x') as f:json.dump(record,f,indent=2,allow_nan=False);f.write('\n')
    print(c['dataset'],'PROFILE',record,flush=True)
if __name__=='__main__':main()
