import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,range(8))
import json,resource,sys,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info
from common import dump,ident
from budget import guard,reserve_gt,commit_gt
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());faiss.omp_set_num_threads(8)
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());method=sys.argv[2];out=Path(c['output'])/method;d=c['dimension']
    for p,v in json.loads((out/'selection_frozen.json').read_text())['files'].items():assert ident(p)==v
    rows=np.fromfile(out/'added_rows.i32','<i4');assert len(rows)==len(np.unique(rows))==1024
    fit=np.fromfile(c['fit_queries'],'<f4').reshape(c['fit_n'],d);queries=np.ascontiguousarray(fit[rows]);guard(C,start)
    t=time.perf_counter();base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1);index=faiss.IndexFlatIP(d)
    for lo in range(0,c['base_n'],100000):
        guard(C,start);block=base[lo:lo+100000];assert (block[:,0].view('<i4')==d).all();index.add(np.ascontiguousarray(block[:,1:]))
    load=time.perf_counter()-t;assert index.ntotal==c['base_n'];ids=np.empty((1024,100),dtype='<i8');dist=np.empty((1024,100),dtype='<f4');times=[]
    for lo in range(0,1024,256):
        guard(C,start);reserve_gt(C,256,c['dataset']+':'+method+':additional');t=time.perf_counter();dd,ii=index.search(queries[lo:lo+256],100)
        times.append(time.perf_counter()-t);commit_gt(256);ids[lo:lo+256]=ii;dist[lo:lo+256]=dd
        print(c['dataset'],method,'ADDED GT',lo+256,flush=True)
    assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dist).all()
    assert (np.diff(dist,axis=1)<=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
    ids.tofile(out/'additional1024.ids.i64');dist.tofile(out/'additional1024.dist.f32');del index
    dump(out/'additional_complete.json',{'status':'COMPLETE_UNVALIDATED','seconds':time.perf_counter()-start,'new_GT':1024,
        'base_load_flat_build_seconds':load,'search_seconds':sum(times),'batch_seconds':times,'affinity':sorted(os.sched_getaffinity(0)),
        'faiss_threads':faiss.omp_get_max_threads(),'threadpools':threadpool_info(),'maxrss_GiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20})
if __name__=='__main__':main()
