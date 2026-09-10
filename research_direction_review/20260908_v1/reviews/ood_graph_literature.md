# OOD／跨模态 ANN 图拓扑文献复审

检索截止：2026-09-08；范围为六篇实读论文，另列一篇全文不可得的直接近邻。这里只做文献分析：未运行项目实验，未读取项目 GT、图、base 或 held-out，未修改源码、旧实验控制目录或交接文件。对本项目的判断是结合任务提供的 P3 失败背景提出的研究建议，当前本地结果由主审另行核验。

**建议修改计划，但现有文献不足以宣布“必须改图”。** 需要取消的是“把目标集中到少量硬区域，再增加预测器复杂度，就会自然转化为搜索收益”的默认推进逻辑。论文更支持先区分到达目标附近与继续收集其余近邻的成本，再决定是否值得改变边；它们同时要求保留实现优化强基线。查询引导图和修补目标邻域连通性已有直接先例，不能把这一层概念本身写成新贡献。

| 论文、版本与一手来源 | 实际阅读范围与可采信证据 | CPU、metric、split 和外推限制 |
|---|---|---|
| **RoarGraph**，PVLDB 17(11), 2735–2749，2024。[出版全文](https://www.vldb.org/pvldb/vol17/p2735-chen.pdf)；[作者代码](https://github.com/matchyc/RoarGraph) | 实读 §2–3 的 OOD 诊断、§4 的方法与算法、§5.1–5.7 的主实验/消融/成本，重点印刷页 2739–2745。通过 query→近邻的二部关系把空间上分散的目标连接起来，再补足可达性。§5.4 也显示补边在低 recall 区间会增加开销；“边更多”并不单调更好。§5.7 的完整建图包含昂贵的 query GT 预处理。 | 双 Xeon Gold 5318Y，512GB；单线程检索、64 线程建图。T2I 10M 为 IP；LAION 10M 与 WebVid 2.5M 为 cosine。测试 10K，与建图 query 不交；主设置 query 量可达 base 等量，敏感性最小为 10% base。不能把论文 WebVid 当作本地 raw-IP 等价实验，不能把 250K–1M 的“小样本”收益移植到 20K fit。 |
| **OOD-DiskANN／RobustVamana**，arXiv v2，2022-11-30；历史奠基论文，非 2024–2026 新作。[版本页](https://arxiv.org/abs/2211.12850v2)；[全文](https://arxiv.org/pdf/2211.12850v2) | 实读 §1.1–1.3、§2/算法 2–4、§4、§5（PDF 页 2–4、6–8）；§3 仅核对量化角色，未逐式复核 APQ 推导。RobustStitch 用临时 query 节点给 base 添加跨接后删除 query 节点；全文总收益还包含 query-aware PQ 与 SSD 排列，不是纯图收益。§2.1 的 Web Ads 基本无改善，是自身的负例。版本仍标 Under Review，本次未确认正式录用。 | 双 Xeon Gold 6140，500GB，Samsung PCIe SSD；§5 为 16 检索线程、SSD beam width=4。含 Yandex 1B/Turing 87M/Web Ads 2.4B，测试 100K/30K/100K，build/eval 随机不放回；query 样本约 base 的 1–2%。图规则以 L2 范数表达，本次未确认 Yandex 的完整 metric 转换实现；不能直接主张与本地 raw-IP 内存检索公平可比。 |
| **Dynamically Detect and Fix Hardness…（NGFix／RFix）**，arXiv v1 2025-10-25；PACMMOD 3(6), Article 318，2025-12；作者注明 SIGMOD 2026 accepted。[全文](https://arxiv.org/html/2510.22316v1)；[出版 DOI](https://doi.org/10.1145/3769783)；[作者代码](https://github.com/yuhuifishash/NGFix) | 实读 §4、§5.1–5.4、§6.1–6.6、§7；PDF 页 6–13、15–24。EH 衡量连接两个目标所需路径中最差的 query 距离排名；NGFix 修目标邻域，RFix 修进入邻域的失败。Theorem 5 只保证历史 query，且要求不剪边；§7 明说新 query 保证仍需扩展。其邻域修补与我们的潜在“目标可达性图”高度接近。 | Xeon Gold 5220，256GB；统一距离函数，单线程检索、32 线程建图。T2I/IP 与 WebVid/cosine；主表历史 query 分别 10M/2.5M，测试去重 10K；MainSearch 末尾 50K 作时间测试。主要结果 k=100，另报 k=10。必须保留 GT 计算、额外度数与训练样本成本，不能用其全量历史 query 结果证明 20K 下可泛化。 |
| **PAG: Projection-Augmented Graph**，arXiv v2 2026-07-21；作者注明 ICML 2026 poster。[版本页](https://arxiv.org/abs/2603.06660v2)；[全文](https://arxiv.org/html/2603.06660v2) | 实读 §1.2、§2–4、§5、附录 F 环境/基线；PDF 页 3–9、附录 F。这里 projection 是随机投影的距离筛查，不是 RoarGraph 的二部图投影。PES 从更多已访问节点发现入边候选，再精确剪枝；TFB 重用已算距离的候选。消融支持同时考虑搜索计算与图连通性，但不是查询样本引导修图的直接验证。 | Xeon Platinum 8276L/AVX-512，754GB；单线程检索、112 线程建图。唯一明确 OOD 的 DataCompDr 为 12.78M×1536、Euclidean，测试 1K；无 WebVid/Yandex raw-IP 实验。在线插入实验另从 corpus 抽 query，该设置不再 OOD。部分 SymphonyQG 基线受 16-bit overflow 影响，不能把全部领先都归因于算法。 |
| **VIBE: Vector Index Benchmark for Embeddings**，首版 2025-05-23，实读 v3 2026-08-23；arXiv 注明 Journal of Data-centric Machine Learning Research (2026)。[版本页](https://arxiv.org/abs/2505.17810v3)；[全文](https://arxiv.org/html/2505.17810v3)；[作者框架](https://github.com/vector-index-bench/vibe) | 实读 §2.1、§4.1–4.4、§5.1/5.3/5.4、§6.1–6.2；PDF 页 4–10、13–19；另核对附录 D 的实现版本。当前是 22 实现、11 ID/8 OOD。文本与图文任务中，Glass/NGT-QG/SymphonyQG 等通用实现胜过已评 OOD 专用方法；attention MIPS 则相反。作者承认实现成熟度混杂，且不收 NDC。它反对“OOD 专用必胜”，不否定拓扑空间。 | 双 Xeon Gold 6230/AVX-512，384GB；单物理核，SMT off/NUMA 绑定，k=100，每配置五次取最快时间，公共超参网格。OOD 测试 1K 与训练分离，预分发训练 GT；Yandex 999K 为 **cosine**，LAION 约 1M 为归一化向量。不能外推到本地 10M raw-IP、16 核 QPS，最优五次也不能与均值五次直接相比。 |
| **Results of the Big ANN: NeurIPS’23 competition**，NeurIPS 2025 Datasets and Benchmarks；2025 发表，报告 2023 竞赛。[会议全文](https://papers.nips.cc/paper_files/paper/2025/file/63092d79154adebd7305dfd498cbff70-Paper-Datasets_and_Benchmarks_Track.pdf)；[冻结框架 v0.3.0](https://github.com/harsha-simhadri/big-ann-benchmarks/releases/tag/v0.3.0) | 实读 §2.2、§3、§4.2、§5（PDF 页 3–7、9）；其他赛道仅检查评估边界。OOD 上 RoarANN 与 PyANNS 并列获胜。前者结合 query-guided graph、量化和重排；后者为通用 Vamana+SQ8 搜索/SQ16 重排、VNNI 与 prefetch。证明工程改进是必要对照，冠军不能当作拓扑贡献的单独消融。 | Azure D8lds_v5，8 vCPU/16GB，批量查询可用全部线程，90% Recall@10 下比 QPS；建图上限 12h。T2I 10M/200D。**OOD 只有 public query**；private 只用于 filtered/sparse。不能称为 OOD 盲测或把竞赛 QPS 与本地直接相除。主文未给足 metric 转换细节，本次没有检查赛道执行源码。 |

第七篇直接近邻 **CDMG/CDMG+**（Efficient and Robust Out-Of-Distribution Vector Similarity Search with Cross-Distribution Monotonic Graph，2026）只作待补全文项。[作者仓库](https://github.com/Lsyhprum/CDMG)描述跨分布单调图，并列出 T2I/LAION/WIT/WebVid/CC3M 各 1M、测试 1K。仓库 README 指向的 `technical_report.pdf` 返回 404；[出版社全文](https://dl.acm.org/doi/pdf/10.1145/3786643)返回 403。因此本次没有实读其理论假设、CPU、metric 或 split，**不采用其 3.6× 摘要数字支持决策，也不宣称已完成对 CDMG 的新颖性排除**。访问记录见 [ood_cdmg_access_log_v1.json](/data/netg/ACSG/research_direction_review/20260908_v1/sources/ood_cdmg_access_log_v1.json)。

**建议保留、删除、改写的内容（研究推断，不是论文已证明本地有效）。**

| 动作 | 建议 | 理由与边界 |
|---|---|---|
| 保留 | Fast 固定图入口层作为成本清楚的基线；维持 raw-IP、fit/pilot/validation/held-out 隔离，完整离线成本和配对评估。 | 新论文没有否定轻量入口的工程价值；它们要求把入口贡献与邻域收集贡献分开。这里未重新检验本地 Fast 数字。 |
| 删除默认推进 | P3 未通过后继续大规模区域层次、路由预测器或门户数量搜索；把区域目标集中度提升视为 Recall 保证。 | 聚类/区域指标不是搜索可达性或实际执行开销；目前缺少桥接证据，增加模型复杂度不会补上因果链。 |
| 改写问题 | 从“如何把近邻归到少数区域”改为“在给定距离计算与内存预算下，哪些候选/边使联合搜索多找回目标”。 | 必须测共享候选池实际搜索，单入口探测结果的并集不等于联合执行。不能仅因到过某个 GT，就声称已到达其余 GT 所在的可搜索邻域。 |
| 改写下一道 gate | 先把失败分解为首次触及目标的代价、触及后继续收集的代价、终止/剪枝失去机会的代价。只在本地证据指向缺边时，提出一个固定边预算的稀疏修补小试验。 | 这是机制鉴别建议，不是立即运行授权。本轮文献复审不触碰项目图。现有区域实验本身不能区分缺边、预算不足与路由泛化问题。 |
| 保留反证路径 | 若做图修补，必须有同度数/同索引内存的普通边候选对照、固定入口与统一搜索代码；同时保留至少一个优化充分的普通图实现作端到端外部基线。 | 只与未优化的 HNSW 比，很难区分算法与 SIMD/量化/缓存收益。拓扑隔离实验与端到端实现竞争应分别报告，不能混成单一速度比。 |
| 新颖性重审 | “query GT 共现连边”“目标附近互相可达”“用 query hardness 修图”均已有明显前作。 | 若考虑图路线，必须提出不同的、可检验的稀疏样本泛化或成本问题；单纯做 NGFix/RoarGraph 的缩小版是复现或工程改进，不能预先称为新方法。CDMG 全文缺口仍待补。 |

如果后续决定做图修补 gate，建议固定原始 metric、20K fit、独立开发 query、入口与搜索实现，比较基础图、固定额外边预算的任务边、同预算普通边对照；同时记录实际新增边、NDC、Recall、搜索 wall time、完整离线成本，并以两个工作负载预先共同约定的通过/失败条件决策。先把已有基线检索保持为一条稳定控制线，不把新论文报告的全量历史 query 设置偷偷引入本地。如果结构改变只能改善 fit 或单个工作负载，应该停止扩大方案。这个提议需要主审结合已有失败与计算预算定案；本文件没有启动它。

本次六篇论文支持“以搜索过程为中心重新定义目标”，不支持“所有 OOD 都应大改图”；也没有一篇以与本项目完全一致的两套 raw-IP 数据、20K fit、10K×3 held-out 和固定资源协议，证实当前候选新方向必然有效。

下载与阅读溯源见 [ood_source_inventory_v1.json](/data/netg/ACSG/research_direction_review/20260908_v1/sources/ood_source_inventory_v1.json) 和 [ood_html_extraction_manifest_v1.json](/data/netg/ACSG/research_direction_review/20260908_v1/sources/ood_html_extraction_manifest_v1.json)。最初六个 PDF 下载均成功，但系统没有 `pdftotext`，原下载清单把随后的解析失败合并记为 `DOWNLOAD_FAILED`；补充清单明确区分下载与解析。三篇 arXiv HTML 用标准库转为文本，另外三篇通过网页工具的 PDF 文本提取阅读。未安装软件包、未复现实验；未逐行核验作者实现与全部附录证明。
