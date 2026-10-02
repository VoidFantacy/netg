# E103：优化后的五集完整重测

E103于2026-09-17T08:18:23.251697+08:00完成统一优化后五集完整重测：800配置、2400轮单线程plain、32800000次真实搜索；NSG/hard/soft/GATE同一span+batch4，HNSW同轮重新计时。全部返回/入口/逐query NDC对齐E97，Recall独立重算。90/95/99%门槛中25个组合至少一方法达到，GT10均值最快22个、进入三轮范围重叠组24个；范围重叠不是显著性判断。图和分析已自动生成，人工图像检查待完成。无训练/新图/GT/默认变更。

用户根据E102结果有条件授权重测；条件仅依据已完成四点GT10仍处最好一组，不先声称五集全面第一。复用E97五集公开查询和每K原16档预算，排除LAION与Recall@10，原模型和数据保持。门槛表取达到目标召回的最快实测点，不插值，实际Recall、L、重复范围全部保留；完整分析必须看各集差异。

独立后台流水线依次冻结、测试、全量历史结果和输入身份对照、GT评分、float64距离抽检、跨K核验、画图和分析。单线程CPU15，端到端包含路由/search/output；计数直接转发真实batch4。无自动重试或选最快轮。

本轮优化仅用于独立评测入口，生产仍E99。Git备份cd3a3229；旧资产/main/index保留，原公开query曝光和GIST来源校验限制保留。

[完整报告](../entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/report.md) · [协议](../entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/protocol.md) · [数值验收](../entry_method_exploration/20260916_optimized_five_dataset_r1_r100_v1/reviews/raw_results_verified.json)
