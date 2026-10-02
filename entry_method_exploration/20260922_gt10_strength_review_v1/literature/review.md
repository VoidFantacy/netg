# 一手文献核对与研究空缺

检索日期：2026-09-22；服务于“GT10为什么强、还能在哪里改”的问题。以下区分读到的方法/定理正文与仅核对作者仓库的项目。论文报告的加速比不移植成本项目的 raw-IP、固定 NSG、CPU15 单线程设置；没有运行外部方法。

| 一手来源 | 本轮核对内容 | 对GT10的直接含义与不可直接移植处 |
|---|---|---|
| [GATE，KDD 2025](https://arxiv.org/html/2506.15986v1) | §4.1–4.3：base侧分层平衡聚类选真实hub，结构与查询监督的双塔，静态高层导航图 | “离线学入口表示、在线小图路由”已有直接前作。GT10区别应落在QGT选点、监督压缩和实际成本证据；双塔这个名称不是创新。GATE以路径步数构造正例，其L2叙述不等于本项目raw-IP、三入口联合beam保证。 |
| [Adaptive Entry，2024](https://arxiv.org/html/2402.04713v1) | 聚类入口、在线最近入口，B-MSNET与Theorem 4.4 | 更好的起点可以改善特定路径长度上界，但上界变小不证明实际路径、有限beam命中或总时间必然变好；图/Voronoi前提要单独核验。 |
| [Learning to Route for ANN Search，ICML 2019](https://proceedings.mlr.press/v97/baranchuk19a.html) | 论文摘要与方法定位：学习图上路由的表示 | 真实搜索反馈和学路由都非首次提出；该方法涉及遍历规则，与本项目只换初始入口的作用位置不同。 |
| [Learning to Route with a Ranking Objective，SIGIR 2024](https://arxiv.org/html/2404.11731v1) | 分区路由、GT所属分区监督、内部精确检索与排序目标 | 分区包含GT后能精确取回，因而有较直接的质量桥梁。入口“靠近GT”后仍需走有限beam，GT10缺的正是这一桥梁，不能直接借其一致性结论。 |
| [LIRA，2025](https://arxiv.org/html/2503.23409v1) | 查询感知分区概率、冗余分配与自适应探测 | 与GT目标分布压缩有关，但其分区搜索/合并和本项目多入口共享一个候选池不同；冗余覆盖优势不能推导本项目加入口必有益。 |
| [SOAR，NeurIPS 2023，2024 arXiv版](https://arxiv.org/html/2404.00774v1) | §3.1–3.3：量化残差、两次分配的误差相关性 | “最近的第二个选择”可能与第一个同错，提供研究动作互补性的动机；这里的对象是IVF分配，不是共享beam入口。不能把去相关公式直接套成已验证改进。 |
| [RoarGraph，VLDB 2024](https://arxiv.org/html/2408.08933v1) | OOD查询与GT分散性、query–base二部图及投影构图 | 支持“query分布信息有价值”的动机；实际改的是大图连接。它不能解释为现有GT10画像已获得同类结构保证，也不是当前固定图任务中的合法入口替换。 |
| [NGFix，2025预印本](https://arxiv.org/html/2510.22316v1) | §5.2 EH、Corollary 1、§5.3/5.4与Theorem 5 | 路径上最大query排名的minimax量、排名诱导子图可达性是直接前作。访问保证依指定算法与L；全Recall定理限历史query且不剪边。不能称本项目E111证书首次提出这类概念，也不能把充分条件当必要条件。 |
| [Maximum Inner Product is Query-Scaled Nearest Neighbor，VLDB 2025](https://arxiv.org/html/2503.06882v1) | §3：正数缩放query的排序不变性、缩放后NNS等价，SSG复杂度前提 | 为raw-IP理论提供参考；其复杂度分析使用同分布高斯/特定图条件，不适用于未经证明的跨模态NSG。缩放query与单位化base是不同操作，后者通常改变raw-IP目标。 |
| [Ada-ef，SIGMOD 2026](https://arxiv.org/html/2512.06636v1) | §5.2/5.3及§7.5：分数到ef的离线表，在线获取距离信息 | 小表和统计模型已有前作，表查找便宜不意味着获取特征免费。它逐query改变ef，当前固定L范围内不能据此宣称入口改进；两跳信息开销在论文消融中也有明确取舍。 |
| [Adaptive Query-Aware Hybrid Search，EDBT 2026](https://openproceedings.org/2026/conf/edbt/paper-253.pdf) | §2.3、§3.1、Algorithm 1：历史查询BST、估计recall、取历史结果作入口 | “查询记忆+便宜组织结构+入口复用”亦有直接先例。它针对属性过滤与高阶遍历，并更新recall模型，不等价于固定NSG的纯入口策略；不能把查表方案直接包装成新的通用范式。 |
| [Clustering on the Unit Hypersphere，JMLR 2005](https://jmlr.org/papers/volume6/banerjee05a/banerjee05a.pdf) | 球面聚类和vMF框架 | 归一化加权均值是成熟统计结构。GT10的闭式最优性不需要vMF假设；若进一步声称Bayes最优分类，则要新增并验证分布、浓度及先验条件。 |
| [ALORS，Artificial Intelligence 2017](https://www.sciencedirect.com/science/article/pii/S0004370216301436) | 出版社摘要：算法响应矩阵的潜在表示与新实例选择 | “服务能力/响应嵌入+query映射”属于已有算法选择框架。E119没有证明整个框架不可能，但新提案必须说明可迁移信息与这个前作的实质区别。 |
| [Hubness分析，SIGMOD 2026作者仓库](https://github.com/H40NaN/GraphANNS-Hubness) | 仅作者README：高入度hub、anti-hub、长尾与剪枝干预；ACM全文本轮403 | 作为结构研究的排重线索，不能声称已读完其理论。本项目“入口hub”只是候选点名称，并不证明它是统计hubness的高入度节点；目前没有此因果归因。 |
| [CDMG，SIGMOD 2026作者仓库](https://github.com/Lsyhprum/CDMG) | 作者README和作者主页核对；ACM全文本轮403 | 跨分布单调图已经有直接研究，若扩展到大图必须比较。仅凭仓库摘要不引用其具体定理或把作者加速比当本项目可达到的收益。 |

## 成本敏感决策的前作边界

项目今天的[记录126](../../20260922_qps_first_theory_v1/prior_work.md)已经逐项核对FrugalML、RouteLLM、多专家延迟决策、Selecting Computations、SATzilla与算法组合。本轮继承其“信息获取费、选择遗憾、完整wall必须一起核算”的问题分解，不将其重述为新的ANN算法，也不把LLM/API的成本尺度迁移到微秒级入口选择。

## 目前真正未闭合的问题

1. **归因缺口。** 现有系统收益里，QGT选择真实H、画像评分、画像诱导的小图状态分别贡献多少？E107/108/115已排除一些简单解释，但没有跨新查询来源和大图的完整因子分解。单位hub控制仍继承GT选出来的H。
2. **桥接缺口。** 代理排序的误差何时会改变真实入口响应，何时仅改变路径/工作量，何时完全不变？已有有限beam/局部最优理论只覆盖部分机制；NGFix式充分条件不是现成充分解释。
3. **可支付信息缺口。** 已有全H oracle很大，能被低成本、查询外信息识别的那部分未知。平均MSE、oracle和拟合内收益都不能填上这个缺口。
4. **跨预算缺口。** 候选排序依赖K与L；E120已测得预算迁移损失，目标预算kNN又未胜简单控制。不能继续假设“学好L128就自动提升R90工作点”。

这些是研究问题，不是新颖性已成立的结论。当前最可信的论文组织方向是“强简单入口基线及其适用边界 + 可审计的效用分解”；算法贡献需要额外的正面结果。没有根据给出会议等级保证。

## 检索边界

查询覆盖入口选择、学习路由、OOD图、搜索难度、hubness、分区路由、统计画像与低成本决策。上表每项只记录实际查看的层次；没有把搜索命中数量当系统综述的完整性证明。外部PDF访问失败不影响本项目原始数据的核算，也不以二手AI摘要替代缺失定理。
