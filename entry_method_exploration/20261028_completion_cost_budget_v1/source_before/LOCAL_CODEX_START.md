# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，核对HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–187及本次整理主要为本地未提交工作，HEAD/旧远端快照不包含这些完整产物；新对话应使用同一工作区。E187已完成，没有待恢复矩阵。

## 先读什么

1. [AGENTS.md](AGENTS.md)：文档职责、数据/历史保护及实际单线程约定。
2. [summary.md](summary.md) → [spec.md](spec.md) → [s-target.md](s-target.md) → [s-experiment.md](s-experiment.md)。
3. [本次费用结论与接续快照](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/conclusion_zh.md)：方法、关键数字、证据边界和未实施的下一步。
4. [E187报告](entry_method_exploration/20261028_adaptive_completion_pilot_v1/report_zh.md)、[六页PDF](entry_method_exploration/20261028_adaptive_completion_pilot_v1/ACSG_自适应残差补全_实验对比_20261028.pdf)、[52点](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/points.csv)、[预算对照](entry_method_exploration/20261028_adaptive_completion_pilot_v1/analysis/discrete_comparisons.csv)、[核验](entry_method_exploration/20261028_adaptive_completion_pilot_v1/reviews/results_audit.json)。旧方案从历史索引进原卡片、协议、配置、结果与修正。

## 本次讨论收敛的判断

**新区域方案能补到旧源外遗漏，但每增加一点召回，访问成本过高，未取得完整Recall–QPS改进。** 固定L200：COCO REG-R增Recall0.2349pp、平均完整耗时增29.30%；Deep增0.4821pp、耗时增62.60%。Deep救回4821个成员中4794个在旧训练残差源外，源外可达已有证据；Deep不使用学习模型的REG-NN仍增耗时54.60%。

旧B32有另一类限制：Deep只增Recall0.0021pp、耗时增3.51%；COCO增1.3715pp、耗时增5.70%。不能把全部残差问题归结为执行慢；需要同时看有效候选量和费用。耗时增幅按`QPS_GT10/QPS_method−1`算，不等于QPS降幅。

默认保留E99 GT10（WebVid soft-t1 / Yandex hard）。E187为原46点加6个独立冻结GT10控制，合计52点/156轮；18个区域点均有扩大L的GT10同时覆盖Recall与QPS。原窗口覆盖15点，另外3点使用后补控制，时间窗口/频率/缓存漂移限制保留。

## 哪些仍未做

已有完整wall与REG扫描/精算计数，尚未有粗路由、PQ扫描、精算等分段耗时，不能指定最大单项瓶颈。下一步优先讨论分段计时、硬访问预算、主搜索信息复用、成本感知实际救回目标、允许不补全；这些均未实施、未测试，不自动启动。

当前实现为全base1024区域/global PQ，GT10后从8个近区域选2个、完整扫码、最多96精算合并。REG-NN取最近、REG-Q看query/区域、REG-R加原结果摘要；没有完整统一动作选择器、硬扫描预算或显式流形估计。

E187仅COCO/Deep真实K100、历史曝光测试；无新盲确认，K1/其余五集未测该新来源。七集两K读E183，几何关联读E184/E185，不作流形因果或新数据净收益准入器。失败始终为单query Recall@100<10%（0–9命中），改善、脱离、成员救回分开。

## 可复制的接续提示词

```text
请接续/data/netg/ACSG。先只读核分支和HEAD，再读LOCAL_CODEX_START.md、AGENTS及四份主文档，沿入口读20261028_completion_cost_handoff_v1/conclusion_zh.md。
当前结论：E187新区域补全能救回旧训练残差源外目标，但单位新增召回成本过高；Deep旧B32另有有效候选不足。E187已完成52点/156轮，两集真实K100；18个区域点被更大L GT10覆盖，默认仍E99 GT10。测试已曝光，后补控制时间窗口不同，未做分段计时或完整动作开关。
请先总结证据与限制，再提出分段计时、硬访问预算、信息复用和成本感知补全的验证方案。保留严格Recall@100<10%的失败定义，完整单线程wall对照附近更大L。现阶段只读理解和方案讨论，不自动重跑、训练、恢复队列、修改默认或改写旧封存；后续按我在新对话中的明确任务继续。
```

## 交接维护

[本次快照与验证](experiment_history/_maintenance/20261028_completion_cost_handoff_v1/README.md)记录文档变化，无新ANN/GT/训练/QPS。E187旧交付收据中的根文档SHA只代表当时版本，本次更新另留收据；不要回跑旧finalize来覆盖封存身份。原大数据/GT/图/静态库/对象仍为本地重跑依赖。
