# ACSG 当前实验总结

2026-09-11。最近完成E32，状态`DIRECT_REWARD_POLICY_COMPLETE_FIT_GAIN_MIXED_DEVELOPMENT_STOP`。[完整报告](entry_method_exploration/20260911_direct_reward_policy_v1/report.md)、[历史21](experiment_history/21_direct_reward_policy.md)、[状态](entry_method_exploration/20260911_direct_reward_policy_v1/state.json)。

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

WebVid cal少2个命中，导致“双集每split均胜teacher及默认”的预设门失败。三正一负和四个teacher对照小正信号完整保留；区间覆盖0，不能称稳定改善或稳定退化。graph NDC近似持平，额外成本来自两HNSW提案、全H填充和学习得分；NDC不能换算成QPS。见[开发门](entry_method_exploration/20260911_direct_reward_policy_v1/results/development_gate.json)、[开发与完整成本图](entry_method_exploration/20260911_direct_reward_policy_v1/figures/development_and_cost.svg)。

## 机制、成本与限制

63.455%/81.84%的query在56动作中hits全相同，却贡献teacher初始数据loss的53.02%/75.64%；直接Recall数据梯度在该组严格为0。这支持目标错配线索，但loss占比不是梯度占比。reward最终画像位移比teacher大5.22/3.61倍，尚未分离尺度、表示和拟合因素。[机制诊断](entry_method_exploration/20260911_direct_reward_policy_v1/results/reward_support.json)、[训练轨迹](entry_method_exploration/20260911_direct_reward_policy_v1/figures/reward_and_greedy.svg)。

训练314.78s/600s、4800更新；新训练标签0，复用224万逻辑标签；实际NSG309008调用、21个fit/开发诊断点、154336个query输出独立GT评分与原kernel/线程验收通过。新QPS点0，新validation及held-out未读/hash。一个H/seed/λ/τ，全部split有历史使用，未建立独立盲测或完整前沿结论。

首次默认模型路径漏`t1`，在模型加载阶段失败、NSG0次；旧配置和输出保留，按E30已有默认配置修正至fit_v2。实际调用/gross预留均未超800000，详见[修正说明](entry_method_exploration/20260911_direct_reward_policy_v1/configuration_repair.md)。旧保护链9211文件保持身份，主文档原版保留source_before。

图表、CSV、原始aligned输出和[Excel](entry_method_exploration/20260911_direct_reward_policy_v1/chart_data.xlsx)齐备；[最终验收](entry_method_exploration/20260911_direct_reward_policy_v1/reviews/final_audit.json)。下一阶段以[s-target.md](s-target.md)为准，本轮不自动追加训练、ANN、validation或held-out。
