# 搜索保证与本项目的适用边界

2026-09-30原文核查。文献与本项目条件分开；以下不构成修改主搜索/停止条件的实验指令。

| 原作 | 核对位置与结论范围 | 对当前入口研究的含义 |
|---|---|---|
| [Distance Adaptive Beam Search, NeurIPS 2025](https://papers.nips.cc/paper_files/paper/2025/hash/904fe070f484231aa26dbdb37816cd40-Abstract-Conference.html)；[原文](https://arxiv.org/abs/2505.15636) | 定义1要求对任意数据库节点对存在严格接近目标的邻居；定理1依赖metric和该可导航性。其方法改变停止判据，给出2/γ近似保证；附录A.2构造标准有限beam在可导航图上任意差的反例。 | 本项目raw负IP不是metric，NSG名称不证明该图条件；现行固定L停止也不同。记录145不是新的失败定理，而是当前kernel的近入口/多入口非单调实现核验。不能把对方保证移植到未改的本算法。 |
| [Projection-Augmented Graph, arXiv:2603.06660](https://arxiv.org/abs/2603.06660)；[作者实现](https://github.com/KejingLu-810/PAG/) | §3.1定理3.1需分块均匀条件、残差正则性、L和d/L等渐近条件；§3.2–3.4用投影筛距离/边及反馈buffer；§4.1同时改变构图与搜索。正文的有限参数单点测试下界另引KS2，不能当无条件全搜索召回保证。 | 它是底图/搜索机制的改进，超出当前“底图、展开、停止固定”的入口对照。相关价值在完整构建与查询费用、分阶段误差控制；本次只作前作比较，未实现或宣称原始IP适配。 |

本地PDF及SHA见`adaptive_beam_download.json`、`additional_papers_download_v1.json`。采用独立目录的pypdf提取正文，版本与文本身份见`text_extraction_v1.json`；复杂图形提取有form调用上限提示，因此未依据丢失的图中文字做定量结论。上述条件直接读取正文公式和章节。

本项目的新增推导是对固定合力/有限总体的风险及实际实现契约作核验，尚未给出新的通用图搜索保证。实际Recall/QPS仍由冻结模型、完整查询链测量；方向、排序、路由或路径上界均不是替代指标。
