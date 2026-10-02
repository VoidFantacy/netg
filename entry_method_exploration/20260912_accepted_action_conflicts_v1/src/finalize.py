from shared import *
import ast,re
threads(8);resources()
for name in ['prequery_freeze','protected','native_dependencies']:check(O/'reviews'/f'{name}.json')
r=read(O/'results/summary.json');v=read(O/'reviews/verification.json');cost=r['cost']
assert v['status']=='PASS' and v['steps']==2400 and v['checkpoint_monitor_rows']==135168 and v['checkpoint_train_rows']==540672
assert cost['optimizer_updates']==0 and cost['new_QPS']==0 and cost['NSG_calls']<=60000
core=(O/'reviews/interpretation.md').read_text();assert read(O/'reviews/visual_review.json')['status']=='PASS'
table='| 数据集 | 方法 | 接受/400 | train正、monitor负步骤 | monitor质量不变的接受步 | monitor累计增/损命中 | monitor单步内部冲突 |\n|---|---|---:|---:|---:|---:|---:|\n'
for x in r['aggregates']:
 table+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {x["stage"]} | {x["accepted"]} | {x["train_positive_monitor_negative_steps"]}/{x["train_positive_steps"]} | {x["accepted_monitor_quality_null"]} | {x["monitor_gain_hits"]}/{x["monitor_loss_hits"]} | {x["monitor_conflict_steps"]} |\n'
