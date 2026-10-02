# GATE 直接入口前作补充核对

2026-10-02 12:45，UTC+8，补充只读审查定稿。只读原论文、固定作者源码及已有 E96/E97/E103 文本；没有执行 ANN、训练、构图、GT、query 评分或新性能测量。本文件独立追加，不修改已定稿的 `access_literature.md` 或文献 manifest。

**结论：GATE 是直接且已在项目内适配、测量过的入口前作。** “历史 query＋图结构监督→可预计算的 hub 画像→小图挑真实入口→原底图搜索”不能再作为新的机制贡献。GATE 的便宜在线访问不等于便宜监督，也不提供原入口/原 native 搜索结果保真；它不改变今天所有新候选 HOLD 的边界。

## 原始身份与本次实读范围

- Jiancheng Ruan, Tingyang Chen, Renchi Yang, Xiangyu Ke, Yunjun Gao，*Empowering Graph-based Approximate Nearest Neighbor Search with Adaptive Awareness Capabilities*，KDD 2025；arXiv:2506.15986v1，2025-06-19。原始 [arXiv](https://arxiv.org/abs/2506.15986v1)、[全文 HTML](https://arxiv.org/html/2506.15986v1)、[ACM DOI](https://doi.org/10.1145/3711896.3736930)。原文提供的 [Zenodo artifact](https://doi.org/10.5281/zenodo.15523071) 本次浏览工具未能打开，未据此猜测内容。
- 实读 §2 的 ANNS/搜索定义、§4.1 HBKM/真实 hub、§4.2 子图与 query 监督（Definition 4）、§4.3 fusion/projection/小图、§4.4 成本、§5.1 单线程与选参、§5.2 对照/消融、结论。另读项目保存的原论文文本第一页核对作者与发表 DOI。
- 作者 [源码固定版本](https://github.com/jacksondca/gate/tree/229f18dadb791ddede22597e44d5ceb028b104ba)，commit `229f18dadb791ddede22597e44d5ceb028b104ba`，与 E96 原协议冻结来源一致。本次通过作者 GitHub API/raw 原文件只读，不依赖二手摘要，也未编译该源码。

## 方法归属：上层增强，不是逐 query 改写主图

原文的上层使用从平衡分层聚类中选出的真实 hub，结合其局部图表示与历史查询监督学习画像，再在画像间建导航图。查询改变选择的 hub；底层 proximity graph 不需按 query 重构。主图拓扑保持并不自动保证初始化、遍历、预算、停止或浮点路径与我们的原搜索一致。

作者 release 的具体在线程序很清楚：[test_gate_search.cpp](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/tests/test_gate_search.cpp) 第 59–68 行用导出画像建小 HNSW，第 99–106 行原 query `searchKnn(...,3)`、按结果堆弹出次序映射真实 hub，第 108 行将入口交给 `IndexNSG::Search`。没有在线 query 神经网络前向。对应离线 [infer.py](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/infer.py) 第 67 行只对 hub/node/graph 特征前向，第 81–82 行直接比较导出画像与原 query 的 cosine；因此“two-tower”论文描述不能代替该 release 的真实执行路径。

它已经覆盖静态 query-distribution-aware hub、图结构特征、learned entry affinity、离线网络导出和小图避免逐 hub 在线推理。它没有给出 target-bank 三桶覆盖证书、保持原 HNSW 入口 trace 的距离 memo，或原 native 回调 bits 的早拒绝证书。后面这些区别仅定义评估对象，不足以证明新颖性或净收益。

## GT 与 hop：论文定义、执行监督是三个不同对象

论文 Definition 4 用 `H(q,v_i)` 表示从 hub 到该 query 真最近邻的图最短路径 hop，并在固定 hub 下对历史 query 集取最小值加 tolerance。§4.2 的实际生成说明则为每个 query 从每个 hub 跑 Algorithm 1，再数到 top-1 的 hop。执行过的有限队列搜索的发现路径长度不能未经证明当作图最短路径，也不能把 hop 当完整 wall 或全部距离计算数。

作者 release 进一步限定了监督：[combine_ep_gt.py](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/experiment/combine_ep_gt.py) 第 23–32 行读真实返回与 GT，返回不匹配便把 hop 设为 999；第 94–102 行组装 query×hub 矩阵；第 122–126 行按**同一个 query 跨 hub 的最小 hop**取正 hub；第 35–59 行由有效 hop 的尾部取负，先将 999 改成 -1。这个实际目标既不是 Definition 4 的固定 hub 跨 query 最小值，也不是“最近真实 hub”标签。

作者 [src/index_nsg.cpp](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/src/index_nsg.cpp) 第 618–660 行从注入入口用 BFS 填初始候选并记深度；第 689–698 行对首次见到的邻居传播父 hop+1；第 708–713 行输出最终返回项的发现路径 hop。`flags` 避免重新发现，它没有运行完整无权图最短路径算法。该量也不是扩展节点数。

成本原文 §4.4 已明确写训练数据构造 `O(|Q|·|V|·S)`，S 是底层 top-1 搜索成本。项目 E96 三集每集 `11024×512` 次标签搜索、共 `16932864` 次，已有完整记录：[E96 report](../20260914_gate_new_ood_v1/report.md:62)。这是已知方法的成本事实，不能把“训练贵”单独重新包装成尚未提出的新缺口。GT10 已有闭式画像构造；如果讨论新的监督机制，必须说明其增加了什么实际搜索效用信息，以及为何值得额外成本。

## 原论文与 release 差别及原样执行限制

原文 Eq.4 是归一化 affinity 的 InfoNCE 类目标；固定 release [train/__main__.py](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/cluster/model/train/__main__.py) 第 35–38 行 InfoNCE 注释，实际是 cosine triplet；第 57–59 行 hub 网络输出直接和正负原 query 做 loss。原文采样数由节点度动态计算，项目 E96/E97 用已披露的 release 5近5远、5跳/1000节点上限。相同方法名不表示监督、采样、网络与核全部逐位一致。

固定作者 snapshot 还有下列纯源码问题，本次未执行验证，**只用于限制“作者代码原样可运行/可作 bit 基准”的主张，不由此否定论文实验**：

- `test_gate_search.cpp:42` 检查 `argc!=7`，但第 59/61/113 行访问 `argv[7]`/`argv[8]`，参数合同不一致。第 87 行有开始 timer，第 113–115 行保存后退出，所读函数没有结束 timer 或 QPS 输出，无法凭这个程序独立确认论文全部 wall 的计时边界。
- 作者 [space_cos.h](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/include/hnswlib/space_cos.h) 第 6–15 行用 `L2Sqr(v,v)` 相乘作分母，并把 `InnerProductDistance` 当 ip；作者 [space_l2.h](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/include/hnswlib/space_l2.h) 第 7–19 行是两向量之差平方和，有限相同向量自距离为 0；[space_ip.h](https://raw.githubusercontent.com/jacksondca/gate/229f18dadb791ddede22597e44d5ceb028b104ba/include/hnswlib/space_ip.h) 第 17–19 行返回 `1-dot`。因此该 scalar 定义不能实现一般 cosine distance；所读 SIMD 分支也采用相同 self-L2 表达式。不能拿这个 snapshot 的 callback 作为我们归一化 IP 核的逐位一致基准。
- 这些检查不能说明论文作者当时运行的二进制/代码必然就是这一 snapshot。项目统一 native cosine/IP 与维度/标签修正必须继续公开，而不是删掉差异后称原样复现。

## 保证与固定核迁移边界

原文 §4.3 以 cosine 的“metric properties”解释导航收敛，没有给出有限 beam 上找最优 entry 的严格证明，更没有 entry 改动后 Recall 非降或端到端 QPS 提升定理。cosine similarity 本身不是 metric；即使用 `1−cos` 作距离，也不一般满足三角不等式。单位圆方向 0°、60°、120° 时距离为 0.5、0.5、1.5，违反 triangle inequality；这是解析数学反例，没有新向量评分实验。换成角度/弦距离也不能自动为任意有限度数图、原 ef10、原 stopping 提供召回或 native bit 保真。

可以在固定底图/固定主搜索合同内迁移的部分是“用另一种静态画像选入口”，项目已经做过。它改变入口，须重新计 Recall@1/@100 与完整 wall；hop 减少、更高 learned affinity、训练 loss、找到更接近 GT1 的 entry 均不能替代实测。其 query 模态鲁棒性是论文经验结果，不是任意新分布或我们冻结测试角色下的保证。

本次不重开 GATE 训练/采样/阈值/seed 分支，不用新 query 或 held-out 追验证。跨 kernel 固定控制的已有后续结果优先于 E96 旧核 QPS。

## 本地已有适配与完整 wall 的证据顺序

[E96 方法边界](../20260914_gate_new_ood_v1/method_notes.md:3) 保同底图/同原 `search_new`，明确 GATE 没有 query 神经塔，全部路由、归一化与映射计入 wall；第 6 行修正旧“扩展数作 hop”的标签。E97 [report](../20260915_gate_l2_r1_r100_v1/report.md:7) 修正正负 hub 冲突并重训五集，[流程](../20260915_gate_l2_r1_r100_v1/report.md:54) 保真实发现 hop、GT1返回门与导出一致性；它是受限适配，不是原论文无效的证据。

最新同核五集完整重测为 [E103](../20260916_optimized_five_dataset_r1_r100_v1/report.md:3)，所有 GATE/GT10/NSG 返回 ID、距离 bits、入口与 E97 一致，NSG/hard/soft/GATE 共用逐字相同 span+batch4；[计时边界](../20260916_optimized_five_dataset_r1_r100_v1/report.md:23) 包含原路由、归一化、图搜索与返回，单线程串行。Web R1 达到 90% 的最快实测点：默认 soft 90.75%/520.79 QPS，GATE 90.34%/507.84，NSG 90.65%/416.68；这是离散门槛点，不是严格等 Recall 比较。五集与 K 的收益不同，不能从这个点宣布通用优劣，更没有跨五集稳定替代默认的 GATE 证据。

## 对今天访问机制结论的影响

GATE 增加直接前作覆盖，收窄“再做一个图感知/query-aware learned entry router”的新意空间；它不新增 target-bank 粗桶保真、不提供可直接兑现的输出保持访问加速，也不改变已有成本缺口。

另核对 [memo_interface_note](memo_interface_note.md)：`UpperHandoff` 复用原 upper 已持有的 `curdist` bits，仅替代 base 原本会执行的同 slot/同回调评分事件；删除/过滤原 sentinel 分支保原逻辑。这个局部控制比对所有请求加 lookup 更简单，Default3 与 TargetBank 都应公平提供；它仍未测省时。memo 若进一步实验须比较所有事前冻结默认控制的最快者，包括原版、handoff 与同 memo 默认。它保的是原 callback 返回 bits 和原事件转移，GATE 保的是已改入口后的常规搜索流程，两者不可混用保真对象。

**处置：GATE 记为直接且已实验的前作；本次只补文献/源码边界，不提出新的训练或性能 GO。**
