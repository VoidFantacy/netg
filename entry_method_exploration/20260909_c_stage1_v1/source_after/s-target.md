# ACSG 下一阶段目标：C 同状态有限动作诊断优先

> 2026-09-08建立，2026-09-09保留A+B联合理论，按用户授权优先执行C0–C2并在实质门停止。本文只维护下一阶段目标、阶段产物和进退条件。最近实测结果见[summary.md](summary.md)，实现合同见[spec.md](spec.md)，历史经验先由[s-experiment.md](s-experiment.md)进入详细复盘。当前用户已明确授权 C0→C1→有界C2，并将 C 设为第一优先级；A+B 仍为设计未运行。C0/C1已通过，C2已完成并触发实质headroom停止门；C3/C4、validation/held-out均未授权且未运行。

## 1. 当前优先级与状态

2026-09-09 当前执行优先级（覆盖旧R0文件中的未授权/先A+B表述）：

1. **C：同一完整搜索状态上的一次补充入口干预。** 已按第一优先级完成C0→C1→每dataset2K drl_train C2。当前冻结配置`NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`；阶段停止，等用户决定后续研究，不自动进入C3或重新分配预算救场。
2. **A+B：可路由性约束的入口—表示联合设计。** 保留以下联合理论，当前不实现、不训练、不与C混跑。
3. **D：策略修改驱动的成对标注。** 仍是某个真实效用策略成立后的离线效率支线。

v4 效用树是 A+B 最直接的本地强参照：它已经允许多叶映射同一 hub，并以真实搜索效用更新分区和叶动作。新 A+B 不能把这些宽泛概念称为首次；其差异必须落在固定 `M=|H|` 的 flat slot codebook、Fast identity 可恢复、显式 slot/action 分解、受限 affine metric partition 及 micro-IP 部署。

| 项目 | 当前状态 | 下一项交付 |
|---|---|---|
| Fast 根因诊断 E20 | 已完成，作为C之前的最近诊断保留 | 保持[当前总结](summary.md)与[历史08](experiment_history/08_fast_router_diagnosis.md)的证据边界 |
| B 独立 R0 v1 | 原 H 外 fixed-m/tree-swap 版本曾因过严的组件碰撞标准关闭；未运行 | 作为[历史版本](entry_method_exploration/20260909_b_r0_v1/README.md)保留，不直接复活旧 pilot |
| A 独立 R0 v1 | standalone per-hub facet 版本的待决状态已结束；未运行 | 作为[历史版本](entry_method_exploration/20260909_a_r0_v1/README.md)保留，其组件前作继续作为强对照 |
| A+B 联合 R0 | `R0_THEORY_REFORMULATED_DESIGN_ONLY_UNRUN` | 用户审阅[联合理论](entry_method_exploration/20260909_ab_joint_r0_v1/theory.md)后，另行冻结最小协议；当前不实现或执行 |
| C stage1 v1 / E21 | `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C` | [实际报告](entry_method_exploration/20260909_c_stage1_v1/report.md)、[gate](entry_method_exploration/20260909_c_stage1_v1/results/analysis_v1/gate.json)、[状态](entry_method_exploration/20260909_c_stage1_v1/state.json)；停止，不进入C3 |

原创性判断更新为：**已有组件不等于整体方法没有原创性。** 方法贡献可以来自新的问题定义、不可分的约束耦合、专门优化与端到端证据；GATE 也是这种贡献形态。当前 A+B 因而是“方法／系统层面的合理原创性候选，尚未由完整查新与实证确立”，不再是“组件已有即强算法 NO-GO”。C 的情况更窄：QING 2012 已覆盖搜索中保留状态并加入新 pivot，ANNiE 等已覆盖 learned live-state control；C 只能把同状态、共同预登记剩余 graph-NDC cap、逐分支实际成本和 candidate-specific `continue/force-expand` 成对动作值作为条件性贡献候选，不能声称首次动态注入。

