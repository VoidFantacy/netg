# 定向阅读的论文、代码与适用范围

访问/复核日期2026-09-10。阅读论文所列方法章节，并对GATE/LRSG核对作者代码；未复现论文实验。下表的“本项目判断”是迁移分析，不是论文已证明的ACSG结果。原文/缓存身份在[sources/manifest.json](sources/manifest.json)和[sources/addendum.json](sources/addendum.json)。

| 论文与一手链接 | 已读范围 | 本轮采用的证据与限制 |
|---|---|---|
| Ruan等，**GATE / Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities**，KDD 2025，[正文](https://arxiv.org/html/2506.15986v1) | §4.2–4.3；hub表示训练、标签和在线作者代码 | 神经网络可离线生成入口向量，再建导航索引；标签围绕到GT1的hop，不能等同本项目固定L的GT10三入口联合收益 |
| Baranchuk等，**Learning to Route in Similarity Graphs**，ICML 2019，[论文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf) | §3.3–3.5及agent/trainer代码 | 学习节点表示、可预计算节点分支；改的是图内路由。query投影是否可折叠须按具体分支分析 |
| Hu等，**LoRA: Low-Rank Adaptation of Large Language Models**，ICLR 2022，[论文](https://arxiv.org/abs/2106.09685) | 摘要、§4.1、§7的rank研究范围 | 预训练语言模型低秩适配与权重合并；没有本任务rank8充分性的证据 |
| Hayou、Ghosh、Yu，**LoRA+: Efficient Low Rank Adaptation of Large Models**，ICML 2024，[正式页面](https://proceedings.mlr.press/v235/hayou24a.html)、[正文](https://arxiv.org/html/2402.12354v2) | 摘要、§3–4的大宽度论证及两因子更新 | 支持审查因子学习率；本项目有QR/裁剪/离散验收，不能直接套用论文比例 |
| Wang等，**LoRA-Pro: Are Low-Rank Adapters Properly Optimized?**，ICLR 2025，[正文](https://arxiv.org/html/2407.18242v3)、[正式PDF](https://openreview.net/pdf?id=gTwRMU3lJ5) | §2，尤其等效完整矩阵更新与梯度差异 | 因子求解器与全参数求解器不同；未证明替换后能改善入口选择 |
| Burges等，**Learning to Rank using Gradient Descent**，ICML 2005，[论文](https://www.microsoft.com/en-us/research/wp-content/uploads/2005/08/icml_ranking.pdf) | §3式1–3，成对概率与cross-entropy | 采用pairwise logistic思想。三入口条件收益、权重、Fast锚定及凸性推导是本报告自己的提案 |
| Xie等，**Differentiable Top-k with Optimal Transport**，NeurIPS 2020，[论文](https://papers.nips.cc/paper_files/paper/2020/file/ec24a54d62ce57ba93a531b460fa8d18-Paper.pdf) | §1–3，熵正则OT与top-k平滑/梯度 | 平滑选择不等于使NSG搜索质量可微；旧single效用也不会自动变联合效用 |
| Berthet等，**Learning with Differentiable Perturbed Optimizers**，NeurIPS 2020，[正文](https://arxiv.org/html/2002.08676v2) | §2，线性目标argmax、扰动、Fenchel–Young损失 | 需要辨认优化器的结构与目标，不能把启发式NSG当论文线性优化oracle直接套定理 |
| Kool、van Hoof、Welling，**Stochastic Beams and Where To Find Them: The Gumbel-Top-k Trick for Sampling Sequences Without Replacement**，ICML 2019，[论文](https://proceedings.mlr.press/v97/kool19a/kool19a.pdf) | §2–3，无放回采样与随机beam | 可借用无放回抽样；论文序列beam不是NSG beam，抽样本身不是奖励梯度 |
| Williams，**Simple statistical gradient-following algorithms for connectionist reinforcement learning**，Machine Learning 1992，[论文](https://link.springer.com/content/pdf/10.1007/BF00992696.pdf) | 一般更新、baseline及§4–5的期望梯度论述 | 给定q、baseline与当次动作独立时可构造无偏score-function估计；方差、样本代价和确定性部署落差仍存在。本地下载失败，web已读 |
| Teterwak、Saenko、Plummer、Lim，**OP-LoRA: The Blessing of Dimensionality with Overparameterized Low-Rank Adaptation**，CVPR 2026 **Workshop**，[正式PDF](https://openaccess.thecvf.com/content/CVPR2026W/ECV/papers/Teterwak_OP-LoRA_The_Blessing_of_Dimensionality_with_Overparameterized_Low-Rank_Adaptation_CVPRW_2026_paper.pdf) | 摘要、§3.1–3.2 | MLP以可学习常量为输入生成低秩因子，训练后丢弃；固定rank下改变优化，不是增加最终函数类。只作相邻任务补充证据 |

作者代码核对：

- [GATE commit 229f18d](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)：缓存[训练](sources/gate_train.py)、[标签](sources/gate_labels.py)、[在线](sources/gate_online.cpp)。在线raw query→HNSW top3。论文给出对比学习表述，发布训练实际使用cosine triplet；阈值选样轴也与论文公式表述存在差异。因此不把作者代码与论文所有细节混写为一个已复现方法。
- [LRSG commit 53ddfde](https://github.com/dbaranchuk/learning-to-route/tree/53ddfded604a4ad4c11de4e2a9672d515a014378)：缓存[agent](sources/lrsg_agent.py)、[trainer](sources/lrsg_trainer.py)。节点分支含图卷积/前馈层；query可为identity/linear；训练用Adam及one-cycle。NoProjAgent折叠线性query矩阵，但仍有query加性项，不能说任意分支在线完全无处理。

这些缓存从前一只读研究目录复制后重新阅读；本轮没有执行作者训练器或下载模型权重。上述论文在别的任务上的性能提升不转写为本项目的收益预测。
