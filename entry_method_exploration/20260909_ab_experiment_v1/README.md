# A+B实验：用户指定探索已完成

最终入口：[五点单线程报告](exploration_5point_v1/report.md)。两数据集各validation2000，NSG/Fast/A+B，L64/128/256/400/800；同一份入口模型用于全部L，查询入口逐条一致。

结论：`EXPLORATORY_NO_OVERALL_FAST_GAIN`。小L劣于Fast，高L少量Recall正值伴随QPS下降；当前不推进完整矩阵。原标签、12个模型、线程/中断/范围修正及全部旧结果保留。

- [最终结果目录](exploration_5point_v1/README.md)、[状态](state.json)、[完整过程复盘](../../experiment_history/11_ab_fixed_slot_exploration.md)。
- [原训练协议](protocol.md)、[单线程修订](evaluation_single_thread_amendment.md)、[后来取消的NSG完整补测计划](baseline_comparison_amendment.md)。
- [原输入](inputs/complete.json)、[全标签核验](reviews/full_labels_verified.json)、[历史执行命令](commands.md)。

原16线程结果不进入最终主表；单线程大矩阵及NSG队列已取消，不再自动继续。当前有效评测范围以exploration_5point_v1协议为准。
