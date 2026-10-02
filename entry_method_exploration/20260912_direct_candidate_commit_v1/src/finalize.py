from shared import *
import re,ast
threads(8);resources();check(O/'reviews/prequery_freeze.json');check(O/'reviews/protected.json');check(O/'reviews/native_dependencies.json');r=read(O/'results/summary.json');v=read(O/'reviews/training_verification.json');assert v['status']=='PASS'
cost=r['cost'];gate=r['gate'];assert cost['NSG_calls']==113950 and gate['status']=='PASS_DUAL_LOCAL_COMMIT_SIGNAL';status='COMPLETE_DIRECT_CANDIDATE_COMMIT_LOCAL_SIGNAL_SEED_INSTABILITY'
tab='| 数据集 | seed | 选中步 | full train ΔR pp | monitor ΔR pp | 末点monitor ΔR pp | 原E47 RL选中monitor ΔR pp | 提交次数/200 |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for x in r['models']:
 tab+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {x["seed"]%100} | {x["selected_step"]} | {x["full_train_delta_recall_pp"]:+.4f} | {x["monitor_delta_recall_pp"]:+.4f} | {x["last_monitor_delta_recall_pp"]:+.4f} | {x["E47_RL_selected_monitor_delta_recall_pp"]:+.4f} | {x["accepted_submissions"]} |\n'
