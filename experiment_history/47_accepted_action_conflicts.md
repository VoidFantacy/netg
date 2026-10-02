# 47. E58 固定接受动作冲突诊断

2026-09-12，`COMPLETE_IMMUTABLE_ACTION_CONFLICT_DIAGNOSIS`。

当前结果更符合“影响稀疏，少数损伤足以抵消微小收益”，而不是所有共享画像动作都普遍互相冲突。全部908个接受步中，WebVid的E52/E53/E56分别136/185、165/199、128/144步对monitor命中完全不变（73.5%/82.9%/88.9%）；Yandex为99/110、145/153、113/117（90.0%/94.8%/96.6%）。质量不变不代表入口或NDC不变。

冲突确实存在，但应保留发生范围：WebVid monitor单步内部同时增损分别7/9/0步；Yandex三方法均0步。train净收益为正却monitor净受损的WebVid步骤17/137、12/111、3/71；Yandex为2/56、1/44、1/23。因而不能把大多数不迁移的训练增益都归成同一步跨查询抵消。许多动作没有在monitor上触发命中变化；一旦发生少量负变化，却可能吃掉累计收益。

WebVid两seed累计monitor增益/损伤：E52为145/95，E53为80/84，E56为42/18；Yandex为11/18、8/8、3/2。每条WebVid E52/E53轨迹的前5个受损query承受70.0%–77.8%的累计损伤；E56两seed与Yandex所有有损伤轨迹的前5个query承受全部损伤。这是有限轨迹上的集中性，尚未证明这些query能凭可部署特征提前识别。累计事件允许同query反复出现，不能等同独立query数。

纯构图RL在这组固定轨迹中减少了WebVid的损伤和训练收益，也没有普遍解决迁移：E57两seed校准均负；Yandex局部命中变化过少，单个动作即可改变方向。原先“候选有收益、均值更新跨不过离散边界”的E50/E51证据仍成立；把步幅问题修好后，稀疏支持和损伤约束成为接续需要验证的问题，当前没有证据扩大训练预算就能解决。最终选型和性能仍以E57为准，本诊断没有重选任何checkpoint。


| 数据集 | 方法 | 接受/400 | train正、monitor负步骤 | monitor质量不变的接受步 | monitor累计增/损命中 | monitor单步内部冲突 |
|---|---|---:|---:|---:|---:|---:|
| WebVid | E52 | 185 | 17/137 | 136 | 145/95 | 7 |
| WebVid | E53 | 199 | 12/111 | 165 | 80/84 | 9 |
| WebVid | E56 | 144 | 3/71 | 128 | 42/18 | 0 |
| Yandex | E52 | 110 | 2/56 | 99 | 11/18 | 0 |
| Yandex | E53 | 153 | 1/44 | 145 | 8/8 | 0 |
| Yandex | E56 | 117 | 1/23 | 113 | 3/2 | 0 |


以上统计汇总每方法两个seed各200步，属于固定轨迹描述。累计收益/损伤是逐步命中变化的总和，同一query可能反复计入，不能当作独立样本数或最终净收益。train正/monitor负分母为train净命中正步骤；质量不变要求增损均0，不能与净增0混为一谈。

## 固定轨迹与证据链

E52为Gaussian候选贪心直接接受，E53为联合画像/拓扑RL真实步长接受，E56为固定评分P的纯离线构图RL。全部12条原200步轨迹重放，无新动作或参数学习，只执行原已接受修改。每步完整构图坐标和拓扑SHA恢复，E56实际评分向量恒P；monitor1024实际HNSW路由，完整三个入口变化才新增原NSG，routeNDC每次真实更新。train4096只恢复既有接受候选patch，无新训练搜索。

所有0/20/…/200共132个checkpoint逐位恢复，train540672行与monitor135168行的返回/距离/入口/NDC及独立GT集合命中核验通过。全部2400步逐query差分求和严格等于终点减起点，选中点/末点与原训练结果相同；原selected没有因本诊断重选。512物理三路parity行、26170序列化画像行身份独立验收。完整逐query正负反转、失败救回/新增、逐hub损益与损伤集中度可从表复查。

## 实际成本和边界

新增3146 NSG（变化patch 1610、其余物理parity），943104 HNSW、1185物理构图，累计查询进程106.439s。CPU15实际单线程、两集串行；分析CPU8，0优化/新GT/cal/validation/held-out查询，0新增QPS。源保护、预算账、所有checkpoint/完整动作链均通过，旧结果保留。

monitor是历史开发查询，参与原选点且初始P拟合曾用它，不能称独立盲测。本阶段说明固定动作如何影响查询，不能拿来替代E57最终性能、预测未测动作或改变最终模型。单步内部共享查询冲突、不同split的迁移失败、跨步骤同一query的反复变化分别统计，避免把不同机制合并为一个比例。

今晚已完成固定动作诊断和最终NSG/Fast/FastGT对比，停止新增训练与查询。下一步优先检验动作影响范围和损伤约束：用独立开发查询的逐query风险约束接受规则，与同预算全局均值接受比较；先证明损伤能下降且收益保留，再扩大模型或训练预算。该方向仍未运行，不根据最终validation回流选择。完整最终性能和选型以E57冻结报告为准，默认配置未替换。

[协议](../entry_method_exploration/20260912_accepted_action_conflicts_v1/protocol.md)、[12条轨迹](../entry_method_exploration/20260912_accepted_action_conflicts_v1/results/runs.csv)、[2400步骤](../entry_method_exploration/20260912_accepted_action_conflicts_v1/results/steps.csv)、[逐query](../entry_method_exploration/20260912_accepted_action_conflicts_v1/results/queries.csv)、[逐hub](../entry_method_exploration/20260912_accepted_action_conflicts_v1/results/hubs.csv)、[汇总](../entry_method_exploration/20260912_accepted_action_conflicts_v1/results/aggregates.csv)、[独立验收](../entry_method_exploration/20260912_accepted_action_conflicts_v1/reviews/verification.json)、[完整逐步曲线](../entry_method_exploration/20260912_accepted_action_conflicts_v1/figures/accepted_action_trajectories.svg)。
