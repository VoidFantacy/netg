# 面向 CCF B 的方法改进：查询表示研究

2026-09-20。用户确认目标为 CCF B 类会议，并同意先核对旧方法、研究限制，再提出最小验证。**本轮完成源码/文献审查、表示分析、16 个既有训练样本的数值几何检查和下一阶段协议；没有训练新模型或产生新的检索性能结论。** 最新正式效果仍为 E103，生产 E99、WebVid soft/Yandex hard 默认保持。

## 结论与选择

优先检验“**真实联合搜索收益能否迁移为一次轻量的查询非线性变换**”。查询网络每条 query 只运行一次，随后仍用原 Micro-HNSW 选三个真实入口，原查询进入原底层 NSG。首轮固定画像、hub、大图及 kernel，只改变查询侧表示，以便定位收益来源。

这与 E28 的 hub 侧 MLP、E36 的在线 56 组合打分有实质区别，但尚不是已经成立的论文创新。若它不能优于同监督的线性控制，或收益不能覆盖新增在线开销，就停止这一机制；不靠增加宽度、seed 或 RL 名称延长分支。若通过，再研究可达集合监督、跨分布迁移及廉价部署，形成可证伪的论文主张。

| 候选机制 | 本轮判断 | 为什么 |
|---|---|---|
| 查询侧非线性残差 + 联合效用蒸馏 | 首选一次受控验证 | 改变查询上的决策边界，保持一次小图路由；旧 hub 侧网络没有检验这一点 |
| 真实入口字典与表示共同设计 | 条件备选 | 仅当固定 H 的候选覆盖确实成为瓶颈；E22 已做 H 内重新映射，不能重命名为新发现 |
| 多步 RL 构图/选入口 | 暂不投入 | 当前一次选入口任务尚无必要的多步状态转移证据；原参数扰动/边修改已有大量负结果 |

CCF B 目标不等于必须使用复杂模型，也无法据此估计录用概率。现在需要补的是相对已有方法的明确差异、差异为何有效的证据，以及跨查询/数据分布的稳定收益。

## 旧实验实际覆盖了什么

| 已有工作 | 源码/原记录 | 确认范围与本轮意义 |
|---|---|---|
| Legacy Neural Router | [train_router.py](../../benches/run/train_router.py)，LightRouter 与训练前向；[复盘04](../../experiment_history/04_utility_and_representation.md) | 模型变换 pos/neg hub，query 只归一化；历史已有真实搜索监督，不能声称首次使用搜索标签 |
| E20 | [复盘08](../../experiment_history/08_fast_router_diagnosis.md) | 单入口 oracle、短名单与实际联合搜索分别检查；共用 beam/visited 会竞争，不能叠加单入口结果推算三入口收益 |
| E22 | [复盘11](../../experiment_history/11_ab_fixed_slot_exploration.md) | 固定真实 H 内的低秩表示及槽位重新映射；不是扩大真实候选入口集合 |
| E23 | [复盘12](../../experiment_history/12_three_entry_rank_exploration.md) | 已有真实三入口边际监督、完整 W/rank8；条件偏好翻转不等于最终最优三元组不可由 top3 表达 |
| E28 | [train.py](../20260911_gt10_shared_transform_v1/src/train.py)，Transform/teacher/fit；[复盘17](../../experiment_history/17_gt10_shared_transform.md) | MLP 输入 P，输出归一化静态 W，在线分数仍 qᵀw；query 不经过 MLP。free-W 控制已经覆盖 hub-MLP 导出的静态单位画像 |
| E29—32 | [历史索引](../../s-experiment.md) | 多等价教师、保留原方法、集合期望目标已探索；更换为集合标签本身不构成新贡献 |
| E36 | [交接86](../../experiment_history/86_post_closeout_rl_direction_review.md) | 已有 query 相关集合 MLP，但在线枚举/评分 56 组合；不能说旧项目完全没有查询相关非线性 |
| E95 | [复盘87](../../experiment_history/87_query_moment_graph_and_branch_stop.md) | 当时固定 H 的画像/小图增强分支停止；本轮不恢复旧 runner |

