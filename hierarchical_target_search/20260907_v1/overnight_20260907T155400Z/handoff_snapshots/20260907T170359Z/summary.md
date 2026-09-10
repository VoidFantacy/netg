# NETG / ACSG 当前研究总结

> 最后核对：2026-09-07。本文件回答当前研究主线、证据边界与阶段决策。实现与复现契约见 `spec.md`；长期计划、阶段 gate 与接续台账见 `s-target.md`。

## 1. 当前方法

### 当前研究主线：目标邻域驱动的分层搜索

新长期计划联合设计覆盖全部 base 的目标区域、查询到目标区域占比的层次预测、以及固定总容量下的区域候选保留。先冻结 NSG，先做 P2 机制证伪，再按 gate 构建完整结构和学习模块。用户已于本次夜间会话明确恢复研究授权；已通过 P0/P1，接续 P2。当前版本 `hierarchical_target_search/20260907_v1` 的 P0/P1 已通过，尚无新方法性能结论。

依赖已准备：METIS v5.2.1/i64、GKlib、独立基线 Python 环境、kRt/gp-ann MIPS 构建、RoarGraph 和局部 MKL；复用现有 GATE 适配。依赖检查通过不代表方法有效。依赖准备轮没有真实数据实验；本次夜间搜索测试与P2初测已完成，证据另立日志。交接见版本目录 `dependencies/README.md`，恢复提示词见 `overnight_prompt.md`。本方法保持全 CPU。新对话的方法开发和实验截止为北京时间 2026-09-08 07:00；停止后整理 `实验总结.md`，首段简洁概括整晚成果，后文详细给出证据、阶段判断和下一步，不能为补报告继续实验。

先在 64 个图结构区域上固定门户和路由，比较统一池、均匀区域池、概率容量区域池，并用 train-only oracle 分离结构与预测问题。完整候选为 16×16 层次区域；不是旧 Multi-view、静态 utility ranker 或 probe-reroute 的续跑。若证据明确指向连接瓶颈，才进入独立辅助图分支。

拟合只用 router_train 后 20K，前 10K 为已有历史使用的开发 pilot；paired Fast 也重建 20K prototype。旧 30K Fast 单列参考。双数据集均须在至少两个相邻工作点达到同 Recall QPS ≥+10%，或同 QPS Recall@10 ≥+1 pp，并有校正区间支持；P6/P7 才确认性能。实现成功和 pilot 通过均不代表项目完成。

### Fast v1：已验证基线

Fast v1 是 `QGT-Cover + closed-form GT-basin prototype + Micro-HNSW top-3`：先用独立 5K QGT 查询及 exact top-100 GT 选真实 base hubs，再用独立 30K 查询的 top-1 GT basin 形成每个入口的“查询画像”（prototype），在线选 top-3 入口搜索冻结 NSG。

它依赖 exact train GT，但不依赖 ACO、DPC、逐 hub probe labels、optimizer 或 MLP，也不修改底图。QGT-Cover 是项目内启发式命名，不是严格 set cover。

### 已结束扩展：Multi-view Target-Basin Routing

`Multi-view Target-Basin Routing` 把三个独立初始化的 Fast build 当作三个 prototype views：保留第一 view 的 rank-0 anchor，合并三路 top-8 候选并选两个补充入口，最终仍以 top-3 搜索同一 frozen NSG。

设计假设是多个 QGT 划分能提供互补候选，anchor 能限制主入口漂移。三个 views 合起来只算一个模型；随机 build seed 不是独立 task，也不是 query bootstrap，因此本方法不能称为元学习。该扩展已在正式化 E1b 因路由成本失败，不再是当前待验证方法。

## 2. 已确认结果

### Fast v1

