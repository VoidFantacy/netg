# 140 近似贡献残差方差与校正预算诊断

2026-09-22，固定原20K fit、E125精确/近似目标、H/温度，只重算已存在权重与向量总和作统计核验。8.023秒，0新GT/搜索/候选W/图/性能点，不访问新复测输入。四权重SHA和向量总和恢复，两集各16个hub显式中心化残差独立复核协方差trace。

Web/Y十训练目标ID重合92.0675%/93.8970%（非新Recall@10评测），hub归属质量平均TV6.5663%/5.5000%。残差贡献trace方差只有原贡献的4.5758%/6.3092%，但直接近似的累加偏差也已较小。

均匀无放回m条精确补标的差值校正，总和预期MSE为(N²/m−N)V；要低于直接近似偏差B需m>N²V/(B+NV)。原尺度阈值Web约1679.3、Y7582.5；按精确画像合力平方归一化后约3268.8/8516.2，即16.34%/42.58%。没有按该阈值训练模型或选定补标数，不保证实际角度/Recall，亦不一票否决纠偏路线。

因此继续保留简单近似成本候选；混合纠偏需要核算额外费用与残差采样噪声，不能承诺少量补标就更好。[报告](../entry_method_exploration/20260922_until2200_improvement_v1/research/approximate_residual_variance_v1/report.md) · [原统计](../entry_method_exploration/20260922_until2200_improvement_v1/research/approximate_residual_variance_v1/results/summary.json)。
