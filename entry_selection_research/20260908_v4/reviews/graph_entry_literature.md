# 新入口预测方向的一手文献与作者实现边界

日期：2026-09-08。本文件服务于 v4 的调研与设计：离线允许较重的真实搜索监督，在线从原始 query 轻量输出真实入口。本次只下载和静态读取论文、选定作者源码及项目既有文本证据；没有训练、ANN 搜索、重建索引、读取原始 base/query/GT/图或安装依赖。下载与抽取的 SHA-256 见 [download_manifest.json](../sources/graph_entry/download_manifest.json) 和 [extraction_manifest.json](../sources/graph_entry/extraction_manifest.json)。

**核心判断：GATE 与 LRSG 已覆盖“搜索相关监督 + 离线重表示 + 在线廉价点积”的大部分叙事。新方向不能以免除在线 query 神经网络、离线折叠线性映射、用搜索反馈学习入口为主要新颖性。真实效用决策树若值得验证，其区别应是：固定原图与搜索语义，将有预算的真实入口损失直接用于分支和叶动作选择，在隔离查询上减少选错入口造成的搜索损失，并以完整在线成本检验。文献目前支持机制对照，尚不支持它在 ACSG 上有效。**

## 1. 审查范围与版本

页码为 PDF 页码，从 1 开始。下载完整文件不代表全文逐段审计；下表明确实际阅读范围。

