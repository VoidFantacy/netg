# GT10 锚定共享入口变换：方法依据与研究判断

本文解释 E28 的方法选择、与 GATE 等工作的关系和实验能回答的范围；本轮实测结论、图和全部负点见 [report.md](report.md)。论文原文与作者代码保存于 [sources](sources/inventory.json)，本轮未复现这些论文的整套实验，不移用其性能数字。

## 1. 研究对象与部署约束

目标是在离线阶段学出更适合选入口的向量，再用一份微型 HNSW 直接给出三个真实 hub，交给原 NSG。训练复杂度与查询复杂度在这里可以分开：训练时能使用真实搜索反馈；部署只保存每个 hub 一条定长向量，模型前向不进入查询路径。

[E27](../20260911_gt10_mechanism_v1/report.md) 已观察到：GT10 hard 的两个局部正点在 exact3 下仍有净命中提升。因此“微型 HNSW 没有找准原有画像的 top3”不足以解释全部收益。本轮主问题是改变画像评分所选择的入口；纯保分数几何变换仍是另一项研究，不能把两者混作同一种优化。

整个链条固定为：

```text
离线：GT10 hard 原型 P ──共享变换/自由残差──> 单位入口向量 W ──> microHNSW
                        ↑
              fit query 的真实三入口搜索教师

在线：原始 query ──一次 microHNSW top3──> 三个真实 hub ──原 NSG──> top10
```

本轮没有 query 端 MLP、在线组合重排、修改主图距离、重新选择 H 或更改 GT。图中训练教师不是上线所需的数据；验证查询的 GT 只在原始结果生成之后参与评分。

## 2. 文献所支持的部分与迁移边界

| 一手来源 | 可核实的方法内容 | 对本轮的启发与边界 |
|---|---|---|
| GATE，KDD 2025 [^1] | 选 hub，采局部子图、提取结构特征；通过到近邻的 hop 构造监督，融合节点与结构特征并学入口表示，再构建高层导航图 | 支持“离线学入口、在线查小图”的路线。它的 GT1/hop 标签与本轮固定 L、GT10、三个入口共同搜索的反馈不同 |
| GATE 作者固定提交代码 [^2] | 发布训练实际用 cosine triplet；hub 侧模型输出与 query 向量直接比较；在线源码 raw query→HNSW3→映射真实入口→NSG | 原始 query 配合离线 hub 变换在其公开实现中可行。论文两塔/对比学习描述与代码细节分别记录，不能声称本轮是 GATE 完整复现 |
| Learning to Route in Similarity Graphs，ICML 2019 [^3] | 学习节点/query 映射，用内积替代图内扩展评分；以到真实近邻的 hop 教师训练，采用访问状态上的模仿学习，并按原距离重排结果 | 说明“学搜索所需评分”有先例。它改变图内路由，本轮只改入口；不能直接借用其效果证明入口方法有效 |
| ListNet，ICML 2007 [^4] | 从 pairwise 转向 listwise，以 top-one 概率和交叉熵构建可训练排名目标 | 提醒训练目标应与最终选择一致。本轮不是复用 ListNet top-one：选择单位是无序三元组，归一化包含全部 H 的三元组 |
| k-DPP，ICML 2011 [^5] | 固定集合大小的概率分布，其归一化由 elementary symmetric polynomial 给出 | 本轮的加性集合概率是 diagonal k-DPP 的特例。所用 normalizer 不是新理论，也没有非对角 DPP 的多样性机制 |
| SlateQ，IJCAI 2019 [^6] | 通过单项选择、奖励/转移只依赖被选项等假设，将 slate 价值分解 | NSG 三入口共享搜索过程不满足这些现成前提。不能从该论文推导三个单入口收益相加就等于联合收益 |
| GleanVec / LeanVec-Sphering [^7] | 利用 query 分布构造线性投影，并研究分段线性降维；全维成对变换可保留原始内积 | 区分“保评分、改几何”与本轮“改入口评分”。本文只借用该区分，没有训练或评测 GleanVec |

GATE 论文 §4.3 的文字与公式存在表述不一致处：一处写成减小正例相似度，但公式及后文说明实际意图是拉近正例。本文以公式和作者训练代码共同核对，不沿用该文字错误。其文中关于 cosine 的 metric 表述也不能作为任意 cosine distance 满足三角不等式的证明；本轮并不依赖这个论断。[^1][^2]

