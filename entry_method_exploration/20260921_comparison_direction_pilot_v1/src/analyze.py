"""Frozen comparisons: paired query changes, complete wall and measured frontiers."""
from common import *
from audit import score,return_hash
import csv

def bootstrap_delta(delta,K,tag,coverage=.9875):
    vals,counts=np.unique(np.asarray(delta,dtype=np.int64),return_counts=True);n=int(counts.sum())
    seed=LOCK['seed']+int(hashlib.sha256(tag.encode()).hexdigest()[:8],16)
    rng=np.random.default_rng(seed);samples=rng.multinomial(n,counts/n,size=LOCK['bootstrap_reps'])@vals/(n*K)*100
    tail=(1-coverage)/2
    return dict(mean_pp=float(np.mean(delta)/K*100),ci_pp=np.quantile(samples,[tail,1-tail]).tolist(),coverage=coverage,
                repetitions=LOCK['bootstrap_reps'],seed=seed,unit='paired query',implementation='multinomial over empirical integer hit differences')

def rows_csv(path,rows):
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def analyze():
    started=time.time();metrics=[];paired=[];oracles=[];matched=[];decisions=[];per_query={};agreements=[]
    for ds,c in LOCK['datasets'].items():
        root=RUN/'results'/ds;n=4096;gt=np.fromfile(RUN/'inputs'/ds/'accept/gt.i64',np.int64).reshape(n,100)
        rows=np.fromfile(RUN/'inputs'/ds/'accept/row_ids.i64',np.int64);truths=[set(v.tolist()) for v in gt]
        for batch in ('accept','curve'):
            cfg=read(root/batch/'config.json')
            for point in cfg['points']:
                K,L=point['K'],point['L'];data={}
                for m in cfg['methods']:
                    name=m['name'];p=root/batch/f'{name}_K{K}_L{L}';z=read(p/'complete.json');times=np.array(z['seconds']);qps=n/times
                    ids=np.fromfile(p/'ids.i32',np.int32).reshape(n,K);h=score(ids,gt,K);a=np.fromfile(p/'actions.i32',np.int32)
                    route=np.fromfile(p/'route_ndc.u64',np.uint64);graph=np.fromfile(p/'graph_ndc.u64',np.uint64)
                    data[name]=(h,ids,a)
                    metrics.append(dict(dataset=ds,method=name,K=K,L=L,n=n,recall_pct=float(h.mean()/K*100),total_hits=int(h.sum()),
                        zero_hit_queries=int((h==0).sum()),qps=float(qps.mean()),qps_N_over_mean_wall=float(n/times.mean()),
                        qps_min=float(qps.min()),qps_max=float(qps.max()),seconds_round0=float(times[0]),seconds_round1=float(times[1]),seconds_round2=float(times[2]),
                        route_ndc_mean=float(route.mean()),graph_ndc_mean=float(graph.mean()),fallback_fraction=float(np.mean(a==0)),
                        unique_single_actions=int(np.unique(a[a>0]).size),batch=batch))
                bh,bi,ba=data['GT10'];bm=next(x for x in reversed(metrics) if x['dataset']==ds and x['method']=='GT10' and x['K']==K and x['L']==L)
                baseline_entries=np.fromfile(root/batch/f'GT10_K{K}_L{L}/entry_ids.i32',np.int32).reshape(n,3)
                baseline_members=[({int(bi[i,0])}&{int(gt[i,0])}) if K==1 else set(bi[i].tolist())&truths[i] for i in range(n)]
                for name,(h,ids,a) in data.items():
                    if name=='GT10':continue
                    delta=h-bh;row=next(x for x in reversed(metrics) if x['dataset']==ds and x['method']==name and x['K']==K and x['L']==L)
                    diff=dict(dataset=ds,method=name,reference='GT10',K=K,L=L,delta_recall_pp=float(delta.mean()/K*100),
                        delta_qps_pct=float((row['qps']/bm['qps']-1)*100),improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),
                        unchanged_queries=int((delta==0).sum()),rescued_zero=int(((bh==0)&(h>0)).sum()),new_zero=int(((bh>0)&(h==0)).sum()),
                        net_hits=int(delta.sum()),fallback_fraction=row['fallback_fraction'],qps_ranges_separated_positive=row['qps_min']>bm['qps_max'],
                        qps_ranges_separated_negative=row['qps_max']<bm['qps_min'])
                    if L==128:diff['bootstrap']=bootstrap_delta(delta,K,f'{ds}:{name}:{K}:{L}')
                    gained=[];lost=[]
                    for i in range(n):
                        new=({int(ids[i,0])}&{int(gt[i,0])}) if K==1 else set(ids[i].tolist())&truths[i]
                        gained.append(len(new-baseline_members[i]));lost.append(len(baseline_members[i]-new))
                    diff['gained_gt_members']=int(sum(gained));diff['lost_gt_members']=int(sum(lost));assert sum(gained)-sum(lost)==delta.sum()
                    entries=np.fromfile(root/batch/f'{name}_K{K}_L{L}/entry_ids.i32',np.int32).reshape(n,3)
                    inside=np.any(entries[:,:1]==baseline_entries,axis=1)&(a>0)
                    groups={'fallback':a==0,'single_inside_GT10_top3':inside,'single_outside_GT10_top3':(a>0)&~inside,'fixed_NSG':a<0}
                    if name=='Single1':assert np.all(inside)
                    diff['action_groups']={}
                    for group,take in groups.items():
                        diff['action_groups'][group]=dict(queries=int(take.sum()),net_hits=int(delta[take].sum()),
                            contribution_to_overall_recall_pp=float(delta[take].sum()/n/K*100),
                            rescued_zero=int(((bh==0)&(h>0)&take).sum()),new_zero=int(((bh>0)&(h==0)&take).sum()))
                    assert sum(g['queries'] for g in diff['action_groups'].values())==n
                    assert sum(g['net_hits'] for g in diff['action_groups'].values())==int(delta.sum())
                    paired.append(diff)
                    if L==128 and name=='GraphCost':
                        for i in range(n):
                            decisions.append(dict(dataset=ds,K=K,query_position=i,source_row=int(rows[i]),action=int(a[i]),baseline_hits=int(bh[i]),
                                selected_hits=int(h[i]),gained_gt_members=gained[i],lost_gt_members=lost[i],delta_hits=int(delta[i]),
                                single_outside_GT10_top3=bool((a[i]>0) and not inside[i])))
                oracle_names=[name for name in data if name!='NSG']
                matrix=np.column_stack([data[name][0] for name in oracle_names]);best=matrix.max(axis=1)
                oracles.append(dict(dataset=ds,K=K,L=L,scope='oracle among measured in-domain policies; lower bound on H-single/default opportunity; fixed NSG excluded',
                    methods=oracle_names,recall_pct=float(best.mean()/K*100),gain_vs_GT10_pp=float((best-bh).mean()/K*100),
                    GraphCost_recall_regret_pp=float((best-data['GraphCost'][0]).mean()/K*100)))
                per_query[f'{ds}_K{K}_L{L}']=matrix.astype(np.uint8)
                if L==128:
                    for other in ('GraphRecall','RandomCost','GraphLinearCost','RawLinearCost','ShuffledCost','Single1','BestFixed'):
                        aa=data['GraphCost'][2];ab=data[other][2]
                        agreements.append(dict(dataset=ds,K=K,method='GraphCost',reference=other,identical_actions=int((aa==ab).sum()),
                            jointly_fallback=int(((aa==0)&(ab==0)).sum()),both_single_same=int(((aa==ab)&(aa>0)).sum()),queries=n))
                    for control in ('Single1','BestFixed','RandomCost','GraphLinearCost','RawLinearCost','GraphRecall','ShuffledCost'):
                        h=data['GraphCost'][0];ch=data[control][0]
                        paired.append(dict(dataset=ds,method='GraphCost',reference=control,K=K,L=L,
                            delta_recall_pp=float((h-ch).mean()/K*100),bootstrap=bootstrap_delta(h-ch,K,f'{ds}:GraphCost-vs-{control}:{K}')))
        for K in (1,100):
            for target in (50,60,70,75,80,85,90,95,99):
                eligible=[r for r in metrics if r['dataset']==ds and r['K']==K and r['recall_pct']>=target and r['method'] in ('GT10','Single1','BestFixed','GraphCost','GraphRecall','RandomCost')]
                fastest={}
                for r in eligible:
                    if r['method'] not in fastest or r['qps']>fastest[r['method']]['qps']:fastest[r['method']]=r
                base=fastest.get('GT10')
                for name in ('GT10','Single1','BestFixed','GraphCost','GraphRecall','RandomCost'):
                    row=fastest.get(name)
                    matched.append(dict(dataset=ds,K=K,target_recall_pct=target,method=name,reachable=row is not None,
                        L=row['L'] if row else None,recall_pct=row['recall_pct'] if row else None,qps=row['qps'] if row else None,
                        speedup_vs_GT10_pct=(row['qps']/base['qps']-1)*100 if row and base else None,
                        scope='fastest measured point meeting threshold; no interpolation'))
    dump(RUN/'results/metrics.json',metrics);rows_csv(RUN/'results/metrics.csv',metrics)
    dump(RUN/'results/paired.json',paired);dump(RUN/'results/measured_policy_oracles.json',oracles)
    dump(RUN/'results/action_agreements.json',agreements)
    dump(RUN/'results/matched_recall.json',matched);rows_csv(RUN/'results/matched_recall.csv',matched)
    rows_csv(RUN/'results/GraphCost_query_changes.csv',decisions)
    np.savez_compressed(RUN/'results/query_hits.npz',**per_query)
    primary=[r for r in paired if r['method']=='GraphCost' and r['reference']=='GT10' and r['L']==128]
    assert len(primary)==4 and len(metrics)==140
    evidence=dict(primary=primary,all_four_primary_recall_intervals_positive=all(r['bootstrap']['ci_pp'][0]>0 for r in primary),
        any_primary_recall_interval_negative=any(r['bootstrap']['ci_pp'][1]<0 for r in primary),
        primary_qps_means_all_positive=all(r['delta_qps_pct']>0 for r in primary),
        primary_qps_round_ranges_all_positive=all(r['qps_ranges_separated_positive'] for r in primary),
        default_changed=False,decision='REQUIRES_FULL_RESULT_INTERPRETATION_AND_INDEPENDENT_AUDIT',
        scope='Historical development acceptance; uncertainty is not equivalence or impossibility')
    dump(RUN/'results/evidence.json',evidence);dump(RUN/'reviews/analysis_complete.json',dict(status='PASS',points=len(metrics),seconds=time.time()-started))
    return evidence

if __name__=='__main__':
    os.sched_setaffinity(0,{15});analyze()
