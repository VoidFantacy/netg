# ACSG 当前接续入口

更新于2026-10-24；仓库`/data/netg/ACSG`，分支`research/state-20261002`，基底HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–184及本次整理为本地工作；HEAD不能冒称包含这些未提交产物，也不把旧远端快照当当前工作区。

## 先读什么

1. [AGENTS.md](AGENTS.md)：协作、文档职责、数据/性能/历史保护约定。
2. [summary.md](summary.md)：唯一当前结论、实际Recall/QPS和证据限制。
3. [spec.md](spec.md)：当前实现、七集metric、数据/计时/复现合同。
4. [s-target.md](s-target.md)：后续三个研究问题及进入/退出条件。
5. [s-experiment.md](s-experiment.md)与[历史目录](experiment_history/README.md)：讨论旧方案时再沿卡片回原证据。
6. [E184报告](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)、[状态](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/state.json)、[整数核验](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/analysis/integer_audit.json)；涉及性能再读[E183报告](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)、[645点](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv)及[独审](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/reviews/independent_results_audit.json)。

## 当前结论与边界

[六页图表PDF](reports/20261024_failure_rescue_residual_v1/ACSG_失败率_救回率与残差作用_20261024.pdf)集中展示失败率、救回率与残差作用，供快速阅读；只复用E183/E184数据。

默认GT10保持：Web软t1/Y硬，E99共享NSG核保持。E184复算七集56K已有查询，区分几何难度、遗漏目标重现、路由与容量；是离线关联诊断，无新ANN/GT/训练/QPS。E183仍为最新性能，Web/COCO残差曲线受益，Flickr/GIST混合，Deep/SIFT及Yandex K100收益不足以统一替换默认。

当前没有待恢复实验队列。历史期限、训练额度、挂起进程、CAL/confirm门和旧runner只属于对应记录；接续先核当前状态，不自动运行。GT几何特征不能充当免费线上信息，已曝光测试不是新盲确认。

## 可复制的只读接续提示词

```text
在/data/netg/ACSG接续研究。先只读核git branch与HEAD，再依LOCAL_CODEX_START.md阅读AGENTS和四主文档。请报告当前默认、最新E184诊断、E183实测Recall/QPS、费用、证据限制及尚未实施的下一问题。讨论旧方案时沿s-experiment进入原卡片/协议/结果。保留旧科学字节与角色；本次只读理解，不训练、构图、生成GT、恢复runner、重测性能或修改默认。
```

2026-10-24整理前的旧交接全文见[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/LOCAL_CODEX_START.md)；科学产物仍在原目录，大向量/图/静态库/teacher响应不因Git文件齐全就可移植复跑。
