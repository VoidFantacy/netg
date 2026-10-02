import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[key]='8'
os.environ['OMP_DYNAMIC']='FALSE';os.environ['OMP_MAX_ACTIVE_LEVELS']='1';os.sched_setaffinity(0,set(range(8)))
import ast,datetime,hashlib,json,time,resource,shutil
from pathlib import Path
import numpy as np,faiss
faiss.omp_set_num_threads(8)
R=Path(__file__).resolve().parents[1];P=R.parent.parent;ROOT=P.parents[1];E=P/'stages/e124_semantic_service_ridge_v1';BASE=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'
C=json.loads((E/'config.locked.json').read_text());PRE=json.loads((R/'reviews/preflight.json').read_text());assert PRE['status']=='PASS'
source=ROOT/'benches/run/build_fast_entry_variants.py';start=time.perf_counter();unix_start=time.time();deadline=datetime.datetime.fromisoformat('2026-09-22T13:25:00+00:00').timestamp();inputs={};big_inputs={};results={};calls=0
def ident(p):return {'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def read(p):inputs[str(p)]=ident(p);return json.loads(p.read_text())
def raw(p,t):inputs[str(p)]=ident(p);return np.fromfile(p,t)
def vecs(p,t):
    z=raw(p,t);d=int(z[:1].view('<i4')[0]);z=z.reshape(-1,d+1);assert (z[:,0].view('<i4')==d).all();return np.ascontiguousarray(z[:,1:])
def dump(p,v):assert not p.exists(),p;p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def alive():
    if time.time()>=deadline or time.perf_counter()-start>=4800:raise TimeoutError('frozen deadline or 80-minute cap reached')
    assert shutil.disk_usage(R).free>=6*2**30,'disk floor'
def progress(state):
    p=R/'reviews/progress.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(dict(state,unix=time.time(),GT_queries=calls),indent=2)+'\n');tmp.replace(p)
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=1,keepdims=True),1e-12)
nodes=[n for n in ast.parse(source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in ['normalize','choose_unique_gt_hubs']];scope={'np':np,'faiss':faiss};exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),scope)
fixed=[Path(__file__),R/'protocol.md',R/'reviews/preflight.json',R/'reviews/preflight_inputs.json',source,E/'config.locked.json']
dump(R/'reviews/rebuild_frozen.json',{'files':{str(p):ident(p) for p in fixed},'deadline_unix':deadline,'start_unix':unix_start,'max_seconds':4800})
status='RUNNING';reason=None
try:
 for ds,dc in C['datasets'].items():
    alive();p=R/'results'/ds;p.mkdir();dp=PRE['datasets'][ds];dimension=dc['dimension'];bpath=Path(dc['base']);st=bpath.stat();big_inputs[str(bpath)]={'bytes':st.st_size,'mtime_ns':st.st_mtime_ns};ds_start=time.perf_counter()
    t=time.perf_counter();qgt=vecs(Path(dp['qgt_queries']),'<f4');fit=raw(Path(dc['fit_source']['queries_file']),'<f4').reshape(20000,dimension);query_load_seconds=time.perf_counter()-t
    oldq=vecs(Path(dp['qgt_GT']),'<i4').astype('i8');oldfit=raw(Path(dc['fit_source']['gt_file']),'<i8').reshape(20000,100);refids=raw(Path(dc['anchor']['ids']),'<i4');H=len(refids)
    result={'status':'RUNNING','query_load_seconds':query_load_seconds,'GT':{},'base_stat':big_inputs[str(bpath)],'dimension':dimension,'base_n':dc['base_n']};results[ds]=result
    t=time.perf_counter();base=np.memmap(bpath,'<f4',mode='r').reshape(dc['base_n'],dimension+1);index=faiss.IndexFlatIP(dimension)
    for lo in range(0,dc['base_n'],100000):
        alive();block=base[lo:lo+100000];assert (block[:,0].view('<i4')==dimension).all();index.add(np.ascontiguousarray(block[:,1:]))
    result['base_load_and_flat_build_seconds']=time.perf_counter()-t;assert index.ntotal==dc['base_n'];generated={}
    print(ds,'flat ready',result['base_load_and_flat_build_seconds'],flush=True)
    for label,queries,old in [('qgt5000',qgt,oldq),('profile20000',fit,oldfit)]:
        n=len(queries);ids=np.empty((n,100),dtype='i8');dist=np.empty((n,100),dtype='f4');durations=[];phase_start=time.perf_counter()
        for lo in range(0,n,256):
            alive();hi=min(lo+256,n);t=time.perf_counter();dd,ii=index.search(np.ascontiguousarray(queries[lo:hi]),100);durations.append(time.perf_counter()-t);ids[lo:hi]=ii;dist[lo:hi]=dd;calls+=hi-lo
            progress({'dataset':ds,'phase':label,'completed':hi,'total':n})
            if hi%2048==0 or hi==n:print(ds,label,hi,'/',n,'search_seconds',sum(durations),flush=True)
        result['GT'][label]={'query_count':n,'search_seconds':sum(durations),'generation_loop_seconds':time.perf_counter()-phase_start,'batch_seconds':durations}
        t=time.perf_counter();ids.tofile(p/f'{label}.ids.i64');dist.tofile(p/f'{label}.dist.f32');result['GT'][label]['output_write_seconds']=time.perf_counter()-t
        audit_start=time.perf_counter();assert (ids>=0).all() and (ids<dc['base_n']).all() and np.isfinite(dist).all();assert (dist[:,1:]<=dist[:,:-1]).all();assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
        equal=np.all(ids==old,axis=1);setequal=np.all(np.sort(ids,axis=1)==np.sort(old,axis=1),axis=1);top10equal=np.all(ids[:,:10]==old[:,:10],axis=1);different=np.flatnonzero(~setequal)
        # Only diagnostic exact re-scoring; never rewrite GT or select a favorable tie rule.
        sample=[]
        for row in different[np.linspace(0,max(0,len(different)-1),min(32,len(different)),dtype=int)]:
            extra=sorted(set(ids[row])-set(old[row]));missing=sorted(set(old[row])-set(ids[row]));qa=queries[row].astype('f8')
            es=np.array(base[extra,1:],dtype='f8')@qa;ms=np.array(base[missing,1:],dtype='f8')@qa
            sample.append({'row':int(row),'new_only':extra,'old_only':missing,'new_min_float64':float(es.min()),'old_max_float64':float(ms.max()),'boundary_gap_float64':float(es.min()-ms.max())})
        result['GT'][label].update({'exact_rank_rows':int(equal.sum()),'exact_set_rows':int(setequal.sum()),'exact_top10_rank_rows':int(top10equal.sum()),'mismatch_float64_samples':sample,'validation_seconds':time.perf_counter()-audit_start})
        generated[label]=ids;dump(p/f'{label}.audit.json',result['GT'][label])
    del index
    alive();t=time.perf_counter();newh,details=scope['choose_unique_gt_hubs'](qgt,generated['qgt5000'],H,20260828,25);result['qgt_H_build_seconds']=time.perf_counter()-t;result['H_exact_match']=bool(np.array_equal(newh,refids));newh.tofile(p/'rebuilt_ids.i32')
    if not result['H_exact_match']:
        result['status']='STOP_NEW_GT_H_NOT_IDENTICAL';status=result['status'];reason=ds;dump(p/'complete.json',result);break
    t=time.perf_counter();hraw=np.array(base[newh,1:],dtype='f4');hubs=unit(hraw);q=unit(fit);gt=generated['profile20000'];a=np.zeros((20000,H));family='gt10_soft_t1' if ds.startswith('web') else 'gt10_hard';manifest=read(BASE/'models'/ds/family/'manifest.json');temp=manifest['temperature']
    for rank in range(10):
        target=unit(np.array(base[gt[:,rank],1:],dtype='f4'))
        for lo in range(0,len(q),4096):
            hi=min(lo+4096,len(q));scores=target[lo:hi]@hubs.T
            if temp is None:a[np.arange(lo,hi),scores.argmax(1)]+=.1
            else:
                z=scores.astype('f8');z-=z.max(1,keepdims=True);z/=temp;np.exp(z,out=z);z/=z.sum(1,keepdims=True);a[lo:hi]+=z/10
    profile=unit(hubs.astype('f8')+a.T@q.astype('f8')).astype('f4');result['target_assignment_and_profile_seconds']=time.perf_counter()-t
    ref=raw(Path(dc['anchor']['W']),'<f4').reshape(H,dimension);result['profile_exact_match']=bool(np.array_equal(profile,ref));result['profile_max_abs_error']=float(np.abs(profile-ref).max());result['assignment_sha256']=hashlib.sha256(a.tobytes()).hexdigest();result['original_assignment_sha256']=manifest['assignments_sha256']
    t=time.perf_counter();profile.tofile(p/'rebuilt_W.f32');result['profile_write_seconds']=time.perf_counter()-t
    result['dataset_process_seconds']=time.perf_counter()-ds_start;result['status']='GT_H_PROFILE_REPRODUCED_ROUTER_PENDING' if result['profile_exact_match'] else 'STOP_NEW_GT_PROFILE_NOT_IDENTICAL';dump(p/'complete.json',result)
    if not result['profile_exact_match']:status=result['status'];reason=ds;break
    del a,profile,base,generated,oldq,oldfit,qgt,fit;print(ds,result['status'],flush=True)
 else:status='GT_H_PROFILE_REPRODUCED_ROUTER_PENDING'
except TimeoutError as e:status='STOP_TIME_CAP_PARTIAL';reason=str(e)
except Exception as e:
 status='FAILED';reason=repr(e);raise
finally:
 for path,v in inputs.items():assert ident(Path(path))==v
 for path,v in big_inputs.items():st=Path(path).stat();assert st.st_size==v['bytes'] and st.st_mtime_ns==v['mtime_ns']
 dump(R/'reviews/rebuild_inputs.json',{'files':inputs,'bases_stat_only':big_inputs})
 dump(R/'reviews/rebuild_complete.json',{'status':status,'reason':reason,'seconds':time.perf_counter()-start,'datasets':results,'GT_query_calls':calls,'faiss_version':faiss.__version__,'faiss_threads':faiss.omp_get_max_threads(),'affinity':sorted(os.sched_getaffinity(0)),'maxrss_GiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/2**20,'user_cpu_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime,'system_cpu_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_stime,'threadpool_process_threads':len(list(Path('/proc/self/task').iterdir())),'router_cost_complete':False,'new_ANN_NSG_QPS':0})
 progress({'status':status,'reason':reason});print(status,reason,flush=True)
