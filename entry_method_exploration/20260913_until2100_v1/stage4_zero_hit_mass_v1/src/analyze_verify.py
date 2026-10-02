from shared import *
from graph_reader import inspect_serialized
import csv
threads();resources();check(O/'reviews/models_before_queries.json');started=time.monotonic()
assert read(O/'reviews/profile_verification.json')['status']=='PASS_INDEPENDENT_STREAMING_PROFILE_REFERENCE'
assert all(x['status']=='COMPLETE' for x in read(O/'logs/jobs.json')) and len(read(O/'logs/jobs.json'))==2
allpoints=[];contrasts=[];selection=[];scored=parity=graphs=patchrows=0;data={}

def metrics(out,base,sl):
    a=out['hits'][sl].astype(int);b=base['hits'][sl].astype(int);dh=a-b
    total=out['route_ndc'][sl].astype(float)+out['graph_ndc'][sl];den=base['route_ndc'][sl].astype(float)+base['graph_ndc'][sl]
    rec=dict(queries=len(a),recall_pct=float(a.mean()*10),delta_recall_pp=float(dh.mean()*10),gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),net_hits=int(dh.sum()),
        helped=int((dh>0).sum()),harmed=int((dh<0).sum()),failure_queries=int((a==0).sum()),failure_pct=float((a==0).mean()*100),
        rescued=int(((b==0)&(a>0)).sum()),new_failures=int(((b>0)&(a==0)).sum()),
        mean_route_NDC=float(out['route_ndc'][sl].mean()),mean_graph_NDC=float(out['graph_ndc'][sl].mean()),mean_total_NDC=float(total.mean()),total_NDC_change_pct=float((total.mean()/den.mean()-1)*100),
        changed_entry_queries=int((out['entries'][sl]!=base['entries'][sl]).any(1).sum()))
    assert rec['gain_hits']-rec['loss_hits']==rec['net_hits']
    assert rec['rescued']-rec['new_failures']==int((b==0).sum()-(a==0).sum())
    if len(a)==1024:
        idx=np.random.default_rng(20260913).integers(0,1024,size=(2000,1024));ci=np.quantile(dh[idx].mean(1)*10,[.025,.975]);rec.update(delta_recall_pp_ci_low=float(ci[0]),delta_recall_pp_ci_high=float(ci[1]))
    else:rec.update(delta_recall_pp_ci_low=None,delta_recall_pp_ci_high=None)
    return rec

for ds in DS:
    c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(22048,100);mapping=np.fromfile(c['hub_ids'],np.int32)
    anchor=dict(np.load(O/'inputs'/ds/'baseline.npz'));modelraw={};dest=O/'results'/ds
    assert read(dest/'query_complete.json')['status']=='PASS_NATIVE_ZERO_MASS_COMPARISON'
    for name in LABELS:
        folder=dest/name;out=dict(np.load(folder/'raw.npz'));patch=dict(np.load(folder/'patch.npz'));iden=read(folder/'identity.json')
        W=np.fromfile(O/'models'/ds/name/'W.f32',np.float32).reshape(c['hub_count'],c['dim'])
        assert digest(W)==iden['W_sha'] and sha(folder/'graph.hnsw')==iden['graph_sha']
        assert inspect_serialized(folder/'graph.hnsw',W,mapping)['topology_sha']==iden['topology_sha']==digest(np.load(folder/'topology.npz')['topology'])
        assert raw_digest(out)==iden['cache_sha']==str(patch['cache_sha']) and str(patch['parent_cache_sha'])==raw_digest(anchor)
        changed=np.flatnonzero((out['entries']!=anchor['entries']).any(1));assert np.array_equal(changed,patch['changed_rows']) and len(changed)==iden['new_NSG']
        keep=np.ones(22048,bool);keep[changed]=False;patchrows+=len(changed)
        for k in ['ids','distances','graph_ndc']:
            assert out[k][keep].tobytes()==anchor[k][keep].tobytes() and out[k][changed].tobytes()==patch[k].tobytes()
        assert out['entries'][changed].tobytes()==patch['entries'].tobytes() and out['route_ndc'].tobytes()==patch['route_ndc'].tobytes()
        assert (np.diff(out['entries'],axis=1)>0).all() and np.isin(out['entries'],mapping).all()
        assert np.isfinite(out['distances']).all() and all(len(set(map(int,row)))==10 for row in out['ids'])
        h=ihits(out['ids'],gt);assert np.array_equal(h,out['hits'])
        masks=np.array([sum((1<<r) for r,g in enumerate(row[:10]) if int(g) in set(map(int,ret))) for ret,row in zip(out['ids'],gt)],np.uint16)
        assert np.array_equal(masks,out['hitmask']);scored+=22048
        pr=dict(np.load(folder/'parity.npz'));equal(pr,{k:out[k][pr['local_rows']] for k in FIELDS});parity+=64;graphs+=1
        if name=='baseline':equal(out,anchor)
        modelraw[name]=out
    data[ds]=modelraw
    for name in LABELS:
        for phase,sl in [('fit',slice(0,20000)),('cal',slice(20000,21024))]:
            allpoints.append(dict(dataset=ds,model=name,phase=phase,**metrics(modelraw[name],anchor,sl)))
    cal=next(x for x in allpoints if x['dataset']==ds and x['model']=='zero_mass2' and x['phase']=='cal')
    calbase=next(x for x in allpoints if x['dataset']==ds and x['model']=='baseline' and x['phase']=='cal')
    rules=dict(net_positive=cal['net_hits']>0,failures_nonincreasing=cal['failure_queries']<=calbase['failure_queries'],total_NDC_within_one_percent=cal['total_NDC_change_pct']<=1)
    selection.append(dict(dataset=ds,selected='zero_mass2' if all(rules.values()) else 'baseline',rules=rules,source='cal only; frozen rule; audit not an argument',sham_selectable=False))
