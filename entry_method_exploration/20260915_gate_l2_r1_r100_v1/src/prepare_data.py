"""Versioned public data, independent roles, and resumable exact L2 GT."""
from common import *
import sys, urllib.request, shutil, importlib.util

LEARN_POOL = 50000
def prefix(url, path, size):
    path=Path(path);meta=path.with_suffix(path.suffix+'.source.json')
    if meta.exists():
        m=json.loads(meta.read_text());assert path.stat().st_size==size and sha(path)==m['sha256'];return
    assert not path.exists(),f'uncommitted download {path}'
    path.parent.mkdir(parents=True,exist_ok=True)
    request_url=url+('?e97_prefix_bytes='+str(size))
    req=urllib.request.Request(request_url,headers={'Range':f'bytes=0-{size-1}'})
    t=time.time();tmp=path.with_suffix(path.suffix+'.part');actual=0
    with urllib.request.urlopen(req,timeout=120) as response, tmp.open('wb') as f:
        status=response.status;cr=response.headers.get('Content-Range')
        if status==206:assert cr and cr.startswith('bytes 0-'),cr
        else:assert status==200
        while actual<size:
            data=response.read(min(4*1024**2,size-actual));assert data,'short public download'
            f.write(data);actual+=len(data)
            if actual%(128*1024**2)==0:print('DOWNLOAD',path.name,actual,size,flush=True)
    assert actual==size;tmp.replace(path)
    dump(meta,dict(url=url,request_url=request_url,status=status,content_range=cr,bytes=size,sha256=sha(path),seconds=time.time()-t,scope='prefix; original full-dataset header retained'))

def write_vecs(path, values, dtype='f4'):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');d=values.shape[1]
    with tmp.open('wb') as f:
        for lo in range(0,len(values),16384):
            x=np.empty((min(16384,len(values)-lo),d+1),dtype=dtype)
            x[:,0].view('i4')[:]=d;x[:,1:]=values[lo:lo+len(x)];x.tofile(f)
    tmp.replace(path)

def xbin(path,dtype,n,d):
    with open(path,'rb') as f:header=np.fromfile(f,'u4',2)
    assert header[0]>=n and header[1]==d and Path(path).stat().st_size==8+n*d*np.dtype(dtype).itemsize
    return np.memmap(path,mode='r',offset=8,dtype=dtype,shape=(n,d))

def acquire(ds):
    inp=RUN/'inputs'/ds;inp.mkdir(parents=True,exist_ok=True);ready=inp/'manifest.json'
    if ready.exists():return
    t=time.time()
    if ds=='gist1m_l2_v1':
        old=ROOT/'benches/datasets/GIST1M';basepath=old/'gist_base.fvecs';test=vecs(old/'gist_query.fvecs');learn=vecs(old/'gist_learn.fvecs')
        source=dict(base='existing original local GIST1M file; original download hash unavailable',reference='http://corpus-texmex.irisa.fr/',learn=str(old/'gist_learn.fvecs'),test=str(old/'gist_query.fvecs'))
        expected=(1000000,960)
    elif ds=='deep10m_l2_v1':
        old=ROOT/'benches/datasets/DEEP10M';basepath=old/'base.10M.fvecs';test=vecs(old/'query.public.10K.fvecs')
        url='https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/learn.350M.fbin'
        p=RUN/'sources/deep.learn.prefix.fbin';prefix(url,p,8+LEARN_POOL*96*4);learn=xbin(p,'f4',LEARN_POOL,96)
        # Compare local source fbin and fvecs through complete row bytes below.
        rawbase=xbin(old/'base.10M.fbin','f4',10000000,96)
        assert np.array_equal(test,xbin(old/'query.public.10K.fbin','f4',10000,96))
        source=dict(base='https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/base.10M.fbin',learn=url,test='https://storage.yandexcloud.net/yandex-research/ann-datasets/DEEP/query.public.10K.fbin')
        expected=(10000000,96)
    elif ds=='sift10m_bigann_l2_v1':
        url='https://dl.fbaipublicfiles.com/billion-scale-ann-benchmarks/bigann/'
        for name,n in [('base.1B.u8bin',10000000),('learn.100M.u8bin',LEARN_POOL),('query.public.10K.u8bin',10000)]:
            prefix(url+name,RUN/'sources'/('bigann.'+name),8+n*128)
        rawbase=xbin(RUN/'sources/bigann.base.1B.u8bin','u1',10000000,128)
        basepath=inp/'base.fvecs'
        if not basepath.exists():write_vecs(basepath,rawbase)
        test=xbin(RUN/'sources/bigann.query.public.10K.u8bin','u1',10000,128).astype('f4')
        learn=xbin(RUN/'sources/bigann.learn.100M.u8bin','u1',LEARN_POOL,128)
        source=dict(base=url+'base.1B.u8bin',base_subset='first 10000000',learn=url+'learn.100M.u8bin',test=url+'query.public.10K.u8bin',reference='https://big-ann-benchmarks.com/neurips21.html')
        expected=(10000000,128)
    else:raise ValueError(ds)
    base=vecs(basepath);assert base.shape==expected
    for lo in range(0,len(base),16384):
        b=base[lo:lo+16384];assert np.isfinite(b).all()
        if ds!='gist1m_l2_v1':assert np.array_equal(b,np.asarray(rawbase[lo:lo+len(b)],'f4'))
    assert len(test)==(1000 if ds.startswith('gist') else 10000) and np.isfinite(test).all()
    assert (np.linalg.norm(test,axis=1)>0).all(),'zero test query requires explicit router semantics'
    testhash={hashlib.sha256(np.asarray(row,'f4').tobytes()).digest() for row in test}
    chosen=[];seen=set(testhash)
    for i in range(len(learn)):
        row=np.asarray(learn[i],'f4');assert np.isfinite(row).all()
        h=hashlib.sha256(row.tobytes()).digest()
        if h in seen:continue
        seen.add(h);chosen.append(i)
        if len(chosen)==27048:break
    assert len(chosen)==27048,'not enough independent learn queries'
    selected=np.asarray(learn[chosen],'f4');source_rows=np.asarray(chosen,'i8')
    splits={'qgt':(0,5000),'fit':(5000,25000),'gate_train':(5000,15000),'gate_monitor':(25000,26024),'cal':(26024,27048)}
    for name,(lo,hi) in splits.items():
        write_vecs(inp/(name+'.fvecs'),selected[lo:hi]);selected[lo:hi].tofile(inp/(name+'.f32'));source_rows[lo:hi].tofile(inp/(name+'.source_rows.i64'))
    write_vecs(inp/'test.fvecs',test);np.asarray(test,'f4').tofile(inp/'test.f32')
    paths=dict(base_path=str(basepath),query_path=str(inp/'test.fvecs'),gt_path=str(inp/'test.gt.ivecs'),index=str(RUN/'models'/ds/'nsg/graph.nsg'))
    for name in splits:paths[name+'_query_path']=str(inp/(name+'.fvecs'))
    identities={'base_path':dict(path=str(basepath),bytes=basepath.stat().st_size,sha256=sha(basepath))}
    for name in list(splits)+['test']:
        p=inp/(name+'.fvecs');identities[name+'_query']=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
    dump(ready,dict(dataset=ds,metric_id=1,metric='squared_L2',normalization='none; preserve supplied vectors',shape=list(base.shape),test_rows=len(test),paths=paths,identities=identities,sources=source,split_bounds=splits,source_rows='unique learn rows after excluding exact test/learn duplicates',learn_candidates_examined=chosen[-1]+1,preparation_seconds=time.time()-t))
    print('INPUTS_READY',ds,flush=True)

