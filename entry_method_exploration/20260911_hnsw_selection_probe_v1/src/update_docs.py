from common import *
assert not (O/'reviews/docs_updated.json').exists()
rel='entry_method_exploration/20260911_hnsw_selection_probe_v1'
for f in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
 assert sha(R/f)==sha(O/'source_before'/f),'root changed since preparation: '+f
assert sha(R/'experiment_history/README.md')==sha(O/'source_before/history_README.md')
card=f'''# 24 当前GT10的HNSW选点最小验证（E35）

2026-09-11，状态`COMPLETE_HNSW_SELECTION_DIAGNOSIS`。用户进一步澄清主要怀疑“HNSW没挑中已有候选里的好点”，因此将验证限定为当前H内的访问、画像排序、实际单入口与联合三入口效用。此前E34删边RL相对GT10起点没有稳定性能增量；本轮没有追加RL训练。

## 数据与实现

双集各128个E20预定pilot，来自train前10K、与当前20K画像拟合行不重叠，但已有历史诊断使用。WebVid原GT10-soft-t1、Yandex原GT10-hard，H815/821、原HNSW/NSG/raw IP固定，L128/K10、三入口真实ID升序。E20全H单入口缓存核对原query/GT/H/NSG后复用，96次预定native回归通过；旧16线程标签仅用于质量，当前CPU15、进程/OMP/BLAS/MKL均单线程。

原HNSW距离函数旁记录内部被评分点，上/底层合并，768组k1/k3/k8对照plain/count、256现有Policy以及top8前三项一致。原C++不读GT；每query实际执行原ANN3、exact3、ef40_3及当前单张GT10的ANN8内全部56组三入口，输出后独立评分。C8与E28/E32的两路并集C8不同，未套用其联合标签。

## 结果与解释

两图均只有1个有向强连通分量，起点可达全部815/821点，最大最短有向跳数7/5。只看单入口效用有差别的92/65个query，最终三入口含任一最优点29/27个、已评分最优点但最终全未选38/34个、完全没评分到最优点25/4个。最优集合包含全部并列最高命中点；“已评分”不等于“扩展”，单入口最优不保证联合有益。

| 真正三入口搜索 | WebVid R@10 | Yandex-IP R@10 |
|---|---:|---:|
| 原ANN ef10 | 75.546875% | 90.234375% |
| exact全画像top3 | 75.703125% | 90.312500% |
| ANN ef40 | 75.703125% | 90.312500% |
| C8全部真实三元组事后oracle | 79.218750% | 93.046875% |

exact相对ANN只有+.15625/+.078125pp，C8 oracle有+3.671875/+2.812500pp。提高ef40使总NDC1774.53/2984.70升至1913.44/3094.16，无wall，不能推QPS。ANN1到全H单入口oracle差的78.36%/94.81%在已评分集合内即可见，这是免费oracle算术分解，不是学习收益。C8三入口oracle仍在59/34个query低于全H单入口，覆盖问题不能全部排除；三入口也不保证支配单入口。

当前证据优先指向收益相关的选择/组合目标，未支持简单归因断图或只缺更多删边训练轮数。用户的“哪些点适合选入”更直接对应每query保留集合，全局hub更换没有验证。下一步应先以一次HNSW的廉价候选做相同成本控制，再决定是否结合实际图交换/导航画像移动。E28共享画像、E32完整56动作精确收益的已做边界保留，不能改名当新方法。

## 成本、修正与验收

实际新NSG15200（15104联合+96回归），HNSW3072，旧209408单入口返回全部重新GT评分。两集查询进程6.22/13.03s、峰值约5.42/9.93GiB，包含load/trace/I/O，非QPS。没有新训练、GT、validation/held-out访问或QPS；诊断预算收口。

首版prepare误用当前20K fit索引旧pilot行，KeyError后在0查询停止；有效prepare_v2改为核验原train源行、SHA及fit不重叠，旧源码/部分输入保留。协议所称距离bits校验实际为C++堆元素浮点值相等，未独立导出两份堆距离bytes作memcmp；报告明确此精度边界。

- [完整报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[状态](../{rel}/state.json)、[准备修正](../{rel}/reviews/initial_preflight_correction.json)。
- [诊断图](../{rel}/figures/selection_diagnosis.svg)、[逐query CSV](../{rel}/results/query_diagnostics.csv)、[全部质量](../{rel}/results/quality.csv)、[详细分解](../{rel}/results/diagnosis.json)。
- [结果核验](../{rel}/reviews/result_verification.json)、[调用](../{rel}/reviews/jobs.json)、[最终验收](../{rel}/reviews/final_audit.json)。

旧E20/E33/E34及实际源/图/模型/GT/标签不改；根文档修改前快照在source_before。后续未实施方案与停止规则见[s-target](../s-target.md)。
'''
(R/'experiment_history/24_hnsw_selection_diagnosis.md').write_text(card)
p=R/'experiment_history/README.md';s=p.read_text();needle='\n\n## 写入规则';assert needle in s;s=s.replace(needle,'\n| [24 HNSW选点诊断](24_hnsw_selection_diagnosis.md) | E35：当前GT10强连通/已评分集合/精确画像与真实C8三入口，双集128个pilot最小验证 |'+needle);p.write_text(s)
p=R/'s-experiment.md';s=p.read_text();at=s.index('| E34 ');s=s[:at]+f'| E35 HNSW选点最小验证 | 双集128个pilot，当前GT10访问旁路、exact/ef40与当前C8全部56个真实三入口 | `COMPLETE_HNSW_SELECTION_DIAGNOSIS`；强连通且已评分好点漏选，exact增量小/联合oracle有空间；没有新RL/QPS | [24 HNSW选点](experiment_history/24_hnsw_selection_diagnosis.md) |\n'+s[at:];s=s.replace('当前最近完成实验已为E34','当前最近完成实验已为E35').replace('二十三份详细卡片','二十四份详细卡片');p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前实验总结

