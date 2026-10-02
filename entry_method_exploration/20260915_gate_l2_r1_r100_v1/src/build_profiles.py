"""QGT real hubs, then frozen GT10 hard and fixed-temperature soft query profiles."""
from common import *
import ast, sys, faiss

def reference_functions():
    p=RUN/'sources/fast_builder.py';tree=ast.parse(p.read_text())
    selected=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ['normalize','choose_unique_gt_hubs']]
    assert len(selected)==2
    scope={'np':np,'faiss':faiss};exec(compile(ast.Module(body=selected,type_ignores=[]),str(p),'exec'),scope)
    return scope

def build(ds):
    faiss.omp_set_num_threads(16);inp=RUN/'inputs'/ds;out=RUN/'models'/ds
    ready=out/'profiles.complete.json'
    if ready.exists():return
    c=json.loads((inp/'manifest.json').read_text());base=vecs(c['paths']['base_path']);ref=reference_functions();norm=ref['normalize'];t=time.time()
    qgt=vecs(inp/'qgt.fvecs');gt=np.fromfile(inp/'qgt.gt.i32','i4').reshape(5000,100)
    if (inp/'qgt_selection.json').exists():ids=np.fromfile(inp/'gt10.ids.i32','i4')
    else:
        ids,details=ref['choose_unique_gt_hubs'](qgt,gt,800,20260828,25)
        ids.tofile(inp/'gt10.ids.i32');norm(np.asarray(base[ids])).tofile(inp/'gt10.hubs.f32')
        dump(inp/'qgt_selection.json',details|dict(seconds=time.time()-t,ids_sha256=sha(inp/'gt10.ids.i32')))
    assert len(ids)==800 and np.all(np.diff(ids)>0)
    q=norm(np.asarray(vecs(inp/'fit.fvecs')));hn=norm(np.asarray(base[ids]));gt=np.fromfile(inp/'fit.gt.i32','i4').reshape(20000,100)
    gaps=[]
    for lo in range(0,len(q),4096):
        s=norm(np.asarray(base[gt[lo:lo+4096,0]]))@hn.T;top=np.partition(s,-2,axis=1)[:,-2:]
        gaps.extend((top.max(axis=1)-top.min(axis=1)).astype('f8'))
    temp=max(float(np.median(gaps)),1e-4)
    weights={name:np.zeros((len(q),len(ids)),dtype='f8') for name in ['gt10_hard','gt10_soft_t1']}
    for rank in range(10):
        for lo in range(0,len(q),4096):
            hi=min(lo+4096,len(q));s=norm(np.asarray(base[gt[lo:hi,rank]]))@hn.T
            weights['gt10_hard'][np.arange(lo,hi),np.argmax(s,axis=1)]+=.1
            z=s.astype('f8');z-=z.max(axis=1,keepdims=True);z/=temp;np.exp(z,out=z);z/=z.sum(axis=1,keepdims=True)
            weights['gt10_soft_t1'][lo:hi]+=z/10
    for name,a in weights.items():
        assert np.max(np.abs(a.sum(axis=1)-1))<1e-12 and np.isfinite(a).all()
        sums=hn.astype('f8')+a.T@q.astype('f8');w=(sums/np.maximum(np.linalg.norm(sums,axis=1,keepdims=True),1e-12)).astype('f4')
        dest=out/name;dest.mkdir(parents=True,exist_ok=True);w.tofile(dest/'W.f32')
        dump(dest/'complete.json',dict(status='PASS',K_gt=10,H=800,fit_rows=20000,prior=1,temperature=None if name=='gt10_hard' else temp,sha256=sha(dest/'W.f32'),mass_min=float(a.sum(axis=0).min()),mass_max=float(a.sum(axis=0).max())))
    dump(ready,dict(status='PASS',seconds=time.time()-t,temperature=temp,fit_only_gap_quantiles=np.quantile(gaps,[0,.25,.5,.75,1]).tolist(),source_sha256=sha(RUN/'sources/fast_builder.py')))
    print('PROFILES_READY',ds,flush=True)

if __name__=='__main__':build(sys.argv[1])
