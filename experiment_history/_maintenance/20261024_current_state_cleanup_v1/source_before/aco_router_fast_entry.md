# ACO / Neural Folding 审计与 Fast-Entry 改进实验

> 最后更新：2026-08-29。本文集中记录 ACO、label mining、Neural Router 的日志/源码诊断，QGT-Cover + closed-form prototype 替代方案，WebVid 多种子结果、相关工作和后续实验。`summary.md` 只保留研究决策，`spec.md` 只保留实现契约；复现命令见 `command.md`。

## 结论

当前 WebVid-2.5M 证据已经从“单次有效”升级为“**三个独立聚类 seed 上均有效**”：在同一冻结 NSG、同一严格 held-out 10K test split 上，无 ACO、无 DPC、无逐 hub probe labels、无神经网络训练的 `QGT-Cover + closed-form GT-basin prototype`，在三个 seed 的所有测试预算上均超过正式 Neural Router 的 Recall@1、Recall@100 和 Mean Recall@10；Recall@10 `<0.1` 的失败查询在所有 seed、所有 L 上都明显少于 Medoid，rescued 始终多于 newly-harmed。

官方 Yandex-IP 也已完成一个 seed 的独立轻量复现：fast-entry 明显超过 Medoid，并在 Recall@1/10/100 上与正式 Neural Router 基本持平。这说明可以优先淘汰当前昂贵且目标错位的 ACO/DPC/labels/Neural Router 主链，研究重心转向“冻结图上的超低成本 query-guided entry layer”。但当前仍不是最终跨数据集结论：Yandex 只有 1 seed × 1 run；等 NDC/latency、公平 QPS 交错运行和强相关基线仍未完成。

## 原训练链的真实瓶颈

WebVid 正式 `/usr/bin/time -v` 记录如下：

| 阶段 | Wall time | 说明 |
| --- | ---: | --- |
| NSG | 879.86 s | 公共冻结底图，不计入 entry-layer 替换倍率 |
| ACO | 1591.43 s | 50 iterations，约 31.83 s/iter |
| DPC | 307.12 s | 依赖 ACO weight |
| labels | 2755.44 s | 实际最大瓶颈；逐 query 探测所有 hubs |
| Neural Router | 1847.95 s | 155 epochs，约 90,985 optimizer steps |

四个 query-dependent 阶段合计 `6501.94s`，即约 108 分 22 秒。此前只把 ACO 和 Neural Router 称为瓶颈并不完整：label mining 比两者都慢。

### ACO 日志与源码诊断

正式 50 轮没有非有限 loss 或空路径，因此不是数值崩溃。问题是有效学习几乎在前几轮结束：

- Avg error：iteration1 `0.00443943`，iteration5 `0.00308913`，final `0.00307887`；1→5 改善 30.42%，5→50 只改善 0.332%。
- best 为 iteration16 的 `0.00306342`；iteration5 后均值 `0.00308874`、标准差 `8.75e-6`。
- zero-error rate 从 85.294% 增到 88.434%，但 avg hops 从 3202.33 增到 3412.25。

源码机制解释了为什么后续训练弱：

1. elite 比例为 30%，而超过 85% 的 path 已是 zero-error，因此 elite 内部几乎没有 accuracy 梯度。
2. 奖励 `1/(error+1e-6)` 令 zero-error path 的主项约为 `1e6`，远大于有误差 path；`1/log(path_size+2)` 的长度项太弱。
3. `ant_search()` 用 400 个全局随机节点初始化候选池，并把这些初始节点都加入 `path`，随后又整条强化，信息素会被随机初始化节点污染。
4. 当前 heuristic exponent `0.01`、pheromone exponent `10`，第一轮后选择几乎被已有 pheromone 主导。

所以 50 轮确实全部执行了，但大部分后续轮次没有合理边际收益。把轮数缩到 5–10 可作为成本消融，却不能修复目标与 path 定义；若保留 ACO，应至少移除随机初始化节点的 reinforcement、改用相对 Medoid/tail utility，并固定随机种子。

### Label mining 与 Neural Router 诊断

30K labels 中只有 25,067 条有效。用 raw hub 几何近邻预筛并不可行：真实 oracle hub 的几何 rank 均值 275.58、中位数 207，hit@32/64/128 只有 17.64%/26.57%/38.80%；简单 top-64 预筛会丢掉约四分之三的现有正标签。

Router 的不稳定也不是普通数值发散：

