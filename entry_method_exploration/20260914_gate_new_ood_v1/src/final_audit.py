"""Post-run artifact/contract audit. Does not execute ANN or change models."""
from common import *
from verify import protected
import csv
from datetime import datetime, timezone, timedelta

def main():
    lock=json.loads((RUN/'config.locked.json').read_text())
    pre=json.loads((RUN/'reviews/preflight.json').read_text())
    analysis=json.loads((RUN/'results/analysis_complete.json').read_text())
    assert pre['status']==analysis['status']=='PASS'
    for name,digest in pre['source_hashes'].items(): assert sha(RUN/name)==digest,name
    for name,digest in analysis['files'].items(): assert sha(RUN/name)==digest,name
    rows=list(csv.DictReader((RUN/'results/metrics.csv').open()))
    keyed={(x['dataset'],x['method'],int(x['L'])):x for x in rows}
    assert len(rows)==len(keyed)==192
    boots=set(); raw_hashes={}; intervals=[]; dominance=[]; costs=[]
    for ds,frozen in zip(DATASETS,pre['datasets']):
        root=RUN/'results'/ds; inp=RUN/'inputs'/ds; model=RUN/'models'/ds
        conf=json.loads((root/'config.json').read_text()); manifest=json.loads((inp/'manifest.json').read_text())
        assert conf['formal'] and conf['n']==10000 and conf['threads']==1 and conf['L']==lock['L']
        assert [x['name'] for x in conf['methods']]==lock['methods']
        assert conf['queries']==manifest['paths']['query_path'] and conf['index']==manifest['paths']['index'] and conf['base']==manifest['paths']['base_path']
        assert sha(model/GATE_MODEL/'W.f32')==frozen['gate_W_sha256']
        assert sha(inp/'gt10.W.f32')==frozen['gt10_W_sha256']
        assert sha(model/'hnsw/full.topology.gz')==frozen['full_hnsw_topology_sha256']
        assert sha(model/GATE_MODEL/'best.pt')==frozen['training']['checkpoint_sha256']
        progress=json.loads((root/'timing_progress.json').read_text())
        assert len(progress)==192 and len({(x['method'],x['L'],x['repeat']) for x in progress})==192
        assert all(x['process_threads']==1 and x['formal'] for x in progress)
        assert not (root/'incomplete_attempts').exists(), 'Unexpected formal retry; audit it explicitly'
        for method in lock['methods']:
            for L in lock['L']:
                p=root/f'{method}_L{L}'; c=json.loads((p/'complete.json').read_text()); r=keyed[(ds,method,L)]
                assert c['status']=='PASS' and c['n']==10000 and c['threads']==1 and c['cpu']==15
                assert c['plain_count_bit_parity'] and c['warmup_bit_parity'] and len(c['seconds'])==3
                boots.add(c['boot_id']); times=np.asarray(c['seconds']); assert np.isfinite(times).all() and (times>0).all()
                assert abs(float(r['qps_mean'])-(10000/times).mean())<1e-9
                assert abs(float(r['qps_from_mean_wall'])-10000/times.mean())<1e-9
                for rep,sec in enumerate(times):
                    found=[x for x in progress if (x['method'],x['L'],x['repeat'])==(method,L,rep)]
                    assert len(found)==1 and found[0]['seconds']==sec and found[0]['boot_id']==c['boot_id']
                hits=np.fromfile(p/'hits10.i8','i1'); failed=np.fromfile(p/'failed_zero_hit.u8','u1'); miss=np.fromfile(p/'gt1_miss.u8','u1')
                assert hits.shape==failed.shape==miss.shape==(10000,) and ((hits>=0)&(hits<=10)).all()
                assert np.array_equal(failed,hits==0) and int(failed.sum())==int(r['failed_queries'])
                assert abs(hits.mean()/10-float(r['recall_at10']))<1e-12
                assert abs(miss.mean()-float(r['gt1_miss_rate']))<1e-12
                for f in p.iterdir():
                    if f.is_file():raw_hashes[str(f.relative_to(RUN))]=sha(f)
        for L in lock['L']:
            ours=keyed[(ds,'GT10',L)]; gate=keyed[(ds,'GATE',L)]
            dominance.append(dict(dataset=ds,L=L,GT10_dominates_GATE_at_same_budget=float(ours['recall_at10'])>=float(gate['recall_at10']) and float(ours['qps_mean'])>=float(gate['qps_mean']),GT10_timing_ranges_separated=float(ours['qps_min'])>float(gate['qps_max'])))
        stage_path=RUN/'reviews'/f'stage_formal_{ds}.json';stage=json.loads(stage_path.read_text());end=stage_path.stat().st_mtime
        intervals.append(dict(dataset=ds,seconds=stage['seconds'],start_approx_unix=end-stage['seconds'],end_approx_unix=end))
        feature=json.loads((inp/GATE_FEATURE_READY).read_text());hbkm=json.loads((inp/'hbkm.json').read_text()) if (inp/'hbkm.json').exists() else None
        labels=json.loads((inp/'labels/complete.json').read_text()); train=json.loads((model/GATE_MODEL/'complete.json').read_text())
        includes_hbkm=ds.startswith('laion')
        known=feature['seconds']+labels['total_seconds']+train['training_seconds']+(hbkm['seconds'] if hbkm and not includes_hbkm else 0)
        costs.append(dict(dataset=ds,release10_feature_seconds=feature['seconds'],feature_seconds_include_HBKM=includes_hbkm,HBKM_known_seconds=hbkm['seconds'] if hbkm else None,effective_GATE_known_preparation_subtotal_seconds=known,subtotal_excludes_input_identity_preparation_GT_original_NSG_superseded_attempts_and_unknown_history=True))
    assert len(boots)==1
    assert intervals[0]['start_approx_unix']>=pre['unix']
    assert all(b['start_approx_unix']>=a['end_approx_unix']-.05 for a,b in zip(intervals,intervals[1:]))
    paired=list(csv.DictReader((RUN/'results/paired_queries.csv').open())); assert len(paired)==288
    for p in paired:
        a=keyed[(p['dataset'],p['reference'],int(p['L']))];b=keyed[(p['dataset'],p['method'],int(p['L']))]
        assert int(b['failed_queries'])-int(a['failed_queries'])==int(p['new_zero_hit'])-int(p['rescued_zero_hit'])
        assert sum(int(p[x]) for x in ['improved_queries','worsened_queries','same_queries'])==10000
        assert abs((float(b['recall_at10'])-float(a['recall_at10']))*100-float(p['recall_delta_pp']))<1e-10
    targets=list(csv.DictReader((RUN/'results/common_recall.csv').open())); assert len(targets)==60
    for t in targets:
        eligible=[x for x in rows if x['dataset']==t['dataset'] and x['method']==t['method'] and float(x['recall_at10'])>=float(t['target_recall'])]
        assert bool(eligible)==(t['achieved']=='True')
        if eligible:assert float(t['qps'])==max(float(x['qps_mean']) for x in eligible)
    dump(RUN/'results/cost_accounting_notes.json',costs)
    dump(RUN/'results/observed_dominance.json',dominance)
    tz=timezone(timedelta(hours=8));formal_seconds=sum(x['seconds'] for x in intervals)
    dump(RUN/'results/runtime_actual.json',dict(formal_stage_seconds=formal_seconds,formal_stage_hours=formal_seconds/3600,formal_intervals=intervals,formal_start_beijing=datetime.fromtimestamp(intervals[0]['start_approx_unix'],tz).isoformat(),formal_end_beijing=datetime.fromtimestamp(intervals[-1]['end_approx_unix'],tz).isoformat(),initial_estimate_formal_hours=6.222524488,
        scope='Formal stage wall includes load, warmup, three timed passes, count and I/O; plotted QPS uses only the three plain search timers.'))
    dump(RUN/'reviews/final_numeric_audit.json',dict(status='PASS',unix=time.time(),points=192,wall_rounds=576,query_method_budget_outputs=1920000,timed_query_calls=5760000,formal_warm_plain_count_query_calls=9600000,all_16_budgets_through_1500=True,threads=1,cpu=15,boot_ids=sorted(boots),formal_retry_count=0,models_and_benchmark_source_unchanged_since_preflight=True,paired_rows=288,common_recall_rows=60,all_three_means_verified=True,protected_sources=protected(),raw_output_sha256=raw_hashes,post_run_tool_sha256=sha(Path(__file__))))
    print(json.dumps(dict(status='PASS',points=192,rounds=576,formal_hours=formal_seconds/3600,dominance_counts={ds:sum(x['GT10_dominates_GATE_at_same_budget'] for x in dominance if x['dataset']==ds) for ds in DATASETS},timing_range_counts={ds:sum(x['GT10_timing_ranges_separated'] for x in dominance if x['dataset']==ds) for ds in DATASETS})))

if __name__=='__main__':main()
