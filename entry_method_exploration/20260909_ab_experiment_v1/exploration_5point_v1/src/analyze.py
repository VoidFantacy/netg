#!/usr/bin/env python3
import csv,json,hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RUN=Path(__file__).resolve().parents[1];OUT=RUN.parent
DATASETS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];LS=[64,128,256,400,800]
NAMES={DATASETS[0]:'WebVid',DATASETS[1]:'Yandex-IP'}
FAMILIES=['nsg_medoid','fast30k_3','joint'];LABELS={'nsg_medoid':'NSG','fast30k_3':'Fast','joint':'A+B'}
def dump(path,obj):Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    metrics=[];table={};verified=[];entry_checks=[]
    for ds in DATASETS:
        root=RUN/'results'/ds;result=json.loads((root/'results.json').read_text());c=json.loads((root/'config.json').read_text())
        assert result['status']=='COMPLETE' and result['queries']==2000 and result['threads']==1
        assert c['threads']==1 and len(result['methods'])==15 and result['timing_repeats']==1
        contract=json.loads((root/'thread_contract.json').read_text());assert contract['status']=='PASS' and contract['actual_openmp_threads']==1
        assert json.loads((root/'verification.json').read_text())['status']=='PASS'
        gt=np.fromfile(c['gt_file'],dtype='int64').reshape(2000,100)[:,:10]
        model_hashes=set();routes={}
        for m in result['methods']:
            family=m['family'];L=m['L'];assert family in FAMILIES and L in LS
            folder=root/m['name'];hits=np.fromfile(folder/'hits.u8',dtype='uint8');ids=np.fromfile(folder/'ids.i32',dtype='int32').reshape(2000,10)
            checked=(ids[:,:,None]==gt[:,None,:]).any(1).sum(1)
            assert np.array_equal(checked,hits) and int(hits.sum())==m['total_hits']
            assert int((hits==0).sum())==m['failed_queries'] and np.isclose(m['recall_at_10'],hits.mean()/10)
            assert m['warm_timed_parity_queries']==2000 and m['original_count_plain_checked_queries']==16
            assert m['end_to_end_seconds']>0 and np.isclose(m['qps'],2000/m['end_to_end_seconds'])
            if family=='joint':model_hashes.add((sha(m['configuration']['W']),sha(m['configuration']['mapping'])))
            raw=(folder/'entry_ids.i32').read_bytes()
            if family in routes:assert raw==routes[family], 'routing entry changed with L'
            else:routes[family]=raw
            record={'dataset':ds,'L':L,'method':family,'recall':m['recall_at_10'],'qps':m['qps'],
                    'failed_queries':m['failed_queries'],'failure_rate':m['failure_rate'],
                    'end_to_end_seconds':m['end_to_end_seconds'],'queries':2000,'threads':1,'timing_repeats':1}
            metrics.append(record);table[ds,L,family]=(record,hits)
            verified.append({'dataset':ds,'L':L,'method':family,'independent_GT_queries':2000,'status':'PASS'})
        assert len(model_hashes)==1
        entry_checks.append({'dataset':ds,'same_joint_model_for_five_L':True,'same_selected_entries_for_five_L':True,
                             'checked_queries_per_method':2000,'methods':FAMILIES,'status':'PASS'})
    comparisons=[]
    for ds in DATASETS:
        for L in LS:
            new,nh=table[ds,L,'joint']
            for baseline in ['fast30k_3','nsg_medoid']:
                old,oh=table[ds,L,baseline];nf=nh==0;of=oh==0
                rescued=int((of&~nf).sum());harmed=int((~of&nf).sum());assert rescued-harmed==old['failed_queries']-new['failed_queries']
                comparisons.append({'dataset':ds,'L':L,'baseline':baseline,'method':'joint',
                    'recall_gain_pp':(new['recall']-old['recall'])*100,
                    'qps_change_pct':(new['qps']/old['qps']-1)*100,
                    'failure_reduction_pp':(old['failure_rate']-new['failure_rate'])*100,
                    'failure_relative_reduction_pct':(1-new['failure_rate']/old['failure_rate'])*100 if old['failure_rate'] else None,
                    'rescued_queries':rescued,'newly_failed_queries':harmed,
                    'recall_improved_queries':int((nh>oh).sum()),'recall_harmed_queries':int((nh<oh).sum())})
    summary={'status':'EXPLORATION_COMPLETE','scope':'single seed, validation2000, one single-thread timing, one fixed joint model across five L',
             'metrics':metrics,'comparisons':comparisons,'routing_L_invariance':entry_checks,
             'formal_significance_or_stability_claim':False}
    dump(RUN/'results/summary.json',summary)
    dump(RUN/'reviews/final_verification.json',{'status':'PASS','metric_checks':verified,'entry_model_L_invariance':entry_checks,
        'total_method_points':30,'independent_GT_scored_query_outputs':60000,'actual_threads':1})
    for name,rows in [('metrics',metrics),('comparisons',comparisons)]:
        with (RUN/'results'/f'{name}.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    colors={'nsg_medoid':'#687580','fast30k_3':'#2675bd','joint':'#db6338'}
    fig,axes=plt.subplots(1,2,figsize=(11,4.2))
    for ax,ds in zip(axes,DATASETS):
        for family in FAMILIES:
            values=[table[ds,L,family][0] for L in LS]
            ax.plot([v['recall']*100 for v in values],[v['qps'] for v in values],marker='o',label=LABELS[family],color=colors[family])
            if family=='joint':
                for v in values:ax.annotate(str(v['L']),(v['recall']*100,v['qps']),xytext=(4,4),textcoords='offset points',fontsize=8)
        ax.set(title=NAMES[ds],xlabel='Recall@10 (%)',ylabel='Single-thread end-to-end QPS');ax.grid(alpha=.25);ax.legend()
    fig.suptitle('Exploration: 2K validation queries; one fixed router; L = 64, 128, 256, 400, 800')
    fig.tight_layout();fig.savefig(RUN/'results/recall_qps.png',dpi=180);fig.savefig(RUN/'results/recall_qps.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for ax,ds in zip(axes,DATASETS):
        for family in FAMILIES:ax.plot(LS,[table[ds,L,family][0]['failure_rate']*100 for L in LS],marker='o',label=LABELS[family],color=colors[family])
        ax.set(title=NAMES[ds],xlabel='Search L',ylabel='Failure rate: Recall@10 < 0.1 (%)');ax.set_xticks(LS);ax.grid(alpha=.25);ax.legend()
    fig.tight_layout();fig.savefig(RUN/'results/failure_rate.png',dpi=180);fig.savefig(RUN/'results/failure_rate.pdf');plt.close(fig)
    lines=['# 五点单线程探索结果','',
        '两个数据集各2000条validation，QGT seed20260828；NSG、Fast30K direct3及同一个冻结A+B入口选择模型。A+B五点使用完全相同的W/mapping，训练标签曾由L128搜索产生；推理不接收L。五个L下逐query入口完全相同，只有图搜索L变化。','',
        '| 数据集 | L | 方法 | Recall@10 | QPS | 失败数/2000 | 失败率 |','|---|---:|---|---:|---:|---:|---:|']
    for ds in DATASETS:
        for L in LS:
            for family in FAMILIES:
                x=table[ds,L,family][0];lines.append(f"| {NAMES[ds]} | {L} | {LABELS[family]} | {x['recall']*100:.3f}% | {x['qps']:.1f} | {x['failed_queries']} | {x['failure_rate']*100:.3f}% |")
    lines+=['','## 相对两种基线','',
        '| 数据集 | L | 基线 | ΔRecall pp | ΔQPS | 失败率下降 pp | 失败率相对下降 | 挽救 / 新增失败 |','|---|---:|---|---:|---:|---:|---:|---|']
    for x in comparisons:
        relative='—' if x['failure_relative_reduction_pct'] is None else f"{x['failure_relative_reduction_pct']:+.2f}%"
        lines.append(f"| {NAMES[x['dataset']]} | {x['L']} | {LABELS[x['baseline']]} | {x['recall_gain_pp']:+.3f} | {x['qps_change_pct']:+.2f}% | {x['failure_reduction_pp']:+.3f} | {relative} | {x['rescued_queries']} / {x['newly_failed_queries']} |")
    lines+=['','失败严格Recall@10<0.1，即GT10零命中；命中1个不失败。正的失败率下降表示改善，负数表示失败增多。',
        '', '## 范围与验收','',
        '- 每点只有一次完整warmup和一次2000query端到端计时；单线程并检查OpenMP/BLAS/MKL。没有route-only/graph-only计时、额外种子、消融或held-out。',
        '- 30个方法点共120000次warm/timed图搜索，另有960次小样本原kernel比较调用；全部warm/timed输出和16条/点独立原kernel的ID、距离bits一致，计数在timer外。',
        '- 三方法每条query的入口在五个L下均保持一致；独立GT评分复核60000个query输出通过。L控制后续候选池，不是入口模型输入。',
        '- Fast为历史30K画像，A+B基于20K画像与20K真实搜索监督；本表比较用户要求的现有基线，不称同训练成本。',
        '- 当前是validation2000、单seed、单次wall的探索结果，QPS小幅差异需要重复计时确认；未作正式显著性或跨构建稳定性声明，不插值推断未测预算。',
        '', '## 文件','',
        '- [原始指标CSV](results/metrics.csv)、[相对变化CSV](results/comparisons.csv)、[完整JSON](results/summary.json)。',
        '- [Recall–QPS](results/recall_qps.png)、[失败率](results/failure_rate.png)、[正确性与入口一致性](reviews/final_verification.json)。',
        '- [协议](protocol.md)、[输入/模型身份](inputs/manifest.json)、[状态](state.json)。','']
    (RUN/'report.md').write_text('\n'.join(lines))
    print(json.dumps({'status':'EXPLORATION_COMPLETE','points':len(metrics),'same_router_across_L':True}))

if __name__=='__main__':main()
