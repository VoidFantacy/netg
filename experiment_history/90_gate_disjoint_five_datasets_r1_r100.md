# E97：GATE正负标签修正与五集Recall@1/100

已完成800点、2400次单线程wall，数据为WebVid、Yandex、Deep、BIGANN-SIFT、GIST，排除LAION。GATE五集新训练，GT10-hard/soft固定对照和NSG、完整HNSW同口径重测。详见[完整复盘](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/report.md)、[CSV](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/results/metrics.csv)和[原始配置](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/config.locked.json)。

底图/向量/模型/GT及E96旧结果保留；新SIFT来源变化、GIST下载校验限制、历史测试曝光、离线成本与指标口径均在复盘中披露。未因本次公开测试自动替换默认方法。

2026-09-16最终分析已完成：[逐集分析与门槛表](../entry_method_exploration/20260915_gate_l2_r1_r100_v1/analysis.md)。WebVid在90% Recall@1门槛下hard为352.5 QPS（90.73%），NSG为280.9（90.65%）；Yandex在95% Recall@1门槛下hard为1127.5 QPS（95.02%），soft为906.1（95.77%）。Deep/SIFT的hard与soft非常接近，GIST的K100更适合完整HNSW。门槛差异不代表整条曲线支配，GATE未显示跨五集稳定优于GT10；原默认未替换。

正式阶段15.826小时，结束于2026-09-16 07:09:42；已记录离线阶段4.869小时。保留[Yandex前缀修正90a](90a_yandex_test_prefix_fix.md)：14:09前检停止、15:20恢复，约70分钟等待不算计算成本；原100K源文件与旧资产未覆盖。
