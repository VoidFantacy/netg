import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.sched_setaffinity(0,range(8));os.environ['OMP_DYNAMIC']='FALSE'
import hashlib,json,resource,shutil,time
from pathlib import Path
import numpy as np,faiss
from threadpoolctl import threadpool_info
R=Path(__file__).resolve().parent;C=json.loads((R/'config.locked.json').read_text());faiss.omp_set_num_threads(8)
def dump(p,v):
    with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def main():
    assert json.loads((R/'reviews/query_freeze.json').read_text())['status']=='ALL_FOUR_CASES_FROZEN_BEFORE_GT'
    started=time.perf_counter();records={};calls=0
    def check():assert time.perf_counter()-started<C['GT_seconds_cap'] and time.time()<C['deadline_unix'] and shutil.disk_usage(R).free>=C['min_free_bytes']
    for ds,dc in C['datasets'].items():
        check();begin=time.perf_counter();basepath=Path(dc['base']);d=dc['dimension'];manifest=json.loads((Path(dc['dataset_dir'])/'manifest.json').read_text())
        base_sha=sha(basepath);assert base_sha==manifest['files'][basepath.name]['sha256']
        raw=np.memmap(basepath,'<f4',mode='r').reshape(dc['base_n'],d+1);base=raw[:,1:];index=faiss.IndexFlatIP(d);t=time.perf_counter()
        for lo in range(0,len(base),100000):
            check();block=raw[lo:lo+100000];assert (block[:,0].view('i4')==d).all();index.add(np.ascontiguousarray(block[:,1:]))
        loadflat=time.perf_counter()-t;pending=[]
        for batch in range(2):
            case=f'{ds}_b{batch}';c=C['cases'][case];out=R/'inputs'/case;n=c['n'];q=np.fromfile(out/'queries.f32','<f4').reshape(n,d)
            assert sha(out/'queries.f32')==json.loads((out/'manifest.json').read_text())['files']['queries.f32']
            ids=np.empty((n,100),dtype='i4');dist=np.empty((n,100),dtype='f4');times=[]
            for lo in range(0,n,256):
                check();hi=min(lo+256,n);t=time.perf_counter();dd,ii=index.search(q[lo:hi],100);times.append(time.perf_counter()-t)
                ids[lo:hi]=ii;dist[lo:hi]=dd;calls+=hi-lo
                (R/'reviews/gt_progress.json').write_text(json.dumps({'case':case,'completed':hi,'n':n,'total_GT_queries':calls,'unix':time.time()})+'\n')
                if hi%1024==0:print(case,'GT',hi,'/',n,flush=True)
            assert (ids>=0).all() and (ids<len(base)).all() and (np.diff(dist,axis=1)<=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
            ids.tofile(out/'gt.i32');dist.tofile(out/'gt_ip.f32');pending.append((case,q,ids,dist,times))
        del index
        for case,q,ids,dist,times in pending:
            check();out=R/'inputs'/case;n=len(q);verify_start=time.perf_counter();checkrows=np.arange(0,n,n//8);qq=q[checkrows].astype('f8')
            bestd=np.full((8,100),-np.inf);besti=np.full((8,100),-1,dtype='i8')
            for lo in range(0,len(base),65536):
                check();score=qq@np.array(base[lo:lo+65536],dtype='f8').T;loc=np.argpartition(score,-100,axis=1)[:,-100:]
                val=np.take_along_axis(score,loc,axis=1);loc+=lo;dd=np.concatenate([bestd,val],axis=1);ii=np.concatenate([besti,loc],axis=1)
                take=np.argpartition(dd,-100,axis=1)[:,-100:];bestd=np.take_along_axis(dd,take,axis=1);besti=np.take_along_axis(ii,take,axis=1)
            checks=[]
            for j,row in enumerate(checkrows):
                actual=np.array(base[ids[row]],dtype='f8')@qq[j];threshold=float(bestd[j].min());tol=2e-5*max(1.,abs(threshold))
                assert actual.min()>=threshold-tol and actual[0]>=bestd[j].max()-tol
                np.testing.assert_allclose(actual,dist[row],rtol=1e-5,atol=3e-5)
                checks.append({'row':int(row),'set_overlap':len(set(ids[row])&set(besti[j])),'float64_threshold':threshold,
                    'actual_minimum':float(actual.min()),'top1_float64_max_error':float(bestd[j].max()-actual[0]),'tolerance':tol})
            result={'status':'PASS_EXACT_GT','case':case,'n':n,'k':100,'metric':'raw_inner_product','query_sha256':sha(out/'queries.f32'),
                'base_sha256':base_sha,'GT_sha256':sha(out/'gt.i32'),'search_seconds':sum(times),'batch_seconds':times,
                'independent_float64_seconds':time.perf_counter()-verify_start,'independent_float64_checks':checks,'GT_threads':8,
                'affinity':sorted(os.sched_getaffinity(0)),'resident_threads':len(list(Path('/proc/self/task').iterdir())),'faiss_version':faiss.__version__,
                'numpy_version':np.__version__,'threadpools':threadpool_info()}
            dump(out/'gt_manifest.json',result);records[case]=result;print(case,'GT VERIFIED',flush=True)
        dump(R/'reviews'/f'{ds}.gt_cost.json',{'status':'PASS','dataset':ds,'total_seconds':time.perf_counter()-begin,'load_flat_seconds':loadflat,'base_sha256':base_sha})
        del raw,base,pending
    assert calls==16384
    dump(R/'reviews/gt_complete.json',{'status':'PASS','seconds':time.perf_counter()-started,'new_exact_GT_queries':calls,'independent_full_base_float64_queries':32,
        'cases':list(records),'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
if __name__=='__main__':main()
