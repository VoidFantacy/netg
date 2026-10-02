# 152 温度误差与标签误差不能独立相加

2026-09-30，只用固定r0训练贡献与已冻结的三种Web温度模型。原GT温度T*下混合标签切向误差1.018872418；pilot温度的纯温度项0.007131806、交叉项+0.024728991，总1.050733214。CDF分别0.002723964、−0.015479632，总1.006116749；近似中位数分别0.001108851、−0.009859301，总1.010121967。交叉项不能省略，固定样本内积不称抽样协方差或因果份额。

原Approx理想单位化chord²1.832123876，固定T混合1.474111238；pilot／CDF／近似中位数1.522729299／1.451823569／1.459219261。所有unit(v).float32逐位恢复冻结W。这里CDF温度离T*比简单中位数更远，却因误差抵消而画像更近；不能按温度MSE排序推画像或Recall。记录151未见稳定温度线上收益，不据本诊断选新温度。

一次解析dW/dlogT在T*处计算，对已冻结三温度的一阶方向相对余项1.829%／1.081%／0.694%；不能外推大温度变化。平方分解与归一化／softmax微分是本场景应用，不冒称新普遍定理。

分析4.022秒、核验86.070秒；7335个逐hub／度量检查、23身份、中心差分最大误差1.166e−10。0新GT/NSG/ANN/画像/图/性能，默认保持。只恢复解释所需的导数与能量，不导出新候选。

[报告](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_error_decomposition_v1/report.md) · [理论](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_error_decomposition_v1/theory.md) · [协议](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_error_decomposition_v1/protocol.md) · [完整结果](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_error_decomposition_v1/results/summary.json) · [独立核验](../entry_method_exploration/20260930_theory_until2200_v1/research/temperature_error_decomposition_v1/reviews/independent_audit.json)。
