from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));rank=list(csv.DictReader((O/'results/ranking.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
fig,axes=plt.subplots(2,3,figsize=(12,6),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[x for x in rows if x['dataset']==ds and x['split']=='all']
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Zero-hit count change'),('route_NDC_change_pct','Routing distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(2),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(2),['Compact − P10','Compact − full mode10'] if j==0 else ['']*2);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E73 · Remove byte-identical profiles only within each real hub\n7,952 historical auxiliary queries/dataset · fixed ef10 · counted work, no QPS',fontsize=12)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('compact_control.'+ext),dpi=160)
plt.close(fig)
lines=['# E73 同hub完全重复画像精简','', '2026-09-13，第5串行会话。仅精简原mode bank同hub字节完全相同的重复槽，保留所有不同向量和原序；Web2445→1771、Y2463→2067，真实H815/821和原P保留。普通原seed/M16/efConstruction200重建两张小图，ef10、7slot去重前三真实hub、原NSG/raw-IP不变。','', '| 数据 | compact 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for ref in ['baseline10','mode10']:
  rr=[x for x in rows if x['dataset']==ds and x['reference']==ref];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {ref} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines+=['','开发质量标记：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'。原E66/E70/E72门保持，不自动替换默认。按前瞻协议，E74将固定这个唯一compact候选并进行完整同批wall，检验真实费用及质量；即使质量未过，也诚实保留成本反证，不调参或改门。','','原full bank按old_to_compact全部还原W与真实hub字节，因此对任意query每hub完整max画像分数集合不变。duplicate3P压缩后的字节集合等于原P，P控制引用原物理图；不声称duplicate的近似图等价。新compact近似拓扑及入口仍会变化，削减节点数量不等于已知QPS节省。','','完整mode前三一致率（full → compact）：']
for ds in DS:
 vals=[float(next(x for x in rank if x['dataset']==ds and x['model']==name)['exact_agreement'])*100 for name in ['mode10','compact10']]
 lines.append(f"- {'WebVid' if ds==DS[0] else 'Yandex'}: {vals[0]:.2f}% → {vals[1]:.2f}%。")
v=read(O/'reviews/verification.json');lines+=['',f"实际{cost['NSG']} NSG/{cost['HNSW']} HNSW/2小图构建，0新聚类/画像训练/GT/梯度；精简{cost['compaction_seconds']:.3f}s、小图build {cost['micro_graph_build_seconds']:.3f}s、编译{cost['compile_seconds']:.3f}s、四native进程{cost['native_job_seconds']:.3f}s。12 plain和12 count图加载；图/路由分项wall未单独计时为null，本阶段无QPS。继承E66画像训练及GT成本不是零。",'',f"{v['set_scored_rows']}集合/mask和{v['independent_scalar_rows']}独立标量集合评分、31808旧控制返回/入口/距离bits/两NDC恢复、全部plain/count与192原kernel通过；七slot完整距离/映射/去重、序列化W/label和source row核验通过。{v['exact_same_triple_return_rows']}相同三入口结果恢复E69。1/2/3槽有效和空/4槽/负ID/H不匹配拒绝在构图前测试。",'', '输入为历史aux7952及固定3976两半，选择反馈计训练；P-fit包含旧train/monitor，cal/audit/aux均历史暴露。E34最终与held-out未读取。CPU15实际进程与数值库1线程，双集原生terminal0后独立分析。strict failure=GT10零命中；GT成员得失、query净命中正负部、救回/新增分账，全量aligned返回与失败源行保留。','','[配对](results/paired.csv) · [原值](results/points.csv) · [失败查询](results/failures.csv) · [成本](results/cost.json) · [图](figures/compact_control.png) · [协议](protocol.md) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E73_REPORT_READY')