- 155 epochs × 587 steps，约 90,985 次优化；12 倍 augmentation 令每 epoch 消费 300,804 samples。
- hard negatives 每 15 epochs 刷新，发生在 16/31/.../151；刷新后的 loss 平均跳升 `0.01928`，最大 `0.08421`。
- best loss `4.96953@epoch105`，final `4.99013@epoch155`。不同 refresh 区间使用不同目标，跨区间全局 early-stop 比较的不是同一个 loss surface。
- 同标签样本被当作 in-batch negatives；`min_ndc` 只过滤 `-1` 而不参与权重；单 top-1 hub 标签与最终 top-3 routing、Recall@10/100 不一致。
- transformed hub 虽采用 residual scale `0.05`，但正式 WebVid hub 的 L2 位移 mean `4.8332`、max `7.6844`，并不能解释为受控的小残差。

因此当前不应继续靠增加 epoch、扩大 MLP 或增加数据增强挽救 Neural Folding。若保留神经基线，至少要用 fixed validation utility、multi-positive mask、cost/tail weighting 和纯 normalized-raw 消融。

## Fast-Entry 方法

### QGT-Cover raw hubs

只读取独立 5K ACO-train query 及其已有 exact top-100 GT：

1. 对归一化 query 做 spherical k-means，hub budget 与正式 W-DPC 一致为 815。
2. 每个 cluster 按离 centroid 的相似度遍历成员 query，从其 top-100 GT 中选择尚未使用的 base node。
3. 得到 815 个唯一 base IDs 和对应 raw base vectors，作为在线 Micro-HNSW 的入口候选。

它不执行 ACO，也不读取 ACPG weight 或 DPC output。Faiss 会警告 5K points 对 815 centroids 样本较少，这正是本轮必须做多 seed 验证的原因；后续应消融更小 hub budget 或增加独立 QGT-train query。

### Closed-form GT-basin prototype

对独立 30K Router-train query：

1. 取每条 query 的 top-1 GT base vector。
2. 将该 GT vector 分配给最相似的 QGT-Cover raw hub basin。
3. 每个 basin 直接计算 normalized query mean，并加入 strength=1 的 raw hub prior。

这是闭式统计量，没有 optimizer、epoch、hard-negative refresh 或 MLP。线上仍使用现有 top-3 Micro-HNSW routing。C++ 评测器的固定槽名仍显示 `Asym-Neural/NETG_AsymHNSW`，但这些 fast-entry 文件中该名称必须解释为 closed-form prototype，不能误报为神经网络。

该方法仍使用已存在的 exact train GT；本轮压缩的是 ACO/DPC/逐 hub label mining/Router 四阶段，不包含 exact train-GT 的准备成本。

## WebVid 三 seed × 3-run 结果

聚类 seeds 为 `20260828/20260829/20260830`。每个 seed 的 Recall@1 和 Recall@100 均对完整 10K held-out query 内部运行 3 次；Recall 是确定性的，3 次主要用于 QPS 标准差。逐 query Recall@10 对每个 seed 运行一次。以下 `±` 是三个聚类 seed 之间的总体标准差，不是内部 QPS 标准差。

### Recall@1

| L | Medoid | 正式 Neural | Fast prototype mean ± std | 最差 seed |
| ---: | ---: | ---: | ---: | ---: |
| 64 | 0.6264 | 0.6660 | **0.67910 ± 0.00218** | 0.67610 |
| 128 | 0.7183 | 0.7478 | **0.75897 ± 0.00211** | 0.75600 |
| 200 | 0.7763 | 0.7940 | **0.80473 ± 0.00151** | 0.80270 |
| 400 | 0.8442 | 0.8539 | **0.86193 ± 0.00135** | 0.86010 |

三个 seed 的最差值在所有 L 上仍超过正式 Neural。QGT raw 的均值为 `0.67477/0.75577/0.80337/0.86133`，说明主要收益已来自 query-guided hub coverage；closed-form prototype 在 Recall@1 上再提供小幅、稳定增益。

### Recall@100

| L | Medoid | 正式 Neural | Fast prototype mean ± std | 最差 seed |
| ---: | ---: | ---: | ---: | ---: |
| 100 | 0.59956 | 0.61422 | **0.61663 ± 0.00052** | 0.61614 |
| 128 | 0.64203 | 0.65497 | **0.65777 ± 0.00028** | 0.65739 |
| 200 | 0.71516 | 0.72362 | **0.72683 ± 0.00052** | 0.72623 |
| 400 | 0.80583 | 0.81055 | **0.81266 ± 0.00013** | 0.81248 |

QGT raw 的均值为 `0.61715/0.65778/0.72676/0.81305`；在 Recall@100 上 raw 与 prototype 基本持平，部分点 raw 略高。因此不能声称 prototype 对所有 K 都更优，它的明确附加价值主要在 Recall@1/10。

### Mean Recall@10 与失败查询

