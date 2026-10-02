# E36 query相关三入口换点策略

已完成8次×3000更新、真实完整三入口反馈、原生在线部署与固定L128单线程成本诊断。Yandex有局部开发信号；WebVid开发门失败，当前推理QPS下降，默认未换。

- [报告](report.md) / [协议](protocol.md) / [状态](state.json) / [开发门](results/development_gate.json) / [最终验收](reviews/final_audit.json)
- [开发质量与成本图](figures/development_quality_and_cost.svg) / [训练图](figures/training_progress.svg) / [交换行为](figures/swap_behavior.svg)
- [Excel](results/query_swap_policy.xlsx) / [完整点CSV](results/points.csv) / [逐query](results/query_results.csv) / [全部训练曲线](results/training_curves.csv)
- [历史25](../../experiment_history/25_query_swap_policy.md) / [下一步](../../s-target.md)

当前版本已收口；方法实现与真实训练完成不等于性能GO。已有cal/audit历史使用，单L成本测量不是完整前沿；无新validation/held-out、多L或改图。
