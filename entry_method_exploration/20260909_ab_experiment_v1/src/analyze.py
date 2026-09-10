#!/usr/bin/env python3
"""Measured, paired results only; no interpolation or oracle-as-method claims."""
import csv,json,hashlib,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT=Path(__file__).resolve().parents[1]
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];SEEDS=[20260828,20260829,20260830]
NAMES={DATASETS[0]:'WebVid',DATASETS[1]:'Yandex-IP'}

def dump(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def bootstrap_mean_discrete(values,scale,seed=20260909):
    """Exactly equivalent to query bootstrap for the mean of discrete differences.

    Each query's value already sums the three builds; builds are not independent
    queries. Sampling the empirical value histogram avoids 100M raw row indices.
    """
    unique,counts=np.unique(values,return_counts=True);rng=np.random.default_rng(seed)
    draws=rng.multinomial(len(values),counts/len(values),size=10000)
    means=(draws@unique)/(len(values)*scale)
    return {'mean':float(values.mean()/scale),'ci95':np.quantile(means,[.025,.975]).tolist(),
            'ci95_bonferroni4':np.quantile(means,[.05/8,1-.05/8]).tolist(),'bootstrap_queries':len(values),'replicates':10000}

def load():
    table={};verification=[]
    for split in ['calibration_check','audit','validation','heldout']:
        for ds in DATASETS:
            query_ref=None
            for seed in SEEDS:
                root=OUT/'results'/split/ds/f'seed{seed}';r=json.loads((root/'results.json').read_text())
                assert r['status']=='COMPLETE' and r['queries']==(1024 if split in ['calibration_check','audit'] else 10000)
                rows=np.fromfile(root/'row_ids.i64',dtype='int64')
                if query_ref is None:query_ref=rows
                else:assert np.array_equal(rows,query_ref),'query pairing across seeds lost'
                assert len(r['methods'])==28
                for metric in r['methods']:
                    cfg=metric['configuration'];name=cfg['family'];L=cfg['L'];n=r['queries'];folder=root/metric['name']
                    hits=np.fromfile(folder/'hits.u8',dtype='uint8');assert len(hits)==n and hits.max()<=10
                    assert int(hits.sum())==metric['total_hits'] and int((hits==0).sum())==metric['failed_queries']
                    assert metric['plain_count_parity_queries']==n
                    timing=metric['timings'];assert len(timing)==(3 if split in ['validation','heldout'] else 0)
                    table[split,ds,L,name,seed]={'metric':metric,'hits':hits,'folder':folder,'timings':timing}
                    verification.append({'split':split,'dataset':ds,'seed':seed,'L':L,'method':name,'queries':n,'status':'PASS'})
    return table,verification

def aggregate(table,split,ds,L,name):
    records=[table[split,ds,L,name,s] for s in SEEDS]
    hits=np.stack([r['hits'] for r in records]);metrics=[r['metric'] for r in records]
    qps=[[t['qps'] for t in r['timings']] for r in records]
    summary={'split':split,'dataset':ds,'L':L,'method':name,'queries_per_build':hits.shape[1],
             'recall':float(hits.mean()/10),'recall_build_std':float((hits.mean(1)/10).std(ddof=1)),
             'failure':float((hits==0).mean()),'failure_build_std':float((hits==0).mean(1).std(ddof=1)),
             'failed_queries_by_build':(hits==0).sum(1).astype(int).tolist(),
             'qps':float(np.mean(qps)) if qps[0] else None,'qps_all':qps,
             'qps_std':float(np.std(qps,ddof=1)) if qps[0] else None,
             'mean_route_ndc':float(np.mean([m['mean_route_ndc'] for m in metrics])),
             'mean_graph_ndc':float(np.mean([m['mean_graph_ndc'] for m in metrics])),
             'mean_total_ndc':float(np.mean([m['mean_total_ndc'] for m in metrics])),
             'fallback_by_build':[bool(m['configuration'].get('selected_fallback',False)) for m in metrics]}
    return summary,hits

def compare(table,split,ds,L,method,baseline):
    new,nh=aggregate(table,split,ds,L,method);old,oh=aggregate(table,split,ds,L,baseline)
    delta=nh.astype('int16')-oh.astype('int16')
    nf=nh==0;of=oh==0;rescued=(of&~nf).sum(1);harmed=(~of&nf).sum(1)
    assert np.array_equal(rescued-harmed,of.sum(1)-nf.sum(1))
    recall=bootstrap_mean_discrete(delta.sum(0),3*10/100)
    failure=bootstrap_mean_discrete(of.astype('int16').sum(0)-nf.astype('int16').sum(0),3/100)
    return {'split':split,'dataset':ds,'L':L,'method':method,'baseline':baseline,'new':new,'fast':old,
            'recall_gain_pp':(new['recall']-old['recall'])*100,'recall_relative_change_pct':(new['recall']/old['recall']-1)*100,
            'recall_gain_bootstrap_pp':recall,'failure_reduction_pp':(old['failure']-new['failure'])*100,
            'failure_relative_reduction_pct':(1-new['failure']/old['failure'])*100 if old['failure'] else None,
            'failure_reduction_bootstrap_pp':failure,
            'qps_change_pct':(new['qps']/old['qps']-1)*100 if new['qps'] is not None else None,
            'qps_change_pct_by_build':[(np.mean(a)/np.mean(b)-1)*100 for a,b in zip(new['qps_all'],old['qps_all'])] if new['qps'] is not None else [],
            'rescued_by_build':rescued.astype(int).tolist(),'newly_failed_by_build':harmed.astype(int).tolist(),
            'recall_improved_queries_by_build':(delta>0).sum(1).astype(int).tolist(),
            'recall_harmed_queries_by_build':(delta<0).sum(1).astype(int).tolist()}

def check_development(table):
    checks=[];pool=[];cal_differences=[]
    for ds in DATASETS:
        inp=OUT/'inputs'/ds;c=json.loads((inp/'runner_config.json').read_text());union=np.fromfile(c['hub_ids'],dtype='int32')
        for seed in SEEDS:
            sc=json.loads((inp/f'seed{seed}/config.json').read_text());cols=np.fromfile(sc['union_columns'],dtype='int32')
            for L in [64,128]:
                full=np.memmap(OUT/'labels'/ds/f'L{L}/hitcount.u8',dtype='uint8',mode='r',shape=(c['num_queries'],len(union)))
                costs=np.memmap(OUT/'labels'/ds/f'L{L}/ndc.u32',dtype='uint32',mode='r',shape=full.shape)
                for split,begin,end in [('calibration_check',20000,21024),('audit',21024,22048)]:
                    for key,record in table.items():
                        sp,dd,ll,name,ss=key
                        if (sp,dd,ll,ss)!=(split,ds,L,seed) or record['metric']['configuration']['k']!=1:continue
                        entries=np.fromfile(record['folder']/'entry_ids.i32',dtype='int32').reshape(-1,3)[:,0]
                        ec=np.searchsorted(union,entries);assert np.array_equal(union[ec],entries)
                        expected=full[np.arange(begin,end),ec]
                        assert np.array_equal(record['hits'],expected),'deployed action does not reproduce label hit count'
                        gn=np.fromfile(record['folder']/'graph_ndc.u32',dtype='uint32')
                        assert np.array_equal(gn,costs[np.arange(begin,end),ec]),'deployed action differs in kernel NDC'
                        checks.append({'dataset':ds,'seed':seed,'L':L,'split':split,'method':name,'rows':end-begin,'status':'PASS'})
                for family in ['w_only','mapping_only','joint','staged']:
                    sel=json.loads((OUT/'models'/ds/f'seed{seed}'/f'L{L}'/family/'selection.json').read_text())
                    actions=np.fromfile(sel['candidate']['mapping'],dtype='int32');action_cols=np.searchsorted(union,np.unique(actions))
                    h_oracle=full[21024:22048,cols].max(1)/10.
                    p_oracle=full[21024:22048,action_cols].max(1)/10.
                    exact=table['audit',ds,L,family+'_exact',seed]['hits']/10.
                    approx=table['audit',ds,L,family,seed]['hits']/10.
                    pool.append({'dataset':ds,'seed':seed,'L':L,'family':family,'active_actions':len(action_cols),
                                 'H_oracle':float(h_oracle.mean()),'P_oracle':float(p_oracle.mean()),
                                 'coverage_loss_pp':float((h_oracle-p_oracle).mean()*100),
                                 'exact_routing_loss_pp':float((p_oracle-exact).mean()*100),
                                 'approx_minus_exact_pp':float((approx-exact).mean()*100)})
                    training_cal=sel['after']['cal_hits'] if family=='staged' else sel['candidate']['metrics']['cal_hits']
                    native_cal=int(table['calibration_check',ds,L,family+'_exact',seed]['hits'].sum())
                    cal_differences.append({'dataset':ds,'seed':seed,'L':L,'family':family,'torch_cal_hits':training_cal,'native_cal_hits':native_cal,'difference_hits':native_cal-training_cal,
                                            'interpretation':'frozen model; float32 GEMM versus native SIMD/1-IP score arithmetic; no reselection'})
    return checks,pool,cal_differences

def main():
    dest=OUT/'results/analysis_v1';assert not dest.exists();dest.mkdir()
    table,verification=load();checks,pool,cal=check_development(table)
    dump(dest/'verification.json',{'status':'PASS','result_checks':verification,'label_replay_checks':checks,'calibration_compilation_differences':cal})
    dump(dest/'mechanism.json',pool)
    summaries=[];comparisons=[]
    families=['fast20k_1','fast20k_3','fast30k_1','fast30k_3','fast20k_exact1','w_only','w_only_exact','mapping_only','mapping_only_exact','joint','joint_exact','staged','staged_exact','joint_selected']
    for split in ['audit','validation','heldout']:
        for ds in DATASETS:
            for L in [64,128]:
                for family in families:summaries.append(aggregate(table,split,ds,L,family)[0])
                for method in ['joint','joint_selected']:
                    for baseline in ['fast30k_3','fast20k_3','fast20k_1','fast30k_1']:
                        comparisons.append(compare(table,split,ds,L,method,baseline))
    primary=[x for x in comparisons if x['split']=='heldout' and x['method']=='joint' and x['baseline']=='fast30k_3']
    mean_quality=all(x['recall_gain_pp']>=-1e-10 for x in primary)
    one_significant=any(x['recall_gain_bootstrap_pp']['ci95_bonferroni4'][0]>0 for x in primary)
    qps=all(x['qps_change_pct']>=0 for x in primary)
    gate={'status':'GO_WITHIN_FROZEN_FOUR_POINTS' if mean_quality and one_significant and qps else 'NO_GLOBAL_PARETO_GO',
          'primary_baseline':'Historical Fast30K direct3 with original default HNSW seed100, remeasured in current harness',
          'all_four_recall_nonnegative':mean_quality,'at_least_one_bonferroni4_significant_recall_gain':one_significant,'all_four_mean_qps_nondecreasing':qps,
          'no_iso_recall_interpolation':True,'primary_method':'joint candidate (cal-selected new checkpoint; no hidden baseline fallback)'}
    dump(dest/'gate.json',gate);dump(dest/'summary.json',{'gate':gate,'summaries':summaries,'comparisons':comparisons})
    fields=['split','dataset','L','method','baseline','recall_gain_pp','recall_relative_change_pct','qps_change_pct','failure_reduction_pp','failure_relative_reduction_pct']
    with (dest/'comparisons.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in comparisons)
    fields=['split','dataset','L','method','recall','failure','qps','qps_std','mean_route_ndc','mean_graph_ndc','mean_total_ndc']
    with (dest/'metrics.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in summaries)
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    styles={'fast30k_3':('Fast30K-3','s'),'fast20k_3':('Fast20K-3','^'),'fast20k_1':('Fast20K-1','v'),'joint':('A+B joint','o'),'joint_selected':('Calibration choice','x')}
    for ax,ds in zip(axes,DATASETS):
        for family,(label,marker) in styles.items():
            rows=[s for s in summaries if s['split']=='heldout' and s['dataset']==ds and s['method']==family]
            ax.plot([s['recall']*100 for s in rows],[s['qps'] for s in rows],marker=marker,label=label)
            for row in rows:
                if family in ['joint','fast30k_3']:ax.annotate('L'+str(row['L']),(row['recall']*100,row['qps']),xytext=(4,4),textcoords='offset points',fontsize=7)
        ax.set(title=NAMES[ds],xlabel='Recall@10 (%)',ylabel='End-to-end QPS');ax.grid(alpha=.25);ax.legend(fontsize=7)
    fig.suptitle('Held-out 10K; three builds x three plain wall repeats; lines connect measured points')
    fig.tight_layout();fig.savefig(dest/'recall_qps.png',dpi=180);fig.savefig(dest/'recall_qps.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4));x=np.arange(4);width=.25
    for j,fam in enumerate(['fast30k_3','fast20k_3','joint']):
        ys=[next(s['failure']*100 for s in summaries if s['split']=='heldout' and s['dataset']==ds and s['L']==L and s['method']==fam) for ds in DATASETS for L in [64,128]]
        ax.bar(x+(j-1)*width,ys,width,label=styles[fam][0])
    ax.set_xticks(x,[f'{NAMES[ds]} L{L}' for ds in DATASETS for L in [64,128]]);ax.set_ylabel('Failure rate: Recall@10 < 0.1 (%)');ax.legend();fig.tight_layout();fig.savefig(dest/'failure_rates.png',dpi=180);fig.savefig(dest/'failure_rates.pdf');plt.close(fig)
    def f(x,d=3):return '—' if x is None else f'{x:.{d}f}'
    lines=['# A+B 低秩槽位路由：完整实测报告','',f"总体判定：**{gate['status']}**。主表比较冻结的新联合候选与重新计时的历史 Fast30K direct3；候选即使校准劣于Fast仍完整报告。",'',
           '## Held-out10K 主结果','', '| 数据集 | L | Fast→A+B Recall@10 | ΔRecall pp | Fast→A+B QPS | ΔQPS | Fast→A+B失败率 | 失败率相对下降 |','|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in primary:
        a=r['fast'];b=r['new'];lines.append(f"| {NAMES[r['dataset']]} | {r['L']} | {f(a['recall']*100)}%→{f(b['recall']*100)}% | {r['recall_gain_pp']:+.3f} | {f(a['qps'],1)}→{f(b['qps'],1)} | {r['qps_change_pct']:+.2f}% | {f(a['failure']*100)}%→{f(b['failure']*100)}% | {f(r['failure_relative_reduction_pct'],2)}% |")
    lines+=['','正的失败率下降表示改善；负值表示失败增多。失败定义严格 `Recall@10<0.1`，命中1个不失败。比例相对各自Fast失败率，不能与Recall pp混用。','',
            '## 配对证据','', '| 数据集 | L | ΔRecall校正95% CI（pp） | 失败率下降（pp） | 被挽救query / 新增失败query（三构建分别） |','|---|---:|---|---:|---|']
    for r in primary:lines.append(f"| {NAMES[r['dataset']]} | {r['L']} | {r['recall_gain_bootstrap_pp']['ci95_bonferroni4']} | {r['failure_reduction_pp']:+.3f} | {r['rescued_by_build']} / {r['newly_failed_by_build']} |")
    lines+=['','query bootstrap先对同一query的三个构建差值求和，再重采样query（10000次）；四主点Bonferroni校正。它不估计新构建总体的不确定性，构建差异和9次wall原值另列。QPS为三构建各三次独立wall得到的QPS算术平均。','',
            '## 同训练量与因素对照','', '| 数据集 | L | 方法 | Recall@10 | QPS | 失败率 | route / graph NDC |','|---|---:|---|---:|---:|---:|---:|']
    for s in summaries:
        if s['split']=='heldout' and s['method'] in ['fast20k_1','fast20k_3','mapping_only','w_only','staged','joint','joint_selected']:
            lines.append(f"| {NAMES[s['dataset']]} | {s['L']} | {s['method']} | {s['recall']*100:.3f}% | {f(s['qps'],1)} | {s['failure']*100:.3f}% | {s['mean_route_ndc']:.1f} / {s['mean_graph_ndc']:.1f} |")
    lines+=['','`joint_selected` 是校准选择允许Fast fallback的策略；回退发生时使用原Fast1后端，不视为新算法提升。每构建fallback标记、全部exact对照、validation和audit结果见[完整JSON](results/analysis_v1/summary.json)。',
            '', '## 执行与限制','',
            '- 20K fit、1024 cal、1024 audit；cal/audit是历史开发池，仅对本次拟合隔离。三QGT独立构建，各模型只选择该构建H内的入口。validation10K和held-out10K均在全部模型冻结后开放。',
            '- rank8、rho0.5、无bias；原query不变、学习向量不归一化，离线折叠W，唯一slot label与真实ID映射分开；原冻结NSG/raw-IP/K10/L64或128不变。',
            '- 基准Fast20K与新方法共享构建seed；Fast30K恢复原默认HNSW seed100和direct1/3调用。历史运行的QPS未拼接到当前结果。',
            '- plain/count/重复结果一致，开发集每个单入口结果与完整标签hit和NDC逐query核验；native SIMD与训练GEMM的校准差值记录在[正确性报告](results/analysis_v1/verification.json)，未据此调整模型。',
            '- QPS来自独立plain full-batch wall，计入路由/映射/原图/正常输出，排除GT、计数、hash、JSON、装载和建图；方法换序，统一16线程。route-only/graph-only是独立诊断，不相加充当端到端时间。',
            '- 同L结果不等于严格isorecall。只测试L64/128两个点，不用连线或oracle推断未测预算的性能。不存在性能保证；负结果不外推所有A+B表示。',
            '', '## 产物','',
            '- [协议](protocol.md)、[配置](config.locked.json)、[输入与标签](inputs/complete.json)、[全标签核验](reviews/full_labels_verified.json)。',
            '- [逐点CSV](results/analysis_v1/metrics.csv)、[相对Fast比较CSV](results/analysis_v1/comparisons.csv)、[完整统计JSON](results/analysis_v1/summary.json)。',
            '- [Oracle覆盖/路由误差分解](results/analysis_v1/mechanism.json)、[正式门](results/analysis_v1/gate.json)。',
            '- [Recall–QPS图](results/analysis_v1/recall_qps.png)、[集合迷失图](results/analysis_v1/failure_rates.png)。','']
    (OUT/'report.md').write_text('\n'.join(lines))
    print(json.dumps(gate))

if __name__=='__main__':main()