## 2. 为什么必须联合 A 与 B

E20 的同 L、单入口 Recall@10 表明：

| 数据集 | L | Fast1 | 真实 GT1 basin | 当前 H 最佳 single |
|---|---:|---:|---:|---:|
| WebVid | 64 | 66.00% | 67.64% | 80.70% |
| WebVid | 128 | 73.87% | 75.61% | 85.96% |
| Yandex | 64 | 82.85% | 85.74% | 93.50% |
| Yandex | 128 | 91.00% | 91.76% | 96.56% |

因此 Fast 在聚合效用上已接近**直接提供旧 GT1 几何 basin 标签时的完美恢复参考值**。下文简称“旧标签参考值”；旧文中的 *label ceiling* 只是历史简称，**不是任意入口策略的效用上界**。该参考值距现有 H 内真实最佳 single 仍差 `4.80–13.07 pp`；它只说明继续恢复旧标签不足以取得主要机会。

同一诊断还显示：exact 画像替代 HNSW 没有双数据集稳定收益；exact C8 的全 H 覆盖损失为 `3.16–6.66 pp`，而 C8 内从 exact1 到最佳 single 又留下约 `2.75–7.50 pp`。候选覆盖和受限路由都在损失，故不能先独立找“oracle 最好入口”再假设它容易匹配，也不能只扩大表示而固定入口语义。

新的核心问题是：

> 在固定在线路由容量和原搜索成本合同下，选择哪些真实入口，并怎样构造轻量 query 决策区域，才能最大化样本外实际 routed finite-L Recall？

## 3. 联合理论对象

固定 dataset、raw-IP base、冻结 NSG、原 `search_new(mode=2)` single-entry kernel、`K=10` 和一个 `L`。令：

```text
u_L(q,e) = query q 从真实 base ID e 起跑的原生 Recall@10
C        = 已完整测量且来源合法的候选入口母集；第一阶段 C=H
M        = 路由槽数；第一阶段 M=|H|
s_j(q)   = 槽 j 的轻量 query score
j(q)     = argmax_j s_j(q)
pi(j)    = 槽 j 映射的真实入口 ID，允许多对一
f(q)     = pi(j(q))
P        = range(pi)，实际活跃入口池
```

联合目标为：

```text
maximize_(theta,pi) mean_i u_L(q_i, pi(argmax_j s_j(q_i;theta)))
subject to M fixed, range(pi) subset of C, router cost fixed/bounded
```

训练保留完整 Recall ties 与效用向量，不以唯一入口 ID accuracy 代替目标。当前 exact Fast1 是可恢复特例：使用 paired-Fast20K 画像、identity score 和 `pi(j)=h_j` 即可得到原策略；这只保证表示类包含基线，不保证训练或样本外不退化。

固定路由分区时，每个槽的经验最优入口有闭式形式：

```text
pi*(j) = argmax_(e in C) sum_(i: j(q_i)=j) u_L(q_i,e)
```

固定 `pi` 时，再以 tie-aware search regret 更新受限 score。候选重映射、分区更新或 split/merge 只能由未参与该次拟合的 fit fold 上 hard-routed utility 接受；soft loss 只服务训练。

## 4. 两种互补误差分解

在同一个有限评估查询集上，令 `J_C^oracle=(1/n) * sum_i max_(e in C) u_L(q_i,e)`，并对任意活跃池 `P` 类似定义 `J_P^oracle`。再令 `J(theta,pi)=(1/n) * sum_i u_L(q_i,pi(z_theta(q_i)))`。对 `P=range(pi)`：

```text
J_C^oracle - J(theta,pi)
  = (J_C^oracle - J_P^oracle) + (J_P^oracle - J(theta,pi))
```

分别是动作池覆盖损失与受限路由损失。联合方法允许略微牺牲前者以更大幅降低后者；只最大化 `J_P^oracle` 不是最终目标。

