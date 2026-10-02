"""Static, shareable figures and a measured-results report; no acceptance tuning."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CURVE_NAMES=['GT10','Single1','BestFixed','GraphCost','GraphRecall','RandomCost']
SHORT={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}

def plot():
    rows=read(RUN/'results/metrics.json');pairs=read(RUN/'results/paired.json');p=RUN/'figures';p.mkdir(exist_ok=True)
    figures=[];colors=dict(zip(CURVE_NAMES,['#222222','#8c6d31','#9467bd','#d62728','#1f77b4','#2ca02c']))
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for di,ds in enumerate(LOCK['datasets']):
        for ki,K in enumerate((1,100)):
            ax=axes[di,ki]
            for name in CURVE_NAMES:
                a=sorted([r for r in rows if r['dataset']==ds and r['K']==K and r['method']==name],key=lambda r:r['L'])
                assert len(a)==5
                y=np.array([r['qps'] for r in a]);lo=y-np.array([r['qps_min'] for r in a]);hi=np.array([r['qps_max'] for r in a])-y
                ax.errorbar([r['recall_pct'] for r in a],y,yerr=[lo,hi],marker='o',markersize=4,label=name,color=colors[name],linewidth=1.3,capsize=2)
            ax.set(title=f'{SHORT[ds]} / Recall@{K}',xlabel='Recall (%)',ylabel='Queries per second');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Frozen L128 policy across five search budgets; CPU15, one thread\nBars show the range of three complete wall-time rounds',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(p/f'recall_qps.{ext}',dpi=160)
    plt.close(fig);figures.append('recall_qps')
    names=['GraphCost','GraphRecall','RandomCost','GraphLinearCost','RawLinearCost','ShuffledCost','Single1','BestFixed','FeatureDefault','NSG']
    fig,axes=plt.subplots(2,2,figsize=(13,9),layout='constrained')
    for di,ds in enumerate(LOCK['datasets']):
        for ki,K in enumerate((1,100)):
            ax=axes[di,ki]
            a=[next(r for r in pairs if r['dataset']==ds and r['method']==name and r['reference']=='GT10' and r['K']==K and r['L']==128) for name in names]
            x=np.array([r['delta_recall_pp'] for r in a]);lo=np.array([r['bootstrap']['ci_pp'][0] for r in a]);hi=np.array([r['bootstrap']['ci_pp'][1] for r in a])
            for j,name in enumerate(names):
                color='#d62728' if name=='GraphCost' else '#6b7280';ax.plot([lo[j],hi[j]],[j,j],color=color);ax.scatter([x[j]],[j],color=color,s=25)
            ax.axvline(0,color='black',linewidth=.8);ax.set_yticks(np.arange(len(names)),names,fontsize=8);ax.invert_yaxis()
            ax.set(title=f'{SHORT[ds]} / Recall@{K}',xlabel='Recall change versus GT10 (percentage points)');ax.grid(axis='x',alpha=.2)
    fig.suptitle('L128 paired query changes; 98.75% bootstrap intervals\nOnly four GraphCost-versus-GT10 comparisons are primary hypotheses',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(p/f'paired_recall.{ext}',dpi=160)
    plt.close(fig);figures.append('paired_recall')
    names=['GraphCost','GraphRecall','RandomCost','GraphLinearCost','RawLinearCost','ShuffledCost']
    fig,axes=plt.subplots(2,2,figsize=(14,8),layout='constrained')
    for di,ds in enumerate(LOCK['datasets']):
        training=read(RUN/'models'/ds/'training_report.json')['methods']
        for ki,K in enumerate((1,100)):
            ax=axes[di,ki];x=np.arange(len(names))
            fit=[training[name]['training'][str(K)]['recall_gain']*100 for name in names]
            cv=[np.mean(training[name]['cv'][str(training[name]['alpha'])]['r_gains'][ki::2])*100 for name in names]
            accept=[next(r['delta_recall_pp'] for r in pairs if r['dataset']==ds and r['method']==name and r['reference']=='GT10' and r['K']==K and r['L']==128) for name in names]
            for offset,v,label in [(-.24,fit,'Fit'),(0,cv,'Out-of-fold'),(.24,accept,'Acceptance')]:ax.bar(x+offset,v,.24,label=label)
            ax.axhline(0,color='black',linewidth=.8);ax.set_xticks(x,names,rotation=25,ha='right',fontsize=8)
            ax.set(title=f'{SHORT[ds]} / Recall@{K}',ylabel='Recall change vs GT10 (pp)');ax.legend(fontsize=8);ax.grid(axis='y',alpha=.2)
    fig.suptitle('Fit, cross-validation and historically exposed development acceptance\nAll phases use actual selected-action recall',fontsize=11)
    for ext in ('png','pdf'):fig.savefig(p/f'generalization.{ext}',dpi=160)
    plt.close(fig);figures.append('generalization')
    dump(RUN/'reviews/figure_manifest.json',dict(status='GENERATED_REQUIRES_VISUAL_REVIEW',files=[ident(p/f'{name}.{ext}') for name in figures for ext in ('png','pdf')],
        data_files=[ident(RUN/'results/metrics.json'),ident(RUN/'results/paired.json')]))

def write_report():
    evidence=read(RUN/'results/evidence.json');cost=read(RUN/'reviews/cost_ledger.json');metrics=read(RUN/'results/metrics.json')
    audit=read(RUN/'reviews/independent_final_audit.json');assert audit['status']=='PASS'
    lines=['# E118：共享比较方向入口预测实验报告','',
        '本版检验从真实搜索比较方向提取查询特征、预测全部现有单入口相对GT10三入口收益。底图、画像、小图、主搜索、展开和停止保持；默认仍Web GT10-soft-t1 / Yandex GT10-hard，生产E99。',
        '', '## 实际完成与主要结果','',
        '两数据集各2048方向发现、4096拟合、4096接受查询。角色互斥，但均为历史曝光开发资料且原GT10画像已使用；接受查询与E117相同，本次接受不是全新盲测。旧GT10/Single1返回恢复是正确性检查，不增加独立query或构成新独立复现。完成11方法的实际K1/K100/L128，以及六方法五预算曲线，共140点、420次完整单线程wall。K1预算64/128/256/400/800，K100预算100/128/256/400/800；模型只在L128训练，其余为冻结策略的预算迁移。','',
        '| 数据 | 指标 | GraphCost−GT10 召回变化(pp) | 98.75%配对区间 | QPS变化 | 零命中救回/新增 |','|---|---|---:|---|---:|---:|']
    for row in evidence['primary']:
        lo,hi=row['bootstrap']['ci_pp'];lines.append(f"| {SHORT[row['dataset']]} | R@{row['K']} | {row['delta_recall_pp']:+.6f} | [{lo:+.6f}, {hi:+.6f}] | {row['delta_qps_pct']:+.3f}% | {row['rescued_zero']}/{row['new_zero']} |")
    lines+=['','上表为L128主比较；QPS是三轮N/wall均值，原始每轮和N/平均wall均保留。速度轮次不是独立query样本，区间跨零表示未确认，不表示等效。全部方法及控制见[完整指标CSV](results/metrics.csv)、[配对结果](results/paired.json)。','',
        '![完整五预算Recall-QPS](figures/recall_qps.png)','',
        '![同监督与固定控制](figures/paired_recall.png)','',
        '## 方法和监督','',
        '比较超平面、方向近似的margin充分条件、有限加性表示及预测误差到regret的推导见[方法与理论边界](method.md)。这些是条件论证，不作为真实有效性证明。',
        '从独立方向角色的真实比较节点对构造单位base差向量；每query至多64个比较、总权重1。正反方向等价，固定32组projective spherical k-means和20轮迭代。单位query对32方向投影，正负ReLU共64维。全H单入口与原GT10三入口均有真实R1/R100和两K各三重复时间标签。',
        '以同query原GT10为基准，预测召回变化和图搜索时间变化；GraphCost采用ΔR−0.1ΔT/Tref，最大预测收益不为正时沿用GT10。训练为标准化多输出ridge，fit内固定四折从五个alpha选择；折内标准化/Tref、置换和拟合均只用折内训练数据。模型/方向/固定动作全部先于接受冻结。',
        'GraphRecall去掉时间项；RandomCost使用同容量随机方向；GraphLinearCost只用图方向线性投影；RawLinearCost使用完整单位query；ShuffledCost在训练折内整行置换响应。GT10、实际画像Single1、fit冻结BestFixed、NSG和计算全部新增特征后仍用GT10的FeatureDefault提供控制。在线每query只执行一次原NSG，全部路由/投影/全H评分/搜索/输出计入正式wall。','',
        '## 拟合、泛化与方向诊断','',
        '![训练与迁移](figures/generalization.png)','',
        '| 数据 | 方向样本数 | 聚类方向相似度中位数 | 比较符号近似一致率 | 聚类耗时(s) |','|---|---:|---:|---:|---:|']
    for ds in LOCK['datasets']:
        z=read(RUN/'reviews'/f'clustering_{ds}.json');lines.append(f"| {SHORT[ds]} | {z['samples']} | {z['angular_cosine_quantiles'][2]:.4f} | {z['weighted_comparison_sign_agreement']*100:.2f}% | {z['seconds']:.2f} |")
    lines+=['','方向相似度和符号近似只是诊断，未用阈值中止训练或选择模型。各模型逐头fit/CV误差、截距基线误差、所选正则、决策收益及全H训练oracle保存在模型training_report。接受oracle仅汇总模型动作域内的已测策略，是该动作域余量的下界；固定NSG入口未必在H内，因此从此oracle排除，仍保留为性能控制。没有把未知入口或时间填成真实标签。','',
        '## 完整成本与实验错误检查','',
        f"实际NSG调用{cost['NSG_calls']:,}次、GT10小图路由{cost['router_calls']:,}次；原生作业含加载/标签/审计/评测共{cost['native_job_seconds']/3600:.3f}小时，ridge训练{cost['training_seconds']:.2f}秒、方向聚类{cost['clustering_seconds']:.2f}秒，编译{cost['compile_seconds']:.2f}秒单列。最大采样RSS {cost['max_observed_rss_bytes']/1024**3:.3f}GiB，当前新产物{cost['artifact_bytes']/1024**3:.3f}GiB。离线用时不代表在线QPS。0新GT、底图、小图或K10测试。",'',
        '必须区分实现错误与方法问题：合成已知响应及独立最小二乘、分支符号/方向等价、原生前向/近tie、trace与原核完整bit/NDC、全H两K重复返回、mask/popcount/真实GT评分、所选fit动作返回hash回放、接受GT10与Single1恢复旧输出、源/model冻结及CPU15实际线程1均有检查。时间重复差异与方向噪声保留为诊断，不能用负面均值替代这些检查。',
        '[独立完成审计](reviews/independent_final_audit.json) · [调用和成本账本](reviews/cost_ledger.json) · [模型冻结](reviews/models_frozen.json) · [实现口径](reviews/implementation_scope.md) · [分析口径](reviews/analysis_contract.md)','',
        '## 结论状态','',
        '自动分析只汇总证据，不以启动成功或某个单点替代研究结论。最终判断需核对图表、同监督控制、强固定控制、配对区间和[匹配Recall的最快实测点](results/matched_recall.csv)。稀疏五预算不插值、没有按接受结果重训。当前默认保持，完成后的具体取舍另见decision.md。','']
    (RUN/'report.md').write_text('\n'.join(lines))
    dump(RUN/'reviews/report_generated.json',dict(status='GENERATED_REQUIRES_REVIEW',report=ident(RUN/'report.md')))

if __name__=='__main__':os.sched_setaffinity(0,{15});plot();write_report()
