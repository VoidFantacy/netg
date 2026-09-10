# A+B 相关论文与作者实现

以下区分原论文的方法、检查到的作者发布代码和本项目的推论。访问日期为2026-09-09；代码均作静态阅读，没有导入、编译或运行。论文序号1–15与[报告](report.md)对应。下载不等于全文审读：下列范围准确标明支撑本次结论的章节和文件，不声称审计了全部训练、数据或实验复现流程。

## 1. GATE：入口表示学习的直接对照

Jiancheng Ruan, Tingyang Chen, Renchi Yang, Xiangyu Ke, Yunjun Gao. **Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities**. KDD 2025. [论文 v1](https://arxiv.org/pdf/2506.15986v1)；[出版 DOI](https://doi.org/10.1145/3711896.3736930)；[作者仓库固定版本](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)。

重点核对 §4.1–4.2、Algorithms 1–2、Definition 4、式(4)与在线部分。HBKM 选择真实 hubs；论文正样本定义为固定 hub v 下满足 `H(q,v)≤min_{q′∈Q}H(q′,v)+t_pos` 的 query。它定义的 H 是通向最近邻的最短路径 hop，实践通过 NSG 搜索计数取样；不能直接视为本地固定 L/GT10 的 Recall 标签。式(4)是 hub–query 对比目标，不是逐入口 Recall 回归。

作者代码检查范围：

- [训练入口](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py#L32-L62)：实际启用 `TripletMarginWithDistanceLoss(1−cosine)`，InfoNCE 被注释。
- [正负样本脚本](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/experiment/combine_ep_gt.py)：`get_hop_count` 将没找到 GT1 的行记为999；正样本按每个 query 的 hub 数组最小值取，不是论文 Definition 4 的固定hub、跨query阈值轴。
- [在线入口](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp)：原 query 在 cosine HNSW 中查 top3，embedding索引映射回 hubs；没有在线 query MLP。

这些是发布快照的具体行为，不据此推断论文所有实验使用了哪个未公开版本。当前脚本还存在参数检查与后续 argv 使用不一致等可见问题，未执行，因此它是方法比较证据，不是可直接复现全部结果的已验收包。

本项目应引用其 query-aware hub embedding 和低开销导航，而把直接有限-L Recall、区域到真实ID的可学习多对一映射、单入口及成本验收作为待验证差别。图/分布编码可作未来增强，但本轮无证据说明必须照搬。

## 2. Adaptive Entry Point Selection：几何候选和理论边界

Yutaro Oguri, Yusuke Matsui. **Theoretical and Empirical Analysis of Adaptive Entry Point Selection for Graph-based Approximate Nearest Neighbor Search**. 2024. [原论文](https://arxiv.org/abs/2402.04713)；[PDF](https://arxiv.org/pdf/2402.04713)。前序作者工作为 [General and Practical Tuning Method for Off-the-Shelf Graph-Based Index](https://arxiv.org/abs/2309.00472)，2023。

重点阅读2024论文 §3.3–4：k-means 得到中心，再选中心附近的真实 base 点，query 选择最近候选；b-monotonic 与 B-MSNET 定理约束了适用图/距离。它适合作为冻结图上的几何入口对照，不能推出任意 learned hub 分数或未归一化IP的搜索保证。

[作者前序系统仓库固定版本](https://github.com/mti-lab/UTokyo-sisap23-challenge-submission/tree/1b2a8c0521ee8e0017ae822467835e7aee6a6329)由本地A/B来源清单记录。本轮核对论文与本地作者实现审查记录，未重新逐文件审计该仓库。前序完整竞赛系统含 PCA/子采样等内容，不能把它们全计成“入口选择组件”，更不能未经适配直接替换当前 NSG 契约。

## 3. Learning to Route in Similarity Graphs：每步路由和可折叠表示

Dmitry Baranchuk, Dmitry Persiyanov, Anton Sinitsin, Artem Babenko. **Learning to Route in Similarity Graphs**. ICML 2019. [论文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)；[作者实现](https://github.com/dbaranchuk/learning-to-route/tree/53ddfded604a4ad4c11de4e2a9672d515a014378)。

核对方法章节及以下源码：

- [walker_trainer.py](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_trainer.py#L62-L123)：对集合正样本计算 `−log(sum_pos exp(score)/sum_all exp(score))`。
- 同文件 `compute_expert_supervision`（约388–459行）：按候选到GT的最小hop保留多个正动作，区分 routing 与 verification。
- [walker_agent.py](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_agent.py#L108-L158)：`NoProjAgent` 把矩阵搬到节点向量侧，并保留处理bias所需的query加项；`PrecomputedWalkerAgent` 预存节点表示。

对本项目的意义是：图搜索监督、正动作集合与离线折叠均有前例。不同之处是该工作学习图内每步路由，本轮保持图内原IP评分与搜索代码，只输出最初入口。不能拿作者 routing/verification 的操作数配置代替本地路由成本。

## 4. Multi-Prototype SVM：主方案预测结构的最近前例

Fabio Aiolli, Alessandro Sperduti. **Multiclass Classification with Multi-Prototype Support Vector Machines**. JMLR 6:817–850, 2005. [论文](https://www.jmlr.org/papers/volume6/aiolli05a/aiolli05a.pdf)。

重点核对 §2–4，尤其式(2)：`H_M(x)=C(argmax_r⟨M_r,x⟩)`。这是向量全局获胜后查类别的相同基本形式；固定类别的分数可写成其多个prototype线性分数的max。多原型的非凸优化通过选定正prototype等方式转化为一系列更容易的问题。

本轮未核验这篇2005论文独立的原始作者代码。预测式本身已足以排除“多向量映射一个label是全新函数类”的表述；但论文的给定类别监督，不等于学习原NSG的H维实测收益与动作重映射。报告的参数锚定、预算和泛化边界属于本项目设计。

## 5. GAMM：多超平面与容量调整

Nemanja Djuric, Zhuang Wang, Slobodan Vucetic. **Growing Adaptive Multi-hyperplane Machines**. ICML 2020. [出版页](https://proceedings.mlr.press/v119/djuric20a.html)；[论文](https://proceedings.mlr.press/v119/djuric20a/djuric20a.pdf)。

核对式(4) `g(i,x)=max_j w_{i,j}ᵀx`、式(6)/(7)的固定潜在分量上界以及增长动机。它从单/少量超平面出发增加容量，并处理无用分量；固定标签下的这种优化并非联合学习真实入口身份。

作者实现线索为 BudgetedSVM，来源见本地 [A来源清单](../20260909_a_r0_v1/source_manifest.json)。本轮没有重新下载运行或逐文件核验该实现，因此报告只以原论文支撑数学关系。把增长思路移植到本项目必须设置固定总slot预算；“哪里有regret就加向量”会改变本轮成本契约。

## 6. ProtoPool：prototype与类别分配可以联合学习

Dawid Rymarczyk, Łukasz Struski, Michał Górszczak, Koryna Lewandowska, Jacek Tabor, Bartosz Zieliński. **Interpretable Image Classification with Differentiable Prototypes Assignment**. ECCV 2022:351–368. [论文](https://www.ecva.net/papers/eccv_2022/papers_ECCV/papers/136720346.pdf)；[作者仓库](https://github.com/gmum/ProtoPool/tree/2bd42882282fd309b3b70faa62a73c3c88cddd56)。

核对 §3，PDF第4–8页：共享prototype池、每类多个slot、每slot对prototype的分布、Gumbel-Softmax、slot正交项以及相似度聚合。它允许多个类别共享prototype，分配方向和本报告“每个获胜slot返回一个真实入口”并不相同。

[model.py](https://github.com/gmum/ProtoPool/blob/2bd42882282fd309b3b70faa62a73c3c88cddd56/model.py#L143-L172) 的 `proto_presence[c,p,n]` 经 softmax/Gumbel，`_mix_l2_convolution` 用 einsum 聚合距离，再进行相似度与类别输出。源码支持“可学习共享分配”的判断；不能将它简化成一次全局 top1 prototype 检索。`main.py`已存档，仅作训练配置线索，未逐行审计其完整训练循环。

与本项目存在可引用的共同思想，尚未直接覆盖原NSG finite-L整行Recall、单入口和固定H路由向量的完整组合。现有组件可构成有意义组合，是否值得发表依赖问题分析、对照和实际结果。

## 7. ProtoNN：联合表示、原型和输出的另一种部署算子

Chirag Gupta et al. **ProtoNN: Compressed and Accurate kNN for Resource-scarce Devices**. ICML 2017. [论文](https://proceedings.mlr.press/v70/gupta17a/gupta17a.pdf)；[作者EdgeML固定版本](https://github.com/microsoft/EdgeML/tree/81025fce8ba28707eabe72e11bf3987a8d745608)。

阅读 §3–4、式(2)、Algorithm 1：预测形式为 `f(x)=Σ_j z_j exp(−γ²||Wx−b_j||²)`，同时训练投影、prototype及输出权重，并用稀疏约束控制规模。其理论分析中的特殊分布条件不是ANN入口泛化保证。

本轮重新核对 [protoNN.py](https://github.com/microsoft/EdgeML/blob/81025fce8ba28707eabe72e11bf3987a8d745608/pytorch/edgeml_pytorch/graph/protoNN.py) 的 `forward`：矩阵投影、全部prototype距离、Gaussian权重、Z加权求和。训练优化的原论文与本地v4审查可相互印证；没有执行作者trainer。

若输出H个入口效用，一般需要原型聚合和输出层计算，不能精确缩成报告主方案的一次top1 MIPS。因此暂不推荐作为第三候选；这不是否定小型ProtoNN在其他预算下的可行性。

## 8. SPOT：直接为决策质量划分区域

Adam N. Elmachtoub, Jason Cheuk Nam Liang, Ryan McNellis. **Decision Trees for Decision-Making under the Predict-then-Optimize Framework**. ICML 2020. [论文](https://proceedings.mlr.press/v119/elmachtoub20a/elmachtoub20a.pdf)；[作者SPOTree](https://github.com/rtm2130/SPOTree/tree/0b92946a2d14202a1ca251201ddbb07892951e78)。

核对 §2、§4、式(2)/(4)、Theorem 1。SPO损失按预测成本诱导的决策在真实成本下的遗憾计分；论文对预测成本产生多个最优决策时采用最坏决策定义。Theorem 1 的叶内平均成本结果使用唯一最优决策假设。

[leaf_model.py](https://github.com/rtm2130/SPOTree/blob/0b92946a2d14202a1ca251201ddbb07892951e78/Algorithms/leaf_model.py#L70-L104) 把叶内加权平均成本送进 `find_opt_decision`。对本地有限动作，直接选“总hit最高的入口”不需要解复杂组合问题，也不需要用噪声人为消除Recall ties。`SPO_tree_greedy.py`已保存，论文的递归划分与MILP两类方法作为算法背景，未运行任何solver。

主方案的固定slot入口更新与SPOT叶动作选择有相同可加决策原理；区别在区域由平面竞争而非树路径产生。该可加性结论本身简单，不应作为“新定理”包装。

## 9. TAO：备用方案交替优化的基础

Miguel Á. Carreira-Perpiñán, Pooya Tavallali. **Alternating Optimization of Decision Trees, with Application to Learning Sparse Oblique Trees**. NeurIPS 2018. [论文](https://faculty.ucmerced.edu/mcarreira-perpinan/papers/neurips18.pdf)；[作者发布页](https://faculty.ucmerced.edu/mcarreira-perpinan/research/TAO.html)。

重点阅读 §3，PDF第3–6页：对不互为后代的节点目标可分，固定子树后比较每个query进入两侧的实际预测；两侧同结果的样本为don't-care。斜切节点用logistic/SVM等代理求解，论文不提供一般全局最优或近似比保证。

本地保存的作者发行版为2026-07-22，位置见 [tao.py](../../entry_selection_research/20260908_v4/sources/policy_compilation/TAO_author_release/tao-python-current/tao.py)。重点核对294–345、395–449行的左右子树损失差、权重与回退；`strict_update`默认False。已核对 [leaf.py](../../entry_selection_research/20260908_v4/sources/policy_compilation/TAO_author_release/tao-python-current/models/leaf.py) 的常量叶接口。无每类只能有一个叶的限制。

本项目必须显式启用/实现与硬Recall相符的验收、全动作叶优化和后代支持约束；不能把通用classification发布包当成已写好的ACSG trainer。

## 10. COMNETS：逐样本真实代价与斜切树的紧邻前例

Jothi Prasanna Shanmuga Sundaram, Magzhan Gabidolla, Miguel Á. Carreira-Perpiñán, Alberto E. Cerpa. **COMNETS: COst-sensitive learning for throughput optimization in Multi-radio IoT NETworkS**. ETFA 2025. [作者最终稿](https://jothiprasanna7.github.io/homepage/pub/COMNETS-ETFA25.pdf)；[预印本记录](https://arxiv.org/abs/2502.03677)。

核对 §IV，PDF第3–4页，式(2) `Σ_n c_n·1[y_n≠T(x_n)]` 和式(3)的L1项。两种radio的吞吐差作为每个样本的错误代价，用TAO斜切树与加权logistic求解，必要时按原目标拒绝更新。它证明“真实机会成本驱动的小树”并非未被研究的概念。

本轮未找到并核验与该最终稿对应的独立完整作者代码，不能声称已经复现。其两动作吞吐差与本地H动作Recall整行矩阵不同；这种不同允许任务与系统贡献，但不自动形成新通用学习理论。

## 11. Latent Structural SVM：交替优化的可用原理与不可继承保证

Chun-Nam John Yu, Thorsten Joachims. **Learning Structural SVMs with Latent Variables**. ICML 2009. [论文](https://icml.cc/2009/papers/420.pdf)；[作者软件页](https://www.cs.cornell.edu/~cnyu/latentssvm/)。

核对式(2)、§4/Algorithm 1、式(6)/(7)：损失增广的全局max减去正确label下的latent max形成凸函数差，CCCP交替补全latent并解凸子问题。原正确label固定，并对损失的latent依赖作限定。

本项目的入口动作可重映射、好动作是大量ties集合，低秩因子还有非凸耦合，不能把作者CCCP保证直接贴到新方法。主方案采用易定义的软期望遗憾提案与硬Recall验收；若以后选择latent hinge，必须重新写出“当前映射没有任何全H最优动作”时的目标定义。作者软件仅核对入口，本轮未下载执行。

## 12. VQ-VAE：codebook形式与任务目标的区别

Aaron van den Oord, Oriol Vinyals, Koray Kavukcuoglu. **Neural Discrete Representation Learning**. NeurIPS 2017. [论文](https://arxiv.org/abs/1711.00937)。

核对 §3.1–3.2、式(1)–(3)：encoder最近code、straight-through梯度、重构/codebook/commitment三项。其code代表潜变量而非原图真实入口；重构query不等价于保留搜索效用。本项目可以借鉴硬选择与连续训练的工程手段，不能声称重构更准就能提高Recall。本轮未核验作者完整实现，不以源码为此项证据。

## 13. Switch Transformers：单专家路由不等于本地入口预算

William Fedus, Barret Zoph, Noam Shazeer. **Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity**. JMLR 23, 2022. [论文](https://www.jmlr.org/papers/volume23/21-0998/21-0998.pdf)。

核对 §2.2，式(3)的专家容量与式(4)–(6)负载均衡目标 `αNΣ_i f_iP_i`。top1控制每token激活的expert数；均衡项用于分布式专家计算和容量溢出。

本地选一个入口后都进入同一个NSG，当前没有“某入口接收太多query就容量溢出”的对应假设。因此不引入强制均匀入口频率；只将塌缩与支持量作为诊断。本轮未审计作者实现，不借用其吞吐结果估算ACSG成本。

## 14. Hydra：配置与选择的组合本身可以有贡献

Lin Xu, Holger H. Hoos, Kevin Leyton-Brown. **Hydra: Automatically Configuring Algorithms for Portfolio-Based Selection**. AAAI 24(1):210–216, 2010. [出版页](https://ojs.aaai.org/index.php/AAAI/article/view/7565)；[论文](https://ojs.aaai.org/index.php/AAAI/article/download/7565/7426)。

阅读PDF第2–3页的动机、改造性能指标与算法：候选solver只因超过现有portfolio而得到奖励，再更新selector。它具体展示如何把已有配置器和选择器结合以学习互补性，支持“有机组合可成立贡献”的评价口径。

与本地入口的关系是离线动作/区域互补，而非照搬SAT配置、presolver或在线特征计算。免费选择最优solver/入口仍是oracle，需支付真实selector成本。早期下载地址失败，后通过出版方正确PDF地址读取；本轮未核验作者完整代码。

## 15. VIPER：教师引导压缩，非本轮必要前置

Osbert Bastani, Yewen Pu, Armando Solar-Lezama. **Verifiable Reinforcement Learning via Policy Extraction**. NeurIPS 2018. [出版页](https://proceedings.neurips.cc/paper_files/paper/2018/hash/e6d8545daa42d5ced125a4bf747b3688-Abstract.html)；[作者仓库](https://github.com/obastani/viper/tree/54fc4ae803322a08cb87fbbe65171a15ef001c7c)。

本轮核对出版摘要及本地v4论文/作者代码审查，未重读完整证明或源码。它借助DNN策略及Q函数学习可验证树。对本项目的有限结论是：教师价值加权可以帮助压缩，但已有真实全动作效用时，并不必须先训重教师；教师表现也不是所有小树的上界。

## 16. 补充背景与未展开的分支

Ian J. Goodfellow et al. **Maxout Networks**. ICML 2013. [论文](https://proceedings.mlr.press/v28/goodfellow13.pdf)。核对§3–4、式(1)，`h_i(x)=max_j(xᵀW_ij+b_ij)`。原文的通用逼近讨论不意味着固定H、固定rank和给定样本量能实现任意效用策略；本报告不把max-linear称为新函数类。

本地v5还讨论了 LIRA、MUVERA、ME-BERT、多知识源prototype路由、routing-guided PQ 等邻近工作，见 [utility_representation](../../entry_selection_research/20260908_v5/reviews/utility_representation.md) 与 [joint_entry_design](../../entry_selection_research/20260908_v5/reviews/joint_entry_design.md)。这些分别改变索引分区/复制、多向量检索、知识源路由或图内距离近似。它们作为边界与组件前例保留；本轮没有逐篇重新完成源码审计，不将旧review的评价冒充本轮新核验结论，也不据广义关键词碰撞否决组合贡献。

## 来源与阅读完整性

- 本轮保存的PDF、文本和选择性作者源码位于 [sources](sources/)。逐文件原URL与SHA见 `download_manifest.json`、`download_addendum.json`、`source_inventory.json`。
- 初始 `download_manifest.json` 将“PDF已下载但pdftotext缺失”记为ERROR；其记录原样保留。后续使用已有pypdf完成文本提取，`source_inventory.json`记录最终实际文件与提取状态。没有因此安装比较依赖或修改ACSG环境。
- 重点公式与实现的核查不等于作者性能复现；无任何本文方法、论文模型或ANN代码被执行。
- 结论是“已找到充分近邻先例与一个可辨认的项目适配空间”，不是“检索穷尽全部文献”或“证明没有相同工作”。
