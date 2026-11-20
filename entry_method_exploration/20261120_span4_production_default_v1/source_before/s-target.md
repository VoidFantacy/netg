# ACSG 后续研究边界

E210 已完成。112个优化点返回与各自对照逐字节一致。纯GT10 QPS变化+12.64%至+30.40%，56/56点过预设筛选。接完整B32变化+11.75%至+29.65%，56/56点过筛选。四集全部已测同L预算支持内核替换候选。生产发布合同仍为E99 GT10。SPAN4可进入切换前的工程验证，优先验证实际并发入口、内存生命周期、非raw-IP兼容性和回退，并用本轮同K/L的等价监督检查作为回归对照。 当前无待恢复实验。

B32的候选质量和额外开销仍依据实际召回门槛、同内核原方法与完整链路验证。E206候选缺口、E207分段和E209预取跨窗证据各按原合同。历史E102/E103与本轮按各自的同期绝对QPS独立比较。

[E210 报告](entry_method_exploration/20261120_span4_four_dataset_retest_v1/report.md) · [E209](experiment_history/209_webvid_b32_span_confirmation_v1.md) · [E206](experiment_history/206_residual_budget_matched_table_v1.md) · [历史索引](s-experiment.md)。
