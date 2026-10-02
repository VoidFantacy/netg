from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));selection=read(O/'results/selection.json');cost=read(O/'results/cost.json')
names=['E61_missing','E62_score','E62_topology','E63_zero_mass','E61_sham','E63_sham'];labels=['Missing','Score only','Topology only','Zero-hit mass','Missing sham','Mass sham']
def p(ds,n,ph):return next(x for x in points if x['dataset']==ds and x['model']==n and x['phase']==ph)
fig,axes=plt.subplots(2,2,figsize=(13,7.8));table=[]
for row,(ds,label) in enumerate(zip(DS,['WebVid','Yandex'])):
    x=np.arange(len(names));base=int(p(ds,'baseline','aux7952')['failure_count'])
    for ph,off,color in [('half1',-.2,'#247b90'),('half2',.2,'#e49a35')]:
        vals=[int(p(ds,n,ph)['net_hits']) for n in names];bars=axes[row,0].bar(x+off,vals,.36,label=ph,color=color);axes[row,0].bar_label(bars,fmt='%+d',fontsize=8)
    vals=[int(p(ds,n,'aux7952')['failure_count'])-base for n in names];bars=axes[row,1].bar(x,vals,color=['#287d8e']*4+['#adb5bd']*2);axes[row,1].bar_label(bars,fmt='%+d',fontsize=9)
    for col,title in enumerate(['Net GT10 hits in each fixed half','Zero-hit count change (all 7,952)']):
        ax=axes[row,col];ax.set_xticks(x,labels,rotation=20,ha='right');ax.axhline(0,color='gray',lw=.7);ax.set_title(label+' — '+title);ax.margins(y=.2);ax.grid(axis='y',alpha=.15)
    for n in names:
        a=p(ds,n,'aux7952');halves=[p(ds,n,ph)['net_hits'] for ph in ['half1','half2']]
        table.append(f"| {label} | {n} | {float(a['delta_recall_pp']):+.4f} | {a['net_hits']} ({'/'.join(halves)}) | {base}→{a['failure_count']} | {a['rescued']}/{a['new_failures']} |")
axes[0,0].legend();fig.suptitle('E64: all frozen candidates on historical auxiliary development rows',fontsize=14)
fig.text(.5,.012,'Source router_train[2048:10000] • Both halves used for selection training • L128 / 1 thread • No QPS',ha='center',fontsize=10)
fig.tight_layout(rect=(0,.04,1,.95));(O/'figures').mkdir(exist_ok=True)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'auxiliary_results.{ext}',dpi=180)
report=['# E64 今日固定候选的扩大历史开发复核','',
'全部候选仍未过预锁辅助门，双集best_all保持原GT10。WebVid纯拓扑端点有净+38命中、两半均正的局部信号，但失败净增2；Yandex四个真实新端点净命中均负。E63训练池的局部正值没有被抹掉，扩大开发后的收益仍不足支持替换。','',
'每集冻结7个现有模型，在router_train[2048:10000]全部7952行上测L128；前后3976为预锁两半。baseline加E61遗漏、E62评分/拓扑、E63零命中质量及两个sham。没有改画像/图/参数/seed，旧E61–E63 cal门失败不回写；两个sham不参加推荐。', '',
'| 数据集 | 模型 | ΔRecall pp | 净hits (两半) | 零命中数 | 救回/新增失败 |','|---|---|---:|---:|---:|---:|']+table+['',
'规则要求总净命中正、两半各非负、失败数不增、totalNDC≤+1%。WebVid E62_topology通过前三项中的命中条件，但11救回伴随13新增失败；不能只汇报Recall改善。WebVid E63全池−2命中、两半+6/−8；Yandex E63−18命中、两半−23/+5，虽失败净减2，仍不满足Recall条件。Yandex E61/S分别−74/−78命中，两半均负。', '',
'诊断展示best_new按既定排序选为WebVid E62_topology、Yandex E63_zero_mass；这两个身份不表示过门或推荐。后续开发wall协议固定使用它们和全部基线，不依据测速改选；E34最终validation只在晚间最终冻结后比较。', '',
'这些7952行与本日P-fit20K、cal/audit2048在同源行身份互斥，但被Fast30K和早期研究使用；不能称全项目未观察。所有本阶段反馈用于辅助选择，属于训练信息。完整原22048行query/GT从原来源逐字恢复，source hash与图/W/mapping均核验。无最终validation/held-out访问。', '',
f"实际新增{cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW，14物理源图加载/复制、28 plain/count加载，0新小图构建/GT/梯度/QPS。两个完成native job共{cost['native_job_seconds']:.3f}秒。首次绑核竞态在exec前0查询停止，原111440预留保留；一次修正后总预留{cost['total_reserved_NSG']:,}，实际调用不含未执行预留。", '',
'首次prepare导入名错误0查询、首次taskset启动竞态0查询均保留原log。run_v2在子进程exec前CPU15绑核，native及控制器共同核验实际线程1/CPU15；两dataset串行，全部terminal实际exit之后分析。111328集合/mask、14图全bytes、224原kernelparity、full plain/count以及选择/失败守恒独立核验通过。', '',
'[协议](protocol.md) · [规则和选择](results/selection.json) · [42个指标行](results/points.csv) · [失败案例](results/failure_cases.csv) · [成本](results/cost.json) · [验收](reviews/verification.json) · [启动修正](launch_repair_amendment.md) · [图](figures/auxiliary_results.svg)']
(O/'report.md').write_text('\n'.join(report)+'\n');print('E64_REPORT_READY')
