#!/usr/bin/env python3
"""Verify aligned outputs, report fixed-scope comparisons, and plot measured points."""
import csv
from pathlib import Path
import numpy as np
from common import DATASETS, LS, OLD, RUN, dump, identity, read, sha

FAMILIES=['nsg_medoid','fast30k_3','fast20k_3','full','rank8']
LABELS={'nsg_medoid':'NSG','fast30k_3':'Fast30K-3','fast20k_3':'Fast20K-3','full':'Full-3','rank8':'Rank8-3'}
SHORT={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex-IP'}


def verify_output(dataset, folder, input_folder, timing):
    results=read(folder/'results.json');config=read(folder/'config.json');thread=read(folder/'thread_contract.json')
    n=config['num_queries'];assert results['status']=='COMPLETE' and results['threads']==1
    assert thread['actual_openmp_threads']==1
    for field in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:assert thread[field]=='1'
    rows=np.fromfile(input_folder/'row_ids.i64',dtype='<i8')
    assert np.array_equal(rows,np.fromfile(folder/'row_ids.i64',dtype='<i8'))
    gt=np.fromfile(input_folder/'gt.i64',dtype='<i8').reshape(n,100)[:,:10]
    count=0;by_key={};entry_cache={}
    for record in results['methods']:
        name=record['name'];out=folder/name;mc=record['configuration']
        ids=np.fromfile(out/'ids.i32',dtype='<i4').reshape(n,10)
        masks=np.fromfile(out/'hitmask.u16',dtype='<u2')
        hits=np.fromfile(out/'hits.u8',dtype='u1')
        entries=np.fromfile(out/'entry_ids.i32',dtype='<i4').reshape(n,3)
        rndc=np.fromfile(out/'route_ndc.u32',dtype='<u4')
        gndc=np.fromfile(out/'graph_ndc.u32',dtype='<u4')
        assert (ids>=0).all() and (np.diff(np.sort(ids,axis=1),axis=1)!=0).all()
        independent=(ids[:,:,None]==gt[:,None,:]).any(axis=1)
        assert np.array_equal(independent.sum(axis=1),hits)
        assert np.array_equal((independent*(1<<np.arange(10,dtype='<u2'))).sum(axis=1),masks)
        assert record['total_hits']==int(hits.sum()) and record['failed_queries']==int((hits==0).sum())
        assert abs(record['recall_at_10']-float(hits.mean()/10))<1e-12
        assert record['full_count_plain_parity_queries']==n
        assert abs(record['mean_graph_ndc']-float(gndc.mean()))<1e-9
        assert abs(record['mean_route_ndc']-float(rndc.mean()))<1e-9
        assert abs(record['mean_total_ndc']-float((rndc.astype('uint64')+gndc).mean()))<1e-9
        if record['family']=='nsg_medoid':
            assert (rndc==0).all() and (entries[:,1:]==-1).all()
        else:
            assert mc['k']==3 and (np.diff(np.sort(entries,axis=1),axis=1)!=0).all()
            if mc.get('canonical_entry_order'):assert (np.diff(entries,axis=1)>0).all()
        if timing:
            assert record['timing_repeats']==1 and record['warmup_queries']==n and record['warm_timed_parity_queries']==n
            assert abs(record['qps']-n/record['end_to_end_seconds'])<1e-9
            key=record['family'];by_key[(key,record['L'])]=(record,hits,gndc,rndc)
            if key in entry_cache:assert np.array_equal(entry_cache[key],entries),f'entry changes with L: {key}'
            else:entry_cache[key]=entries.copy()
        else:
            assert record['qps'] is None and record['timing_repeats']==0 and record['warmup_queries']==0
        count+=n
    return results,by_key,count


def main():
    assert read(RUN/'state.json')['status']=='VALIDATION_COMPLETE_ANALYSIS_PENDING'
    for item in read(RUN/'models/frozen_before_validation.json')['files']:
        assert sha(item['path'])==item['sha256'],item['path']
    records=[];comparisons=[];proof=[];diagnostics={};baseline_regression=0
    for dataset in DATASETS:
        inp=RUN/'inputs'/dataset
        results,by_key,verified=verify_output(dataset,RUN/'results'/dataset,inp/'validation',True)
        assert len(results['methods'])==25 and set(by_key)=={(f,L) for f in FAMILIES for L in LS}
        proof.append({'dataset':dataset,'validation_outputs_verified':verified,'model_and_entries_fixed_across_five_L':True})
        diagnostics[dataset]={}
        for split in ['fit_probe','cal','audit']:
            detail,_,n=verify_output(dataset,RUN/'diagnostics'/dataset/split,inp/split,False)
            diagnostics[dataset][split]=detail['methods']
            proof.append({'dataset':dataset,'split':split,'diagnostic_outputs_verified':n,'QPS_reported':False})
        for (family,L),(r,hits,gndc,rndc) in by_key.items():
            records.append({'dataset':dataset,'family':family,'L':L,'queries':r['queries'],
                'recall_at_10':r['recall_at_10'],'qps':r['qps'],'failed_queries':r['failed_queries'],
                'failure_rate':r['failure_rate'],'mean_graph_ndc':r['mean_graph_ndc'],
                'mean_route_ndc':r['mean_route_ndc'],'mean_total_ndc':r['mean_total_ndc'],
                'end_to_end_seconds':r['end_to_end_seconds'],'model_name':r['configuration'].get('model_name',family),
                'lambda':r['configuration'].get('lambda')})
            if family in ['nsg_medoid','fast30k_3']:
                old=OLD/'exploration_5point_v1/results'/dataset/f'{family}_L{L}'
                new=RUN/'results'/dataset/r['name']
                for filename,dtype in [('ids.i32','<i4'),('distances.f32','<u4'),('entry_ids.i32','<i4')]:
                    assert np.array_equal(np.fromfile(old/filename,dtype=dtype),np.fromfile(new/filename,dtype=dtype)),f'legacy regression: {dataset} {family} {L} {filename}'
                baseline_regression+=r['queries']
            if family in ['full','rank8']:
                for bf in ['fast20k_3','fast30k_3','nsg_medoid']:
                    b,bhits,bgndc,brndc=by_key[(bf,L)]
                    comparisons.append({'dataset':dataset,'family':family,'baseline':bf,'L':L,
                        'delta_recall_pp':100*(r['recall_at_10']-b['recall_at_10']),
                        'delta_qps_percent':100*(r['qps']/b['qps']-1),
                        'delta_graph_ndc_percent':100*(r['mean_graph_ndc']/b['mean_graph_ndc']-1),
                        'delta_total_ndc_percent':100*(r['mean_total_ndc']/b['mean_total_ndc']-1),
                        'baseline_failures':b['failed_queries'],'method_failures':r['failed_queries'],
                        'rescued_zero_hit':int(((bhits==0)&(hits>0)).sum()),
                        'newly_zero_hit':int(((bhits>0)&(hits==0)).sum()),
                        'queries_recall_improved':int((hits>bhits).sum()),'queries_recall_worsened':int((hits<bhits).sum())})
    for filename,rows in [('metrics.csv',records),('comparisons.csv',comparisons)]:
        with (RUN/'results'/filename).open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    summary={'status':'ALL_50_POINTS_VERIFIED','metrics':records,'comparisons':comparisons,'diagnostics':diagnostics,
             'scope':'two datasets, one build, 2000 validation queries each, five L, single timing repeat; exploratory only'}
    dump(RUN/'results/summary.json',summary)
    dump(RUN/'reviews/result_verification.json',{'status':'PASS','checks':proof,'legacy_NSG_and_Fast30K_outputs_bit_identical':baseline_regression,
        'validation_query_outputs_verified':100000,'diagnostic_metadata_exception':'See diagnostic_metadata_correction.json for v1 warm_timed_queries field only',
        'source_results':[identity(RUN/'results'/ds/'results.json') for ds in DATASETS]})
    # Standard standalone scientific figure; plot only actual measured points.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figures=RUN/'figures';figures.mkdir(exist_ok=True)
    colors={'nsg_medoid':'#7b8492','fast30k_3':'#222222','fast20k_3':'#2678bd','full':'#cf3c43','rank8':'#d89921'}
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
    for ax,ds in zip(axes,DATASETS):
        for family in FAMILIES:
            rows=sorted([r for r in records if r['dataset']==ds and r['family']==family],key=lambda x:x['L'])
            ax.plot([r['recall_at_10']*100 for r in rows],[r['qps'] for r in rows],'-o',ms=4,color=colors[family],label=LABELS[family])
        ax.set_title(SHORT[ds]);ax.set_xlabel('Recall@10 (%)');ax.set_ylabel('Queries / second')
        ax.set_yscale('log');ax.grid(True,alpha=.22);ax.legend(fontsize=8)
    fig.suptitle('Fixed three-entry routing: single-thread, 2,000 queries, one timing run',fontsize=11)
    fig.savefig(figures/'recall_qps.svg');fig.savefig(figures/'recall_qps.png',dpi=180);plt.close(fig)
    # Exact values remain in CSV; concise tables keep family and baseline identities explicit.
    lines=['# 三入口排序五点结果原值','',summary['scope'],'','[Recall–QPS图](../figures/recall_qps.svg)','']
    for ds in DATASETS:
        lines += ['## '+SHORT[ds],'','| L | 方法 | Recall@10 % | QPS | 零命中失败 | graph NDC | route NDC |','|---:|---|---:|---:|---:|---:|---:|']
        for L in LS:
            for family in FAMILIES:
                r=next(x for x in records if x['dataset']==ds and x['family']==family and x['L']==L)
                lines.append(f"| {L} | {LABELS[family]} | {100*r['recall_at_10']:.3f} | {r['qps']:.2f} | {r['failed_queries']} | {r['mean_graph_ndc']:.2f} | {r['mean_route_ndc']:.2f} |")
        lines.append('')
    (RUN/'results/tables.md').write_text('\n'.join(lines)+'\n')
    dump(RUN/'state.json',{'status':'RESULTS_VERIFIED_REPORT_PENDING','protocol_sha256':sha(RUN/'protocol.md'),
                           'points':50,'validation_query_outputs':100000,'new_method_status':'interpretation pending; no automatic performance GO'})
    print('ALL_50_POINTS_VERIFIED',flush=True)

if __name__=='__main__':main()