- WebVid held-out：Fast 在已测预算上优于旧 Formal Neural Router。
- Yandex official 10M/IP held-out：Recall 基本等效，主要优势是 Medoid-normalized QPS。
- LAION validation 与 held-out 已完成；但 LAION 与 WebVid public query 源文件相同，只能证明跨 base corpus/scale 迁移，不能算独立第三 query workload。
- 现有 `build_wall_seconds` 只覆盖已有 exact GT 后的入口构建。完整成本必须报告 `T_exact-GT + T_QGT + T_prototype + T_router-index`，不能把秒级数字称为完整训练。

权威结果：`fast_entry_benchmark_results/benchmark_summary.md` 与 `fast_entry_variants/laion10m_acsg_v1_{validation,heldout}_report.md`。

### Three-view：同 L 有收益，但部署成本 NO-GO

旧 `28/29/30` 单组模型在 WebVid/Yandex validation 10K、Recall@10、`L=64/128` 四点均优于 seed-20260828 Fast：

| 数据集 | L | Python reference Recall delta | graph NDC delta | C++ Recall delta |
| --- | ---: | ---: | ---: | ---: |
| WebVid | 64 | `+0.871 pp` | `-2.278%` | `+0.822 pp` |
| WebVid | 128 | `+0.369 pp` | `-1.388%` | `+0.340 pp` |
| Yandex | 64 | `+0.250 pp` | `-1.709%` | `+0.214 pp` |
| Yandex | 128 | `+0.209 pp` | `-0.992%` | `+0.148 pp` |

这证明当前路由在同 L 下有质量潜力，但不证明部署收益。正式化结果如下：

1. 旧 E0 的 16 项检查通过，覆盖路由／搜索 parity、真实 anchor 和 count/timing 接口分离；后续源码审计发现整批计时仍包含 GT 评分，不能将旧 E0 解释为 wall 计时边界已完全合格；
2. E1 dense 在双数据集 train-1K 上仅 routing NDC 就超过 paired Fast L64 总预算；
3. E1b 固定后两路 `M16/efConstruction200/efSearch32` Micro-HNSW，在 train-10K 将 mean routing NDC 从 WebVid `1760.299` 降到 `642.337`、Yandex `1766.112` 降到 `549.376`，anchor mismatch 均为 0；
4. 等 total-NDC 匹配后，WebVid L64/L128 目标的 Recall@10 分别比 Fast 低 `14.697/4.960 pp`，Yandex 低 `4.103/1.463 pp`，四点全 FAIL。

因此总决策为 `NO_GO_ROUTING_COST`。等 NDC 与等 wall 是合取 gate；前者已失败，计时不能逆转结论，故未运行。E2–E4、tail、独立构建和 held-out 均按规则 `NOT_RUN`。证据：`target_basin_formalization/20260907_v1/{gate.json,report.md}`。

## 3. Claim 边界

- 可确认：三个旧 view 在同 L 下有小幅 graph-search Recall 收益；固定 HNSW-all 后端能大幅降低 dense routing NDC，并逐 query 保持 anchor。
- 不可确认：总成本收益、tail 改善、跨独立构建稳定性、多视角互补因果或 held-out 泛化；这些阶段未获执行授权。
- 不能把失败解释成 HNSW top-8 完全失真：后两 view 对 scalar-float exact top-8 的集合 recall 为 WebVid `0.9873/0.9883`、Yandex `0.9972/0.9976`。真正瓶颈是剩余 routing NDC 挤占 graph-search 预算。
- GATE 已覆盖“冻结图上的 query-aware entry navigation”。本结果不能包装为新的通用路由范式、tail-risk 优化或元学习。

## 4. 已停止方向

- confidence attention：WebVid/Yandex 需要相反 alpha；当前共享-alpha 公式 train-only no-go。结论只针对该公式，不能外推为所有 attention 或元学习无效。
- static utility ranker、probe-reroute、graph-BFS Basin Transition Graph、residual basin modes：已跨数据集或 validation 失败，不再扫同类参数。
- finite-beam trace：trace 有增量信息，但成本／收益集中性不通过；后续 cost-first distillation 的四点 utility CI 均跨零。不得误写成“trace 没有信息”或数学上不可预测。
- 旧 NETG 已用真实 graph reachability；不能把 reachability 本身写成当前创新。

