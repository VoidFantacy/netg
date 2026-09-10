# 真实搜索效用表示与可压缩路由：多面入口索引候选

2026-09-08；`RESEARCH_ONLY_NOT_IMPLEMENTED_NOT_RUN`。本次只读交接/历史审计文本，检索原论文并静态读取作者源文件；没有训练、ANN 搜索、依赖安装或原始 validation/held-out 读取。

**在本子题内，保留一个有条件推荐：按真实决策遗憾分配容量的多面入口索引。暂不推荐“低秩效用矩阵 + 残差 + 神经条件解码”作为独立研究贡献。** 后者与已有矩阵补全、动作表示、两塔及 GATE/LRSG 太接近。前者让一个入口由多个独立打分面竞争，在线通过一次所有面的 MIPS 得到真实入口；重点不是增加 prototype 数量，而是把有限容量分给造成真实搜索损失的决策冲突，并把压缩/近似检索误差与选择损失分开控制。

这仍是**待验证的算法候选，不是已证明高原创性的方法**。Maxout、多向量检索、结构化 margin、剪枝与增量加基函数均有前作。若最终只是每入口固定四个向量再套 HNSW，应降级为多原型对照，不应列为高原创性主方向。

## 1. 近期一手材料与实际审查范围

| 工作 | 原文/作者材料与阅读范围 | 对当前任务真正提供的约束 |
|---|---|---|
| RPQ，*Routing-Guided Learned Product Quantization for Graph-Based Approximate Nearest Neighbor Search*，ICDE 2024 | [arXiv v1，2023-11-30](https://arxiv.org/html/2311.18724v1)，重点 §3–6，PDF pp.5–8；Alg.1/2、Eq.8–11。已保存原 PDF。 | 不应只保留向量重构/邻近性，应关注压缩是否改变搜索决策；但其对象是全图 PQ 和逐步候选选择，不是当前冻结 kernel 的入口效用。 |
| MUVERA，NeurIPS 2024；作者 FDE 源码公开说明发表于 2025-06-25 | [正式论文](https://papers.neurips.cc/paper_files/paper/2024/file/b71cfefae46909178603b5bc6c11d3ae-Paper-Conference.pdf)，§1.1、§2、Theorem 2.1 的范围；[作者发布页](https://research.google/blog/muvera-making-multi-vector-retrieval-as-fast-as-single-vector-search/)与链接的 C++ FDE 实现。 | 多向量相似度及向单向量索引转换已有系统前作。其 Chamfer 近似保证不等于真实搜索效用保证，也不适合不加判断就用于仅有一个 query 向量的本任务。 |
| GATE，KDD 2025；LRSG，ICML 2019 | 复用本轮已核实的[固定版本一手审计](../../20260908_v4/reviews/graph_entry_literature.md)，不是重新声称全文新审阅。 | 搜索监督、离线复杂入口/节点表示、在线原 query 内积、线性 query 映射折叠均已有强前作。 |
| Maxout，ICML 2013 | [PMLR 作者论文页](https://proceedings.mlr.press/v28/goodfellow13.html)及其数学对象，用于必要的早期碰撞核查。 | `max_j(w_jᵀq+b_j)` 不是新函数类，不能以多个面/非凸选择域首次出现为贡献。 |

RPQ v1 首页仍有 PVLDB/URL 模板占位，正式 venue 应以 ICDE 2024 的 DOI `10.1109/ICDE60146.2024.00370` 区分；本次没有确认可归属作者、可配对该版本的 RPQ 实现，不把第三方索引目录当作者代码。其 Eq.9 对文中定义的距离使用正指数，和“选最近”文字存在符号疑点；缺少作者代码核实，不能直接照该公式实施或据此否定作者全部实验。

MUVERA 作者代码为 Google `graph-mining` 的 `sketching/point_cloud`，本次固定 commit `c228bf13ed1e5b679a60dc29e4dcb79bc1e15d64`。`fixed_dimensional_encoding.cc:103–194` 的 query 端按 SimHash 分桶求和，`:196` 起 document 端聚合、按桶大小平均并可补空桶；源码还提供随机投影与最终 CountSketch。它是 FDE 生成实现，不能称为所审查文件已提供完整 ACSG 路由或论文所有端到端 benchmark。[固定版本源码](https://github.com/google/graph-mining/blob/c228bf13ed1e5b679a60dc29e4dcb79bc1e15d64/sketching/point_cloud/fixed_dimensional_encoding.cc)

下载的两个 PDF、三个作者源码文件及 SHA-256 见 [manifest.json](../sources/utility_representation/manifest.json)。未运行所下载程序。PEOs、DRR 和 2026 其他路由检索仅作筛选，没有在本文件中将未完成审计的论文当作新机制证据。

## 2. 为什么保留多面入口索引

令动作池为当前真实 hubs `H`，保持 base、原 IP、冻结 NSG 和后续单入口搜索不变。对各 L 单独定义实测 `R_i(h)=Recall@10(q_i,h;L)`；不把不同 L 强称同计算预算，也不假定其 Recall 对 L 单调。

为每个 hub h 分配 `m_h≥1` 个仿射打分面：

```text
s_h(q) = max_{j≤m_h} (qᵀ w_hj + b_hj)
h_hat(q) = hub(argmax_{h,j} [q;1]ᵀ[w_hj;b_hj])
sum_h m_h ≤ M_max
```

每个面带回同一真实 hub ID。一个 hub 可以在 query 空间多块分离区域获胜，不需要几何 query 聚类、GT1 basin、base 分区或树的不可逆顶层分支。与 v4 树相比，这里所有面同时竞争；近似索引的遗漏是显式误差，而不是树根走错后整支永久消失。与单向量 GATE/NETG 相比，增加的是每动作的决策区域表达能力，而非把同一 hub 的原向量再过更深 MLP。

**该结构与多原型方法有直接相似处，区别必须由训练和容量分配证明。** 固定模式数、按 query cosine 聚类、再计算均值，仍属于已失败 residual basin modes 的近邻变体；从每入口正 query 均值初始化后停下也仍是 centroid。这里拟议每个新增面由真实反事实损失的冲突集合提出，并通过所有训练 query 的真实决策验收，允许“救回少数高损失 query，但不能在大量其他 query 上错误抬高同一 hub”这一约束反向删除面。

## 3. 核心训练不是任意唯一 ID 分类

定义 `R_i*=max_h R_i(h)`、`r_i(h)=R_i*−R_i(h)`，以及完整的同分最优集合 `G_i={h:R_i(h)=R_i*}`。不把全部近似同分正例排斥为 hard negatives。拟议使用带动作遗憾的结构化代理：

```text
ell_i(s) = max_h [s_h(q_i)+r_i(h)] − max_{g∈G_i} s_g(q_i)
```

对精确分数 argmax，有逐行代数关系 `r_i(h_hat)≤ell_i(s)`。证明只需将被选动作代入第一个 max，并用其分数不小于任一最优动作分数；不是新的普适 regret 定理。保留所有最优动作的第二个 max 是潜变量式非凸训练，可能模式塌缩，不因损失写得合理就保证收敛或泛化。首轮只用精确 Recall ties；若放宽为 epsilon-good 集合，界必须额外加入 epsilon，不能静默改变。

拟议的算法增量是**按决策损失而非几何密度分配固定总面数**：

1. 初始化每 hub 一个面，以同一全部效用向量训练作强基线；不能从 Fast top32 截断负动作。
2. 计算当前动作 `h_hat_i` 与真实最优集合，按 `r_i(h_hat_i)` 收集高损失冲突；对每个可能救回这些 query 的 h 提出少量新面。可以固定少数确定性种子，再局部优化上式；不能把单个 query 直接存为无限新原型。
3. 新面加入后，其 `max` 会在所有 query 上抬高该 hub 分数。用完整训练行重新计算真实 argmax 结果，将新伤害、净 regret 改善和增加的面数共同验收；只改善正例相似度不算通过。
4. 在固定 `M_max` 下交替增生、删除贡献小/造成误选的面及优化已有面。使用 calibration 选择一个预算和轮数，audit 冻结前完成；不给 audit 自适应分配面。
5. 与相同总向量数的固定每-hub maxout、query 几何聚类多原型、hard-ID maxout、单面模型比较。若自适应容量和 regret 目标没有独立收益，应删除这些复杂度并将方向降级。

这是拟议的条件生成/剪枝算法轮廓，未实现、无最优性保证。每次提案是否高效、面之间是否有强相互依赖、总内存与 QPS 是否可接受，均需要小型证伪。单纯把训练改名为“decision-oriented”不构成算法增量。

## 4. 把表示误差和部署近似分开

把每个面量化为 `v_bar` 后，若对给定 q 有可计算的统一 score 误差 `epsilon(q)`，且路由返回动作的压缩 score 距压缩全局最优不超过 `eta(q)`，则同一代数给出：

```text
真实入口 regret ≤ ell_i(s) + 2·epsilon(q_i) + eta(q_i)
```

例如确定的面向量残差范数给出 `|[q;1]ᵀ(v−v_bar)|≤||[q;1]||·||v−v_bar||`；这是粗上界，可能过松。上述式子只分解**已知行标签下的损失**，不是未知 query 上可认证的真实 Recall 保证。`ell_i` 在线未知，不能宣称系统知道自己离 oracle 多远。

普通 HNSW 不提供每 query 已认证的 `eta`，因此若采用 HNSW，只能在开发集做 exhaustive-score 对照测量路由选择损失；不能把索引的经验 Recall 当成该界的假设已成立。首个最小模型先不量化，分别测 exact facet scan 和微型 MIPS：前者隔离表示，后者支付实际部署近似。若后续实现按残差区间做保守候选精排，可获得 score-gap 认证，但最坏情况会扫描/精排全部面，其成本必须计入；不要为了“有界”预先叠加复杂索引。

RPQ 对本设计的启发仅在于训练/压缩必须关注后续决策，而不只是重构 MSE。RPQ 本身已经含实际搜索候选序列监督，不能声称本项目首次用 trajectory 训练压缩。我们首轮不复制其全图 PQ、不改原搜索距离，亦不把其 next-hop 距离排序等同真实入口 Recall。

## 5. 部署计算图和完整成本

```text
已有 raw query q
  → 仅拼接常数 1（或等价处理 affine bias）
  → 所有 M 个面上的微型 MIPS
  → facet_id 映射 real hub_id
  → 一次冻结原 kernel 的单入口搜索
```

不能把 learned facet 做独立 cosine 归一化后仍声称原仿射 score 等价；需要真正 IP 索引，或经验证保序的变换。一个 query 向量时 `max_h max_j` 可直接展平为所有面的 MIPS，**无需 MUVERA 的 FDE**。MUVERA 的 sum-MaxSim 适用于多个 query 向量；其单位向量误差理论也不能无条件覆盖带 bias 的 raw-IP facet。将本问题扩成多 query heads 再调用 MUVERA 会引入新在线编码和维度膨胀，不作为首轮方案。

以 `M=4H` 为只读算术示例：WebVid 815 hubs、512d 时约 3,260 个 513d 面，float32 权重约 6.38 MiB，exact scan 约 167 万 MAC/query；Yandex 821 hubs、200d 时约 2.52 MiB、66 万 MAC/query。另计索引边、ID 映射、bias、精排、状态重置和原图搜索。数千向量的小 HNSW 可能便宜，也可能因面数增大/范数差异/缓存造成路由成本超过收益；没有测量前不能称轻量成功。

离线成本包含 exact train GT 的复用身份、全部 query×hub×L 搜索、提案/优化/剪枝每轮、模型导出与微索引构建。20K×815 为每 L 1,630 万次搜索；821 为 1,642 万次。若完整标签已在授权训练切分存在可按 manifest 复用，否则不能将它视作免费。该方向可以与独立的主动标签获取结合，但不要将低秩补全假设隐含塞进本方法。

## 6. 与已失败路线逐项对照

| 既有路线 | 已有机制/失败 | 本候选必须多做的验证 |
|---|---|---|
| GATE/旧 NETG/LRSG | 搜索监督、离线表示、raw query/线性打分已有；LRSG 改逐跳评分。 | 单面同损失控制；验证多个面确实修复单面决策冲突，且无需改变原 kernel。 |
| search-aware centroid / signed residual | 唯一 oracle 标签均值；或用有符号效用权重改变一个均值表达。 | 学独立面、全局竞争并计算新伤害；不能把均值加 residual 称新训练器。 |
| residual basin modes | 几何模式拆分已有失败，不能靠增 mode 数扫参数。 | 相同面数的几何分簇控制；真实 regret 驱动容量分配须有额外收益。 |
| static utility ranker | 已有 Recall/NDC、软标签和 query–hub interaction，但 Fast32 限制。 | 全 H 竞争只是控制差异，非独立创新；另验证 facet 结构与损失各自贡献。 |
| BTG/BFS 静态扩散 | 拓扑可达/扩散代理不能等同 query 条件的有限搜索效用。 | 不以 BFS 或子图聚类构造正例；唯一主标签来自具体 query、entry、kernel、L 的真实运行。 |
| v2 Atlas | 64-query 近邻搬运局部效用，Fast8，质量差区间跨零。 | 在线不读 train query 记忆，面数固定不随训练行线性增大；不据 Atlas 失败推断 maxout 可行。 |
| v4 效用树 | 多叶可同 hub，通过 query 分支选择。 | 同训练标签/参数字节对照；面对全局竞争与单路径决策的效果、成本分别测量。 |

本地具体身份与失败边界见[旧训练器/结果审计](../../20260908_v4/reviews/local_failure_audit.md)和当前 `summary.md`；此处没有重新读取原始实验数组。

## 7. 最小可证伪验证（未授权执行）

先做两个相邻 L 的单入口设计，不加入组合、在线 probe、query encoder 或 graph-conditioned hypernetwork。fit/calibration/audit 的 query 必须物理分离；训练完整效用、命中 mask、轨迹可用来产生标签或做训练期分析，不能成为 audit/deploy 输入。不同 L 单独建模，以免跨预算误差掩盖机制。

有限候选：单面；固定总面数的 maxout；同面数的几何分簇；regret 驱动增删面。先冻结两个总预算 `2H/4H` 和明确迭代上限；不因失败追加更多 modes。全部从全 H 标签出发、同输入/同统计切分。为节省验证成本，可以先在已有授权训练标签的子样本设计开发审计，最终需要新的冻结 held-out；本轮没有执行任何一步。

三道顺序门槛：

1. **表示门槛：** exact facet scan 在双数据集隔离开发 query 上，相对同损失单面模型和 Fast1 有稳定正 Recall 增益；若仅训练集获益、或与几何多原型持平，停止将其作为高原创性候选。
2. **算法增量门槛：** 相同面数下，regret 容量分配优于固定配额 maxout/hard-ID 训练；报告救回、新伤害、活跃面、每hub面数与外推失败。无增量则仅保留普通 maxout 对照，取消新算法叙事。
3. **部署门槛：** 微 MIPS 后的损失明确小于表示收益，再测原始 query 到搜索完成的纯 wall，比较 Fast1/Fast3；graph NDC、索引 Recall、MAC 不能替代 Recall–QPS。冻结后仍遵守双数据集和 held-out 10K×3 的稳定性合同。

首轮不要求证明全空间统一误差；可以报告 score approximation 的实测分位数与明确最坏值，并标为经验量。完整的高概率 regret/索引认证理论若要成为论文主贡献，需要额外假设与证明，本笔记没有提供。

## 8. 新颖性与失败风险的最终评估

**已有部分：** Maxout 表达、多原型/多向量检索、MIPS、小索引、搜索监督、结构化 margin、压缩误差传播和基函数增删均不是首次。**潜在研究部分：** 面向真实有限搜索损失的反事实容量分配，将每入口多区域选择与完整训练期新伤害约束结合，再将表示与索引误差明确分摊到选择损失；这需要可检验的算法、对照和实证，当前尚未成立。

主要失败风险是 max-of-affine 的 hub score 本身仍凸，未必能以少数面表达复杂预算效用；训练非凸并可能靠极端范数制造误选；稀有好 hub 无足够样本；新增面竞争造成大量新伤害；固定总面数与数据维度会限制表示；微索引和 affine/IP 适配费用可能吞掉全部收益。

因此本子题建议把它作为**有清楚结构与可证伪增量的候选**加入综合比较，优先级应低于已有直接瓶颈证据、更明确独特机制的方向。不要承诺“较高原创性已确认”。低秩+残差+神经条件解码则暂淘汰：现有证据不足以让其超出现成组合，应等主动矩阵标签或其他方向确实需要时再作为工具引入。

## 附录：三分钟定向新颖性压力测试

补查日期：2026-09-08。检索组合包括 `cost-sensitive maxout`、`entry point multi-prototype nearest neighbor`、`learned entry point selection 2026`、`multiple prototypes utility routing`、`multiclass multiple prototypes cost-sensitive`。**在这次有限检索中没有确认同时采用“固定 ANN 图真实入口效用、每动作多个仿射面、固定总容量下反事实增删、面级 MIPS”的一篇完整近同方法；这不是查新证明，更不能转化为首次宣称。** 许多精确词组返回跨任务或弱相关结果，意味着检索召回有明显限制。

新增而有实际压力的近作是 **DFAMS（2025-08 预印本，ACL 2026 正式发表）**。原文 §3.3 已用同一知识源的多个 prototype，先 KMeans 初始化，再以有监督/多原型对比学习训练，在线按 prototype 相似度做检索触发和跨知识源份额分配。[正式出版页](https://aclanthology.org/2026.acl-long.1135/)、[原文 §3.3](https://arxiv.org/html/2508.20353v1#S3.SS3)、[作者仓库](https://github.com/Artessay/DFAMS)。本次读取原文方法和作者 README，未做完整源码/性能审计。其输入使用 LLM 动态信息流表示，标签主要为知识源类别；未在所读方法中看到固定 NSG query×entry 实测 regret 的 facet 增删。因此它不直接覆盖本候选全部合同，但已排除了“多原型训练后路由”“同一动作对应多语义区域”“以多原型分配检索计算”这些宽泛创新点。

另外，[Maxout](https://proceedings.mlr.press/v28/goodfellow13.html) 已覆盖最大仿射表达，[MUVERA](https://papers.neurips.cc/paper_files/paper/2024/file/b71cfefae46909178603b5bc6c11d3ae-Paper-Conference.pdf) 已覆盖多向量检索机制；成本敏感分类与损失驱动基函数增删又都是成熟工具。即使没有找到同标题 ANN 论文，**把它们按真实入口标签连接起来仍很可能只是监督多原型的任务适配**。“检测高 regret 后增加一个面”这一句不够支撑强新颖性。

因此本次压力测试后的评级保持并进一步收紧：**中等机制差异、原创性未证实，适合作为表示对照或备选，不能据现有设计优先宣称高原创主线。** 唯一可能提升评级的证据是固定同面数、同标签预算和同部署成本下，反事实冲突驱动的容量分配能系统性优于普通监督 maxout/多原型，且这种收益对应可解释、可复现的入口效用结构；若达不到，直接撤掉新机制叙事。没有因此增加网络、训练阶段、实验授权或模型设计。
