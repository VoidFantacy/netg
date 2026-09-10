# 一手文献阅读记录

检索/核对截至2026-09-10。共14项独立工作，定向方法调研，不是穷尽式系统综述。[主清单](sources/manifest.json)及[补充清单](sources/addendum.json)保存URL、访问时间、下载内容和SHA。方法章节阅读不代表复现其全部系统或逐页读完附录。

| 一手来源 | 本次阅读范围与直接事实 | 迁移到ACSG的边界 |
|---|---|---|
| [RoarGraph，PVLDB 2024](https://arxiv.org/html/2408.08933v1) | OOD现象、§4.2投影与后续连通增强：query的多个base近邻形成构图关系，包含剪枝和连接控制 | 原方法重建base图；不能把微型画像图改造称为已验证RoarGraph收益。源码局部定位不构成复现 |
| [OOD-DiskANN，2022预印本](https://arxiv.org/html/2211.12850v1) | §2 RobustVamana：借训练query的连接生成base间关系，再移除query节点；另有量化等系统组件 | 不是单独改变入口，也不是只提高度数；其全系统结果不能归到路由层 |
| [LeanVec，TMLR 2024](https://arxiv.org/html/2312.16335v2) | §2.2–2.3：不同query/base分布下双侧线性降维，近似内积并重排 | 在线变换开销需要本机重测；大索引中的成本占比不能搬到约800画像的小索引 |
| [GleanVec / LeanVec-Sphering，2024预印本](https://arxiv.org/html/2410.22347v1) | §3、§3.1，特别是全维式10的保内积关系；一般降维版本有近似误差 | 本报告受限对角成对变换为迁移提案。保内积不等于保证HNSW更快 |
| [LIRA，WWW 2025](https://arxiv.org/html/2503.23409v1) | §3–4分区、query近邻分布监督、冗余分配及数据集；实验含Yandex TI | 原系统是分区路由及分区内检索。不能据此保证替换本项目k-means获益 |
| [GATE，KDD 2025](https://arxiv.org/html/2506.15986v1) | §4.1–4.3：HBKM选hub，使用图/路径信息学习hub表示并建立导航图 | 与入口层架构重合明显；论文不支持把静态度数当作真实效用，也不支持首次性主张 |
| [Banerjee等，JMLR 2005，vMF](https://jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf) | 球面混合模型及EM、软归属、不同集中参数，与spherical k-means的关系 | 方向统计依据；没有跨模态ANN或本地800簇的性能证据。小样本簇须控制自由度 |
| [SOAR，NeurIPS 2023 / arXiv 2024](https://arxiv.org/html/2404.00774v1) | §3的量化残差相关错误、互补次级分配 | 说明冗余应具互补性；不是独立随机k-means多视角，也不是共享NSG beam的联合效用证明 |
| [LoRA，ICLR 2022](https://arxiv.org/html/2106.09685v2) | 低秩残差参数化和rank研究，沿用同日已核对缓存 | 应用领域与损失不同，不能推导本项目最优rank=8 |
| [AdaLoRA，ICLR 2023](https://arxiv.org/html/2303.10512v2) | §3基于重要性的奇异方向/预算分配 | 多矩阵LLM适配与单个hub画像矩阵不同，只支持rank需要选择这一原则 |
| [HNSW原论文](https://arxiv.org/pdf/1603.09320) | 建图/搜索和多样性邻居选择，PDF方法页 | 导航需平衡局部近邻与方向覆盖，不等于所有入口越高出度越好 |
| [Learning Space Partitions for Nearest Neighbor Search / Neural LSH，ICLR 2020](https://arxiv.org/html/1901.08544) | §2平衡kNN图分区、学习query到分区的映射及多探测；明确讨论query/data分布相近假设 | 不能直接把base kNN图分区当作OOD解决方案；离线层次分组也不等同于已失败P3在线保护beam |
| [Learning Partition Trees for Nearest Neighbor Search，2026-07预印本](https://arxiv.org/html/2607.09909v1) | 摘要与主要假设筛查：理论保证依赖分布/分区条件，未深入复核全部证明 | 只登记近期相关工作；未据此推荐具体算法或声称OOD保证 |
| [Quodar，ICCPR 2025会议论文集，2026出版](https://link.springer.com/chapter/10.1007/978-981-95-8318-8_1) | 仅浏览器中出版社摘要：面向OOD的query-aware hybrid partition | 全文未能取得。下载文件为Client Challenge，清单明确标记`CHALLENGE_BODY_NOT_PAPER`；没有把挑战页当论文、没有据标题补齐方法 |

论文中报告的QPS/加速数没有迁移成本项目预期。自有推导、代码事实、旧实测与论文已验证方法在[报告](report.md)中分别表述；没有安装新研究插件或启动作者系统。
