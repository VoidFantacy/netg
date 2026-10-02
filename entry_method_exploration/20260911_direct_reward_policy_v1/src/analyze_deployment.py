from deployment_common_v2 import *
import csv

def ci(delta):
    v,c=np.unique(delta,return_counts=True);rng=np.random.default_rng(SEED)
    draws=rng.multinomial(len(delta),c/len(delta),size=2000)@v/len(delta)*10
    return list(map(float,np.quantile(draws,[.025,.975])))

def frontier(rows,key):
    valid=[x for x in rows if x[key] is not None]
    keep=[x for x in valid if not any(y['recall_pct']>=x['recall_pct'] and y[key]>=x[key] and (y['recall_pct']>x['recall_pct'] or y[key]>x[key]) for y in valid)]
    by_recall={}
    for x in keep:
        if x['recall_pct'] not in by_recall or x[key]>by_recall[x['recall_pct']][key]:by_recall[x['recall_pct']]=x
    return sorted(by_recall.values(),key=lambda x:x['recall_pct'])

def interp(points,key,target):
    if not points or target<points[0]['recall_pct']-1e-10 or target>points[-1]['recall_pct']+1e-10:return None
    return float(np.exp(np.interp(target,[x['recall_pct'] for x in points],np.log([x[key] for x in points]))))

assert read(O/'results/fit_gate.json')['status']=='PASS'
dev=read(O/'results/development_gate.json')
formal=dev['status']=='PASS_VALIDATION_ALLOWED'
if formal:assert read(O/'state.json')['status']=='VALIDATION_COMPLETE_ANALYSIS_PENDING'
else:assert read(O/'state.json')['status']=='DEVELOPMENT_COMPLETE'
points=[];paired=[];timings=[];front=[];validation_parity=[]
for ds in DS:
    default='gt10_soft' if ds==DS[0] else 'gt10_hard'
    for stage in ['fit','cal','audit']+(['validation'] if formal else []):
        run_id='fit_v2' if stage=='fit' else stage;dest=O/'results'/f'{run_id}_{ds}';r=read(dest/'results.json');c=read(dest/'config.json')
        verify_outputs(dest,c,r);outs={}
        for m in r['methods']:
            row=dict(dataset=ds,split=stage,method=m['model_name'],L=m['L'],queries=r['queries'],recall_pct=m['recall_at_10']*100,
                failed_queries=m['failed_queries'],failure_pct=m['failure_rate']*100,route_ndc=m['mean_route_ndc'],graph_ndc=m['mean_graph_ndc'],total_ndc=m['mean_total_ndc'],
                qps=m['qps'],qps_min=m['qps_min'],qps_max=m['qps_max'],policy_build_seconds=m['policy_build_seconds'])
            for i in range(5):row['qps_run'+str(i)]=m['qps_runs'][i] if formal and stage=='validation' else None
            points.append(row);outs[(m['model_name'],m['L'])]=np.fromfile(dest/m['name']/'hits.u8',np.uint8).astype(int)
            for i,(qps,seconds) in enumerate(zip(m['qps_runs'],m['end_to_end_seconds'])):
                timings.append(dict(dataset=ds,method=m['model_name'],L=m['L'],repeat=i,qps=qps,end_to_end_seconds=seconds,queries=r['queries']))
        for L in sorted({m['L'] for m in r['methods']}):
            for method,reference in [('teacher',default),('reward',default),('reward','teacher')]:
                aa=outs[method,L];bb=outs[reference,L];delta=aa-bb;lo,hi=ci(delta)
                a=next(x for x in points if x['dataset']==ds and x['split']==stage and x['method']==method and x['L']==L)
                b=next(x for x in points if x['dataset']==ds and x['split']==stage and x['method']==reference and x['L']==L)
                paired.append(dict(dataset=ds,split=stage,method=method,reference=reference,L=L,queries=r['queries'],delta_recall_pp=float(delta.mean()*10),
                    ci95_low_pp=lo,ci95_high_pp=hi,improved_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()),
                    gained_hits=int(delta[delta>0].sum()),lost_hits=int(-delta[delta<0].sum()),rescued_zero_hit=int(((bb==0)&(aa>0)).sum()),new_zero_hit=int(((bb>0)&(aa==0)).sum()),
                    graph_ndc_change_pct=(a['graph_ndc']/b['graph_ndc']-1)*100,total_ndc_change_pct=(a['total_ndc']/b['total_ndc']-1)*100,
                    same_L_qps_change_pct=(a['qps']/b['qps']-1)*100 if a['qps'] is not None else None))
        if stage=='validation':
            old=read(E30/'results'/f'validation_{ds}'/'results.json')
            for method in {m['model_name'] for m in r['methods']}:
                ms=[m for m in r['methods'] if m['model_name']==method]
                first=dest/ms[0]['name']
                for m in ms:
                    d=dest/m['name'];assert sha(d/'entry_ids.i32')==sha(first/'entry_ids.i32')
                    if method in ['teacher','reward']:
                        assert sha(d/'candidates.i32')==sha(first/'candidates.i32') and sha(d/'action_slots.i32')==sha(first/'action_slots.i32')
                    else:
                        oldm=next(x for x in old['methods'] if x['model_name']==method and x['L']==m['L']);od=E30/'results'/f'validation_{ds}'/oldm['name']
                        for name in ['ids.i32','distances.f32','entry_ids.i32','hits.u8','graph_ndc.u32']:assert sha(d/name)==sha(od/name)
                validation_parity.append(dict(dataset=ds,method=method,entry_consistent_across_five_L=True,old_E30_output_bit_recovery=method not in ['teacher','reward']))
    if formal:
        dsrows=[x for x in points if x['dataset']==ds and x['split']=='validation']
        for reference in [default,'teacher']:
            aa=[x for x in dsrows if x['method']=='reward'];bb=[x for x in dsrows if x['method']==reference]
            af,bf=frontier(aa,'qps'),frontier(bb,'qps');low=max(af[0]['recall_pct'],bf[0]['recall_pct']);high=min(af[-1]['recall_pct'],bf[-1]['recall_pct'])
            assert high>low,'no overlapping frontier interval'
            for fraction in [.25,.5,.75]:
                target=low+fraction*(high-low);ratios=[]
                for i in range(5):
                    key='qps_run'+str(i);a=interp(frontier(aa,key),key,target);b=interp(frontier(bb,key),key,target)
                    ratios.append(a/b if a is not None and b is not None else None)
                finite=all(x is not None for x in ratios)
                front.append(dict(dataset=ds,method='reward',reference=reference,overlap_low=low,overlap_high=high,fraction=fraction,target_recall_pct=target,
                    median_frontier_qps_ratio=interp(af,'qps',target)/interp(bf,'qps',target),run_ratio_median=float(np.median(ratios)) if finite else None,
                    run_ratio_min=min(ratios) if finite else None,run_ratio_max=max(ratios) if finite else None,all_rounds_in_support=finite,
                    **{'run'+str(i)+'_ratio':ratios[i] for i in range(5)}))