core='''连续提交已经把部分已见候选机会转成真实静态画像收益，说明E50的更新转化缺口可以实际改善。WebVid两seed选中monitor +0.3125/+0.2051pp，高于原E47 RL对应+0.0781/+0.0098pp；第一seed末点完整训练池+0.6250pp，第二seed末点+0.6543pp。但这是不同状态逐步分岔后的完整算法对照，不是固定状态因果消融，直接证据仍由E50/E51提供。

损伤和种子不稳定也真实存在：Yandex第一seed选中monitor +0.0586pp，第二seed−0.0977pp、末点−0.1270pp，而原E47 RL第二seed选中为+0.0781pp。两seed末点完整训练池均上涨（+0.2515/+0.2734pp），不能据此声称独立query稳定提升。预锁双集“至少一个可行正monitor候选”门通过，只说明候选信号存在；不是四seed稳定性、开发或性能GO。该方法是贪心局部搜索对照，不包装成RL。
'''
next_text='''下一阶段E53保留原RL八候选LOO梯度和Adam方向，以GT无关的候选中位半径r，在r/4、r/2、r三个真实确定点与不动之间按原J选择；Gaussian候选只估计方向，不可直接提交。m/v和局部计数每步推进，实际均值接受后真实恢复图身份与缓存。其依据来自E51放大机会和最大半径损伤的固定控制；协议在E52完整结果之前写定，源码和独立审计已准备，尚未冻结训练。

E53四run预计9612build/36107264 HNSW，NSG固定62976+实际变化、每run预留150000/总600000，0新开发反馈。用E52实测时长保守估算，须预计21:10前完成；用户最后最佳候选对NSG/Fast/FastGT的QPS/Recall/零GT10失败率比较必须在21:15前进入准备窗口，21:40停止新查询，22:00收口。当前尚未执行最终完整比较。
'''
body=f'''# E52 直接提交已测有效候选的连续对照

2026-09-12，`{status}`，局部门`{gate['status']}`。四次连续训练和独立重放完成；0梯度更新，800决策、295实际提交。

{tab}
{core}
## 方法与实际成本

原E47 RL P/B/scale/局部H×16、两seed/200×8/σ.3/GT无关hub和Gaussian ε保持。原J在全部合法候选（系数±2内）与不动之间择优，平分先不动再原序；原八候选即使越界也按原Gaussian真实评测，只限制提交。没有Adam/动量，checkpoint的零m/v只是存储兼容。完整train4096实际route/精确补测，当前缓存来自真正被选中的候选，每步重新build提交W验证拓扑SHA；新状态下一步重新获得真实反馈。

原step0/20/…/200 monitor1024与非零feasible checkpoint选择保持，train512从完整缓存提取。每步确定J不减与逐query提交命中差守恒通过，净命中/monitor损伤不隐藏。selected/last导出普通静态HNSW/W，线上仍一次HNSW→三个真实ID→原NSG，没有在线策略模型。

实际113950 NSG=62976冷启动/监控/parity固定调用+50974候选变化；26276864 HNSW、7212普通构图、6400候选、800决策、295提交、0梯度更新。逻辑候选26214400行与真实新增搜索分开；无额外均值route。WebVid/Yandex进程349.330/270.407s，累计619.738s约10.3分钟，实际单线程CPU15、串行，含加载/构图/写盘/验收，不是线上QPS。

## 核验与解释范围

独立6400候选W/画像公式/Gaussian/原奖励、800合法集合择优/no-op/tie/提交拓扑链、全部完整cache hash/50974变化patch、292638集合评分、44全checkpoint、8导出和512三路parity通过，22.427s，0新搜索。原E37–E51/source/native/data/GT全SHA保护；4job完整预留400000、全部成功，无失败重试。

0新cal/audit/原validation/held-out查询或训练反馈、新GT/QPS。原monitor参与checkpoint选择，不能称盲测。默认保持WebVid GT10-soft-t1 / Yandex GT10-hard；最新完整Recall–QPS仍E49，未形成双集前沿增益。

## 接续

{next_text}

[协议](protocol.md)、[模型表](results/models.csv)、[44 checkpoint](results/checkpoints.csv)、[800真实步骤](results/steps.csv)、[成本](results/cost.json)、[局部门](results/gate.json)、[独立核验](reviews/training_verification.json)、[完整学习曲线](figures/commit_learning.svg)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E52 直接提交已测有效候选的连续对照','# 41. E52 连续候选择优提交');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_direct_candidate_commit_v1/'+m.group(1)+')',hist);(R/'experiment_history/41_direct_candidate_commit.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E51 更新方向/半径');s=s[:i]+'| E52 连续候选择优提交 | 原RL同候选预算/日程，原J在合法已测候选+不动中择优 | `COMPLETE_DIRECT_CANDIDATE_COMMIT_LOCAL_SIGNAL_SEED_INSTABILITY`；Web双seed正，Y一正一负；113950 NSG/800决策295提交，0梯度 | [41 连续提交控制](experiment_history/41_direct_candidate_commit.md) |\n'+s[i:];p.write_text(s.replace('四十份详细卡片','四十一份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [41 连续候选择优提交](41_direct_candidate_commit.md)：E52真实800决策改善更新转化，保留Yandex种子间损伤差异。\n')
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E52，`{status}`。[报告](entry_method_exploration/20260912_direct_candidate_commit_v1/report.md)、[历史41](experiment_history/41_direct_candidate_commit.md)。

{tab}
{core}
实际113950 NSG/26276864 HNSW/7212build/800决策295提交，约10.3分钟；6400候选/800提交/44checkpoint/8导出/292638集合评分独立审计通过。0新开发/QPS；最新完整曲线仍E49，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

E53保留RL方向并按真实J接受预定步长，协议/源码已准备、尚未冻结训练。用户目标持续至22:00并最终比较最佳候选与NSG/Fast/FastGT三指标，最终完整比较尚未执行，详见[s-target](s-target.md)。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E52四训练及独立审计完成，[历史41](experiment_history/41_direct_candidate_commit.md)。用户要求持续至22:00，大胆假设、小心证明，并最终比较最佳方法与NSG/Fast/FastGT的QPS、召回率、失败查询率。

## 当前证据

{core}
E50证明候选反馈到确定均值转化缺口，E51同方向放大救回9/12与4/4机会，也测到最大半径伤害。E48区分评分和邻接的局部质量响应，两集机制不同，不可统一固定一项解决。

## 立即接续E53

{next_text}
[E53协议](entry_method_exploration/20260912_feedback_step_rl_v1/protocol.md)、[训练源码](entry_method_exploration/20260912_feedback_step_rl_v1/src/train.py)、[独立审计源码](entry_method_exploration/20260912_feedback_step_rl_v1/src/audit_training.py)均已准备，冻结/训练尚未执行。完整训练池/监控选点/画像公式/实际线程和源保护保持；新资源artifact384MiB/free8GiB，各dataset≤2400s。原E47和E52对照完整保留，不按新结果换旧seed。

如果模型形成可用局部信号，完整学成W/G的评分/邻接四格可作为额外机制问题；它不同于E48单行小动作，当前仅设计思路，不能当已测结果或提前替换默认。不得因此延误最终性能矩阵。

## 最终交付

[最终合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)：冻结cal预选最佳候选，对NSG、原Fast30K（GT1/seed100/legacy堆）、FastGT10-hard（E24/20K/seed20260828），WebVid另soft匹配起点，同机CPU15实际1线程五L五轮比较完整QPS/Recall/GT10零命中失败率。全部点/五轮范围/配对失败转换/图与独立核验，最终audit不得回流选模型。E49 WebVid缺hard基线，最终要求尚未完成。21:15前留最终窗口、21:35停止训练、21:40停止新查询、22:00收口。
''')
p=R/'spec.md';s=p.read_text().replace('E52直接提交控制已实现并启动，完整验收尚未完成','E52直接提交控制已完成并验收').replace('src/输入/协议已冻结，当前训练中。','src/输入/协议与四训练均已完成，结果由summary维护。');s+='\nE52 [audit_training.py](entry_method_exploration/20260912_direct_candidate_commit_v1/src/audit_training.py)独立重放6400 Gaussian候选/800提交选择与全缓存、原J/合法mask/no-op/tie/拓扑状态链，292638集合评分、44完整checkpoint/8导出及512parity通过；实际113950 NSG/26276864 HNSW/7212build，295提交，0梯度更新。E53 RL方向+真实反馈步长接受已实现源码及协议，尚未冻结执行，不声称已有训练结果。\n';p.write_text(s)
dump(O/'reviews/visual_review.json',dict(status='PASS',file='figures/commit_learning.png',method='Viewed full train/monitor actual curves against original RL; seed instability visible'))
dump(O/'state.json',dict(status=status,gate=gate['status'],NSG_calls=113950,decision_steps=800,gradient_updates=0,accepted_submissions=295,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/41_direct_candidate_commit.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(x['status']=='COMPLETE' for x in jobs) and sum(x['actual'] for x in jobs)==113950
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),verification=v,cost=cost,campaign_complete=False))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print('E52 FINAL AUDIT PASS',flush=True)
