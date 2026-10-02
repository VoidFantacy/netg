from shared import *
import ast,re
threads(8);resources()
for name in ['prequery_freeze','launch_v2_freeze','protected','native_dependencies']:check(O/'reviews'/f'{name}.json')
r=read(O/'results/summary.json');v=read(O/'reviews/training_verification.json');assert v['status']=='PASS';cost=r['cost'];gate=r['gate']
models=[read(O/'models'/ds/f'graph_rl_{seed}'/'model.json') for ds in DS for seed in SEEDS]
for k in ['construction_calls','topology_installations','score_vector_verifications']:assert sum(m[k] for m in models)==9612
assert cost['builds']==19224 and cost['gradient_updates']==800 and v['serialized_graphs']==8 and v['serialized_constant_profile_rows']==6544
core=(O/'reviews/interpretation.md').read_text();assert read(O/'reviews/visual_review.json')['status']=='PASS'
tab='| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | E53 joint选中monitor ΔR pp | 接受/200 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for m in r['models']:
 tab+=f'| {"WebVid" if m["dataset"]==DS[0] else "Yandex"} | {m["seed"]%100} | {m["selected_step"]} | {m["full_train_delta_recall_pp"]:+.4f} | {m["monitor_delta_recall_pp"]:+.4f} | {m["last_monitor_delta_recall_pp"]:+.4f} | {m["E53_joint_RL_selected_monitor_delta_recall_pp"]:+.4f} | {m["accepted_updates"]} |\n'