旧分支的实现、表格和诊断保留在 `aco_router_fast_entry.md`、`finite_beam_reachability_diagnostics/`、`probe_reroute_results/` 和其他对应 `*_diagnostics/`，不在本总结重复展开。

## 5. 当前决策

旧 Multi-view 批次按 gate 终止，E2–E4 不是欠账，不续扫 HNSW。新方法依赖准备已完成，用户已恢复夜间研究授权，当前按 `s-target.md` 的 P0→P1→P2 完成输入、测量和机制审计；只有通过对应 gate 才进入后续阶段。恢复后优先可靠搜索对照和真实 wall 测量，不提前训练完整模型。

## 6. 不可破坏边界

- 旧 Multi-view 不再运行 E4；新方法 held-out 仅在 P6 通过且方法冻结后执行。
- 冻结 NSG、base、metric、normalization、query split 与 GT 不变。
- 新 artifact 隔离保存并记录 checksum、seed、代码、线程和成本，不覆盖历史结果。
- 三个 views 是一个 ensemble；三个 timing runs 不是三个独立 Recall 样本。
- 任何实验定义或结论变化都同步更新 `spec.md` 与本文件。

## 7. 证据入口

- 实现与复现：`spec.md`
- 本批协议与终局：`s-target.md`
- Fast：`fast_entry_benchmark_results/benchmark_summary.md`
- Three-view：`target_basin_ensemble_diagnostics/v1/decision.json`
- Multi-view 正式化终局：`target_basin_formalization/20260907_v1/{gate.json,report.md}`
- Confidence no-go：`target_basin_meta_diagnostics/v1/decision.json`
- GATE：`gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md`
- 历史诊断：`aco_router_fast_entry.md` 与对应 `*_diagnostics/`

### 本次夜间接续（更新于北京时间 2026-09-08 00:45）

本轮产物位于 `hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/`。用户已恢复全 CPU 自主研究授权；`control/taskctl.py` 保存独立进程组、命令、启动身份、日志、超时和资源，watchdog 于06:59关闭研究任务、07:00硬截止，随后仅整理报告。所有原有产物保留；旧 Fast 默认源码未改。

P0/P1 已 PASS：完整输入 SHA、split 隔离、图内 base 抽样核对；搜索合成和 sanitizer、两数据集512 pilot查询×L64/128的结果/NDC/新纯wall一致性、m4/6/8实际入口消费均通过。新 evaluator 使用配对20K Fast、纠正 HNSW入口顺序；同入口搜索核与legacy parity不等于旧端到端Fast入口顺序相同。

P2 两数据集10K development pilot已完成独立count、5轮纯wall、预选0..15查询trace（注册23条中只运行16条子集）。64图区域满足严格1.2容量，2门户/区和区域画像仅用20K fit。METIS内部额外容差曾令WebVid12区各超2节点；保留失败产物，补偿库内容差后硬上限通过，未放宽门槛。分区时间27.78/171.64秒，不含exactGT。

真实预测下，区域概率池相对同路由统一池在WebVid L64/128退化5.431/3.640 pp、Yandex退化6.867/3.488 pp，且更慢。oracle同路由区域池分别提高5.413/5.252 pp与3.155/3.359 pp，但仍付出额外wall和NDC。所有真实方法在当前两点均被paired Fast支配，**当前没有有效端到端性能改善证据**。证据为 `p2/analysis_v1/{analysis.json,report.md}`；10K配对bootstrap区间是探索性普通95%，5轮计时不是5个独立Recall样本。

当前 `P2_REVIEW`：轨迹竞争重建与区域预测缺口诊断正在补齐。P2 gate尚未通过，P3–P8未开始；validation/held-out未读取，未触发辅助图。下一行动是完成两项诊断后按原机制gate作决定，不能用oracle优势替代部署性能门槛。更详细的失败历史、命令和阶段状态见本轮 `ledger.md`、`control/jobs/` 与版本 `state.json`。
