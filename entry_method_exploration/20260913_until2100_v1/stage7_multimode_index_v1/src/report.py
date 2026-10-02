from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();resources();rows=list(csv.DictReader((O/'results/points.csv').open()));pairs=list(csv.DictReader((O/'results/paired.csv').open()));sel=read(O/'results/selection.json')['datasets'];build=read(O/'results/build.json');v=read(O/'reviews/verification.json')
fig,axes=plt.subplots(2,3,figsize=(13,7.6),layout='constrained');colors=['#495566','#3388c4','#e06a35'];models=['baseline','duplicate3P','mode3P']
for i,ds in enumerate(DS):
    for j,(metric,title,scale) in enumerate([('recall','Recall@10 (%)',100),('failure_rate','Zero-hit failure rate (%)',100),('total_ndc','Total distance evaluations',1)]):
        ax=axes[i,j]
        for k,m in enumerate(models):
            vals=[float(next(r for r in rows if r['dataset']==ds and r['model']==m and r['split']==s)[metric])*scale for s in ['fit','aux']]
            ax.bar(np.arange(2)+(k-1)*.24,vals,.23,color=colors[k],label=m)
            for x,y in zip(np.arange(2)+(k-1)*.24,vals):ax.text(x,y,f'{y:.2f}' if j<2 else f'{y:.0f}',ha='center',va='bottom',fontsize=8)
        ax.set_xticks([0,1],['Fit20K','Aux7952']);ax.set_ylabel(title);ax.set_title(('WebVid' if i==0 else 'Yandex')+' | L128');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        if i==0 and j==0:ax.legend(fontsize=8,loc='lower right')
fig.suptitle('E66: one index, three profiles per real entry\nHistorical training / auxiliary selection feedback; count diagnostics, no QPS',fontsize=13)
(O/'figures').mkdir(exist_ok=True)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('development.'+ext),dpi=170)
plt.close(fig)
lines=['# E66 单个小索引的多画像开发结果','', '固定真实H，每hub保留原P和两份加权GT10 query模态；三slot一真实hub。一次HNSW取7slot，按距离/slot序去重为3真实入口，再执行原NSG。duplicate3P为同容量重复P控制；两模式的随机分组作用未隔离。所有新模型及门均在查询前冻结。','', '| 数据集 | 合格双模态 / H | fit净命中 | aux净命中 | aux两半 | aux失败净增 | aux相对duplicate净命中 | 开发门 |','|---|---:|---:|---:|---|---:|---:|---|']
for b in build['datasets']:
    ds=b['dataset'];s=sel[ds];lines.append(f"| {ds} | {b['eligible_two_modes']}/{b['total_hubs']} | {s['fit_net_hits']:+d} | {s['aux_net_hits']:+d} | {s['aux_halves']} | {s['aux_failure_net_change']:+d} | {s['aux_net_vs_duplicate']:+d} | {'PASS' if s['passed'] else 'FAIL'} |")
lines+=['','此门是开发质量/成本信号，未测完整wall，不能由同L Recall或NDC宣称性能改进。两个集合均历史暴露，aux7952全部属于辅助选型训练反馈；fit包含旧train/monitor，基础Fast30K和旧E10亦使用这些源行。E34最终validation及held-out未进入本阶段。','', '| 数据集 / 集合 / 比较 | ΔRecall pp | 成员找回 / 丢失 | 失败救回 / 新增 | 入口变化数 | 总NDC变化 |','|---|---:|---:|---:|---:|---:|']
for p in pairs:
    if p['split'] in ['fit','aux']:
        lines.append(f"| {p['dataset']} / {p['split']} / {p['model']}−{p['reference']} | {float(p['recall_change_pp']):+.4f} | {p['member_gain']} / {p['member_loss']} | {p['rescued']} / {p['new_failures']} | {p['changed_queries']} | {float(p['total_ndc_change_pct']):+.3f}% |")
lines+=['','成员找回/丢失按GT10 mask集合计算；逐query净命中正部/负部另存paired表，两者净值相同但不混用。失败严格hits=0；原命中0..10的分组受上下界限制，不作为在线可预测收益。全部失败转换按源namespace行号及三入口保存。','',f"实际新增 {v['new_NSG']} NSG、{v['new_HNSW']} HNSW；4个新3H小图构建，2个baseline源图加载、12个后续物理图加载及18次count重载。合成另1小图/15 HNSW/0NSG。画像训练时间 {sum(b['seconds'] for b in build['datasets']):.3f}s，原生进程操作时间 {sum(j['seconds'] for j in v['jobs']):.3f}s（含加载/计数/I/O，不是QPS）。无新GT/梯度更新。",'',f"独立集合评分 {v['independent_query_sets']} 条开发返回，{v['baseline_recovered_queries']} 条baseline恢复；另768预检返回及288原kernelparity。所有7slot去重、图坐标/label/邻接、plain/count bits和CPU15实际单线程通过。父/子质量与ESS、raw prior守恒及7个固定父hub/集的20轮独立重放通过。",'', '[开发图](figures/development.png) · [全部指标](results/points.csv) · [配对](results/paired.csv) · [失败query](results/failure_cases.csv) · [11组原命中分析](results/cohorts.csv) · [冻结门](results/selection.json) · [协议](protocol.md) · [验收](reviews/verification.json)','', '本阶段完成不代表整日21:00目标完成；需要后续完整开发wall与晚间冻结后的最终同批对照。无开发门时停止该容量/阈值/seed版本，保留局部正负，不扫模式数找阳性。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('REPORT_WRITTEN',flush=True)
