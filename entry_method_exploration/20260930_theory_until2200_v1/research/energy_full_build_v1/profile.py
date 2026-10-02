import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='8'
os.sched_setaffinity(0,range(8))
import hashlib,json,sys,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_info
from common import unit,assignment,dump,ident
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());method=sys.argv[2];p=Path(c['output']);out=p/method;n,d=c['fit_n'],c['dimension']
    for path,v in json.loads((out/'selection_frozen.json').read_text())['files'].items():assert ident(path)==v
    temp=json.loads((out/'selection.json').read_text())['temperature'];base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1)[:,1:]
    h=unit(np.array(base[np.fromfile(p/'ids.i32','<i4')],dtype='f4'));q=unit(np.fromfile(c['fit_queries'],'<f4').reshape(n,d)).astype('f8')
    rows=np.fromfile(out/'selected_rows.i32','<i4');pilot=np.fromfile(p/'pilot_rows.i32','<i4');added=np.fromfile(out/'added_rows.i32','<i4')
    assert np.array_equal(rows,np.r_[pilot,added]) and len(np.unique(rows))==2048
    gt=np.r_[np.fromfile(p/'pilot1024.ids.i64','<i8').reshape(1024,100),np.fromfile(out/'additional1024.ids.i64','<i8').reshape(1024,100)]
    ap=np.fromfile(p/'labels/ids.i32','<i4').reshape(n,100);a=assignment(base,ap,h,temp);approx_hash=hashlib.sha256(a.tobytes()).hexdigest()
    assert approx_hash==json.loads((out/'selection.json').read_text())['approx_assignment_sha256']
    a[rows]=assignment(base,gt,h,temp);v=h.astype('f8')+a.T@q;w=unit(v).astype('<f4');assert np.isfinite(w).all()
    v.tofile(out/'v.f64');w.tofile(out/'W.f32')
    dump(out/'profile_complete.json',{'status':'COMPLETE_UNVALIDATED','seconds':time.perf_counter()-start,'temperature':temp,
        'profile_sha256':hashlib.sha256(w.tobytes()).hexdigest(),'assignment_sha256':hashlib.sha256(a.tobytes()).hexdigest(),
        'approx_assignment_sha256':approx_hash,'new_profiles':1,'exact_labels_consumed':2048,'approx_labels_consumed':20000,
        'approx_labels_retained_after_override':17952,'affinity':sorted(os.sched_getaffinity(0)),'threadpools':threadpool_info(),
        'minimum_resultant_norm':float(np.linalg.norm(v,axis=1).min())})
    print(c['dataset'],method,'PROFILE',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
