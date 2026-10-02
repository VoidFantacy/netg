# 有限目标库访问：原论文机制、保真对象与成本边界

2026-10-02，理论与原论文只读研究定稿，审校完成 12:29（UTC+8）。已完整读取根 AGENTS、summary、spec，并沿历史卡进入 E165/E166 原报告/协议、原生源码与粗筛设计；另复核 E25/E73/E75/E85/E164 的原边界。本文件是独立研究笔记，不修改根文档或旧协议。今日允许理论探索至 13:00，未运行新 ANN/NSG/GT、训练、构图或新 query，未接触 held-out。

**当前更值得保留的问题，是能否以严格保持 E166 原输出的访问优化，消除其完整 wall 成本缺口。GT10 三桶扫描尚无保留局部质量信号的依据：旧 TargetBank 所选 slot 的覆盖只有 Web 33.76%、Y 45.73%，且 Web 的多数旧救回位于桶外。** 距离 memo、精确界与学习路由均有直接前作，不能以这些组件命名宣称新意。下面把论文原贡献、可迁移机制和我们尚未获得的证据分开。

## 1. 必须保存的局部证据

默认仍为 Web GT10-soft-t1、Y GT10-hard，主搜索为 E99。E166 固定 E165 的 20K 物理 raw-target slot 图、映射、ef10 和原单入口 NSG；评价是两集各 4096 条历史 E105 query。中心点与 E165 同源，不是新的独立复验。

| Web R1 | 默认 Recall / QPS | TargetBank Recall / QPS | 配对 ΔRecall pp / 救回、损伤 | 旧完整 wall 额外成本 μs/query |
|---|---:|---:|---:|---:|
| L800 | 89.184570% / 517.829 | 89.843750% / 508.319 | +0.659180 / 63、36 | 36.126 |
| L1000 | 90.454102% / 417.190 | 90.991211% / 413.177 | +0.537109 / 50、28 | 23.282 |
| L1250 | 91.381836% / 337.677 | 91.772461% / 334.231 | +0.390625 / 42、26 | 30.529 |

前两点配对 95% 描述区间为正，第三点下界为 0；三个点均慢。E166 全部 12 个同预算 TargetBank QPS 低于默认，预定 72 项跨预算比较没有已测均值支配点。Web R100 均值微负，Y 各格未形成稳定质量优势。目标路由平均距离请求 Web 234.444、Y 304.942，主图只省 Web 约 14–23、Y 约 65–89 次距离；这些数不能当 wall 分项归因。原件：[E166 报告](../20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/report.md)、[协议](../20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/protocol.md)。表中成本由本次 [只读旧数组核算](bucket_feasibility.json)引用原完整轮次派生，不是新计时。

E165 预锁前 16 条的全 20K float64 诊断中，原 TargetIndex 达到全 bank 最优分数仅 Web 12/16、Y 14/16。故“精确 bank 最优”与“E166 原近似路由结果”是两个不同参考对象。原件：[E165 报告](../20260930_theory_until2200_v1/research/query_target_transfer_v1/report.md)。

## 2. 保真应先说明对象

| 保真对象 | 足够条件 | 不能顺带推出 |
|---|---|---|
| 全 bank 最大 raw-IP 分数 | 不删除任何可能胜过 incumbent 的目标，且剪枝界有效 | 原近似 HNSW 的 slot/入口 |
| 全 bank 精确最优 real-ID | 上项加预先固定的 slot/real-ID tie 规则 | 相对默认三入口的 NSG Recall |
| E166 原 TargetBank 路由 | 同物理图、邻接顺序、heap/visited/tie，以及每次参与决策的 native 距离 bits | 全 bank 真 argmax |
| E166 原主搜索输出 | 同上项实际入口与固定 E99/query/K/L，完整执行原核 | 新来源的质量优势或新 QPS |
| 可靠 Recall–QPS 改进 | 冻结方法后实测完整 wall/返回，并完成相应确认 | 由 NDC、覆盖率、理论或费用下降代替 |

raw target 范数可不同，不能将 `1-qᵀt` 当成 L2 度量或直接单位化目标。全 bank 分数更高、候选更多、真实目标更接近，都不保证有限 pool NSG 对默认入口的召回单调；E145 已有原生反例。若更换入口，就需重新评价真实搜索响应。