对固定 slot 分区 `z_theta`，再定义：

```text
J_cell*(theta) = (1/n) * sum_j max_(e in C) sum_(i:z_theta(q_i)=j) u_L(q_i,e)
```

则：

```text
J_C^oracle - J(theta,pi)
  = (J_C^oracle - J_cell*(theta)) + (J_cell*(theta) - J(theta,pi))
```

第一项衡量当前轻量分区压缩 oracle 策略的损失，第二项衡量 slot→entry 语义映射的估计／优化损失。在同一 fit 矩阵上应用上述闭式 `pi*` 会使第二项为零并不劣 identity，但这不是 audit、泛化或 wall 保证。

若加入模型拟合和 micro-index，还要继续分列：policy-class 可实现性、估计／优化、exact→approx 路由、完整部署成本。所有分解都是记账恒等式，不称新定理。

## 5. A、B 与 affine 的最新定义

**A：受限路由表示。** 槽表示可稳定匹配的 query 决策区域，不预先一对一属于 hub。多个槽映射同一入口时，该入口自然拥有多个可能不连通的区域。首版仍固定总槽数，不靠扩容获益。

**B：可路由性约束的动作语义与入口池。** `pi` 根据槽内聚合真实搜索效用选择入口，`P=range(pi)` 隐式形成活跃池。首版只在现有 H 内重映射；只有它通过且覆盖项仍主导，才扩展 H 外候选并另立列生成／交换协议。

**A+B：** 交替更新轻量分区和 slot→entry 映射，在固定 `M` 下直接最大化实际路由策略效用。它不是“先做 A、再做 B”的流水线。

当前 Fast 路由是 prototype 上的 inner product HNSW，距离函数为 `1-q^T p`；prototype 为单位向量，所以对固定 query 排序与 cosine 等价，在线 query 不额外归一化，原图仍吃 raw query。affine 的首版语义固定为：

```text
s_j(q) = (Aq)^T c_j^0 + b_j
A      = I + U V^T，或预注册的 diagonal residual
```

- `c_j^0` 冻结或强锚定到 paired-Fast20K 画像；`A` 使用 identity regularization。
- 不同时自由训练 `A` 与每槽任意权重，否则 affine 可被权重吸收，只是重参数化。
- 首版固定“无 translation + per-slot bias”；导出 `[A^T c_j^0;b_j]` 后不得独立 cosine 归一化。
- transformed query 只用于 router；原 raw query 继续进入冻结 NSG。
- WebVid 512d 与 Yandex 200d 是不同图、入口 ID 和坐标系，各自拟合参数，只共享结构／超参数；不能称作同一 router 的跨数据集 affine calibration。
- CORAL/whiten-recolor 只能作域对齐控制，分布对齐不保证搜索效用对齐。

## 6. 原创性主张与强对照

可辩护的候选贡献单位是：

> **Fast-compatible、固定 M 的 flat slot/action codebook，在冻结图的 finite-L 原生搜索效用下显式解耦 query 区域与真实入口动作，并以受限 affine partition 和 many-to-one 映射共同优化可部署效用。**

可以候选性主张：旧标签完美恢复参考值的实证诊断与新问题重述；Fast identity 可恢复的 slot/action factorization；固定路由容量下同时优化真实入口动作与可路由分区；exact→micro-index→full-wall 的完整部署验证。

不能声称：maxout、多原型、多个区域映射同一动作、decision-focused loss、portfolio、affine、交替优化、误差恒等分解或 MIPS 本身首次出现；也不能在未通过查新和实验前写“首个方法”或新泛化定理。

