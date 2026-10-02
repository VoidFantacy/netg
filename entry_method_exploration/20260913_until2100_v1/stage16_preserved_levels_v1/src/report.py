from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');levels=read(O/'results/levels.json')
fig,axes=plt.subplots(2,3,figsize=(12,6),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[x for x in rows if x['dataset']==ds and x['split']=='all']
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Zero-hit count change'),('route_NDC_change_pct','Routing distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(2),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(2),['Preserved levels − P10','Preserved levels − compact10'] if j==0 else ['']*2);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E75 · Keep original random levels while removing duplicate profiles\n7,952 historical auxiliary queries/dataset · fixed ef10 · counted work, no QPS',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('preserved_levels.'+ext),dpi=160)
plt.close(fig)
lines=['# E75 精简画像保留原随机层级','', '2026-09-13，第6串行会话。唯一改变是精简时按原slot消耗随机流，保留原节点层级；画像、紧凑插入顺序、种子、ef10与7slot去重3真实入口均固定。Web1771/Y2067画像，真实H815/821、原NSG/raw-IP保持。','', '| 数据 | 新图对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for ref in ['baseline10','compact10']:
  rr=[x for x in rows if x['dataset']==ds and x['reference']==ref];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {ref} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines+=['','预锁接续门：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'。要求同时胜P与compact、两半非负且零命中失败不增。'+('至少一集通过，允许独立E76完整wall；另一集同配置只作迁移对照。' if gate['wall_measurement_allowed'] else '无一集通过，停止本层级控制，不新增其完整wall或扫seed/ef。')+' 原E73/E74局部信号及全部旧门保持，不替换默认，不由NDC/同LRecall宣称性能改善。','']
for r in levels:lines.append(f"{'WebVid' if r['dataset']==DS[0] else 'Yandex'}：普通精简使{r['ordinary_level_changes']}个保留节点层级改变；本图全部{r['retained_profiles']}个层级恢复原full对应slot。原入口slot {r['source_full_entry']}，普通compact入口对应原slot {r['ordinary_entry_original_slot']}，新图入口对应原slot {r['preserved_entry_original_slot']}。层级保留连同入口身份改变，是本次构图干预；它不保留原full邻接或保证改善检索。")
v=read(O/'reviews/verification.json');lines+=['',f"实际{cost['NSG']} NSG/{cost['HNSW']} HNSW/2真实小图；合成另4图/512 HNSW。成功编译{cost['compile_seconds']:.3f}s、构图{cost['micro_graph_build_seconds']:.3f}s、四native总{cost['native_job_seconds']:.3f}s；无新画像训练/GT/梯度，继承E66画像训练30.286s及早期GT成本未重测、不记零。计数操作wall不是QPS，正式QPS为0。首次编译priority_queue比较错误及源码/日志保留，0构图/查询后修复，不影响冻结模型或预算。",'',f"独立{v['set_scored_rows']}集合/mask、{v['independent_scalar_rows']}逐行set评分、31808旧控制全字段恢复、全部plain/count及192原kernel通过。{v['same_triple_return_rows']}相同三入口返回/距离bits/graphNDC恢复；全部七slot距离/映射/去重和图W/labels/邻接、原随机流与保留层级均核验。合成实际覆盖零/正层、最高入口删除、非同一内外label、ties、重复返回及5种非法keep拒绝。",'', '输入为历史aux7952和固定3976两半，选择反馈计训练；P-fit含旧train/monitor，cal/audit/aux均历史暴露。本轮未新增fit/cal/audit查询，E34最终与held-out未进入。CPU15/实际进程和数值库1线程、方法与数据集串行，两个数据集原生工具terminal0后评分；失败严格GT10零命中，成员集合得失与query净命中正负部分列。整日目标未完成。','','[协议](protocol.md) · [配对](results/paired.csv) · [原值](results/points.csv) · [失败查询](results/failures.csv) · [层级身份](results/levels.json) · [成本](results/cost.json) · [图](figures/preserved_levels.png) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E75_REPORT_READY')
