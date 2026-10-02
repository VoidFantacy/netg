# 动作耦合前作与本次缺口

2026-09-22核对一手来源。这里不声称多任务学习、图正则或输出核是新方法。

- [Evgeniou、Micchelli、Pontil，JMLR 2005](https://jmlr.org/papers/volume6/evgeniou05a/evgeniou05a.pdf)：关联任务的正则化与多任务核是直接前作。应用到入口就是把各入口效用视作输出任务，必须承认这个重合。
- [Efficient Output Kernel Learning，NeurIPS 2015](https://proceedings.neurips.cc/paper/2015/file/a5cdd4aa0048b187f7182f1b9ce7a6a7-Paper.pdf)：§2的输入核×输出核、固定输出核对应任务耦合及独立输出特例已读。本轮若固定入口几何关系，不是学习新的输出核算法，也不借用其联合凸优化贡献。
- [Laplacian-Regularized Graph Bandits，AISTATS 2020](https://proceedings.mlr.press/v108/yang20c.html)：本轮核对摘要的用户图平滑假设和条件regret分析。此处是离线完整响应，不满足相同在线bandit反馈设置，不能直接搬其界或收益倍数。
- [Algorithm selection based on graph kernels，ASE 2020](https://link.springer.com/article/10.1007/s10515-020-00270-x)：原文实现段使用软件验证实例图核和成对算法排序。对象是输入实例图，与本轮固定动作输出关系不同，但“图结构帮助算法选择”不新。

项目内已核E118方向ridge、E119能力嵌入/GBDT/TabM、E121离散query状态表。当前新证据只在动作侧：相邻真实hub的中心化响应更相似。提案应检验这种关联能否降低查询外多动作选择误差，同时仍可编译成静态评分向量；它不引入新的线上query信息，也不是重训更深网络的依据。

一般函数值平滑不自动支持欧氏系数图平滑。本轮拟用训练设计诱导的预测函数能量，明确协方差、正则偏差与采样方差的条件。闭式矩阵求解和风险分解属于标准线性代数/统计工具；若实际选择与完整成本不改善，则只保留结构观察，不包装为算法贡献。
