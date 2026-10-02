import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,range(8))
import hashlib,json,resource,sys,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info
from lazy_gt import Replay,LazyGT,selector_scope
from budget import guard,reserve,commit
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());faiss.omp_set_num_threads(8)

def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')

def array_sha(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()

def load_flat(c,start):
    t=time.perf_counter();raw=np.memmap(c['base'],'<f4',mode='r',shape=(c['base_n'],c['dimension']+1));index=faiss.IndexFlatIP(c['dimension'])
    for lo in range(0,c['base_n'],100000):
        guard(C,start);block=raw[lo:lo+100000];assert np.all(block[:,0].view('<i4')==c['dimension'])
        index.add(np.ascontiguousarray(block[:,1:]))
    assert index.ntotal==c['base_n'];return index,time.perf_counter()-t

def query_rows(index,q,c,name,out,start):
    t=time.perf_counter();n=len(q);ids=np.empty((n,100),dtype='<i8');dist=np.empty((n,100),dtype='<f4');times=[];sizes=[]
    assert C['fit_batch']==1024 and C['returned_k']==100 and C['stored_prefix']==11
    for lo in range(0,n,C['fit_batch']):
        hi=min(lo+C['fit_batch'],n);size=hi-lo;guard(C,start);reserve(C,'GT',size,c['case']+':'+name)
        bs=time.perf_counter();dd,ii=index.search(q[lo:hi],100);times.append(time.perf_counter()-bs);sizes.append(size)
        commit('GT',size);ids[lo:hi]=ii;dist[lo:hi]=dd
        (R/'reviews/progress.json').write_text(json.dumps({'case':c['case'],'phase':name,'rows':hi,'n':n,'unix':time.time()})+'\n')
        print(c['case'],name,hi,'search_seconds',sum(times),flush=True)
    assert ids.min()>=0 and ids.max()<c['base_n'] and np.isfinite(dist).all()
    assert np.all(np.diff(dist,axis=1)<=0) and np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
    np.ascontiguousarray(ids[:,:11]).tofile(out/(name+'.ids.i64'));np.ascontiguousarray(dist[:,:11]).tofile(out/(name+'.dist.f32'))
    return {'n':n,'search_seconds':sum(times),'batch_seconds':times,'batch_sizes':sizes,'whole_phase_seconds':time.perf_counter()-t,
            'returned_k':100,'stored_prefix':11,'all100_ids_sha256':array_sha(ids),'all100_dist_sha256':array_sha(dist)}

def main():
    start=time.perf_counter();c=json.loads(Path(sys.argv[1]).read_text());out=Path(c['output']);out.mkdir();d=c['dimension'];method=c['method']
    t=time.perf_counter();qraw=np.fromfile(c['qgt_queries'],'<f4').reshape(-1,d+1);assert np.all(qraw[:,0].view('<i4')==d)
    qgt=np.ascontiguousarray(qraw[:,1:]);fit=np.fromfile(c['fit_queries'],'<f4').reshape(c['fit_n'],d)
    assert len(qgt)==5000 and c['fit_n']==20000 and np.isfinite(qgt).all() and np.isfinite(fit).all()
    if method=='Default':rows=np.arange(c['fit_n'],dtype='<i4');name='fit20000'
    else:
        order=np.random.default_rng(c['pilot_seed']).permutation(c['fit_n']);n=2048 if method=='Uniform' else 1024
        rows=order[:n].astype('<i4');name='selected2048' if method=='Uniform' else 'pilot1024'
    rows.tofile(out/'exact_rows.i32')
    if method=='Uniform':
        rest=np.setdiff1d(np.arange(c['fit_n'],dtype='<i4'),rows);rest.tofile(out/'approx_rows.i32')
    result={'input_and_split_seconds':time.perf_counter()-t,'GT':{}}
    t=time.perf_counter();scope=selector_scope(c['selector_source'],faiss.Kmeans);q=scope['normalize'](qgt.astype('f4'))
    km=faiss.Kmeans(d,c['H'],niter=25,nredo=1,verbose=False,spherical=True,seed=20260828);km.train(q);search=km.index.search(q,1)
    assignment=search[1][:,0];centroids=scope['normalize'](km.centroids.astype('f4'));first=[]
    for cluster in range(c['H']):
        members=np.flatnonzero(assignment==cluster)
        if len(members):
            similarity=q[members]@centroids[cluster];first.append(int(members[np.argsort(-similarity)][0]))
    np.savez(out/'cluster_plan.npz',assignment=assignment,first_representatives=np.asarray(first,dtype='i4'))
    result['cluster_centroids_sha256']=array_sha(km.centroids);result['qgt_cluster_plan_seconds']=time.perf_counter()-t
    index,result['base_load_flat_build_seconds']=load_flat(c,start);qgt_batches=[]
    def search_qgt(query_rows,phase):
        guard(C,start);reserve(C,'GT',len(query_rows),c['case']+':qgt:'+phase);t=time.perf_counter()
        dd,ii=index.search(np.ascontiguousarray(qgt[query_rows]),100);elapsed=time.perf_counter()-t;commit('GT',len(query_rows))
        qgt_batches.append({'phase':phase,'n':len(query_rows),'seconds':elapsed});return dd,ii
    t=time.perf_counter();lazy=LazyGT(5000,100,search_qgt);lazy.prefetch(first)
    replay=Replay(q,km.centroids,search);scope=selector_scope(c['selector_source'],lambda *a,**kw:replay)
    ts=time.perf_counter();hubs,detail=scope['choose_unique_gt_hubs'](qgt,lazy,c['H'],20260828,25);result['qgt_selector_replay_seconds']=time.perf_counter()-ts
    hubs.tofile(out/'ids.i32');generated=np.flatnonzero(lazy.cached).astype('i4');generated.tofile(out/'qgt_demand.rows.i32')
    lazy.ids[generated].tofile(out/'qgt_demand.ids.i64');lazy.dist[generated].tofile(out/'qgt_demand.dist.f32')
    dump(out/'qgt_trace.json',lazy.trace);dump(out/'qgt_generation.json',lazy.generated)
    result['GT']['qgt_demand']={'n':len(generated),'computed_queries':lazy.computed,'logical_consumed_rows':len(set(x['row'] for x in lazy.trace)),
        'first_representatives':len(first),'fallback_batches':sum(x['phase']=='fallback_source_block' for x in lazy.generated),
        'overlap_checks':lazy.overlap_checks,'search_seconds':sum(x['seconds'] for x in qgt_batches),'batches':qgt_batches,'whole_phase_seconds':time.perf_counter()-t}
    result['GT'][name]=query_rows(index,np.ascontiguousarray(fit[rows]),c,name,out,start);del index
    result.update(qgt_H_details=detail,new_GT=lazy.computed+len(rows),status='COMPLETE_UNVALIDATED',seconds=time.perf_counter()-start,
        affinity=sorted(os.sched_getaffinity(0)),threads=len(list(Path('/proc/self/task').iterdir())),faiss_threads=faiss.omp_get_max_threads(),
        threadpools=threadpool_info(),numpy_version=np.__version__,faiss_version=faiss.__version__,maxrss_GiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20)
    dump(out/'exact_complete.json',result);print(c['case'],'EXACT DONE',result['seconds'],flush=True)

if __name__=='__main__':main()
