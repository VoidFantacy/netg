# 候选入口、几何导航与少量入口组合：一手证据核查

核查日期：2026-09-08。范围为入口候选构造、query 到入口的匹配、少量入口组合；本文是调研证据笔记，不是新方法 GO 或实验结果。已读取项目 AGENTS、summary、spec 和本轮提示词，复用 `research_direction_review/20260908_v1/` 的论文材料，另外定向查阅近期原论文和作者源码。没有训练、构图、ANN 性能评测、依赖安装或原始 validation/held-out query/GT 访问。方法源码未修改。

**研究建议：优先证伪“保留 Fast 主入口、学习真实三入口联合收益”。** 理由是它改变了旧单入口 utility ranker 的监督对象，而且能在一个固定小短名单内完整枚举，从而较清楚地区分排序损失和组合损失。现有证据尚不能支持部署收益，也不足以承诺论文新颖性。候选池缺失、联合收益大小和廉价可预测性均需要未来有界验证。

## 1. 文献事实与本地可比性

### kRt/hRt：多代表分片路由，不是 query 标签学习或联合入口优化

- **版本与阅读位置：** Gottesbüren 等，*Unleashing Graph Partitioning for Large-Scale Nearest Neighbor Search*，PVLDB 18(6):1649–1662，2025，DOI `10.14778/3725688.3725696`。[正式全文](https://www.vldb.org/pvldb/vol18/p1649-gottesbueren.pdf)。重点核对 §2–3，尤其 §3.1–3.2、PDF pp.4–5 / 刊物 pp.1652–1653；实验边界见 §4。已复用本地 `sources/p1_routing/krt.pdf` 与按页提取文本。
- **论文机制：** 每个 shard 内层次 k-means，产生多个代表以描述非凸片区；在代表集合上用树或 HNSW 检索，然后给 shard 排序。无需 query 标签训练。作者发现频数排序对第一 shard 较好，对后续排序较弱，并比较“第一片按频数、剩余按距离”的混合策略。kRt 是经验较强的方法；LSH 理论属于 hRt。
- **作者实现：** 已核对本地未修改文件，commit `df5efb4a6b303011c795666ed267f29d994b558c`。[src/hnsw_router.h](https://github.com/larsgottesbueren/gp-ann/blob/df5efb4a6b303011c795666ed267f29d994b558c/src/hnsw_router.h) 中 `HNSWRouter::Query` 把近邻代表点映射到 shard，累计 `min_dist/frequency`；`FrequencyQuery` 仅将最高频 shard 放第一，其余按最小距离排序。[src/route_search_combination.cpp](https://github.com/larsgottesbueren/gp-ann/blob/df5efb4a6b303011c795666ed267f29d994b558c/src/route_search_combination.cpp) 合并独立 shard 检索的命中 ID，并累计片内搜索时间。
- **本地限制：** 它解决的是独立分片搜索，不是原 directed NSG 中共享 beam 的多个入口。论文 TTI 使用 inner product，但 hRt 的 ℓp、p∈[1,2] 理论不能移植为 raw-IP 保证。论文 QPS 使用分布式顺序模拟/最慢主机归因，不是本地 16-thread 整批 wall。不能从“选到 shard”推导“从某入口能在有限 L 内得到目标”。
- **对方案的约束：** 多代表表示非凸区域已有前例；仅把一个 prototype 改成多个 prototype 不构成独立创新。它支持设置一个简单多代表几何对照，不支持复活硬区域容量方案。

### RoarGraph：query-guided 改图，实际搜索以固定单入口开始

- **版本与阅读位置：** Chen 等，*RoarGraph: A Projected Bipartite Graph for Efficient Cross-Modal Approximate Nearest Neighbor Search*，PVLDB 17(11):2735–2749，2024。[正式全文](https://www.vldb.org/pvldb/vol17/p2735-chen.pdf)。本次实读 §3.2、§4.1–4.2.4，刊物 pp.2739–2742，另核对 §5.5–5.7 样本/成本段落；复用既有 PDF，未重复下载。
- **论文机制：** 先计算历史 query GT；建立 query→base 近邻关系，最近 base→query 的受限反向关系；随后投影到 base 图并补充连通性。论文 §3.2 指出 OOD top-k 目标可能分散，抵达一个近邻附近未必容易收集其余近邻。此论述支持“入口好坏不能只看几何近”，不证明当前 NSG 的实际瓶颈。
- **作者实现：** 已核对本地未修改文件，commit `7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e`。[src/index_bipartite.cpp](https://github.com/matchyc/RoarGraph/blob/7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e/src/index_bipartite.cpp) 的 `CalculateProjectionep`（L2004）取 base 均值最近的 **L2** 节点；`SearchRoarGraph`（L2311）仅把 `projection_ep_` 放入初始化列表，后续遍历投影图。不能将其误报为现成的 query-aware 入口选择器。
- **完整成本与限制：** §5.5 最小训练 query 配置为 base 的 10%，仍远大于当前 20K；§5.7 中 query GT 预处理占完整构建时间 87%–93%。论文 T2I 是 IP，WebVid/LAION 是 cosine；本地 raw-IP 契约和 CPU 资源不能据论文速度比直接复验。这里的主收益属于改图系统，不能混入纯入口同图归因。
- **对方案的约束：** query GT 共现及目标间可达性已经是图构造前作的核心；把它缩小为新 pool 或辅助图不自动产生新颖性。当前用户固定图，本文不建议触发 RoarGraph 式改图。

### Adaptive Entry Point Selection：base 几何候选的直接先例

- **版本与阅读位置：** Oguri、Matsui，*Theoretical and Empirical Analysis of Adaptive Entry Point Selection for Graph-based Approximate Nearest Neighbor Search*，arXiv `2402.04713v1`，2024-02-07。[版本页](https://arxiv.org/abs/2402.04713v1)、[全文](https://arxiv.org/html/2402.04713v1)。实读 §3.3、§4.2–4.3、§5.1–5.4；本笔记只使用明确锁定的 v1，不声称核对全部后续版本。
- **论文机制：** 对 base 做 k-means，每个中心取最近真实 base 节点为候选，再以 query 距离选择入口。§4 在 Euclidean Voronoi/B-MSNET 等条件下比较路径 hop 上界；这不是实际有限 beam 的 Recall–QPS 保证，更不是 raw-IP 的保证。§5 包含 1M 规模的 Yandex/CLIP OOD 实验，但不包含当前 10M/raw-IP/Fast 设置。
- **实现证据边界：** 原文 §5.1 明确使用 Faiss NSG/k-means 与官方 DiskANN。本次论文 HTML 和定向检索未能确认专用作者仓库，故**不能写成已核对该论文完整作者实现，也不能断言作者没有代码**。
- **成本与限制：** 候选准备需 base 聚类、真实节点映射与路由索引；论文选取的较优配置与本地 hub budget 不同。论文对 vanilla 单 medoid 的收益不能等同于对已经 query-aware 的 Fast 的收益。
- **对方案的约束：** “聚类→真实节点候选→按 query 距离选入口”已有明确先例。重建 pool 必须显示其超出 base 几何或 QGT 现有池的必要性。

### PilotANN FES：GPU 分桶距离计算，不是入口效用监督

- **版本与阅读位置：** Gui 等，*PilotANN: Memory-Bounded GPU Acceleration for Vector Search*，arXiv `2503.21206v1`，2025-03-27。[版本页](https://arxiv.org/abs/2503.21206v1)、[全文](https://arxiv.org/html/2503.21206v1)。核对 §5、§6.1、§6.3；出版状态仅按已核实的此 arXiv 版本记录。
- **论文机制：** Fast Entry Selection 将入口向量组织为少量粗簇；query 先选最近簇，再在对应簇内进行可按块复用的距离计算。论文 `r=32` 配合 GPU warp，重点是批量计算密度及减少不必要距离。整体系统还包含 GPU 子图、SVD 紧凑向量和 CPU 精炼，不能将整体速度归给入口组件。
- **作者实现：** 检索时 commit `0aee5f6c5d34158587d95e2aa5309c9a9529943a`。[pilot_ann/layers/entry.py](https://github.com/ytgui/PilotANN/blob/0aee5f6c5d34158587d95e2aa5309c9a9529943a/pilot_ann/layers/entry.py) L48–61 调用 `router_init` 并保存入口/路由向量；L79 明确 `query.is_cuda is True`，L81–85 调 `routing_cuda`。这些路径没有真实搜索效用标签。这里核对的是入口模块，不声称审计全部内核。
- **本地限制：** FES 主要速度依据是 GPU 批处理密度；当前 CPU-only 条件不能直接使用该论证。把几何分桶移植为 CPU 代码属于独立适配，必须核验 raw-IP、完整路由成本、候选遗漏和单 query 行为。

### PathWeaver ghost staging：主图之外的小导航层也已有直接先例

- **版本与阅读位置：** Kim 等，USENIX ATC 2025，pp.1501–1517。[正式出版页](https://www.usenix.org/conference/atc25/presentation/kim)；本次正文使用 arXiv `2507.17094v1`，2025-07-23，[全文](https://arxiv.org/html/2507.17094v1)。核对 §3.2、§5.6.2、§6.1 与实现可用性部分。
- **论文机制：** 从 base 随机采样小集合建 ghost 图，先在辅助图搜索，再转入原图；§6.1 特别区分这种在已有图外加入口导航层的目的。系统还包括多 GPU 路径传递及方向筛选，它们的收益不能混归为入口选取。
- **作者实现：** 检索时 commit `c0804a5f46fd603794f4ce6205956a35ca46890e`。[pathweaver/single_pathweaver_one.py](https://github.com/AIS-SNU/PathWeaver/blob/c0804a5f46fd603794f4ce6205956a35ca46890e/pathweaver/single_pathweaver_one.py) L107–117 用 `np.random.randint` 采样并调用 CAGRA 构建 ghost 图；L138 设置 `ghost_topk=1`；L214–216 先搜 ghost，再将 top1 映射到 base 搜主图。单 GPU 入口路径是几何单入口导航，非 query 标签学习或少量入口组合。硬件要求与路径入口见[固定 commit README](https://github.com/AIS-SNU/PathWeaver/blob/c0804a5f46fd603794f4ce6205956a35ca46890e/README.md)。
- **本地限制：** CAGRA/GPU/L2 实现和本地 CPU/raw-IP 有明显适配缺口。论文采样率结论不是本地最优预算；不能据此把更小的多层导航索引直接称为新方法。

## 2. 三个实质不同方向与主动反驳

| 方向 | 机制、监督与成本 | 最可能失败之处及新颖性边界 |
| --- | --- | --- |
| A：重建固定预算候选池 | 从 fit GT1/GT10 的真实节点或 base 几何代表中选池；重建 prototype、路由索引、标签及全部下游结果。完整离线成本包含 exact GT、选池、真实节点映射、模型/索引构建。 | 当前历史 815 池的免费单入口 oracle 已强，尚无“缺池为主要瓶颈”证据。20K 易漏稀有目标；query guided、几何候选均已有先例。不能把 pool 改动和排序改善混在一项比较中。 |
| B：固定池/短名单的单入口 utility 排序 | 同一 Fast view 检索短名单；离线使用单入口 Recall/NDC 标签，在线廉价 scorer 选 top-3。 | 与旧 `sparse_utility_ranker_results/analysis.md` 的 top32、真实单入口标签、diagonal listwise 机制高度重叠。旧结果 WebVid 小幅正向但 Yandex 成本匹配失败。仅更换 loss/MLP 或扩大模型不足以解释新成功机制。 |
| C：anchor 条件的真实三入口组合选择 | 固定一个小短名单、保留 Fast rank-0；标签直接来自每组三入口在同一 shared-beam 内的真实搜索。在线只计算组合分数，再一次搜索；不在线 probe、不读取 GT。 | 没有证据保证组合收益大或可预测；anchor 可能排除好组合，短名单可能漏入口，静态几何特征仍可能不足。监督对象的改变是与旧 ranker 的实质差异，但真实监督/学习入口/图感知本身已被 GATE 和旧 NETG 覆盖。 |

**唯一推荐是 C 的有界证伪，不是正式方法实施。** 它允许在固定小候选族内分离“单入口排序不准”和“单入口效用不能代表联合行为”。如果联合族没有实际剩余空间，或者只在免费 oracle 中有空间而廉价预测失败，就停止这个版本，不扩大模型、短名单或参数扫描。

GATE、旧 NETG/Fast 的完整对照由本轮主报告和专门 routing 核查负责。本笔记不独立重述尚未在本子任务中完整审计的 GATE 源码；相关新颖性主张必须与那份证据合读。

## 3. 最小可证伪机制检查建议

以下是输入主协议的机制建议，**未实现、未执行，也不是可直接运行命令**。样本数量、命令、统计族和资源上限以本轮主报告的冻结草案为准。

1. 固定原 NSG/raw-IP/K10、同 20K paired Fast、一个 Fast view 的 `C8`；C8 必须含原始 top-3 和 rank-0 anchor。固定 route 顺序、去重、默认图入口和真实消费语义。
2. 枚举 `(anchor,u,v)`，最多 `C(7,2)=21` 个三入口组合。所有标签都是**共享 beam 真实联合搜索**，不是独立单入口命中的并集。该 oracle 只是固定候选族内乐观诊断，不是全池所有三入口的最优值。
3. 以固定 fit/pilot 小样本分别保存：全池单入口 oracle、C8 单入口 oracle、单入口效用排序选 top-3 后的真实重放、21 组真实联合 oracle。前两项分离短名单损失；pool 的改进还需独立候选池对照，不能仅靠当前池 oracle 推出。单入口排序重放与联合 oracle 的差异用于检验组合剩余空间。
4. 先检验有限族联合 oracle 相对单入口排序重放是否存在足够大且跨数据集的收益；没有则停止。若有，再用仅 fit 拟合的廉价 scorer 在未参与拟合的历史 pilot 检验 paired 收益和 harmed/rescued。不能用 pilot oracle 标签调整 scorer 后继续将该 pilot 当未参与选择数据。
5. 在线计时必须计入短名单检索、特征与组合评分、归一化、去重/reset、真实搜索及结果写入；GT、hash、trace、JSON 在计时外。计数独立，plain/count 返回 ID 一致。只改善同 L Recall 或 graph NDC 不够；完整 Recall–QPS 门槛保持项目标准。
6. 离线显式报告每 query/L 最多 21 次联合标签搜索、额外单入口诊断、exact GT、候选构造、训练、路由索引、峰值内存与文件字节。复用缓存不等于真实成本为零；缺失历史耗时填 `null + reason`。

需要记录的失败包括：短名单漏选；真实联合 oracle 无剩余空间；收益仅集中少数历史 query；共享 beam 交互在 query 侧特征中不可预测；路由成本抵消收益；anchor 限制造成系统性伤害；不同 L 需要相反选择。共享 beam 的候选竞争和有限容量使加入口后的行为不能从单入口集合直接相加；本文不主张已经证明这种效用具备单调性或子模性。

## 4. 可复核材料与证据缺口

源码快照及 SHA-256 见 [`../sources/author_candidates/manifest.json`](../sources/author_candidates/manifest.json)。本次保存 6 份小型源码/README 快照，约 135 KB：gp-ann 两份、RoarGraph 一份、PilotANN 一份、PathWeaver 两份。gp-ann/RoarGraph 的本地读取文件在记录 commit 下 `git status --short -- <files>` 为空；其他快照通过固定 commit 的 raw URL 获取。manifest 同时记录复用 kRt/RoarGraph PDF 的原路径、URL 和 SHA，未复制大文件。

没有完成 Adaptive Entry 专用作者实现核验；没有进行 PilotANN/PathWeaver 全系统代码审计；没有发现足够证据证明所建议的 anchor 组合学习在本地 CPU/raw-IP/20K 条件下有效。2025 的新增入口相关材料扩大了近期覆盖，但定向检索不是穷尽式新颖性证明。以上缺口不能通过本轮自行运行实验补齐。
