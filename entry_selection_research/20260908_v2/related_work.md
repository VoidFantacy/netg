# 相关工作比较：候选、匹配与组合

核查日期2026-09-08。优先复用此前保存的原论文，联网补查版本和作者源码；只读方法/实验及相关实现，没有复现论文性能。本表中的速度是作者报告，项目结果明确标为本地事实。PDF页码从1起算，给出节号的HTML链接指向固定版本。主要证据快照、固定commit及SHA在 `sources/author_entry/`、`sources/author_candidates/` 和两份[入口论文审计](reviews/entry_papers_and_author_code.md)、[候选论文审计](reviews/candidate_papers_and_author_code.md)。

## 直接前作与本地方法

| 工作/版本、原文位置 | 候选构造 | query匹配、监督与多入口语义 | 完整成本与本地适用性 |
| --- | --- | --- | --- |
| **Fast v1，本地当前源码**：[builder](../../benches/run/build_fast_entry_variants.py)，144–238行 | 独立QGT5K球面query聚类，从GT顺序取唯一真实base hub | GT1向量最近raw-hub basin的query均值画像；单Micro-HNSW top3，共享原图搜索 | CPU，辅助cosine/主搜索rawIP；依赖exactGT。当前旧模型30K，新paired基线20K。不是严格set cover，不是神经模型；没有直接训练组合效用 |
| **旧NETG本地匿名稿**：[PDF](<../../ACSG/NETG_XM_KDD2026_ (5).pdf>)，§3.2–3.4/Alg.2，pp.3–6；当前[labels源码](../../benches/bench_generate_labels.cpp)187–226行 | ACO与W-DPC选择拓扑hub | 每query遍历hub真实probe；top1成功后最小NDC标签；hub离线残差变换，query直接搜Micro-HNSW，top3原图 | 已覆盖真实搜索监督、非神经在线路由。稿中0ms不能当路由免费；文件名不能证明出版身份。历史配置与当前20K/rawIP不是同一实验 |
| **GATE，KDD2025，arXiv2506.15986v1**：[全文](https://arxiv.org/pdf/2506.15986v1)，§4 pp.5–7、§5 pp.7–9 | base HBKM，局部图/Graph2Vec | 搜索hop监督hub表征、小导航图选入口；作者release在线原query直接cosine top3，不调用query MLP | 论文标签复杂度Q×H×search；512hubs/CPU查询。论文与release的标签轴、loss、hop有差异。原release L2/部分CUDA准备；本地rawIP10K适配失败不等于作者所有GATE失败 |
| **Adaptive Entry Selection，2024v1**：[正文](https://arxiv.org/html/2402.04713v1)，§3.3、§4.2–4.3、§5.1–5.4 | base k-means，中心附近真实节点 | query几何最近入口；无真实效用标签 | 聚类/映射/路由索引成本要计。Euclidean B-MSNET/Voronoi条件下的hop界不保证本地rawIP有限beam。专用作者仓库未确认，不声称已审完整实现 |
| **PSP / Spherical Navigation，PVLDB2025，2503.06882v2**：[全文](https://arxiv.org/pdf/2503.06882v2)，§4.1–4.2 pp.6–7、§5 Exp-3 p.11 | base方向聚类，再按原范数分布选navigation节点 | cosine选簇，从簇内随机填初始化池；主图保留原空间IP | 原论文SN消融平均约+6.2%属作者设置；完整PSP还改图/早停。作者默认关闭SN，可选代码预读query-cluster，缺在线选簇timer。只迁移入口是受约束适配；WebVid近单位范数未必受益 |
| **Adaptive Query-Aware Hybrid Search，EDBT2026 Short，pp.530–536**：[官方全文](https://www.openproceedings.org/2026/conf/edbt/paper-253.pdf)，§2.3–3.3/Alg.1 pp.2–3，§4 pp.4–6 | 属性分组的历史query树保存答案，取历史答案作为HNSW入口 | 预测recall辅助树遍历，过滤two-hop搜索；真实recall在搜索后反馈更新历史状态 | 作者range代码读取当前GT作后续状态更新；预计算特征/过滤表在timer外，GT/CSV在内，ef循环还共用历史树。不是当前无在线GT、unfiltered rawIP、固定3入口的可直接复现对照；不能把事后反馈误写为当前query直接用GT选入口 |

与本地负分支必须直接对照：旧search-aware centroid将全池single oracle压成一个query均值；residual prototype/static utility继承single标签；static ranker已做top32、真实Recall/NDC成本目标和top3真实部署；probe/拓扑chooser已有在线graph信号却仍选不好替代入口；cost-first atlas也试过无在线probe的历史效用迁移。相应失败只约束这些实现，不能否定所有可预测性，但新方案不能仅换模型名重启。

## 可借鉴机制与不可混用的系统

| 工作/版本、原文位置 | 核心机制与作者实现 | 对本地入口问题的边界 |
| --- | --- | --- |
| **kRt/hRt，PVLDB18(6):1649–1662，2025**：[正式全文](https://www.vldb.org/pvldb/vol18/p1649-gottesbueren.pdf)，§3.1–3.2 pp.4–5/刊物1652–1653、§4 | 图分片，每片层次k-means多代表，HNSW/树搜代表后按min-distance/frequency排序片；无query标签。代码汇总独立shard搜索 | TTI有rawIP；LSH理论属hRt且不覆盖rawIP。多代表不是新概念。分片覆盖/复制/最慢主机模拟QPS不同于共享原图入口，不能推断少量入口联合最优 |
| **LIRA，WWW2025**：[作者全文](https://zheng-kai.com/paper/2025_www_zeng.pdf)，§3 pp.4–6、§4与附录pp.6–8/11–14 | query+到各中心距离输入；二元含kNN标签，多标签路由与数据复制；各片独立HNSW | 有IP代码但大规模脚本CUDA；先全query×partition计算再汇总，不能作为本地已验证端到端CPU路由。分片/复制和训练规模与20K固定NSG不同 |
| **LTR-IVF，SIGIR2024，2404.11731v1**：[全文](https://arxiv.org/pdf/2404.11731v1)，§3–4 pp.2–4 | 固定分区，线性代表Wq；实际训练top1目标所属分区的CE；提出top-k扩展 | MIPS直接相关，但主要测分片覆盖，假设片内精确检索；没有本地CPU完整QPS证明。简单query→候选监督已有前作 |
| **SOAR，NeurIPS2023，2404.00774v1**：[正文](https://arxiv.org/html/2404.00774v1)，§3.4–3.5 pp.5–7、§5.4 pp.9–10 | 冗余VQ分配以正交残差减少相关失误；ScaNN复制压缩项并去重。均匀球面query假设下推出特定残差损失 | MIPS/CPU有意义，ScaNN同机实验与十亿级异硬件成本比较分开。它改IVF赋值与存储；“互补”不是新概念，残差理论不能变成共享beam入口保证 |
| **RoarGraph，PVLDB17(11):2735–2749，2024**：[全文](https://www.vldb.org/pvldb/vol17/p2735-chen.pdf)，§3.2/§4 pp.2739–2742、§5.5–5.7 | query-base二部关系投影并补连通性；作者搜索从固定projection_ep起步 | query GT预处理作者报告占完整构建87–93%，最小query比例10% base。是改图系统，不是可直接替换的query-aware入口selector，也非20K证据 |
| **MAG，SIGIR2025，2504.14861v2**：[全文](https://arxiv.org/pdf/2504.14861v2)，§4.1–4.2 pp.5–6、§5 pp.7–9 | 混合L2/IP图，先L2再IP；公开路径固定L_NN=5、visited重置和高范数补种子 | 改图、metric阶段和搜索状态；不当作同图三入口选择，不能漏计前段搜索。norm/angle分工已有直接前作 |
| **PilotANN FES，2503.21206v1，2025-03-27**：[正文](https://arxiv.org/html/2503.21206v1)，§5、§6.1/6.3 | 几何粗分桶和批量入口距离，r32对应warp；作者entry.py要求CUDA | 无搜索utility标签；速度依GPU计算密度。完整系统还含GPU子图/向量压缩/CPU精炼，不外推CPU/rawIP/20K入口收益 |
| **PathWeaver，ATC2025 / 2507.17094v1**：[正式页](https://www.usenix.org/conference/atc25/presentation/kim)、[正文](https://arxiv.org/html/2507.17094v1)，§3.2、§5.6.2/6.1 | 随机base子样本建ghost图，先搜ghost得top1，再进入主图；作者路径调用CAGRA | “主图外加小导航层”已有直接例子。GPU/L2/多GPU完整系统效果不同于本地CPU共享beam三入口，不能借系统QPS宣称新入口机制有效 |
| **NeuRoute，2608.15438v1，2026-08-15预印本**：[全文](https://arxiv.org/pdf/2608.15438v1)，§3–6 pp.5–22；复用此前全文核查 | MLP/hash-bucket与latent clustering，新query按logit/centroid gate和heap更新停止；作者单A100训练 | L2、2M训练子集、重建索引；在线状态控制已有新作，但不是本轮入口组合前作复现。不是所有数据都胜普通实现；不据此恢复旧confidence/区域计划 |

## 可复核的作者实现入口

| 仓库固定身份 | 本轮具体审查位置 | 重要核验 |
| --- | --- | --- |
| [GATE v0.0.1 / 229f18d](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba) | `tests/test_gate_search.cpp`、`cluster/experiment/combine_ep_gt.py`、`cluster/model/train/{model.py,__main__.py}`、`src/index_nsg.cpp` | 无在线query MLP；论文固定hub的query最小hop阈值 vs release固定query的hub最小hop；triplet启用/InfoNCE注释；首次发现hop不同于最短路/NDC |
| [PSP d3eb2e0](https://github.com/ZJU-DAILY/PSP/tree/d3eb2e09059828a883ce96c9f6a9b98a39e824ed) | `test/test_mips_search.cpp:89–105`、`src/index_mips.cpp:616–640` | SN默认关闭；可选query-cluster预读；初始化L点，不同于Fast3 |
| [MAG cbabb2b](https://github.com/ZJU-DAILY/MAG/tree/cbabb2b7d06d0a2e7f171219686aa49b72edf4ea) | `include/index_mag.h:613–737` | 全base范数列表、L2池搜索后清visited再IP；不是固定步数免费入口 |
| [gp-ann df5efb4](https://github.com/larsgottesbueren/gp-ann/tree/df5efb4a6b303011c795666ed267f29d994b558c) | `src/hnsw_router.h`、`src/route_search_combination.cpp` | min_dist/frequency排序shard，分别搜索后合并 |
| [LIRA 7beeee5](https://github.com/SimoneZeng/LIRA-ANN-search/blob/7beeee52d5b9a880f443876e24563713146ef581/LIRA_largescale.py) | `LIRA_largescale.py:51,122–163,210,257` | IP可用、CUDA、预计算query×partition与路由汇总 |
| [RoarGraph 7c9ef95](https://github.com/matchyc/RoarGraph/blob/7c9ef95dcb9b1022a2e3b8dfee55409ad73c605e/src/index_bipartite.cpp) | `CalculateProjectionep`、`SearchRoarGraph` | base均值最近L2节点为固定projection entry |
| [PilotANN 0aee5f6](https://github.com/ytgui/PilotANN/blob/0aee5f6c5d34158587d95e2aa5309c9a9529943a/pilot_ann/layers/entry.py) | `router_init`、`routing_cuda` | FES走CUDA，几何入口，没有搜索utility监督 |
| [PathWeaver c0804a5](https://github.com/AIS-SNU/PathWeaver/blob/c0804a5f46fd603794f4ce6205956a35ca46890e/pathweaver/single_pathweaver_one.py) | L107–117、L138、L214–216 | 随机子样本、CAGRA、ghost_topk1、两阶段检索 |
| [ScaNN 807d4a2](https://github.com/google-research/google-research/blob/807d4a2f41202059bac2446259d135a89ed3630a/scann/scann/scann_ops/py/scann_builder.py) | `tree`里的`soar_lambda`、`database_spilling` | 明确只许dot_product并设置TWO_CENTER_ORTHOGONALITY_AMPLIFIED；本轮仅审builder，不冒充核对全部SOAR C++核心 |
| [QueryAwareIndexing e6dfc9a](https://github.com/AdeelAslamSoton/QueryAwareIndexing/tree/e6dfc9a34698e036f11b9baf2a73b6ba0f4c9909) | `example_query_aware_range.cpp`、`query_aware_range_filter_hnswlib.h`、point示例/header、`bst.h`等8文件 | range搜索后GT反馈、预计算/计时与状态复用边界；point默认预测关闭，不能等同论文全部曲线 |

ScaNN此处锁定的是相关文件最近提交，不声称它是2023论文artifact；源码与SHA保存在[snapshot manifest](sources/scann_author_source.json)。旧NETG/SOAR本地PDF身份及按页提取记录见[local_paper_extraction.json](sources/local_paper_extraction.json)，只用已存在的解析器wheel读取，未安装或修改环境。

EDBT2026补充完整读了7页及8个作者源码文件，具体GT反馈时序、metric/过滤限制和默认代码差异见[2026补充审计](reviews/recent_2026_entry_addendum.md)。论文自己也报告一个数据集上原HNSW高层导航比原始BST更快；历史答案复用不保证入口检索成本足够低。该近作加强相关工作覆盖，不改变唯一先证伪推荐。

## 新颖性与覆盖限制

**当前能推荐一个研究问题，不能确认一种原创且有效的方法。** A需要超过几何/HBKM/QGT/norm-angle候选；B需要解释为何区别于GATE/旧ranker/atlas；C需要证明真实组合交互既存在、又可预测、且可加选择在同成本下不能获得同样结果。换成pairwise/listwise、加attention、多个随机seed或把hub改名为basin不满足这个要求。

此前14篇复审仍作为邻接背景：[路由分区](../../research_direction_review/20260908_v1/reviews/routing_partition_literature.md)、[搜索成本](../../research_direction_review/20260908_v1/reviews/search_cost_literature.md)、[OOD图](../../research_direction_review/20260908_v1/reviews/ood_graph_literature.md)。本轮复用不等于重新完整审阅它们每篇证明；特别是CDMG全文缺口没有消失。旧报告笼统的validation使用措辞以当前spec的逐版本口径为准。

OpenReview `rZyQVls8TD`检索摘要涉及batch/MST入口复用，但正文打开遇浏览器验证，未拿它支撑方法或新颖性结论。Adaptive Entry专用作者代码未确认；PilotANN/PathWeaver/SOAR只审相关组件；原论文与代码版本不一致的地方不推定隐藏实验设置。定向检索不是穷尽式系统综述，更不是论文接受或本地领先证明。
