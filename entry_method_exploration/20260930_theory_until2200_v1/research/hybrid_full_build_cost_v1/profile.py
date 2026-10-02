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
    q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8');rows=np.fromfile(out/'selected_rows.i32','<i4');rest=np.fromfile(out/'approx_rows.i32','<i4')
    gt=np.fromfile(out/'selected2048.ids.i64','<i8').reshape(len(rows),100);ap=np.fromfile(out/'labels/ids.i32','<i4').reshape(len(rest),100)
    assert len(rows)==2048 and len(rest)==17952 and np.array_equal(np.sort(np.r_[rows,rest]),np.arange(n))
    target_ids=np.empty((n,100),dtype='i8');target_ids[rows]=gt;target_ids[rest]=ap
    temp=None;tempstart=time.perf_counter()
    if c['soft']:
        target=unit(np.array(base[gt[:,0]],dtype='f4'));s=target@h.T;top=np.partition(s,-2,axis=1)[:,-2:];gaps=(top.max(1)-top.min(1)).astype('f8')
        temp=max(float(np.median(gaps)),1e-4);gaps.tofile(out/'temperature_gaps.f64')
    tempend=time.perf_counter();a=np.zeros((n,len(h)))
    for rank in range(10):
        target=unit(np.array(base[target_ids[:,rank]],dtype='f4'))
        for lo in range(0,n,4096):
            hi=min(lo+4096,n);s=target[lo:hi]@h.T
            if temp is None:a[np.arange(lo,hi),s.argmax(1)]+=.1
            else:
                s=s.astype('f8');s-=s.max(1,keepdims=True);s/=temp;np.exp(s,out=s);s/=s.sum(1,keepdims=True);a[lo:hi]+=s/10
    v=h.astype('f8')+a.T@q;w=unit(v).astype('f4');assert np.isfinite(w).all()
    np.testing.assert_allclose(a.sum(1),1.,rtol=1e-13,atol=1e-13)
    w.tofile(out/'W.f32')
    result={'status':'COMPLETE_UNVALIDATED','seconds':time.perf_counter()-start,'temperature':temp,'temperature_seconds':tempend-tempstart,
        'assignment_and_profile_seconds':time.perf_counter()-tempend,'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest(),
        'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),'new_profiles':1,'exact_labels_consumed':len(rows),'approx_labels_consumed':len(rest),
        'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min())}
    with (out/'profile_complete.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(c['dataset'],'PROFILE',result,flush=True)
if __name__=='__main__':main()
