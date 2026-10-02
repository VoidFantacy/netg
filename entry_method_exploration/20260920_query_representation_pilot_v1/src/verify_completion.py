from common import *
import re,datetime
import torch

def verify():
    gate=read(RUN/'reviews/representation_gate.json')
    assert gate['status']=='STOP_REPRESENTATION'
    assert not any(x['primary_ANN_gate']['passed'] for x in gate['datasets'])
    assert read(RUN/'reviews/headroom_gate.json')['status']=='PASS'
    assert read(RUN/'reviews/parity_gate.json')['status']=='PASS'
    assert read(RUN/'reviews/objective_checks.json')['status']=='PASS'
    frozen=read(RUN/'reviews/models_frozen.json');assert len(frozen['models'])==6
    for x in frozen['all_files']+[frozen['source']]:assert sha(x['path'])==x['sha256']
    trained=read(RUN/'results/training_runs.json');assert len(trained)==6
    for m in trained:
        assert m['epochs']==40 and m['seed']==20260920 and not m['cal_payload_access']
        assert m['final']['objective']<m['initial']['objective']
        out=RUN/'models'/m['dataset']/m['family']
        saved=torch.load(out/'model.pt',map_location='cpu',weights_only=True)
        for name in (['W'] if m['family']=='WFree' else ['U','V']):
            assert np.array_equal(saved[name].numpy().ravel(),np.fromfile(out/(name+'.f32'),'float32'))
        assert saved['P'].shape==(m['h'],m['dim'])
        assert np.array_equal(saved['P'].numpy().ravel(),np.fromfile(m['P'],'float32'))
    freeze_time=(RUN/'reviews/models_frozen.json').stat().st_mtime_ns
    protected=read(RUN/'reviews/protected_before.json')
    for x in protected:assert sha(x['path'])==x['sha256'],x['path']
    original_files={}
    for ds in DS:
        for split in ['fit','cal']:
            manifest=read(RUN/'inputs'/ds/split/'manifest.json')
            for x in manifest['source_inputs']+manifest['router_assets']+manifest['new_inputs']:
                assert sha(x['path'])==x['sha256'],x['path'];original_files[x['path']]=x
            old=manifest['index_stat'];assert stat_identity(old['path'])==old
            if split=='cal':
                for name in ['queries.f32','gt.i64']:
                    assert (RUN/'inputs'/ds/split/name).stat().st_mtime_ns>freeze_time
    for name in ['label_source_lock.json','quality_source_lock.json']:
        lock=read(RUN/'reviews'/name)
        for x in lock['sources']+[lock['binary']]+lock.get('libraries',[]):assert sha(x['path'])==x['sha256'],x['path']
    assert (RUN/'src/search_core.hpp').read_text()==(RUN/'src/label.cpp').read_text().split('static void guard',1)[0]
    e103=ROOT/'entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/src/kernels.hpp'
    assert sha(e103)==sha(RUN/'src/kernels.hpp')
    # Verify pre-edit document snapshots against the preceding research audit.
    prior=read(ROOT/'entry_method_exploration/20260920_query_representation_research_v1/reviews/completion_audit.json')
    root_names=['spec.md','summary.md','s-target.md','s-experiment.md','experiment_history/README.md']
    for name in root_names:
        expected=next(x['sha256'] for x in prior['delivered'] if x['path']==name)
        assert sha(RUN/'source_before'/name)==expected
    assert sha(RUN/'source_before/AGENTS.md')==sha(ROOT/'AGENTS.md')
    label_jobs=read(RUN/'logs/label_jobs.json');quality_jobs=read(RUN/'logs/quality_jobs.json')
    assert len(label_jobs)==6 and len(quality_jobs)==2
    for job in label_jobs+quality_jobs:
        assert job['status']=='FINISHED' and job['exit_code']==0
        pid=job['pid'];cmd=Path(f'/proc/{pid}/cmdline')
        assert not cmd.exists() or str(RUN/'bin').encode() not in cmd.read_bytes(),'same job still running'
    main_calls=sum(x['actual_main_calls'] for x in label_jobs)+sum(x['result']['main_search_calls'] for x in quality_jobs)
    route_calls=sum(x['router_calls'] for x in label_jobs)+sum(x['result']['router_calls'] for x in quality_jobs)
    assert main_calls==655808 and main_calls<LOCK['max_main_search_calls'] and route_calls==36000
    assert all(read(Path(x['output'])/'complete.json')['threads']==1 for x in label_jobs)
    assert all(x['result']['threads']==1 for x in quality_jobs)
    assert all(x['result']['formal'] is False for x in quality_jobs)
    assert not list(RUN.rglob('timing_progress.json')),'No conditional plain matrix should exist'
    metrics=read(RUN/'results/quality_metrics.json');assert len(metrics)==72
    independently_recomputed=[]
    for ds in DS:
        c=read(RUN/'inputs'/ds/'cal/config.json');gt=np.fromfile(c['gt'],'int64').reshape(512,100)
        label=RUN/'labels'/ds/'cal_labels';slots=np.fromfile(label/'baseline_slots.i32','int32').reshape(512,2)[:,0]
        for K in [1,100]:
            raw=np.memmap(label/f'k{K}.ids.i32',mode='r',dtype='int32',shape=(512,56,K))
            original=raw[np.arange(512),slots]
            def total(a):return sum(len(set(map(int,a[i])).intersection(map(int,gt[i,:K]))) for i in range(512))
            base_hits=total(original)
            for method in ['IdentityANN','QLinearANN','QMLPANN','WFreeANN']:
                a=np.fromfile(RUN/'results'/ds/'quality'/method/f'k{K}.ids.i32','int32').reshape(2560,K)[2048:]
                count=total(a);row=next(x for x in metrics if (x['dataset'],x['split'],x['method'],x['K'])==(ds,'cal',method,K))
                assert abs(row['recall']-count/512/K)<1e-12
                delta=(count-base_hits)/512/K*100
                assert abs(row['delta_gt10_pp']-delta)<1e-10
                if method=='QMLPANN':assert count<base_hits
                independently_recomputed.append(dict(dataset=ds,method=method,K=K,hit_sum=count,baseline_hit_sum=base_hits,delta_pp=delta))
    figures=read(RUN/'reviews/figure_manifest.json')
    for x in figures['files']:assert sha(x['path'])==x['sha256']
    assert read(RUN/'reviews/figure_review.json')['png_visually_checked']
    docs=[RUN/'report.md',RUN/'protocol.md',ROOT/'experiment_history/98_query_representation_pilot.md']+[ROOT/x for x in root_names]
    missing=[];link_count=0;audit_path=RUN/'reviews/completion_audit.json'
    for p in docs:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
            if target.startswith(('http://','https://','#','mailto:')):continue
            target=target.split('#',1)[0]
            if not target:continue
            destination=(p.parent/target).resolve();link_count+=1
            if not destination.exists() and destination!=audit_path:missing.append(dict(source=str(p),target=target))
    assert not missing,missing
    costs=dict(main_nsg_calls=main_calls,micro_hnsw_route_calls=route_calls,training_runs=6,
               training_seconds=frozen['wall_seconds'],training_maxrss_kib=frozen['maxrss_kib'],
               search_subprocess_wall_seconds=sum(x['wall_seconds'] for x in label_jobs+quality_jobs),
               search_maxrss_kib=max([read(Path(x['output'])/'complete.json')['maxrss_kib'] for x in label_jobs]+[x['result']['maxrss_kib'] for x in quality_jobs]),
               micro_hnsw_builds=2,micro_hnsw_build_seconds=sum(m['graph_build_seconds'] for x in quality_jobs for m in x['result']['models']),
               fresh_gt_calls=0,bottom_graph_builds=0,K10_searches=0,formal_plain_rounds=0,
               version_elapsed_seconds=time.time()-LOCK['created_unix'],
               generated_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()),
               inherited_GT_graph_profile_cost='not remeasured; not zero')
    assert costs['training_seconds']<1800 and costs['version_elapsed_seconds']<7200
    dump(RUN/'reviews/cost.json',costs)
    requirements=[
        dict(item='source/data identities and disjoint historical roles',status='PASS',evidence='inputs/*/{fit,cal}/manifest.json'),
        dict(item='six entry permutations and same-entry original kernel',status='PASS',evidence='reviews/parity_gate.json'),
        dict(item='true K1/K100 joint utility and fit headroom gate',status='PASS',evidence='reviews/headroom_gate.json'),
        dict(item='six fixed model runs and cal after freeze',status='PASS',evidence='reviews/models_frozen.json'),
        dict(item='actual exact/ANN routing and independent scoring',status='PASS',evidence='results/quality_metrics.csv'),
        dict(item='prelocked representation decision',status='STOP_REPRESENTATION',evidence='reviews/representation_gate.json'),
        dict(item='conditional 160-config/480-plain full wall',status='NOT_ENTERED_BY_FROZEN_GATE',evidence='reviews/representation_gate.json'),
        dict(item='complete paired results, costs, figure and handoff',status='PASS',evidence='report.md'),
    ]
    result=dict(status='PASS_TASK_COMPLETE_METHOD_STOP',time=datetime.datetime.now().astimezone().isoformat(),requirements=requirements,
                protected_selected_files_unchanged=len(protected),input_and_router_identities_verified=len(original_files),
                large_index_checks='size/mtime, loaded shape/metric; no fresh full content hash',
                root_before_snapshots_verified=6,current_documents=[identity(p) for p in docs],
                compiled_kernel_byte_identical_E103=True,live_same_jobs=0,local_links_checked=link_count,missing_local_links=[],
                independent_raw_return_recomputation=independently_recomputed,models_frozen_before_cal_payload_copy=True,
                fresh_test_or_heldout_access=False,production_changed=False,default_changed=False,costs=costs,
                source=identity(Path(__file__)))
    dump(audit_path,result)
    print(json.dumps({k:result[k] for k in ['status','protected_selected_files_unchanged','input_and_router_identities_verified','live_same_jobs','local_links_checked','costs']}))

if __name__=='__main__':verify()
