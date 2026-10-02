from common import *
import csv, math, collections
import numpy as np

SHORT={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'}
NAMES={'nsg':'NSG','fast30k':'Fast30K','gt1_hard':'GT1 hard','gt10_hard':'GT10 hard','gt1_soft':'GT1 soft','gt10_soft':'GT10 soft',
       'e28_mlp':'E28 MLP','e29_cost_ce':'E29 CE','e29_cost_margin':'E29 margin','single':'Single teacher',
       'multi':'Equivalent teachers','multi_matched':'Equivalent, matched drift','single_matched':'Single, matched drift'}
DEFAULT={DS[0]:'gt10_soft',DS[1]:'gt10_hard'}
TARGETS={DS[0]:[.75,.80,.85],DS[1]:[.90,.95,.98]}

def writecsv(name,rows):
    if not rows:return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (O/'results'/f'{name}.csv').open('w') as f:
        writer=csv.DictWriter(f,fields);writer.writeheader();writer.writerows(rows)

def array(dest,m,name,dtype):return np.fromfile(dest/m['name']/name,dtype)

def bootstrap(values,scale=10.):
    if np.all(values==values[0]):return [float(values[0]*scale)]*2
    rng=np.random.default_rng(SEED);samples=[]
    for _ in range(100):
        draws=rng.integers(0,len(values),(20,len(values)))
        samples.extend(values[draws].mean(1)*scale)
    return [float(v) for v in np.quantile(samples,[.025,.975])]

def frontier(ms):
    return sorted([m for m in ms if not any(o['recall_at_10']>=m['recall_at_10'] and o['qps']>=m['qps'] and
        (o['recall_at_10']>m['recall_at_10'] or o['qps']>m['qps']) for o in ms)],key=lambda m:(m['recall_at_10'],-m['qps'],m['L']))

def interpolate(ms,recall,repeat=None):
    ms=frontier(ms)
    if not ms or recall<ms[0]['recall_at_10'] or recall>ms[-1]['recall_at_10']:return None
    xs=np.array([m['recall_at_10'] for m in ms]);ys=np.array([m['qps'] if repeat is None else m['qps_runs'][repeat] for m in ms])
    return float(np.exp(np.interp(recall,xs,np.log(ys))))

def frontier_intervals(formal):
    """Descriptive upper envelope of the measured log-linear curves; no new search."""
    intervals=[]
    for ds,points in formal.items():
        curves=collections.defaultdict(list)
        for point in points:curves[point['model_name']].append(point)
        curves={name:frontier(curve) for name,curve in curves.items()}
        lo,hi=min(TARGETS[ds]),max(TARGETS[ds])
        knots=sorted({lo,hi}|{m['recall_at_10'] for curve in curves.values() for m in curve if lo<m['recall_at_10']<hi})
        parts=[]
        for left,right in zip(knots,knots[1:]):
            mid=(left+right)/2;lines={}
            for name,curve in curves.items():
                if interpolate(curve,mid) is None:continue
                a,b=interpolate(curve,left),interpolate(curve,right)
                assert a is not None and b is not None
                slope=(math.log(b)-math.log(a))/(right-left)
                lines[name]=(math.log(a),slope)
            cuts={left,right};names=sorted(lines)
            for i,name in enumerate(names):
                a,s=lines[name]
                for other in names[i+1:]:
                    b,t=lines[other]
                    if abs(s-t)<1e-14:continue
                    cross=left+(b-a)/(s-t)
                    if left+1e-12<cross<right-1e-12:cuts.add(cross)
            cuts=sorted(cuts)
            for a,b in zip(cuts,cuts[1:]):
                midpoint=(a+b)/2
                winner=min(lines,key=lambda name:(-(lines[name][0]+lines[name][1]*(midpoint-left)),name))
                if parts and parts[-1]['method']==winner and abs(parts[-1]['recall_high_pct']/100-a)<1e-10:
                    parts[-1]['recall_high_pct']=b*100
                else:parts.append(dict(dataset=SHORT[ds],method=winner,recall_low_pct=a*100,recall_high_pct=b*100,
                    scope='descriptive log-linear upper envelope within frozen target range; no validated switching policy'))
        intervals.extend(parts)
    return intervals

def delta(dest,m,b):
    n=m['queries'];mh=array(dest,m,'hits.u8',np.uint8).astype(float);bh=array(dest,b,'hits.u8',np.uint8).astype(float)
    diff=mh-bh;lo,hi=bootstrap(diff)
    mn=array(dest,m,'graph_ndc.u32',np.uint32).astype(float);bn=array(dest,b,'graph_ndc.u32',np.uint32).astype(float)
    same=(array(dest,m,'entry_ids.i32',np.int32).reshape(n,3)==array(dest,b,'entry_ids.i32',np.int32).reshape(n,3)).all(1)
    for name,dtype,width in [('ids.i32',np.int32,10),('distances.f32',np.uint32,10),('graph_ndc.u32',np.uint32,1)]:
        av=array(dest,m,name,dtype).reshape(n,width);bv=array(dest,b,name,dtype).reshape(n,width)
        assert np.array_equal(av[same],bv[same]),(m['name'],name)
    return dict(delta_recall_pp=float(diff.mean()*10),ci_low_pp=lo,ci_high_pp=hi,delta_graph_ndc=float((mn-bn).mean()),
        delta_graph_ndc_pct=float((mn.mean()/bn.mean()-1)*100),entry_changed_queries=int((~same).sum()),
        gained_hits=int(np.maximum(diff,0).sum()),lost_hits=int(np.maximum(-diff,0).sum()),improved_queries=int((diff>0).sum()),harmed_queries=int((diff<0).sum()),
        same_L_qps_change_pct=(m['qps']/b['qps']-1)*100 if m['qps'] is not None else None)

def choose_best(formal):
    ratios=[];ranking=[];decisions=[];target_winners=[]
    for ds,ms in formal.items():
        curves=collections.defaultdict(list)
        for m in ms:curves[m['model_name']].append(m)
        default=DEFAULT[ds];targets=TARGETS[ds]
        for name,points in curves.items():
            rows=[]
            for target in targets:
                b=interpolate(curves[default],target);m=interpolate(points,target)
                covered=b is not None and m is not None
                rec=dict(dataset=SHORT[ds],method=name,reference=default,recall_pct=target*100,covered=covered,
                    reference_qps=b,interpolated_qps=m,ratio=m/b if covered else None,
                    change_pct=(m/b-1)*100 if covered else None,interpolation='median Pareto segments in Recall-logQPS; no extrapolation')
                if covered:
                    reps=[interpolate(points,target,i)/interpolate(curves[default],target,i) for i in range(5)]
                    rec.update(ratio_min=min(reps),ratio_max=max(reps),all_repeats_faster=all(r>1. for r in reps),
                        passing_target=m/b>=1.03 and all(r>1. for r in reps),regression_target=m/b<=.97)
                    rec.update({f'ratio_run{i+1}':r for i,r in enumerate(reps)})
                else:rec.update(ratio_min=None,ratio_max=None,all_repeats_faster=False,passing_target=False,regression_target=False)
                ratios.append(rec);rows.append(rec)
            covered=[r for r in rows if r['covered']]
            geo=float(np.exp(np.mean(np.log([r['ratio'] for r in covered])))) if covered else None
            full=len(covered)==len(targets);passes=sum(r['passing_target'] for r in rows);regressions=sum(r['regression_target'] for r in rows)
            ranking.append(dict(dataset=SHORT[ds],method=name,reference=default,covered_targets=len(covered),all_targets_covered=full,
                geomean_ratio=geo,geomean_change_pct=(geo-1)*100 if geo is not None else None,passing_targets=passes,regression_targets=regressions,
                worst_change_pct=min((r['change_pct'] for r in covered),default=None),eligible_replacement=full and passes>=2 and regressions==0))
        rs=[r for r in ranking if r['dataset']==SHORT[ds]]
        complete=[r for r in rs if r['all_targets_covered']]
        order=lambda r:(-r['geomean_ratio'],-r['worst_change_pct'],r['method'])
        fastest=sorted(complete,key=order)[0]
        eligible=sorted([r for r in complete if r['eligible_replacement'] and r['method']!=default],key=order)
        recommended=eligible[0]['method'] if eligible else default
        decisions.append(dict(dataset=SHORT[ds],default=default,descriptive_fastest=fastest['method'],descriptive_fastest_change_pct=fastest['geomean_change_pct'],
            recommended=recommended,reason='replacement gate passed' if eligible else 'no challenger passed frozen replacement gate',
            qualified_challengers=[r['method'] for r in eligible],historical_validation=True,blind_confirmation=False))
        for target in targets:
            rows=[r for r in ratios if r['dataset']==SHORT[ds] and r['recall_pct']==target*100 and r['covered']]
            top=sorted(rows,key=lambda r:(-r['interpolated_qps'],r['method']))[0]
            target_winners.append(dict(dataset=SHORT[ds],recall_pct=target*100,descriptive_fastest=top['method'],qps=top['interpolated_qps'],
                change_vs_default_pct=top['change_pct'],passing_target=top['passing_target'],scope='descriptive interpolation; not a validated switching policy'))
    dump(O/'results/method_selection.json',dict(status='COMPLETE',decisions=decisions,target_winners=target_winners,
        rule='three targets covered; >=2 median +3% and all 5 repeat ratios >1; no median -3% target',ranking=ranking))
    return ratios,ranking,target_winners

def main():
    assert read(O/'state.json')['status']=='EVALUATION_COMPLETE_ANALYSIS_PENDING'
    allpoints=[];deltas=[];contrasts=[];fitgroups=[];fitaccept=[];regression=0;cache_count=0;checks=[];formal={};same_entries_checks=0
    for ds in DS:
        for stage in ['fit','cal','audit','validation']:
            dest=O/'results'/f'{stage}_{ds}';c=read(dest/'config.json');res=read(dest/'results.json');n=c['num_queries']
            gt=np.fromfile(c['gt_file'],np.int64).reshape(n,100)[:,:10]
            assert np.array_equal(np.fromfile(dest/'row_ids.i64',np.int64),np.fromfile(c['row_ids'],np.int64))
            assert res['threads']==1 and res['GT_opened_after_all_raw_search']
            bykey={(m['model_name'],m['L'],m['configuration']['exact']):m for m in res['methods']}
            for m in res['methods']:
                ids=array(dest,m,'ids.i32',np.int32).reshape(n,10);found=(ids[:,:,None]==gt[:,None,:]).any(1);hits=found.sum(1)
                assert np.array_equal(hits,array(dest,m,'hits.u8',np.uint8))
                assert np.array_equal((found*(1<<np.arange(10))).sum(1),array(dest,m,'hitmask.u16',np.uint16))
                assert abs(hits.mean()/10-m['recall_at_10'])<1e-12 and hits.sum()==m['total_hits']
                assert (np.diff(np.sort(ids,axis=1),axis=1)!=0).all() and (ids>=0).all() and (ids<c['base_count']).all()
                assert m['repeated_output_parity'] and m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16
                for fname,key in [('graph_ndc.u32','mean_graph_ndc'),('route_ndc.u32','mean_route_ndc')]:
                    assert abs(array(dest,m,fname,np.uint32).mean()-m[key])<1e-9
                assert abs(m['mean_graph_ndc']+m['mean_route_ndc']-m['mean_total_ndc'])<1e-9
                rec=dict(dataset=SHORT[ds],stage=stage,method=m['model_name'],L=m['L'],exact=m['configuration']['exact'],queries=n,
                    recall_pct=m['recall_at_10']*100,qps=m['qps'],qps_min=m['qps_min'],qps_max=m['qps_max'],
                    graph_ndc=m['mean_graph_ndc'],route_ndc=m['mean_route_ndc'],total_ndc=m['mean_total_ndc'],
                    route_only_seconds=m['route_only_seconds'],graph_only_seconds=m['graph_only_seconds'],
                    policy_build_seconds=m['policy_build_seconds'],source=str(dest/m['name']))
                if stage=='validation':
                    assert res['timing_repeats']==5 and len(m['qps_runs'])==len(m['end_to_end_seconds'])==5
                    rates=np.array(m['qps_runs']);seconds=np.array(m['end_to_end_seconds'])
                    assert np.allclose(rates,n/seconds,rtol=1e-12) and abs(np.median(rates)-m['qps'])<1e-8
                    rec.update({f'qps_run{i+1}':v for i,v in enumerate(rates)})
                    rec.update({f'wall_run{i+1}_s':v for i,v in enumerate(seconds)})
                    rec['timing_spread_pct']=(max(rates)-min(rates))/np.median(rates)*100
                else:assert m['qps'] is None
                allpoints.append(rec)
                base=bykey[('gt10_hard',m['L'],m['configuration']['exact'])]
                deltas.append(dict(dataset=SHORT[ds],stage=stage,method=m['model_name'],L=m['L'],exact=m['configuration']['exact'],reference='gt10_hard',**delta(dest,m,base)))
                same_entries_checks+=1
            aliases=read(O/'models'/ds/'drift_match.json')['aliases']
            sm=aliases.get('single_matched','single_matched');mm=aliases.get('multi_matched','multi_matched')
            comparisons=[('multi_minus_single','multi','single'),('matched_multi_minus_single',mm,sm),('multi_raw_minus_matched','multi',mm)]
            for L,exact in sorted({(m['L'],m['configuration']['exact']) for m in res['methods']}):
                for title,m,b in comparisons:
                    contrasts.append(dict(dataset=SHORT[ds],stage=stage,L=L,exact=exact,contrast=title,method=m,reference=b,
                        **delta(dest,bykey[(m,L,exact)],bykey[(b,L,exact)])))
            if stage=='fit':
                ts=np.fromfile(E28/'inputs'/ds/'proposals/triples.i32',np.int32).reshape(n,56,3);hubs=np.fromfile(c['hub_ids'],np.int32)
                labels=E28/'labels'/ds;stored_ids=np.memmap(labels/'ids.i32',np.int32,mode='r',shape=(n,56,10))
                stored_hits=np.fromfile(labels/'hits.u8',np.uint8).reshape(n,56);stored_ndc=np.fromfile(labels/'graph_ndc.u32',np.uint32).reshape(n,56)
                good=np.fromfile(O/'inputs'/ds/'teachers/multi.u8',np.uint8).reshape(n,56).astype(bool)
                singleton=np.fromfile(O/'inputs'/ds/'teachers/single.u8',np.uint8).reshape(n,56).astype(bool)
                gain=np.fromfile(O/'inputs'/ds/'teachers/headroom.u8',np.uint8).astype(bool);rr=np.arange(n)
                base=bykey[('gt10_hard',128,False)];bh=array(dest,base,'hits.u8',np.uint8).astype(float);bn=array(dest,base,'graph_ndc.u32',np.uint32).astype(float)
                teacher_gain=stored_hits.max(1).astype(float)-bh
                for m in res['methods']:
                    entries=array(dest,m,'entry_ids.i32',np.int32).reshape(n,3);local=np.searchsorted(hubs,entries)
                    assert (local<len(hubs)).all() and np.array_equal(hubs[local],entries)
                    match=(ts==local[:,None,:]).all(2);assert (match.sum(1)<=1).all()
                    known=match.any(1);slot=match.argmax(1);cache_count+=int(known.sum())
                    hits=array(dest,m,'hits.u8',np.uint8).astype(float);ndc=array(dest,m,'graph_ndc.u32',np.uint32).astype(float)
                    ids=array(dest,m,'ids.i32',np.int32).reshape(n,10)
                    assert np.array_equal(ids[known],stored_ids[rr[known],slot[known]])
                    assert np.array_equal(hits[known],stored_hits[rr[known],slot[known]])
                    assert np.array_equal(ndc[known],stored_ndc[rr[known],slot[known]])
                    for group,mask in [('all',np.ones(n,bool)),('headroom',gain),('no_headroom',~gain)]:
                        diff=hits-bh;lo,hi=bootstrap(diff[mask]);den=teacher_gain[mask].sum()
                        keep=np.minimum(np.maximum(diff[mask],0),teacher_gain[mask]).sum()
                        fitgroups.append(dict(dataset=SHORT[ds],method=m['model_name'],group=group,queries=int(mask.sum()),
                            recall_pct=float(hits[mask].mean()*10),baseline_recall_pct=float(bh[mask].mean()*10),delta_recall_pp=float(diff[mask].mean()*10),ci_low_pp=lo,ci_high_pp=hi,
                            graph_ndc=float(ndc[mask].mean()),baseline_graph_ndc=float(bn[mask].mean()),delta_graph_ndc_pct=float((ndc[mask].mean()/bn[mask].mean()-1)*100),
                            gained_hits=int(np.maximum(diff[mask],0).sum()),lost_hits=int(np.maximum(-diff[mask],0).sum()),net_hits=int(diff[mask].sum()),
                            improved_queries=int((diff[mask]>0).sum()),harmed_queries=int((diff[mask]<0).sum()),teacher_gain_retained_pct=float(keep/den*100) if den>0 else None))
                        fitaccept.append(dict(dataset=SHORT[ds],method=m['model_name'],group=group,queries=int(mask.sum()),known_fraction=float(known[mask].mean()),
                            unique_teacher_match=float((singleton[rr,slot]&known)[mask].mean()),equivalent_acceptance=float((good[rr,slot]&known)[mask].mean()),
                            different_but_equivalent_queries=int((good[rr,slot]&~singleton[rr,slot]&known&mask).sum()),outside_C8_queries=int((~known&mask).sum()),
                            maxhits_queries=int(((hits==stored_hits.max(1))&mask).sum()),scope='actual HNSW and original NSG on all fit queries'))
            if stage=='validation':
                formal[ds]=res['methods'];old=read(E29/'results'/f'validation_{ds}'/'results.json')
                oldby={(m['model_name'],m['L']):m for m in old['methods']}
                olddest=E29/'results'/f'validation_{ds}'
                for name in {m['model_name'] for m in res['methods']}:
                    ms=sorted([m for m in res['methods'] if m['model_name']==name],key=lambda m:m['L']);assert len(ms)==5
                    for m in ms[1:]:
                        assert np.array_equal(array(dest,m,'entry_ids.i32',np.int32),array(dest,ms[0],'entry_ids.i32',np.int32))
                        if name!='nsg':assert sha(dest/(m['name']+'.hnsw'))==sha(dest/(ms[0]['name']+'.hnsw'))
                    for m in ms:
                        key=(name.removeprefix('e29_'),m['L'])
                        if key in oldby:
                            for fname,dtype in [('ids.i32',np.int32),('distances.f32',np.uint32),('entry_ids.i32',np.int32),('graph_ndc.u32',np.uint32),('route_ndc.u32',np.uint32),('hits.u8',np.uint8),('hitmask.u16',np.uint16)]:
                                assert np.array_equal(array(dest,m,fname,dtype),array(olddest,oldby[key],fname,dtype)),(ds,name,m['L'],fname)
                            regression+=n
            checks.append(dict(dataset=ds,stage=stage,points=len(res['methods']),outputs=n*len(res['methods']),physical_calls=res['physical_graph_calls'],status='PASS'))
            print('ANALYSIS_VERIFIED',ds,stage,flush=True)
    curves=[];alignment=[];teachers=[];geometry=[];models=[]
    for ds in DS:
        for row in read(O/'inputs'/ds/'teachers/verification.json')['statistics']:
            teachers.append(dict(row,dataset=SHORT[ds]))
        dm=read(O/'models'/ds/'drift_match.json')
        geometry.append(dict(dataset=SHORT[ds],**{k:v for k,v in dm.items() if k in ['target_drift','matched_smaller','matched_larger','alpha','actual_drift','relative_error']},
            single_raw_drift=dm['raw_drifts']['single'],multi_raw_drift=dm['raw_drifts']['multi']))
        for cell in CELLS:
            d=O/'models'/ds/cell;r=read(d/'model.json')
            models.append(dict(dataset=SHORT[ds],method=cell,training_seconds=r['training_seconds'],epochs=r['epochs'],
                first_objective=r['first']['objective'],last_objective=r['last']['objective'],first_loss=r['first']['data_loss'],last_loss=r['last']['data_loss'],
                final_drift=r['last']['drift'],final_gradient_norm=r['last']['gradient_norm'],W_sha256=r['W']['sha256']))
            curves += [dict(dataset=SHORT[ds],method=cell,**v) for v in read(d/'training_curve.json')]
            for a in read(d/'alignment_curve.json'):
                alignment += [dict(dataset=SHORT[ds],method=cell,epoch=a['epoch'],**v) for v in a['metrics']]
    ratios,ranking,target_winners=choose_best(formal)
    for row in allpoints:
        if row['stage']!='validation':continue
        peers=[other for other in allpoints if other['dataset']==row['dataset'] and other['stage']=='validation']
        dominates=lambda other:other['recall_pct']>=row['recall_pct'] and other['qps']>=row['qps'] and (other['recall_pct']>row['recall_pct'] or other['qps']>row['qps'])
        row['pareto_all_methods_and_L']=not any(dominates(other) for other in peers)
        row['pareto_same_L']=not any(dominates(other) for other in peers if other['L']==row['L'])
    tables=dict(all_points=allpoints,delta_gt10=deltas,contrasts=contrasts,fit_groups=fitgroups,fit_acceptance=fitaccept,
        target_ratios=ratios,method_ranking=ranking,target_winners=target_winners,teacher_sets=teachers,training_curves=curves,
        training_alignment=alignment,drift_match=geometry,model_summary=models,frontier_intervals=frontier_intervals(formal))
    for name,rows in tables.items():writecsv(name,rows)
    dump(O/'results/analysis_tables.json',tables)
    calls=sum(c['physical_calls'] for c in checks)
    assert len(allpoints)==180 and sum(c['outputs'] for c in checks)==491200 and regression==180000
    assert calls==NORMAL_CAP
    dump(O/'reviews/output_verification.json',dict(status='PASS',total_points=len(allpoints),total_query_outputs=sum(c['outputs'] for c in checks),
        formal_points=120,formal_repeats=5,historical_regression_outputs=regression,fit_native_cache_parity_outputs=cache_count,
        same_entry_result_checks=same_entries_checks,physical_calls=calls,jobs=checks))
    dump(O/'state.json',dict(status='ANALYSIS_COMPLETE_DIAGNOSTICS_PLOTS_PENDING',training_runs=4,real_search_calls=calls,heldout_access=False))
    print('ANALYSIS_COMPLETE',flush=True)

if __name__=='__main__':main()
