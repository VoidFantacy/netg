#!/usr/bin/env python3
"""Matched single-thread NSG/Fast/A+B results, with original controls preserved."""
import csv
import json
import shutil
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from analyze_single_thread import aggregate, compare, DATASETS, SEEDS, NAMES

OUT=Path(__file__).resolve().parents[1]
RUN=OUT/'baseline_comparison_v1'
FAMILIES=['nsg_medoid','fast30k_3','fast20k_3','joint']
LABELS={'nsg_medoid':'NSG-Medoid','fast30k_3':'Fast30K-3','fast20k_3':'Fast20K-3','joint':'A+B'}


def dump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')


def main():
    dest=RUN/'analysis_v1';assert not dest.exists();dest.mkdir()
    table={};checks=[]
    for split in ['validation','heldout']:
        for ds in DATASETS:
            fixed_reference={}
            for seed in SEEDS:
                root=RUN/'results'/split/ds/f'seed{seed}'
                result=json.loads((root/'results.json').read_text())
                assert result['status']=='COMPLETE' and result['queries']==10000 and result['threads']==1
                assert len(result['methods'])==8
                assert json.loads((root/'config.json').read_text())['threads']==1
                runtime=json.loads((root/'thread_contract.json').read_text())
                assert runtime['status']=='PASS' and runtime['observed_openmp_threads']==1
                original=OUT/'single_thread_v1/results'/split/ds/f'seed{seed}'
                assert (root/'row_ids.i64').read_bytes()==(original/'row_ids.i64').read_bytes()
                for metric in result['methods']:
                    config=metric['configuration'];name=config['family'];L=config['L']
                    assert name in FAMILIES and L in [64,128]
                    folder=root/metric['name'];hits=np.fromfile(folder/'hits.u8',dtype='uint8')
                    assert len(hits)==10000 and int(hits.max())<=10
                    assert int(hits.sum())==metric['total_hits'] and int((hits==0).sum())==metric['failed_queries']
                    assert metric['plain_count_parity_queries']==10000 and len(metric['timings'])==3
                    for timing in metric['timings']:
                        assert timing['end_to_end_seconds']>0 and np.isclose(timing['qps'],10000/timing['end_to_end_seconds'])
                    compared=0
                    if name!='nsg_medoid':
                        for filename in ['hits.u8','hitmask.u16','route_ndc.u32','graph_ndc.u32','ids.i32','entry_ids.i32','router_labels.i32']:
                            assert (folder/filename).read_bytes()==(original/metric['name']/filename).read_bytes(),(ds,seed,L,name,filename)
                            compared+=1
                    else:
                        assert config['k']==1 and metric['mean_route_ndc']==0
                        route=np.fromfile(folder/'entry_ids.i32',dtype='int32').reshape(-1,3)
                        assert np.all(route[:,0]==config['fixed_entry']) and np.all(route[:,1:]==-1)
                        assert not (root/(metric['name']+'.hnsw')).exists()
                        signature=[(folder/x).read_bytes() for x in ['hits.u8','ids.i32','graph_ndc.u32']]
                        if L in fixed_reference:assert signature==fixed_reference[L], 'fixed NSG changed across QGT builds'
                        else:fixed_reference[L]=signature
                    table[split,ds,L,name,seed]={'metric':metric,'hits':hits,'folder':folder,'timings':metric['timings']}
                    checks.append({'split':split,'dataset':ds,'seed':seed,'L':L,'method':name,'threads':1,'queries':10000,'prior_output_files_identical':compared,'status':'PASS'})
    summaries=[];comparisons=[]
    for split in ['validation','heldout']:
        for ds in DATASETS:
            for L in [64,128]:
                for family in FAMILIES:summaries.append(aggregate(table,split,ds,L,family)[0])
                for baseline in ['nsg_medoid','fast30k_3','fast20k_3']:
                    comparisons.append(compare(table,split,ds,L,'joint',baseline))
                comparisons.append(compare(table,split,ds,L,'fast30k_3','nsg_medoid'))
    primary=[x for x in comparisons if x['split']=='heldout' and x['method']=='joint' and x['baseline']=='fast30k_3']
    quality=all(x['recall_gain_pp']>=-1e-10 for x in primary)
    significant=any(x['recall_gain_bootstrap_pp']['ci95_bonferroni4'][0]>0 for x in primary)
    speed=all(x['qps_change_pct']>=0 for x in primary)
    gate={'status':'GO_WITHIN_FROZEN_FOUR_POINTS' if quality and significant and speed else 'NO_GLOBAL_PARETO_GO',
          'primary_baseline':'Fast30K direct3 remeasured in same single-thread batch as NSG and A+B',
          'all_four_recall_nonnegative':quality,'at_least_one_bonferroni4_significant_recall_gain':significant,
          'all_four_mean_qps_nondecreasing':speed,'threads':1,'NSG_not_used_to_relax_Fast_gate':True}
    dump(dest/'verification.json',{'status':'PASS','threads':1,'result_checks':checks,
                                 'same_frozen_model_results_as_original_single_thread_run':True,
                                 'NSG_fixed_graph_not_three_independent_graph_builds':True})
    dump(dest/'summary.json',{'gate':gate,'summaries':summaries,'comparisons':comparisons})
    dump(dest/'gate.json',gate)
    fields=['split','dataset','L','method','recall','qps','qps_std','failure','mean_route_ndc','mean_graph_ndc','mean_total_ndc']
    with (dest/'metrics.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:x[k] for k in fields} for x in summaries)
    fields=['split','dataset','L','method','baseline','recall_gain_pp','qps_change_pct','failure_reduction_pp','failure_relative_reduction_pct']
    with (dest/'comparisons.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows({k:x[k] for k in fields} for x in comparisons)
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,ds in zip(axes,DATASETS):
        for family,marker in zip(FAMILIES,['D','s','^','o']):
            values=[s for s in summaries if s['split']=='heldout' and s['dataset']==ds and s['method']==family]
            ax.plot([v['recall']*100 for v in values],[v['qps'] for v in values],marker=marker,label=LABELS[family])
            for value in values:ax.annotate('L'+str(value['L']),(value['recall']*100,value['qps']),xytext=(3,3),textcoords='offset points',fontsize=7)
        ax.set(title=NAMES[ds],xlabel='Recall@10 (%)',ylabel='Single-thread end-to-end QPS');ax.grid(alpha=.25);ax.legend(fontsize=8)
    fig.suptitle('NSG, Fast and A+B measured together; 10K queries, three batches x three repeats')
    fig.tight_layout();fig.savefig(dest/'recall_qps.png',dpi=180);fig.savefig(dest/'recall_qps.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4));positions=np.arange(4);width=.24
    for offset,family in zip([-1,0,1],['nsg_medoid','fast30k_3','joint']):
        values=[next(s['failure']*100 for s in summaries if s['split']=='heldout' and s['dataset']==ds and s['L']==L and s['method']==family) for ds in DATASETS for L in [64,128]]
        ax.bar(positions+offset*width,values,width,label=LABELS[family])
    ax.set_xticks(positions,[f'{NAMES[ds]} L{L}' for ds in DATASETS for L in [64,128]])
    ax.set_ylabel('Failure rate: Recall@10 < 0.1 (%)');ax.legend();fig.tight_layout()
    fig.savefig(dest/'failure_rates.png',dpi=180);fig.savefig(dest/'failure_rates.pdf');plt.close(fig)
    report=OUT/'report.md'
    if report.exists():
        saved=OUT/'single_thread_v1/report_before_nsg.md';assert not saved.exists();shutil.copy2(report,saved)
    lines=['# A+B、Fast与NSG：单线程完整实测报告','',f"原Fast比较门：**{gate['status']}**。以下主表全部来自四方法同批单线程测量，未拼入旧16线程QPS。",'',
           '## Held-out10K 三项指标','',
           '| 数据集 | L | 方法 | Recall@10 | QPS | 失败率 | 三批失败查询数（每批10K） |','|---|---:|---|---:|---:|---:|---|']
    for s in summaries:
        if s['split']=='heldout':lines.append(f"| {NAMES[s['dataset']]} | {s['L']} | {LABELS[s['method']]} | {s['recall']*100:.3f}% | {s['qps']:.1f} | {s['failure']*100:.3f}% | {s['failed_queries_by_build']} |")
    lines+=['','失败严格`Recall@10<0.1`，即GT10零命中；命中1个不算失败。每个方法每批10K条，三个QGT构建对应三个比较批次，QPS为各批三轮共9次独立wall的QPS均值。NSG使用同一冻结图和固定入口，三批不是独立NSG构建。','',
            '## A+B相对Fast和NSG','',
            '| 数据集 | L | 基线 | ΔRecall（pp） | ΔQPS | 失败率下降（pp） | 失败率相对下降 | 挽救 / 新增失败（三批） |','|---|---:|---|---:|---:|---:|---:|---|']
    for r in comparisons:
        if r['split']=='heldout' and r['method']=='joint':
            relative='—' if r['failure_relative_reduction_pct'] is None else f"{r['failure_relative_reduction_pct']:+.2f}%"
            lines.append(f"| {NAMES[r['dataset']]} | {r['L']} | {LABELS[r['baseline']]} | {r['recall_gain_pp']:+.3f} | {r['qps_change_pct']:+.2f}% | {r['failure_reduction_pp']:+.3f} | {relative} | {r['rescued_by_build']} / {r['newly_failed_by_build']} |")
    lines+=['','正的失败率下降表示改善；负值表示失败增多。统计使用相同query配对，全部查询保留；四Fast主点Bonferroni校正区间和各批原始计时见完整JSON。加入NSG未放宽原Fast成功门，也没有重新训练或选择模型。','',
            '## 公平性与边界','',
            '- 全部方法使用相同raw IP、冻结NSG、K10和L64/128；NSG固定使用图中enterpoint，沿用项目NSG_Medoid定义。无Micro-HNSW，路由NDC为0。',
            '- Fast30K为历史direct3基线；Fast20K与A+B共用后20K画像训练数据和各自QGT构建，训练量区别明确保留。A+B是校准选择的新联合候选，没有用Fast回退掩盖负结果。',
            '- OpenMP/BLAS/MKL均为1，配置、实际OpenMP team和输出均验收；同一时段只执行一个评测进程。计时包含路由、映射、原图搜索和正常输出，排除GT、count、hash、JSON、装载和建图。',
            '- count/plain及三次plain输出一致；新增NSG与独立原kernel固定入口调用核验。Fast/A+B的全部逐query输出与先前单线程评测完全一致，仅QPS重新测量。',
            '- 验证/测试只在全部12个模型冻结后读取。1024 cal/audit来自历史开发池，仅对本次拟合隔离；三构建query配对bootstrap不估计任意新构建的总体不确定性。',
            '- 仅测L64/128，不用连线推断未测L或严格等Recall性能。负结果仅约束本次冻结方案。',
            '', '## 产物','',
            '- [同批完整统计](baseline_comparison_v1/analysis_v1/summary.json)、[三指标CSV](baseline_comparison_v1/analysis_v1/metrics.csv)、[相对比较CSV](baseline_comparison_v1/analysis_v1/comparisons.csv)。',
            '- [线程与逐query复核](baseline_comparison_v1/analysis_v1/verification.json)、[判定门](baseline_comparison_v1/analysis_v1/gate.json)。',
            '- [Recall–QPS图](baseline_comparison_v1/analysis_v1/recall_qps.png)、[失败率图](baseline_comparison_v1/analysis_v1/failure_rates.png)。',
            '- [全部因素/单入口/exact结果](single_thread_v1/results/analysis_v1/summary.json)、[覆盖和路由损失诊断](single_thread_v1/results/analysis_v1/mechanism.json)。',
            '- [原方法协议](protocol.md)、[单线程修订](evaluation_single_thread_amendment.md)、[NSG比较修订](baseline_comparison_amendment.md)。','']
    report.write_text('\n'.join(lines))
    print(json.dumps(gate))


if __name__=='__main__':main()
