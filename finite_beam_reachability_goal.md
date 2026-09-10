# Finite-Beam Reachability 轻量融合目标与执行计划

> 状态：待执行  
> 执行代理建议：GPT-5.6 Terra  
> 当前授权边界：只实现、运行和报告本文件定义的诊断与条件式 pilot；不修改
> `spec.md`、`summary.md`，不读取 held-out test，不覆盖任何已有 artifact。

## 1. 最终目标

判断并验证：冻结 NSG 的真实 finite-beam 搜索过程中，是否存在能够补充 prototype 几何相似度、
同时又能被压缩为低成本入口表示的 graph-reachability 信号。

若证据成立，产出一个无需在线逐入口 probe 的轻量候选方案；若证据不成立，给出可审计的 no-go
结论，停止该方向。这里的 reachability 特指：给定查询 `q`、入口 `e` 和预算 `L` 时，真实搜索
过程到达高效用结果区域的能力，不是静态图上的无预算连通性。

工作假设：

> 在控制 query–prototype similarity 和 query–raw-entry distance 后，真实 finite-beam 展开中的
> rewind、stagnation、frontier gap 等过程量，仍能解释 query–entry search utility 的残差；这些
> 规律可以由训练 trace 汇总成少量 entry/mode 表示，使在线路由保持轻量。

## 2. 为什么做、为什么不是重复旧实验

- 旧 NETG 对大量 `query × hub` 组合执行真实搜索，以能否命中 top-1 GT 和最小 NDC 生成单一
  hard label。它包含真实搜索可达性，但成本高且丢弃了其他候选、预算和连续效用信息。
- Fast v1 的 QGT-Cover 与 closed-form prototype 很轻，但在线选择主要由几何相似度决定。
- 已完成的 BTG v1 只使用 graph-BFS basin 和聚合边频扩散，Yandex 上 no-go；禁止继续扫描其
  horizon、temperature 或 gamma。
- 已完成的 top-32 sparse utility 静态几何 ranker 跨数据集 no-go；禁止把本任务变成继续调该
  ranker，或扩大为通用 MLP/双塔。
- 已完成的 probe-then-reroute/topology chooser no-go；本任务不得以更多在线 probe 或 resumable
  search 绕过这个结论。

本任务新增的唯一科学变量是：**实际 `search_new` finite-beam 展开过程本身的统计结构**。

## 3. 范围与硬约束

### 3.1 数据与图

- 数据集：`webvid2_5m_light_v1`、`yandex_t2i_official10M_ip_v1`。
- 只用各自独立的 prototype-train 和 validation；禁止读取或推断 held-out test。
- 使用现有冻结 NSG、Fast seed `20260828` 的 hubs/prototypes 和现有 GT；不得重建或修改底图。
- pilot 默认每个数据集 2,000 条 prototype-train queries、Fast geometry top-8 single-entry
  candidates、`L=64/128`、`K=10`。
- 只有 pilot gate 通过后，才允许扩展到预先登记的 validation 10K；不得根据 validation 结果
  返回修改特征、阈值或模型。

### 3.2 成本边界

- 禁止恢复 `query × all hubs` 穷举。
- pilot 上限为 `2 datasets × 2K queries × top-8 × 2 L` 的 single-entry searches。
- 在线候选方案不得执行图 probe；允许的在线工作仅为小型向量索引检索、常数规模聚合和 top-m
  选择。
- 如无法做到无在线 probe，应报告“reachability informative but not lightweight”，不得把它包装
  成本项目主方法。

### 3.3 工作区与产物保护

- 开始前完整阅读 `AGENTS.md`、`summary.md`、`spec.md`，并运行相关 executable 的 `--help`。
- 不清理、reset、删除或覆盖用户工作区、旧日志、旧结果和旧 artifact。
- 新代码优先放在独立 diagnostic 路径；若可行，不改 `ACSG::search_new` 的生产行为。
- 所有输出写入新目录：

```text
finite_beam_reachability_diagnostics/
  v1/
    manifests/
    traces/
    models_or_closed_form_artifacts/
    routes/
    report.json
    analysis.md
```

- 本轮按用户要求不更新 `spec.md`、`summary.md`；留待后续独立验收与同步。

## 4. 指标与数据语义

每个 `(dataset, query, entry, L)` 必须保存原始结果，而不是只保存最终分数：

```text
query_id / entry_id / geometry_rank
prototype_distance / raw_entry_distance
search_L / top_k
result_ids / result_distances
recall_at_10 / graph_ndc
trace_features
```

主 utility 保留分量并在 train-only 阶段冻结归一化方式：

```text
u(q,e;L) = Recall@10(q,e;L)
           - lambda * graph_ndc(q,e;L) / graph_ndc_fast_top3(q;L)
```

