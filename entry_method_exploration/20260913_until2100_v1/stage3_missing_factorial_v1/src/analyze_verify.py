from shared import *
from graph_reader import inspect_serialized
import csv
threads();resources();check(O/'reviews/models_before_queries.json');started=time.monotonic()
assert len(read(O/'logs/jobs.json'))==2 and all(x['status']=='COMPLETE' for x in read(O/'logs/jobs.json'))
allpoints=[];selection=[];cohorts=[];cases=[];interactions=[];scored=parity=graphs=patchrows=0;data={}
def metrics(out,base,sl):
    a=out['hits'][sl].astype(int);b=base['hits'][sl].astype(int);dh=a-b
    total=out['route_ndc'][sl].astype(float)+out['graph_ndc'][sl];den=base['route_ndc'][sl].astype(float)+base['graph_ndc'][sl]
    return dict(queries=len(a),recall_pct=float(a.mean()*10),delta_recall_pp=float(dh.mean()*10),gain_hits=int(np.maximum(dh,0).sum()),loss_hits=int(np.maximum(-dh,0).sum()),net_hits=int(dh.sum()),
        helped=int((dh>0).sum()),harmed=int((dh<0).sum()),failure_queries=int((a==0).sum()),failure_pct=float((a==0).mean()*100),rescued=int(((b==0)&(a>0)).sum()),new_failures=int(((b>0)&(a==0)).sum()),
        mean_route_NDC=float(out['route_ndc'][sl].mean()),mean_graph_NDC=float(out['graph_ndc'][sl].mean()),mean_total_NDC=float(total.mean()),total_NDC_change_pct=float((total.mean()/den.mean()-1)*100),changed_entry_queries=int((out['entries'][sl]!=base['entries'][sl]).any(1).sum()))
