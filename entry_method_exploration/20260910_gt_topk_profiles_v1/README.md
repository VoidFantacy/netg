# E24：固定 H 的 GT1/GT10 × 硬/软画像

独立实验入口。当前状态见[state.json](state.json)；原有base、raw-IP、NSG、QGT seed20260828及H815/821不变。

- 方法与预算：[protocol.md](protocol.md)、[config.locked.json](config.locked.json)。
- 结果：[report.md](report.md)、[完整表](results/tables.md)、[JSON](results/summary.json)、[CSV](results/metrics.csv)、[配对变化](results/comparisons.csv)。
- 图：[Recall–QPS](figures/recall_qps.svg)、[相对matched Fast变化](figures/deltas.svg)、[cal候选](figures/cal_recall_qps.svg)。
- 成本：[costs.json](results/costs.json)；执行：[commands.md](commands.md)、[完整调用账](reviews/search_jobs.json)。
- 验收：[输入](inputs/preflight.json)、[恢复](reviews/recovery_gate.json)、[cal门](reviews/cal_gate.json)、[全结果检查](reviews/result_verification.json)、[保护/冻结核验](reviews/immutable_integrity.json)。

所有模型只用fit GT构建，cal选温度/主候选，audit只报告。validation为有历史使用的前2000条；所有画像/选择冻结后才访问，held-out未打开。实验结果目录禁止覆盖；其它方向不是自动执行队列。