| L | Medoid | 正式 Neural | Fast prototype mean ± std |
| ---: | ---: | ---: | ---: |
| 64 | 0.61955 | 0.65220 | **0.65985 ± 0.00120** |
| 128 | 0.71853 | 0.74196 | **0.74994 ± 0.00106** |
| 200 | 0.77719 | 0.79299 | **0.80041 ± 0.00122** |
| 400 | 0.84669 | 0.85496 | **0.86019 ± 0.00043** |

Recall@10 `<0.1` 的逐 query 统计：

| L | Medoid failed | Fast failed mean [min,max] | Rescued mean | Newly harmed mean | Net rescued mean |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 884 | **463.3 [444,485]** | 660.0 | 239.3 | **420.7** |
| 128 | 467 | **211.7 [206,221]** | 353.0 | 97.7 | **255.3** |
| 200 | 279 | **122.7 [117,134]** | 204.3 | 48.0 | **156.3** |
| 400 | 101 | **45.3 [40,51]** | 69.7 | 14.0 | **55.7** |

在 `<0.2/<0.5/<0.8` 各阈值和所有 L 上也都是正净救回；完整数值位于机器可读汇总。由此可排除“只提升均值、tail 实际恶化”这一解释，但 newly-harmed 始终非零，后续仍须报告。

## 官方 Yandex-IP 独立轻量复现

为避免 fast 方法对旧 ACO/DPC artifact 存在任何隐式依赖，构建器新增 `--qgt-only --target-hubs`：该路径只读取独立 5K QGT-train、30K Router-train、两者 exact GT 和 base vectors；manifest 的 sources 中没有 labels、DPC hubs、ACO weights 或 Neural Router bins。Yandex 使用与正式方法相同的 821 hub budget、seed `20260829`，构建耗时 `16.58s`、峰值 RSS 约 1.73 GiB。

10K held-out × 1-run 的 QGT+prototype 与正式结果对照如下：

| 指标 | L | Medoid | 正式 Raw | 正式 Neural | Fast prototype |
| --- | ---: | ---: | ---: | ---: | ---: |
| Recall@1 | 64 | 0.8352 | **0.8567** | 0.8541 | 0.8540 |
|  | 128 | 0.9007 | **0.9140** | 0.9127 | 0.9126 |
|  | 200 | 0.9294 | **0.9379** | 0.9373 | 0.9372 |
|  | 400 | 0.9627 | **0.9665** | 0.9660 | 0.9655 |
|  | 800 | 0.9814 | 0.9830 | 0.9834 | **0.9835** |
| Recall@100 | 100 | 0.7918 | 0.8037 | 0.8039 | **0.8046** |
|  | 128 | 0.8275 | 0.8376 | 0.8375 | **0.8382** |
|  | 200 | 0.8807 | 0.8878 | 0.8874 | **0.8880** |
|  | 400 | 0.9378 | **0.9413** | 0.9406 | 0.9405 |
|  | 800 | 0.9696 | 0.9707 | **0.9709** | **0.9709** |

Mean Recall@10 的 fast 值在 L64/128/200/400/800 为 `0.82972/0.89747/0.92865/0.96053/0.97999`，正式 Neural 为 `0.8295/0.8976/0.9278/0.9606/0.9796`，二者几乎重合。Recall@10 `<0.1` 的 Medoid→fast 失败数为 `499→267`、`290→153`、`192→104`、`95→59`、`46→28`；rescued/newly-harmed 分别为 `367/135`、`205/68`、`133/45`、`62/26`、`31/13`，所有 L 均为正净救回。

因此 Yandex 的正确解读不是“fast 明显打败原方法”，而是：**用 16.6 秒的无 ACO/无神经构建，基本复现了正式 Neural Router 的搜索效果。** Yandex 原 ACO/DPC/labels/Router 约为 `64+522+3456+1694=5736s`，相对 16.58s 约缩短 346 倍；仍不含 exact train-GT 准备成本。该结果只有一个 seed 和一个 search run，不能据单次 QPS 宣称线上加速。

## 时间与依赖验证

全部 fast variants 的独立冷启动构建重复实测为 `13.06s`，另外两个 seed 在 page cache 热后为 `1.24–1.27s`。此前第一次冷构建为 `12.14s`。保守按 13.06s 计算，相对原四阶段 `6501.94s` 约缩短 **498 倍**；按首次 12.14s 为 536 倍。正式表格应使用冷启动范围或重新清缓存的多次计时，不能使用 warm-cache 1.2s 宣称倍率。

单个 seed 的完整验证耗时实测约：Recall@1 3 分钟、Recall@100 3 分钟、逐 query Recall@10 1.5 分钟，合计约 7.5 分钟；三个 seed 约 22.5 分钟。一键脚本预估 24 分钟。

