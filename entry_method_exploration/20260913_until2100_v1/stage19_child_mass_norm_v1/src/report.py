from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');retain=read(O/'results/gain_retention.json');v=read(O/'reviews/verification.json')
order=[('mass10','baseline10'),('mass10','compact10'),('mass10','uniform10'),('uniform10','compact10')];labels=['Mass norm − P','Mass norm − compact','Mass norm − uniform','Uniform norm − compact']
fig,axes=plt.subplots(2,3,figsize=(12,7),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[next(x for x in rows if x['dataset']==ds and x['candidate']==a and x['reference']==b and x['split']=='all') for a,b in order]
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Zero-hit count change'),('route_NDC_change_pct','Routing distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(4),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(4),labels if j==0 else ['']*4);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E78 · Child-mass norm weighting at a fixed compact graph\n7,952 historical auxiliary queries/dataset · mass versus matched uniform attenuation · no QPS',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('mass_norm.'+ext),dpi=150)
plt.close(fig)
lines=['# E78 固定图子质量范数权重','', '主候选对子画像乘rho^(1/d)，rho来自原P-fit子质量占比，不再单位化；P首槽不动。统一对照乘exp(mean_child(log rho)/d)，平均log缩放相同。两者原方向、slot/真实映射、完整compact图邻接/层级/入口保持；只在新图文件安装向量字节，0构图、无新增在线计算。','', '| 数据 | 候选 / 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for a,b in order:
  rr=[x for x in rows if x['dataset']==ds and x['candidate']==a and x['reference']==b];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {a}/{b} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines+=['','主候选预锁门：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'。对P/C要求全量正、两半非负/失败不增；对uniform要求全量与两半非负/失败不增。'+('至少一集通过，允许独立E79五L五轮完整wall。' if gate['wall_measurement_allowed'] else '无一集通过，停止此范数权重版本，不追加其wall，不改选uniform或扫指数。')+' 旧E73/E74 Yandex局部信号与E75/E77原停止状态保持，不升级为默认或性能GO。','', '旧收益保留与新损伤均按逐query净命中正负部分解，不是GT成员实际新增/丢失计数：']
for r in retain:
 if r['candidate']=='mass10':lines.append(f"- {'WebVid' if r['dataset']==DS[0] else 'Yandex'}：保留旧正命中{r['retained_old_gain']}/{r['old_gain']}，丢失{r['forgone_old_gain']}，另生正命中{r['new_gain']}；避免旧损失{r['avoided_old_loss']}，新增/放大损失{r['new_or_amplified_loss']}，最终总损失{r['new_total_loss']}（旧{r['old_loss']}）。")
lines+=['','本乘法权重不是旧E10加log(rho)/d的等价变换，也不是校准概率；1/d只是固定小尺度设计。正内积分数下降、负分数向0靠近，不保证三入口/NSG单调；原底层raw-IP/NSG未改变。float32舍入会有极小方向数值差，不把它称精确位相同方向。','','实际129536 NSG/129280 HNSW、0build/4向量安装/0新合成ANN/0新GT/梯度，evaluator同SHA引用、编译0。'+f"权重构造{cost['profile_construction_seconds']:.3f}s、向量安装{cost['vector_install_seconds']:.3f}s、四native {cost['native_job_seconds']:.3f}s。继承E66画像训练30.286s及早期GT成本未重测；计数操作wall不能当QPS，本阶段QPS点0。",'',f"独立{v['set_scored_rows']}返回集合/mask、{v['independent_scalar_rows']}逐行set评分；31808旧P/C全字段恢复、256原kernel、全部plain/count/7slot/图W/labels及非向量bytes保持通过。rho范围/统一平均log缩放、逐行标量导出bytes和P原字节验收通过；4种非法shape/NaN/rho实际零查询拒绝。{v['same_triple_return_rows']}主候选相同三入口返回行恢复。",'', 'aux7952及两半均历史暴露，选择反馈计训练；P-fit含旧train/monitor，cal/audit已观察，E34最终与held-out未打开。查询串行CPU15/实际进程及数值库1线程，两个数据集工具terminal0后分析。strict failure=GT10零命中，aligned返回/源行及全部成员得失保存。整日目标未完成。','','[协议](protocol.md) · [配对](results/paired.csv) · [失败查询](results/failures.csv) · [收益保留](results/gain_retention.json) · [权重/安装](results/construction.json) · [成本](results/cost.json) · [图](figures/mass_norm.png) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E78_REPORT_READY')
