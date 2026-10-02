from common import *
import sys, importlib.util

def protected():
    before=json.loads((RUN/'reviews/protected_sources_before.json').read_text());after=[]
    for item in before:
        actual=sha(item['path']);assert actual==item['sha256'],f'protected source changed: {item["path"]}';after.append(dict(path=item['path'],sha256=actual))
    return after

def web_reuse():
    ds=DATASETS[0];inp=RUN/'inputs'/ds;meta=json.loads((inp/'manifest.json').read_text());old=ROOT/'gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/hbkm512_sinkhorn_seed42_v2';om=json.loads((old/'manifest.json').read_text());assert om['parameters']['k1']==32 and om['parameters']['k2']==16
    assert om['sources']['base_sha256']==meta['identities']['base_path']['sha256']
    assert sha(old/'hub_ids.int32')==om['outputs']['hub_ids_sha256'];assert sha(old/'hubs.fvecs')==om['outputs']['hubs_sha256']
    em=json.loads((old/'graph2vec_wl2_d512_e10_mc5_seed42_v1/manifest.json').read_text());sub=ROOT/em['input']['subgraph_dir'];h=hashlib.sha256()
    for i in range(512):
        p=sub/f'{i}.json';h.update(p.name.encode());h.update(b'\0');h.update(p.read_bytes())
    assert h.hexdigest()==em['input']['combined_sha256']
    graph,_,_=nsg_map(meta['paths']['index']);edges=0
    # Every stored induced directed edge must match the current frozen graph.
    for i in range(512):
        a=json.loads((sub/f'{i}.json').read_text());nodes=set(a['nodes']);assert len(nodes)<=1000 and int(np.fromfile(inp/'gate.ids.i32','i4')[i]) in nodes;expected=[[int(node),int(nb)] for node in sorted(nodes) for nb in graph[node] if nb in nodes]
        assert expected==a['edges'];edges+=len(expected)
    assert sha(old/'graph2vec_wl2_d512_e10_mc5_seed42_v1/graph2vec_embedding.npy')==em['output']['npy_sha256']
    oldids=np.fromfile(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'hub_ids.i32','i4');assert np.array_equal(oldids,np.fromfile(inp/'gt10.ids.i32','i4'))
    rec=dict(status='PASS',hub_count=512,induced_subgraphs_checked=512,edges_checked=edges,HBKM=[32,16],g2v_source_sha256=h.hexdigest(),GT10_mapping_matches_frozen_E24=True)
    dump(RUN/'reviews/web_reuse.json',rec);return rec

def preflight():
    from evaluation_smoke import main as evaluation_smoke
    evaluation_smoke()
    assert sha(RUN/'protocol.md')==json.loads((RUN/'config.locked.json').read_text())['protocol_sha256']
    assert sha(RUN/'hbkm_provenance_amendment.md')==json.loads((RUN/'reviews/hbkm_amendment_lock.json').read_text())['amendment_sha256']
    assert sha(RUN/'sampling_amendment.md')==json.loads((RUN/'reviews/sampling_amendment_lock.json').read_text())['amendment_sha256']
    assert json.loads((RUN/'reviews/topology_smoke/complete.json').read_text())['status']=='PASS'
    records=[];expected=['6fb5b5510b29504de38271be7c343bd5e85a029f5755c7b3d74177cbf1ebbb18','56d1baa271c79ea280d57ee1c7a8359438ffffc98a75cac799051b13fbdbe0ff','9699ad29076d1a1aeb1a2536b55e73654e8611784f2844e9b8d1ae2cd7be6c5f']
    for ds,base_sha in zip(DATASETS,expected):
        inp=RUN/'inputs'/ds;model=RUN/'models'/ds;c=json.loads((inp/'manifest.json').read_text());assert c['identities']['base_path']['sha256']==base_sha
        # Read-only identity refresh includes public files, without quality scoring.
        for value in c['identities'].values():assert sha(value['path'])==value['sha256'],value['path']
        assert json.loads((inp/'labels/parity.json').read_text())['status']=='PASS'
        assert json.loads((inp/'labels/complete.json').read_text())['rows']==11024
        training=json.loads((model/GATE_MODEL/'complete.json').read_text());assert training['status']=='COMPLETE'
        features=json.loads((inp/GATE_FEATURE_READY).read_text())
        for name,digest in features['files'].items():assert sha(inp/name)==digest
        assert json.loads((model/GATE_MODEL/'config.json').read_text())['graph_features_sha256']==sha(inp/GATE_GRAPH_FILE)
        assert sha(model/GATE_MODEL/'best.pt')==training['checkpoint_sha256']
        assert sha(model/GATE_MODEL/'W.f32')==training['best']['embedding_sha256']
        assert json.loads((model/GATE_MODEL/'independence.json').read_text())['status']=='PASS'
        d=c['shape'][1]
        for weights,idsfile in [(inp/'gt10.W.f32',inp/'gt10.ids.i32'),(model/GATE_MODEL/'W.f32',inp/'gate.ids.i32')]:
            ids=np.fromfile(idsfile,'i4');w=np.fromfile(weights,'f4').reshape(len(ids),d);assert np.isfinite(w).all() and np.max(np.abs(np.linalg.norm(w,axis=1)-1))<2e-6
            assert ((ids>=0)&(ids<c['shape'][0])).all() and len(set(map(int,ids)))==len(ids)
        if not ds.startswith('laion'):
            assert np.array_equal(np.fromfile(inp/'gt10.ids.i32','i4'),np.fromfile(ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'hub_ids.i32','i4'))
        hb=json.loads((model/'hnsw/complete.json').read_text());assert hb['status']=='PASS' and hb['base_sha256']==base_sha and hb['nodes']==c['shape'][0]
        records.append(dict(dataset=ds,gate_W_sha256=sha(model/GATE_MODEL/'W.f32'),gt10_W_sha256=sha(inp/'gt10.W.f32'),full_hnsw_topology_sha256=sha(model/'hnsw/full.topology.gz'),training=training,hnsw=hb))
    records[0]['reuse']=web_reuse()
    dump(RUN/'reviews/preflight.json',dict(status='PASS',unix=time.time(),datasets=records,protected_sources=protected(),all_models_frozen_before_test=True,source_hashes={str(p.relative_to(RUN)):sha(p) for p in list((RUN/'src').glob('*.py'))+list((RUN/'src').glob('*.cpp'))+list((RUN/'src').glob('*.hpp'))+list((RUN/'bin').iterdir()) if p.is_file()}))

if __name__=='__main__':globals()[sys.argv[1]]()
