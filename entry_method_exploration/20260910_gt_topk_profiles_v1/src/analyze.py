"""Independent output scoring, fixed comparisons, costs and scientific figures. No searches."""
import csv
import hashlib
import time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import DATASETS, E23, RUN, check_lock, dump, identity, read, sha

SHORT={DATASETS[0]:'WebVid',DATASETS[1]:'Yandex-IP'}
LABEL={'nsg_medoid':'NSG','fast30k_3':'Fast30K-3','gt1_hard':'Fast20K / GT1 hard',
       'gt10_hard':'GT10 hard','gt1_soft':'GT1 soft','gt10_soft':'GT10 soft'}
COLOR={'nsg_medoid':'#9299a5','fast30k_3':'#695e75','gt1_hard':'#181f2a',
       'gt10_hard':'#d77a16','gt1_soft':'#3478ba','gt10_soft':'#11856a'}


def csv_write(path, rows):
    if not rows:return
    with Path(path).open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def bootstrap(delta, seed):
    rng=np.random.default_rng(seed);values=[];n=len(delta)
    for start in range(0,2000,50):
        ids=rng.integers(n,size=(min(50,2000-start),n))
        values.extend(delta[ids].mean(axis=1)*10)  # one hit is 10 Recall percentage points
    return np.quantile(values,[.025,.975]).tolist()