2026-09-11。最近完成E35，状态`COMPLETE_HNSW_SELECTION_DIAGNOSIS`。[报告]({rel}/report.md)、[历史24](experiment_history/24_hnsw_selection_diagnosis.md)、[状态]({rel}/state.json)。用户澄清主要怀疑HNSW未挑中已有好点，本轮完成最小实际验证，没有新训练或QPS。

## 当前结论

两张GT10原HNSW底层有向图均强连通、起点可达全部815/821点。已评分的有用点未入最终三入口，是这批样本上的主要机制线索；静态断图不是本次观测到的原因。覆盖问题仍存在，不能把全部空间都归为末端排序。

| 验证项 | WebVid | Yandex-IP |
|---|---:|---:|
| 单入口效用有差别的query | 92/128 | 65/128 |
| 其中已评分最优点、最终三入口全未选 | 38 | 34 |
| 其中未评分到任何最优点 | 25 | 4 |
| exact画像top3相对原ANN3 ΔRecall | +0.15625pp | +0.078125pp |
| 当前C8真实三入口oracle相对原ANN3 | +3.671875pp | +2.812500pp |

最优点包含全部并列最高单入口命中点；已评分不是已扩展，单入口最优不能代替真实三入口收益。C8 oracle实际跑完56个组合后用GT挑选，不是学习成果或可部署增益。提高ef40只得到与exact相同的小Recall增量，并增加总NDC；没有新wall，不能换算QPS。[图]({rel}/figures/selection_diagnosis.svg)、[全部质量/失败率]({rel}/results/quality.csv)、[逐query]({rel}/results/query_diagnostics.csv)。

## 执行、核验与边界

各128个预定E20训练pilot，与当前20K画像fit不重叠，但以前做过诊断。当前WebVid GT10-soft-t1/Yandex GT10-hard，原H/ID/画像/HNSW/NSG/raw IP固定、L128/K10；CPU15与进程/OMP/BLAS/MKL1。当前C8为单张GT10 top8，与E28/E32的两路union C8不同。

旧全H单入口209408返回独立GT复核、96个预定native单入口回归通过。当前15104联合输出复算，768组原路由plain/count、256现有Policy与top8前缀通过；新NSG总15200/HNSW3072。首次pilot/fit行检查在0查询停止，修正为核验原train源行；原版本保留。距离parity实际为浮点值相等，不夸大成独立堆距离byte比对。[验收]({rel}/reviews/final_audit.json)。

两集查询进程6.22/13.03s含load/trace/I/O，非QPS。没有新RL、GT生成、validation/held-out访问。旧源/图/标签/模型/历史原件保护，预算收口。

## 与上一轮及下一步的关系

[E34性能补测](entry_method_exploration/20260911_hnsw_rl_benchmark_v1/report.md)仍是当前RL实际性能依据：删边RL相对直接GT10起点没有稳定增量，不能把相对NSG的全部提高归因RL。原GT10与E28局部信号、E32精确收益fit信号、E33单集删边开发信号分别保留，默认未换。

下一步优先一次HNSW现有候选的查询相关保留/组合，在相同候选成本下比较原top3、简单控制和学习；再验证局部图交换能否补充访问空间。不能据强连通/更多epoch直接推导成功，也不能把已有共享画像/精确56动作目标改名RL。[s-target](s-target.md)记录详细未实施设计。
''')
p=R/'spec.md';s=p.read_text();s=s.replace('E34冻结RL图五L/五轮端到端wall与失败率补测已验收','E35当前GT10 HNSW访问/选择最小验证已验收');s+=f'''

