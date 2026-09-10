# NETG / ACSG 当前研究总结

> 最后核对：2026-09-07。本文件回答当前研究主线、证据边界与阶段决策。实现与复现契约见 `spec.md`；长期计划、阶段 gate 与接续台账见 `s-target.md`。

## 1. 当前方法

### 当前研究主线：目标邻域驱动的分层搜索

新长期计划联合设计覆盖全部 base 的目标区域、查询到目标区域占比的层次预测、以及固定总容量下的区域候选保留。先冻结 NSG，先做 P2 机制证伪，再按 gate 构建完整结构和学习模块。用户已于本次夜间会话明确恢复研究授权；已通过 P0/P1/P2机制gate；P3结构与门户完整pilot完成但搜索收益gate为NOPASS，三项有界失败诊断也已完成。当前版本 `hierarchical_target_search/20260907_v1` 没有有效端到端性能改善证据，真实P2路由退化、oracle有潜力但更慢。

依赖已准备：METIS v5.2.1/i64、GKlib、独立基线 Python 环境、kRt/gp-ann MIPS 构建、RoarGraph 和局部 MKL；复用现有 GATE 适配。依赖检查通过不代表方法有效。依赖准备轮没有真实数据实验；本次夜间已完成搜索/计时验收、P2/P3完整pilot及失败诊断，证据另立日志。交接见版本目录 `dependencies/README.md`，恢复提示词见 `overnight_prompt.md`。本方法保持全 CPU。新对话的方法开发和实验截止为北京时间 2026-09-08 07:00；停止后整理 `实验总结.md`，首段简洁概括整晚成果，后文详细给出证据、阶段判断和下一步，不能为补报告继续实验。

P2已运行64个图结构区域、每区2门户，比较统一池、均匀区域池和概率容量区域池。P3已运行16×16区域、每叶3门户共768，oracle全局选4叶区；oracle读取开发pilot真实GT区域占比，仅作诊断，不是可部署路由。P4层次线性预测尚未启动。本主线独立于旧 Multi-view、静态 utility ranker 和 probe-reroute。若证据明确指向连接瓶颈，才进入独立辅助图分支。

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

这证明该历史三view配置在同 L 下有质量潜力，但不证明部署收益。正式化结果如下：

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

旧 Multi-view 批次按 gate 终止，E2–E4 不是欠账，不续扫 HNSW。新方法依赖准备已完成，用户已恢复夜间研究授权，已按 `s-target.md` 通过 P0/P1/P2，P3固定结构与门户诊断已完成但搜索收益gate未通过；门户暴露、目标泛化、实际局部目标尺度诊断及完整23查询trace均已完成。当前整理既有证据和截止报告，P4预测模型不启动。

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

### 本次夜间接续（核对于北京时间 2026-09-08 02:56）

**P3 NOPASS，当前无有效端到端性能改善。** P0/P1/P2和P3新增256叶区实现验收通过；P2真实区域保护在双数据集退化，oracle虽有Recall潜力但更慢，因而仅获一次表示修订进入P3。P3训练结构改善没有传递成预定搜索收益：主对照oracle_probability下λ1_greedy3−λ0_greedy3，WebVid L64/128为−0.866/−0.790 pp，两个普通95%区间均为负；Yandex−0.095/−0.017 pp，区间含0。完整数值、CI及证据见[当前研究判断](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/current_findings.md)和[P3 gate](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P3.json)。

三项诊断已完成：所有8格的实际入口集合均改变，排除“新门户没进入实际route”；WebVid pilot的目标集中度有部分传递（top4区域目标比例M4 +1.808 pp），但Recall损失主要来自fit见过的目标，不能全部归因于unseen；Yandex M4变化−0.004 pp。M4不是Recall上界，seen是base目标ID在fit GT10出现，不是查询重叠。实际邻接审计证实两数据集全部fit目标满足d(u)·9Q<M的严格条件；这说明当前目标量级足以让可行的净GT分散改善移动降低J，但不证明该移动存在、实际被选中或导致检索退化。完整限制与独立复核见当前研究判断。

固定23查询trace全部补齐，460条trace/276配对重放通过；原P2 gate保留决策时16条证据，[完成补充](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/trace_completion_addendum_v1.json)说明后续覆盖。8个门户对照的普通95%区间均含0，不证明等效；五轮计时不是五个独立Recall样本。Fast部分frontier计数未测量，不能把占位零当成实测。

P4–P8、validation性能评测和held-out均未启动，没有辅助图触发证据；机制修订计数仍1，不调λ、不重开本版本P3。下一次最高优先项是审查“目标更集中却丢seen命中”反例下的方法目标与有限容量搜索是否一致，先形成可证伪小gate再决定新版本。当前无重任务，截止保护仍运行，实时身份/资源见[控制台账](hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/control/watchdog_status.json)。07:00核验停止后才创建《实验总结》；到时停止不等于长期研究目标完成。