def gt(ds,name):
    import faiss
    faiss.omp_set_num_threads(16)
    inp=RUN/'inputs'/ds;c=json.loads((inp/'manifest.json').read_text());out=inp/(name+'.gt');out.mkdir(exist_ok=True)
    if (out/'complete.json').exists():return
    base=vecs(c['paths']['base_path']);q=vecs(inp/(name+'.fvecs'));t=time.time()
    index=faiss.IndexFlatL2(base.shape[1]);index.add(np.asarray(base))
    for lo in range(0,len(q),512):
        p=out/f'rows_{lo}.npz'
        if p.exists():continue
        ts=time.time();dist,ids=index.search(np.asarray(q[lo:lo+512]),100)
        assert np.isfinite(dist).all() and (ids>=0).all() and (ids<len(base)).all()
        tmp=p.with_suffix('.npz.tmp')
        with tmp.open('wb') as f:np.savez(f,ids=ids.astype('i4'),dist=dist,seconds=time.time()-ts,source_start=lo)
        tmp.replace(p);print('GT',ds,name,lo+len(ids),len(q),time.time()-t,flush=True)
    parts=[]
    for lo in range(0,len(q),512):
        z=np.load(out/f'rows_{lo}.npz');assert int(z['source_start'])==lo and z['ids'].shape==(min(512,len(q)-lo),100)
        parts.append(z['ids'])
    ids=np.concatenate(parts)
    assert ids.shape==(len(q),100) and (ids>=0).all() and (ids<len(base)).all()
    assert np.all(np.diff(np.sort(ids,axis=1),axis=1)>0),'duplicate exact IDs'
    # Independent direct float64 distance computation over every base row.
    # Ties at the kth boundary are recorded; no alternate IDs are substituted.
    checks=[]
    for qi in sorted(set([0,len(q)-1])):
        best_d=np.empty(0,dtype='f8');best_i=np.empty(0,dtype='i8');query=q[qi].astype('f8')
        for lo in range(0,len(base),16384):
            delta=np.asarray(base[lo:lo+16384],dtype='f8')-query
            values=np.einsum('ij,ij->i',delta,delta);idx=np.argpartition(values,min(99,len(values)-1))[:100]
            ds2=np.concatenate([best_d,values[idx]]);is2=np.concatenate([best_i,lo+idx]);take=np.argsort(ds2,kind='stable')[:100]
            best_d,best_i=ds2[take],is2[take]
        actual=((np.asarray(base[ids[qi]],'f8')-query)**2).sum(axis=1)
        tol=max(1e-7,abs(float(best_d[-1]))*3e-6)
        assert np.max(np.abs(np.sort(actual)-best_d))<=tol,(name,qi,'exact distance disagreement')
        strict=best_i[best_d<best_d[-1]-tol]
        assert set(map(int,strict)).issubset(set(map(int,ids[qi])))
        checks.append(dict(query=qi,full_base_rows=len(base),float64_top100_distance_error=float(np.max(np.abs(np.sort(actual)-best_d))),tolerance=tol,identical_ID_set=bool(set(ids[qi])==set(best_i))))
    write_vecs(inp/(name+'.gt.ivecs'),ids,'i4');ids.tofile(inp/(name+'.gt.i32'))
    if name=='fit':ids[:10000].tofile(inp/'gate_train.gt.i32')
    dump(out/'complete.json',dict(status='PASS',n=len(q),base_sha256=c['identities']['base_path']['sha256'],metric='squared_L2',k=100,threads=16,seconds=time.time()-t,independent_direct_float64_checks=checks,gt_sha256=sha(inp/(name+'.gt.ivecs'))))

if __name__=='__main__':
    if sys.argv[1]=='acquire':acquire(sys.argv[2])
    elif sys.argv[1]=='gt':gt(sys.argv[2],sys.argv[3])
