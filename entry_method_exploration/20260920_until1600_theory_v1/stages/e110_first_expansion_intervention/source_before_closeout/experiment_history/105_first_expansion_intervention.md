# 105｜E110 固定三入口的首展开干预

2026-09-20 E110固定三入口首展开干预运行中。先由E107全4096行既有结果核验：GT10增加两个入口时Web47.85%/Y42.41%改变原NSG首节点；单位hub为0%/7.37%。这只是关联；新协议固定GT10精确三入口，强制画像top1先展开一次，再恢复原循环，与原1/3入口全K/L比较。无新GT/图/训练/QPS，尚无干预收益结论。[协议](../entry_method_exploration/20260920_until1600_theory_v1/stages/e110_first_expansion_intervention/protocol.md)。

新诊断只读E107全部既有输入/输出、使用同Faiss原raw-IP距离和Neighbor排序，0新NSG/ANN；约8.82秒含编译。Web单位hub等范数导致top1始终是top3中的raw最近点；Y范数不同且有7.37%首节点变化。GT画像排序无该保序关系。Web单位hub首节点均保持但仍有损伤，已知首节点保持不足以保证单调。

E110预锁所有既有开发query与54方法点，真实K1/K100、全量原输出恢复及同首节点no-op检查。干预只识别所定义的第一次展开反事实，不解释所有后续竞争。投入门、成本和停止条件见原协议；当前未给出结果。首次编译未同步旧KernelCall类型别名，2.02秒失败，0搜索；前件源码/日志/锁完整保留后修正签名，不修改方法或门。

[首节点诊断](../entry_method_exploration/20260920_until1600_theory_v1/research/initial_seed_order_v1/initial_order.csv) · [完整原结果分组](../entry_method_exploration/20260920_until1600_theory_v1/research/initial_seed_order_v1/stratified_results.csv) · [编译修正](../entry_method_exploration/20260920_until1600_theory_v1/stages/e110_first_expansion_intervention/reviews/compile_signature_correction.json)。