浮点对象也必须固定：原路由比较的是 float32 `1-native_dot(q,t)`；不同 native dot 可以在减法后折成同一距离（如 `2^-30` 与 `2^-29` 都可返回 `1.0f`）。全 bank 的 float64 raw-IP argmax、native dot argmax、native distance argmin 并非自动同一总序。原 `CompareByFirst` 只比较距离，同距离节点的保留还依赖既有 heap 操作和访问顺序；不能新加 slot tie 后称恢复原近似路径。memo 直接缓存完整原 distance，避开这个偷换。

## 3. 原论文实读与迁移结论

以下均阅读了方法正文或原始作者实现，而非仅检索摘要；所有论文机制都只是候选原理，没有转录其速度倍数作为本项目证据。

### 3.1 固定分区的学习路由

**A Learning-to-Rank Formulation of Clustering-Based Approximate Nearest Neighbor Search，Vecchiato 等，SIGIR 2024。** [原始全文](https://arxiv.org/html/2404.11731v1)。已读 §1、§3、§3.1、§4.1。

固定分区后学习线性代表 `Wq`，以 GT1 所属分区的一热标签作交叉熵监督；单相关分区时联系 MRR 一致性。路由替换质心点积，不要求额外深模型。§4.1 的主要对象是被探测分区包含 GT 的覆盖，精确桶内检索是其前提。可迁移的是廉价的监督粗路由；原贡献已经覆盖这点。我们最后执行有限图搜索，桶覆盖、固定图实用入口和完整 wall 仍隔着未验证响应，不能用其覆盖改善证明当前方案有效。

**Learning to Index for Nearest Neighbor Search，Chiu 等，2018 初稿 / 2019 v3，TPAMI 正式卷期 2020。** [实读 v3](https://arxiv.org/html/1807.02962v3)、[作者卷期记录](https://sites.google.com/site/chihyichiu/publication)。已读 §III-A/B/C/D 和复杂度讨论。

网络由 query 或 query–centroid 特征估计相关簇概率，排序探测并分配子簇配额，候选再作 ADC 重排。式 6 已将加权近邻量除以“该量+簇大小”，并归一化；“按命中概率/桶大小决定访问”已有实质先例。原文给推理 `O(τλ²+λM)`、簇选择和 ADC 成本，不能假设免费。其训练目标是簇中的 GT 分布，数据规模和量化重排不同于我们的有限入口 bank；转成固定 NSG 效用需要新响应监督，不是仅换 loss。

### 3.2 精确 MIPS 的安全拒绝

**Fast Exact Max-Kernel Search，Curtin 等，SDM 2013（2012 预印本）。** [原论文](https://arxiv.org/pdf/1210.6287)。已读 §3、定理 3.1、§4 定理 4.1–4.3、§5 定理 5.1。

cover tree 节点的核分数上界由当前核值与覆盖半径导出，只在不能胜过 incumbent 时剪枝；线性核允许带范数的 raw-IP。定理 5.1 的查询界依赖扩张常数和方向集中度，不能无条件写作高维 `O(log n)`。可迁移的是合法界加保守回退，而非某个树名。对我们 20K bank，评估全部桶中心、半径界、排序或树导航也要收费；原论文的核计算数不等于当前完整 QPS。

**FEXIPRO: Fast and Exact Inner Product Retrieval in Recommender Systems，Li 等，SIGMOD 2017。** [作者原论文](https://lihui.info/doc/SIGMOD17.pdf)。已读 §2.2.1/算法 2、§3/定理 1、§4.1–4.2/定理 2、算法 3–5。

已有 partial-IP 加剩余范数的 Cauchy–Schwarz 界、SVD 重排和带误差项的整数上界；并非普通量化后直接相信近似分数。定理 1 在实数算术保持 IP，thin SVD 离线 `O(d²N)`、query 旋转 `O(d²)`。我们只访问约 234/305 个目标，密集旋转可能先吃掉节省；2017 硬件上的整数优势不能直接搬到当前 SIMD。数学等值不保证 native float32 bits，严格路由保真还需覆盖原浮点累加误差，并对不能确定拒绝的候选调用完整原距离。

### 3.3 利用查询分布的访问顺序

**To Index or Not to Index: Optimizing Exact Maximum Inner Product Search，Abuzaid 等，ICDE 2019（2017 预印本）。** [原始会议论文](https://www.bailis.org/papers/mips-icde2019.pdf)。已读 §III-A–E、§IV-A 和成本讨论。

MAXIMUS 聚类 query/user，以簇最大角半径建立 item 分数上界和排序，扫描到剩余上界不超过 top-k 即停；前缀批矩阵乘利用多用户摊销。OPTIMUS 用样本实测选择索引或 BMM，明确计入决策开销。查询簇不是零成本新信息：原 §III-E 假设相对静态用户；新 query 若越过旧角锥，不能直接继承旧上界。单 query 不能借 batch 矩阵乘的摊销倍数。该方向的可迁移点是分布决定访问顺序、证书决定停止，而不是学习一个更高级 router 名称。

### 3.4 成本敏感的条件计算

**Adaptive Neural Networks for Efficient Inference，Bolukbasi 等，ICML 2017。** [PMLR 原论文](https://proceedings.mlr.press/v70/bolukbasi17a/bolukbasi17a.pdf)。已读 §3/式 1–5、§4/式 6–7、§5.1–5.2。

早退/模型转交被写为时间与正部 excess-loss 的约束或代价优化，再归约为带权分类；策略自身评估成本 `τ(γ)` 明确入目标，且包含无需执行策略的常数控制。可迁移的是“多花一段访问是否值得”，不是置信度越低就必然需要更多算分。我们需要真实固定 NSG 动作的配对命中差与完整成本，GT1 所属桶标签不足；E25 和 E164 已测试实际成本敏感选择而未形成稳定收益，不能再以 conditional computation 重开同一特征/动作的调参。

### 3.5 细粒度剪枝与原图输出的区别

**Tribase: A Vector Data Query Engine for Reliable and Lossless Pruning Compression using Triangle Inequalities，Xu 等，SIGMOD/PACMMOD 2025。** [作者原 PDF](https://madsys.cs.tsinghua.edu.cn/publication/tribase-a-vector-data-query-engine-for-reliable-and-lossless-pruning-compression-using-triangle-inequalities/SIGMOD25-xu.pdf)、[作者上传全文镜像](https://www.researchgate.net/publication/388893240_Tribase_A_Vector_Data_Query_Engine_for_Reliable_and_Lossless_Pruning_Compression_using_Triangle_Inequalities)。已读 §2.2、§3.1–3.2、§4.4–4.6、§6.3、§6.6；原 PDF 后续取回超时，以作者全文复核关键节。

中心距离、subNN 距离和角度界用于更细剪枝；§4.5 区分安全界与加强剪枝后会丢质量的 regime，§4.6 已提出 TriHNSW 邻居入队剪枝。故“给图加入三角界”有直接前作；它没有提供我们原 raw-IP 图逐位等价的证书。角度检查、邻居元数据和 SIMD 交互要收费，多个模块节省不能相加。L2 的三角界不能原样用于可变范数目标的 IP 距离。

继续追到[作者固定源码](https://raw.githubusercontent.com/xuqianmamba/Tribase/b8953d4c11a1b766778928d87c3982c4875a4716/hnswlib/hnswlib/hnswalg.h)（[2024-10-13 提交](https://github.com/xuqianmamba/Tribase/commit/b8953d4c11a1b766778928d87c3982c4875a4716)，413–568 行）：`searchBaseLayerSTTribase`额外维护 `top_tri_candidates`，默认 `trief=max(1,ef−1)`（426–427 行），501–505 行按另一个 `tri_lowerBound` 标 visited，553–559 行维护其更小队列。这具体说明其拒绝阈值不是我们原 ef10 阈值。[作者 README](https://github.com/xuqianmamba/Tribase#trihnsw)也将其称为不同剪枝逻辑、实测保留质量；不能由“lossless”标题推断原 HNSW 输出 bits 保真。

**Panorama: Fast-Track Nearest Neighbors，Ramani 等，2025-10-01 预印本。** [原始 v1](https://arxiv.org/html/2510.00566v1)。已读 §2、§3、§4、§5.2、附录 B.5/D。

学习正交变换集中能量，以逐段 IP 和残差范数界加快精排。复杂度分析依赖能量衰减、距离分布等假设。HNSW 接法以 `(LB+UB)/2` 排 candidate heap，精确距离后入 result heap，确实改变原搜索优先级；其无 Recall 损失的实测不等于输出保真。附录 B.5 用 batch100 NumPy 估计 query 旋转摊销费用，不能替代当前串行完整 wall。它是“学变换+逐段界+HNSW”极直接的碰撞。

### 3.6 距离 memo 的直接作者先例

**FISHDBC: Flexible, Incremental, Scalable, Hierarchical Density-Based Clustering for Arbitrary Data and Distance，Dell’Amico，2019。** [原论文](https://arxiv.org/html/1910.07283v1)、[作者距离缓存的固定源码](https://raw.githubusercontent.com/matteodellamico/flexible-clustering/0039a6d9237a80aead64931f9c09449057aab674/flexible_clustering/fishdbc.py)。已读论文 §3、§3.1/算法 1、§3.2，以及作者源码 `FISHDBC.__init__`、`decorated_d`、`add`（84–97、125–161 行）；GitHub 只读提交元数据确认该版本于 2018-02-19 已存在，不依赖当前 master 的后续修改。

论文复用 HNSW 构建时产生的距离维护聚类；作者实现另有 `_distance_cache`，固定当前插入项、按另一个节点键缓存，命中返回已有距离，结束本次插入清空，并统计 hit/miss。缓存复用本身已有直接实现。我们的场景是静态在线 query、原生 raw-IP、重复物理目标 slot，且要求输出 bits 不变；这些是需验证的具体合同，不能将 memo 当作原创算法。作者构建/聚类收益不替代线上效果。

## 4. 三桶提案受到的新只读诊断

原 [coarse 设计](../20260930_theory_until2200_v1/research/target_bank_coarse_access_design.md)按 raw target 到原 H 的最近方向分桶，在线以原 GT10 三画像返回选择桶后 raw 精排。这具有标准 IVF 的粗路由—表内扫描结构；GT10 画像与 raw hub 的分桶方向也并非同一评分对象。若只更换神经路由或桶监督，首先与上述 learning-to-index/learning-to-rank 比较。

本次 [bucket_feasibility.json](bucket_feasibility.json)仅使用 E165 旧 ID/映射及 E166 旧入口、slot、hit/NDC，不开 query/base 向量，不算任何新 IP，不搜索。

| 旧 E105 分布诊断 | Web | Yandex |
|---|---:|---:|
| 三桶物理 M 均值 / p99 / 最大 | 107.330 / 341.15 / 544 | 86.837 / 155 / 182 |
| 三桶 real-ID 去重 M 均值 | 82.121 | 85.385 |
| 原 GT10 路由 + 物理扫描请求均值 | 219.589 | 193.851 |
| 原 GT10 路由 + 去重扫描请求均值 | 194.380 | 192.399 |
| 原 TargetBank 距离请求均值 | 234.444 | 304.942 |
| 旧近似 TargetBank 所选 slot 在三桶中 | 1383/4096 = 33.765% | 1873/4096 = 45.728% |

Web L1000 旧 50 救回/28 损伤中，覆盖组为 10/3（净 7），桶外为 40/25（净 15）。这挑战了“原 GT10 粗筛会保留目标侧局部收益”的直觉；它不是新策略 Recall 预测。未覆盖者可以由另一个入口救回，覆盖者也可能被桶内更高 IP 目标替换后损伤，因此两组都没有结果保真。更不能用“旧 slot 是否覆盖”作免费部署 gate：在线获得该 slot 已要执行目标路由。

混合距离请求只是工作量代理。连续扫描可能省随机访存，也可能失去目标选择；Web 请求数优势小且尾部更重。原 3N/H 的约 74 条估计已不能描述实际分布。没有新 wall/新返回，不能宣称这个版本接近 GO；本稿不建议因覆盖低而追加桶数、重新分桶、补 target IP 或扫阈值。

## 5. 更小的保真问题：单 query native 距离 memo

### 5.1 固定合同与简短证明

保留 E166 原 20K 物理 slot 图的节点、层级、入口、邻接顺序、物理 visited、heap/tie 和 ef10。只包装距离函数：对同一次 query、相同向量字节，第一次调用原 native 函数并保存完整 `distance` bits，后续请求直接返回它；不重新由缓存 IP 计算 `1-IP`，不近似算分，不合并图节点。

TargetBank 可用静态 `slot→unique real-target key`；Default3 用画像 slot key。实际源已在 E166 原审计逐行核验 `target[i]` 对应的 raw vector bits。原 distance 函数按 query/vector/dimension 计算；在相同 FP 环境和 immutable 输入下其值与访问次数无关。若每次缓存返回与原函数 bits 相同，则每个状态转移的比较、heap 更新与 visited 更新相同。由归纳法，原路由 slot/距离、映射入口和固定 E99 返回/距离/主图 NDC 相同。证明只给等价，不给速度。

源码依据：E166 [experiment.cpp](../20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/experiment.cpp) 16–20、29 行；继承的 [hnswalg.h](../20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/hnswalg.h) 333/394 行底层与 1281/1299 行上层均用同一 `fstdistfunc_`/`dist_func_param_`，1313–1314 行将原 query 传入底层；[space_ip.h](../20260930_theory_until2200_v1/research/query_target_transfer_v1/src/common/hnswlib/space_ip.h) 348–379 行构造时依 dimension/CPU 选定回调，389–394 行提供固定 callback/参数。它可能是 SIMD 函数，不能称为全程 scalar。上层没有跨层完整距离 memo；下层 visited 只阻止物理 slot 重访，不合并重复 target slot。源码说明存在复用机会，不说明 E166 实测命中率。

query stamp 必须在整个上层+底层调用前更新，跨层保持同一 stamp；wrap 时按预锁清空，不能沿用旧 query 值。相同 real-ID 仅在相同 query、native callback/参数、vector bits、dimension、kernel 与 FP 环境都成立时合并 cache key；不合并不同的画像向量。缓存只存在于本次路由内部，不跨数据集/方法/查询，也不把路由距离借给 NSG。尤其不能跨 scalar 与 batch4 的不同累加路径复用结果。分别记录 logical distance requests、native dot 次数和 cache hits，不能将减少 dot 偷换为原图改变。

E166 [计数包装](../20260930_theory_until2200_v1/research/target_bank_frozen_curve_v1/src/common/evaluate.cpp) 8–9 行仅 `++n` 后调用原 native 函数，没有调用次数依赖的评分或 RNG。未来 memo 命中仍保留需要的 logical 计数，把 actual-dot 单独记数；函数纯性/输入不变也是条件，不能把一个改变后续评分或停止的 callback 偷换成此合同。

### 5.2 已知规模与尚缺的成本

全 bank 去重 Web 20000→15789，Y 20000→19671，仅说明 payload 存储的最大静态减少约 21.06%/1.65%。实际每 query cache hit 还取决于访问序列，含跨层同 slot 重算；全库比例既不是命中率也不是 dot 或 wall 节省率。E165/E166 保存的是最终 slot 与总 NDC，没有这轮所需距离请求 trace；本次没有为了补它重跑搜索。[历史审查](history_gap_audit.md)对 E35 旧 ef10/k8、两集各 128 条画像路由 trace 只读计数，发现同物理 slot 请求重复约 8.34%/8.54%；它说明默认画像图也有通用缓存机会，但旧 query/bank 不能外推 E166 命中率或完整 wall。

令旧一次路由请求数为 R，实际不同 cache key 数为 C。常数成本近似下的算术盈亏条件是

`(R-C)·cost_dot > R·cost_lookup + C·cost_store + cost_stamp/reset`。

这只解释缓存工作量，不能由 route NDC 估算主目标的时间缺口。更直接的完整 wall 条件为：令 `D=T_target−T_default`，`S_target=T_target−T_target_memo`，`S_default=T_default−T_default_memo`，则目标库 memo 胜过默认 memo 当且仅当 `S_target−S_default>D`。但 `S_default` 可以负，此式可能靠劣化默认通过。因此性能结论必须同时胜过原 Default3 和 Default3 memo，条件是 `S_target>D+max(S_default,0)`，即与两默认中更快的 `T_default_best=min(T_default,T_default_memo)` 比；这只是两个固定基线控制，不是免费逐 query 选择器。E166 旧 Web R1 的 D 为上表 36.126/23.282/30.529 μs/query；它是旧完整 wall 量级，正式新比较须同批重测原版与 memo，不能将旧时钟差当未来速度证书。完整推导见[成本条件](full_cost_conditions.md)。

缓存还会改变 cache 压力、预取和间接访问，需要完整 wall 实测。图的 payload 共享存储可以另立版本，但改变 loader/布局及指针间接，不应与第一次 memo 验证绑在一起。E73 已显示精确分数集合保持而重建近似图输出改变；E75 保留随机层级也不恢复邻接，不应将“删节点重建图”称为此保真机制。历史反证 agent 对 E35 距离观察、E46 完整响应缓存、E73 去重和 E99–102 主核优化的定向核对未发现相同在线距离 memo 实验；此结论限核查范围，不是算法首次性。

### 5.3 未来最小控制，当前未实现或运行

共同输出/计时控制至少为 Default3 原实现与 slot memo、TargetBank 原实现与 real-target memo。若需要将收益归因于 target 重复而非所有 HNSW 都有的跨层重算，再加入 TargetBank slot memo：该对照只复用同物理 slot，real-target memo 才额外复用跨 slot 同目标。DefaultRank1 与 Default3 路由相同，不必为 memo 单独拟合新 gate。

所有控制共用同一个 native 算分函数、stamp/缓存实现习惯、固定 query/图/K/L/主搜索，缓存成本放在真实 timer 内。先验收路由 slot/距离 bits、入口、返回/距离 bits、主图 NDC 和 logical 请求数逐位恢复，再看完整串行 wall；不能因输出相同省掉身份核验。未来冻结一次小范围成本验证即可，不扩 ef/L/样本/模型。若 cache 开销吃掉节省，或原默认/默认 memo 任一仍更好，则结束该缓存版本；不能通过较慢的默认 memo 降低性能门。

一个尚待授权与单独冻结的最小工作范围可沿用旧四中心：Web K1/L1000、K100/L1250，Y K1/L128、K100/L256，同时保留两数据集的正负格，不从本次理论稿再挑新的 L。这里只说明未来控制范围，今日不调用任何这些 query。

即便输出保真且速度变好，继承的也只是 E166 开发 query 上 Web R1 的质量信号；Y 与 K100 旧负点同时继承。这可以隔离访问成本问题，不能单独完成新来源的可靠 Recall–QPS 目标，也不是充分论文贡献。

## 6. 安全界的两种后继，不能混成一个版本

**保留全 bank 精确最优。** 对桶 B_h 选中心 c_h、raw 最大残差半径 r_h，可用 `U_h(q)=qᵀc_h+||q||r_h`。先扫描候选桶给 incumbent，再按上界访问剩余桶，直到所有剩余上界不能胜过它；stable tie 需继续处理可并列者。这是标准分支定界思想，FastMKS/FEXIPRO/MAXIMUS 已有明确先例。它恢复有限 bank 最大分数，可能修正 E166 的近似遗漏，也可能改变入口和质量；评估全部 H 个界及导航成本不能免费。

**保留 E166 原近似路由。** 若使用便宜 score 上界，必须保证它覆盖原 native float 距离，不只是实数 IP。底层只在原 `top_candidates.size()>=ef` 且证实原 `lowerBound>dist` 为假时提前拒绝；上层只在证实原 `d<curdist` 为假时拒绝。其他候选仍执行完整原距离，以原值入 heap；visited 和邻接遍历保持原顺序。不能用最终 top1 阈值代替 ef10 的队列阈值，不能照抄 Panorama 的估计 heap，也不能把 Tribase 的新 threshold 当原阈值。

更具体地，设证书给出原完整回调距离的保守下界 `d_minus(q,t)<=d_native(q,t)`。底层仅在队列已满且 `d_minus>=lowerBound` 时拒绝，上层仅在 `d_minus>=curdist` 时拒绝；原条件是严格 `<`，相等也可拒绝。原底层先写 physical visited（391 行）再评分，提前拒绝仍须完成这项写入和全部原邻接顺序。logical 请求与原计数保留，另记实际 native dot 与证书拒绝，不能把被拒节点留成未访问或让 counter/RNG/副作用改变以后状态。当前 E166 没有 filter/自定义 stop condition；换成此类路径须另证，不能自动继承。

实数 raw-IP 上界本身不足以产生 `d_minus`。它还要包含该 SIMD callback 的乘法/归约误差、`1-dot` 的舍入折叠，以及证书计算自身的 outward error；原编译与 FP 模式是合同的一部分。不能把缓存的 distance 用 `1-distance` 当成原 native dot，它可能已丢低位。非有限值、溢出、下溢/FTZ 或无法证明间隔时须原函数回退，不能依一个未经证明的 `epsilon` 拒绝。本文尚无具体 native 误差包络与拒绝间隔，也无真实证书成本，故早拒绝保持 `HOLD_NATIVE_SAFE_BOUNDS_MISSING_MARGIN_AND_FULL_COST`。即便补出保守界，界检查若比原完整 SIMD dot 贵也应停止该版本。

一个无 dense query 旋转的数学形式是沿原边预存 `δ_ij>=||t_i−t_j||`，利用 `U_j=qᵀt_i+||q||δ_ij>=qᵀt_j`。它对 raw-IP 有效，无需假装 IP 是度量。**但以仍在当前接收阈值内的展开节点 i 作 pivot，它没有正间隔拒绝力：**理想实数下 `d_i=1−qᵀt_i<=b=lowerBound`，而该界给 `d_j>=d_i−||q||δ_ij<=d_i<=b`，不能证实 `d_j>=b`，除退化相等情况。upper 层若 pivot 就是当前 best，同理不能证实邻居不改进。误差包络只会让界更松。这是分析该特定球界的适用条件，不是否定所有安全界。

这个限制也不能扩大为“整次展开绝不剪枝”：原 base 的 neighbor loop 中 `lowerBound` 会下降，但仍继续扫该轮旧 pivot 的邻接；upper 同一旧邻接列表中也可能先更新 `curdist`。若旧 pivot 此时已落在更紧阈值之外，`d_i−b>=||q||δ_ij` 才可能给剩余邻居拒绝间隔。必须记清 pivot 是该轮邻接列表的原节点，不可更新 `currObj` 后把旧边 δ 配到新节点。另一种可能是使用已计算但远离 query 的 anchor；其离线映射/距离元数据和检查费用仍未取得。

更紧的方向信息可作理论对照：对非零 pivot 令 `u=t_i/||t_i||`，`c=qᵀu`、`β=uᵀt_j`、`τ=||t_j−βu||`、`Q=||q||`，则 `qᵀt_j<=cβ+sqrt(Q²−c²)τ`。这可能低于 pivot 本身分数，属于标准正交残差/角度界思想，FEXIPRO 与 Tribase 已有直接邻近机制。此式不是新执行方案：从 native distance 不能无误恢复 c，需对 c/β/τ/Q 的有效区间求保守最大值并覆盖 native error。query/pivot 残差范数可按同一 query/pivot 复用，但新增边元数据、query 范数、sqrt 和界检查仍可能比完整 SIMD dot 更贵；当前没有算任何新边信息或候选 IP，没有真实 margin 与费用。

两个后继都还缺便宜而足够紧的界、native 误差包络、真实拒绝率和完整费用。密集 SVD/学习旋转引入 `O(d²)` query 工作，当前小 bank 路由未显示其摊销余量；随机概率界也不构成严格 bits 保真。本稿不建议今天训练变换、量化索引或生成新访问 trace。

## 7. 条件访问的正确标签与研究边界

若以后决定“本 query 是否值得额外读目标桶”，动作标签应是一次固定主搜索的真实质量/完整成本差，如 `Δhits(q,a)` 与 `Δwall(q,a)`；动作后的信息不能装成决策前免费特征。预测 GT 桶覆盖、bank 最大 IP、原近似 slot 或低 confidence 都不是这个效用。

已有 GT10 返回和静态桶大小可以作为廉价特征，但过去 E25 7/13 特征选择器、E85 路由前 query 线性选择、E164 状态到相对 rank 表已关闭相应固定版本。新 gate 必须先说明出现了什么新的可迁移响应、已有信息为何足以辨识救回与损伤，以及比常数/置换/同监督低成本规则多什么；再使用同监督与完整成本控制。不能据今日只读分组挑阈值，也不能让“桶外旧救回”变成可部署规则。

## 8. 当前优先级与结束条件

1. **优先保留输出不变的 memo 成本问题。** 保真对象明确，零训练和零图改变；已有作者实现，定位为系统控制与成本诊断。真实访问重复率及 shared-default 完整 wall 是唯一待补关键，不预言通过。
2. **保留安全早拒绝的理论合同。** 全 bank 精确最优与原路由队列保真分别立题；当前浮点/阈值/摊销缺口较大，先于学习变换解决这些缺口。
3. **三桶 raw 精排保持提案状态。** 工作量尚有可能，原输出覆盖低，旧多数 Web 救回在桶外；原最小 matched controls 和几何粗筛控制仍必要。今天不扩大桶/分桶/样本。
4. **不以条件计算重开旧 gate。** 先证明新动作信息及完整成本，GT 标签预测改善不替代有限 NSG 效用。

这些是可证伪研究问题，不是 runner、授权实验或默认替换。主目标仍未完成；当前只读理论工作的有用结果，是拆清哪些对象可严格保留、哪些组件已有前作，以及下一次真实成本验证应只改变什么。
