"""Validate corrected training and identities, then freeze before test scoring."""
from common import *
import torch
from train_gate import Tower, release_samples
torch.set_num_threads(16);torch.set_num_interop_threads(1)
assert (RUN/'preparation.complete.json').exists()
records=[];protected={};t=time.time()
for ds in DATASETS:
    inp=RUN/'inputs'/ds;model=RUN/'models'/ds;c=json.loads((inp/'manifest.json').read_text());d=c['shape'][1]
    hops=np.concatenate([np.fromfile(inp/'labels'/f'rows_{lo}.hop.i32','i4').reshape(-1,512) for lo in range(0,11024,128)])
    pos,neg=release_samples(hops);assert all(not set(p)&set(n) for p,n in zip(pos,neg))
    pairs=np.fromfile(inp/'gate.triplets.i32','i4').reshape(-1,3)
    assert not np.any(pairs[:,1]==pairs[:,2])
    best=hops.min(axis=1);assert np.all(hops[pairs[:,1],pairs[:,0]]==best[pairs[:,1]])
    assert np.all(hops[pairs[:,2],pairs[:,0]]>best[pairs[:,2]])
    gate=model/GATE_MODEL;gc=json.loads((gate/'config.json').read_text());done=json.loads((gate/'complete.json').read_text())
    assert gc['label_rule']=='disjoint_positive_negative_v1' and done['status']=='COMPLETE'
    net=Tower(d);net.load_state_dict(torch.load(gate/'best.pt',map_location='cpu',weights_only=True));net.eval()
    node=torch.from_numpy(np.fromfile(inp/'gate.hubs.f32','f4').reshape(512,d));graph=torch.from_numpy(np.fromfile(inp/GATE_GRAPH_FILE,'f4').reshape(512,d))
    with torch.no_grad():w=torch.nn.functional.normalize(net(node,graph),dim=1).numpy()
    saved=np.fromfile(gate/'W.f32','f4').reshape(512,d);np.testing.assert_allclose(w,saved,rtol=3e-5,atol=3e-6)
    base=vecs(c['paths']['base_path']);g,v,meta=nsg_map(c['paths']['index']);assert base.shape==v.shape==tuple(c['shape'])
    for lo in range(0,len(base),32768):assert np.array_equal(base[lo:lo+32768].view('u4'),v[lo:lo+32768].view('u4'))
    gids=np.fromfile(inp/'gt10.ids.i32','i4');assert np.all(np.diff(gids)>0)
    if c['metric_id']==1:
        fm=json.loads((inp/'graph2vec_release10_v2/manifest.json').read_text());assert fm['environment']['pythonhashseed']=='0' and fm['algorithm']['workers']==1
    if ds.startswith(('webvid','yandex')):
        oldids=ROOT/'entry_method_exploration/20260910_gt_topk_profiles_v1/inputs'/ds/'hub_ids.i32'
        assert np.array_equal(gids,np.fromfile(oldids,'i4'))
    for name in ['gt10_hard','gt10_soft_t1']:
        z=np.fromfile(model/name/'W.f32','f4').reshape(len(gids),d);assert np.isfinite(z).all()
        np.testing.assert_allclose(np.linalg.norm(z,axis=1),1,atol=2e-6)
    hm=json.loads((model/'hnsw/complete.json').read_text());assert hm['metric_id']==c['metric_id'] and hm['base_sha256']==c['identities']['base_path']['sha256']
    important=[Path(c['paths']['base_path']),Path(c['paths']['index']),inp/'manifest.json',inp/'gate.ids.i32',inp/'gt10.ids.i32',inp/'gate.triplets.i32',gate/'best.pt',gate/'W.f32',model/'gt10_hard/W.f32',model/'gt10_soft_t1/W.f32',model/'hnsw/full.topology.gz']
    important += [p for p in inp.iterdir() if p.is_file() and p.suffix in ['.f32','.fvecs','.ivecs','.i32','.i64','.json']]
    for p in dict.fromkeys(important):
        protected[str(p)]=dict(bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns,sha256=sha(p))
    records.append(dict(dataset=ds,status='PASS',train_triplets=len(pairs),positive_negative_overlap=0,identical_positive_negative_queries=0,checkpoint_export_max_abs=float(np.abs(w-saved).max()),metric_id=c['metric_id'],base_shape=c['shape'],training_epochs=done['epochs'],training_seconds=done['training_seconds'],test_exposure='historical public test already used in earlier work' if ds.startswith(('webvid','yandex')) else 'public queries identity checked; no test scoring before freeze'))
    del net,base,g,v
    print('MODEL_VERIFIED',ds,flush=True)
native=json.loads((RUN/'reviews/changes_verified.json').read_text())
for name,h in native['code'].items():
    if name.endswith(('.hpp','.cpp')):assert sha(RUN/'src'/name)==h,('native changed after verified',name)
sources={str(p):sha(p) for folder in ['src','sources','bin'] for p in (RUN/folder).rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.suffix not in ['.fbin','.u8bin']}
dump(RUN/'reviews/frozen_models.json',dict(status='PASS',unix=time.time(),seconds=time.time()-t,datasets=records,protected=protected,sources=sources,config_sha256=sha(RUN/'config.locked.json')))