本轮直接检查了 Legacy、E28、E97 GATE 训练源码和 GATE 作者发布的 model/infer。GATE 论文使用双塔表述；所查作者提交及本地适配实际导出 hub 表示，在线 query 直接用于 cosine。不能把这条源码事实泛化为所有双塔方案，也不能把论文的一般双塔公式误读为已实现在线查询 MLP。

作者源码身份来自 [上游来源记录](../20260914_gate_new_ood_v1/sources/gate_upstream_model.py.source.json)，提交 `229f18dadb791ddede22597e44d5ceb028b104ba`；[infer 副本](../20260915_gate_reproduction_audit_v1/sources/cluster__model__train__infer.py) 第 67/81 行分别计算 hub embedding 与原 query cosine。[本地 train_gate.py](../20260915_gate_l2_r1_r100_v1/src/train_gate.py) 第 100/103 行同样使用原查询。

## 文献差异，而非模型名称差异

| 一手文献 | 已有内容 | 本项目必须额外证明的内容 |
|---|---|---|
| [GATE，KDD 2025](https://arxiv.org/html/2506.15986v1)，§4.2–4.3 | 真实 hub、拓扑增强、查询监督、导航小图；双塔框架已存在 | 在其框架附近，真实有限预算三入口效用与查询表示的改变能提供什么不可替代的收益 |
| [Learning to Route in Similarity Graphs，ICML 2019](https://proceedings.mlr.press/v97/baranchuk19a/baranchuk19a.pdf)，§3.1–3.4 | 学习 query/node 两个映射；用最短路径专家监督图遍历；实验 query 分支为恒等/线性 | 本项目只改变初始入口，不用学习分数替代底图遍历；仅提 query encoder 并非新颖性证明 |
| [Clustering-Based ANN 的 LTR，SIGIR 2024](https://arxiv.org/html/2404.11731v1)，§3 | 固定分区，以 GT 所属分区作为相关性，学习线性路由代表 | 有限 beam 的入口联合收益与分区包含 GT 不等价；不能直接移植其单相关项/MRR 一致性结论 |
| [CRINN，arXiv 2508.02091](https://arxiv.org/abs/2508.02091)，摘要 | 以运行速度奖励优化 ANNS 实现 | 此处只用来区分研究对象；本轮未完整复现/审读算法，不能据其标题推断多步入口 RL 必要 |

上述是针对当前设计的定向查新，不是穷尽性 novelty 审查。后续若 pilot 通过，还须围绕最终监督目标做更完整查新；不能现在就声称“首次”。

## 表示分析

令 H 个固定画像组成 P，画像 p_h 对应真实 hub ID。旧方法的精确路由分数为 s_h(q)=qᵀp_h。

1. **hub 侧网络仍是静态线性路由。** 无论离线网络多深，导出 w_h 后，两入口分界为 qᵀ(w_a−w_b)=0。E28 的训练非线性并没有变成 query 上的非线性分界。此论断针对精确分数，不声称有限 ef 的 HNSW 输出分区也线性。
2. **仿射 query 可折叠。** 若 f(q)=Aq+b，则 p_hᵀf(q)=qᵀAᵀp_h+bᵀp_h，可用静态权重加 hub bias 表达。无 bias 时不需要额外维度；有 bias 可增广常数维。折叠后不可再随意单位化各行，否则分数已改变。浮点/HNSW 遍历一致性另验，不由代数等价自动保证。
3. **非线性 query 确实改变表示族，但固定 P 仍有限制。** 三入口集合 S 严格成为 top3 当且仅当存在 z，使所有 a∈S、b∉S 满足 (p_a−p_b)ᵀz>0。有限约束下可缩放成统一正 margin 的线性可行性问题。某个 S 可达，不等于所有 S 可达，更不等于同一个小网络能对新 query 预测它。
4. **小变换可以有条件保序。** 设 z=q+δ；若旧 pair gap 大于 ‖p_a−p_b‖₂‖δ‖₂，则该 pair 次序不变。这只是 Cauchy–Schwarz 的直接结果，可解释正则化和边界稳定性，不能包装成新的搜索召回定理。

以上分析帮助排除无效控制与设计诊断，本身不足以支撑一篇方法论文。

## 本轮实际完成的数值检查

在读取样本前固定两集各 8 个 fit 位置：0、2500、…、17500。只读 E24 GT10-hard 画像、既有 fit query 和 E28 已保存教师 slot；不读取 GT、hits、cal、audit、validation 或 test 载荷。WebVid 此处也使用 hard，是为了匹配 E28 教师身份，不代表修改 Web soft 默认。

对每条样本求 `min ||δ||∞`，约束原单位查询 q 加 δ 后，教师三个画像以至少 1e-4 margin 超过其余全部 H−3 个画像；不只在原 C8 内比较。HiGHS 每次最多 5 秒、1 线程。每个成功解重新检查全部 pair margin 和精确 top3 集合，保存 z 作为数值 witness。

| 数据集 | 原 query 已选中教师集合 | 找到并核验的可行 witness | 最大坐标变化范围 | 新旧方向 cosine 最小值 |
|---|---:|---:|---:|---:|
| WebVid，H815/d512 | 3/8 | 8/8 | 0—0.00621522 | 0.99011709 |
| Yandex，H821/d200 | 2/8 | 8/8 | 0—0.00404808 | 0.99837393 |

仿射分数折叠另经同一批真实 P/query 检查，最大绝对误差分别 1.78e-15/1.22e-15。整个脚本约 7.82 秒。输入 SHA 前后相同。原件见 [预锁规则](reviews/geometry_lock.json)、[脚本](src/audit_representation.py)、[逐行结果](results/representation.json)、[witness](results/geometry_witnesses.npz)。

**允许的解释：** 这 16 个历史教师集合没有被固定 P 的精确 top3 几何直接排除，查询变换有可检验的表示空间。**不允许的解释：** 8/8 不是数据集总体可达率；历史 K10 教师不是新的 K1/K100 收益；独立求出的 z 使用教师信息，不能在线使用；本轮没有检验小 MLP 的可学习性、OOD 迁移或 HNSW 可达性，也没有证明全局最小扰动的严格数值证书。

## 推荐方案与论文成立条件

首轮模型：q₀=normalize(q)，z=q₀+U ReLU(Vq₀)，隐藏宽度 16，U 零初始化。P 与小图保持原件。在线为：

```mermaid
flowchart LR
  Q[原始查询 q] --> N[归一化与一次残差 MLP]
  N --> H[固定 P 的 Micro-HNSW]
  H --> E[三个真实入口]
  Q --> S[原 NSG 与原距离]
  E --> S
```

查询变换只影响路由，不能改变底图的 IP/L2 定义。两层约 2dr 乘加：WebVid 16384、Yandex 6400；这不是延迟预测，激活、归一化、调用及所有小图开销均要计入 full wall。

主要监督仍用**同一次真实三入口搜索的结果**，复用已有集合损失作为控制，不同时引入新的 hub、图结构、预算条件输入和多种损失。若存在可靠迁移，再研究“先约束教师集合在轻量路由表示中可达，再蒸馏”的方法；离线 LP 的成本、任意教师 tie 与泛化都必须收费/检查。首轮不把它们混在一起以免无法归因。

需要依次成立的证据链是：当前 K1/K100 下有联合效用余量 → 小网络能在开发 query 上比线性控制更好地兑现 → 原小图能实际找到对应入口 → 完整在线时间仍优于 GT10 → 新的分布/独立评估支持迁移。任一环缺失，就不能把训练拟合或几何 witness 写成论文性能。

具体样本、控制、训练上限、完整预算及停止标准已写入 [最小验证协议](protocol.md)。协议为待实现设计，未启动训练/搜索队列。验收与原文件保护见 [completion_audit.json](reviews/completion_audit.json)。