- `lambda` 的候选值和最终值只能用 prototype-train 内部划分确定；validation 不参与选择。
- 必须同时报告原始 Recall 和 NDC，不能只报告合成 utility。
- GT 命中、首次命中位置等字段属于监督/诊断标签，不得作为部署时的输入特征。
- 距离统一按当前 `DistanceComputer` 的“越小越优”语义解释；不得自行混用 IP/L2 符号。

建议至少记录以下 trace 统计。若某项与当前算法不相容，应在 manifest 中写明替代定义和理由，
不得静默省略：

1. `expanded_count`：实际弹出并展开的 flagged nodes 数；
2. `evaluated_neighbor_count`：邻居距离计算数，与总 NDC 的关系必须可核对；
3. `accepted_insertion_count` 与 `rejected_by_pool_bound_count`；
4. `rewind_count`：一次展开后 `updated_pos <= current_k` 导致游标回退的次数；
5. `rewind_span_sum/max`；
6. `best_distance_improvement_count` 与归一化 improvement 总量；
7. `max/mean_stagnation_expansions`：连续多少次展开没有改善当前 best distance；
8. `frontier_gap` 的终态及少量固定 checkpoint 值；定义必须基于当前候选池并支持 IP/L2；
9. pool-bound 改善次数和归一化幅度；
10. 首次出现任一 top-10 GT 的 expansion/NDC 位置，仅作为监督标签。

不得默认保存每次搜索的完整 node-ID path，以免生成不可控的大 artifact。只有定位语义错误时才可
对不超过 20 个固定样本保存完整 debug trace，并在报告中说明。

## 5. 行动步骤

### 阶段 A：实现审计与冻结设计

1. 核对 `ACSG::search_new`、`search_on_graph_new`、`bench_entry_oracle` 和现有 sparse utility/
   probe artifact 的真实调用链。
2. 写一份不超过两页的 `v1/trace_design.md`，逐项定义事件、计数时点、距离归一化、线程安全和
   artifact schema。
3. 明确采用“diagnostic-only traced replica”还是“默认关闭的 callback”。优先选择不会改变生产
   搜索热路径的方案。
4. 在任何大于 20 queries 的运行前冻结 trace schema、pilot query 行范围和命令。

阶段 A 验收：设计中每个 feature 都能对应到明确代码事件；明确哪些字段是训练监督、哪些字段
未来在线可用；不存在读取 validation GT 来选 feature 的路径。

### 阶段 B：trace 插桩与语义一致性测试

1. 实现只读 trace 采集模式和独立输出；默认搜索模式行为保持不变。
2. 增加小型确定性测试或固定样本 parity checker。
3. 对两个数据集各不超过 20 queries、top-3 entries、`L=64/128` 做 smoke test。
4. 检查并报告运行时间、峰值 RSS、输出字节数及按完整 pilot 外推的 ETA/磁盘。

阶段 B 必须全部满足：

- traced/untraced 的结果 IDs 完全一致；距离在 `1e-6` 容差内一致；Recall 和 NDC 完全一致；
- 相同输入重复运行的 trace feature 完全一致；
- trace-off 下现有 executable 的行为和输出 schema 不变；
- 所有计数非负且满足代码可推导的不变量，例如
  `accepted + rejected <= evaluated_neighbor_count`；
- 无 held-out 路径出现在命令、manifest 或输出中。

任一 parity 条件失败时立即停止，不运行 pilot。

### 阶段 C：双数据集最小 pilot

1. 使用冻结的前 2K prototype-train queries、geometry top-8、`L=64/128`、`K=10` 生成 trace。
2. 同时保存 geometry-rank-0、Fast-top3 和 Medoid 对照的 Recall/NDC。
3. manifest 至少记录：dataset/artifact version、query/GT/index/prototype/hub-ID 路径与 SHA256、
   build seed、代码 SHA256、query 行范围、shortlist、L/K、线程、CPU、wall time、peak RSS、
   `heldout_accessed=false`。
4. 先在 prototype-train 内固定 fit/tune 划分；所有 feature 定义、归一化、lambda 和判定阈值在
   查看 validation 前冻结。

阶段 C 数据完整性验收：

- 预期 `(query, entry, L)` 行数完整且主键无重复；
- candidate 顺序与现有 Fast router 精确重算的 geometry top-8 一致；
- trace 汇总重算得到的 Recall/NDC 与保存字段一致；
- 两个数据集均有完整 checksum、资源和耗时记录；
- 失败或中断可重入，且不会覆盖已经完成的另一数据集结果。

### 阶段 D：增量解释力 gate

只回答一个问题：trace 是否解释 geometry baseline 不能解释的 utility residual。

