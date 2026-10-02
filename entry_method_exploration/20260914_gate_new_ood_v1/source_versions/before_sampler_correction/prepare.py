import os
os.environ['OPENBLAS_NUM_THREADS']='16'
from common import *
import argparse, importlib.util, shutil, subprocess, sys

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def inputs(ds):
    out=RUN/'inputs'/ds;out.mkdir(parents=True,exist_ok=True)
    if (out/'manifest.json').exists():return json.loads((out/'manifest.json').read_text())
    start=time.time();c=settings(ds);base=vecs(c['base_path']);graph,stored,meta=nsg_map(c['index'])
    assert base.shape==stored.shape
    for b in range(0,len(base),32768):
        assert np.array_equal(base[b:b+32768].view('u4'),stored[b:b+32768].view('u4'))
        assert np.isfinite(base[b:b+32768]).all()
    identities={}
    for key,path in c.items():
        if key in ('train_path','query_path','gt_path'):continue
        if Path(path).exists():
            print('hash',ds,key,flush=True);identities[key]=dict(path=path,bytes=Path(path).stat().st_size,sha256=sha(path))
    # Public test identity only. No GT scoring or query-dependent selection.
    for key in ('query_path','gt_path'):
        path=c[key];identities[key]=dict(path=path,bytes=Path(path).stat().st_size,sha256=sha(path))
    splitkeys=['acpg_query_path','drl_train_query_path','validation_query_path','query_path']
    seen={};duplicates=[]
    for key in splitkeys:
        a=vecs(c[key]);assert a.shape[1]==base.shape[1]
        for i,row in enumerate(a):
            h=hashlib.sha256(row.tobytes()).digest()
            if h in seen and seen[h][0]!=key:duplicates.append([seen[h],[key,i]])
            else:seen[h]=(key,i)
    assert not duplicates, f'cross-role duplicate queries: {duplicates[:3]}'
    q=vecs(c['drl_train_query_path']);gt=vecs(c['drl_train_gt_path'],'i4')
    for name,lo,hi in [('gate_train',10000,20000),('gate_monitor',2048,3072),('cal',0,1024)]:
        np.asarray(q[lo:hi]).tofile(out/(name+'.f32'));np.asarray(gt[lo:hi]).tofile(out/(name+'.gt.i32'))
    fast=ROOT/'fast_entry_variants'/(ds+('_validation_seed20260828' if ds.startswith('laion') else '_seed20260828'))
    fm=json.loads((fast/'manifest.json').read_text());idsfile=ROOT/fm['variants']['qgt_cover']['ids_file']
    ids=np.fromfile(idsfile,'i4');assert len(ids)==len(set(ids.tolist()))
    # Original Fast binary IDs include an int32 length prefix.
    if ids[0]==len(ids)-1:ids=ids[1:]
    assert len(ids)==fm['variants']['qgt_cover']['selected_hubs']
    ids.tofile(out/'gt10.ids.i32');unit(base[ids]).tofile(out/'gt10.hubs.f32')
    if not ds.startswith('laion'):
        variant='gt10_soft_t1' if ds.startswith('webvid') else 'gt10_hard'
        w=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/models'/ds/variant/'W.f32'
        shutil.copy2(w,out/'gt10.W.f32');profile=dict(variant=variant,source=str(w),sha256=sha(w))
    else:profile=dict(variant='pending_cal_selection',candidate_formula='original E24 GT10')
    result=dict(dataset=ds,paths=c,shape=list(base.shape),graph=meta,identities=identities,split_duplicates=duplicates,profile=profile,preparation_seconds=time.time()-start)
    dump(out/'manifest.json',result);print('INPUTS_READY',ds,flush=True);return result

def features(ds):
    c=inputs(ds);out=RUN/'inputs'/ds
    if (out/'gate_features.json').exists():return
    start=time.time();base=vecs(c['paths']['base_path']);resource_check()
    if ds.startswith('webvid'):
        old=ROOT/'gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/hbkm512_sinkhorn_seed42_v2'
        ids=np.fromfile(old/'hub_ids.int32','i4');hub=vecs(old/'hubs.fvecs')
        assert np.array_equal(base[ids],hub)
        emb=np.load(old/'graph2vec_wl2_d512_e10_mc5_seed42_v1/graph2vec_embedding.npy')
        source=dict(kind='verified_reuse',path=str(old),historical_cost_seconds=None,reason='inherited build; this stage accounts verification only')
    else:
        km=module('e96_kmeans',RUN/'sources/kmeans.py')
        if (out/'gate.ids.i32').exists():
            ids=np.fromfile(out/'gate.ids.i32','i4');hub=base[ids]
        else:
            from resume_hbkm import hbkm
            clusters=hbkm(km,base,out/'hbkm_checkpoints')
            assert len(clusters)==512 and sum(map(len,clusters))==len(base)
            hub,ids=km.extract_hub_nodes(base,clusters);del clusters
            ids.tofile(out/'gate.ids.i32');hub.tofile(out/'gate.hubs.f32')
            dump(out/'hbkm.json',dict(seconds=time.time()-start,hubs=512,k1=32,k2=16,max_iters=20,sinkhorn_iters=10,lambda_penalty=.01,seed=42,ids_sha256=sha(out/'gate.ids.i32')))
        sg=module('e96_subgraph',RUN/'sources/subgraph2json.py');g,_,_=nsg_map(c['paths']['index'])
        class Graph:
            def __len__(self):return len(g)
            def __getitem__(self,i):return g[i][g[i]>=0]
        lo=2**31;hi=0
        for b in range(0,len(g),100000):
            degree=(g[b:b+100000]>=0).sum(axis=1);lo=min(lo,int(degree.min()));hi=max(hi,int(degree.max()))
        sub=out/'subgraphs';sub.mkdir(exist_ok=True);t=time.time()
        for h,id in enumerate(ids):
            p=sub/f'{h}.json'
            if not p.exists():dump(p,sg.sample_graph(int(id),Graph(),base,lo,hi,False))
            if h%64==0:print('subgraphs',ds,h,flush=True)
        dump(out/'subgraphs.json',dict(seconds=time.time()-t,min_degree=lo,max_degree=hi))
        target=out/'graph2vec'
        if not (target/'manifest.json').exists():
            subprocess.run([sys.executable,str(RUN/'sources/graph2vec_embed.py'),str(sub),str(target),'--dimensions',str(base.shape[1])],check=True)
        emb=np.load(target/'graph2vec_embedding.npy');source=dict(kind='new_hbkm_graph2vec',hbkm=str(out/'hbkm.json'),graph2vec=str(target/'manifest.json'))
    assert ids.shape==(512,) and len(set(map(int,ids)))==512 and emb.shape==(512,base.shape[1])
    assert np.isfinite(emb).all() and np.array_equal(base[ids],hub)
    ids.tofile(out/'gate.ids.i32');np.asarray(hub,'f4').tofile(out/'gate.hubs.f32');np.asarray(emb,'f4').tofile(out/'gate.graph2vec.f32')
    dump(out/'gate_features.json',dict(source=source,seconds=time.time()-start,files={p.name:sha(p) for p in [out/'gate.ids.i32',out/'gate.hubs.f32',out/'gate.graph2vec.f32']}))
    print('GATE_FEATURES_READY',ds,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['inputs','features']);p.add_argument('datasets',nargs='*');a=p.parse_args()
    for ds in a.datasets or DATASETS: globals()[a.stage](ds)