## 当前GT10 HNSW访问与选点诊断（E35，2026-09-11）

[协议]({rel}/protocol.md)冻结双集E20前128个训练pilot、当前原GT10 HNSW/H/画像/真实ID/NSG，L128/K10。有效[prepare_v2.py]({rel}/src/prepare_v2.py)核对原train query/GT文件源行与SHA、当前20K fit不重叠、H映射与NSG身份，切出旧全H单入口ID/hits/mask/NDC；首版prepare因pilot不在fit而0查询停止，原件保留。旧16线程标签只作质量证据。

[probe.cpp]({rel}/src/probe.cpp)用SpaceInterface距离回调旁路记录实际被评分内部ID，不改hnswlib搜索/metric。`observed_ip`调用原InnerProductSpace函数；k1/k3/k8逐query与plain/count堆元素值及NDC一致，现有Policy三入口一致。被评分包含上/底层并保留重复事件，不能直接称扩展；ef10下k1/3/8的底层预算均为max(ef,k)=10，最终裁剪k不改变这次搜索预算。堆距离检查为浮点值相等，没有单独memcmp两份距离字节。

输出exact全H同原生距离排序、ann8/ef40/efH、评分mask/events/NDC；每query原NSG执行ANN3/exact3/ef40_3和当前ANN8全部56组三入口，真实ID升序共享beam，C++不读GT。另16query×3固定单入口/集回归旧缓存。新NSG15200、HNSW3072，无新训练/GT/validation/held-out/QPS；CPU15，进程与OMP/BLAS/MKL单线程。

[analyze.py]({rel}/src/analyze.py)复算209408旧单入口及15104新联合返回、mask、96个native回归，解析HNSW有向底层强连通/可达/度/最短跳，按全部并列最佳单入口A0分解访问与最终选择，并输出真正C8三入口oracle。当前C8是单张GT10 top8，不能复用E28/E32两路并集C8标签；若query、H、NSG、metric、L、entry顺序变更，相关标签必须重新验证/生成。