1. baseline 只使用 prototype distance、raw-entry distance、geometry rank 和简单 entry prior。
2. trace 版本在完全相同的划分与模型容量下增加阶段 C 的 trace features。
3. 优先使用可解释、低容量方法或闭式统计；不得为了过 gate 扫描大模型或宽超参网格。
4. 同时评估：pairwise candidate ordering、top-1 selected-entry utility、Recall@10、NDC，以及
   query-level bootstrap 95% CI。
5. 分别报告 WebVid/Yandex、`L=64/128`，不得只给合并平均值。

阶段 D 通过条件：

- 两个数据集上 trace 相对 geometry baseline 的 selected-entry mean utility delta 都为正，且
  query-bootstrap 95% CI 下界大于 0；
- 每个数据集的 `L=64` 和 `L=128` Recall@10 均不下降；
- 相对 geometry rank-0 的平均 graph NDC 增幅不超过 `0.5%`；
- 改善不是由 GT-only 字段泄漏、单个 entry、单一 query 小群或一个 L 独占贡献。

如未通过，写 no-go 报告并停止，不进入阶段 E。

### 阶段 E：无在线 probe 的轻量压缩 gate（仅 D 通过后）

目标不是直接训练大路由器，而是验证 trace 规律能否被压缩到在线可用表示。

1. 从训练 trace 构造少量 reachability-conditioned entry/mode summaries，例如按正 utility residual
   和稳定 trace pattern 加权的 query prototypes；具体公式必须在 validation 前冻结。
2. 在线只能用 query 向量、小型索引和这些离线 summaries 选择入口，不能运行图 probe，也不能
  读取 GT 或 trace label。
3. 先在 prototype-train 的未参与构造部分交叉验证；内部成立后才允许一次性运行 WebVid/Yandex
   validation 10K、单 build seed。
4. 与 Medoid、geometry rank-0、Fast top-3 在同一 `L` 下比较，并补等总 NDC口径。

阶段 E 通过条件：

- WebVid、Yandex validation 的 mean utility delta 相对对应 geometry baseline 均
  `> 0.0001`；
- 两个数据集在 `L=64/128` 的 Recall@10 均不下降；
- 平均 graph NDC 增幅不超过 `0.5%`，且加入 routing NDC/latency 后结论不反转；
- 在线额外 artifact 和路由成本有明确记录，且没有逐入口图搜索；
- validation 只执行冻结配置，不根据结果回调参数。

如 D 通过而 E 失败，结论必须写成：`reachability informative but not lightweight/predictable`，
不得宣称形成新方法。

### 阶段 F：结果报告与交付

产出：

1. `finite_beam_reachability_diagnostics/v1/report.json`：机器可读配置、provenance、完整指标和
   gate 状态；
2. `finite_beam_reachability_diagnostics/v1/analysis.md`：结论、逐数据集表、失败分析和下一步；
3. 新增/修改源码列表与逐文件目的；
4. 可复现命令、测试结果、wall time、peak RSS、artifact bytes；
5. 明确终态之一：
   - `NO_GO_TRACE_NOT_INCREMENTAL`
   - `NO_GO_NOT_LIGHTWEIGHT`
   - `GO_LIGHTWEIGHT_REACHABILITY`

报告必须区分观察事实、统计推断和机制假设。不得把单 seed pilot 写成正式结果，不得把
reachability gate 的通过等同于完整论文方法成立。

## 6. 整体完成标准

只有同时满足以下条件，任务才算完成：

- 阶段 A/B/C/D 已完成，或者在预定义 stop condition 处正确停止；
- 若 D 通过，则阶段 E 已完成或给出可复现的技术阻塞证据；
- 代码测试和 trace parity 全部通过；
- 两个数据集均按相同协议处理，没有只保留有利数据集；
- 没有读取 held-out、修改冻结图或覆盖既有 artifact；
- `report.json`、`analysis.md`、manifest、命令和源码修改齐全；
- 给出唯一明确的 go/no-go 终态，而不是只罗列结果；
- 留出 `spec.md`、`summary.md` 待办，但本轮不修改它们。

## 7. Terra 执行时的停机与汇报规则

- 发现代码语义与本文件、`spec.md` 或 `summary.md` 冲突时，先报告证据，不自行改实验定义。
- 预计运行超过 10 分钟时使用独立日志与结果路径；启动后观察约一分钟，按真实吞吐报告 ETA。
- 同一错误连续出现三次，或需要扩大到 all-hub、held-out、改图、在线多次 probe、大模型时停止，
  向用户说明所需的新授权。
- 不因剩余时间或算力充足而跳过 gate；后续阶段只能由前一阶段通过触发。

