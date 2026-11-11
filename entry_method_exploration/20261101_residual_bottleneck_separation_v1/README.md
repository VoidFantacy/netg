# E197 残差入口瓶颈分离

2026-11-02完成七数据集、K1/K100、两窗、9434点/28302完整T1。默认E99 GT10保持；训练费用不作当前排除条件。先读[定位结论与新方案](findings_zh.md)，再读[详细表格报告](report_zh.md)。

本轮确认有限C入口的GT教师空间，模型实现局部选点改善，但336学习器窗口点均被同窗强GT10/B32/SQ覆盖，拒绝泛化不足。保留WebVid两个简单观察配置和历史M5/B32/SQ正面场景。新监督/两段选择/前置拒绝为未实现建议。

- 方法和角色：[协议](protocol.md)、[角色冻结](role_freeze.json)、[正式冻结](formal_freeze.json)、[源码](src/benchmark.cpp)。
- 数值：[全部点](analysis/points.csv)、[强控制](analysis/comparisons.csv)、[跨窗](analysis/stability.csv)、[瓶颈](analysis/bottlenecks.csv)。
- 核验：[主分析](analysis/analysis_receipt.json)、[stdlib](analysis/stdlib_audit.json)、[模型决策](analysis/decision_audit.json)、[成本](analysis/cost_ledger.json)。
- 图：[教师空间](analysis/figures/quality_headroom.svg)、[费用A](analysis/figures/complete_wall_A.svg)、[费用B](analysis/figures/complete_wall_B.svg)。
- 重启：[恢复资格](reviews/recovery_qualification.json)、[窗口恢复](reviews/reboot_recovery_complete.json)、[持久化](reviews/persistent_storage_delivery.json)、[存储修正](storage_amendment_20261102.md)。
- 收口：[交付核验](delivery_validation.json)、[文件身份](delivery_manifest.json)。

原timed包身份按1原持久/11原三轮SHA恢复/2新GIST区分；恢复窗动作witness为重放来源。公开A/B不是盲确认，不改默认、无新PDF、无待恢复矩阵。新输出在/root/acsg-e197-storage，部分已核验packet归档在/data/acsg-e197-durable-overflow，由稳定文件链接访问，均为持久磁盘。逐点JSON、raw与候选payload可按各archive manifest无损恢复；旧科学文件和seal保持原身份。
