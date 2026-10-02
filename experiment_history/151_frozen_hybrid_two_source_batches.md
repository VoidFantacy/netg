# 151 冻结混合候选的两批新源确认

2026-09-30，`COMPLETED_COST_QUALITY_TRADEOFF_NO_DEFAULT_CHANGE`。在源向量读取前冻结Web五个、Y三个方法及全部图／参数，两集各2×4096条query，四批全部锁定后再生成GT；真实K1/K100、CPU15实际单线程、1 warm+3完整wall+1 count，不据首批决定是否追加第二批。

| 主候选相对默认 | ΔR1 (pp)／描述95%区间 | ΔR100 (pp)／描述95%区间 | ΔQPS1／QPS100 |
|---|---|---|---|
| Web HybridPilotTemperature | −0.073242／[−0.170898,+0.024414] | −0.022949／[−0.050049,+0.004517] | +0.010%／−0.580% |
| Y HybridFixedTemperature | −0.097656／[−0.244141,+0.048828] | −0.023193／[−0.120117,+0.073120] | +0.149%／−0.241% |

合并默认R1/QPS1/R100/QPS100为Web90.759277%/417.098/90.632690%/336.237，Y91.723633%/2355.541/91.324341%/1304.594；主候选分别Web90.686035%/417.139/90.609741%/334.288，Y91.625977%/2359.056/91.301147%/1301.452。此为四个固定工作点，不代替全曲线／同召回结论。

Web混合相对原Approx的R1救回4／损伤0，+0.048828pp，两个新批均正；R100净少22成员。Y混合相对Approx净−2个R1命中／−34个R100成员，两批方向相反，开发正值未稳定迁移。温度CDF相对HybridPilot仅R1净+1、R100净+4；近似中位数分别−1／+9，区间均跨0，R100跨批异号。保留成本候选，不采用温度扩展或替换默认，也不继续扫温度。

全部GT／mask／返回／线程／身份独立核验后解释负值。32条预定全库float64检查通过；另对全部2条小GT1/GT2间隔且改变R1的query全库复算，GT1正确，不删除样本或改标签。Web CDF K100第二批第三轮13.403秒较慢，其他两轮约12.16秒；全部保留，合并实测QPS−1.511%，不自行归因或删轮。性能期间无训练／GT／其他性能作业，CPU14有轻量源码／论文读取与PDF提取，条件如实留存。

新GT16384（另34次全库float64核验），NSG655872含512 E99检查，ANN655360；0新W／图。控制器2062.164秒，其中GT760.328、四原生job555.631/85.470/554.218/84.868秒。131072返回query评分、256组分数、78个bootstrap离散分布及31身份通过；分析3.695秒、主核验14.437秒、补核5.673秒。描述区间无多重校正，源窗口不是全源随机或语义独立；这些源现已曝光。

下一步补两项独立证据：温度与标签误差的训练侧交叉分解、让原默认也享有按需QGT后的构建费用参照。不得把共享工程优化当作混合监督独占收益。默认Web GT10-soft-t1／Y GT10-hard、生产E99保持。

[完整报告及绝对表](../entry_method_exploration/20260930_theory_until2200_v1/research/fresh_transfer_v1/report.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/fresh_transfer_v1/protocol.md) · [全部每批／配对结果](../entry_method_exploration/20260930_theory_until2200_v1/research/fresh_transfer_v1/results/summary.json) · [主核验](../entry_method_exploration/20260930_theory_until2200_v1/research/fresh_transfer_v1/reviews/independent_audit.json) · [小间隔核验](../entry_method_exploration/20260930_theory_until2200_v1/research/fresh_transfer_v1/reviews/small_gap_float64_audit.json)。