nexttext='''今晚已完成固定动作诊断和最终NSG/Fast/FastGT对比，停止新增训练与查询。下一步优先检验动作影响范围和损伤约束：用独立开发查询的逐query风险约束接受规则，与同预算全局均值接受比较；先证明损伤能下降且收益保留，再扩大模型或训练预算。该方向仍未运行，不根据最终validation回流选择。完整最终性能和选型以E57冻结报告为准，默认配置未替换。'''
body=f'''# E58 已接受动作的跨查询收益与损伤

2026-09-12，`COMPLETE_IMMUTABLE_ACTION_CONFLICT_DIAGNOSIS`。

{core}

{table}

以上统计汇总每方法两个seed各200步，属于固定轨迹描述。累计收益/损伤是逐步命中变化的总和，同一query可能反复计入，不能当作独立样本数或最终净收益。train正/monitor负分母为train净命中正步骤；质量不变要求增损均0，不能与净增0混为一谈。

## 固定轨迹与证据链

E52为Gaussian候选贪心直接接受，E53为联合画像/拓扑RL真实步长接受，E56为固定评分P的纯离线构图RL。全部12条原200步轨迹重放，无新动作或参数学习，只执行原已接受修改。每步完整构图坐标和拓扑SHA恢复，E56实际评分向量恒P；monitor1024实际HNSW路由，完整三个入口变化才新增原NSG，routeNDC每次真实更新。train4096只恢复既有接受候选patch，无新训练搜索。

所有0/20/…/200共132个checkpoint逐位恢复，train540672行与monitor135168行的返回/距离/入口/NDC及独立GT集合命中核验通过。全部2400步逐query差分求和严格等于终点减起点，选中点/末点与原训练结果相同；原selected没有因本诊断重选。{v['parity_rows']}物理三路parity行、{v['serialized_profile_rows']}序列化画像行身份独立验收。完整逐query正负反转、失败救回/新增、逐hub损益与损伤集中度可从表复查。

## 实际成本和边界

新增{cost['NSG_calls']} NSG（变化patch {cost['normal_new_NSG']}、其余物理parity），{cost['HNSW_calls']} HNSW、{cost['builds']}物理构图，累计查询进程{cost['query_seconds']:.3f}s。CPU15实际单线程、两集串行；分析CPU8，0优化/新GT/cal/validation/held-out查询，0新增QPS。源保护、预算账、所有checkpoint/完整动作链均通过，旧结果保留。

monitor是历史开发查询，参与原选点且初始P拟合曾用它，不能称独立盲测。本阶段说明固定动作如何影响查询，不能拿来替代E57最终性能、预测未测动作或改变最终模型。单步内部共享查询冲突、不同split的迁移失败、跨步骤同一query的反复变化分别统计，避免把不同机制合并为一个比例。

{nexttext}

[协议](protocol.md)、[12条轨迹](results/runs.csv)、[2400步骤](results/steps.csv)、[逐query](results/queries.csv)、[逐hub](results/hubs.csv)、[汇总](results/aggregates.csv)、[独立验收](reviews/verification.json)、[完整逐步曲线](figures/accepted_action_trajectories.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n\n'+table+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_accepted_action_conflicts_v1/'+m.group(1)+')',body.replace('# E58 已接受动作的跨查询收益与损伤','# 47. E58 固定接受动作冲突诊断'))
(R/'experiment_history/47_accepted_action_conflicts.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E57 扩展');s=s[:i]+f'| E58 接受动作冲突诊断 | E52/E53/E56完整12条轨迹，train/monitor逐query增损 | `COMPLETE`；2400步/{cost["accepted"]}接受，{cost["NSG_calls"]}新NSG，0训练 | [47 接受动作冲突](experiment_history/47_accepted_action_conflicts.md) |\n'+s[i:];p.write_text(s.replace('四十六份详细卡片','四十七份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [47 接受动作冲突诊断](47_accepted_action_conflicts.md)：完整固定轨迹的跨查询收益/损伤、质量稀疏与失败转移。\n')
performance=(E57/'reviews/interpretation.md').read_text()
points=[x for x in read(E57/'results/analysis.json')['points'] if x['phase']=='validation' and x['L']==128]
labels={'nsg':'NSG','fast30k':'Fast30K','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft起点','best_new':'cal选中新候选'}
pt='| 数据集 | 方法 | Recall@10 % | QPS五轮中位数 | 零命中失败率 % |\n|---|---|---:|---:|---:|\n'
for x in points:pt+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {labels[x["model"]]} | {x["recall_pct"]:.3f} | {x["QPS"]:.2f} | {x["failure_pct"]:.2f} |\n'
(R/'summary.md').write_text('# ACSG 当前结果摘要\n\n2026-09-12，最终比较与固定动作诊断完成。\n\n'+core+'\n\n[动作诊断报告](entry_method_exploration/20260912_accepted_action_conflicts_v1/report.md)。\n\n'+performance+'\n\nL128代表点，单线程历史validation2000，失败定义为GT10零命中。\n\n'+pt+'\n完整五L与五轮范围见[最终比较](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)。\n\n'+nexttext+'\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，今晚授权实验已经结束。\n\n'+nexttext+'\n\n第一步仅基于训练开发分区量化每个动作影响哪些查询、损伤是否重复落在同一群体；锁定独立风险开发集、接受约束、同候选预算对照与停止条件。第二步用新冻结协议验证，最终validation仅作固定模型评估，不能再训练。现有E58只能支持该假设，尚未证明此约束有效。\n\n[最终三指标](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)、[动作诊断](entry_method_exploration/20260912_accepted_action_conflicts_v1/report.md)。\n')
p=R/'spec.md';s=p.read_text();s+='\nE58 [run.py](entry_method_exploration/20260912_accepted_action_conflicts_v1/src/run.py)只重放E52/E53/E56已有接受动作，原训练patch恢复train4096，monitor1024全路由并按完整三入口缓存NSG；拒绝步不构图/查询。固定132个checkpoint和逐query差分守恒独立核验，选中身份不改；输出steps/queries/hubs与图字节身份，计数不用于QPS估算。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/47_accepted_action_conflicts.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
jobs=read(O/'logs/jobs.json');assert len(jobs)==2 and all(x['status']=='COMPLETE' for x in jobs) and sum(x['actual'] for x in jobs)==cost['NSG_calls']
assert jobs[0]['completed_at']<=jobs[1]['started_at']
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
dump(O/'state.json',dict(status='COMPLETE_IMMUTABLE_ACTION_CONFLICT_DIAGNOSIS',cost=cost,default_replaced=False))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,cost=cost,verification=v,artifact_bytes=sum(p.stat().st_size for p in files(O))))
print('E58 FINAL AUDIT PASS; seal externally after log closes',flush=True)