## 3. 为什么同时比较线性、MLP 和自由入口向量

令固定原型为 \(P\in\mathbb{R}^{H\times d}\)，输出为：

\[
W_h=\operatorname{normalize}(P_h+f_\theta(P_h)).
\]

共享线性采用无偏置矩阵；小 MLP 采用 \(d\to64\to d\)，中间 ReLU、有隐藏偏置、无输出偏置。两者的残差输出都零初始化，使训练从 GT10 原型附近开始。自由参考为每个 hub 独立的残差 \(D_h\)，同样归一化；它使用完全相同的教师、损失、正则候选、训练轮数和优化器。

| 模型 | WebVid d512/H815 参数量 | Yandex d200/H821 参数量 | 查询时新增网络计算 |
|---|---:|---:|---:|
| 原 GT10 hard | 0 | 0 | 0 |
| 共享 linear | 262144 | 40000 | 0 |
| 小 MLP，宽64 | 65600 | 25664 | 0 |
| free 残差 | 417280 | 164200 | 0 |

参数量与最终画像存储量是不同概念：四种方法最终都存同样的 \(H\times d\) float32 表。只要导出静态 W，上线选择始终是 \(q^TW_h\)。两个入口之间的精确评分边界为 \(q^T(W_a-W_b)=0\)；MLP 没有使 query 空间的这条边界变成非线性。

因此，这里的 MLP 主要改变“如何从原型生成并共享入口向量”，提供一个参数共享和正则化假设。固定 H 时，任意导出的 MLP 向量表都能由 free 表表示；不能说 MLP 的最终函数族比自由 W 更大。如果 MLP 更好，需要用实测说明是共享规律或优化/正则带来的收益。如果 free 更好，也不能直接归因于结构无用，因为相同轮数不保证不同参数化达到相同优化程度。

线性 query 塔有时可折叠到离线 hub 表：若评分为 \((Bq)^TW_h\)，则等于 \(q^T(B^TW_h)\)。真正的非线性 query 塔一般不能这样精确折叠。本轮保持一次 microHNSW 的部署约束，不引入这个在线成本；“两塔”本身也不能充当创新性结论。

## 4. 为什么重新构造完整三元组教师

旧 [E23](../20260910_three_entry_rank_v1/report.md) 已经使用过真实三入口搜索标签，不能把它误写成只用了单入口伪标签。其训练将固定另外两个入口时的第三入口偏好压成 pairwise 约束；在有限抽样中，确实观察到同一 query 的某些入口相对偏好随另外两个入口改变。这个事实说明条件偏好可能冲突，但不足以证明所有静态评分方法都不可能成功。

本轮不继续将不同上下文的条件偏好分别压入一个排序，而为每个 query 直接给出一个完整目标三元组。候选来自实际部署的 GT1 hard HNSW3 与 GT10 hard HNSW3 并集，再用 GT10 原型精确分数补齐八个 hub。两条已部署基线的实际三入口因而一定包含在 56 个枚举三元组中。

每个三元组按真实 ID 升序注入原 NSG，在 L128 搜索，保存原始 top10 ID、hits/mask 和 graph NDC。教师按以下确定次序选择：最大 hits；在这些集合中最小 graph NDC；再取原型分数和最大者；最后真实 ID 字典序。前两项让教师优先关注有限 L 的检索质量，并在同等质量下偏好较低图工作。

这里有三个明确限制。第一，八个候选仍由原画像提出，教师无法发现候选以外的更好入口。第二，最优观察集合只针对一个 L，未必在其它 L 最优。第三，先 max hits 再 min NDC 是一个固定偏好次序，并非直接最小化同 Recall 的真实 wall。教师的 NDC 降低也不是 QPS 结论。

旧缓存复用要求相同 query、GT、H 映射、图、L 和入口顺序。两套原输入完整 hash 一致，缓存又与新原生 kernel 抽查对齐后才使用；新旧标签合并后由独立 Python 根据原始 ID 重新计算全部 224 万个三元组的 hits 和 mask。缓存节省的是重复调用，不创造新的独立样本。

## 5. 与直接 top3 相容的目标，以及它仍然不能解决的问题