if formal:
    byds=[]
    for ds in DS:
        default='gt10_soft' if ds==DS[0] else 'gt10_hard';rows=[x for x in front if x['dataset']==ds and x['reference']==default]
        passed=all(x['all_rounds_in_support'] and x['run_ratio_median']>1.01 and x['run_ratio_min']>1 for x in rows)
        byds.append(dict(dataset=ds,default=default,passed=passed,targets=3,rounds=5))
    go=all(x['passed'] for x in byds)
    performance=dict(status='PASS_PROPOSE_INDEPENDENT_REPLICATION' if go else 'STOP_FULL_COST_PERFORMANCE_GATE',by_dataset=byds,scope='historically reused validation2K; descriptive frontier interpolation, not blind formal GO')
    conclusion='DIRECT_REWARD_POLICY_COMPLETE_LOCAL_FRONTIER_SIGNAL' if go else 'DIRECT_REWARD_POLICY_COMPLETE_RECALL_GAIN_WITH_ROUTING_COST'
else:
    performance=dict(status='NOT_RUN_DEVELOPMENT_GATE_FAILED',by_dataset=[],qps=None,reason='prelocked cal/audit gate failed; no validation or wall invocation')
    conclusion='DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP'
dump(O/'results/performance_gate.json',performance)
tables=dict(real_points=points,real_paired=paired,wall_runs=timings,common_recall=front)
for name,rows in tables.items():
    if rows:
        with (O/'results'/(name+'.csv')).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
dump(O/'results/deployment_tables.json',tables)
jobs=read(O/'logs/evaluation_jobs.json');charged=sum(x.get('charged_calls',x['reserved_calls']) for x in jobs)
actual=sum(read(O/'results'/(x.get('run_id',x['stage'])+'_'+x['dataset'])/'results.json')['physical_graph_calls'] if x['status']=='COMPLETE' else x['verified_actual_calls'] for x in jobs)
assert actual==charged<=DEPLOY_CAP
dump(O/'reviews/deployment_verification.json',dict(status='PASS',query_outputs=sum(x['queries'] for x in points),points=len(points),real_NSG_calls=actual,
    charged_calls=charged,gross_reserved_calls=sum(x['reserved_calls'] for x in jobs),verified_pre_query_failed_calls=0,validation_parity=validation_parity,
    wall_points=sum(x['qps'] is not None for x in points),timing_runs=len(timings),implemented_timer_includes_full_C8=True,heldout_access=False))
dump(O/'results/conclusion.json',dict(status=conclusion,cache_gate='PASS_REAL_DEVELOPMENT_ALLOWED',development_gate=dev['status'],performance_gate=performance['status'],
    current_defaults=dict(webvid='gt10_soft',yandex='gt10_hard'),performance_replacement_proven=False,heldout_access=False))
dump(O/'state.json',dict(status='DEPLOYMENT_ANALYSIS_COMPLETE',conclusion=conclusion,heldout_access=False))
print(json.dumps(dict(conclusion=conclusion,performance=performance,dev=dev,points=points),indent=2),flush=True)
