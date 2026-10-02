# 145：画像分数到有限搜索的连接与反例

2026-09-30理论诊断已完成核验，默认不变。动机是记录144的画像方向改善未转化为稳定Recall收益；本次冻结全部旧模型/开发query，不进行新的方法选择。

对实际W做float64全H排序，区分分数排序变化、Micro-HNSW近似集合变化与主搜索返回变化；保守浮点边界单列。主候选相对默认精确/实际入口变化Web846/1088、Y704/846，其中精确相同而实际改变319/176条。最终K1返回改变15/26条，K100改变113/78条，说明当前工作点对大量入口改变不敏感。相同入口全部返回bits/graph NDC一致；分数协方差恒等式、间隔充分证书和集合并集界得到逐项核验。

Web主候选相对Approx的K100净损52成员，“精确相同/实际改变”组净损59，另一组净救7；该交叉分组不构成小图改变的因果证明，不据此调图或温度。完整wall沿用记录144，无新增性能。

原span+batch4 kernel在预定强连通合成环上，L2/L128、L2/负IP四组合均证实：更近入口及增加更近入口可能让原有成功搜索失败。12次合成调用与独立Python候选池轨迹相同，说明路径存在/距离更近不能单独保证有限beam Recall；不是生产NSG频率证据。

分析2.070秒、审计5.047秒；256标量排序、640证书、240交叉表及全部返回命中重算通过。0新真实NSG/ANN/GT、0模型或性能点。首编译include遗漏已修正，原源码与图构造未改，失败日志保留。下一步实测固定低标签候选的完整构建费用，继续区分方向、开发质量和费用。

后补原文核查：NeurIPS2025 Adaptive Beam Search已有更强的可导航图有限beam反例，本记录不声称新的失败定理。正保证的metric/图/停止条件也不直接适用于当前raw-IP实现。[前作补充](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/literature_addendum.md)。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/report.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/theory.md) · [统计](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/results/summary.json) · [审计](../entry_method_exploration/20260930_theory_until2200_v1/research/routing_bridge_v1/reviews/independent_audit.json)。
