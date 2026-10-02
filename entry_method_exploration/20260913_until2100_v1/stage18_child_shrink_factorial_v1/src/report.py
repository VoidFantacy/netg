from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');interaction=read(O/'results/interactions.json');v=read(O/'reviews/verification.json')
fig,axes=plt.subplots(2,3,figsize=(13,7),constrained_layout=True)
order=[('shrink10','baseline10'),('shrink10','compact10'),('score10','compact10'),('topology10','compact10')];labels=['A (shrink+rebuild) − P','A (shrink+rebuild) − C','S (score only) − C','T (topology only) − C']
for di,ds in enumerate(DS):
 rr=[next(x for x in rows if x['dataset']==ds and x['candidate']==a and x['reference']==b and x['split']=='all') for a,b in order]
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Zero-hit count change'),('route_NDC_change_pct','Routing distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(4),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(4),labels if j==0 else ['']*4);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E77 · Half parent-child shrinkage, with score/topology controls\n7,952 historical auxiliary queries/dataset · A is fixed candidate; S/T diagnostic · no QPS',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('shrink_factorial.'+ext),dpi=150)
plt.close(fig)
lines=['# E77 子画像固定半收缩与评分/构图四格','', '每个子画像改为unit(P+U)，原P首槽逐字保持，alpha固定一半、原物理槽/映射/ef10不变。C为E73 compact；A为新评分Ws普通重建Gs；S仅换评分、T仅换构图。只有A是本阶段预指定新方法，S/T用于解释，不按反馈改选。','', '| 数据 | 候选 / 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for a,b in [('shrink10','baseline10'),('shrink10','compact10'),('score10','baseline10'),('score10','compact10'),('topology10','baseline10'),('topology10','compact10')]:
  rr=[x for x in rows if x['dataset']==ds and x['candidate']==a and x['reference']==b];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {a}/{b} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines+=['','A预锁接续门：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'；要求对P和C全量净命中正、固定两半非负、零命中不增。'+('至少一集通过，允许独立E78完整同批wall，并保留另一集原样迁移对照。' if gate['wall_measurement_allowed'] else '无一集通过，停止A本版本，不追加其wall，不改选S/T或扫alpha/seed。')+' 旧E73/E74 Yandex局部信号、E75失败和E76关联边界均保留，尚不替换默认。','']
for r in interaction:lines.append(f"{'WebVid' if r['dataset']==DS[0] else 'Yandex'}：评分主效应Σ(S−C)={r['score_main_sum']:+d}，构图主效应Σ(T−C)={r['topology_main_sum']:+d}，交互Σ(A−S−T+C)={r['interaction_sum']:+d}，合计A−C={r['full_delta']:+d}；{r['nonzero_interaction_queries']}条query有非零命中交互。效应以完整图配置为干预，不拆成单画像/单边因果信用。")
lines+=['','E76不支持低ESS普遍导致损伤，因此本轮不按低ESS删模式。收缩作用于GT10同hub子方向且保留原P，与旧E26 GT1/GT10单画像插值不同；收缩本身不是创新，E26十点九个Recall损伤保留。球面拉回父P不保证分数或三入口单调，评分与图作用必须看真实结果。','',f"实际{cost['NSG']} NSG/{cost['HNSW']} HNSW，2普通小图build、4向量安装，0新合成ANN/梯度/GT。同SHA evaluator和builder复用，编译0；两图build {cost['micro_graph_build_seconds']:.3f}s，四native总{cost['native_job_seconds']:.3f}s。画像构造用时见construction.json；向量安装独立耗时未记录为null，不能记零。继承E66画像训练30.286s与早期GT成本未重测。此阶段计数操作wall不是QPS，新增QPS点0。",'',f"独立{v['set_scored_rows']}返回集合/mask、{v['independent_scalar_rows']}逐行set评分，31808旧P/C完整字节恢复、320原kernel、全部plain/count/7slot距离与真实映射通过。四格层级/入口相同，交叉图每个非向量字节保持源图；画像float64构造/逐行标量参考、P逐字保持和全部图布局W/label/邻接均验收。{v['same_triple_return_rows']}相同三入口行结果保持。逐query交互及GT成员净值恒等式通过。",'', '所有query源router_train[2048:10000]历史aux7952与固定3976两半，选择反馈计训练。fit含旧train/monitor、cal/audit已暴露；E34最终与held-out未打开。CPU15/实际进程与数值库1线程、方法和数据集串行，双集工具terminal0后评分；strict failure=GT10零命中。全部旧字节/新版本保留，整日21:00目标未完成。','','[协议](protocol.md) · [全部配对](results/paired.csv) · [原值](results/points.csv) · [失败查询](results/failures.csv) · [四格交互](results/interactions.json) · [构造](results/construction.json) · [成本](results/cost.json) · [图](figures/shrink_factorial.png) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E77_REPORT_READY')
