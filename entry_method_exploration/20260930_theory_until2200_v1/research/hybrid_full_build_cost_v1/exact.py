import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,range(8))
import ast,json,resource,shutil,sys,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info
faiss.omp_set_num_threads(8)
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());out=Path(c['output']);out.mkdir();d=c['dimension'];calls=0
    def check():
        assert time.time()<C['deadline_unix'] and time.perf_counter()-start<C['seconds_cap'] and shutil.disk_usage(R).free>=6*2**30
    t=time.perf_counter();qraw=np.fromfile(c['qgt_queries'],'<f4').reshape(-1,d+1);assert (qraw[:,0].view('<i4')==d).all()
    qgt=np.ascontiguousarray(qraw[:,1:]);fit=np.fromfile(c['fit_queries'],'<f4').reshape(c['fit_n'],d)
    assert len(qgt)==5000 and np.isfinite(qgt).all() and np.isfinite(fit).all()
    rows=np.random.default_rng(c['pilot_seed']).permutation(c['fit_n'])[:c['pilot_n']].astype('<i4')
    rest=np.setdiff1d(np.arange(c['fit_n'],dtype='i4'),rows);rows.tofile(out/'selected_rows.i32');rest.tofile(out/'approx_rows.i32')
    np.ascontiguousarray(fit[rest]).tofile(out/'approx_queries.f32')
    result={'input_and_split_seconds':time.perf_counter()-t,'GT':{},'new_GT':0}
    t=time.perf_counter();base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1);index=faiss.IndexFlatIP(d)
    for lo in range(0,c['base_n'],100000):
        check();block=base[lo:lo+100000];assert (block[:,0].view('<i4')==d).all();index.add(np.ascontiguousarray(block[:,1:]))
    result['base_load_flat_build_seconds']=time.perf_counter()-t;assert index.ntotal==c['base_n'];newqgt=None
    for label,queries in [('qgt5000',qgt),('selected2048',np.ascontiguousarray(fit[rows]))]:
        startphase=time.perf_counter();n=len(queries);ids=np.empty((n,100),dtype='i8');dist=np.empty((n,100),dtype='f4');times=[]
        for lo in range(0,n,256):
            check();hi=min(lo+256,n);t=time.perf_counter();dd,ii=index.search(np.ascontiguousarray(queries[lo:hi]),100)
            times.append(time.perf_counter()-t);ids[lo:hi]=ii;dist[lo:hi]=dd;calls+=hi-lo
            (R/'reviews/progress.json').write_text(json.dumps({'dataset':c['dataset'],'phase':label,'completed':hi,'total':n,'new_GT_current_dataset':calls,'unix':time.time()})+'\n')
            if hi%1024==0 or hi==n:print(c['dataset'],label,hi,'/',n,'search_seconds',sum(times),flush=True)
        assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dist).all()
        assert (np.diff(dist,axis=1)<=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
        t=time.perf_counter();ids.tofile(out/f'{label}.ids.i64');dist.tofile(out/f'{label}.dist.f32');write=time.perf_counter()-t
        result['GT'][label]={'n':n,'search_seconds':sum(times),'batch_seconds':times,'write_seconds':write,'whole_phase_seconds':time.perf_counter()-startphase}
        if label=='qgt5000':newqgt=ids
    del index
    t=time.perf_counter();source=Path(c['selector_source']);nodes=[x for x in ast.parse(source.read_text()).body if isinstance(x,ast.FunctionDef) and x.name in ['normalize','choose_unique_gt_hubs']]
    assert len(nodes)==2;scope={'np':np,'faiss':faiss};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
    hubs,detail=scope['choose_unique_gt_hubs'](qgt,newqgt,c['H'],20260828,25);hubs.tofile(out/'ids.i32')
    result.update(qgt_H_seconds=time.perf_counter()-t,qgt_H_details=detail,new_GT=calls,status='COMPLETE_UNVALIDATED',seconds=time.perf_counter()-start,
        affinity=sorted(os.sched_getaffinity(0)),threads=len(list(Path('/proc/self/task').iterdir())),faiss_threads=faiss.omp_get_max_threads(),
        threadpools=threadpool_info(),numpy_version=np.__version__,faiss_version=faiss.__version__,maxrss_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    assert calls==7048;dump(out/'exact_complete.json',result);print(c['dataset'],'EXACT DONE',result['seconds'],flush=True)
if __name__=='__main__':main()
