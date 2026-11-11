# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–188及整理主要是本地未提交工作，HEAD/旧远端不能代表这些完整产物。E188已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)；[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E188报告](entry_method_exploration/20261028_completion_cost_budget_v1/report_zh.md)、[六页PDF](entry_method_exploration/20261028_completion_cost_budget_v1/ACSG_补全成本与硬预算实验_20261028.pdf)、[100点](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/points.csv)、[实际预算对照](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/discrete_comparisons.csv)。
3. [校准角色修正](entry_method_exploration/20261028_completion_cost_budget_v1/calibration_role_correction.md)、[修正选择](entry_method_exploration/20261028_completion_cost_budget_v1/corrected_selection_freeze.json)、[正式选择检验](entry_method_exploration/20261028_completion_cost_budget_v1/analysis/selected_validation.csv)、[核验](entry_method_exploration/20261028_completion_cost_budget_v1/reviews/results_audit.json)。
4. 讨论旧方案从历史卡片进入原协议/源码/结果，不将旧状态当当前队列。

## 已收敛结论

24个硬预算区域点中24个被实测GT10同时覆盖Recall与QPS；速度筛选通过0点、预算召回筛选通过0点。 默认E99 GT10保持。OPT-R返回与REG-R逐字一致，证明的是工程省费；块预算改变访问与候选取舍，必须对照完整wall和附近GT10 L。Deep L200：REG-R平均扫码26134.2，BLOCK-R2048降至1962.3；额外平均耗时361.46→135.77μs，Recall增量0.4821→0.2247pp。扫描减少与救回保留必须一起判断，不把访问次数下降当完整性能收益。

旧B32的末4K校准与16K训练表重叠，原选择存在角色缺陷；正式前修正选择资格，原件保持。原B32仍是正式参考，不能用表内校准收益批准泛化。测试历史曝光，两集真实K100，无K1/其他五集的新预算法证据。

## 可复制的接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD及LOCAL_CODEX_START、AGENTS和四份主文档，再读E188报告与calibration_role_correction.md。
E188已完成正式100点/300轮及校准100点/300轮。默认E99 GT10保持，硬预算和等价工程优化的效果见真实CSV，不把扫码量下降或来源外救回等同可靠Recall–QPS改进。
旧B32包含末4K校准训练标签，原选择已保留，正式前另冻修正选择；无新盲确认。本轮模型/预算/矩阵已收口，不自动重跑、扩大预算、修改默认或改写旧seal。按我当前明确任务继续。
```

本轮修改前根文档在[E188 source_before](entry_method_exploration/20261028_completion_cost_budget_v1/source_before/)，科学与文档交付收据见[E188目录](entry_method_exploration/20261028_completion_cost_budget_v1/)。旧E187科学seal保持，旧根文档SHA只代表当时版本。
