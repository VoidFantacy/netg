# 补标与画像理论的前作和适用范围

2026-09-30从作者论文/PMLR/arXiv原文核对；PDF及下载SHA单列保存。本页仅用下列前作支持统计方法的来源和条件，不引用其应用结果来保证本项目Recall。

| 原文 | 本项目借鉴 | 不能直接移植的结论 |
|---|---|---|
| Angelopoulos, Duchi, Zrnic, [PPI++](https://arxiv.org/pdf/2311.01453)，§6.1、Example 6.1 | 用控制变量系数减少估计方差 | 原独立有标签/无标签样本的均值最优系数含1+n/N；本项目已知有限池全部预测总和，须重新推导设计方差，不能照抄该系数。最优统计效率也不保证画像方向或Recall。 |
| Zrnic, Candès, [Active Statistical Inference](https://proceedings.mlr.press/v235/zrnic24a.html)，ICML 2024 | 使用预测误差信息分配标签，并通过逆概率修正保持统计目标 | 原Bernoulli概率采样是期望预算，不能冒充固定m无放回；本项目还要计入预测误差模型的pilot标签和费用。 |
| Li, Zrnic, Candès, [Robust Sampling for Active Statistical Inference](https://arxiv.org/html/2511.08991v1)，§2.1–2.2、Theorem 1 | 错误的不确定性会使主动抽样比均匀更差；可沿均匀与主动之间的路径研究稳健性 | “不劣两端”依赖最优插值参数的一致估计、是渐近方差结论；固定50%均匀混合只提供支持和粗方差上界，不继承论文不劣保证。 |
| Lee, Kim, [Statistical Optimality of Prediction-Powered Inference](https://arxiv.org/html/2606.08730v1)，有限总体SRSWOR设定、附录A | 区分固定预测器、有限池设计无偏与总体渐近推断 | 2026年预印本；本项目只采用可自行全枚举核验的有限总体恒等式，不据摘要宣布新估计器的高维最优性。 |
| Li, Ignatiadis, [Prediction-Powered Adaptive Shrinkage Estimation](https://arxiv.org/pdf/2502.14166)，ICML 2025，已读v3 §2、4–6 | 先作任务内方差缩减，再向预测均值收缩；CURE计入收缩源与目标的协方差 | 原设定为任务特定IID样本和独立无标签样本，跨任务先验及四阶矩支持任务数增长时的渐近最优；已知二阶矩理论不能直接覆盖小样本plug-in，§6另给UniPAS扩展。本项目共享query、固定有限池与归一化方向不满足直接移植前件，γ收缩本身不新颖。 |

本项目的实际问题是恢复固定H下的归一化向量画像。每条query同时对许多hub有向量贡献；真正关注的方向误差是经过hub相关投影与归一化的联合误差。把各hub视作相互独立标签、按hub分别收费或把十个目标当十个独立query，都会改变问题。

已有方法重叠：差值估计、Horvitz–Thompson/Hansen–Hurwitz、控制变量、Neyman式分配均属前作。方向投影的代数本身也不是可申报的新算法。研究价值需要由“现有ANN教师有什么廉价信息能预测哪类训练贡献误差，以及同成本下是否改善实际路由/搜索”建立。

下一阶段先检验信息，不直接用完整真值构造oracle采样概率。所有诊断真值、可用特征、pilot训练和接受池独立记录；测试概率预冻结，零误差样本也保留正抽样支持。默认不变。
