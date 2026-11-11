"""Prepare only the two missing GATE baselines using existing non-test roles."""
from pathlib import Path
import sys, os, json, time, importlib.util, subprocess, hashlib
RUN=Path(__file__).resolve().parents[1]
ROOT=RUN.parents[1]
sys.path.insert(0,str(RUN/'src'))
from common import dump,sha,nsg_map,resource_check
import numpy as np

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def inputs(ds):
    out=RUN/'inputs'/ds;out.mkdir(exist_ok=True)
    if (out/'manifest.json').exists():return json.loads((out/'manifest.json').read_text())
    old=ROOT/'entry_method_exploration/20261016_m5_multimodal_transfer_v1'
    prep=old/'inputs'/ds/'prepared';models=old/'models'/ds
    c=json.loads((ROOT/'entry_method_exploration/20261017_gt10_residual_comprehensive_v1/configs'/f'{ds}.benchmark.json').read_text())
    n=c['base']['n'];d=c['base']['d']
    q=np.memmap(prep/'residual.f32',dtype='<f4',mode='r',shape=(16000,d))
    gt=np.memmap(models/'exact/residual.gt100.i64',dtype='<i8',mode='r',shape=(16000,100))
    test=np.memmap(prep/'test.f32',dtype='<f4',mode='r',shape=(c['queries']['n'],d))
    qhash=[hashlib.sha256(x.tobytes()).digest() for x in q[:11024]]
    thash={hashlib.sha256(x.tobytes()).digest() for x in test}
    assert len(set(qhash))==11024 and not set(qhash)&thash
    gids=np.fromfile(prep/'source_group_ids.i64','<i8')
    rows=np.fromfile(prep/'residual.source_rows.i64','<i8')[:11024]
    trows=np.fromfile(prep/'test.source_rows.i64','<i8')
    assert not set(gids[rows])&set(gids[trows])
    assert not set(gids[rows[:10000]])&set(gids[rows[10000:]])
    for role,a,b in [('gate_train',0,10000),('gate_monitor',10000,11024)]:
        np.asarray(q[a:b]).tofile(out/(role+'.f32'))
        np.asarray(gt[a:b],dtype='<i4').tofile(out/(role+'.gt.i32'))
    g,stored,meta=nsg_map(c['index']);base=np.memmap(prep/'base.f32',dtype='<f4',mode='r',shape=(n,d))
    for a in range(0,n,8192):assert np.array_equal(stored[a:a+8192].view('u4'),base[a:a+8192].view('u4'))
    result={'dataset':ds,'shape':[n,d],'metric_id':0,'paths':{'index':c['index'],'base_path':str(prep/'base.f32')},'graph':meta,
      'roles':{'train':[0,10000],'monitor':[10000,11024],'source':str(prep/'residual.f32'),'gt_source':str(models/'exact/residual.gt100.i64')},
      'exact_vector_and_identity_groups_disjoint_from_test':True,'GATE_train_monitor_disjoint':True,'roles_overlap_B32_supervision':True,
      'identities':{str(p):sha(p) for p in [prep/'residual.f32',models/'exact/residual.gt100.i64',prep/'test.f32',prep/'residual.source_rows.i64',prep/'test.source_rows.i64']}}
    dump(out/'manifest.json',result);return result

def features(ds):
    c=inputs(ds);out=RUN/'inputs'/ds
    if (out/'gate_release10_features.json').exists():return
    resource_check();t=time.monotonic();n,d=c['shape']
    base=np.memmap(c['paths']['base_path'],dtype='<f4',mode='r',shape=(n,d))
    km=module('e200_kmeans',RUN/'sources/kmeans.py')
    if not (out/'gate.ids.i32').exists():
        from resume_hbkm import hbkm
        clusters=hbkm(km,base,out/'hbkm_checkpoints');hub,ids=km.extract_hub_nodes(base,clusters)
        np.asarray(ids,dtype='<i4').tofile(out/'gate.ids.i32');np.asarray(hub,dtype='<f4').tofile(out/'gate.hubs.f32')
        dump(out/'hbkm.json',{'seconds':time.monotonic()-t,'seed':42,'k1':32,'k2':16,'source':str(RUN/'sources/kmeans.py')})
    ids=np.fromfile(out/'gate.ids.i32','<i4');hub=np.fromfile(out/'gate.hubs.f32','<f4').reshape(512,d)
    assert len(set(ids))==512 and np.array_equal(base[ids],hub)
    sg=module('e200_subgraph',RUN/'sources/subgraph2json.py');sg.compute_dynamic_sample_size=lambda *args:10
    graph,_,_=nsg_map(c['paths']['index'])
    class Graph:
        def __len__(self):return len(graph)
        def __getitem__(self,i):return graph[i][(graph[i]>=0)&(graph[i]<len(graph))]
    sub=out/'subgraphs_release10_v2';sub.mkdir(exist_ok=True)
    for h,node in enumerate(ids):
        p=sub/f'{h}.json'
        if not p.exists():dump(p,sg.sample_graph(int(node),Graph(),base,0,0,False))
        if h%64==0:print('SUBGRAPHS',ds,h,flush=True)
    target=out/'graph2vec_release10_v2'
    if not (target/'manifest.json').exists():
        subprocess.run([sys.executable,str(RUN/'sources/graph2vec_embed.py'),str(sub),str(target),'--dimensions',str(d)],check=True,env=dict(os.environ,PYTHONHASHSEED='0'))
    emb=np.load(target/'graph2vec_embedding.npy');assert emb.shape==hub.shape and np.isfinite(emb).all()
    np.asarray(emb,dtype='<f4').tofile(out/'gate.release10.graph2vec.f32')
    dump(out/'gate_release10_features.json',{'seconds':time.monotonic()-t,'sampling':'fixed10 5near+5far max5hop max1000nodes','files':{p.name:sha(p) for p in [out/'gate.ids.i32',out/'gate.hubs.f32',out/'gate.release10.graph2vec.f32']}})

if __name__=='__main__':
    assert sys.argv[1] in ['coco','flickr30k'];features(sys.argv[1])
