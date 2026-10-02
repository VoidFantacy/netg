# ACSG 下一阶段目标与接续

2026-09-12，今晚授权实验已经结束。

今晚已完成固定动作诊断和最终NSG/Fast/FastGT对比，停止新增训练与查询。下一步优先检验动作影响范围和损伤约束：用独立开发查询的逐query风险约束接受规则，与同预算全局均值接受比较；先证明损伤能下降且收益保留，再扩大模型或训练预算。该方向仍未运行，不根据最终validation回流选择。完整最终性能和选型以E57冻结报告为准，默认配置未替换。

第一步仅基于训练开发分区量化每个动作影响哪些查询、损伤是否重复落在同一群体；锁定独立风险开发集、接受约束、同候选预算对照与停止条件。第二步用新冻结协议验证，最终validation仅作固定模型评估，不能再训练。现有E58只能支持该假设，尚未证明此约束有效。

[最终三指标](entry_method_exploration/20260912_expanded_final_comparison_v1/report.md)、[动作诊断](entry_method_exploration/20260912_accepted_action_conflicts_v1/report.md)。

E59进一步收紧预期：19个已测模型cal的逐query有限上界仅WebVid+0.293 pp、Yandex+0.117 pp，覆盖起点漏检约1.2%；这是固定池上界而非全表示上界。下一阶段应先证明新的动作机制能在独立开发样本获得更多且较少损伤的支持，不能默认学会在现有19模型间选择就有足够部署收益。详见[冻结池诊断](entry_method_exploration/20260912_frozen_pool_transfer_v1/report.md)。
