# E176 Git 阅读快照（2026-10-11）

**默认保留 GT10，原 M5 保留；E176 完成后停止。** 目标是可靠的 Recall–QPS 综合改进，本轮局部组合收益没有建立可靠默认替换。

目标 `VoidFantacy/netg:research/state-20261002`，发布父 `84dc95730818a750e72a425bd0f96a25e3604ffb`。本入口编写时实际服务器 HEAD 为 `96cf05d5410cf51272048cd1f90b4bb194e23c62`；新发布 SHA 尚未生成。发布身份以后续 [发布记录](publication.md) 和本地 `git rev-parse HEAD` 为准。

先按 [本地 Codex 入口](../../LOCAL_CODEX_START.md) 阅读 AGENTS→summary→spec→s-target→s-experiment→history176，再读本轮原件。下列 `portable` 是浏览副本，只转换已入库目标的绝对链接；原科学文件、SHA、数值和服务器路径身份保持不动：

- [E176 详细复盘（浏览版）](portable/experiment_176.md) / [原件](../../experiment_history/176_m5_residual_completion_curve_v1.md)
- [冻结报告（浏览版）](portable/e176_report.md) / [原件](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/report.md)
- [费用补充（浏览版）](portable/e176_cost_ledger.md) / [原件](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/cost_ledger_supplement.md)
- [独立结果审计](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/independent_result_audit/report.json) / [最终交付复核](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/reviews/final_delivery_review.json)
- [160点CSV](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/points.csv) / [全部800比较解释](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/interpretation.csv)
- [主方法曲线](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/recall_qps_budget_curves.png) / [机制对照曲线](../../entry_method_exploration/20261010_m5_residual_completion_curve_v1/analysis/final_v1/figures_delivery_v3/mechanism_budget_curves.png)

本轮 WebVid2.5M/Yandex official10M raw-IP，各原已曝光 public_test 前10000；真实K1/K100、L200/400/800/1000/1200、八方法。160点、480个完整wall批次、800比较、60机制记录，CPU15/T1串行、每点三轮。只有一个公共角色，没有新独立确认；线段仅连接真实点，不能插值作性能承诺。

M5RES12−原M5：Recall14升/6平/0降，点QPS中位数严格双升8/20，原冻结配对比率primary9/20；对M5OPT双升0/20，PAIR对WIDE12双升0/20。速度定义分别为 `median(QPS_A)/median(QPS_B)` 与 `median_r(QPS_A_r/QPS_B_r)`，不一般相等，全部原标志保留。WebK100五点组合收益可见，但缓存省费不能归为条件补全的独立质量收益；PAIR/WIDE离线容量未配平。

单次全量untimed oracle与返回字词资格已核；没有第二整批native replay，timed输出未保存。NDC仅固定256样本，CI为描述性、独审未重生bootstrap。公开信号、U外成员救回与旧TRAIN支持均不能直接证明跨模态泛化。

历史新增FIT获每集额外900秒授权，实际Web469.143610秒/Y472.986268秒，旧TRAIN债保留；未知行政费用保持null，内外计时不重复加。授权已完成，不授权本地再次拟合。仓库代码、图、汇总和审计可读；本地复跑需要 [外部资产迁移与域一致性检查](external_assets.md)，不能把本次发布当已迁移的数据/可运行环境。