使用归一化 query 只在训练中消除范数造成的温度差异。上线使用原始 query；对于相同 query，正比例缩放不会改变精确内积排序。设

\[
z_h=\hat q^TW_h/0.05,\qquad
P_\theta(S\mid q)=\frac{\exp(\sum_{h\in S}z_h)}{Z_3(q)},\quad |S|=3,
\]

\[
Z_3(q)=\sum_{1\le a<b<c\le H}\exp(z_a+z_b+z_c).
\]

训练损失为目标三元组的负对数似然，加上画像漂移惩罚：

\[
\mathcal L=\frac1N\sum_i\left[\log Z_3(q_i)-\sum_{h\in S_i^*}z_{ih}\right]
+\lambda\frac1H\sum_h\|W_h-P_h\|^2.
\]

最大概率集合就是三个最大分数的入口：若一个集合包含分数较低的 a，却遗漏分数更高的 b，将 a 换成 b 会增加分子而不改变分母。重复这一替换即得到 top3。该推导只保证模型自身的精确 MAP；HNSW 可能没有返回这个 MAP，更没有保证其 MAP 等于真实 NSG 最优入口。

令 \(e_k\) 为权重 \(\exp z\) 的第 k 阶 elementary symmetric polynomial，则 \(Z_3=e_3\)。本轮实现用 log-prefix 递推计算 e1/e2/e3，复杂度 \(O(3H)\)，避免枚举全部 \(\binom H3\) 个模型集合。小 H 穷举 normalizer、穷举梯度、有限差分、平移不变性、极端 logits 有限性和 top3 MAP 都已核验。该计算与 diagonal k-DPP 的归一化一致。[^5]

全 H 归一化约束候选以外的分数，避免只在 C8 内排序后任由未约束入口进入上线 top3。但是，候选以外并未逐一搜索过，把有限教师当作目标仍包含信息损失。目标是对教师集合的模仿，不是无偏估计全部 H 的搜索效用。

这个加性分布不建模任意互补性。它不具有非对角 DPP 的成对多样性项，更不能表示任意三元组协同。如果为了得到更一般的三元组分数而加入在线成对交互，通常就无法只靠一次独立 top3 完成精确选择。当前实验保持固定部署接口，检验这个受限但廉价的模型族是否已足够有用。

还必须区分“模型的 MAP 是 top3”与“损失每次下降都会改善 top3”。一个可直接计算的反例是五个入口、教师为 {0,1,2}：分数从 `[0.03,0.02,0.01,0,-0.01]` 变为 `[10,10,1,2,-10]` 时，教师概率从约0.103升至0.269，负对数似然从2.273降至1.313，但 top3 从正确的 {0,1,2} 变为 {0,1,3}。前两个教师项更确定，足以补偿第三项排错造成的概率损失。这个数学例子不构成搜索性能证据，却说明受限参数化、正则和有限优化下，必须另测真实选择；不能由代理损失下降推断入口已经更好。计算见 [反例数值](reviews/surrogate_counterexample.json)。

## 6. 控制变量与解释顺序

三族同用 fit20k、唯一教师、温度0.05、Adam lr0.003、80个完整梯度 epoch、λ10/100。仅 cal1024 的 L64/128 选择每族一个 λ；不选 epoch、不挑 seed、不展开宽度/秩/温度。原 hard/soft 对照按历史身份保留，原 Fast30K 保持其 query 数、seed100 和入口顺序，避免把输入或顺序差异当作神经模型收益。

训练损失、训练侧精确教师命中和真实检索成绩必须依次判断。损失下降只说明优化器推动了代理目标；教师匹配上升只说明模仿得更接近；同 L hits/NDC 改善只说明一个预算参数下的效果。最终选择仍看同机、同一批次的完整 Recall–QPS 前沿。

训练和正式计时分开运行。每个查询方法实际线程为1，固定 CPU15、OMP/BLAS/MKL均为1；每个点三次完整 warm+plain wall，轮换方法顺序。计时包含原始 query 路由、映射与排序、原 NSG 和结果写入预分配内存；GT、计数器、I/O、索引加载构建在外。逐位核验不同重复、plain/count、原 wrapper 结果。

报告保留所有五个 L 和全部方法，包括负点。精确 top3 只作为 audit 的画像/近似分解诊断。两个方法在相同 L 的 Recall 差采用逐 query 配对 bootstrap；wall 三次重复只表示本机重复波动范围，不能伪装成三倍 query 样本量。曲线之间的 log-QPS 插值单独标为插值，不能写成实测等 Recall 加速。

