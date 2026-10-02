# 已核对前作的条件与本地结论

2026-09-20。只记录支持当前理论判断的原论文，不把标题相似当成方法相同，不以未读证明支撑新颖性结论。

| 原作 | 本次核对内容 | 与ACSG的边界 |
|---|---|---|
| [Adaptive Entry Point Selection，2024](https://arxiv.org/html/2402.04713v1) | §3–4入口选择、B-MSNET与路径条件 | 其欧氏路径分析不直接保证当前raw-IP、有限池、多入口的Recall |
| [Distance Adaptive Beam Search，2025](https://arxiv.org/html/2505.15636v1) | 可导航图条件、自适应停止与标准beam的区别 | 证明依赖其图和停止条件；修改当前停止条件会成为不同搜索合同 |
| [A Learning-to-Rank Formulation of Clustering-Based ANN，2024](https://arxiv.org/html/2404.11731v1) | query到分区的路由目标 | 分区覆盖与共享候选池中的三个入口不是同一效用，不可直接转移一致性结论 |
| [LeanVec，2023/2024](https://arxiv.org/html/2312.16335v2)及[后续sphering研究](https://arxiv.org/html/2410.22347v1) | 双侧表示、query分布与索引几何 | 保分数双变换已有背景；本地E95已做对应构图后恢复P，不能同A加逆变换改名续跑 |
| [vMF方向分布，JMLR 2005](https://www.jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf) | §2–3的方向密度、均值估计、混合后验 | 可解释闭式方向估计；条件后验不等于有限beam搜索效用 |
| [Graph Based K-Nearest Neighbor Search Revisited，TODS 2025](https://doi.org/10.1145/3736716) | 出版社索引可读摘要、引言与§2；定位到LMG及两阶段搜索 | 全文打开仍失败，作者公开paper目录未找到该PDF；未完成§4证明核对，不判断本地证书首次性 |
| [Breaking the Single-Reference-Vector Barrier，WWW 2026](https://xiejiadong.github.io/files/paper/%5Bwww26%5Dmulti-vector.pdf) | 作者PDF摘要与问题定义：一条查询含多个参考向量，all/any检索 | 不是给同一个hub学习多个query画像，未把它当作ACSG多画像改进依据 |

本地已证实的是闭式目标、限定条件下的保留引理、保分数导航等价性、以及原kernel上的两个反例。尚未证明真实NSG满足能把GT10区域相关性转成高覆盖搜索收益的充分条件，也没有文献证据表明这些基础引理本身构成新的可发表理论贡献。

对CCF B投稿的影响：不能用“加入RL/MLP/双塔”代替新问题或新机制；也不能仅靠把已知方向统计和有限beam现象重新命名来声称创新。需要明确本地方法相对前作的实际差异，并用完整匹配性能、机制对照和独立数据证据支撑。具体会场尚未指定，本次不推断录用概率或会场要求。
