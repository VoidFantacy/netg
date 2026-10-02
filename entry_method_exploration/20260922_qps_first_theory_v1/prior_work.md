# 前作、成本假设与本项目排重

阅读日期：2026-09-22。只引用一手论文/作者材料；以下是用于设计审查的短摘记，不是完整文献综述。一般目标、决策论恒等式和更换模型名称不构成创新。

## 1. 三篇指定论文

| 工作与核对位置 | 目标及成本 | 保证的条件与边界 | 可迁移到本系统的部分 |
|---|---|---|---|
| [FrugalML, NeurIPS 2020](https://proceedings.neurips.cc/paper/2020/file/789ba2ae4d335e8a2ad283a3f7effced-Paper.pdf)，Sec.2-3、Lemma 1-2、Theorem 3 | 给定平均 API 费用预算最大化正确率；先付基础 API，再按其输出类别/置信度决定加购。费用按调用单价相加 | 稀疏混合结论属于该策略空间，不是“两个 ANN 入口最优”。学习界依赖 IID、全部服务输出、条件正确率对阈值的 Lipschitz 条件和离散网格 | 可以借用先验/后验条件决策和共同已付成本记账；不能把美元换成微秒，或忽略本地特征、评分、cache 成本 |
| [RouteLLM, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/5503a7c69d48a2f86fc00b3dc09de686-Paper-Conference.pdf)，Sec.3、5.4-5.5、Table 7 | 学强/弱模型的偏好胜率，以阈值调质量与强模型调用比例，主要费用来自大模型 | 有跨模型/域实验，但没有本地 ANN 完整 wall 保证。论文确实测了路由开销：SW 2.9 req/s CPU，MF 155.16 req/s GPU；还核算 embedding 和 VM 费用 | 选择前预测而非先运行所有动作值得借鉴；胜率不是收益幅度。其 GPU/CPU 配置和生成费用尺度不能直接拿来证明我们的微秒路由负担小 |
| [Regression with Multi-Expert Deferral, ICML 2024](https://proceedings.mlr.press/v235/mao24d.html)；正文核对 [arXiv v1](https://arxiv.org/pdf/2403.19494) Sec.4、Theorem 5/7、Appendix C | 固定预测器加专家选择，允许实例/标签依赖专家损失和有界回归损失 | 固定预测器界要求基础分类 surrogate 的假设类一致性界；受限类有 minimizability gaps，不能直接删去。整体两阶段还要求 regular 类。是风险转换界，不等于有限样本已训练好或推理免费 | 合法动作的 Recall 损失及执行费用可组织为条件风险，但 full wall 的有界性/尾部、实际假设类、估计误差、模型费都须另证；不能仅换其 loss 就宣布 QPS 一致 |

版本说明：PMLR 官方页核验了会议身份；其 GitHub PDF 被浏览工具识别为 octet-stream，无法读取。上述多专家论文的公式/定理编号明确对应已阅读的 28 页 arXiv v1，不冒称核对了会议 PDF 的相同编号。

## 2. 更贴近“信息是否值得计算”的已有理论

| 工作 | 已经解决/提出的事情 | 本项目不可直接借用的结论 |
|---|---|---|
| [Selecting Computations: Theory and Applications, UAI 2012](https://aima.eecs.berkeley.edu/~russell/papers/uai12-meta.pdf)，Definitions 1-3、Theorem 5、myopic 段落 | 区分对象动作和为选择动作而执行的计算，比较信息价值与计算费；完美信息价值限制可合理支付的计算量 | 后续采样/独立臂条件不对应固定 ANN；单步信息价值不能排除多组互补。我们的单组 VOI 式是这一类基本决策论的应用 |
| [Boosting as a Metaphor for Algorithm Design, CP 2003](https://ai.stanford.edu/~eugnud/papers/boosting-CP.pdf)，Sec.2.1-2.2 | 明确区分平均时间和相对时间；分级获取特征，仅当预期选择收益超过新增特征费才继续；用不同训练部分学习运行时间和升级收益 | “付费信息门控”本身不是新意。求解器秒级计算不能证明 ANN 微秒级可行；逐级贪心也不保证一般全局最优 |
| [SATzilla2012 Solver Description](https://www.cs.ubc.ca/~hutter/papers/12-SATzilla-solver-description.pdf) | 成本敏感的成对选择；先预测特征是否过贵，必要时回退，后续误分类按性能损失加权 | 特征耗时预测、backup、cost-sensitive classifier 均已有先例；不采用其预求解器、90 秒阈值或改变本项目主搜索 |

本轮最有用的组合不是某一种新网络：元决策解释为什么要支付信息费，成本敏感选择解释为何要预测损失幅度，多专家一致性解释 surrogate 何时保留动作目标。完整平均时间、真实召回约束和固定 L 仍需由本系统自己的证据连接。

## 3. 与已做入口方法逐项排重

| 版本 | 已经做过的实质 | 结果与不能换名重启的部分 | 后继尚须证明的不同点 |
|---|---|---|---|
| [E25](../../experiment_history/14_selective_profile_gate.md) | GT1/GT10 专家；BaseGate 七特征/条件第二路由、Dual 十三特征；质量差加权分类，完整费用评测 | Web Dual 部分 Recall 正而 QPS 负，Y 无稳定质量收益。其“cost-sensitive”主要指质量错选代价，不等于训练时显式 wall 惩罚 | 新的便宜信息源及其超过特征/门控费的条件收益；只说 defer/两阶段不够 |
| [E36](../../experiment_history/25_query_swap_policy.md) | 同次 top8 的 56 三元组，query 投影与 MLP、局部 swap，奖励含 NDC | Y 有局部 Recall 增益但 QPS -8.30%，Web 两者下降；NDC 近似不替代 wall | 不新增投影/大动作评分，并证实新增信息和真实费用；不能再称一次路由加小模型为新结构 |
| [E104](../../experiment_history/98_query_representation_pilot.md)、[E105](../../experiment_history/99_wfree_frozen_replication.md) | 真实效用监督的表示/静态画像，重学习放离线、在线普通小图 | QMLP 未过门，WFree cal 正信号未在独立完整复测复现 | 离线摊销本身不新；必须解释哪种可共享响应及其迁移，而非重新蒸馏同一教师 |
| [E117](../../experiment_history/119_entry_set_pilot.md) | 原 top3 与三个 rank-single；六个画像/真实距离关系特征；深度 2 CostTree、完整 wall | 已含 Recall 与时间联合目标，四质量区间跨零且总体无完整加速；停止加深树/调权重 | 拟议原路由内部状态必须在这些最终分数关系之外有目标预算决策价值；目标重写不算充分区别 |
| [E118](../../experiment_history/121_comparison_direction_pilot.md) | 32 主搜索比较方向、64 ReLU、全 H ridge；GraphCost/GraphRecall | GraphCost 20 点命中同默认且全慢；oracle 和少量 CV MSE 改善未兑现 | 复用已有计算不等于新增 32 投影；不拿大量默认回退掩盖评分成本 |
| [E119](../../experiment_history/122_service_capability_pilot.md) | 全 H 响应能力、交互、MSE/Rank 及 GBDT/TabM，时间进入净效用 | 六臂 query-out 净效用均负；有拟合内正值，不唯一归因为模型不足 | 需要目标预算、可观测廉价信息和选择后泛化；新 MLP/双塔或修 Rank 不能解释全部结果 |
| [E120](../../experiment_history/124_target_budget_response.md)、[record125](../../experiment_history/125_knn_three_point_timing.md) | 目标预算标签、七策略 TargetKNN；三点三次完整 wall | 目标标签未胜固定/置换；12 点 Recall 正但 QPS 全负。预算迁移问题真实存在，改标签未解决全部问题 | 当前 Recall 曲线仅容许很小条件新增费；不能把总时间差当 kNN 单项，也不调 k 续跑 |

额外碰撞检查：E35 已分析实际路由访问候选，E113 已尝试主搜索比较对共享支持，E116 已尝试原路由 ID 到 H 外真实入口绑定。因此“观察 trace”“按 ID 查表”“比较方向”都不能单独申报创新。拟议结构仅改变原 top3 保留方式，不做 H 外绑定；是否有新的可验证机制仍未知。

## 4. 结论

两类优先结构都有成熟的一般前作。本文保留的研究缺口更窄：在不可改动主搜索的微秒成本约束下，原 GT10 路由已付出的计算结果是否足以提供目标预算、查询外可迁移的动作收益分区？目前没有支持这个问题的已对齐状态/响应/成本证据，因此没有通过新颖性及可行性审查的实施 GO。
