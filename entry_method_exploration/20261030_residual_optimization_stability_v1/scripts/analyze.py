from common import *

rows=[];paired=[];quality={};rng=np.random.default_rng(19420261032)
for ds in DS:
 for window in ['public','confirmation']:
    c=read(R/f'configs/{ds}.{window}.json');g=np.asarray(gt(c['test_gt']),dtype=np.int32);done=read(Path(c['output_dir'])/'complete.json');n=len(g)
    audit=read(R/f'reviews/{ds}.{window}.audit.json');assert audit['points']==64
    packets={}
    for p in done['results']:
        K=p['K'];d=Path(p['result_dir'])/'raw';ids=np.fromfile(d/'ids.i32','<i4').reshape(n,K)
        hits=np.empty(n,np.int32)
        for i in range(n):hits[i]=len(set(ids[i])&set(g[i,:K]))
        packets[K,p['L'],p['method']]=(p,ids,hits)
    bootstrap=rng.integers(0,n,size=(1000,n))
    for (K,L,m),(p,ids,hits) in packets.items():
        main,mainids,mainhits=packets[K,L,'GT10'];delta=hits-mainhits;rescued=lost=0
        for i in range(n):
            a=set(ids[i])&set(g[i,:K]);b=set(mainids[i])&set(g[i,:K]);rescued+=len(a-b);lost+=len(b-a)
        recall_bs=hits[bootstrap].mean(1)/K*100;delta_bs=delta[bootstrap].mean(1)/K*100
        rec=dict(dataset=ds,window=window,K=K,L=L,method=m,n=n,hits=int(hits.sum()),recall_pct=float(hits.mean()/K*100),recall_CI_lo=float(np.quantile(recall_bs,.025)),recall_CI_hi=float(np.quantile(recall_bs,.975)),gain_pp=float(delta.mean()/K*100),gain_CI_lo=float(np.quantile(delta_bs,.025)),gain_CI_hi=float(np.quantile(delta_bs,.975)),rescued=rescued,lost=lost,improved_queries=int(np.count_nonzero(delta>0)),harmed_queries=int(np.count_nonzero(delta<0)),failed_lt10=int(np.count_nonzero(hits<10)) if K==100 else '',complete_queries=int(np.count_nonzero(hits==K)),qps=p['qps'],mean_us=1e6/p['qps'],qps_min=min(x['qps'] for x in p['rounds']),qps_max=max(x['qps'] for x in p['rounds']),scans_per_query=p['scans_per_query'],SQ_scores_per_query=p['SQ_scores_per_query'],extra_exact_per_query=p['extra_exact_per_query'])
        for j,x in enumerate(p['rounds']):rec[f'qps_round{j}']=x['qps']
        rows.append(rec);quality[ds,window,K,L,m]=hits
        if m in ['OPT-B32','OPT-SQ']:
            legacy='B32' if m=='OPT-B32' else 'REUSE-SQ';old,oldids,oldhits=packets[K,L,legacy];assert np.array_equal(ids,oldids) and np.array_equal(hits,oldhits)
            speeds=[p['rounds'][j]['qps']/old['rounds'][j]['qps']-1 for j in range(3)]
            paired.append(dict(dataset=ds,window=window,K=K,L=L,method=m,legacy=legacy,recall_pct=rec['recall_pct'],legacy_qps=old['qps'],opt_qps=p['qps'],qps_gain_pct=100*(p['qps']/old['qps']-1),mean_time_change_pct=100*(old['qps']/p['qps']-1),round0_gain_pct=100*speeds[0],round1_gain_pct=100*speeds[1],round2_gain_pct=100*speeds[2],all_rounds_faster=all(x>0 for x in speeds),screen_pass=p['qps']/old['qps']>=1.02 and all(x>0 for x in speeds),identical_six_array_packets=True))

for row in rows:
    group=[x for x in rows if (x['dataset'],x['window'],x['K'])==(row['dataset'],row['window'],row['K'])]
    for method,name in [('GT10','GT'),('B32','B32')]:
        controls=[x for x in group if x['method']==method]
        eligible=[x for x in controls if x['hits']>=row['hits']]
        fastest=max(eligible,key=lambda x:x['qps']) if eligible else None
        row[f'{name}_quality_threshold_L']=fastest['L'] if fastest else ''
        row[f'{name}_quality_threshold_recall_pct']=fastest['recall_pct'] if fastest else ''
        row[f'{name}_quality_threshold_qps']=fastest['qps'] if fastest else ''
        row[f'{name}_threshold_speed_gain_pct']=100*(row['qps']/fastest['qps']-1) if fastest else ''
        dom=[x for x in controls if x['hits']>=row['hits'] and x['qps']>=row['qps'] and (x['hits']>row['hits'] or x['qps']>row['qps'])]
        row[f'{name}_cover_L']=';'.join(str(x['L']) for x in dom)
        budget=[x for x in controls if x['qps']>=row['qps']]
        best=max(budget,key=lambda x:(x['hits'],x['qps'])) if budget else None
        row[f'{name}_same_budget_recall_delta_pp']=row['recall_pct']-best['recall_pct'] if best else ''
    row['GT_or_B32_covered']=bool(row['GT_cover_L'] or row['B32_cover_L'])

stability=[]
for a in paired:
 if a['window']!='public':continue
 b=next(x for x in paired if x['window']=='confirmation' and all(x[k]==a[k] for k in ['dataset','K','L','method']))
 stability.append(dict(dataset=a['dataset'],K=a['K'],L=a['L'],method=a['method'],public_gain_pct=a['qps_gain_pct'],confirmation_gain_pct=b['qps_gain_pct'],public_screen=a['screen_pass'],confirmation_screen=b['screen_pass'],both_windows_pass=a['screen_pass'] and b['screen_pass']))
csvwrite(R/'analysis/points.csv',rows);csvwrite(R/'analysis/optimization_pairs.csv',paired);csvwrite(R/'analysis/stability.csv',stability)
np.savez_compressed(R/'analysis/per_query_hits.npz',**{'__'.join(map(str,k)):v for k,v in quality.items()})
verdict=dict(formal_points=len(rows),formal_batches=sum(len(read(Path(read(R/f'configs/{ds}.{w}.json')['output_dir'])/'complete.json')['results'])*3 for ds in DS for w in ['public','confirmation']),paired_points=len(paired),optimization_screen_pass=sum(x['screen_pass'] for x in paired),stable_configurations=sum(x['both_windows_pass'] for x in stability),configurations=len(stability),default_changed=False,notes='finite frozen grids, one graph/profile, three timing repetitions, confirmation sampled from registered-role-disjoint vectors; no global historical nonexposure claim')
assert len(rows)==256 and len(paired)==56 and len(stability)==28
dump(R/'analysis/verdict.json',verdict);print(json.dumps(verdict),flush=True)