def main():
    started=time.monotonic();lock=check_lock()
    state=read(RUN/'state.json')
    completed_validation=state.get('all_60_points_complete',False) or all((RUN/'results'/ds/'results.json').exists() for ds in DATASETS)
    if read(RUN/'reviews/cal_gate.json')['validation_allowed']:
        assert completed_validation,'cannot analyze partial validation as a complete run'
    metrics=[];arrays={};all_checks=[];microchecks=[];regressions=[];ann=[]
    for ds in DATASETS:
        meta=read(RUN/'inputs'/ds/'prepared.json')
        for stage in ['recovery','cal','audit']+(['validation'] if completed_validation else []):
            folder=RUN/('results' if stage=='validation' else 'diagnostics')/ds
            if stage!='validation':folder/=stage
            result=read(folder/'results.json');config=read(folder/'config.json')
            assert result['status']=='COMPLETE' and result['threads']==1
            n=config['num_queries'];gtk=config['gt_k'];assert gtk==100
            gt=np.fromfile(config['gt_file'],dtype='<i8').reshape(n,gtk)[:,:10]
            rows=np.fromfile(config['row_ids'],dtype='<i8')
            assert np.array_equal(rows,np.fromfile(folder/'row_ids.i64',dtype='<i8'))
            tc=read(folder/'thread_contract.json')
            assert tc['status']=='PASS' and tc['actual_openmp_threads']==tc['process_threads']==1
            assert tc['cpu']==lock['query_cpu']
            per_family={}
            for m in result['methods']:
                path=folder/m['name']
                ids=np.fromfile(path/'ids.i32',dtype='<i4').reshape(n,10)
                dist=np.fromfile(path/'distances.f32',dtype='<f4').reshape(n,10)
                entries=np.fromfile(path/'entry_ids.i32',dtype='<i4').reshape(n,3)
                hits=np.fromfile(path/'hits.u8',dtype='u1')
                masks=np.fromfile(path/'hitmask.u16',dtype='<u2')
                r=np.fromfile(path/'route_ndc.u32',dtype='<u4').astype('int64')
                g=np.fromfile(path/'graph_ndc.u32',dtype='<u4').astype('int64')
                assert np.isfinite(dist).all() and (ids>=0).all() and (ids<meta['base_rows']).all()
                assert (np.diff(np.sort(ids,axis=1),axis=1)>0).all()
                independent_masks=np.zeros(n,dtype='<u2')
                for rank in range(10):independent_masks|=((ids==gt[:,rank,None]).any(axis=1).astype('<u2')<<rank)
                independent_hits=np.array([int(x).bit_count() for x in independent_masks],dtype='u1')
                assert np.array_equal(masks,independent_masks) and np.array_equal(hits,independent_hits)
                assert int(hits.sum())==m['total_hits'] and int((hits==0).sum())==m['failed_queries']
                assert abs(hits.mean()/10-m['recall_at_10'])<1e-12
                assert abs(r.mean()-m['mean_route_ndc'])<1e-12 and abs(g.mean()-m['mean_graph_ndc'])<1e-12
                assert abs((r+g).mean()-m['mean_total_ndc'])<1e-10
                assert m['process_threads']==1
                if m['family']!='nsg_medoid':
                    assert (np.diff(np.sort(entries,axis=1),axis=1)>0).all()
                    hubs=np.fromfile(RUN/'inputs'/ds/'hub_ids.i32',dtype='<i4')
                    assert np.isin(entries,hubs).all()
                    if m['configuration']['canonical_entry_order']:assert (np.diff(entries,axis=1)>0).all()
                else:assert np.all(r==0)
                if config['measure_wall']:
                    assert m['warmup_queries']==n and m['timing_repeats']==1
                    assert abs(m['qps']-n/m['end_to_end_seconds'])<1e-8
                else:assert m['qps'] is None and m['end_to_end_seconds'] is None and m['warmup_queries']==0
                key=(ds,stage,m['name']);arrays[key]={'hits':hits.astype('int16'),'r':r,'g':g,'entries':entries,'path':path,'rows':rows}
                rec={'dataset':ds,'stage':stage,'method':m['name'],'family':m['family'],
                     'model_name':m['configuration'].get('model_name',m['family']),
                     'exact':m['configuration'].get('exact',False),'L':m['L'],'queries':n,
                     'recall_percent':100*m['recall_at_10'],'qps':m['qps'],'total_hits':m['total_hits'],
                     'failed_queries':m['failed_queries'],'failure_percent':100*m['failure_rate'],
                     'route_ndc':m['mean_route_ndc'],'graph_ndc':m['mean_graph_ndc'],'total_ndc':m['mean_total_ndc'],
                     'end_to_end_seconds':m['end_to_end_seconds'],'route_only_seconds':m['route_only_seconds'],
                     'graph_only_seconds':m['graph_only_seconds'],
                     'router_construct_seconds':m['router_plain_construct_seconds'],
                     'router_count_load_seconds':m['router_count_load_seconds'],'physical_calls':m['physical_graph_calls']}
                metrics.append(rec)
                all_checks.append({'dataset':ds,'stage':stage,'method':m['name'],'queries':n,'status':'PASS'})
                if stage=='validation':
                    entry_digest=hashlib.sha256(entries.tobytes()).hexdigest()
                    graphfile=folder/(m['name']+'.hnsw')
                    graphhash=sha(graphfile) if graphfile.exists() else None
                    per_family.setdefault(m['family'],[]).append({'L':m['L'],'entries_sha256':entry_digest,'hnsw_sha256':graphhash})
            for family,records in per_family.items():
                assert len({x['entries_sha256'] for x in records})==1
                assert len({x['hnsw_sha256'] for x in records})==1
                microchecks.append({'dataset':ds,'family':family,'status':'PASS','five_L':records})
        for stage in ['cal','audit']:
            table=[m for m in metrics if m['dataset']==ds and m['stage']==stage]
            baseline=next(x for x in table if x['family']=='gt1_hard' and not x['exact'])
            ba=arrays[(ds,stage,baseline['method'])]
            for m in table:
                if m['exact']:continue
                ex=next(x for x in table if x['model_name']==m['model_name'] and x['exact'])
                a=arrays[(ds,stage,m['method'])];b=arrays[(ds,stage,ex['method'])]
                overlap=np.array([len(set(x)&set(y)) for x,y in zip(a['entries'],b['entries'])])
                changed=np.any(np.sort(a['entries'],axis=1)!=np.sort(ba['entries'],axis=1),axis=1)
                ann.append({'dataset':ds,'stage':stage,'model_name':m['model_name'],'family':m['family'],
                    'HNSW_recall_percent':m['recall_percent'],'exact_recall_percent':ex['recall_percent'],
                    'exact_minus_HNSW_pp':ex['recall_percent']-m['recall_percent'],
                    'ANN_top3_set_recall_percent':100*overlap.mean()/3,
                    'identical_exact_set_percent':100*np.mean(overlap==3),
                    'changed_vs_Fast20K_percent':100*changed.mean()})
        if completed_validation:
            old=read(E23/'results'/ds/'results.json')
            for family,oldfamily in [('nsg_medoid','nsg_medoid'),('fast30k_3','fast30k_3'),('gt1_hard','fast20k_3')]:
                for L in lock['L']:
                    current=next(x for x in metrics if x['dataset']==ds and x['stage']=='validation' and x['family']==family and x['L']==L)
                    prior=next(x for x in old['methods'] if x['family']==oldfamily and x['L']==L)
                    currdir=arrays[(ds,'validation',current['method'])]['path'];priorpath=E23/'results'/ds/prior['name']
                    fields=['ids.i32','distances.f32','entry_ids.i32','hits.u8','hitmask.u16','route_ndc.u32','graph_ndc.u32']
                    for field in fields:assert (currdir/field).read_bytes()==(priorpath/field).read_bytes(),(ds,family,L,field)
                    regressions.append({'dataset':ds,'family':family,'L':L,'queries':2000,'fields':fields,'status':'BIT_EQUAL_TO_E23'})
    csv_write(RUN/'results/metrics.csv',metrics);csv_write(RUN/'results/ann_diagnostics.csv',ann)
    comparisons=[]
    for m in metrics:
        if m['stage']=='recovery' or m['exact']:continue
        bases=['gt1_hard','nsg_medoid'] if m['stage']=='validation' else ['gt1_hard']
        for base in bases:
            if m['family']==base:continue
            b=next(x for x in metrics if x['dataset']==m['dataset'] and x['stage']==m['stage'] and x['L']==m['L'] and x['family']==base and not x['exact'])
            aarr=arrays[(m['dataset'],m['stage'],m['method'])];barr=arrays[(b['dataset'],b['stage'],b['method'])]
            delta=aarr['hits']-barr['hits']
            # The same seed is reset for every pair: aligned query bootstrap, not timing/entry bootstrap.
            ci=bootstrap(delta,20260910)
            comps={'dataset':m['dataset'],'stage':m['stage'],'L':m['L'],'method':m['method'],'family':m['family'],
                 'baseline':base,'delta_recall_pp':m['recall_percent']-b['recall_percent'],
                 'query_bootstrap95_low_pp':ci[0],'query_bootstrap95_high_pp':ci[1],
                 'qps_change_percent':100*(m['qps']/b['qps']-1) if m['qps'] is not None else None,
                 'route_ndc_change':m['route_ndc']-b['route_ndc'],
                 'graph_ndc_change_percent':100*(m['graph_ndc']/b['graph_ndc']-1),
                 'total_ndc_change_percent':100*(m['total_ndc']/b['total_ndc']-1),
                 'baseline_failed':b['failed_queries'],'method_failed':m['failed_queries'],
                 'rescued':int(((barr['hits']==0)&(aarr['hits']>0)).sum()),
                 'newly_harmed':int(((barr['hits']>0)&(aarr['hits']==0)).sum()),
                 'still_failed':int(((barr['hits']==0)&(aarr['hits']==0)).sum()),
                 'changed_entry_set_percent':100*np.any(np.sort(aarr['entries'],axis=1)!=np.sort(barr['entries'],axis=1),axis=1).mean()}
            assert comps['method_failed']==comps['baseline_failed']-comps['rescued']+comps['newly_harmed']
            comparisons.append(comps)
    csv_write(RUN/'results/comparisons.csv',comparisons)
    support=[]
    for ds in DATASETS:
        for m in read(RUN/'models'/ds/'complete.json')['models']:
            s=m['support']
            support.append({'dataset':ds,'model_name':m['name'],'family':m['family'],'K_gt':m['K_gt'],
                'temperature':m['temperature'],'positive_mass_hubs':m['hubs_with_positive_mass'],
                'median_mass':s['mass']['median'],'max_mass':s['mass']['max'],'median_ESS':s['ess']['median'],
                'median_query_effective_hubs':s['query_effective_hubs']['median'],
                'mean_max_query_weight':s['query_max_weight']['mean'],
                'mean_cosine_to_P0':m['cosine_to_P0']['mean'],'max_abs_to_P0':m['max_abs_to_P0']})
    csv_write(RUN/'results/profile_support.csv',support)
    dump(RUN/'reviews/result_verification.json',{'status':'PASS','points':len(all_checks),
         'independently_rescored_outputs':sum(x['queries'] for x in all_checks),
         'checks':all_checks,'single_thread_and_CPU_checked':True,'all_distance_bits_native_count_plain':'evaluated in each point outside wall',
         'five_L_same_entries_and_HNSW':microchecks,'E23_baseline_regressions':regressions,
         'E23_baseline_regression_outputs':sum(x['queries'] for x in regressions)})
    primary={ds:read(RUN/'models'/ds/'selection.json')['primary']['family'] for ds in DATASETS}
    summary={'status':'ANALYSIS_COMPLETE','completed_validation':completed_validation,'primary_families':primary,
             'cal_gate':read(RUN/'reviews/cal_gate.json')['status'],'metrics':metrics,'comparisons':comparisons,
             'ann_diagnostics':ann,'support':support,
             'limitations':['one QGT construction','one timing per point','historically reused development and validation',
               'query bootstrap uncorrected descriptive only','cosine target assignment retains raw-IP norm mismatch',
               'exact profile score is not entry-utility oracle','no held-out access']}
    dump(RUN/'results/summary.json',summary)
    tables=['# E24 完整原值与对照','',
        '新方法构建只用fit；cal选参数，audit只报告，validation按预冻结选择。所有QPS为单线程单方法独立plain wall，单次计时。',
        'GT1硬即matched Fast20K；GT1软/GT10软在audit与validation使用各自cal冻结温度。', '']
    for stage in ['cal','audit']+(['validation'] if completed_validation else []):
        tables+=['## '+stage,'','| 数据集 | 方法 | L | Recall@10 % | QPS | 零命中 | route NDC | graph NDC | total NDC |',
                 '|---|---|---:|---:|---:|---:|---:|---:|---:|']
        for m in metrics:
            if m['stage']!=stage:continue
            qps=f"{m['qps']:.2f}" if m['qps'] is not None else '未计时'
            tables.append(f"| {SHORT[m['dataset']]} | {m['method']} | {m['L']} | {m['recall_percent']:.4f} | {qps} | {m['failed_queries']} | {m['route_ndc']:.3f} | {m['graph_ndc']:.3f} | {m['total_ndc']:.3f} |")
        tables.append('')
    tables+=['## 相对matched Fast20K的validation消融','',
             '| 数据集 | 方法 | L | ΔRecall pp | ΔQPS % | query bootstrap 95% pp | 挽救 / 新增失败 |',
             '|---|---|---:|---:|---:|---|---|']
    for c in comparisons:
        if c['stage']!='validation' or c['baseline']!='gt1_hard' or c['family'] not in ['gt10_hard','gt1_soft','gt10_soft']:continue
        tables.append(f"| {SHORT[c['dataset']]} | {LABEL[c['family']]} | {c['L']} | {c['delta_recall_pp']:+.3f} | {c['qps_change_percent']:+.2f} | [{c['query_bootstrap95_low_pp']:+.3f}, {c['query_bootstrap95_high_pp']:+.3f}] | {c['rescued']} / {c['newly_harmed']} |")
    tables+=['','全部对NSG及matched Fast的配对结果：[comparisons.csv](comparisons.csv)。',
             '画像支持：[profile_support.csv](profile_support.csv)；近似检索诊断：[ann_diagnostics.csv](ann_diagnostics.csv)。',
             '曲线：[Recall–QPS](../figures/recall_qps.svg)；成本：[costs.json](costs.json)。']
    (RUN/'results/tables.md').write_text('\n'.join(tables)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    if completed_validation:
        fig,axes=plt.subplots(1,2,figsize=(13,5.2),constrained_layout=True)
        for ax,ds in zip(axes,DATASETS):
            for family in LABEL:
                data=sorted([m for m in metrics if m['stage']=='validation' and m['dataset']==ds and m['family']==family],key=lambda x:x['L'])
                ax.plot([x['recall_percent'] for x in data],[x['qps'] for x in data],marker='o',markersize=4,
                        color=COLOR[family],label=LABEL[family],linestyle='--' if family=='fast30k_3' else '-',
                        linewidth=2 if family=='gt1_hard' else 1.5)
            ax.set(title=SHORT[ds]+' | validation 2,000',xlabel='Recall@10 (%)',ylabel='End-to-end QPS (1 thread)')
            ax.grid(alpha=.18);ax.legend(fontsize=8,loc='upper right')
        fig.suptitle('Fixed H, three real entries: GT1/GT10 x hard/soft profiles\nOne build; one independent plain-wall timing per point',fontsize=12)
        for ext in ['png','svg']:fig.savefig(RUN/f'figures/recall_qps.{ext}',dpi=180)
        plt.close(fig)
        fig,axes=plt.subplots(2,2,figsize=(12,7),sharex='col',constrained_layout=True)
        for col,ds in enumerate(DATASETS):
            for family in ['gt10_hard','gt1_soft','gt10_soft']:
                data=sorted([c for c in comparisons if c['stage']=='validation' and c['dataset']==ds and c['family']==family and c['baseline']=='gt1_hard'],key=lambda x:x['L'])
                xx=np.arange(5)
                axes[0,col].plot(xx,[c['delta_recall_pp'] for c in data],marker='o',color=COLOR[family],label=LABEL[family])
                axes[1,col].plot(xx,[c['qps_change_percent'] for c in data],marker='o',color=COLOR[family])
            axes[0,col].set_title(SHORT[ds]);axes[0,col].set_ylabel('Recall change (percentage points)')
            axes[1,col].set_ylabel('QPS change (%)');axes[1,col].set_xlabel('NSG search L')
            for row in range(2):
                axes[row,col].axhline(0,color='black',lw=.8);axes[row,col].grid(alpha=.2)
                axes[row,col].set_xticks(np.arange(5),[str(x) for x in lock['L']])
            axes[0,col].legend(fontsize=9)
        fig.suptitle('Validation changes versus matched Fast20K-3\nTiming differences are exploratory, not a stability claim',fontsize=12)
        for ext in ['png','svg']:fig.savefig(RUN/f'figures/deltas.{ext}',dpi=180)
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,5),constrained_layout=True)
    for ax,ds in zip(axes,DATASETS):
        for m in [x for x in metrics if x['dataset']==ds and x['stage']=='cal' and not x['exact']]:
            ax.scatter(m['recall_percent'],m['qps'],color=COLOR[m['family']],s=35)
            ax.annotate(m['model_name'].replace('gt','GT').replace('_',' '),(m['recall_percent'],m['qps']),xytext=(4,4),textcoords='offset points',fontsize=7)
        ax.set(title=SHORT[ds]+' | cal 1,024, L128',xlabel='Recall@10 (%)',ylabel='End-to-end QPS (1 thread)');ax.grid(alpha=.2)
    fig.suptitle('Predeclared calibration candidates: HNSW direct3 (selection uses hits, not time)',fontsize=12)
    for ext in ['png','svg']:fig.savefig(RUN/f'figures/cal_recall_qps.{ext}',dpi=180)
    if not completed_validation:
        for ext in ['png','svg']:fig.savefig(RUN/f'figures/recall_qps.{ext}',dpi=180)
    plt.close(fig)
    jobs=read(RUN/'reviews/search_jobs.json')
    costs={'physical_real_search_calls':sum(j['actual_calls'] for j in jobs),
        'reserved_real_search_calls':sum(j['reserved_calls'] for j in jobs),'normal_limit':lock['normal_real_call_cap'],
        'hard_limit':lock['total_real_call_cap'],'repair_calls_used':sum(j['reserved_calls'] for j in jobs if j.get('repair')),
        'synthetic_calls':sum(j['actual_calls'] for j in read(RUN/'reviews/synthetic_jobs.json')),
        'new_training_label_search_calls':0,'single_or_triple_training_labels_dependency':False,
        'processes':jobs,'process_seconds_by_stage':{stage:sum(j['process_seconds'] for j in jobs if j['name'].startswith(stage+'_')) for stage in ['recovery','cal','audit','validation']},
        'input_verification_prepare_seconds':read(RUN/'inputs/preflight.json')['seconds'],
        'evaluator_compile_seconds':read(RUN/'bin/evaluate.build.json')['seconds'],
        'profile_build':{ds:{key:read(RUN/'models'/ds/'complete.json')[key] for key in ['total_stage_seconds','shared_assignment_costs']} for ds in DATASETS},
        'GT1_hard_recovery_core_seconds':{ds:read(RUN/'models'/ds/'gt1_hard/manifest.json')['profile_seconds'] for ds in DATASETS},
        'new_method_offline_cost_boundary':'fit targets loaded, scores/weights/profiles built; GT/QGT/NSG already available; repeated eval router builds counted separately',
        'all_evaluator_router_construct_seconds':sum(m['router_construct_seconds'] for m in metrics),
        'all_evaluator_count_router_load_seconds':sum(m['router_count_load_seconds'] for m in metrics),
        'exact_GT_from_scratch':{'seconds':None,'reason':'reused existing exact raw-IP GT100; generation not rerun'},
        'QGT_H_from_scratch':{'seconds':None,'reason':'fixed existing seed20260828 H; no clustering or hub selection rerun'},
        'NSG_from_scratch':{'seconds':None,'reason':'frozen graph reused; old info timings not remeasured full pipeline'},
        'max_observed_RSS_bytes':max(j['max_observed_rss_bytes'] for j in jobs),
        'maximum_process_threads':max(j['max_observed_process_threads'] for j in jobs),
        'query_cpu':lock['query_cpu'],'cache_condition':'warm batch, source hashes/load may warm OS cache; no cold-cache control',
        'analysis_seconds':time.monotonic()-started}
    dump(RUN/'results/costs.json',costs)
    print('ANALYSIS_COMPLETE',len(metrics),'points',sum(x['queries'] for x in all_checks),'rescored outputs',flush=True)
    for c in comparisons:
        if c['stage']=='validation' and c['baseline']=='gt1_hard' and c['family']==primary[c['dataset']]:
            print(SHORT[c['dataset']],c['L'],c['family'],'deltaR',round(c['delta_recall_pp'],4),'deltaQPS',round(c['qps_change_percent'],3),'CI',c['query_bootstrap95_low_pp'],c['query_bootstrap95_high_pp'],flush=True)


if __name__=='__main__':main()