for ds in DS:
    c=read(O/'inputs'/ds/'config.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(22048,100);mapping=np.fromfile(c['hub_ids'],np.int32);modelraw={};dest=O/'results'/ds
    assert read(dest/'query_complete.json')['status']=='PASS_NATIVE_MISSING_FACTORIAL'
    for name in LABELS:
        folder=dest/name;out=dict(np.load(folder/'raw.npz'));patch=dict(np.load(folder/'patch.npz'));iden=read(folder/'identity.json')
        parent=dict(np.load(E61/'results'/ds/('missing_lambda05' if name=='A' else 'baseline')/'raw.npz'))
        W=np.fromfile(O/'models'/ds/name/'W.f32',np.float32).reshape(c['hub_count'],c['dim']);target=np.load(O/'models'/ds/name/'topology.npz')['topology']
        assert digest(W)==iden['W_sha'] and sha(folder/'graph.hnsw')==iden['graph_sha']
        assert inspect_serialized(folder/'graph.hnsw',W,mapping)['topology_sha']==iden['topology_sha']==digest(target)==digest(np.load(folder/'topology.npz')['topology'])
        assert raw_digest(out)==iden['cache_sha']==str(patch['cache_sha']) and str(patch['parent_cache_sha'])==raw_digest(parent)
        changed=np.flatnonzero((out['entries']!=parent['entries']).any(1));assert np.array_equal(changed,patch['changed_rows']) and len(changed)==iden['new_NSG']
        keep=np.ones(22048,bool);keep[changed]=False;patchrows+=len(changed)
        for k in ['ids','distances','graph_ndc']:assert out[k][keep].tobytes()==parent[k][keep].tobytes() and out[k][changed].tobytes()==patch[k].tobytes()
        assert out['entries'][changed].tobytes()==patch['entries'].tobytes() and out['route_ndc'].tobytes()==patch['route_ndc'].tobytes()
        assert (np.diff(out['entries'],axis=1)>0).all() and np.isin(out['entries'],mapping).all()
        assert np.isfinite(out['distances']).all() and all(len(set(map(int,row)))==10 for row in out['ids'])
        assert np.array_equal(ihits(out['ids'],gt),out['hits'])
        masks=np.array([sum((1<<r) for r,g in enumerate(row[:10]) if int(g) in set(map(int,ret))) for ret,row in zip(out['ids'],gt)],np.uint16)
        assert np.array_equal(masks,out['hitmask']);scored+=22048
        pr=dict(np.load(folder/'parity.npz'));equal(pr,{k:out[k][pr['local_rows']] for k in FIELDS});parity+=64;graphs+=1
        if name in ['C','A']:equal(out,parent)
        modelraw[name]=out
    data[ds]=modelraw;base=modelraw['C']
    for name in LABELS:
        for phase,sl in [('fit',slice(0,20000)),('cal',slice(20000,21024))]:allpoints.append(dict(dataset=ds,model=name,phase=phase,**metrics(modelraw[name],base,sl)))
    eligible=[];rules={}
    for name in ['S','T']:
        p=next(x for x in allpoints if x['dataset']==ds and x['model']==name and x['phase']=='cal')
        b=next(x for x in allpoints if x['dataset']==ds and x['model']=='C' and x['phase']=='cal')
        rules[name]=dict(net_positive=p['net_hits']>0,failures_nonincreasing=p['failure_queries']<=b['failure_queries'],total_NDC_within_one_percent=p['total_NDC_change_pct']<=1)
        if all(rules[name].values()):eligible.append(p)
    eligible.sort(key=lambda p:(-p['net_hits'],p['mean_total_NDC'],p['model']))
    selection.append(dict(dataset=ds,selected=eligible[0]['model'] if eligible else 'C',eligible=[p['model'] for p in eligible],rules=rules,audit_selectable=False))
dump(O/'results/selection.json',dict(status='FROZEN_CAL_SELECTION',datasets=selection,model_freeze_sha=sha(O/'reviews/models_before_queries.json'),rule_sha=sha(O/'config.locked.json')))
for ds in DS:
    raw=data[ds];base=raw['C'];c=read(O/'inputs'/ds/'config.json');source=np.fromfile(c['row_ids'],np.int64)
    for name in LABELS:allpoints.append(dict(dataset=ds,model=name,phase='audit',**metrics(raw[name],base,slice(21024,22048))))
    H=np.stack([raw[n]['hits'].astype(np.int16) for n in LABELS]);I=H[1]-H[2]-H[3]+H[0]
    save(O/'results'/ds/'aligned_effects.npz',source_rows=source,model_names=np.array(LABELS),hits=H,interaction=I)
    for phase,sl in [('fit',slice(0,20000)),('cal',slice(20000,21024)),('audit',slice(21024,22048))]:
        interactions.append(dict(dataset=ds,phase=phase,total=int(I[sl].sum()),nonzero_queries=int((I[sl]!=0).sum()),positive_mass=int(np.maximum(I[sl],0).sum()),negative_mass=int(np.maximum(-I[sl],0).sum())))
        for b in range(11):
            rows=np.arange(22048)[sl][base['hits'][sl]==b]
            if len(rows)==0:continue
            for name in ['A','S','T']:
                p=metrics(raw[name],base,rows);mb=base['hitmask'][rows];ma=raw[name]['hitmask'][rows]
                gained=sum(int(x).bit_count() for x in ma&(~mb)&1023);lost=sum(int(x).bit_count() for x in mb&(~ma)&1023)
                assert gained-lost==p['net_hits']
                cohorts.append(dict(dataset=ds,phase=phase,base_hits=b,model=name,member_gained=gained,member_lost=lost,**p))
    catastrophe=np.flatnonzero((H[0,:20000]==10)&(H[1,:20000]==0));assert len(catastrophe)==(14 if ds==DS[0] else 20)
    for r in catastrophe:
        cases.append(dict(dataset=ds,local_row=int(r),namespace=c['namespace'],source_row=int(source[r]),C=int(H[0,r]),A=int(H[1,r]),S=int(H[2,r]),T=int(H[3,r]),interaction=int(I[r]),
            S_zero=bool(H[2,r]==0),T_zero=bool(H[3,r]==0),S_entries=' '.join(map(str,raw['S']['entries'][r])),T_entries=' '.join(map(str,raw['T']['entries'][r]))))
for name,items in [('points',allpoints),('fit_cal_audit_hit_cohorts',cohorts),('catastrophic_cases',cases),('interactions',interactions)]:
    with (O/'results'/f'{name}.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(items[0]));w.writeheader();w.writerows(items)
costs=[read(O/'results'/ds/'query_complete.json') for ds in DS]
assert scored==176384 and parity==512 and graphs==8 and sum(x['NSG_calls'] for x in costs)==patchrows+1536
dump(O/'results/cost.json',dict(datasets=costs,NSG_calls=patchrows+1536,HNSW_calls=177408,builds=8,topology_installations=4,new_cross_state_NSG=patchrows,
    reused_E61_control_rows=88192,model_NSG_rows_reused=88192-patchrows,native_phase_seconds=sum(x['seconds'] for x in costs),new_GT=0,gradient_updates=0,formal_QPS_points=0))
dump(O/'reviews/verification.json',dict(status='PASS',independent_set_scores=scored,independent_GT10_masks=scored,physical_graphs=graphs,three_way_parity_rows=parity,full_CA_route_recovery_rows=88192,cache_checked_rows=scored,catastrophic_cases=34,selection_only_cal=True,all_native_jobs_complete=True,seconds=time.monotonic()-started))
dump(O/'state.json',dict(status='COMPLETE_VERIFIED_MISSING_FACTORIAL',selection=selection,native_pids=[],formal_QPS_points=0))
print(json.dumps(dict(selection=selection,points=allpoints,interactions=interactions),indent=2),flush=True)
