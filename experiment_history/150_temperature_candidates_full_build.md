# 150 两种温度公式的冻结画像与主候选完整费用

2026-09-30，记录149过训练探索门后，固定同一r0/2048混合目标，同时保留HybridRectifiedCDF和更简单的HybridApproxMedian；没有读新评价源、调温度或选最好种子。两种温度分别0.01638525724/0.01631888747。

主候选无标签依赖完整构建121.432秒，含按需QGT815+2048精确fit、全20K教师、温度/画像/小图；额外2048近似教师已计费。简单控制在同批新标签上增量3.007秒，不称独立全流程费用。新精确GT2863、NSG20032、审计ANN1024、2画像/图、1聚类；无新Recall或QPS。

全部标签、H及新温度核验；两份W与权重由独立混合目标聚合路径逐位恢复，图真实标签/向量与512对plain/count路由通过。默认保持；下一步在模型冻结后固定来源/预算，测试真实K1/K100完整wall，不让更准确温度代替性能证据。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_full_build_v1/report.md)、[协议](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_full_build_v1/protocol.md)、[成本及身份](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_full_build_v1/results/summary.json)、[独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_full_build_v1/reviews/independent_audit.json)。