seed `20260828` 的 Recall@1 还直接加载冻结 version-1 NSG 文件，结果与从匹配 ACPG 容器释放 weights 后完全一致，证明 fast-entry Recall 不依赖 ACO pheromone/weight。所有新产物写在 `fast_entry_variants/`，未覆盖正式 ACPG、DPC、labels 或 Router。

早期探索文件 `fast_entry_variants/webvid2_5m_light_v1/eval_qgt_vs_prototype_r1.json` 的 raw task 曾错误配对 QGT vectors 与 W-DPC IDs，该 raw task 为 **INVALID**，禁止引用；修正结果只来自各 seed 目录的 `eval_r1_3run.json`、`eval_r100_3run.json` 和 `per_query_r10.json`。

## 相关工作与论文定位

- [GATE (KDD 2025)](https://arxiv.org/pdf/2506.15986) 使用 HBKM hubs、图子结构上的历史正负 query 和对比式双塔，是最接近的 learned entry router；它说明 query-aware hub routing 本身不能作为新颖点。
- [RoarGraph (PVLDB 2024)](https://www.vldb.org/pvldb/vol17/p2735-chen.pdf) 用 query-base 二部关系和 query-guided connectivity 改图，属于需要公平比较的 query-aware graph repair。
- [OOD-DiskANN / RobustVamana](https://arxiv.org/pdf/2211.12850) 将少量训练 query 临时插入构图并连接共同邻居，代表低成本 OOD graph augmentation 路线。
- [Steiner-Hardness](https://arxiv.org/abs/2408.13899) 提供图原生 query hardness，可用于 tail 分层和 CVaR，而不必进入快速在线路径。
- [SOAR](https://research.google/pubs/soar-improved-indexing-for-approximate-nearest-neighbor-search/) 的正交残差冗余分配可启发多入口多样性约束。

当前可辩护的定位是“ultra-light query-guided entry layer on a frozen graph”。若要形成新的论文方法，下一步应增加 tail-aware coverage/facility-location、CVaR 或 diverse multi-entry objective，而不是把 spherical k-means 或 query-aware hubs 本身包装成创新。

## 产物与下一步

- 训练审计：`logs/webvid2_5m_light_v1/training_bottleneck_audit.json`
- 单 seed 探索汇总：`fast_entry_variants/webvid2_5m_light_v1/evaluation_summary.json`
- 多种子权威汇总：`fast_entry_variants/webvid2_5m_light_v1_multiseed_summary.json`
- Yandex 单 seed 轻量汇总：`fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260829/evaluation_summary.json`
- 各 seed 原始产物：`fast_entry_variants/webvid2_5m_light_v1_seed<seed>/`
- 构建脚本：`benches/run/build_fast_entry_variants.py`
- 多种子汇总：`benches/run/summarize_fast_entry_multiseed.py`
- 一键验证：`benches/run/run_fast_entry_validation.sh`
- Yandex 一键轻量验证：`benches/run/run_yandex_qgt_fast_light.sh`

三聚类 seed × 3-run 稳定性复验已完成。2026-08-29 复核后不再要求重建 WebVid `L_build=500`：此前将 RoarGraph 的 `L_pjpq=500` 对应为 NSG `L_build=500` 依据不足，且当前千万级重建成本过高。下一道门槛改为在现有冻结 `R64/L_build100/C512` NSG 上做等 NDC/latency 的 current/broad single/top-m oracle，再决定是否进入 hub budget `128/256/512/815`、更多 QGT-train query、GT top-1/10/100 与独立 hardness 分层。原 ACO 只作为历史基线，不再默认作为主方法。

## 双数据集重复测试更新（2026-08-29）

Yandex-IP 三 seed × 3-run 稳定性复验及 WebVid 同协议重测已完成，结果统一整理到 `fast_entry_benchmark_results/benchmark_summary.md`。WebVid 上 Fast Prototype 相对 Formal Neural 的 Recall@1/100 与 Medoid 归一化 QPS 均提升；Yandex 上 Recall 基本持平，归一化 QPS 在全部测试 L 上为正提升。两个数据集所有 L、四个 tail 阈值相对 Medoid 的净救回均为正。后续方法门槛改为等 NDC/latency、hub-budget 与 GT-objective 消融，不再重复当前稳定性测试。

QPS–Recall 图为 `fast_entry_benchmark_results/figures/webvid_qps_recall.{png,pdf}` 和 `yandex_qps_recall.{png,pdf}`。QPS 进程不计算 tail；tail 是后续独立进程重新搜索并事后汇总的结果。
