# ACSG / Fast-Entry 相关工作检索与明确改进方向

> 检索日期：2026-08-29。范围限定为与 cross-modal/OOD 图 ANNS、query-aware entry、tail hardness 和多路冗余直接相关的原始论文。当前工作区实测与 artifact 以项目 `spec.md`、`summary.md`、`aco_router_fast_entry.md` 和 `fast_entry_benchmark_results/` 为准。

## 结论先行

当前 `QGT-Cover + closed-form GT-basin prototype` 已经是一个有价值的强起点，但单独作为新方法还不足以支撑 A/B 类投稿：GATE 已在 KDD 2025 明确占据“冻结图 + query-aware hubs + learned entry navigation”这一位置，RoarGraph/RobustVamana 又占据“用历史 query 改底图”的位置。仅强调“不用 ACO/神经网络、构建快约 500 倍”容易被评价为对现有 query-aware hub routing 的工程简化。

建议唯一主线是暂名 **TailRisk-Cover：冻结图上的风险约束、互补多入口覆盖**。它不再学习单一 oracle hub，也不再以 query 几何聚类作为目标，而是在固定 hub 数和在线 NDC/latency 预算下，直接优化 hard-query tail risk，并显式降低多个入口的相关失败。QGT-Cover 保留为初始化和强消融，不再作为最终创新本体。

## 已下载论文

| 文件 | 发表信息 | 与本项目的关系 |
| --- | --- | --- |
| `GATE_KDD2025_arXiv2506.15986.pdf` | KDD 2025, DOI `10.1145/3711896.3736930` | 最接近的 learned entry router，必须主比较 |
| `RoarGraph_PVLDB2024.pdf` | PVLDB 17(11), 2024 | query-guided graph reconstruction，OOD 强基线 |
| `OOD-DiskANN_WWW2023_arXiv2211.12850.pdf` | WWW 2023 | RobustVamana，用少量 OOD query 改图 |
| `Steiner-Hardness_PVLDB2024.pdf` | PVLDB 17(13), 2024 | 图原生 query hardness，可做独立分层和 tail 评测 |
| `SOAR_NeurIPS2023_arXiv2404.00774.pdf` | NeurIPS 2023 | “互补而非重复”的多路冗余设计启发 |
| `Dynamic-Hardness_arXiv2510.22316.pdf` | arXiv 预印本，发表状态未确认 | 最新竞争方向：在线检测并修复两阶段图缺陷 |

PDF 合计约 17 MiB。SHA-256：

```text
a27be6601997e4a6aaad859e56acb1ccacaa50706af2ccb5e5686178e06df6c5  Dynamic-Hardness_arXiv2510.22316.pdf
bb291e267eccd8be8bd684c729eb85c274653e3cbcbf3f6d3b413cfccc4db023  GATE_KDD2025_arXiv2506.15986.pdf
d70918ea7ee74fa70d2672c3f4e2bec09cd735f0fadb51d3d82103bfcfd00d1a  OOD-DiskANN_WWW2023_arXiv2211.12850.pdf
2638cc472fc30cd50b8e20fc42c15833150b0dc799e005da44c76f93c95b36f2  RoarGraph_PVLDB2024.pdf
f19137e00eae6c0ae51ad930693577361533514131371f14c59e1dfcc1788a85  SOAR_NeurIPS2023_arXiv2404.00774.pdf
27f83dabdc5eb0eaea15dae0ce1d4856e086ad05c96d63abbbc694ba121f1f2a  Steiner-Hardness_PVLDB2024.pdf
```

## 方法比较

| 方法 | 是否改底图 | 历史 query 如何进入方法 | 在线机制 | 优化目标 | 对 TailRisk-Cover 的约束 |
| --- | --- | --- | --- | --- | --- |
| GATE | 否 | 对每个 query×hub 从 hub 搜索 top-1，以 hop 阈值产生正负样本 | 在 512 个增强 hub 上建高层图并选入口 | 平均 QPS/路径长度、单入口适配 | query-aware hub 和双塔不是新颖点；必须比较相同冻结图和相同预算 |
| 当前 Fast-Entry | 否 | 5K query 的 exact top-100 GT 生成 hubs；30K top-1 GT basin 生成闭式 prototype | Micro-HNSW 取 top-3，再搜冻结 NSG | query 几何覆盖和 GT-basin 均值 | 极快但未直接优化搜索 utility/tail；exact train GT 成本必须计入 |
| RoarGraph | 是 | 构造 query-base 二部图，再投影为 base-only 图并增强连通 | 直接搜索重建后的图 | OOD 邻域可达性与整体 QPS–Recall | 是端到端 OOD 强基线；不能只在弱 NSG 上和自己的入口层比较 |
| RobustVamana | 是 | 将少量 OOD query 临时放入构图过程、连接 base，再移除 query | 搜索改造后的 Vamana | OOD 平均 latency/recall | 代表低成本 query-guided graph repair；用于判断入口层与改图的边界 |
| Steiner-Hardness | 否 | query/GT 与代表图计算连接难度 | 不改变搜索 | 与真实 query effort 的相关性、公平分层 | 用它或等价图原生指标预先定义 hard decile，避免按本方法结果挑 tail |
| SOAR | 属于分区索引冗余 | 利用训练 query/残差使第二分区补偿第一分区失败 | 搜多个互补分区 | 降低相关漏检 | 启发 top-m entry 不能只是相似度前三，而应优化条件边际收益 |
| Dynamic-Hardness | 是 | 以 Escape Hardness 识别入口到邻域、邻域内部两阶段缺陷 | RFix + NGFix 动态修图 | 检测并修复 query hardness | 说明“hardness-aware”四字本身也不够，必须把冻结图、风险目标和多入口互补讲清楚 |

