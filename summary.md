# NETG / ACSG 当前研究状态与下一步

> 最后核对：2026-09-04。实现与 artifact 契约见 `spec.md`；本文件只保留当前方法、有效证据、
> 停止边界和下一步。

## 当前方法

当前应以 **Multi-view Target-Basin Routing** 作为 Fast v1 的中等容量扩展：

1. 每个独立 QGT/GT-basin build 都形成一套 entry 的“查询画像”（prototype view）。
2. seed-20260828 Fast 的 rank-0 入口保持不变，作为保守锚点。
3. 三个 view 各提供 top-8 候选，重复 entry 按最高 prototype cosine 合并。
4. 从并集选择另外两个入口，在冻结 NSG 上执行原搜索；在线不读取 GT、probe label 或 held-out。

它不是为了显得复杂而增加延迟。三个独立 view 是对 target basin 的三个估计，候选并集用于减少
单次 QGT 划分遗漏；anchor 防止主入口漂移。相对 Fast，prototype 容量约为 3 倍、候选上限由
单路 top-3 扩展到三路 top-8 并集，仍不修改底图。

当前不能称它为“元学习”。它与图中 metric-based prototypical network、memory/attention 有概念
联系，但没有足够多的独立 task 支撑 MAML/Reptile 式 task distribution；随机 build seed 也不能
伪装成不同任务。

## 最新结果

### Three-view ensemble：GO

train-first 规则冻结后，WebVid/Yandex 的 10K validation、Recall@10、`L=64/128` 四点均优于
seed-20260828 Fast：

| 数据集 | L | Recall delta | graph NDC delta |
| --- | ---: | ---: | ---: |
| WebVid | 64 | `+0.871 pp` | `-2.278%` |
| WebVid | 128 | `+0.369 pp` | `-1.388%` |
| Yandex | 64 | `+0.250 pp` | `-1.709%` |
| Yandex | 128 | `+0.209 pp` | `-0.992%` |

C++ 在线实现复验仍四点同方向：Recall delta 为 WebVid `+0.822/+0.340 pp`、Yandex
`+0.214/+0.148 pp`；16-thread 批量 routing 有效 wall 开销为 WebVid `52.3 µs/query`、
Yandex `19.1 µs/query`。这些结果证明路由质量，不等于正式 total-NDC/端到端 latency 结论。

artifact：`target_basin_ensemble_diagnostics/v1/decision.json`。

### 元学习启发的 confidence attention：NO-GO

测试了 `score_v(q,e) + α·(top1_v-top2_v)`，其中 `α=0` 精确复现当前 ensemble；只在
`drl_train` 上比较 `α∈{-2,-1,-0.5,0.5,1,2}`。

- WebVid 仅 `α=-0.5` 通过两预算；
- Yandex 仅相反的 `α=+0.5` 通过两预算；
- 没有共享非零 α 同时通过双数据集 gate。

因此停止 confidence attention，不读取 validation/held-out，不引入 MAML、Reptile 或
“meta-learning”宣传。保留无校准的 hard max merge，说明跨 view 置信间隔并不是可迁移的
reliability signal。

artifact：`target_basin_meta_diagnostics/v1/decision.json`。

### 待 Astra 复核：本次做法与判断依据

输入思路来自元学习的三类常见路线：model-based memory/attention、optimization-based
MAML/Reptile、metric-based prototypical learning。本次没有直接套用“元学习”名称，而是先按
当前实验条件做映射：

1. 当前 GT-basin prototype 本身已经是 metric-based prototype；three-view ensemble 可理解为
   三套独立 prototype memory，但这只是结构类比，不构成元学习贡献。
2. 只有 WebVid、Yandex 两个独立 workload，不足以定义 MAML/Reptile 所需的 task
   distribution；build seed 只是随机重复，不能当作新任务，因此未实现梯度型 meta-learner。
3. 唯一直接可证伪的增量是 query-adaptive view attention：用每个 view 的
   `top1-top2` cosine margin 表示该 view 对当前 query 的置信度，并加入候选分数。

具体冻结公式为
`s'_v(q,e)=s_v(q,e)+α·(s_v(q,e_1)-s_v(q,e_2))`。保持 seed-20260828 rank-0 不变，
三个 view 各取 top-8、重复 ID 取最大调整分数，再选两个补充入口。`α=0` 与当前 ensemble
route 逐字节一致；非零 `α` 只在双数据集 `drl_train` 10K、Recall@10、`L=64/128` 上评估。
继续条件是同一非零 `α` 在四个点均不降低 Recall 和冻结 utility，且 route-set 变化至少 1%。

实测出现跨 workload 符号冲突：WebVid 偏好降低高 margin view 的权重（`α=-0.5`），Yandex
偏好提高它（`α=+0.5`）。因此结论限定为：**当前 cosine margin 不是可迁移的 view reliability
估计，attention 变体 no-go；不否定拥有足够多真实任务时的元学习。** Astra 复核时应重点检查：
任务定义是否充分、margin 作为置信度是否合理、共享 alpha gate 是否过严，以及是否存在不读取
held-out且不把 seed 当 task 的更合理 episodic 构造。

## 既有基线与边界

- Fast v1 是 `QGT-Cover + closed-form GT-basin prototype + Micro-HNSW top-3`，依赖 exact
  train GT，但不依赖 ACO/DPC/probe labels/optimizer/MLP。
- Fast 在 WebVid held-out 明显优于旧 Neural Router；Yandex held-out 的 Recall 基本等效，
  主要优势是 QPS。LAION/WebVid public query 相同，LAION 不是独立第三 workload。
- 现有秒级 `build_wall_seconds` 只是已有 exact GT 后的构建时间。完整成本必须报告
  `T_exact-GT + T_QGT + T_prototype + T_online-index`，不得把秒级数字称为完整训练。
- static utility ranker、probe-reroute、topology reroute、graph-BFS Basin Transition Graph 和
  residual basin modes 已跨数据集或 validation 失败，不继续扫参数。
- 旧 NETG 已经使用真实 graph reachability；不能把 reachability 本身写成新贡献。

## 下一步

只推进 three-view ensemble 的正式化，不再增加模块：

1. 构建三组彼此独立的 three-view ensemble，验证收益不是当前 `28/29/30` 组合偶然产生。
2. 补 Recall@1/10/100、rescued/newly-harmed、P1/P5、bottom-CVaR。
3. 计入 routing NDC、routing latency、graph cost 和 GT-inclusive offline cost，做等 total-NDC 与
   等端到端 latency 比较。
4. 上述 P2 gate 冻结并通过后，才允许一次 held-out；held-out 结果不得返回调参。

## 不可破坏边界

- train/validation 用于选方法；当前新实验不得读取 held-out。
- 冻结 NSG、base、metric、normalization、query split 与 GT 不变。
- 新 artifact 使用隔离目录并保存路径、checksum、seed、线程和成本；不覆盖历史结果。
- three-view 的三个 seed 是一个模型的三个 view，不等于三次独立方法重复。

## 当前证据入口

- 实现规格：`spec.md`
- Three-view ensemble：`target_basin_ensemble_diagnostics/v1/`
- Meta-inspired no-go：`target_basin_meta_diagnostics/v1/`
- Fast 正式结果：`fast_entry_benchmark_results/benchmark_summary.md`
- GATE：`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`
- 历史 reachability/utility/reroute 诊断：对应 `*_diagnostics/` 与 `probe_reroute_results/`
