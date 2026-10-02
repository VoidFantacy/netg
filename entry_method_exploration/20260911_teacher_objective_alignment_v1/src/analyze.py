from common import *
import csv, collections
import numpy as np

SHORT={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'}
NAMES={'nsg':'NSG','fast30k':'Fast30K','gt1_hard':'GT1 hard','gt10_hard':'GT10 hard',
       'gt1_soft':'GT1 soft','gt10_soft':'GT10 soft','e28_mlp':'Previous MLP',
       'cost_ce':'Cost teacher + CE','keep_ce':'Keep teacher + CE',
       'cost_margin':'Cost teacher + margin','keep_margin':'Keep teacher + margin'}
TARGETS={DS[0]:[.75,.80,.85],DS[1]:[.90,.95,.98]}

def writecsv(name,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (O/'results'/f'{name}.csv').open('w') as f:
        writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)

def array(dest,m,name,dtype):
    return np.fromfile(dest/m['name']/name,dtype)

def bootstrap(values,scale=10.):
    rng=np.random.default_rng(20260911)
    samples=[]
    # Bound temporary memory even for the full fit set.
    for _ in range(100):
        draws=rng.integers(0,len(values),(20,len(values)))
        samples.extend(values[draws].mean(1)*scale)
    return [float(v) for v in np.quantile(samples,[.025,.975])]

def frontier(ms):
    return sorted([m for m in ms if not any(
        other['recall_at_10']>=m['recall_at_10'] and other['qps']>=m['qps'] and
        (other['recall_at_10']>m['recall_at_10'] or other['qps']>m['qps'])
        for other in ms)],key=lambda m:m['recall_at_10'])

def interpolate(ms,recall,repeat=None):
    ms=frontier(ms)
    xs=np.array([m['recall_at_10'] for m in ms])
    if recall<xs.min() or recall>xs.max():return None
    ys=np.array([m['qps'] if repeat is None else m['qps_runs'][repeat] for m in ms])
    return float(np.exp(np.interp(recall,xs,np.log(ys))))

def delta_record(ds,stage,dest,m,base):
    mh=array(dest,m,'hits.u8',np.uint8).astype(float)
    bh=array(dest,base,'hits.u8',np.uint8).astype(float)
    diff=mh-bh
    lo,hi=bootstrap(diff)
    a=array(dest,m,'entry_ids.i32',np.int32).reshape(-1,3)
    b=array(dest,base,'entry_ids.i32',np.int32).reshape(-1,3)
    unchanged=(a==b).all(1)
    for name,dtype,width in [('ids.i32',np.int32,10),('distances.f32',np.uint32,10),('graph_ndc.u32',np.uint32,1)]:
        av=array(dest,m,name,dtype).reshape(-1,width)
        bv=array(dest,base,name,dtype).reshape(-1,width)
        assert np.array_equal(av[unchanged],bv[unchanged]),(ds,stage,m['name'],name)
    return dict(dataset=SHORT[ds],stage=stage,method=m['model_name'],L=m['L'],
                exact=m['configuration'].get('exact',False),queries=len(diff),
                delta_recall_pp=float(diff.mean()*10),ci_low_pp=lo,ci_high_pp=hi,
                delta_qps_pct=None if m['qps'] is None else (m['qps']/base['qps']-1)*100,
                delta_graph_ndc_pct=(m['mean_graph_ndc']/base['mean_graph_ndc']-1)*100,
                improved_queries=int((diff>0).sum()),harmed_queries=int((diff<0).sum()),
                gained_hits=int(diff[diff>0].sum()),lost_hits=int(-diff[diff<0].sum()),
                entry_change_pct=float((~unchanged).mean()*100),rescued_zero=int(((bh==0)&(mh>0)).sum()),
                new_zero=int(((bh>0)&(mh==0)).sum()))

def main():
    assert read(O/'state.json')['status']=='EVALUATION_COMPLETE_ANALYSIS_PENDING'
    allrows,checks,comparisons,contrasts,interps,fitgroups,training,alignments=[],[],[],[],[],[],[],[]
    validation={}
    regression_outputs=0
    fit_cache_checks=0
    fit_consistency=[]
    for ds in DS:
        for stage in ['fit','cal','audit','validation']:
            dest=O/'results'/f'{stage}_{ds}'
            result=read(dest/'results.json');c=read(dest/'config.json')
            n=c['num_queries'];gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
            assert np.array_equal(np.fromfile(c['row_ids'],np.int64),np.fromfile(dest/'row_ids.i64',np.int64))
            for m in result['methods']:
                ids=array(dest,m,'ids.i32',np.int32).reshape(n,10)
                found=(ids[:,:,None]==gt[:,None,:]).any(1)
                assert np.array_equal(found.sum(1),array(dest,m,'hits.u8',np.uint8))
                assert np.array_equal((found*(1<<np.arange(10))).sum(1),array(dest,m,'hitmask.u16',np.uint16))
                assert (ids>=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
                for part in ['route','graph']:
                    assert array(dest,m,f'{part}_ndc.u32',np.uint32).mean()==m[f'mean_{part}_ndc']
                assert abs(m['mean_total_ndc']-m['mean_graph_ndc']-m['mean_route_ndc'])<1e-9
                assert m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16 and m['repeated_output_parity']
                if result['timing_repeats']:
                    assert len(m['qps_runs'])==3 and np.median(m['qps_runs'])==m['qps']
                    assert np.allclose(np.array(m['qps_runs'])*np.array(m['end_to_end_seconds']),n,atol=1e-10)
                record=dict(dataset=SHORT[ds],stage=stage,method=m['model_name'],L=m['L'],
                    exact=m['configuration'].get('exact',False),queries=n,recall_pct=m['recall_at_10']*100,
                    total_hits=m['total_hits'],qps=m['qps'],qps_min=m['qps_min'],qps_max=m['qps_max'],
                    graph_ndc=m['mean_graph_ndc'],route_ndc=m['mean_route_ndc'],total_ndc=m['mean_total_ndc'],
                    failed_queries=m['failed_queries'],build_seconds=m['policy_build_seconds'],
                    route_us=None if m['route_only_seconds'] is None else m['route_only_seconds']/n*1e6,
                    graph_us=None if m['graph_only_seconds'] is None else m['graph_only_seconds']/n*1e6,
                    physical_calls=m['physical_graph_calls'])
                for k in range(len(m['qps_runs'])):
                    record[f'qps_repeat_{k+1}']=m['qps_runs'][k]
                    record[f'wall_seconds_repeat_{k+1}']=m['end_to_end_seconds'][k]
                allrows.append(record)
            bykey={(m['model_name'],m['L'],m['configuration'].get('exact',False)):m for m in result['methods']}
            for m in result['methods']:
                if m['model_name'] not in CELLS+['gt10_soft','e28_mlp']:continue
                key=('gt10_hard',m['L'],m['configuration'].get('exact',False))
                comparisons.append(delta_record(ds,stage,dest,m,bykey[key]))
            for L in sorted({m['L'] for m in result['methods']}):
                ms={name:bykey[(name,L,False)] for name in CELLS}
                vals={name:array(dest,m,'hits.u8',np.uint8).astype(float) for name,m in ms.items()}
                ndcs={name:array(dest,m,'graph_ndc.u32',np.uint32).astype(float) for name,m in ms.items()}
                terms={
                    'teacher_under_ce':{'keep_ce':1,'cost_ce':-1},
                    'teacher_under_margin':{'keep_margin':1,'cost_margin':-1},
                    'loss_under_cost':{'cost_margin':1,'cost_ce':-1},
                    'loss_under_keep':{'keep_margin':1,'keep_ce':-1},
                    'interaction':{'keep_margin':1,'cost_margin':-1,'keep_ce':-1,'cost_ce':1}}
                for name,coef in terms.items():
                    diff=sum(vals[key]*weight for key,weight in coef.items())
                    lo,hi=bootstrap(diff)
                    ndc=sum(ndcs[key]*weight for key,weight in coef.items())
                    contrasts.append(dict(dataset=SHORT[ds],stage=stage,L=L,contrast=name,queries=n,
                        delta_recall_pp=float(diff.mean()*10),ci_low_pp=lo,ci_high_pp=hi,
                        delta_graph_ndc=float(ndc.mean()),positive_queries=int((diff>0).sum()),negative_queries=int((diff<0).sum())))
            checks.append(dict(dataset=ds,stage=stage,points=len(result['methods']),query_outputs=n*len(result['methods']),physical_calls=result['physical_graph_calls'],status='PASS'))
            if stage=='fit':
                old=E28/'labels'/ds
                proposals=E28/'inputs'/ds/'proposals'
                ts=np.fromfile(proposals/'triples.i32',np.int32).reshape(n,56,3)
                hubs=np.fromfile(c['hub_ids'],np.int32)
                assert (np.diff(hubs)>0).all()
                stored_ids=np.memmap(old/'ids.i32',np.int32,mode='r',shape=(n,56,10))
                stored_hits=np.fromfile(old/'hits.u8',np.uint8).reshape(n,56)
                stored_ndc=np.fromfile(old/'graph_ndc.u32',np.uint32).reshape(n,56)
                headroom=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool)
                teacher_gain=stored_hits.max(1).astype(float)-array(dest,bykey[('gt10_hard',128,False)],'hits.u8',np.uint8)
                base=bykey[('gt10_hard',128,False)]
                bh=array(dest,base,'hits.u8',np.uint8).astype(float)
                bn=array(dest,base,'graph_ndc.u32',np.uint32).astype(float)
                be=array(dest,base,'entry_ids.i32',np.int32).reshape(n,3)
                original_bs=np.fromfile(O/'inputs'/ds/'teachers/baseline.i32',np.int32).reshape(n,3)
                assert np.array_equal(be,hubs[original_bs])
                for m in result['methods']:
                    entry=array(dest,m,'entry_ids.i32',np.int32).reshape(n,3)
                    local=np.searchsorted(hubs,entry)
                    assert (local<len(hubs)).all()
                    assert np.array_equal(hubs[local],entry)
                    match=(ts==local[:,None,:]).all(2)
                    assert (match.sum(1)<=1).all()
                    known=match.any(1);slots=match.argmax(1);rows=np.arange(n)
                    ids=array(dest,m,'ids.i32',np.int32).reshape(n,10)
                    hits=array(dest,m,'hits.u8',np.uint8).astype(float)
                    ndc=array(dest,m,'graph_ndc.u32',np.uint32).astype(float)
                    assert np.array_equal(ids[known],stored_ids[rows[known],slots[known]])
                    assert np.array_equal(hits[known],stored_hits[rows[known],slots[known]])
                    assert np.array_equal(ndc[known],stored_ndc[rows[known],slots[known]])
                    fit_cache_checks+=int(known.sum())
                    fit_consistency.append(dict(dataset=ds,method=m['model_name'],in_C8_queries=int(known.sum()),outside_C8_queries=int((~known).sum()),cached_native_parity=True))
                    for group,mask in [('all',np.ones(n,bool)),('headroom',headroom),('no_headroom',~headroom)]:
                        diff=hits-bh
                        gained=float(np.maximum(diff[mask],0).sum());lost=float(np.maximum(-diff[mask],0).sum())
                        denominator=float(teacher_gain[mask].sum())
                        retained=float(np.minimum(np.maximum(diff[mask],0),teacher_gain[mask]).sum())
                        fitgroups.append(dict(dataset=SHORT[ds],method=m['model_name'],group=group,queries=int(mask.sum()),
                            baseline_recall_pct=float(bh[mask].mean()*10),recall_pct=float(hits[mask].mean()*10),delta_recall_pp=float(diff[mask].mean()*10),
                            graph_ndc=float(ndc[mask].mean()),baseline_graph_ndc=float(bn[mask].mean()),delta_graph_ndc_pct=float((ndc[mask].mean()/bn[mask].mean()-1)*100),
                            mean_per_query_ndc_change_pct=float(((ndc[mask]/bn[mask]-1)*100).mean()),
                            improved_queries=int((diff[mask]>0).sum()),harmed_queries=int((diff[mask]<0).sum()),gained_hits=int(gained),lost_hits=int(lost),
                            entry_change_pct=float((entry[mask]!=be[mask]).any(1).mean()*100),
                            C8_teacher_gain_retention_pct=None if denominator==0 else retained/denominator*100,
                            outside_C8_queries=int((~known & mask).sum())))
            if stage=='validation':
                validation[ds]=result['methods']
                families={name:[m for m in result['methods'] if m['model_name']==name] for name in NAMES}
                oldres=read(E28/'results'/f'validation_{ds}'/'results.json')['methods']
                mappings={name:name for name in ['nsg','fast30k','gt1_hard','gt10_hard','gt1_soft','gt10_soft']}
                mappings.update(e28_mlp='mlp',cost_ce='linear')
                for name,ms in families.items():
                    for m in ms:
                        if name!='nsg':
                            assert np.array_equal(array(dest,m,'entry_ids.i32',np.int32),array(dest,ms[0],'entry_ids.i32',np.int32))
                            assert sha(dest/(m['name']+'.hnsw'))==sha(dest/(ms[0]['name']+'.hnsw'))
                        if name in mappings:
                            oldm=next(x for x in oldres if x['model_name']==mappings[name] and x['L']==m['L'])
                            olddir=E28/'results'/f'validation_{ds}'/oldm['name']
                            for fname in ['ids.i32','distances.f32','entry_ids.i32','graph_ndc.u32','route_ndc.u32','hits.u8','hitmask.u16']:
                                assert (dest/m['name']/fname).read_bytes()==(olddir/fname).read_bytes(),(ds,name,m['L'],fname)
                            regression_outputs+=n
                targets=sorted(set(TARGETS[ds]+[m['recall_at_10'] for m in families['gt10_hard']]))
                for name,ms in families.items():
                    if name=='gt10_hard':continue
                    for target in targets:
                        base_qps=interpolate(families['gt10_hard'],target);method_qps=interpolate(ms,target)
                        if base_qps is None or method_qps is None:continue
                        ratios=[interpolate(ms,target,k)/interpolate(families['gt10_hard'],target,k) for k in range(3)]
                        row=dict(dataset=SHORT[ds],method=name,recall_target_pct=target*100,baseline_qps=base_qps,method_qps=method_qps,
                            delta_qps_pct=(method_qps/base_qps-1)*100,ratio_min=min(ratios),ratio_max=max(ratios),
                            predeclared_target=target in TARGETS[ds],is_interpolation=True)
                        row.update({f'ratio_repeat_{k+1}':v for k,v in enumerate(ratios)})
                        interps.append(row)
    for m in read(O/'models/training_runs.json'):
        for row in read(O/'models'/m['dataset']/m['cell']/'training_curve.json'):
            training.append(dict(dataset=SHORT[m['dataset']],cell=m['cell'],teacher=m['teacher'],loss=m['loss'],**row))
        for point in read(O/'models'/m['dataset']/m['cell']/'alignment_curve.json'):
            for teacher,groups in point['metrics'].items():
                for group,record in groups.items():
                    alignments.append(dict(dataset=SHORT[m['dataset']],cell=m['cell'],epoch=point['epoch'],reference_teacher=teacher,group=group,**record))
    gates=[]
    for cell in CELLS:
        records=[]
        for ds in DS:
            rows=[r for r in interps if r['dataset']==SHORT[ds] and r['method']==cell and r['predeclared_target']]
            passing=[r for r in rows if r['delta_qps_pct']>=3 and r['ratio_min']>1]
            regression=[r for r in rows if r['delta_qps_pct']<=-3]
            records.append(dict(dataset=SHORT[ds],covered_targets=len(rows),passing_targets=len(passing),regression_targets=len(regression),
                geometric_mean_qps_change_pct=None if not rows else (float(np.exp(np.mean(np.log([1+r['delta_qps_pct']/100 for r in rows]))))-1)*100))
        gates.append(dict(method=cell,gate_applicable=all(r['covered_targets']>=2 for r in records),
            dual_dataset_GO=all(r['passing_targets']>=2 and r['regression_targets']==0 for r in records),datasets=records))
    dump(O/'results/performance_gate.json',dict(scope='Predeclared local exploration; three-repeat coarse-grid interpolation, not measured matched-recall certificate',methods=gates))
    dump(O/'reviews/output_verification.json',dict(status='PASS',jobs=checks,total_points=sum(r['points'] for r in checks),
        total_query_outputs=sum(r['query_outputs'] for r in checks),physical_calls=sum(r['physical_calls'] for r in checks),
        historical_regression_outputs=regression_outputs,fit_native_cache_parity_outputs=fit_cache_checks,
        GT_rescore_all=True,same_entry_same_output=True,across_L_entry_and_HNSW_equal=True))
    dump(O/'results/fit_cache_consistency.json',fit_consistency)
    tables={'all_points':allrows,'differences':comparisons,'factor_contrasts':contrasts,'interpolation':interps,
        'fit_groups':fitgroups,'training_curves':training,'alignment_curves':alignments}
    for name,rows in tables.items():writecsv(name,rows)
    dump(O/'results/analysis_tables.json',tables)
    dump(O/'state.json',dict(status='ANALYSIS_COMPLETE_PLOTS_AND_REPORT_PENDING',real_search_calls=NORMAL_CAP,training_runs=8,heldout_access=False))
    print(json.dumps(read(O/'reviews/output_verification.json')),flush=True)

if __name__=='__main__':main()
