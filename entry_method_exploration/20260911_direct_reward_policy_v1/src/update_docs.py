from common import *

assert read(O/'results/development_gate.json')['status']=='STOP_DEVELOPMENT_GATE'
rel='entry_method_exploration/20260911_direct_reward_policy_v1'
card=R/'experiment_history/21_direct_reward_policy.md';assert not card.exists()
card.write_text(f'''# 21 直接检索收益策略优化（E32）

2026-09-11完成，状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。用户同意小规模直接收益目标对照。两集缓存门通过，实际fit和cal/audit完成；相对teacher四个开发点均正，但WebVid cal未胜当前默认，按预设开发门停止，无新validation/QPS。

## 与旧版本的实质区别

[E31](20_training_effectiveness.md)固定教师/共享linear/λ100，只改优化日程，Yandex未产生缓存改善。本轮保持该模型、候选、λ、日程和标签，比较multi teacher hinge与完整56动作的精确期望Recall。数据梯度初始化范数匹配β，之后冻结；无需采样策略梯度/PPO，没有多步状态或图拓扑重连。训练/部署都在同C8中选完整三元组，避免将C8标签外推成全H入口选择收益。

4次各1200步，从A=0训练。checkpoint只按期望和贪心graph NDC≤各自初始化+1%的可行点中本组fit目标最小选择。β WebVid110.404375/Yandex91.075940，λ100/τ.05/seed20260911/CPU8/float64不变。全部点均可行，teacher选中/末点A/W共8文件逐位恢复E31 multi。48处共享A有限差分、策略梯度恒等式、常收益零梯度、完整fit独立β及8模型恢复通过。

## 保留的训练信号

| 数据集 | C8 anchor R@10 | teacher | reward | reward−anchor pp | reward−teacher pp |
|---|---|---|---|---|---|
| WebVid2.5M | 75.1875% | 75.3990% | 76.3145% | +1.1270 | +0.9155 |
| Yandex10M IP | 90.1815% | 90.1775% | 90.4825% | +0.3010 | +0.3050 |

上述float32选点对应原真实NSG L128/K10标签，同C8成本变化仅+0.08685%/+0.03378%。后续完整实际fit逐条命中和图NDC复现。相对teacher净增1831/610命中，正负query均保留；缓存Recall不直接等于QPS。

reward在63.455%/81.84%的动作hits完全相同的query上数据梯度为零；这些query却占teacher初始数据loss的53.02%/75.64%。原teacher仍学习NDC并列选择，这是目标错配的机制线索，不等于梯度范数占比或完整因果证明。reward位移比teacher大5.22/3.61倍，未做等位移臂；收益也可能包含尺度/表示/拟合因素。

## 开发、完整成本与停止

C8在线Policy包含两固定HNSW direct3、全H填充、8个学习得分、56动作argmax及原NSG。8万逻辑路由候选/slot/真实三入口与冻结计算全部一致。双集fit7点、cal/audit14点完成，154336个返回独立GT评分与原kernel/线程核验通过。默认仍为WebVid GT10-soft-t1/Yandex GT10-hard。

| 数据集/split | reward−teacher pp | reward−默认 pp | 总NDC相对默认 |
|---|---|---|---|
| WebVid cal | +0.0293 | -0.0195 | +53.87% |
| WebVid audit | +0.2051 | +0.1660 | +53.76% |
| Yandex cal | +0.1172 | +0.0293 | +31.81% |
| Yandex audit | +0.1074 | +0.0879 | +32.12% |

开发每split1024条，全部相对默认的配对95%区间覆盖0。WebVid cal少2个命中导致预设“双集每split都严格胜teacher/默认”门失败；不是稳定退化证明。相对teacher四点为正的小信号保留，不据此放宽门。图NDC近似持平，但路由NDC从约112/107增到1069/1047；无独立wall，不能把NDC比例换算成QPS。未开展新validation评测；旧validation输入有保护性SHA256读取，held-out未读/hash。

## 成本、修正和解释边界

训练314.78s/600s、4800更新，新训练标签0，复用224万逻辑组合标签。实际NSG309008次，805056次在线HNSW查询含parity，21个诊断点，没有QPS点。诊断进程wall213.77s含一次约5秒配置失败。

首次fit把默认W路径漏写`t1`，在第二个Policy加载阶段退出、实际NSG0次。原输出/配置/控制器/日志保留，以E30实际配置修正后使用fit_v2；新增启动前文件核验。零查询失败的160064预留显式释放，但保留gross账；最终实际309008/gross469072均低于800000。原模型、收益门和温度选择未变。细节见[配置修正](../{rel}/configuration_repair.md)。

当前只支持“直接收益有更强fit信号及小幅开发对照信号”；没有稳定默认替换、完整端到端前沿或多步RL成功证据。一个H/seed/λ/τ，全部split有历史使用。E31固定teacher支线仍关闭，原GT10/E28局部正信号保留；下一步优先泛化和一致而更便宜的候选机制，未自动追加实验。

- [完整报告](../{rel}/report.md)、[协议](../{rel}/protocol.md)、[条件部署清单](../{rel}/deployment_plan.md)、[缓存门](../{rel}/results/cache_gate.json)、[开发门](../{rel}/results/development_gate.json)、[状态](../{rel}/state.json)。
- [训练与策略收益图](../{rel}/figures/reward_and_greedy.svg)、[开发与成本图](../{rel}/figures/development_and_cost.svg)、[Excel](../{rel}/chart_data.xlsx)。
- [模型复核](../{rel}/reviews/model_and_cache_verification.json)、[全量路由验收](../{rel}/reviews/route_parity.json)、[真实结果验收](../{rel}/reviews/deployment_verification.json)、[最终验收](../{rel}/reviews/final_audit.json)。
''')
s=(R/'s-experiment.md').read_text();needle='| E31 有界训练有效性检查 |'
assert needle in s
s=s.replace(needle,'| E32 直接真实收益策略 | 同模型/候选/标签、teacher与精确期望Recall共4次1200步；在线C8与21个真实fit/开发点 | `DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`；双集缓存门通过、相对teacher开发四正，WebVid cal未胜默认且路由成本高，停止validation/QPS | [21 直接收益策略](experiment_history/21_direct_reward_policy.md) |\n'+needle,1)
s=s.replace('当前最近完成实验已为E30','当前最近完成实验已为E32').replace('十九份详细卡片','二十一份详细卡片')
(R/'s-experiment.md').write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();needle='| [20 训练有效性检查](20_training_effectiveness.md) | E31同目标优化、缓存真实命中与未知界、双集门停止、无新QPS |'
assert needle in s;s=s.replace(needle,needle+'\n| [21 直接收益策略](21_direct_reward_policy.md) | E32完整组合期望Recall、双集fit信号、真实开发四点对照及候选成本、开发门停止 |')
p.write_text(s)
(R/'summary.md').write_text(f'''# ACSG 当前实验总结

2026-09-11。最近完成E32，状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。[完整报告]({rel}/report.md)、[历史21](experiment_history/21_direct_reward_policy.md)、[状态]({rel}/state.json)。

## 当前结论

直接最大化完整三入口的真实期望Recall，比原教师目标学出了更强的训练集收益；cal/audit相对teacher四点均为正，但相对当前默认只有三正一负，幅度小、区间覆盖0。完整C8候选生成还带来较高路由NDC。按预锁开发门停止，本轮无新validation/QPS，尚不能替换默认或宣称端到端性能收益。

当前默认保留WebVid GT10-soft-t1、Yandex GT10-hard，依据[E30既有同批五轮曲线](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)。GT10/E28既有局部正信号保留；E31的固定teacher优化支线不因新目标信号而重启。

## 本轮实现与实际结果

固定NSG/H/GT/fit20K/C8全部56个动作标签、共享linear与λ100、τ.05、优化日程。teacher为最高hits且最低NDC并列G的hinge；reward精确计算策略期望Recall，β只在初始化匹配数据梯度范数。4次各1200步，选成本可行域中本组fit总目标最低点。teacher的选中/末点A/W逐位恢复E31；新目标不是多步PPO或图拓扑重连。

| 数据集 | 同C8 anchor R@10 | teacher | reward | reward−anchor pp | reward−teacher pp |
|---|---|---|---|---|---|
| WebVid2.5M | 75.1875% | 75.3990% | 76.3145% | +1.1270 | +0.9155 |
| Yandex10M IP | 90.1815% | 90.1775% | 90.4825% | +0.3010 | +0.3050 |

这是float32完整组合选点的真实L128/K10标签效用，双集缓存门通过。新在线C8的候选/slot/真实三入口对8万逻辑路由全量一致；实际fit两集的hits/NDC全量复现，故不是仅训练loss下降。

| 数据集/split（每个1024query） | reward−teacher pp | reward−当前默认 pp | 总NDC相对默认 |
|---|---|---|---|
| WebVid cal | +0.0293 | -0.0195 | +53.87% |
| WebVid audit | +0.2051 | +0.1660 | +53.76% |
| Yandex cal | +0.1172 | +0.0293 | +31.81% |
| Yandex audit | +0.1074 | +0.0879 | +32.12% |

WebVid cal少2个命中，导致“双集每split均胜teacher及默认”的预设门失败。三正一负和四个teacher对照小正信号完整保留；区间覆盖0，不能称稳定改善或稳定退化。graph NDC近似持平，额外成本来自两HNSW提案、全H填充和学习得分；NDC不能换算成QPS。见[开发门]({rel}/results/development_gate.json)、[开发与完整成本图]({rel}/figures/development_and_cost.svg)。

## 机制、成本与限制

63.455%/81.84%的query在56动作中hits全相同，却贡献teacher初始数据loss的53.02%/75.64%；直接Recall数据梯度在该组严格为0。这支持目标错配线索，但loss占比不是梯度占比。reward最终画像位移比teacher大5.22/3.61倍，尚未分离尺度、表示和拟合因素。[机制诊断]({rel}/results/reward_support.json)、[训练轨迹]({rel}/figures/reward_and_greedy.svg)。

训练314.78s/600s、4800更新；新训练标签0，复用224万逻辑标签；实际NSG309008调用、21个fit/开发诊断点、154336个query输出独立GT评分与原kernel/线程验收通过。新QPS点0，未开展新validation评测；旧validation输入有保护性SHA256读取，held-out未读/hash。一个H/seed/λ/τ，全部split有历史使用，未建立独立盲测或完整前沿结论。

首次默认模型路径漏`t1`，在模型加载阶段失败、NSG0次；旧配置和输出保留，按E30已有默认配置修正至fit_v2。实际调用/gross预留均未超800000，详见[修正说明]({rel}/configuration_repair.md)。旧保护链9211文件保持身份，主文档原版保留source_before。

图表、CSV、原始aligned输出和[Excel]({rel}/chart_data.xlsx)齐备；[最终验收]({rel}/reviews/final_audit.json)。下一阶段以[s-target.md](s-target.md)为准，本轮不自动追加训练、ANN、validation或held-out。
''')
(R/'s-target.md').write_text(f'''# ACSG 下一阶段方向与实验接续

2026-09-11。E32已完成并停在开发门，状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。[报告]({rel}/report.md)、[历史21](experiment_history/21_direct_reward_policy.md)、[开发门]({rel}/results/development_gate.json)。当前授权的小规模直接收益试验已收口，没有排队的训练/ANN/validation任务。

## 当前采用与保留信号

默认仍为WebVid GT10-soft-t1/Yandex GT10-hard，以[E30同批曲线](entry_method_exploration/20260911_equivalent_teacher_sets_v1/report.md)为依据。原GT10/E28局部正信号保留，E31固定teacher/共享linear/λ100的优化支线继续关闭。

E32更换为完整动作的真实期望Recall，同C8 fit相对teacher+0.9155/+0.3050pp，cal/audit相对teacher四点均正；对当前默认则三正一负、幅度小。不能把新目标简单等同于旧teacher重训，也不能说训练之外完全没有信号。WebVid cal少2命中而未过预设门，总路由成本同时增加：完整audit总NDC约+54%/+32%。尚无QPS或稳定替换证据。

## 优先一：直接收益的泛化与候选成本

先用现有原始结果完成问题定义，不直接扩成PPO/大模型。关键问题分开：目标是否改善同候选的真实动作选择；该改善能否在独立评估保留；同一候选生成能否用足够低的在线代价实现。

下一份小协议应先锁定一项主要变化及对照。泛化方向可考虑fit标签内部固定交叉拟合，或预先确定的位移/容量控制，至少保留原teacher、原anchor和直接收益对照；不能根据现有cal/audit选有利折或超参。已有20K×56标签只支持原query、C8、完整三入口、L128/K10及同kernel身份；可复用的部分无需新NSG标签，但新增模型及额外训练必须单列预算与停止规则。

候选成本方向先区分两路HNSW、全H填充、学习打分和NSG成本。若改为更便宜的候选域，必须显式列出旧标签覆盖率与新增组合标注需求；缺失标签不作0，不把新域的训练与旧C8部署收益混用。最终完整wall必须包含候选生成和全部在线处理，graph NDC持平不能作为总成本通过。

进入后续真实评测的条件应在运行前锁定：同域对照有实际收益，模型/候选/核验通过；在明确独立的开发数据上胜默认且成本可接受；随后同机单线程完整Recall–QPS曲线。若成本或开发门失败，保留信号后停止，不用剩余预算扩网格。阶段产物仍为协议、冻结身份、模型、aligned结果、gate、图/CSV/Excel和成本账。

## 优先二：GT10独立复现与公平比较

原GT10的独立复现与强基线问题仍未完成。E32只比较默认画像及teacher/直接收益C8，不代表所有NSG/Fast/其它方法的完整比较。复现方案需要明确固定图上变化的是query、build seed或其它因素；已有历史validation不能重新称盲测。先核对现有基线与输入身份、GT成本、Recall区间，再定义最小新矩阵。

新方案至少预锁共同Recall目标、完整端到端wall、单线程与CPU、重复轮次、构建/查询/GT依赖和硬cap；只以独立同机前沿证据认定性能收益。不得由E32缓存或同L Recall替代。

## 优先三：多步强化学习只在问题确有顺序决策时考虑

当前56动作已知收益，精确期望目标足够检验目标对齐，无需采样PPO。若未来研究搜索过程中的多步动作，须先说明状态、允许动作、真实转移、成本奖励和非RL对照，以及与已停止C状态干预的实质差异；不能重命名恢复旧runner。当前单步C8信号不授权图重连、无限标签采样或新多步训练。

## 接续要求与未执行边界

完整阅读AGENTS→summary→spec→本文件→s-experiment，再由[历史21](experiment_history/21_direct_reward_policy.md)进入原协议、部署清单、全部gate、模型和原始结果，必要时追溯[E31](experiment_history/20_training_effectiveness.md)/[E30](experiment_history/19_equivalent_teacher_sets.md)。保留原版本；本轮修正控制器为`*_v2.py`，旧失败配置不覆盖。

可用接续指令：核对E32的四个开发点、teacher与直接收益的位移差和完整路由账；在固定一个问题后，提出带对照、数据依赖、标签/训练/查询成本与停止规则的最小协议。上述三个方向的下一阶段均未执行；不从本轮剩余预算自动启动训练、ANN、validation或held-out。

正式性能继续CPU15、进程/OMP线程1、OMP/BLAS/MKL1，一次一个方法，不与训练、编译或重分析并发。所有收益解释须区分fit信号、开发信号、原始实测前沿和插值分析。
''')
p=R/'spec.md';s=p.read_text();s=s.replace('（E30等效教师/漂移控制/五轮评测工具已实现；原Fast/kernel不变）','（E32完整动作期望收益、同C8在线策略与真实开发验收已实现；原Fast/kernel不变）')
s+=f'''

## 完整动作直接收益策略 v1（E32，2026-09-11）

独立版本[{rel}]({rel}/protocol.md)固定E28 C8/56组合标签及E31共享linear。新[train.py]({rel}/src/train.py)支持teacher hinge和精确策略期望Recall regret，两组从A=0、λ100/τ.05、同1200步日程；β只用初始化fit数据梯度范数计算一次并冻结。每步记录期望与贪心Recall/NDC；在二者成本均≤各自初始化+1%的点中选本组fit总目标最低最早点，导出A.f64/W.f32与末点原件。独立NumPy复核β、全部选中/末点目标和模型；teacher逐位恢复E31。

新[Policy]({rel}/src/benchmark_with_nsg.cpp)的family=c8接受`c8_anchor`及两个固定`c8_policies`：先复用原HNSW direct3并集和原GT10全H float32得分填满8，再以unit query/float32 W的float64分数枚举56完整动作，按真实ID映射后调用原NSG。候选/slot/真实三入口与冻结fit计算全量一致，plain/count共享已序列化小图。route NDC包含两HNSW距离、H次填充得分和8次模型得分；graph/total分别记录。新Decision保存8候选local ID和动作slot，GT仅在全部原始搜索后读取评分。

[evaluate.cpp]({rel}/src/evaluate.cpp)保留原kernel和direct3路径，支持无wall的完整plain/count/原kernel16条验收；条件wall接口实现一次完整warmup+5轮轮换独立wall，包含完整C8生成/打分/组合选择/映射/NSG/output，排除GT/count/hash/I/O/build。该wall接口已编译，本轮因开发门失败未产生QPS测量。实际fit/cal/audit21点已完成，配置与实际CPU15/单线程均核验。

有效控制器为[run_deployment_v2.py]({rel}/src/run_deployment_v2.py)及[deployment_common_v2.py]({rel}/src/deployment_common_v2.py)：启动前校验所有画像/映射文件、拒绝已有输出，分离缓存/路由/fit/开发/条件validation门并记录调用账。初始默认W路径漏`t1`的零查询失败原件保留；修正只恢复E30已有默认身份，释放预留的特例与证据见[配置修正]({rel}/configuration_repair.md)。其它失败仍按完整预留计费。输入/模型/候选改变须重新核对标签复用键；不得把本C8策略收益直接外推为全H或单路HNSW选点收益。实验结论由summary与[历史21](experiment_history/21_direct_reward_policy.md)维护。
'''
p.write_text(s)
dump(O/'reviews/document_update.json',dict(status='PASS',history_card=str(card),updated=['experiment_history/README.md','s-experiment.md','summary.md','s-target.md','spec.md'],
    prior_versions=str(O/'source_before'),stale_headers_corrected=['spec E30 to E32','s-experiment recent E30 to E32 and history count 19 to 21']))
print('DOCUMENTS_UPDATED',flush=True)
