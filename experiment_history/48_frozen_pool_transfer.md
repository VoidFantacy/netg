# 48. E59 冻结模型池迁移诊断

2026-09-12，`COMPLETE_READ_ONLY_FROZEN_POOL_TRANSFER`。

把现有19模型全部放到同一cal1024上看，可迁移的局部收益空间确实很小：WebVid只有11个query能被其中任一模型改善，Yandex只有7个。即便允许知道GT、对每条query零成本选最优模型，Recall最多分别+0.293/+0.117 pp，仅填补当前漏检的1.19%/1.14%；这是已测有限模型池上界，不是所有画像或建图方法的上界。

cal最佳单一模型与这个有限上界的差额，WebVid为18个命中，其中17个是没有覆盖到的其它模型收益，1个是自身损伤；Yandex差3个，分成2个未覆盖、1个自身损伤。因此在当前最佳cal模型处，剩余差额主要是覆盖有限，并非大量正负抵消。其它候选仍可能有显著损伤，两集cal均有7个模型monitor净正而cal净负。全部36个新模型在train净正；训练改善并不保证新开发query改善。

两个cal上都未出现同一query在这些模型间既受益又受损，受益和受损主要落在不同query。这并不能证明不同query的要求在共享参数中不可兼容；要证明硬冲突还需要更有针对性的可兼容动作反事实。E58所见“少量关键损伤能抵消微小收益”仍然成立，但此处的固定最优模型表明，只消除已观察损伤也未必带来足够的整体改进。E57原选型与最终曲线完全保持。


| 数据集 | split | 可获益query | 有限池逐query上界 ΔR pp | 最佳单一模型 ΔR pp | 差额：未覆盖/自身损伤命中 | 上界占起点漏检 |
|---|---|---:|---:|---:|---:|---:|
| WebVid | train | 146/4096 | 1.0718 | 0.6250 | 168/15 | 4.38% |
| WebVid | monitor | 28/1024 | 0.8105 | 0.3125 | 35/16 | 3.19% |
| WebVid | cal | 11/1024 | 0.2930 | 0.1172 | 17/1 | 1.19% |
| Yandex | train | 39/4096 | 0.3247 | 0.2515 | 30/0 | 3.20% |
| Yandex | monitor | 6/1024 | 0.1562 | 0.0781 | 8/0 | 1.63% |
| Yandex | cal | 7/1024 | 0.1172 | 0.0879 | 2/1 | 1.14% |


## 实际口径

19模型含默认与18新候选，全部使用E57已经预锁的原selected，不新增或更换checkpoint。E47 RL/ES、E52贪心的A/S/T、E53联合RL的A/S/T、E56纯构图RL两个seed分别保留身份。train4096和monitor1024从原prior_raw全量恢复；cal1024只读取E57已生成返回。对应模型跨split身份不变，不把不同模型的训练最佳和cal最佳当作同一模型泛化。

O为每个query在19个已测状态中的最大正命中变化总和，B为一个固定模型的最大净命中总和；O−B=(O−G_best)+L_best。默认在池内，O与B均非负。原cal选中者也单独分解；它在本次两个cal上恰为净命中最佳，但其它split的描述性B不会替换E57选择。逐query上界假设知道GT并可零成本选择模型，不能部署，不能证明其余未测画像空间没有机会。

每模型gain/loss/帮助/损伤/入口变化而命中不变/失败转移全部保存；固定池同一query跨模型正负符号和跨split净值分别统计。模型与query重复相关，不作独立样本显著性推断。monitor参与历史选点，初始P拟合曾用它；cal已选型，均不称盲测。最终validation响应未作为本阶段输入或标签。

## 核验与成本

独立集合评分233472行、114个model/split点、12288逐query分解；原hit字节、全部收益损伤/失败转移/有限池差额恒等式、19候选cal的U和固定选择恢复通过。源保护和分析源码SHA通过，分析验证1.380s，CPU8实际1线程。新增NSG/HNSW/build/optimizer/GT/QPS均0；不导入任何原生搜索接口。图与数表来自同一冻结矩阵，人工检查渲染通过。

最新完整性能继续以[E57报告](../entry_method_exploration/20260912_frozen_pool_transfer_v1/../20260912_expanded_final_comparison_v1/report.md)的45点/225轮为准；[E58](../entry_method_exploration/20260912_frozen_pool_transfer_v1/../20260912_accepted_action_conflicts_v1/report.md)固定动作证据保持。本次不更新最终模型和默认配置。下一阶段优先检验离线动作的跨开发分组一致性和逐query损伤约束，避免只对均值奖励继续堆训练；具体设计须保持训练/风险开发/校准/最终评估分工，尚未运行。

[协议](../entry_method_exploration/20260912_frozen_pool_transfer_v1/protocol.md)、[六split表](../entry_method_exploration/20260912_frozen_pool_transfer_v1/results/splits.csv)、[114模型点](../entry_method_exploration/20260912_frozen_pool_transfer_v1/results/models.csv)、[逐query](../entry_method_exploration/20260912_frozen_pool_transfer_v1/results/queries.csv)、[36模型迁移](../entry_method_exploration/20260912_frozen_pool_transfer_v1/results/transfers.csv)、[独立核验](../entry_method_exploration/20260912_frozen_pool_transfer_v1/reviews/verification.json)、[收益/损伤图](../entry_method_exploration/20260912_frozen_pool_transfer_v1/figures/pool_transfer.svg)。