### GATE 的关键差异

GATE 使用 HBKM 将 base 分成平衡簇，取离质心最近的 base node 作为 hub；对每个 hub 采样多跳子图并用 Graph2Vec 表达拓扑；随后对每个历史 query 从每个 hub 搜索 top-1，以 hop count 阈值形成正负 query；最后用多头注意力融合 hub/node topology、再以双塔对比学习对齐 query 与 hub，并在增强 hub 上建立余弦高层图。论文默认 `|V|=512`、训练 200 epochs，样本生成复杂度明确为 `O(|Q||V|S)`；主指标是 QPS、Recall 与平均路径长度，而不是逐 query CVaR 或 harmed/rescued。

当前 Fast-Entry 的独特事实是构建端极简，且在 WebVid 上已经优于原 Neural Router；但它与 GATE 的概念重合仍很大：都是在冻结 NSG 上用历史 query 生成候选入口表示，再通过一个小型导航图选择入口。可发表差异必须来自优化问题和可验证的机制，而不是“我们的 encoder 更简单”。

## 明确改进：TailRisk-Cover

### 1. 问题定义

给定冻结底图 `G`、独立 train queries `Qtr`、候选 base entries `C`、hub budget `B`、在线入口数 `m` 与搜索预算集合 `Lset`，学习：

1. 一个 hub 子集 `H ⊂ C, |H|≤B`；
2. 每个 hub 的轻量 query-side prototype；
3. 一个返回 `m` 个互补入口的 router。

对训练 query `q` 和入口集合 `S`，在固定搜索预算下定义可实测 utility：

```text
u(q,S) = Σ_K a_K · [Recall@K(q,S)-Recall@K(q,Medoid)]
         - γ · [NDC(q,S)-NDC(q,Medoid)]_+
```

其中 `K={1,10,100}`；所有项由冻结图的真实搜索 trace 获得，不再把“top-1 GT 命中”或“hub 分类准确率”当代理目标。训练风险使用预先固定的 hard groups 或下分位效用：

```text
maximize  mean_q u(q,π(q)) + λ · CVaR_lower,α(u(q,π(q)))
subject to |H|≤B, |π(q)|=m, route_NDC≤budget
```

若直接优化 empirical CVaR 不稳定，第一版实现使用 hardness decile 的 group-DRO/saturation：最大化各 decile 覆盖效用的最小值。hardness 必须由 Medoid NDC/Recall 或 Steiner-Hardness 在独立 train/validation 上定义，不能由 TailRisk-Cover 的结果反向定义。

### 2. Sparse utility，而不是 GATE 式全量 query×hub 探测

候选 `C` 由三类节点并集产生：train top-k GT 节点、Medoid 失败 trace 的 frontier/near-GT 节点、QGT-Cover 的几何代表。每个 query 只探测 `r=16/32` 个候选：GT 邻域候选、trace 候选和少量探索候选。保存稀疏表：

```text
query_id, candidate_entry_id, K, L, recall, ndc, hops, success, medoid_delta
```

这一步直接修复当前 labels 只保留单 hub/min_ndc 的信息损失，也把复杂度从 GATE/旧 labels 的 `O(|Q||H|)` 降到 `O(|Q|r)`。exact train GT 的生成时间、读取时间和空间必须单列；同时做 `GT-free trace-only` 消融，判断方法是否必须依赖 exact train GT。

### 3. 风险加权 hub coverage

先将负 utility 截为 0，构造 coverage `c(q,v)=max(0,u(q,{v}))`。固定 query 权重时，

```text
F(H)=Σ_q w_q max_{v∈H} c(q,v)
```

是标准 facility-location 型覆盖目标，可用 lazy greedy 高效求解并给出清楚的近似性质。为处理 tail，外层按 group-DRO/CVaR 迭代更新 hard groups 的权重；论文应把“内层子模覆盖的保证”和“外层风险重加权的经验算法”分开陈述，避免宣称未经证明的整体保证。

### 4. 互补 top-m，而不是相似度 top-3

当前 Micro-HNSW 的 top-3 只代表三个 prototype 与 query 相似，不能保证搜索失败互补。训练时为候选 entry 对记录共同失败率，在线在召回的 top-r prototypes 中贪心选择：

