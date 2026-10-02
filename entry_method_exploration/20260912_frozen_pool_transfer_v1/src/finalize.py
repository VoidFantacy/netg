from common import *
import re
start();check(O/'reviews/analysis_freeze.json');check(O/'reviews/protected.json')
r=read(O/'results/summary.json');v=read(O/'reviews/verification.json');assert v['status']=='PASS' and v['independent_set_scoring_rows']==233472
core=(O/'reviews/interpretation.md').read_text();assert read(O/'reviews/visual_review.json')['status']=='PASS'
table_text='| 数据集 | split | 可获益query | 有限池逐query上界 ΔR pp | 最佳单一模型 ΔR pp | 差额：未覆盖/自身损伤命中 | 上界占起点漏检 |\n|---|---|---:|---:|---:|---:|---:|\n'
for x in r['splits']:
 table_text+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {x["phase"]} | {x["any_gain_queries"]}/{x["queries"]} | {x["oracle_delta_recall_pp"]:.4f} | {x["best_hit_delta_recall_pp"]:.4f} | {x["best_hit_uncovered"]}/{x["best_hit_own_loss"]} | {100*x["oracle_fraction_of_missing"]:.2f}% |\n'
body=f'''# E59 冻结模型池的收益覆盖与迁移

2026-09-12，`COMPLETE_READ_ONLY_FROZEN_POOL_TRANSFER`。

{core}

{table_text}

## 实际口径

19模型含默认与18新候选，全部使用E57已经预锁的原selected，不新增或更换checkpoint。E47 RL/ES、E52贪心的A/S/T、E53联合RL的A/S/T、E56纯构图RL两个seed分别保留身份。train4096和monitor1024从原prior_raw全量恢复；cal1024只读取E57已生成返回。对应模型跨split身份不变，不把不同模型的训练最佳和cal最佳当作同一模型泛化。

O为每个query在19个已测状态中的最大正命中变化总和，B为一个固定模型的最大净命中总和；O−B=(O−G_best)+L_best。默认在池内，O与B均非负。原cal选中者也单独分解；它在本次两个cal上恰为净命中最佳，但其它split的描述性B不会替换E57选择。逐query上界假设知道GT并可零成本选择模型，不能部署，不能证明其余未测画像空间没有机会。

每模型gain/loss/帮助/损伤/入口变化而命中不变/失败转移全部保存；固定池同一query跨模型正负符号和跨split净值分别统计。模型与query重复相关，不作独立样本显著性推断。monitor参与历史选点，初始P拟合曾用它；cal已选型，均不称盲测。最终validation响应未作为本阶段输入或标签。

## 核验与成本

独立集合评分233472行、114个model/split点、12288逐query分解；原hit字节、全部收益损伤/失败转移/有限池差额恒等式、19候选cal的U和固定选择恢复通过。源保护和分析源码SHA通过，分析验证{v['seconds']:.3f}s，CPU8实际1线程。新增NSG/HNSW/build/optimizer/GT/QPS均0；不导入任何原生搜索接口。图与数表来自同一冻结矩阵，人工检查渲染通过。

最新完整性能继续以[E57报告](../20260912_expanded_final_comparison_v1/report.md)的45点/225轮为准；[E58](../20260912_accepted_action_conflicts_v1/report.md)固定动作证据保持。本次不更新最终模型和默认配置。下一阶段优先检验离线动作的跨开发分组一致性和逐query损伤约束，避免只对均值奖励继续堆训练；具体设计须保持训练/风险开发/校准/最终评估分工，尚未运行。

[协议](protocol.md)、[六split表](results/splits.csv)、[114模型点](results/models.csv)、[逐query](results/queries.csv)、[36模型迁移](results/transfers.csv)、[独立核验](reviews/verification.json)、[收益/损伤图](figures/pool_transfer.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n\n'+table_text)
def history_link(m):
 link=m.group(1);return ']('+str(Path('../entry_method_exploration/20260912_frozen_pool_transfer_v1')/link)+')'
hist=re.sub(r'\]\(([^)]+)\)',history_link,body.replace('# E59 冻结模型池的收益覆盖与迁移','# 48. E59 冻结模型池迁移诊断'))
(R/'experiment_history/48_frozen_pool_transfer.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E58 接受');s=s[:i]+'| E59 冻结池迁移复核 | 19模型×train/monitor/cal已有输出，全量有限池上界和损伤 | `COMPLETE`；233472集合评分、0新搜索；cal有限空间稀疏，最终选择保持 | [48 冻结池迁移](experiment_history/48_frozen_pool_transfer.md) |\n'+s[i:];p.write_text(s.replace('四十七份详细卡片','四十八份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [48 冻结池迁移](48_frozen_pool_transfer.md)：19模型的有限收益覆盖、损伤与跨split不一致，无新搜索。\n')
p=R/'summary.md';s=p.read_text();s=s.replace('2026-09-12，最终比较与固定动作诊断完成。','2026-09-12，最终比较、固定动作及19模型迁移诊断完成。');i=s.index('\n\n当前结果');s=s[:i]+'\n\n'+core+'\n\n[冻结池诊断](entry_method_exploration/20260912_frozen_pool_transfer_v1/report.md)。'+s[i:];p.write_text(s)
p=R/'spec.md';s=p.read_text().replace('E57扩展候选池最终比较已验收','E57最终比较、E58动作及E59迁移诊断已验收');s+='\nE59 [analyze.py](entry_method_exploration/20260912_frozen_pool_transfer_v1/src/analyze.py)仅读取固定19模型的原selected train/monitor输出及E57 cal输出，生成114个模型split点、有限池逐query上界与跨split增损。无原生接口/搜索/训练，原cal选择保持；oracle与单模型差额严格分成未覆盖和自身损伤，不能当部署性能。\n';p.write_text(s)
p=R/'s-target.md';s=p.read_text();s+='\nE59进一步收紧预期：19个已测模型cal的逐query有限上界仅WebVid+0.293 pp、Yandex+0.117 pp，覆盖起点漏检约1.2%；这是固定池上界而非全表示上界。下一阶段应先证明新的动作机制能在独立开发样本获得更多且较少损伤的支持，不能默认学会在现有19模型间选择就有足够部署收益。详见[冻结池诊断](entry_method_exploration/20260912_frozen_pool_transfer_v1/report.md)。\n';p.write_text(s)
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/48_frozen_pool_transfer.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text())
dump(O/'state.json',dict(status='COMPLETE_READ_ONLY_FROZEN_POOL_TRANSFER',new_queries=0,new_training=0,final_selection_unchanged=True))
dump(O/'reviews/final_audit.json',dict(status='PASS',local_links=links,protected_files=len(read(O/'reviews/protected.json')['files']),verification=v,artifact_bytes=sum(p.stat().st_size for p in files(O))))
print('E59 FINAL AUDIT PASS; seal externally after log closes',flush=True)
