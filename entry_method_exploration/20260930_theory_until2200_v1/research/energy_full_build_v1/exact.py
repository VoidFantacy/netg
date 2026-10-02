import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,range(8))
import json,resource,shutil,sys,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info
from lazy_gt import Replay,LazyGT,selector_scope
faiss.omp_set_num_threads(8)
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text())
from budget import guard, reserve_gt, commit_gt
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());out=Path(c['output']);out.mkdir();d=c['dimension'];calls=0
    def check():
        guard(C,start)
    t=time.perf_counter();qraw=np.fromfile(c['qgt_queries'],'<f4').reshape(-1,d+1);assert (qraw[:,0].view('<i4')==d).all()
    qgt=np.ascontiguousarray(qraw[:,1:]);fit=np.fromfile(c['fit_queries'],'<f4').reshape(c['fit_n'],d)
    assert len(qgt)==5000 and np.isfinite(qgt).all() and np.isfinite(fit).all()
    rows=np.random.default_rng(c['pilot_seed']).permutation(c['fit_n'])[:c['pilot_n']].astype('<i4')
    rows.tofile(out/'pilot_rows.i32')
    result={'input_and_split_seconds':time.perf_counter()-t,'GT':{},'new_GT':0}
    t=time.perf_counter();scope=selector_scope(c['selector_source'],faiss.Kmeans);q=scope['normalize'](qgt.astype('f4'))
    km=faiss.Kmeans(d,c['H'],niter=25,nredo=1,verbose=False,spherical=True,seed=20260828);km.train(q);search=km.index.search(q,1)
    assignment=search[1][:,0];centroids=scope['normalize'](km.centroids.astype('f4'));first=[]
    for cluster in range(c['H']):
        members=np.flatnonzero(assignment==cluster)
        if len(members):
            similarity=q[members]@centroids[cluster];first.append(int(members[np.argsort(-similarity)][0]))
    np.savez(out/'cluster_plan.npz',assignment=assignment,centroids=km.centroids,first_representatives=np.asarray(first,dtype='i4'))
    result['qgt_cluster_plan_seconds']=time.perf_counter()-t
    t=time.perf_counter();base=np.memmap(c['base'],'<f4',mode='r').reshape(c['base_n'],d+1);index=faiss.IndexFlatIP(d)
    for lo in range(0,c['base_n'],100000):
        check();block=base[lo:lo+100000];assert (block[:,0].view('<i4')==d).all();index.add(np.ascontiguousarray(block[:,1:]))
    result['base_load_flat_build_seconds']=time.perf_counter()-t;assert index.ntotal==c['base_n'];qgt_batches=[]
    def search_rows(query_rows,phase):
        nonlocal calls
        check();reserve_gt(C,len(query_rows),c['dataset']+':'+phase);t=time.perf_counter();dd,ii=index.search(np.ascontiguousarray(qgt[query_rows]),100);elapsed=time.perf_counter()-t;calls+=len(query_rows);commit_gt(len(query_rows))
        qgt_batches.append({'phase':phase,'n':len(query_rows),'seconds':elapsed})
        (R/'reviews/progress.json').write_text(json.dumps({'dataset':c['dataset'],'phase':phase,'new_GT_current_dataset':calls,'unix':time.time()})+'\n')
        print(c['dataset'],phase,'computed',calls,'search_seconds',elapsed,flush=True);return dd,ii
    t=time.perf_counter();lazy=LazyGT(5000,100,search_rows);lazy.prefetch(first)
    replay=Replay(q,km.centroids,search);scope=selector_scope(c['selector_source'],lambda *a,**kw:replay)
    select_start=time.perf_counter();hubs,detail=scope['choose_unique_gt_hubs'](qgt,lazy,c['H'],20260828,25);result['qgt_selector_replay_seconds']=time.perf_counter()-select_start
    hubs.tofile(out/'ids.i32');generated=np.flatnonzero(lazy.cached).astype('i4');generated.tofile(out/'qgt_demand.rows.i32')
    lazy.ids[generated].tofile(out/'qgt_demand.ids.i64');lazy.dist[generated].tofile(out/'qgt_demand.dist.f32')
    dump(out/'qgt_trace.json',lazy.trace);dump(out/'qgt_generation.json',lazy.generated)
    result['GT']['qgt_demand']={'n':len(generated),'computed_queries':lazy.computed,'logical_consumed_rows':len(set(x['row'] for x in lazy.trace)),
        'first_representatives':len(first),'fallback_batches':sum(x['phase']=='fallback_source_block' for x in lazy.generated),
        'overlap_checks':lazy.overlap_checks,'search_seconds':sum(x['seconds'] for x in qgt_batches),'batches':qgt_batches,'whole_phase_seconds':time.perf_counter()-t}
    t=time.perf_counter();queries=np.ascontiguousarray(fit[rows]);ids=np.empty((len(rows),100),dtype='i8');dist=np.empty((len(rows),100),dtype='f4');times=[]
    for lo in range(0,len(rows),256):
        check();hi=min(lo+256,len(rows));reserve_gt(C,hi-lo,c['dataset']+':pilot1024');bs=time.perf_counter();dd,ii=index.search(queries[lo:hi],100);times.append(time.perf_counter()-bs);commit_gt(hi-lo)
        ids[lo:hi]=ii;dist[lo:hi]=dd;calls+=hi-lo
        (R/'reviews/progress.json').write_text(json.dumps({'dataset':c['dataset'],'phase':'pilot1024','completed':hi,'total':len(rows),'new_GT_current_dataset':calls,'unix':time.time()})+'\n')
        if hi%1024==0:print(c['dataset'],'pilot1024',hi,'search_seconds',sum(times),flush=True)
    assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dist).all()
    assert (np.diff(dist,axis=1)<=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
    ids.tofile(out/'pilot1024.ids.i64');dist.tofile(out/'pilot1024.dist.f32')
    result['GT']['pilot1024']={'n':len(rows),'search_seconds':sum(times),'batch_seconds':times,'whole_phase_seconds':time.perf_counter()-t}
    del index
    result.update(qgt_H_details=detail,new_GT=calls,status='COMPLETE_UNVALIDATED',seconds=time.perf_counter()-start,
        affinity=sorted(os.sched_getaffinity(0)),threads=len(list(Path('/proc/self/task').iterdir())),faiss_threads=faiss.omp_get_max_threads(),
        threadpools=threadpool_info(),numpy_version=np.__version__,faiss_version=faiss.__version__,maxrss_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    assert calls==lazy.computed+1024;dump(out/'exact_complete.json',result);print(c['dataset'],'EXACT DONE',result['seconds'],flush=True)
if __name__=='__main__':main()
