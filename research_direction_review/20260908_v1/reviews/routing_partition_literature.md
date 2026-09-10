# 路由、分区与查询自适应：文献证据核对

审阅日期：2026-09-08。范围为 2024—2026-09-08；只使用论文全文、作者仓库及正式出版信息。本文是独立文献核对，未启动实验、未修改 ACSG 原图、GT、旧 gate 或已有结果。全部 PDF、按 PDF 页码分段的提取文本及 SHA-256 位于 `../sources/p1_routing/`，来源记录见 `download_manifest.json`。页码均为 PDF 页码，kRt 同时给出刊物页码。

**判断：这些论文支持学习更有价值的入口、分片或候选集，但不支持从“GT 更集中”直接推出“固定原图上按 GT mass 分配受保护队列容量更优”。** 分片包含答案、从入口能到达答案、额外搜索预算能带来多少答案，是三个不同对象。当前计划需要先证明第三个对象，并把强基线放在前面。

## 核心证据表

| 论文与出处 | 实际优化对象、监督与检索过程 | 代价与证据条件 | 与当前 ACSG 计划的关系、不可外推处 |
|---|---|---|---|
| **GATE**, *Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities*, KDD 2025；[全文](https://arxiv.org/pdf/2506.15986v1)，[正式 DOI](https://doi.org/10.1145/3711896.3736930) | §4.1–4.3，pp.5–7：平衡层次 k-means 选 hubs；采样局部子图提取结构表征；两塔模型用 query–hub 对比学习训练；额外 hub 导航图为原 NSG 选入口。§4.2 的标签来自**每个 query × 每个 hub 的实际 NSG top-1 搜索 hop 数**。正样本阈值相对于该 hub 在查询集上的最小 hop，不是 GT 区域质量。 | §4.4，p.7：标签准备复杂度明确为 `O(|Q|·|V|·S)`。§5，pp.7–9：512 hubs；Xeon E5-2650 v4、128GB；建图 48 线程、查询单线程、重复 10 次；五数据集，包含 Text2Image10M。论文问题和伪代码用 L2；仅凭数据集名不能认定等价于本项目 raw IP。论文报告约 1.2–2× 查询加速。 | **方法级接近 Fast 的“额外入口索引＋保持基础图”方向；组件级接近结构表征与监督入口。** “图拓扑感知入口”本身已非新概念。可借鉴实际搜索效用标签；不能照搬全 query×hub 成本，也没有保护区域队列的结果。论文未给足以重建本项目全部监督成本的端到端时间分解。 |
| **LIRA**, *A Learning-based Query-aware Partition Framework for Large-scale ANN Search*, WWW 2025；[作者全文](https://zheng-kai.com/paper/2025_www_zeng.pdf)，[代码](https://github.com/SimoneZeng/LIRA-ANN-search) | §3，pp.4–6：输入 query 与其到各中心的距离，输出每个分区是否包含 kNN 的二元概率；标签 `[5,4,1,0,0] → [1,1,1,0,0]`，**不是 GT mass**。训练使用 base 子集作为查询、在该子集计算 kNN。模型用于选择需复制的数据及复制目标；阈值决定 probed partitions。每个分区重建独立 HNSW，结果合并。 | §4、A.3–A.6，pp.6–8、11–14：50M 子集，1024 分区，主实验 k=100，HNSW M=32、ef=128；大规模 redundancy=100%，即每点增加一个副本。平台含 Xeon Silver 4214 与 4×RTX3080。Table 2 给不同 Recall/QPS 工作点，不全是严格相同 recall 比较。 | **概念级直接碰到 GT 集中/减少探测分区；组件级碰到 learned multi-label routing。** 依靠独立分片＋复制改变可检索对象，不能证明固定图区域配额；GT mass→capacity 也不是其目标。CPU-only 训练可行性与本项目 IP/OOD 泛化须另证。 |
| **kRt/hRt**, *Unleashing Graph Partitioning for Large-Scale Nearest Neighbor Search*, PVLDB 18 (2025), 1649–1662；[正式全文](https://www.vldb.org/pvldb/vol18/p1649-gottesbueren.pdf)，[作者代码](https://github.com/larsgottesbueren/gp-ann) | §2–3，pp.2–5：稀疏近似 kNN 图最小割分片，可复制边界点。**kRt 在每片内部层次 k-means，以多个中心表示非凸片区**；检索这些代表点，用距离或频数排序分片。无需查询标签训练。hRt 有 LSH 理论，kRt 是经验效果更好的方法，两者不可混称。 | §4，pp.6–10：1B、40/48 分片，允许 5% 不均衡，重叠配置 20% 数据复制；各片单独 HNSW。包含 TTI 原始 inner product。Oracle 分片覆盖先用片内全扫描测，QPS 再用片内 HNSW。吞吐是**单机顺序模拟 60 主机、每主机 32 核、按最慢主机计时**，排除网络时延。TTI 图构造＋分区约 124 min（Table 4），router 另计。 | **概念级直接覆盖“图分区→GT 集中→少查几片”；多代表路由也是现成组件。** 能支持“单个中心不够”，却没有证明每片只用 2–3 portals 足够。其 LSH 理论适用 ℓp、p∈[1,2]，不可当 raw IP 保证；更不可把分片覆盖等同于固定原图搜索预算收益。 |
| **LTR-IVF**, *A Learning-to-Rank Formulation of Clustering-Based Approximate Nearest Neighbor Search*, SIGIR 2024；[全文](https://arxiv.org/pdf/2404.11731v1)，[作者代码](https://github.com/tomvek/mips-learnt-ivf) | §3–4，pp.2–4：保持分区，只学习线性分区代表 `Wq`。训练为 exact top-1 所在分区的 softmax cross-entropy，借 MRR 一致 surrogate 解释；§3.1 提出 top-k 扩展，但**实际训练仅 top-1**。使用独立 60/20/20 训练/验证/测试查询。 | MS MARCO/HotpotQA/Fever，数百万文本向量、MIPS；报告 top-1/top-k 分区覆盖随 nprobe 的变化。假设片内精确搜索，**没有端到端 CPU QPS/NDC 收益验证**。100 epochs 上限，batch512，Adam。 | **“给固定分区学习 query→region 标签”已有非常简单的直接对照。** 它应先于复杂 router 出现在可学习性检查中；但其分片覆盖结果不能回答共享图上的可达性、队列容量和搜索效用。也不能把论文提出但未训练的 top-k 目标当成实验证实。 |
| **TaCo**, *Data-adaptive and Query-aware Subspace Collision for High-dimensional Approximate Nearest Neighbor Search*, PACMMOD 4(3)/SIGMOD 2026，Article241；[全文](https://arxiv.org/pdf/2603.24919v1)，[正式 DOI](https://doi.org/10.1145/3802118) | §3–4，pp.6–16：协方差谱分解、分配特征方向以平衡子空间，建立每子空间 IMI；统计查询与点的**子空间碰撞次数**，按可观测 SC-score 分布选完整分数层，再在原空间精排。min-heap 加速 IMI cell activation；非 learned router，无 GT 标签训练。 | §5，pp.17–22：**L2**；1M/10M base，随机取出 **100 个 base 点作查询**，默认 k=50；双 EPYC9554、756GB，C++/SIMD/OpenMP/Pthreads。建索引时间**排除数据变换等预处理**，索引内存排除原向量。对 SuCo 报 >1.5× QPS@0.9 recall；对其他类方法的优劣依数据与 recall 而变。 | **概念级覆盖 query-specific compute；其依据是已经观测到的候选质量，而不是静态 GT mass。** 新建投影/IMI，不兼容直接复用固定 ACSG 原图；同分布、100 查询、L2 结果不能证明 OOD raw IP。距离顺序理论依投影残差和间隔条件，非无条件保序。其 lifetime-cost 图仍沿用排除变换的 indexing 定义，不能直接作为完整 break-even。 |
| **NeuRoute**, *Logit-Guided Neural Routing for Billion-Scale Vector Search with Sub-Hour Index Construction*, arXiv v1，2026-08-15；[全文](https://arxiv.org/pdf/2608.15438v1)，[作者仓库](https://github.com/XingqiaoWang/NeuRoute) | §3，pp.5–11：MLP 保持 minibatch 中近邻对的 L2 距离；中位阈值生成 binary buckets、桶内 latent clustering。query 按 logit 距阈值的距离枚举 bucket，再以 centroid gate 和**当前 heap 的有效更新**决定停止。encoder 无 GT，但 gate 校准使用独立查询上的高预算检索 top-k 输出（p.10）。 | §4–6，pp.12–22：固定 2M 训练子集，batch4096、500 epochs，**单 A100 训练**；CPU 检索 24 线程，1TB RAM。L2；GLDv2 做 unit normalization。Table6：BigANN1B 0.903 recall/2414 QPS；Deep1B1B 0.901/842，而 OPQ-IVFPQ-refine 为0.912/3342。0.82/0.93h 包含 GPU 训练，排除外部预处理。 | **组件级接近 confidence-guided probing/heap-state stopping；方法整体重建 hash/cluster index。** 新预印本，未独立复现；其自述结果并非普遍胜出 HNSW/OPQ。可借鉴“在线收益信号＋校准＋全过程成本”，不能据此复活已失败的静态 confidence attention，更不证明 GT mass 容量分配。 |

## 作者代码带来的补充核实

- LIRA [大规模主程序](https://raw.githubusercontent.com/SimoneZeng/LIRA-ANN-search/main/LIRA_largescale.py) 当前公开代码明确设置 GloVe/Text2Image 为 `inner_product`，所以它有 IP 实现证据；但这不能证明本地 raw IP 数据、预处理与论文配置完全相同。该文件使用 `cuda:{get_idle_gpu()}`，1% base 作训练集，大规模每点最多两份。`get_cmp_recall` 先枚举所有 query×partition 搜索，随后 `query_tuning` 用选中分片的预计算 NDC 和命中结果汇总。这个公开脚本不是我已验证的 CPU 端到端在线基准；本文没有把论文 QPS 还原成源码确认结果。
- NeuRoute [README](https://github.com/XingqiaoWang/NeuRoute) 有完整 build/query 入口，query benchmark 使用 TorchScript/C++、24 search threads；它存在叫 `ip1536` 的实现 metric 选项。论文 GLDv2 已对 base/query 做单位化，故该名字不能构成非归一化 raw IP 的实验支持。
- GATE 正式公开 artifact 入口为 [Zenodo DOI](https://doi.org/10.5281/zenodo.15523071)（论文 p.1）。本轮未下载运行其代码，也未核实其中 Text2Image 的实际 metric/normalize 路径。保留不确定性。

## 阅读覆盖与证据限度

| 条目 | 本轮实际阅读覆盖 | 未声称完成的核实 |
|---|---|---|
| GATE | 全文主线与方法 §3–4、实验 §5（pp.1–9），明确读标签公式、复杂度、实验配置；全文 PDF11页已保存 | 未跑代码；未从 artifact 确认 raw IP、模型训练硬件、完整训练成本；图表只取有清晰正文/表格支持的结论 |
| LIRA | 方法 §3、实验 §4、AppendixA.3–A.6；重点逐段读 pp.4–8、11–14；作者 README/大规模代码只读 | 未审完整源码；GPU/CPU 计时全流程边界仍不能从论文硬件表推断；未称其 Table2 全为 matched-recall |
| kRt/hRt | §2–4（pp.2–10），重点图构造、代表点、hRt theorem、oracle/真实检索两类评估；全文14页保存 | hRt 后续证明与附录未逐式复核；不使用理论作为 ACSG IP 保证；未独立复現60主机模拟 |
| LTR-IVF | 5页短论文正文全部，特别 §3.1 与 §4 的训练目标区别 | 没有 CPU 效益证据；没有把它未测的 multi-label top-k 训练当结论 |
| TaCo | §3–5 核心正文 pp.6–22；逐式读 Algorithm1–6、Lemma1/Theorem2条件、成本排除项，另读引言与出版页 | 没有复核所有证明的正确性；不把 Theorem1 贪心最优声称推广到任意数据；未跑作者实现；图中的最高数值未凭视觉猜测 |
| NeuRoute | §3–6 pp.5–22 主要方法、校准、训练/硬件、结果和消融实验条件，另读引言与作者 README | Appendix B–E 只定位、未逐图核对；未独立复现；未将预印本等同于会议接受 |

另检索到 **Learning Partition Trees for Nearest Neighbor Search**，[arXiv:2607.09909](https://arxiv.org/abs/2607.09909)，全文47页已保存；本轮只核实摘要与问题设定，**不纳入方向决策证据**。其摘要以 Gaussian-like marginal、存在 perfect tree 等条件给理论学习结果，不能用来支撑本项目 CPU raw IP 或固定图队列。没有为增加论文数量而声称完成全文证明审阅。

## 推理链的三个断点

设 `m_r(q)=|GT(q)∩R_r|/k`。在独立、无重叠、片内精确检索下，选分片集合 A 的覆盖率恰为 `Σ[r∈A] m_r(q)`；这是 LTR/kRt 一类覆盖评估成立的结构基础。若复制数据，则还必须按唯一 ID 做 union，不能相加。

固定全局图的检索不同。portal 的路径会跨区、多个入口会重叠，队列满时会挤出候选；这些行为不由 GT 的最终所属区决定。若用 `U(q,S,b)` 表示从入口/活动集合 S、预算 b 下实际找到的唯一 GT 数量，那么 `m_r(q)` 既不决定 `U`，也不决定额外预算的 `ΔU/Δcost`。

1. **GT 集中→入口可达：未成立。** 分区内有答案，不代表 2–3 个 portal 在小预算上能找到它；多中心 router 只描述分片，不是 portal 可达性证明。GATE 将真实搜索 hop 纳入标签，正是不同信息。
2. **入口可达→预算应按 mass 分配：未成立。** 一区可包含多数 GT 且容易搜索；另一区 GT 少但存在关键长路径。按数量分配会与边际收益相反。还存在两个区复用同一过渡节点的情况，静态 mass 无法表达重复工作。
3. **局部保护队列提升 Recall→方法实用：未成立。** 额外路由、队列和 reset 开销、增加 NDC、对较大普通 beam 的替代关系必须共同衡量。TaCo/NeuRoute 选择从已发生的候选质量变化控制后续工作，也没有证明静态区域配额的成本收益。

这三点是审阅者根据方法定义作出的推论，不是任何论文已替 ACSG 证明的实验结论。

## 撞题边界与对下一版提案的建议

| 可能的表述 | 已有工作覆盖 | 能否作为当前新贡献 |
|---|---|---|
| 图分区令 GT 更集中、降低 probe fan-out | kRt/GP；LIRA 的 redundancy 与 learned probing | 单独不成立；只更换 partitioner/增加层数也不够 |
| 用 GT 所属区域训练轻量 router | LTR-IVF、LIRA；GATE 学 query–hub suitability | 单独不成立；尤其需要胜过线性 scorer 与多代表路由 |
| 多视图/多中心代表非凸区域 | kRt 的多层中心，GATE 的候选 hubs（机制不同） | 组件差异可能存在，但须解释 QGT 视图与此的实际区别 |
| 根据 query difficulty 动态给计算预算 | TaCo 的候选分数层；NeuRoute 的 calibrated gate/heap updates | 概念已有；新的在线状态、代价模型或泛化证据才可能形成差异 |
| 在固定原图上抑制有价值候选被跨区竞争挤出 | 本组论文没有直接给出同一机制 | **尚有机制差异空间，尚无方法价值结论**；必须证明普通 beam/多入口/独立重启同成本不能实现该收益 |

建议把提案由“先更精细 GT 分区再训练 router”改为**先测实际搜索预算有没有可预测且足够大的收益差异**。第一道门应包含原图 Fast、相同实际入口的统一队列、普通 beam 增大、独立多入口搜索/重启，以及轻量线性分区 scorer 或 kRt 式多代表路由；计入路由、图内搜索、队列与 reset，匹配 recall、NDC 和 wall time 中适用的约束。Oracle 仅刻画空间，不能形成可部署结果。只有受保护队列在强对照下有剩余收益，才值得决定训练目标、监督稀疏度和 router 复杂度；否则区域化方案应停止或转为纯诊断发现。

若要研究学习目标，应优先考虑在隔离的训练查询上直接监督“加入某入口/再给一段预算，相对当前已找到集合增加多少唯一命中、付出多少真实成本”；必须包含零收益和负收益情况。这个建议只是可证伪问题定义，不能声称它在现有 ACSG 实现上已经有效，也不能借这份文献报告启动新实验。
