"""Verify immutable E96 inputs and reuse compatible structures, never old training labels."""
from common import *
import shutil, sys
OLD=ROOT/'entry_method_exploration/20260914_gate_new_ood_v1'
E24=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1'

def materialize_public_test_prefix(c, inp, n=10000):
    """Materialize the fixed E96/E97 public-query prefix for strict readers."""
    q=vecs(c['paths']['query_path']);gt=vecs(c['paths']['gt_path'],'i4')
    assert len(q)==len(gt) and len(q)>=n and gt.shape[1]==100
    assert q.shape[1]==c['shape'][1] and np.isfinite(q[:n]).all()
    if len(q)==n:return c
    selection=dict(rule='first n rows, fixed before results; same rows as E96',start=0,stop=n,source_rows=len(q),sources={})
    for key,array,name in [('query_path',q,'public_test10k.fvecs'),('gt_path',gt,'public_test10k.gt.ivecs')]:
        source=Path(c['paths'][key]);identity=c['identities'][key]
        assert sha(source)==identity['sha256'] and source.stat().st_size==identity['bytes']
        selection['sources'][key]=dict(identity)
        size=n*(array.shape[1]+1)*4
        with source.open('rb') as f:prefix=f.read(size)
        assert len(prefix)==size
        dest=inp/name
        if dest.exists():assert dest.read_bytes()==prefix
        else:
            tmp=dest.with_suffix(dest.suffix+'.tmp');tmp.write_bytes(prefix);tmp.replace(dest)
        actual=vecs(dest,'i4' if key=='gt_path' else 'f4')
        assert actual.shape==(n,array.shape[1]) and np.array_equal(actual.view('u4'),array[:n].view('u4'))
        c['paths'][key]=str(dest)
        c['identities'][key]=dict(path=str(dest),bytes=size,sha256=sha(dest))
        alias='drl_test_gt_path' if key=='gt_path' else 'drl_test_query_path'
        if alias in c['paths']:
            c['paths'][alias]=str(dest);c['identities'][alias]=dict(c['identities'][key])
    c['public_test_selection']=selection
    return c

def reuse(ds):
    assert ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
    inp=RUN/'inputs'/ds;inp.mkdir(parents=True,exist_ok=True)
    if (inp/'reuse.complete.json').exists():return
    source=OLD/'inputs'/ds;c=json.loads((source/'manifest.json').read_text());t=time.time();protected={}
    for key in ['base_path','index','query_path','gt_path']:
        rec=c['identities'][key];p=Path(rec['path']);assert p.stat().st_size==rec['bytes'] and sha(p)==rec['sha256'],key
        protected[str(p)]=rec
    base=vecs(c['paths']['base_path']);g,stored,meta=nsg_map(c['paths']['index'])
    for lo in range(0,len(base),32768):assert np.array_equal(base[lo:lo+32768].view('u4'),stored[lo:lo+32768].view('u4'))
    names=['gate.ids.i32','gate.hubs.f32',GATE_GRAPH_FILE,GATE_FEATURE_READY,'gt10.ids.i32','gt10.hubs.f32']
    names += [name+suffix for name in ['gate_train','gate_monitor','cal'] for suffix in ['.f32','.gt.i32']]
    for name in names:
        p=source/name;h=sha(p);protected[str(p)]=dict(bytes=p.stat().st_size,sha256=h)
        if (inp/name).exists():assert sha(inp/name)==h
        else:shutil.copy2(p,inp/name)
    assert not (inp/'gate.triplets.i32').exists(),'reuse stage must precede corrected label generation'
    if not (inp/'labels').exists():(inp/'labels').symlink_to(source/'labels',target_is_directory=True)
    for p in sorted((source/'labels').iterdir()):
        if p.is_file():protected[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
    ids=np.fromfile(inp/'gate.ids.i32','i4');assert np.array_equal(base[ids],np.fromfile(inp/'gate.hubs.f32','f4').reshape(512,-1))
    profiles={}
    for variant in ['gt10_hard','gt10_soft_t1']:
        p=E24/'models'/ds/variant/'W.f32';out=RUN/'models'/ds/variant;out.mkdir(parents=True,exist_ok=True)
        h=sha(p);shutil.copy2(p,out/'W.f32');protected[str(p)]=dict(bytes=p.stat().st_size,sha256=h)
        dump(out/'complete.json',dict(status='PASS',kind='verified_frozen_E24_profile',source=str(p),sha256=h))
        profiles[variant]=str(out/'W.f32')
    hs=OLD/'models'/ds/'hnsw';out=RUN/'models'/ds/'hnsw';out.mkdir(parents=True,exist_ok=True)
    hm=json.loads((hs/'complete.json').read_text());assert hm['status']=='PASS' and hm['base_sha256']==c['identities']['base_path']['sha256']
    hp=hs/'full.topology.gz';h=sha(hp);protected[str(hp)]=dict(bytes=hp.stat().st_size,sha256=h)
    if not (out/'full.topology.gz').exists():(out/'full.topology.gz').symlink_to(hp)
    dump(out/'complete.json',hm|dict(metric_id=0,reuse_source=str(hs),topology_sha256=h,new_build_seconds=0))
    c.update(metric_id=0,metric='raw_inner_product',test_rows=10000,reuse_source=str(source),profiles=profiles)
    c=materialize_public_test_prefix(c,inp,c['test_rows'])
    dump(inp/'manifest.json',c)
    dump(inp/'reuse.complete.json',dict(status='PASS',seconds=time.time()-t,protected=protected,labels='only immutable hop/return caches reused; corrected triplets generated in E97'))
    print('IP_REUSE_READY',ds,flush=True)

if __name__=='__main__':reuse(sys.argv[1])
