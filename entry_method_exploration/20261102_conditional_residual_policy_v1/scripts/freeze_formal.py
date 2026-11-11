from common import *
from prepare_matrix import points,NEW
assert read(R/'reviews/calibration_complete.json')['status']=='PASS_TWO_COMPLETE_WALL_CALIBRATIONS'
proposals=[];frozen=[]
for ds in DS:
    cal=read(R/'storage/calibration'/ds/'complete.json')['results'];extra=[]
    for item in cal:
        if item['method'] not in NEW:continue
        K=item['K'];target=1e6/item['qps']
        for control in ['GT10','OPT-B32']:
            grid=sorted([x for x in cal if x['method']==control and x['K']==K],key=lambda x:x['L'])
            # Monotone interpolation only proposes L; all performance measured again.
            costs=np.maximum.accumulate([1e6/x['qps'] for x in grid]);ls=[x['L'] for x in grid]
            centre=int(np.floor(np.interp(target,costs,ls)+.5))
            candidates=[max(100 if K==100 else 1,centre+d) for d in [-2,0,2]]
            extra.extend((K,L,control) for L in candidates)
            proposals.append(dict(dataset=ds,K=K,method=item['method'],L=item['L'],control=control,calibration_mean_us=target,centre_L=centre,proposed=candidates))
    plist=points(extra)
    for window in ['A','B']:
        cfg=read(R/'configs'/f'{ds}.{window}.json')
        cfg.update(model_files=[dict(K=K,L=L,path=str(R/'storage/models'/ds/f'k{K}_L{L}'/'model.json')) for K,L in STATES],points=plist,audit=True)
        dest=R/'configs'/f'{ds}.{window}.formal.json';dump(dest,cfg);frozen.append(dict(path=str(dest),sha256=sha(dest),points=len(plist)))
        for p in plist:pass
csvwrite(R/'analysis/cost_control_proposals.csv',proposals)
historical=read(OLD/'formal_freeze.json'); inherited=[]; large=[]
for ref in historical['files']:
    p=Path(ref['path'])
    if p.parent==REPO:continue
    assert sha(p)==ref['sha256'],str(p)
    inherited.append(ref)
for ref in historical['large_inherited_inputs']:
    if ref.get('dataset') not in DS:continue
    st=Path(ref['path']).stat()
    assert st.st_size==ref['bytes'] and st.st_mtime_ns==ref['mtime_ns'],ref['path']
    large.append(ref)
bound={x['path'] for x in large}
for ds in DS:
    for window in ['A','B']:
        c=read(R/'configs'/f'{ds}.{window}.formal.json')
        for p in [c['base']['path'],c['index']]:
            if p in bound:continue
            st=Path(p).stat();large.append(dict(path=p,bytes=st.st_size,mtime_ns=st.st_mtime_ns,dataset=ds,identity='E195/E197 inherited base or graph, current stat only'));bound.add(p)
        for p in [c['queries']['path'],c['test_gt']['path']]:
            inherited.append(dict(path=p,sha256=sha(p),bytes=Path(p).stat().st_size))
dump(R/'inherited_identity.json',dict(status='PASS_PRIOR_FROZEN_FILES_AND_LARGE_ASSET_STATS',files=inherited,large=large,prior_freeze=dict(path=str(OLD/'formal_freeze.json'),sha256=sha(OLD/'formal_freeze.json'))))
sources=list((R/'src').glob('*'))+list((R/'scripts').glob('*.py'))+[R/'protocol.md',R/'role_freeze.json',R/'storage/formal_benchmark']
sources+=list((R/'storage/models').rglob('model.json'))+list((R/'storage/models').rglob('node_ids.i32'))+list((R/'storage/models').rglob('node_embeddings.f64'))
dump(R/'formal_freeze.json',dict(status='FROZEN_BEFORE_PUBLIC_NEW_RESPONSES',configs=frozen,sources=[dict(path=str(p),sha256=sha(p)) for p in sources if p.is_file()],
    inherited_inputs=read(R/'labels_inputs.json'),inherited_identity_sha256=sha(R/'inherited_identity.json'),model_roles='Q8 state matched, exposed public A/B',total_points=sum(x['points'] for x in frozen)))
print('FORMAL_FROZEN',sum(x['points'] for x in frozen),flush=True)