```text
score(v | S,q) = predicted_utility(q,v)
                 + η · marginal_GT_or_trace_coverage(v | S)
                 - β · correlated_failure(v,S)
```

这是与 SOAR 相同的核心原则：第二/第三入口必须在第一入口容易失败时提供备份。第一版可完全闭式：prototype 相似度作为预测 utility，训练统计的 pairwise failure matrix 提供相关性惩罚；无需神经网络。随后再比较一个轻量线性/MLP scorer，只有显著提高真实 tail utility 才保留。

## 为什么这一方向比继续改 Router 更可能发表

1. **新问题清楚：**首次把 frozen-graph entry layer 明确定义为固定预算下的 lower-tail risk optimization，而非平均 hop 或单 hub 分类。
2. **机制可解释：**风险加权 coverage 解释 hub 为什么被选；相关失败惩罚解释 top-m 为什么互补；每个模块都有逐 query 证据。
3. **与最近工作正交：**GATE 学表示、RoarGraph/RobustVamana 改图、Steiner 测 hardness；TailRisk-Cover 在不改底图条件下优化 risk-aware diverse entries。
4. **继承已有优势：**QGT-Cover 是 warm start，现有 fast 构建和双数据集结果不是推倒重来。
5. **可以被证伪：**若在强底图、等 NDC 下 existing/broad oracle 的 tail headroom 很小，就及时停止入口主线，避免继续堆模型。

## 投稿级实验门槛

### P0：先做，不通过就不实现完整方法

- 继续冻结当前 WebVid/Yandex `R64/L_build100/C512` NSG；不把 RoarGraph 的 `L_pjpq=500` 误当成 NSG `L_build=500`，也不先支付高成本重建底图。
- 在 validation 上做 Medoid、当前 QGT、existing-hub oracle、broad sparse-candidate oracle、oracle diverse top-3/top-5；全部按等 NDC和等 latency报告。
- 若 broad oracle 相对当前 Fast 在 hardest 10% 上的 lower-tail Recall/CVaR 改善不足，或相关失败优化没有 headroom，TailRisk-Cover no-go。

### 必须基线

- 同冻结图入口层：Medoid、Random-k、KMeans/HBKM raw、当前 QGT Raw/Prototype、GATE、LSH-APG、TailRisk-Cover。
- 改图端到端：NSG、HNSW、RobustVamana/OOD-DiskANN、RoarGraph；Dynamic-Hardness 若代码/正式版本可复现则加入，否则明确列为不可复现的同期预印本。
- oracle：existing candidate single/top-m、broad candidate single/top-m。

### 数据和统计

- 主任务至少 WebVid-2.5M、official Yandex T2I-10M/IP、LAION-10M；同模态数据作为安全性 control。
- 保持 ACO/QGT-train、utility-train、validation、held-out test 物理隔离。
- 最终每方法至少 3 build seeds；每点 10K held-out × 3 timing runs；Recall 的 seed 方差与 QPS 的 run 方差分开。
- 报告 Recall@1/10/100、QPS–Recall、NDC–Recall、P1/P5 recall、bottom-1%/5% CVaR、四个预注册 tail 阈值、rescued/newly-harmed、build time/RSS/index size/break-even。
- 计入 exact train-GT；同时报告无 exact GT 的 trace-only 版本。

## Go / No-Go 与投稿定位

满足以下条件才建议按 CCF A 强度冲击 KDD/VLDB/SIGMOD 一类 venue：

- 两个以上 OOD/cross-modal 数据集上，在强底图与等 NDC/latency 下，TailRisk-Cover 对 GATE 和当前 Fast 都有稳定的 lower-tail 改善；
- harmed 不因追求 CVaR 显著增加，平均 Recall/QPS 不出现不可接受退化；
- diverse top-m 的改善能由共同失败率下降解释，并在不同 hub budget、GT 目标和 train-query 规模下稳定；
- 与 RoarGraph/RobustVamana 的端到端比较清楚呈现“低构建成本、冻结图兼容性、效果”的 Pareto 区间；
- 第三个数据集和完整成本核算成立。

若只能做到“与 GATE/当前 Fast 召回相近但更快构建”，更现实的是 CCF B 或系统/工业方向；若 broad diverse oracle 在当前合理冻结图上没有明显 tail headroom，则收窄 workload/论断或停止该 entry 改进。Graph repair 只作为竞争基线或 future work，不自动成为本项目方法。

## 原始链接

- GATE: <https://arxiv.org/abs/2506.15986>
- RoarGraph: <https://www.vldb.org/pvldb/vol17/p2735-chen.pdf>
- OOD-DiskANN: <https://arxiv.org/abs/2211.12850>
- Steiner-Hardness: <https://www.vldb.org/pvldb/vol17/p4668-wang.pdf>
- SOAR: <https://arxiv.org/abs/2404.00774>
- Dynamic-Hardness: <https://arxiv.org/abs/2510.22316>