| 工作 | 一手来源与实际阅读范围 | 作者实现范围 |
|---|---|---|
| GATE，KDD 2025 | [2506.15986v1](https://arxiv.org/pdf/2506.15986v1)，方法 §4.1–4.4，pp.5–7；实验 §5，pp.7–9。复用并复核本任务 v2 的逐项审计。 | [release v0.0.1](https://zenodo.org/records/15523071)，commit `229f18dadb791ddede22597e44d5ceb028b104ba`；聚类、样本、模型、训练、在线测试与 NSG 搜索。源码副本与逐字一致性在 [v2 审计](../../20260908_v2/reviews/entry_papers_and_author_code.md)。 |
| LRSG，*Learning to Route in Similarity Graphs*，ICML 2019 | [PMLR 正文](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，§3.1–3.6，pp.3–5；§4，尤其 §4.2，p.6。 | [dbaranchuk/learning-to-route](https://github.com/dbaranchuk/learning-to-route/tree/53ddfded604a4ad4c11de4e2a9672d515a014378)，commit `53ddfded604a4ad4c11de4e2a9672d515a014378`；读取 `lib/walker_agent.py`、`lib/walker_trainer.py`、相关 HNSW/graph 定义及 SIFT1M notebook 代码单元。未执行 notebook。 |
| LAN，*LAN: Learning-based Approximate k-Nearest Neighbor Search in Graph Databases* | [作者 PDF](https://edisonchan-szu.github.io/publication/LAN.pdf)，重点 §V 初始节点选择，pp.7–8；核查问题单位与总体流程。 | [csypeng/LAN](https://github.com/csypeng/LAN/tree/71c50ca398a906a22199af230a40f8a4dcec43cb)，commit `71c50ca398a906a22199af230a40f8a4dcec43cb`；重点完整定位 `init_node_sel_model_train.py` 的标签、模型与损失。另存路由与交叉图代码，未据未完整审计部分下结论。 |
| NeuRoute，2026-08-15 预印本 | [2608.15438v1](https://arxiv.org/html/2608.15438v1)，§3.1–3.2 的对象、编码与损失，结合论文流程说明；仅用于对象辨析。 | [作者仓库](https://github.com/XingqiaoWang/NeuRoute/tree/8d94121cf022a6e96a2debc377e5f48154da86a0)，commit `8d94121cf022a6e96a2debc377e5f48154da86a0`；已读 README，未做完整源码审计，不作为可复现实验背书。 |
| Parabel，WWW 2018 | [作者论文](https://manikvarma.org/pubs/prabhu18b.pdf)和[作者代码页](https://manikvarma.org/code/Parabel/download.html)，本轮检索确认层次多标签对象与作者发布范围；未完整逐页审计。 | 作者提供 C++/Matlab 发布；没有下载、编译或运行其程序，也不把第三方 Python/Rust 重写称作作者实现。 |

另外保存了 RRP（arXiv:2201.09290v1）和 DRR 作者补充材料供后续定位；本笔记没有完成其方法与代码配对审查，因此不依据这些下载文件主张新颖性或效果。

## 2. GATE：最直接的入口学习前作

论文先从 base 聚类产生真实 hubs，用局部图特征表征 hub，再采样 query×hub 图搜索路径信息学习 hub 向量；在线以小型导航索引选择真实入口。这里的监督是搜索 hop，不能等同当前有限 beam 下的 Recall@10、NDC 或 wall time。论文标签准备成本含 `|Q|×|H|` 次搜索，不是只计算一次 GT。[论文 §4](https://arxiv.org/pdf/2506.15986v1)

作者 release 提供四个直接影响新方案定位的事实：

1. **在线直接用原 query。** `tests/test_gate_search.cpp:56–68` 读取 hub embedding 并构建 cosine HNSW；`:99–108` 用原 query 检索 top-3，然后映射真实 base ID。训练网络作用于 hub 特征，不能给这条在线路径加上不存在的 query MLP。[测试源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp#L56)
2. **release 损失为 cosine triplet。** `cluster/model/train/__main__.py:35–39` 的 InfoNCE 被注释，启用 `TripletMarginWithDistanceLoss`；`:57–59` 将 hub 表达与原 query 正负样本送入损失。这与只按示意图描述“两塔在线推理”不同。[训练源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py#L35)
3. **论文和 release 的正样本比较轴不同。** Definition 4 以固定 hub 跨 query 的最小 hop 为阈值基准；`combine_ep_gt.py` 转为 query×hub 后按每 query 的最小值筛正 hubs，未命中 GT 标为 999。应分别引用版本，不能推断未公开论文运行究竟采用哪一份实现。[标签源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/experiment/combine_ep_gt.py)
4. **实现中的 hop 是发现路径长度。** `src/index_nsg.cpp:645–712` 初始化后给首次发现节点记父 hop+1，visited 后无最短路松弛；它不是距离计算次数，也不是严格图最短路径真值。[搜索源码](https://github.com/jacksondca/gate/blob/229f18dadb791ddede22597e44d5ceb028b104ba/src/index_nsg.cpp#L645)

对 v4 的推断：以真实有限搜索结果为损失，确实比 hop 阈值更贴近当前目标，但“改用真实搜索反馈”单独不足以证明强新颖性。应明确损失对象、输入信息、动作集合、训练归约和在线结构。若仍是 raw query 对所有 learned hub vectors 点积，容易落回 GATE 的核心形式。

## 3. LRSG：廉价在线评分和线性映射离线折叠已有实现

论文学习查询与图节点的相容分数，离线用图网络生成节点表达，在线在图搜索的每一步使用学习分数，最终再用原始距离验证候选。训练采取模仿学习，expert 根据到真实最近邻的最短 hop 指导动作，并聚合当前策略遇到的状态。论文主要目标和评测围绕给定距离计算预算的最近邻查找；它是改变沿途路由分数的工作，不是冻结原距离搜索后只预测起点。[论文 §3–4](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)

作者代码核查：

- `walker_agent.py:26–55` 的 query 映射是可选线性层；不投影时允许直接使用原 query。节点端存在多层/图卷积计算，不代表这些计算必须留在线上。[agent 源码](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_agent.py#L26)
- `NoProjAgent:108–132` 明确包装已有模型，将 query 变换吸收到预计算节点向量中；实现使用线性权重、逆与 bias 处理，有其维度及可逆条件。`PrecomputedWalkerAgent:135–158` 缓存节点表达。因此“将线性 query encoder 折到候选端”不是本项目独有的新机制；也不能把任意非线性网络说成可无损折叠。[离线折叠与预计算](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_agent.py#L108)
- `walker_trainer.py:388–459` 生成 expert 集合时保留多条 hop 最优动作；`:62–123` 使用正集合与全候选的 logsumexp 差，鼓励任一正确动作。因此“多个好动作不应被任意单一标签互相排斥”也有明确前作，不宜作为全新训练原则。[expert](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_trainer.py#L388)、[集合损失](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_trainer.py#L62)
- `walker_trainer.py:145–229` 先获取固定/既有策略提供的初始 ID，再以学习表达模拟搜索，最后做原距离验证。所读 SIFT1M notebook 使用单最近邻目标及 routing 248 / verification 8 配置，不能直接迁移为当前 Recall@10、三入口共享 beam 的收益证据。[训练与验证流程](https://github.com/dbaranchuk/learning-to-route/blob/53ddfded604a4ad4c11de4e2a9672d515a014378/lib/walker_trainer.py#L145)

对 v4 的推断：LRSG 最强碰撞在“离线吸收复杂性、在线轻量评分、搜索相关监督、容许多种正确动作”。当前候选可以把动作严格限制为入口，并保持后续图距离与搜索语义不变，从而隔离入口价值；但这是研究合同上的清晰区分，尚不自动形成足够论文贡献。若采用代价斜切树，需把它与这些表示学习路径及普通成本敏感分类分开比较。

## 4. LAN 和 NeuRoute：名字接近，学习对象不同

### LAN

LAN 数据库中的一个对象是一张图，距离是 GED。其初始节点选择模型学习 query 图附近的数据库图，后续还包含昂贵 GED 计算与图间学习；这不是当前向量空间内“从某真实入口跑固定 NSG 后能否低成本获得 GT10”。论文 §V 的正例与近邻关系有关，而非本项目的搜索效用。[作者论文 §V](https://edisonchan-szu.github.io/publication/LAN.pdf)

源码 `init_node_sel_model_train.py:169–210` 将 GED 真值排序前 200 及并列项设为正例，负例约采样训练对象的 10%；`:232–279` 对 query 做 GIN 编码，与数据库图 embedding 拼接后逐候选 MLP+sigmoid；`:305–315` 使用正类权重 10 的 BCE。这里的全候选评分和 query 图网络成本不能从“预测初始节点”这一名称中省略。[作者模型与标签](https://github.com/csypeng/LAN/blob/71c50ca398a906a22199af230a40f8a4dcec43cb/init_node_sel_model_train.py#L169)

因此 LAN 可作学习入口邻近性的背景对照，但不能证明真实 NSG 入口效用已被该标签解决，也不宜作为本项目在线轻量设计的直接模板。

### NeuRoute

NeuRoute 是完整 learned hashing 索引：神经编码产生二进制桶地址，桶内再聚类，查询由 logit 的阈值偏离度指导多桶探测，筛选中心后精确重排。§3.2 的监督保存 mini-batch 原始距离的局部相似关系，未使用固定 NSG 的 query×entry 搜索结果。它更换索引组织且在线有 query encoder，与本轮固定图、轻量输出入口的对象不同。[原文方法](https://arxiv.org/html/2608.15438v1#S3)、[作者 README](https://github.com/XingqiaoWang/NeuRoute/blob/8d94121cf022a6e96a2debc377e5f48154da86a0/README.md)

截至本轮读取的是 2026-08-15 预印本和仓库 README，未独立复现其吞吐量、构建时间或作者完整代码；这些数字不纳入 ACSG 方法推荐证据。

## 5. 层次标签与树路由的最低相关工作边界

Parabel 将大量标签组织为平衡层次，再用轻量分类器预测相关标签；作者明确其目标是 extreme multi-label classification，并提供 C++ 发布。它已经说明“把大动作集合做成树以降低预测成本”不是新研究命题。这里只完成一手来源定位与框架确认，未完整审计其叶节点、beam 和全部代码，不据此给出逐项性能对照。[作者论文](https://manikvarma.org/pubs/prabhu18b.pdf)、[发布页](https://manikvarma.org/code/Parabel/download.html)

本轮主报告另查的 Filter Tree/TAO 需要承担具体归约与优化机制的引用。本笔记未独立核对那些论文，不能替代相应原文证据。对于拟采用的“真实效用斜切决策树，可多叶输出同一 hub”，这里建议将下列内容标作**待验证设计区别**：

- 叶动作是有限真实入口/入口集合，叶到 hub 不必一一对应；它表达同一 hub 在 query 空间中可能存在多块有效区域。
- 分支学习应比较其实际下游叶动作的搜索损失，而非先把某个 argmin hub 变成唯一正确类别后只优化分类准确率。训练代价如何估计和缺失动作如何处理必须明示。
- 这些区别不等于已证明优势。没有与硬标签树、同容量普通成本敏感模型和现有 Fast 的对照，不能把有效性归因于真实效用训练。

## 6. 从文献得出的可证伪约束

| 需要回答的问题 | 最小设计约束 | 不能替代它的证据 |
|---|---|---|
| 入口优势是否可预测 | 固定图、固定预算与动作集合；在隔离 query 上度量选择后真实搜索损失和 regret。 | train loss 下降、入口 ID 分类准确率、邻近标签准确率。 |
| 树的表达是否有必要 | 在相同输入、叶数/深度和训练标签条件下，比较真实效用树与硬标签树；允许多叶同 hub 的影响单独记录。 | 仅与旧 ranker 比一次，或只证明训练 oracle 有空间。 |
| 是否超出 GATE/LRSG 叙事 | 明确改变的是固定后续搜索下的入口决策目标与决策结构，提供原 query 轻量基线。 | “没有在线神经网络”“离线折叠”“用了搜索标签”。 |
| 在线收益是否覆盖路由支出 | 同时记 query 预处理、每层斜切点积、分支/内存访问、ID 映射、初始化与图搜索；用纯 wall 评估完整流程。 | hop、graph NDC、免费 oracle、离线缓存完的 query 决策。 |
| 离线重训练是否可接受 | 明列 exact train GT、query×action 搜索、叶/分支迭代、重复标签预算和模型输出时间。 | 只报 optimizer/train 耗时，或因用户允许离线重就不报告总量。 |

若全量标签是 20K query × 815 hubs，则每预算点每数据集为 1,630 万次搜索；821 hubs 则为 1,642 万次。这只是算术预算，没有执行。树的深度对在线成本给出结构上限，但不能将 `O(d·depth)` 直接换算成现有机器上的微秒，也不能忽略 cache、分支和 dense dot 的常数差异。

建议的停止条件是：若在明确的标签预算内，入口效用在隔离 query 上无法被小树捕捉，或完整路由支出超过图搜索节省，应判定该候选不成立；不要通过无限增深树、增大候选集或加入新在线编码器改变原假设后继续宣称同一方案获胜。

## 7. 本笔记支持与不支持的结论

支持：GATE 为直接入口前作；LRSG 为离线重、在线轻以及集合正确动作监督的强前作；LAN 和 NeuRoute 必须按实际对象区分。斜切树方向可以作为与 learned hub embedding 有结构区别的设计候选继续进行小规模证伪设计。

不支持：该候选已经优于 Fast；GATE/LRSG 已被本地完全复现或完全否定；真实搜索代价监督本身首次出现；树路由本身足够新颖；本轮下载或静态审计等于训练或性能验证。最终推荐与实验许可仍由 v4 主报告统一表达。
