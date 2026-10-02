# 标签质量认证与已有提前终止方法的关系

2026-09-30，只读论文；本页不新增搜索或训练。关联[hard区间条件](../research/hard_mass_certificate_v1/theory.md)、[单区域球/半空间条件](../research/hard_mass_certificate_v1/cone_bound.md)和[soft质量配对](../research/soft_mass_transport_v1/theory.md)。

| 一手来源及已读范围 | 与本问题的直接重合 | 不能直接移用的结论 |
|---|---|---|
| [Ram与Gray 2012](https://arxiv.org/html/1202.6101)，§3.2.1定理3.1、§4–5 | 精确MIPS球界、单/双树分支定界；界松会抵消收益 | 旧数据加速不等于当前batch BLAS上的完整构建收益 |
| [Flores-Velazco与Mount 2020](https://arxiv.org/html/2002.06650v3)，§2及定理1/4 | 用较少样本保留近邻类别，依赖metric与margin条件 | 某个近似邻居的类别保持不等于raw-IP top10完整hub计数 |
| [Ranzato等 CCS2025](https://www.math.unipd.it/~ranzato/papers/ccs2025.pdf)，§4–5、7–8 | 以可行近邻次序及多数类确定性提前剪枝 | 多数类别、完整质量、目标ID是不同对象；组合代价不能忽略 |
| [Feng等 PVLDB2023](https://www.vldb.org/pvldb/vol16/p1346-feng.pdf)，§3–5 | 可能世界、确定/可能排名、top-k及窗口聚合；盒近似会丢相关性 | 本项目组计数的精确特殊式与其通用聚合的关系尚未全面形式化 |
| [Voráček与Hein ICML2022](https://proceedings.mlr.press/v162/voracek22a/voracek22a.pdf)，§2.2–2.3、附录A–D | 原型分类区域、点到分类超平面距离及可靠半径 | 当前raw-IP topK监督任务不同；几何边界式本身不能作为新意 |
| [Teofili与Lin ECIR2025](https://cs.uwaterloo.ca/~jimmylin/publications/Teofili_Lin_ECIR2025.pdf)，§3–5 | 按候选集合变化饱和提前结束HNSW | 历史稳定是启发式信号，不自动给出未访问点的全局排除证据 |
| [FARS公开稿，Label-Histogram Stabilization](https://lemma-public-asset.analemma.ai/online/fars/live/live_live_20260213/idea_29a2ce03-c573-41ec-a413-a7c46e3b5aa6/main.pdf)，§3–5 | 直接监控相邻checkpoint标签直方图L1变化，带warmup与patience；概念重合明确 | 页面标明自动研究系统生成，未确认同行评审，未本地复现；其标签指标是返回目标与query真标签相同的比例，不是GT10完整质量身份 |
| [Cohen与Fausti arXiv v2](https://arxiv.org/html/2309.02413v2)，§5.1定理5.1 | Hilbert距离到L1的锐界可直接给softmax权重扰动界 | 该定理不能消掉温度变化、query聚合、画像归一化及有限搜索的误差环节 |

Kudo等2003提前终止论文当前只取得出版社摘要和节选，仍保留“未阅读全文”的身份：[DOI](https://doi.org/10.1016/S0167-8655(02)00302-1)。不从摘要推断其全部定理范围。

## 当前可主张的层次

“标签比ID更早稳定”已是公开方法动机，不能作为本项目单独的新颖性主张。当前可研究的问题是：对画像真正消费的完整hard/soft质量，能否用可靠全局信息减少离线标注，而不是只观察过去若干步不变。盒条件与球/半空间特例首先属于正确性条件，尚无真实分组、浮点或费用证据。

只看历史直方图稳定不够的原因可以直接说明：两个数据实例可在停止前给出相同已访问目标、分数和类别；一个实例的未访问区域含有更高分的另一类目标，另一个没有。任何仅依赖这段共同历史的确定性规则都给出同一停止决定，却不能同时认证两者的真实topK质量相同。这个不辨识论证针对缺乏全局限制的信息模型，不证明上述启发式方法没有实际价值，也不是对特定HNSW实现的新反例测试。

后继首先检验单区域粗界的实际机会；若精确top10阈值都无法通过该界，换一个更好的近似教师也不能挽救同一界。更细的分块/标签索引属于另一个成本假设，不在当前版本自动增加。
