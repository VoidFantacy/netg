# Finite-Beam Reachability v1 独立纠偏审计

## 结论

本轮终态为 **`NO_GO_NOT_LIGHTWEIGHT`**，细分状态为
`TRACE_INCREMENTAL_PASS_COST_ALIGNMENT_FAIL_COMPRESSION_UNTESTED`。

这个终态不表示真实 finite-beam trace 没有信息。相对同容量 geometry baseline，trace selector
在 WebVid、Yandex 的 `L=64/128` 四点上 selected-entry mean utility delta 都为正，query bootstrap
95% CI 下界也都大于 0。但原 Stage D 还要求相对 geometry rank-0 的平均 graph NDC 增幅不超过
`0.5%`，实际只有 WebVid `L=128` 通过，另外三点失败；收益也明显集中在少数 query，pairwise
ordering 仅一点评价改善。因此 Stage D 整体失败，严格按 gate 停止，未进入 Stage E，未读取
validation 或 held-out。

原 `v1/report.json` 的 `NO_GO_TRACE_NOT_INCREMENTAL` 不予接受：它把“trace 的增量解释力”和
“所选入口是否满足成本约束”混成了同一个结论。原文件被保留以维持 provenance；本目录给出
不覆盖的纠偏结果。

## Stage B/C 工程验收

- 两数据集各 20 query、geometry top-3、`L=64/128` 的 traced/native parity：共 240 个 case，
  result IDs、NDC 完全一致，distance 在 `1e-6` 内一致，0 failure。
- 使用相同输入重新运行后，两个数据集各 120 行均与原 smoke trace 逐字段完全一致；WebVid
  row SHA256 为 `fa382c8c...b86de5`，Yandex 为 `d27b3dcb...dc3c0`。
- 完整 pilot 每数据集均为 32,000/32,000 行，无重复 `(query_id, entry_id, L)`；query 范围
  `[0,2000)`，rank `0..7` 与 `L=64/128` 布局完整。
- Recall 从独立 train GT 重算为 0 mismatch；`trace.distance_evaluations` 与保存的 graph NDC
  重算为 0 mismatch；trace 计数不变量为 0 failure。
- benchmark 现会拒绝重复 candidate IDs，并检查 FastRouter 返回的每个 entry 都属于冻结的
  candidate-ID 集合。该检查不改变搜索过程；补丁后的重复 smoke 与旧 smoke 行完全一致。
- 当前 checkout 原本已有大量未提交改动；manifest 的整个源文件 hash 只用于复现，不把无关
  diff 归因于本诊断。

## Stage D：trace 相对拟合 geometry baseline

fit 使用 train 行 `[0,1600)`，audit 使用 `[1600,2000)`；两种 selector 使用同一 closed-form
ridge 容量，trace 版本只增加预注册的过程统计。utility 为
`Recall@10 - 0.05 * graph_ndc / max(fast_top3_graph_ndc, 1)`。

| dataset | L | utility delta [95% CI] | Recall delta | geometry→trace pairwise acc. | 正收益 query | top-10%/正收益总量 |
|---|---:|---:|---:|---:|---:|---:|
| WebVid | 64 | +0.021640 [0.008840, 0.035580] | +2.150 pp | 0.5358→0.5138 | 24.00% | 97.00% |
| WebVid | 128 | +0.014949 [0.003760, 0.027328] | +1.425 pp | 0.5369→0.5153 | 20.75% | 99.17% |
| Yandex | 64 | +0.018345 [0.003530, 0.034803] | +1.775 pp | 0.5082→0.5079 | 21.50% | 99.14% |
| Yandex | 128 | +0.015689 [0.005948, 0.027322] | +1.525 pp | 0.5103→0.5248 | 25.00% | 99.01% |

最大单 entry 选择占比只有 `1.25%–2.25%`，所以不是单 entry 垄断；但 query 贡献高度集中，
不能通过 Stage D 的“非小 query 群贡献”条件。

## Stage D：相对 geometry rank-0 的硬成本 gate

| dataset | L | Recall delta | mean graph-NDC relative delta | `<= 0.5%` |
|---|---:|---:|---:|---:|
| WebVid | 64 | +2.525 pp | +0.924% | FAIL |
| WebVid | 128 | +1.200 pp | -0.193% | PASS |
| Yandex | 64 | +1.900 pp | +1.988% | FAIL |
| Yandex | 128 | +0.875 pp | +1.030% | FAIL |

因此 Stage D 整体为 FAIL，Stage E 不得触发。

## 诊断性 cost-constrained top-8 oracle

只为区分“候选空间无解”和“selector 未学会成本对齐”，在每个 query 的 top-8 中先施加同一个
预注册约束 `NDC(e) <= 1.005 * NDC(rank0)`，再用真实 utility 选最优入口。它使用搜索结果标签，
不可部署，也不计为 Stage E 方法。

| dataset | L | utility delta [95% CI] | Recall delta | mean per-query NDC delta |
|---|---:|---:|---:|---:|
| WebVid | 64 | +0.036058 [0.024207, 0.049729] | +3.125 pp | -8.396% |
| WebVid | 128 | +0.016217 [0.010347, 0.022881] | +1.325 pp | -5.237% |
| Yandex | 64 | +0.024678 [0.014315, 0.037013] | +2.175 pp | -5.202% |
| Yandex | 128 | +0.006712 [0.002512, 0.012731] | +0.500 pp | -3.242% |

观察事实是四点均存在成本可行的正收益入口；尚未验证的是这些入口能否由 query 与少量离线
summary 在搜索前预测。若另立新目标，唯一合理方向是 **cost-constrained reachability
distillation**：trace 只作离线 teacher，先预测硬 NDC feasibility，再预测连续 utility residual；
在线只允许 query、prototype 和少量 entry/mode summary，不允许图 probe。该新目标必须重新
预注册 train-internal gate，不能用本轮 oracle 直接宣称可轻量部署。

## Gate 与访问边界

- Stage A/B/C：PASS。
- Stage D 增量解释力子项：PASS。
- Stage D Recall 子项：PASS。
- Stage D NDC 成本子项：FAIL（3/4）。
- Stage D 非小 query 群贡献子项：FAIL；pairwise 证据也不稳定。
- Stage E：NOT RUN，因 Stage D stop condition 已触发。
- validation：未读取。
- held-out：未读取。
- `spec.md`、`summary.md`：按本目标约束未修改。