| 前作／本地参照 | 已覆盖内容 | A+B 必须证明的边界 |
|---|---|---|
| v4 utility tree | 多叶同 hub、真实 finite-L utility、分区与叶动作更新 | flat fixed-M codebook、exact Fast identity 恢复、显式 slot/action factorization、共享受限 metric adapter 与 micro-IP 部署 |
| GATE | 小真实 hub 集、two-tower query-aware 表示、拓扑语义与 hub 导航图 | GATE 先固定 HBKM hubs；A+B 在原图不变时让真实入口动作与受限路由区域由原 kernel utility 共同决定，并直接针对旧几何标签完美恢复参考值 |
| MProtSVM／AMM／Maxout | 每类多线性面与 grow/prune | 类与 prototype 归属预给定；A+B 把 slot→real-entry 语义及活跃池也作为变量，但不主张新函数类 |
| SPOTrees／decision-focused learning | 按下游决策损失学习区域 | A+B 的动作是冻结图真实节点，并受 flat MIPS 容量和真实 graph-search wall 约束；不主张 decision loss 新颖 |
| Hydra／portfolio work | 互补候选与 instance selector 的联合配置 | A+B 针对同一冻结图的入口动作、有限 L 搜索效用和可索引 query 分区；不主张 portfolio 思想新颖 |

如果联合项不能稳定超过两个单独主效应，应把结果降级成已有组件在 ACSG 上的适配，而不是继续宣称共设计贡献。

## 7. 最小析因与阶段门槛

第一阶段固定 `C=H`、`M=|H|`、single-entry、exact score：

| 路由分数 | identity `pi` | utility-remapped `pi` |
|---|---|---|
| 当前 Fast IP/cosine | exact Fast1 | mapping-only（B） |
| 受限 affine | affine-only（A） | joint A+B |

报告：

```text
Delta_interaction = J_joint - J_affine_only - J_mapping_only + J_exact_Fast1
```

阶段顺序：

1. **R0协议锁：** 冻结 2×2 容量、fold、ties、统计族、资源、输入身份和停止条件；当前未完成、未授权执行。
2. **回顾性 kill-screen：** 现有 E20 512 pilot 只可估计效应和检查实现，不作新证据或阈值选择后的 audit。
3. **existing-H exact gate：** 新的隔离样本上，joint 必须超过 exact Fast1、旧 GT1-basin 标签完美恢复参考值、affine-only 与 mapping-only，并满足双数据集、L64/L128 的预注册伤害规则；同时把 v4 树作为直接强对照。
4. **micro-index gate：** exact 通过后才测同 scorer 的近似路由损失；随后测 routing、graph、total 的独立整批 wall。
5. **H 外 gate：** 只有 existing-H joint 通过且覆盖损失仍主导，才允许扩 C；不能失败后直接以更多候选、M、top-m 或模型容量救场。
6. **正式阶段：** 方法冻结后仍需双数据集、相邻工作点、三独立构建和 held-out 10K×3；同 L Recall、oracle、NDC 或训练 loss 不能替代 Recall–QPS。

主要停止条件：joint 只提高训练／oracle、不胜任一主效应、只靠增容量或更多标签才赢、任一数据集出现系统性伤害、micro-index 或完整 wall 吞掉质量收益。失败只否决冻结配置，不外推成所有 query-only 共设计不可能。

## 8. C、与 A+B 的关系、资源与文档接续

C 已完成首阶段，当前结论是**C1通过，C2四点共同实质门失败，停止当前冻结配置**。本地 E13/E15 表明搜索进展有增量信号，但 E14 最终 v4 已使用 paid trace、frontier、topology 和 merged Recall/NDC 监督，在 WebVid 仍显著选错替代入口；其 Yandex 最终扩展未运行。C R0当时尚未测量的同状态、共同cap、四候选force相对continue增量，已由[E21](experiment_history/10_c_state_intervention.md)实际补齐。WebVid +0.980/+0.635pp通过，Yandex +0.230/+0.140pp未达四点均≥+0.5pp；四个校正区间均正，停止原因是实质空间不足，不是完全没有正增量。前作与原设计边界仍见[C R0](entry_method_exploration/20260909_c_r0_v1/README.md)。

