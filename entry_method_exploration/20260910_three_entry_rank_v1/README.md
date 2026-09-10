# 三入口收益排序探索 v1

状态：`EXPLORATORY_SMALL_RECALL_SIGNAL_NO_CLEAR_QPS_GAIN`。2026-09-10已完成用户授权的实现、标注、训练和双数据集五点单线程比较。

- [报告与结论](report.md)、[全部50点原值](results/tables.md)、[Recall–QPS图](figures/recall_qps.svg)
- [协议](protocol.md)、[锁定配置](config.locked.json)、[实际执行说明](commands.md)、[状态](state.json)
- [结果与比较CSV](results/metrics.csv)、[比较CSV](results/comparisons.csv)、[成本账](results/costs.json)
- [输入身份](inputs/preflight.json)、[模型冻结](models/frozen_before_validation.json)、[结果核验](reviews/result_verification.json)、[最终审计](reviews/final_audit.json)

原源码、图、GT、E22标签/模型/结果保留。运行脚本拒绝覆盖现有输出，不要在该目录直接重跑；后续实验另建版本并重新锁定范围。
