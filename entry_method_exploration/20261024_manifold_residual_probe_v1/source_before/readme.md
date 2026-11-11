# ACSG：GT10入口路由与残差补全研究

更新于2026-10-24。**当前默认是GT10**：由训练目标构造查询画像，Micro-HNSW选择三个真实base入口，再搜索固定NSG；WebVid为soft-t1，Yandex为hard。原ACO→DPC→Neural Router属于历史路线，不是当前默认流水线。

[开始阅读](LOCAL_CODEX_START.md) · [当前结论](summary.md) · [实现合同](spec.md) · [后续问题](s-target.md) · [历史索引](s-experiment.md)。

## 最新研究

- [E184：残差与空间分布/失败修复](entry_method_exploration/20261024_residual_geometry_diagnosis_v1/report_zh.md)。七集56K已有查询的离线诊断：几何难度与残差可复用性需要分开，不能单归因多模态或库规模；无新性能，默认不变。[低于10%召回查询比例：全L修正版PDF](reports/20261024_failure_rescue_residual_lt10_v2/ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf)；严格0–9个GT100命中，区分有所改善与升到≥10%，替代旧未满100口径。
- [E183：七集完整性能](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)。645点/1935完整单线程批次；WebVid/COCO的残差曲线受益，其余数据按范围判断。[简版PDF](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/concise_v1/NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf) · [645点CSV](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/final_v1/points.csv)。

残差补全在固定主返回后查冻结posting、去重、按原metric评分合并，不改变主图遍历；它仍为研究方案。所有当前数字、费用和限制以summary及实际协议/审计为准。

## 实现与复现

核心代码在[ACSG](ACSG/)，评测/数据配置在[benches](benches/)，隔离研究在[entry_method_exploration](entry_method_exploration/)。使用本地CPU依赖和`.venv_cpu`，具体输入、源码、kernel和计时边界读[spec](spec.md)。旧绝对路径或一键命令不代表新实验已授权/可重跑；当前没有待恢复队列。

文档清理前的旧NETG介绍、构建/ACO命令、论文作图说明已[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/readme.md)。历史结果、源码和大资产保持原位；这次整理没有训练、性能重测、Git提交或发布。