status='COMPLETE_CONSTRUCTION_ONLY_RL_LOCAL_SIGNAL' if gate['status'].startswith('PASS') else 'COMPLETE_CONSTRUCTION_ONLY_RL_NO_DUAL_LOCAL_SIGNAL'
nexttext='''E57按训练前协议将E55原17候选加本次两个seed全部selected，19模型/集；同fit128恢复、cal1024原U/低NDC/固定序选型后冻结。仅当某集改选新模型时，对该集全部NSG/Fast/FastGT及候选重新同批五L五轮；若身份不变，整组复用E55已验计时，不重复或混批。新调用88768+受影响组完整矩阵，最大719488；保留历史validation非盲测身份，21:40停止新查询、22:00收口。'''
body=f'''# E56 RL只优化离线构图，查询画像评分固定

2026-09-12，`{status}`；局部门`{gate['status']}`。

{core}

{tab}

## 实际方法与序列化身份

离线局部坐标C沿用E53的H×16参数/同Gaussian与hub日程、LOO RL梯度/Adam方向及r/4、r/2、r真实反馈接受；训练评价始终是固定原画像P上的实际G(C)。普通build(C)取完整邻接，再build(P)并安装G(C)，逐次全向量字节检查后才查询。原漂移公式作为离线构图坐标正则保留；不是直接逐边参数化，也不是E33仅删原底边。与E53有相同候选/梯度预算，额外物理构图与安装成本单列，不能称等wall训练。

selected/last的W.f32恒P，construction_W.f32仅离线，graph.hnsw是真实P/G(C)。checkpoint W字段是构图坐标，不能用于线上评分。8图独立原生字节解析验证6544画像行、真实ID/节点层级与完整多层拓扑SHA；每次逻辑构图全物理P检查共9612次。线上仍一个普通HNSW top3再原NSG，无RL策略或隐藏C评分。

## 成本与核验

实际{cost['NSG_calls']} NSG=62976固定+{cost['candidate_new_NSG']}Gaussian变化+{cost['deterministic_new_NSG']}确定点变化；36107264 HNSW、9612逻辑构图、19224物理构图/9612安装，800梯度/接受决策、{cost['accepted_updates']}真实接受。完整进程{cost['training_process_seconds']:.3f}s，CPU15实际单线程、每seed独立native、两集串行；加载和实际所有物理构图均记账。0新cal/audit/validation/held-out训练反馈、0新GT/本阶段QPS。

独立6400Gaussian/2400确定点、800四分量梯度/Adam/步长选择/拓扑缓存状态链、44完整checkpoint、8导出/512三路parity通过；{v['return_set_scores']}集合评分，审计{v['seconds']:.3f}s。每run完整预留150000 NSG/4806物理构图，总19224<25000；原native每实例7500守卫不变，实际成本未因重建实例省略。

## 设计时序与启动修正

算法和超参文件写成时间早于E55 WebVid最终结果生成；封存时该结果已可用但尚未读取，首次严格“生成前封存”检查失败如实留档。之后资源预测守卫仅依据E53旧dataset耗时比修正，未使用E55最终质量；此与方法算法改变区分。E56首入口预测完成超出21:10目标约16秒，在native创建前退出，NSG/HNSW/build/update均0；有效train_v2仅将预测目标调为21:12，21:15实际训练硬停仍保持，原代码/config/log保留。没有查询失败后重试或修改种子。

历史monitor参与选点且P拟合曾用它，不能称盲测；训练局部门不是独立泛化/性能GO，不撤销E53或E55负结果，默认尚未替换。

{nexttext}

[协议](protocol.md)、[有效训练](src/train_v2.py)、[模型表](results/models.csv)、[800步骤](results/steps.csv)、[成本](results/cost.json)、[独立重放](reviews/training_verification.json)、[设计时序](reviews/design_before_result_inspection.json)、[资源预测修正](reviews/design_guard_revision.json)、[启动窗口修正](launch_window_revision.md)、[学习曲线](figures/construction_learning.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+tab+'\n'+nexttext+'\n')
hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_construction_only_rl_v1/'+m.group(1)+')',body.replace('# E56 RL只优化离线构图，查询画像评分固定','# 45. E56 纯离线构图RL'))
(R/'experiment_history/45_construction_only_rl.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E55 固定');s=s[:i]+f'| E56 纯构图RL | RL优化离线C产生G(C)，全部查询恒P评分 | `{status}`；{cost["NSG_calls"]} NSG/19224build/800梯度，8图全部P字节核验 | [45 纯构图RL](experiment_history/45_construction_only_rl.md) |\n'+s[i:];p.write_text(s.replace('四十四份详细卡片','四十五份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [45 纯离线构图RL](45_construction_only_rl.md)：固定在线评分P，实际G(C)反馈训练及部署字节核验。\n')
(R/'summary.md').write_text('# ACSG 当前结果摘要\n\n2026-09-12，E56纯构图RL四训练完成，[报告](entry_method_exploration/20260912_construction_only_rl_v1/report.md)。\n\n'+core+'\n\n'+tab+'\n最新完整性能仍为[E55](entry_method_exploration/20260912_final_method_comparison_v1/report.md)：原17候选池cal选中者在两集五L全部未超过匹配GT10起点；Fast/GT10对NSG优势保留，新RL增量未成立。\n\n'+nexttext+'\n')
(R/'s-target.md').write_text('# ACSG 下一阶段目标与接续\n\n2026-09-12，E56纯构图RL已完成且独立验收，训练停止。\n\n'+nexttext+'\n\n[E57预锁协议](entry_method_exploration/20260912_expanded_final_comparison_v1/protocol.md)，源码已准备。不得根据E55/后续最终validation改变训练，全部新旧候选保留；在线W必须P，construction_W只离线。\n')
p=R/'spec.md';s=p.read_text().replace('E55固定候选池完整比较已验收','E56纯构图RL已验收').replace('已实现并启动：每逻辑构图','已完成四训练并验收：每逻辑构图').replace('完整四训练尚待验收','完整四训练和独立部署字节核验已通过');s+='\nE56 [graph_bytes.py](entry_method_exploration/20260912_construction_only_rl_v1/src/graph_bytes.py)独立解析HNSW二进制头、每节点画像/真实ID和所有层邻接，核验6544导出画像行恒P及拓扑SHA。有效[train_v2.py](entry_method_exploration/20260912_construction_only_rl_v1/src/train_v2.py)仅预测窗口区别于原首入口，21:15实际训练硬停不变，算法和实际构图/查询接口一致。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/45_construction_only_rl.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(x['status']=='COMPLETE' for x in jobs) and sum(x['actual'] for x in jobs)==cost['NSG_calls'] and sum(x['reserved_builds'] for x in jobs)==19224
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
dump(O/'state.json',dict(status=status,gate=gate['status'],cost=cost,campaign_complete=False));dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,cost=cost,verification=v,artifact_bytes=sum(p.stat().st_size for p in files(O))))
print('E56 FINAL AUDIT PASS; seal externally after log closes',flush=True)
