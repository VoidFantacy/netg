from shared import *
import re,ast
threads(8);resources();check(O/'reviews/preanalysis_freeze.json');check(O/'reviews/protected.json');r=read(O/'results/analysis.json');gate=read(O/'results/gate.json');v=read(O/'reviews/verification.json')
assert v['status']=='PASS' and gate['status']=='PASS_CANDIDATE_COMMIT_CONTROL_GATE'
status='COMPLETE_CANDIDATE_COMMIT_DIAGNOSIS_UPDATE_TRANSFER_BOTTLENECK'
tab='| 数据集（RL两seed） | 有净正候选步骤/400 | 其中均值命中全空 | J-best单步净值和 | 原均值净值和 | 越界选中候选 |\n|---|---:|---:|---:|---:|---:|\n'
for x in gate['datasets']:
 tab+=f'| {"WebVid" if x["dataset"]==DS[0] else "Yandex"} | {x["positive_candidate_steps"]} ({100*x["positive_candidate_fraction"]:.2f}%) | {x["positive_candidate_mean_null_steps"]} ({100*x["mean_null_fraction_on_positive"]:.2f}%) | {x["J_best_net_sum"]} | {x["mean_net_sum"]} | {x["J_best_illegal_steps"]} |\n'
core='''已测候选到确定更新的转化是明确瓶颈，不能再把主要原因说成完全没有局部可用动作。WebVid RL两seed 400步中214步有净正候选，其中184步（85.98%）Adam均值命中完全不变；Yandex97步有净正候选，其中93步（95.88%）均值不变。J-best包含不动并使用原完整目标，在两个数据集的独立单步反事实净值和为1207/409，原实际均值为51/10。前者不能串成同一条新训练轨迹，不能作为新模型Recall；它只证明原状态中存在已观测而均值未利用的机会。

原目标的成本/失败/漂移项没有在这些状态中让J-best放弃最大净命中：所有八run的J-best净命中和等于hit-best，逐step的hit-best净值按定义不小于J-best，故逐step均相等。不能由此否认成本对方向或新状态的影响。J-best选中系数全部在±2内，不需要扩大旧确定参数边界才得到这些候选。

冲突仍在，但不是“无可提交动作”的证据。RL两seed中，WebVid J-best累计gain1394/loss187；Yandex421/12。逐query有限oracle与hit-best之间，WebVid2012−1207=805分成未覆盖618、自身损伤187；Yandex489−409=80分成未覆盖68、自身损伤12。不同状态或重复query的合计仅作诊断，tie按净命中/J/原序决定，差额不能等同全表示不可避免的冲突。
'''
next_text='''下一步实施独立固定状态步长/方向控制：RL双seed两集step20/40/…/200，40个原状态；沿实际Adam系数方向放大到GT无关原候选半径的1/4、1/2、1倍，沿原J-best候选方向取1/4、1/2，保留原端点。全部真实路由与合法缓存补测，区分原步长未跨边界、方向错过候选和有限半径内无响应。该控制不能凭较大一步正值代替连续学习。

E50预锁的候选择优提交接续门双集通过，随后做同样σ/两seed/200×8/full4096的连续贪心局部搜索对照：原J在已测候选+不动中择优，越界候选不提交；新状态真实重测、缓存随实际提交更新，不使用旧分岔反馈。明确该对照不是RL，不扩原E47训练预算。最终仍按用户要求与NSG/Fast/FastGT作同批QPS/Recall/失败率比较，21:15前冻结最终候选窗口，21:40停止新查询，22:00收口。
'''
body=f'''# E50 已测候选到Adam均值的转化诊断

2026-09-12，`{status}`，接续门`{gate['status']}`。

{tab}
{core}
## 核验与范围

固定E47全部1600状态/12800候选，不挑正例。重建原完整train4096缓存，保留每条真实route NDC/原NSG返回，原J/reward完整恢复；C+八候选的J-best和hit-best、实际均值M分别计算。14400分支cache hash及135648条冷启动/变化patch独立集合评分通过，原画像漂移/失败/NDC和有限oracle分解保持。0新NSG/HNSW/构图/优化/开发/GT，耗时39.760s；原E37–E49全SHA保护。

该结果证明转化缺口存在，尚未因果证明只需放大Adam就能解决，也未验证持续提交候选后的泛化。原E49的WebVid局部正值和Yandex五L平值保持，默认未替换。

## 接续

{next_text}

[协议](protocol.md)、[全部1600步骤](results/steps.csv)、[八run统计](results/runs.csv)、[接续门](results/gate.json)、[独立核验](reviews/verification.json)、[实现](src/analyze_verify.py)。
'''
(O/'report.md').write_text(body);(O/'conclusion.md').write_text(core+'\n'+next_text+'\n')
hist=body.replace('# E50 已测候选到Adam均值的转化诊断','# 39. E50 候选到均值转化诊断');hist=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/'+m.group(1)+')',hist);(R/'experiment_history/39_candidate_commit_diagnosis.md').write_text(hist)
p=R/'s-experiment.md';s=p.read_text();i=s.index('| E49 冻结局部画像性能');s=s[:i]+'| E50 候选到均值转化 | E47全1600状态/12800候选的原J-best、hit-best和Adam均值 | `COMPLETE_CANDIDATE_COMMIT_DIAGNOSIS_UPDATE_TRANSFER_BOTTLENECK`；有正候选时均值空响应Web86%/Yandex96%，直接提交控制门通过；0新搜索 | [39 更新转化诊断](experiment_history/39_candidate_commit_diagnosis.md) |\n'+s[i:];p.write_text(s.replace('三十八份详细卡片','三十九份详细卡片'))
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [39 候选到均值转化](39_candidate_commit_diagnosis.md)：E50全轨迹证明已测机会到确定更新的缺口，0新搜索。\n')
(R/'summary.md').write_text(f'''# ACSG 当前结果摘要

2026-09-12，最近完成E50，`{status}`。[报告](entry_method_exploration/20260912_candidate_commit_diagnosis_v1/report.md)、[历史39](experiment_history/39_candidate_commit_diagnosis.md)。

{tab}
{core}
1600状态/14400缓存分支及135648独立集合评分通过，0新搜索。最近完整Recall–QPS仍E49：WebVid RL仅L128局部正，Yandex五L质量平；没有双集前沿增益，默认保持WebVid GT10-soft-t1 / Yandex GT10-hard。

接续固定状态步长/方向反事实与独立连续候选择优提交，详见[s-target](s-target.md)。用户目标至22:00并要求最终最佳候选对NSG/Fast/FastGT的QPS/召回/失败率，最终完整比较尚未执行。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段目标与接续

2026-09-12，E50完成，[历史39](experiment_history/39_candidate_commit_diagnosis.md)，接续门双集通过。用户目标持续至22:00，大胆假设、小心证明，并最终比较最佳方法与NSG/Fast/FastGT三指标。

## 已有证据与明确问题

{core}
{next_text}
当前固定状态控制和连续提交均尚未执行。已验E46精确缓存可在新状态真实route4096、只对完整三入口变化补测原NSG；旧反馈不满足缓存键时不得复用。每个独立阶段新协议/模型/资源/日程先冻，原E47/E49门及结果不得改判。

## 最终比较必须落实

[最终交付合同](entry_method_exploration/20260912_until2000_v1/final_comparison_contract.md)：Fast=原30K GT1/seed100/legacy堆，FastGT=E24 GT10-hard/20K/seed20260828，WebVid另保留soft匹配起点。最佳候选按cal规则冻结，不用最终audit/QPS换模型；无新方法稳定超越当前GT10则如实说明。现有历史audit1024、五L五轮、失败=GT10零命中，完整Recall–QPS/失败率–QPS/随L三指标、全部原值和配对失败转换及独立单线程核验。21:15前留出最终比较窗口，21:35停止训练、21:40停止新查询、22:00收口。
''')
p=R/'spec.md';s=p.read_text().replace('E50轨迹诊断尚未执行','E50轨迹诊断已验收');s+='\nE50 [analyze_verify.py](entry_method_exploration/20260912_candidate_commit_diagnosis_v1/src/analyze_verify.py)只读E47原12800候选/1600均值稀疏patch及完整route NDC，重建缓存并恢复原J。C+八候选的J-best与净命中/J排序hit-best只作独立单步反事实，含不动，不能传播旧状态输出。14400cache hash/135648独立集合评分和有限oracle分解通过，0新搜索/优化；1600step CSV和原来源保持完整追踪。E51步长方向控制及连续提交当前尚未执行。\n';p.write_text(s)
dump(O/'state.json',dict(status=status,gate=gate['status'],new_NSG=0,optimizer_updates=0,campaign_complete=False))
roots=[R/x for x in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/39_candidate_commit_diagnosis.md']];links=0
for p in roots+[O/'report.md',O/'protocol.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link or link.startswith('#'):continue
  assert (p.parent/link.split('#')[0]).exists(),(p,link);links+=1
for p in files(O/'src'):
 if p.suffix=='.py':ast.parse(p.read_text(),filename=str(p))
dump(O/'reviews/final_audit.json',dict(status='PASS',protected_files=len(read(O/'reviews/protected.json')['files']),local_links=links,artifact_bytes=sum(p.stat().st_size for p in files(O)),verification=v,new_NSG=0,campaign_complete=False))
freeze(O/'reviews/final_artifact_freeze.json',files(O)+roots);print('E50 FINAL AUDIT PASS',flush=True)
