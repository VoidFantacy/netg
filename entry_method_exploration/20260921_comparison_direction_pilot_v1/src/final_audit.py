"""Independent final coverage, source, timing, metrics and call-accounting audit."""
from common import *
import math,csv

def main():
    start=time.time();assert read(RUN/'state.json')['status']=='MEASUREMENTS_COMPLETE'
    assert (RUN/'reviews/stage2_complete.json').exists()
    jobs=read(RUN/'reviews/jobs.json');ledger=[];total=routers=0
    for job in jobs:
        assert job['exit_code']==0, 'execution failures require separately reconciled correction history'
        pp=Path(f"/proc/{job['pid']}/cmdline")
        assert not pp.exists() or str(RUN/'bin/experiment').encode() not in pp.read_bytes()
        cfg=read(job['argv'][-2]);out=Path(job['argv'][-1]);done=read(out/'complete.json');n=cfg['n'];mode=cfg['mode']
        if mode=='trace':
            A=cfg['trace_single_actions']+1;expected=2*n*A+min(n,8)*A;route=n
        elif mode=='labels':
            A=done['A'];expected=n*A*(2*cfg['label_repeats']+1)+3*math.ceil(n/cfg['label_block']);route=n
        elif mode=='evaluate':
            nm=len(cfg['methods']);npnt=len(cfg['points']);expected=npnt*nm*(n*(cfg['repeats']+2)+min(n,16))
            route=0
            for point in cfg['points']:
                K=point['K']
                for m in cfg['methods']:
                    skips=m['type']=='nsg' or (m['type']=='fixed' and m['fixed'][str(K)]>=0)
                    if not skips:route+=n*(cfg['repeats']+2)
        else:assert mode in ('features','predict');expected=route=0
        assert done['search_calls']==expected and done.get('router_calls',0)==route,(job['kind'],expected,done)
        calls=done.get('new_search_calls',expected);total+=calls;routers+=route
        ledger.append(dict(dataset=job['dataset'],kind=job['kind'],NSG_calls=calls,router_calls=route,seconds=job['seconds']))
    assert total<=LOCK['max_search_calls']
    checkedfiles=0
    for manifest in ('native_frozen.json','python_frozen.json','models_frozen.json','preserved_assets.json'):
        for f in read(RUN/'reviews'/manifest)['files']:assert ident(f['path'])==f;checkedfiles+=1
    assert (RUN/'src/kernels.hpp').read_bytes()==(ROOT/'entry_method_exploration/20260920_entry_set_pilot_v1/src/kernels.hpp').read_bytes()
    assert (RUN/'src/trace_kernel.hpp').read_bytes()==(ROOT/'entry_method_exploration/20260920_until1900_theory_v1/stages/e113_comparison_support/src/trace_kernel.hpp').read_bytes()
    for c in LOCK['datasets'].values():
        st=Path(c['index']).stat();assert st.st_size==c['index_stat']['bytes'] and st.st_mtime_ns==c['index_stat']['mtime_ns']
    audits=['synthetic_checks.json']
    for ds in LOCK['datasets']:
        audits += [f'{prefix}_{ds}.json' for prefix in ('input_audit','direction_audit','label_audit','fit_replay_audit','acceptance_audit','prediction_audit_fit','prediction_audit_accept','features_fit','features_accept','clustering')]
    for name in audits:assert read(RUN/'reviews'/name)['status']=='PASS',name
    frozen=read(RUN/'reviews/models_frozen.json')['created_unix']
    for job in jobs:
        if job['kind'].startswith('accept') or job['kind']=='curve':assert job['started_unix']>frozen
    metrics=read(RUN/'results/metrics.json');paired=read(RUN/'results/paired.json');hits={};times={};metriclookup={}
    assert len(metrics)==140
    for ds,c in LOCK['datasets'].items():
        gt=np.fromfile(RUN/'inputs'/ds/'accept/gt.i64',np.int64).reshape(4096,100)
        gtsets=[set(row.tolist()) for row in gt]
        for batch in ('accept','curve'):
            cfg=read(RUN/'results'/ds/batch/'config.json');expected_names=['GT10','Single1','BestFixed','NSG','GraphCost','GraphRecall','RandomCost','GraphLinearCost','RawLinearCost','ShuffledCost','FeatureDefault'] if batch=='accept' else ['GT10','Single1','BestFixed','GraphCost','GraphRecall','RandomCost']
            assert [m['name'] for m in cfg['methods']]==expected_names
            required=[(1,128),(100,128)] if batch=='accept' else [(K,L) for K in (1,100) for L in ((64,256,400,800) if K==1 else (100,256,400,800))]
            assert [(p['K'],p['L']) for p in cfg['points']]==required
            for K,L in required:
                for name in expected_names:
                    p=RUN/'results'/ds/batch/f'{name}_K{K}_L{L}';I=np.fromfile(p/'ids.i32',np.int32).reshape(4096,K)
                    h=(I[:,0]==gt[:,0]).astype(np.int64) if K==1 else np.array([sum(int(e) in g for e in row) for row,g in zip(I,gtsets)],np.int64)
                    key=(ds,name,K,L);hits[key]=h
                    row=next(v for v in metrics if (v['dataset'],v['method'],v['K'],v['L'])==key);metriclookup[key]=row
                    z=read(p/'complete.json');t=np.array(z['seconds']);times[key]=t
                    assert len(t)==3 and np.all(t>0) and z['threads']==1
                    assert abs(row['recall_pct']-h.sum()/4096/K*100)<1e-10 and row['total_hits']==int(h.sum())
                    assert row['zero_hit_queries']==int((h==0).sum()) and abs(row['qps']-(4096/t).mean())<1e-8
                    assert abs(row['qps_N_over_mean_wall']-4096/t.mean())<1e-8
    for row in paired:
        ds,name,ref,K,L=row['dataset'],row['method'],row['reference'],row['K'],row['L']
        a=hits[ds,name,K,L];b=hits[ds,ref,K,L];delta=a-b
        assert abs(row['delta_recall_pp']-delta.sum()/4096/K*100)<1e-10
        if 'net_hits' in row:
            assert row['net_hits']==int(delta.sum()) and row['improved_queries']==int((delta>0).sum()) and row['harmed_queries']==int((delta<0).sum())
            assert row['rescued_zero']==int(((b==0)&(a>0)).sum()) and row['new_zero']==int(((b>0)&(a==0)).sum())
            assert row['gained_gt_members']-row['lost_gt_members']==row['net_hits']
            groups=row['action_groups'];assert sum(g['queries'] for g in groups.values())==4096
            assert sum(g['net_hits'] for g in groups.values())==row['net_hits']
            assert sum(g['rescued_zero'] for g in groups.values())==row['rescued_zero']
            assert sum(g['new_zero'] for g in groups.values())==row['new_zero']
        if 'bootstrap' in row:
            z=row['bootstrap'];assert z['coverage']==.9875 and z['repetitions']==20000
            assert abs(z['mean_pp']-row['delta_recall_pp'])<1e-10
            assert z['ci_pp'][0]<=z['ci_pp'][1] and z['ci_pp'][0]>=-100 and z['ci_pp'][1]<=100
    # Validate CSV as rendered interchange data, not merely JSON.
    csvrows=list(csv.DictReader((RUN/'results/metrics.csv').open()));assert len(csvrows)==len(metrics)
    for row in csvrows:
        key=(row['dataset'],row['method'],int(row['K']),int(row['L']));ref=metriclookup[key]
        for k in ('recall_pct','qps','qps_N_over_mean_wall'):assert abs(float(row[k])-ref[k])<1e-10
    for row in read(RUN/'results/matched_recall.json'):
        candidates=[m for m in metrics if m['dataset']==row['dataset'] and m['K']==row['K'] and m['method']==row['method'] and m['recall_pct']>=row['target_recall_pct']]
        assert row['reachable']==bool(candidates)
        if candidates:assert row['qps']==max(m['qps'] for m in candidates)
    query_hit_cache=np.load(RUN/'results/query_hits.npz')
    for row in read(RUN/'results/measured_policy_oracles.json'):
        ds,K,L=row['dataset'],row['K'],row['L'];names=row['methods']
        assert 'NSG' not in names and 'GT10' in names and 'GraphCost' in names
        matrix=np.column_stack([hits[ds,name,K,L] for name in names]);best=matrix.max(axis=1)
        assert np.array_equal(query_hit_cache[f'{ds}_K{K}_L{L}'],matrix)
        assert abs(row['recall_pct']-best.mean()/K*100)<1e-10
        assert abs(row['gain_vs_GT10_pp']-(best-hits[ds,'GT10',K,L]).mean()/K*100)<1e-10
        assert abs(row['GraphCost_recall_regret_pp']-(best-hits[ds,'GraphCost',K,L]).mean()/K*100)<1e-10
    resources=[]
    for p in (RUN/'reviews').glob('resources_*_attempt*.json'):resources+=read(p)
    assert resources and all(x['threads']==1 and x['cpu']=='15' and x['rss']<=40*1024**3 and x['free_bytes']>=6*1024**3 for x in resources)
    size=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file());assert size<=LOCK['max_new_bytes']
    costs=dict(jobs=ledger,NSG_calls=total,router_calls=routers,native_job_seconds=sum(j['seconds'] for j in jobs),
        compile_seconds=read(RUN/'reviews/build.json')['seconds'],training_seconds=read(RUN/'reviews/models_frozen.json')['training_seconds'],
        clustering_seconds=sum(read(RUN/'reviews'/f'clustering_{ds}.json')['seconds'] for ds in LOCK['datasets']),
        measurement_elapsed_seconds=read(RUN/'reviews/stage2_started.json')['unix']+read(RUN/'reviews/stage2_complete.json')['seconds']-read(RUN/'reviews/stage1_started.json')['unix'],
        max_observed_rss_bytes=max(x['rss'] for x in resources),artifact_bytes=size,new_GT=0,new_graph=0,new_K10=0,
        full_base_and_graph_rehash=False,large_index_identity='locked stat plus source identity and search output parity')
    dump(RUN/'reviews/cost_ledger.json',costs)
    dump(RUN/'reviews/independent_final_audit.json',dict(status='PASS',seconds=time.time()-start,points=140,wall_rounds=420,
        checked_source_model_files=checkedfiles,required_audits=audits,independent_return_scoring=True,model_before_acceptance=True,
        fixed_sources_unchanged=True,NSG_calls=total,actual_threads=1,actual_CPU=15,complete_five_budget_curves=True))
    return costs

if __name__=='__main__':os.sched_setaffinity(0,{15});main()
