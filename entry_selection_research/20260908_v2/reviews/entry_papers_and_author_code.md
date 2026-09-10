# 入口选择原论文与作者代码核查

核查日期：2026-09-08。本文为入口方向调研的独立证据笔记，区分原文事实、作者报告、本地事实和研究推断；不构成实验 GO。先读项目交接，再复用 `research_direction_review/20260908_v1/sources/p1_routing/` 的论文材料，并联网读取原论文及作者代码。没有训练、构图、ANN 性能评测、安装依赖或读取原始 query/GT/base/图。

**主要判断：GATE 是最接近 Fast 的直接前作；PSP 的 Spherical Navigation 是 raw-IP 候选构造的重要前作；MAG 是改变搜索语义的边界对照。现有文献不能单独支持优先重建候选池，也不能证明复杂模型可以选中本地历史 oracle 入口。尤其不能将 Fast 相对 GATE 的优势解释为免除了作者实现中的在线 query MLP，因为所核实 release 没有该在线步骤。**

## 1. 版本、阅读覆盖与证据身份

页码均为 PDF 页码，从 1 开始。源码审查属于静态读取，未运行作者程序。

| 工作 | 原论文版本、实际阅读范围 | 作者代码身份及范围 |
|---|---|---|
| GATE，*Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities*，KDD 2025 | [arXiv:2506.15986v1](https://arxiv.org/pdf/2506.15986v1)，2025-06-19；方法 §4.1–4.4，pp.5–7；实验 §5，pp.7–9；另读问题定义和引言。版本页未列后续修订。 | 论文指向 [Zenodo v0.0.1](https://zenodo.org/records/15523071)，对应 `jacksondca/gate` commit `229f18dadb791ddede22597e44d5ceb028b104ba`，2025-05-25。检查聚类、样本、模型、训练、推理测试和底层搜索。 |
| PSP，*Maximum Inner Product is Query-Scaled Nearest Neighbor*，PVLDB 18(6):1770–1783 | [arXiv:2503.06882v2](https://arxiv.org/pdf/2503.06882v2)，2025-07-23；先读 v1，再核对 v2 的 §4–5；入口 §4.1–4.2，pp.6–7；SN 消融 §5 Exp-3，p.11。正式 DOI：[10.14778/3725688.3725705](https://doi.org/10.14778/3725688.3725705)。 | [ZJU-DAILY/PSP](https://github.com/ZJU-DAILY/PSP)，本次 main 为 `d3eb2e09059828a883ce96c9f6a9b98a39e824ed`，2025-10-31。重点 `test/test_mips_search.cpp`、`src/index_mips.cpp`，并定位 build/header/仓库树。 |
| MAG，*Stitching Inner Product and Euclidean Metrics for Topology-aware Maximum Inner Product Search*，SIGIR 2025 | [arXiv:2504.14861v2](https://arxiv.org/pdf/2504.14861v2)，2025-07-23；先读 v1，再核对 v2 §3.2、§4 和 §5；ANMS §4.2，p.6；实验设置 §5.1，p.7。 | [ZJU-DAILY/MAG](https://github.com/ZJU-DAILY/MAG)，main 为 `cbabb2b7d06d0a2e7f171219686aa49b72edf4ea`，2025-08-23。重点 `include/index_mag.h`、`test/test_mag.cpp`。 |
| LIRA，*A Learning-based Query-aware Partition Framework for Large-scale ANN Search*，WWW 2025 | 复用既有逐页材料及[作者全文](https://zheng-kai.com/paper/2025_www_zeng.pdf)；既有核查覆盖 §3，pp.4–6；§4 和 Appendix A.3–A.6，pp.6–8、11–14。本次没有重新逐页审阅全文，以既有核查和下述源码补查为限。 | 本地准备版本 `7beeee52d5b9a880f443876e24563713146ef581`；本次在线获取该 commit 的 `LIRA_largescale.py`，与本地逐字核对。[作者文件](https://github.com/SimoneZeng/LIRA-ANN-search/blob/7beeee52d5b9a880f443876e24563713146ef581/LIRA_largescale.py)。 |

小型作者源码副本与 URL、commit、字节数、SHA-256、既有本地副本一致性保存在 [download_manifest.json](../sources/author_entry/download_manifest.json)。GATE 的八个所存文件全部与本地 `GATE/gate_old/jacksondca-gate-78334b4/` 对应文件逐字一致；该目录名中的 `78334b4` **不是**本次核实的 release commit，不能拿它代替版本记录。新保存副本未被编译或运行。

## 2. GATE：概念高度接近，但论文、release 和本地适配必须分开

### 2.1 原文事实与作者报告

§4.1 用 base 侧 balanced hierarchical k-means 选真实 hub；§4.2 为 hub 采样局部子图并用 Graph2Vec 等方法编码，同时收集 query×hub 实际 NSG 搜索 hop；§4.3 学习 hub 表示，再在小型导航图检索入口。论文 Definition 4 的正查询阈值相对**固定 hub 在查询集上的最小 hop**，并非 GT10 区域占比，也不是 Recall@10 或总延迟目标。§4.4 明确标签准备为 `O(|Q|·|H|·S)`。

§5 使用 512 hubs、五个数据集，平台为 Xeon E5-2650 v4/128GB，建图 48 线程、查询单线程、重复 10 次。约 1.2–2× 加速是作者报告，未在本任务复现。论文问题定义采用 L2；不能仅因包含 Text2Image10M 就认定其为当前 Yandex raw-IP 契约。[论文](https://arxiv.org/pdf/2506.15986v1)

### 2.2 五项关键实现差异

1. **没有在线 query MLP。** `tests/test_gate_search.cpp:56–68` 读入已导出的 hub embedding，构建 cosine HNSW；`:99–108` 直接使用原 query 搜 top-3 embedding 并映射真实 base IDs。`model.py` 的输入为 hub node/graph features；训练 query 正负向量直接进入损失。在线成本包括 cosine 小索引检索和图搜索，不能凭“两塔模型”名称加上不存在的 query 神经网络。[在线源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp#L56)、[模型](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/model.py)
2. **样本阈值的比较方向不同。** 论文 §4.2 定义 `H(q,h) ≤ min_q′ H(q′,h)+t_pos`。release `combine_ep_gt.py` 将数据转为 query×hub 后，按每 query 的 `min(array)` 选正 hubs；`get_hop_count` 对未命中 GT 的结果标 999，负样本又采用另外的筛选。这是公开版本差异，不能据此推断作者所有论文实验究竟用了哪个未公开配置。[样本源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/experiment/combine_ep_gt.py)
3. **release 实际使用 cosine triplet loss。** `cluster/model/train/__main__.py:35–39` 的 InfoNCE 调用被注释，启用 `TripletMarginWithDistanceLoss(1−cosine)`；`:57–59` 对 hub embedding 和原 query 正负样本求损失。模型也含 TransformerEncoder，不能以论文示意图中的“轻量 MLP”完整描述该 release。[训练源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py#L35)
4. **返回 hop 不是 NDC，也不是严格最短路径距离。** `src/index_nsg.cpp:645–662` 用 BFS 填初始池；`:684–697` 把首次发现节点标为父节点 hop+1；visited 后没有最短路松弛；`:712` 返回结果节点的发现 hop。论文将 H 称为 shortest-path hop，而该 release 提供的是具体有限搜索过程中的发现路径长度。[搜索源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/src/index_nsg.cpp#L618)
5. **release 不是可直接执行的 CPU/raw-IP 完整基准。** 测试文件硬编码 L2；`argc != 7` 检查又与后续访问 `argv[7]/argv[8]` 不一致。聚类文件包含 `.cuda()`，所读聚类实现没有论文 Algorithm 2 的显式平衡惩罚。上述事实意味着需要记录适配；不等于论文性能被否定，也不许可把修好的本地版本称为作者原件逐位复现。[聚类源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/kmeans.py)

### 2.3 本地 10K 适配的证据边界

[本地 standalone GATE 分析](../../../gate_baseline_artifacts/webvid2_5m_frozen_r64_v2/analysis.md)的合同为同一冻结 WebVid NSG/raw IP、512 balanced HBKM hubs、每 hub 1,000 节点 topology-only 子图、WL(2)+PV-DBOW 512d；只用旧 prototype-train 前 10K 训练，使用 validation 10K 选择 checkpoint，最终以 dense cosine top-3 路由评测。它采用文档化 Sinkhorn 平衡分配和 gensim Graph2Vec 适配，是本项目独立版本。

该结果在全部 12 个已测 validation 点的 Recall 上低于 Fast，并使用更多 graph NDC；Yandex 因 gate 未继续。它不是新 20K paired Fast 的公平复验，不是作者原论文的全条件复现，也没有提供已验收的当前完整路由加搜索成本前沿。报告中的“dominated”应结合上述 Recall/graph-NDC 口径解读，不能自动改写为新纯 wall 的结论。训练记录约 46m42s 只是该适配训练阶段，不含全部标签、聚类、子图、Graph2Vec 和索引准备。

**研究推断：** 入口选择、搜索监督、图感知、hub 小索引均已被 GATE 覆盖。Fast 可强调省去逐 hub 标签搜索和 optimizer，不能声称它相对 release 省去了在线 query MLP。若新方案学习条件增益，须说明目标、信息和标签预算与 GATE、旧 NETG 和已失败 ranker 的具体区别。

## 3. PSP：角度覆盖与原始范数是现成候选构造轴

### 3.1 原文机制和限制

PSP 的 Spherical Navigation（SN）在 base 的单位球投影上做聚类，以保持角度覆盖；再按各簇原空间范数分布抽取真实 navigation nodes，存入 IVF。查询以 cosine 选择最近簇，从该倒排表随机取节点填初始化池。论文明确辅助归一化仅用于入口 ID 选择，主图仍在原空间用 IP 搜索。

作者在 §5 Exp-3/p.11 报告 SN 在五数据集平均约 +6.2%，但其完整系统还包含 NSSG、额外 spherical pathways 和 AET；这个数字不是当前冻结 NSG/三个入口的本地效果。[v2 原文 §4.1–4.2](https://arxiv.org/html/2503.06882v2#S4)

### 3.2 作者源码和计时边界

- `test/test_mips_search.cpp:89–105` 中 SN 初始化和调用被注释，默认实际调用 `Search_Mips_IP_Cal_with_No_SN`。
- 可选 SN 路径通过 `read_kmeans` 读取已经生成的 `query_cluster` 和簇内节点；该步骤在 timer 之前。公开测试文件没有展示 timer 内对新 query 完成 cosine 选簇。
- `src/index_mips.cpp:616–640` 接受外部 `init_nodes`：先生成长度 L 的随机数组，填入 graph entries 和提供的 IDs，再计算 IP。初始化规模和语义不同于 Fast 固定三个入口。

[作者测试](https://github.com/ZJU-DAILY/PSP/blob/d3eb2e09059828a883ce96c9f6a9b98a39e824ed/test/test_mips_search.cpp#L89)、[作者搜索](https://github.com/ZJU-DAILY/PSP/blob/d3eb2e09059828a883ce96c9f6a9b98a39e824ed/src/index_mips.cpp#L616)

**研究推断：** 可把 SN 的 norm/angle 原则列为限定候选池对照，但必须支付 base 扫描、聚类/分配、候选保存、在线选簇和原图搜索成本。无 query 标签不等于零离线成本。WebVid 近单位范数令“高范数优先”的区分信号可能较弱；Yandex raw IP 有适用动机，但具体效果未知。只迁移入口部分、固定原 NSG 和入口数时，应标为“受约束 SN 思想对照”，不能宣称复现完整 PSP。PSP 默认代码未覆盖 SN 的在线选簇计时，不足以确认其完整在线成本。

## 4. MAG：双度量导航是搜索策略，不是廉价静态入口匹配

原文 §4.1 混合 Euclidean 和 IP 导向边，§4.2/p.6 先运行 L2 导航 m 步，再切换 IP 继续搜索。§5 报告 12 数据集、Recall@100、CPU 检索及三轮重复。作者报告的是联合索引/搜索收益，不能当作固定图入口层收益。[v2 原文](https://arxiv.org/pdf/2504.14861v2)

所核实 `include/index_mag.h:626–737` 与论文参数化描述仍有差别：固定 `L_NN=5`，先执行该 L2 池的完整搜索，再清空 visited；后续 IP 初始化保留五个 L2 结果，其余位置用离线按范数排序的 base 节点填充。它没有把前段严格限制为 m 次扩展，两个阶段还可能重复访问和距离计算。`:613–624` 的候选准备扫描并排序全部 base；`test/test_mag.cpp:90–98` 在计时前准备该列表，计时包含两阶段搜索。[核心源码](https://github.com/ZJU-DAILY/MAG/blob/cbabb2b7d06d0a2e7f171219686aa49b72edf4ea/include/index_mag.h#L613)

**研究推断：** 该工作支持“norm/angle 作用不同”是已有研究对象，却不能作为当前有限 20K 查询、冻结图、固定搜索语义方案的直接收益证明。迁移预搜索会改变搜索策略，且与已失败 probe-reroute 类方向存在成本问题；不得只给它“入口匹配”名称就排除前段成本。

## 5. LIRA：保留为分片路由前作，勿当作同图入口基线

既有[路由文献复审](../../../research_direction_review/20260908_v1/reviews/routing_partition_literature.md)已核对 LIRA：预测分区是否含 kNN 的二元多标签，模型参与数据复制和 probing，每个分区重建独立 HNSW。它不是在当前同一全图上选择几个真实入口。论文主配置使用大规模 base 子集训练和数据冗余，不能等同本项目 20K 历史查询条件。

本次源码复核：`LIRA_largescale.py:51` 明确部分数据集采用 `inner_product`；`:210` 强制选择 CUDA；`:257` 为 query 与到所有中心距离的双输入 MLP；`:122–163` 先逐 query×partition 获得搜索结果，再在 `query_tuning` 汇总选中分片的预计算命中/工作量。因此只能确认有 IP 实现，不能据此确认 CPU 端到端在线复现或当前 raw-IP/20K 公平性。[固定版本源码](https://github.com/SimoneZeng/LIRA-ANN-search/blob/7beeee52d5b9a880f443876e24563713146ef581/LIRA_largescale.py)

## 6. 对方案比较、成本和证伪设计的约束

| 研究轴 | 本次文献带来的约束 | 仍需本地证伪的事实 |
|---|---|---|
| 候选池 | HBKM、角度覆盖、高范数候选均有前作；重建全池的 base 扫描/聚类不能漏计。 | 同样入口数、相同搜索语义下，预先限定的扩展池是否比当前池提供额外空间；更换池是否反而更难选择。 |
| 短名单与排序 | GATE 已学习 query–hub 适配，并通过小索引避免在线全扫；新颖性不能落在“真实搜索监督”本身。 | 好入口是否进入廉价短名单、短名单内部排名能否在隔离查询上改善，新增成本是否超过节省的图搜索。 |
| 真实入口组合 | 本组论文没有证明固定 NSG 共享 beam 的单调性或子模性。 | 单入口好不等于组合好；真实联合搜索相对现有入口是否有正/负条件增益，以及该差异是否可预测。 |

完整离线成本至少包含 exact train GT、额外搜索标签/轨迹、候选构造、表示学习和路由索引；缺失耗时应写 null 和原因。全 20K×815 标签矩阵为 **1,630 万次搜索/预算点/数据集**，20K×821 为 **1,642 万次**；这是未运行的算术预算，不能叫“轻量训练”。小样本、稀疏候选、有限真实组合应有明确标签预算，并将标签稀疏带来的覆盖缺口与预测失败分开。

在线成本必须包含 query 归一化、候选检索、评分/组合决策、去重/状态重置和原图搜索。paper 的 hop、graph-only NDC、免费 oracle 和完整 latency 均是不同对象。若目标是组合增益，应直接使用受控的真实联合搜索结果，不以独立单入口命中并集作标签真值或部署结果。

**本笔记不单独选定一个已有效的方法。** 对综合报告的建议是：当前更适合围绕现有池和廉价短名单检查选择/组合损失，先证明存在可预测、能支付路由成本的条件增益；不要因原论文中某个组件成功就直接重建全池或叠加模型。若新候选与旧静态 utility、probe-reroute 或 Multi-view 在目标与输入上没有实质差异，应明确不推荐，而不是重命名重启。

## 7. 文献覆盖限制

- 本文没有穷尽全部入口论文；自适应入口理论、2026 批查询复用、SOAR、FES/PilotANN 和其他近期检索由本版本其他笔记覆盖。
- 精确检索 `PEANNS` / `PE-ANNS` 未确认对应 ANN 原论文；不把未知缩写编造成相关工作，不据此声称该工作不存在。
- GATE 论文、release、本地 raw-IP 适配三者已分开；发现差异不等于证明论文实验采用错误实现，也不能从本地适配失败否定所有 GATE/入口学习。
- PSP/MAG 只审查与当前入口研究相关的机制、实验设置和作者搜索/测试文件，未逐式重证全部理论。理想图定理不能自动迁移到当前有限 beam 的冻结 NSG。
- 作者结果均未独立复现；公开文件缺少的配置、完整标签成本和计时阶段不由猜测补齐。
- 本轮允许的新增内容只有调研文档及小型一手源码证据；原源码、二进制、环境、数据、模型和历史 gate/state 均不改。
