# 149 Web温度的配对CDF校准

2026-09-30，承接144的pilot温度交互问题。固定16组2048训练样本，原精确/近似GT1对应gap；精确全量只评价，估计器仅用样本真值与全体廉价近似gap。校正CDF是既有PPI分位数思路的有限总体适配，系数1、整数通分最左最近网格固定，没有平滑/调参。

温度MSE：PilotMedian 2.48188e-7，RectifiedCDF 5.22183e-8，打乱配对2.09459e-7；预定4项探索门均过。真中位点CDF方差比为16.877%（配对）/199.517%（打乱）。但更简单的ApproxMedian仅1.38648e-8，更好；后续必须保留此控制，不能只因校正方法复杂就选择它。r0温度为0.01638525724（CDF）/0.01631888747（纯近似），原pilot0.01589798927，真值0.01620113850。

0新标签/搜索/画像/图/线上指标，分析0.584秒/独立核验0.356秒。32个CDF、320标量阈值、120有限总体枚举及20K近似gap全排序通过。若构建要多生成当前管线跳过的2048近似教师行，不能免费使用缓存。无Recall结论或默认替换。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_cdf_v1/report.md)、[冻结协议](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_cdf_v1/protocol.md)、[理论](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_cdf_v1/theory.md)、[全结果](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_cdf_v1/results/summary.json)、[核验](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_cdf_v1/reviews/independent_audit.json)。