# Freeze deterministic cal selection before constructing audit comparisons.
dump(O/'results/selection.json',dict(status='FROZEN_CAL_SELECTION',datasets=selection,models_freeze_sha=sha(O/'reviews/models_before_queries.json'),rule_sha=sha(O/'config.locked.json')))
for ds in DS:
    raw=data[ds];base=raw['baseline']
    for name in LABELS:allpoints.append(dict(dataset=ds,model=name,phase='audit',**metrics(raw[name],base,slice(21024,22048))))
    for phase,sl in [('fit',slice(0,20000)),('cal',slice(20000,21024)),('audit',slice(21024,22048))]:
        contrasts.append(dict(dataset=ds,contrast='zero_mass_minus_sham',phase=phase,**metrics(raw['zero_mass2'],raw['sham_mass2'],sl)))
    save(O/'results'/ds/'aligned_effects.npz',source_rows=np.fromfile(read(O/'inputs'/ds/'config.json')['row_ids'],np.int64),
         hits=np.stack([raw[n]['hits'] for n in LABELS]),delta_hits=np.stack([raw[n]['hits'].astype(np.int16)-base['hits'] for n in LABELS]),model_names=np.array(LABELS))
for name,rows in [('points',allpoints),('target_identity_contrast',contrasts)]:
    with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS]
assert scored==132288 and parity==384 and graphs==6
assert sum(x['NSG_calls'] for x in costs)==patchrows+1152
dump(O/'results/cost.json',dict(datasets=costs,NSG_calls=sum(x['NSG_calls'] for x in costs),HNSW_calls=133056,builds=6,new_model_changed_entry_NSG=patchrows,
      historical_baseline_rows_reused=44096,model_NSG_rows_reused=sum(sum(m['reused_NSG_rows'] for m in x['models'] if m['model']!='baseline') for x in costs),
      native_phase_seconds=sum(x['seconds'] for x in costs),new_GT=0,gradient_updates=0,formal_QPS_points=0))
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,independent_GT10_masks=scored,physical_graphs=graphs,three_way_parity_rows=parity,
      full_baseline_route_recovery_rows=44096,cache_checked_rows=132288,selection_only_cal=True,all_native_jobs_complete=True,seconds=time.monotonic()-started))
dump(O/'state.json',dict(status='COMPLETE_VERIFIED_ZERO_MASS_DEVELOPMENT',selection=selection,next_action='Report all fit/cal/audit gains and damage; no formal QPS claim',formal_QPS_points=0))
print(json.dumps(dict(selection=selection,points=allpoints,contrasts=contrasts),indent=2),flush=True)
