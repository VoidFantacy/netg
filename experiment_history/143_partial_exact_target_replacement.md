# 143 少量精确目标替换的方向偏差—方差

2026-09-30，训练侧诊断完成。原20K近似目标中，均匀替换2048条精确目标；双集16个固定种子全部改善实际画像方向误差，平均相对原ApproxTarget10降18.72%/11.44%，预定seed0降19.54%/8.09%。N/m放大无偏纠偏则风险增加为2.88/7.48倍。没有选择最好seed或调整m。

固定投影下推导R(γ)=(1−γ)²B+γ²N(1−f)V/f，直接替换为γ=f；预测切向风险比0.8604/0.8889，实际均值0.8640/0.8901。是既有收缩思想在有限训练池的具体核算，不宣称统计方法创新。方向改善不等价于Recall收益。

同批seed0精确GT1给出Web温度0.0158979893；20K温度0.0162011385逐位恢复。重估温度会让贡献依赖采样，需另做因素控制。高残差采样不必改善有偏替换，不能直接套record142树。

完整权重表独立重聚合32模型、32种子身份、有限总体60次风险枚举及24文件身份核验通过；同一代理另实现。分析7.259秒、审计9.012秒，0新GT/搜索/部署画像/性能。后继固定seed0检查低成本画像及温度，默认保持。

证据：[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/partial_replacement_v1/report.md)、[预锁协议](../entry_method_exploration/20260930_theory_until2200_v1/research/partial_replacement_v1/protocol.md)、[结果](../entry_method_exploration/20260930_theory_until2200_v1/research/partial_replacement_v1/results/summary.json)、[审计](../entry_method_exploration/20260930_theory_until2200_v1/research/partial_replacement_v1/reviews/independent_audit.json)。