[CSV/JSON]({rel}/results/diagnosis.json)、[图]({rel}/figures/selection_diagnosis.svg)及[验收]({rel}/reviews/final_audit.json)只支持机制诊断。all56联合费用、单/三入口oracle及几何exact分开；NDC/进程时间不是QPS。后续设计不属于此已实现API，见s-target。
''';p.write_text(s)
(R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E35已完成当前GT10 HNSW选点最小验证，状态`COMPLETE_HNSW_SELECTION_DIAGNOSIS`。[报告]({rel}/report.md)、[历史24](experiment_history/24_hnsw_selection_diagnosis.md)。本轮完成用户要求的最小验证；下列训练/构图均为尚未实施方案，无排队任务。

## 已确认的问题位置

两图强连通、全部815/821点可达。128个历史训练pilot中，效用有差别的92/65个query里，38/34个已评分任一单入口最优点却没有放进最终三入口，25/4个没有评分到最优点。exact画像top3只给原ANN3 +.15625/+.078125pp；当前单张GT10 top8的真实56组合oracle给+3.671875/+2.812500pp。优先处理查询相关保留与组合，WebVid仍需关注访问覆盖。

这些是历史小样本诊断和免费oracle，不是模型收益。单入口最佳不保证联合更好；强连通不保证有限预算可导航。E34冻结删边RL相对GT10起点没有稳定增量，E33随机控制仍未建立学习优势，不能只用更多epoch或PPO名义继续原删边表示。GT10/E28已有局部前沿与E32精确收益信号分别保留，默认仍为WebVid原GT10-soft-t1/Yandex原GT10-hard。

## 优先一：同一廉价候选机制下，验证能否学会保留有用点

固定一次原GT10 HNSW top8，训练与部署使用同一候选来源，原三入口作为no-op保底。当前8选3只有56个完整集合，先以真实联合命中而非单入口标签或命中并集评价。一个查询相关小选择器可将原画像分数、当前所选集合与候选间关系作为输入，允许一步换入/换出，比较最终三入口；全部特征计算与选择器wall都要计费。

对照至少原top3、同预算随机换点、相同表示的完整56动作精确期望目标，以及采样/多步RL。若56动作固定且能全枚举，精确目标是方差和收敛参照，不能省略。对照共享同一候选生成/标签/参数量/可选no-op/成本惩罚，完整报告fit、实际开发、失败挽救/新增以及路由/图/总费用；不能从oracle推定可学。E28/E32已做共享画像与完整56动作收益，其两路C8候选成本高；新方案要明确一次HNSW的实质差异，避免全H补齐开销重现。

建议下一份冻结协议采用fit2048/集、cal512/audit512/集，行选择先锁定且明确历史暴露。新当前C8全部标签为2×2048×56=229376次NSG，旧E28/E32 C8不能直接复用；全部准备/标签/parity/开发上限300000，串行查询单线程，L128/K10。最多两RL seed、每个预锁3000更新、每100步记录同固定monitor；不得看开发后无限延长。此处是成本估算和候选设计，样本身份、模型维度、奖励权重、CPU/墙钟/RSS及repair账必须在执行协议中锁定。

奖励可用实际终态hits相对初态的增量减总成本惩罚；多步改写使用相邻两态差分奖励，使累计量等于终态−初态，显式stop/no-op，防止重复领取同一命中。GT只在离线反馈阶段可见；在线只能由query与候选特征作选择，不能反复NSG搜索获得奖励。先检查策略确实改善真实终态，而非只降低代理loss。

建议门槛：冻结选择前双集cal相对原top3至少+.10pp，audit也为正，且相对同表示简单控制有增量，总NDC≤原+1%；query区间与跨seed方向一起报告。NDC只作成本初筛；通过后仍需另锁同机单线程完整Recall–QPS范围。若fit能学但开发未转移，停止该表示并定位泛化；若连fit也学不到当前小空间中的已知收益，先查目标/梯度/容量，不扩大图或训练网格。该门槛是下一份方案建议，本轮未据此进行训练或选点。

## 优先二：在选点机制成立后，再做有真实状态变化的构图迭代

固定H/真实ID/原NSG，动作限制为少量有向边交换，或小半径导航画像移动后重建HNSW；每次动作后真实遍历→最终三入口→原NSG反馈。区别于E33只删已有边：允许把曾漏访的点接入有用路径，或使其能被最终选择规则保留。连通度/最低出入度/预算作为硬约束，真实Recall与总费用作为目标，不奖励度数本身。

强连通保护可沿用从固定起点正向和反向的生成树骨架，余边允许等度交换；但骨架能保证可达，不能保证搜索有效。对照原图、匹配逐点出度随机交换、简单局部结构搜索、学习交换，记录每次动作实际影响哪些query的评分集合与最终入口。若状态/候选集合并未变化，只在固定56个终态间挑选，应先采用优先一的精确目标解释，不扩大成复杂图RL。

构图闭环的新增组合不能按缓存外无标签=0处理；重建、真实反馈、checkpoint/随机对照都进入预算。动作种类和有效样本数要由优先一的新结果决定，本轮不承诺更大的训练网格。只有学习稳定超过相同预算简单交换，且完整wall有收益，才讨论默认替换；否则停止当前动作表示。

## 优先三：全局候选点的选入/换出

用户已澄清主要怀疑现有H内漏选，因此全局hub替换暂居后。当前单入口全H与C8差距只说明既有H中仍有未充分利用的点，不证明需要新base节点。若以后确要改变全局候选库，应另评估点的跨query边际收益、覆盖冗余与真实联合互补，固定H容量并保留原anchor，再对少量候选做交换。更换H/真实ID将使原画像、图、路由与标签链失效，必须重建对应依赖；不得直接搬旧全H/C8结果作为新pool标签。

## 接续要求

完整阅读AGENTS→summary→spec→本文件→s-experiment，从[历史24](experiment_history/24_hnsw_selection_diagnosis.md)进入E35原协议、输入修正、逐query和真实联合输出，再核对[E34](experiment_history/23_hnsw_rl_benchmark.md)/[E33](experiment_history/22_hnsw_edge_rl.md)/[E32](experiment_history/21_direct_reward_policy.md)/[E28](experiment_history/17_gt10_shared_transform.md)相应证据。原版本保持，不用历史NO_GO为新的明确授权制造额外确认。

接续指令示例：在独立版本先锁“一次HNSW top8+原三入口no-op”的query相关集合策略，对齐原top3、匹配随机、同表示精确56动作目标和RL；先核对新样本与标签兼容，记录300000新NSG上限及全成本，完成预定训练/开发后按冻结门收口。图交换、pool替换和正式QPS需分别明确范围；本轮E35诊断已结束，不能把此未实施设计写成已训练成果。
''')
dump(O/'reviews/docs_updated.json',dict(status='UPDATED_REVIEW_PENDING',paths=[str(R/f) for f in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md','experiment_history/24_hnsw_selection_diagnosis.md']]))
print('DOCS_UPDATED')
