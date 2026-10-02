# 21 直接检索收益策略优化（E32）

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

开发每split1024条，全部相对默认的配对95%区间覆盖0。WebVid cal少2个命中导致预设“双集每split都严格胜teacher/默认”门失败；不是稳定退化证明。相对teacher四点为正的小信号保留，不据此放宽门。图NDC近似持平，但路由NDC从约112/107增到1069/1047；无独立wall，不能把NDC比例换算成QPS。未读/hash新validation或held-out。

## 成本、修正和解释边界

训练314.78s/600s、4800更新，新训练标签0，复用224万逻辑组合标签。实际NSG309008次，805056次在线HNSW查询含parity，21个诊断点，没有QPS点。诊断进程wall213.77s含一次约5秒配置失败。

首次fit把默认W路径漏写`t1`，在第二个Policy加载阶段退出、实际NSG0次。原输出/配置/控制器/日志保留，以E30实际配置修正后使用fit_v2；新增启动前文件核验。零查询失败的160064预留显式释放，但保留gross账；最终实际309008/gross469072均低于800000。原模型、收益门和温度选择未变。细节见[配置修正](../entry_method_exploration/20260911_direct_reward_policy_v1/configuration_repair.md)。

当前只支持“直接收益有更强fit信号及小幅开发对照信号”；没有稳定默认替换、完整端到端前沿或多步RL成功证据。一个H/seed/λ/τ，全部split有历史使用。E31固定teacher支线仍关闭，原GT10/E28局部正信号保留；下一步优先泛化和一致而更便宜的候选机制，未自动追加实验。

- [完整报告](../entry_method_exploration/20260911_direct_reward_policy_v1/report.md)、[协议](../entry_method_exploration/20260911_direct_reward_policy_v1/protocol.md)、[条件部署清单](../entry_method_exploration/20260911_direct_reward_policy_v1/deployment_plan.md)、[缓存门](../entry_method_exploration/20260911_direct_reward_policy_v1/results/cache_gate.json)、[开发门](../entry_method_exploration/20260911_direct_reward_policy_v1/results/development_gate.json)、[状态](../entry_method_exploration/20260911_direct_reward_policy_v1/state.json)。
- [训练与策略收益图](../entry_method_exploration/20260911_direct_reward_policy_v1/figures/reward_and_greedy.svg)、[开发与成本图](../entry_method_exploration/20260911_direct_reward_policy_v1/figures/development_and_cost.svg)、[Excel](../entry_method_exploration/20260911_direct_reward_policy_v1/chart_data.xlsx)。
- [模型复核](../entry_method_exploration/20260911_direct_reward_policy_v1/reviews/model_and_cache_verification.json)、[全量路由验收](../entry_method_exploration/20260911_direct_reward_policy_v1/reviews/route_parity.json)、[真实结果验收](../entry_method_exploration/20260911_direct_reward_policy_v1/reviews/deployment_verification.json)、[最终验收](../entry_method_exploration/20260911_direct_reward_policy_v1/reviews/final_audit.json)。