C 的阶段门及当前进度为：

1. **C1已PASS：** 新state-machine的pause/clone/no-op/resume与原search_new在ID、float bits、NDC和扩展顺序等价，独立审阅通过；
2. **C2已FAIL并停止：** early-finished、无合法候选与no-op全部纳入N=2000均值；四点共同实质门未过，详见gate；
3. **C3未授权未运行：** 原定要求state-conditioned胜同容量query-only、原位共享状态胜restart/merge；当前不进入此阶段；
4. **C4未授权未运行：** 原定完整计入candidate/state/controller/injection/suffix后验独立整批Recall–QPS；当前没有性能GO。

任一门失败即停止该配置，不扩大为全 H chooser、多 checkpoint 或多步 RL。C 改变搜索过程语义，必须另验 partial-row 截断、expanded 与 visited 分离、count/plain 和纯 wall；旧独立 single 标签不能复用。

C 与 A+B 唯一自然的后续接口是：冻结的 deployed A+B 在 `t=0` 选初始真实入口并以固定 slot 工作量给出至多四个去重真实 ID，C 在其真实诱导状态上决定 continue 或一次 force-expand。A+B 的 runner-up 只可作候选生成控制，不等于条件救援效用；many-to-one 映射产生的重复 ID 必须在固定 slot 数后去重。起始策略改变会使 `P(S_t|router)` 变化，所以必须在最终 micro A+B 上重新 cross-fit 标注，不能迁移 Fast-C 或 exact-AB-C 标签。

只有A+B与C将来分别通过其独立门后，才允许`{Fast, deployed A+B} × {off, policy-specific C}`的2×2；本次C失败，因此当前不联动。`AB+C`只要胜 AB 并改善完整 frontier，就可称模块组合；只有交互量也稳定为正，才称协同。若 A+B 后没有 C oracle headroom，或 C 在 AB 状态上不胜 query-only/continue，就不联动，不能让 C 挽救 A+B 叙事。

若 A+B 后续采用完整 20K×H、两 L 标签，当前已知逻辑量仍为 `65.44M` fit calls；加两份 1024 开发集合为 `72.141056M`。这些是设计算术，不是已支付成本或 ETA。H 外每新增列另计；节省的合法复用不能改用于扩范围。任何重任务都须单进程、CPU-only、最多16线程，先观察约一分钟并按实际吞吐报告 ETA。

C 当前使用独立 stage1 v1 protocol/config/state/manifest：paired Fast3、K10、L64/128、完成33/65次扩展后的唯一checkpoint、全局额外B=1856，固定top7的后四槽、不补位；natural与force按同候选配对。四个点无条件oracle均值≥+0.5pp、Bonferroni4区间下端>0且有实际NDC envelope内非零有效覆盖，仅判common-cap headroom，不判等成本/Pareto。旧 A/B 草案不得拼接成伪命令。新实验结束或停止时，先写 `experiment_history` 和 `s-experiment`，再更新 `summary` 与本文；架构/API/metric/artifact/计时变化才同步 `spec`。

研究来源：[联合理论包](entry_method_exploration/20260909_ab_joint_r0_v1/README.md)、[C 独立 R0](entry_method_exploration/20260909_c_r0_v1/README.md)、[A 独立 R0](entry_method_exploration/20260909_a_r0_v1/README.md)、[B 独立 R0](entry_method_exploration/20260909_b_r0_v1/README.md)、[v5 A专题](entry_selection_research/20260908_v5/reviews/utility_representation.md)、[v5 B专题](entry_selection_research/20260908_v5/reviews/joint_entry_design.md)、[v5 C专题](entry_selection_research/20260908_v5/reviews/adaptive_intervention.md)、[v4树](entry_selection_research/20260908_v4/method.md)、[Fast诊断](fast_router_diagnosis/20260908_v1/report.md)。旧版本保留其当时判断；当前优先级与理论以本文及对应 R0 包为准。