## 7. 怎样看待论文潜力

目前可研究的核心不是“在入口前放 MLP”，而是固定部署约束下的三个问题：什么样的联合搜索反馈能够压缩为可检索的静态入口表；GT10 多目标先验是否稳定改善这种压缩；共享结构是否减少样本需求并改善跨 query 泛化。GATE、图路由学习、listwise 和固定集合分布都已经覆盖若干组件，不能单靠组件拼接声称新方法。

要形成有说服力的研究贡献，至少需要稳定的端到端前沿收益、对负点的机制解释、教师与部署选择之间误差的可量化分析，以及独立数据/图/种子上的重复。当前重复使用的开发与 validation 切片只能支持本地探索结论。即便某条曲线领先，也不足以直接判断达到某一会议等级；如果原 GT10 更好，应保留这个结果，解释标签和模型瓶颈，而不是因为模型更复杂就优先推荐它。

本轮后续建议必须由实测结果约束：教师有空间但模型学不到时，优先研究压缩与监督；fit 好而开发/validation 差时，优先研究泛化或正则；exact 好而 HNSW 差时，再研究小图近似；质量改善但 wall 无收益时，检查图内工作与访存。这些是结果解释分支，不是自动授权的新实验队列。

若研究更贴近 top3 的训练目标，应先从完整教师集合与最强负例之间的 margin 开始，明确它优化的是教师成员选择，仍不等于真实 NSG 效用。更复杂的备选包括 SoftSort 的排序连续松弛，以及 SOFT top-k 用熵正则最优传输近似集合成员指示。前者以排序值到原分数的距离构造行softmax；后者通过Sinkhorn求解并对运输问题求导。它们提供可微选择工具，但温度/熵正则带来近似偏差，没有解决本项目的教师偏差和候选覆盖，也没有被本轮训练或评测；不因其名称包含top-k就预期收益。[^8][^9]

## 来源

[^1]: Ruan et al. [Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities](https://arxiv.org/html/2506.15986v1)，KDD 2025，§4.2–4.3。缓存 [PDF](sources/gate.pdf)。

[^2]: GATE 作者代码，[固定提交 229f18dadb791ddede22597e44d5ceb028b104ba](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)。训练入口 `cluster/model/train/__main__.py`、模型 `model.py`、导出 `infer.py`、在线 `tests/test_gate_search.cpp`；本地代码与来源核验见 sources。

[^3]: Baranchuk et al. [Learning to Route in Similarity Graphs](https://proceedings.mlr.press/v97/baranchuk19a.html)，ICML 2019，§3。缓存 [PDF](sources/learn_route.pdf)。

[^4]: Cao et al. [Learning to Rank: From Pairwise Approach to Listwise Approach](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2007-40.pdf)，ICML 2007，§4–5。缓存 [PDF](sources/listnet.pdf)。

[^5]: Kulesza and Taskar. [k-DPPs: Fixed-Size Determinantal Point Processes](https://www.alexkulesza.com/pubs/kdpps_icml11.pdf)，ICML 2011，§3。缓存 [PDF](sources/kdpp.pdf)。

[^6]: Ie et al. [SlateQ: A Tractable Decomposition for Reinforcement Learning with Recommendation Sets](https://www.ijcai.org/proceedings/2019/0360.pdf)，IJCAI 2019，§4.1。缓存 [PDF](sources/slateq.pdf)。

[^7]: Tepper et al. [GleanVec: Accelerating vector search with minimalist nonlinear dimensionality reduction](https://arxiv.org/abs/2410.22347)，固定 v1，§3.1 Eq.10 及 §4。缓存 [PDF](sources/gleanvec.pdf)。

[^8]: Prillo and Eisenschlos. [SoftSort: A Continuous Relaxation for the argsort Operator](https://proceedings.mlr.press/v119/prillo20a.html)，ICML 2020，§1及算子定义。缓存 [PDF](sources/softsort.pdf)。

[^9]: Xie et al. [Differentiable Top-k Operator with Optimal Transport](https://arxiv.org/abs/2002.06504)，2020，§2–3。缓存 [PDF](sources/soft_topk.pdf)。
