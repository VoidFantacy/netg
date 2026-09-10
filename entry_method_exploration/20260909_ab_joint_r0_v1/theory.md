# 可路由性约束的入口—表示联合设计

> 版本：`20260909_ab_joint_r0_v1`  
> 状态：`R0_THEORY_REFORMULATED_DESIGN_ONLY_UNRUN`  
> 范围：理论重构与证据边界；未实现、未训练、未运行。

## 1. 更新后的核心判断

先前把 A“多面入口表示”和 B“入口池发现”分开审计，会自然得到两个偏悲观结论：多面分类器已有前作，portfolio 与 selector 共同选择也已有前作。但当前 Fast 根因证据说明，这两个问题本来就不能独立解决：

1. Fast1 在聚合 Recall 上距“直接提供旧 GT1 几何 basin 标签”只差 WebVid `1.64/1.74 pp`、Yandex `2.89/0.76 pp`；继续只提高旧标签恢复不能取回主要空间。
2. 即使直接提供该旧标签，距当前 H 内真实最佳 single 仍差 WebVid `13.07/10.35 pp`、Yandex `7.75/4.80 pp`。
3. exact 画像扫描替代 Micro-HNSW 没有双数据集稳定收益，说明主要矛盾不是近似索引漏掉当前画像最高分。
4. exact C8 相对全 H 的覆盖损失为 `3.16–6.66 pp`，C8 内从当前 exact1 到最佳 single 又有约 `2.75–7.50 pp`；候选覆盖和可路由选择同时构成瓶颈。

因此新问题不是“先找逐 query 最优入口，再训练更强分类器”，而是：

> **在固定轻路由容量和固定在线成本下，应如何共同设计可稳定匹配的查询决策区域及其真实入口动作，使可部署策略的 finite-L 原生搜索效用最大？**

这可理解为把全 H oracle 策略压缩成一个受限、可部署的入口策略。允许牺牲少量免费 oracle coverage，换取更小的路由／可实现性损失；最终只看样本外真实 routed Recall 与完整 wall。

## 2. 数学对象

对固定 dataset、base、raw-IP metric、冻结 NSG、`K=10` 和一个搜索预算 `L`，定义：

```text
u_L(q,e) = 原 ACSG::search_new(mode=2) 从真实 base ID e 单入口搜索的 Recall@10
C        = 已完整测量、训练侧合法得到的候选入口母集
M        = 路由槽数量；首版固定 M=|H|
s_j(q)   = 第 j 个路由槽的轻量分数，j=1...M
pi(j)    = 槽 j 对应的真实入口 ID，pi ∈ C^M
j(q)     = argmax_j s_j(q)
f(q)     = pi(j(q))
P        = range(pi)，实际被使用的入口集合，|P|≤M
```

`pi` 允许多对一：多个不相邻的槽区域可以映射到同一入口；某些候选入口可以没有槽。于是一个入口的决策区域是若干槽 cell 的并集，可以不连通。这是更新后的 A；`P=range(pi)` 又使实际入口池与受限路由器共同产生，这是更新后的 B。

经验目标为：

```text
maximize_(theta,pi)  (1/n) * sum_i u_L(q_i, pi(argmax_j s_j(q_i;theta)))
subject to           M fixed, range(pi) subset of C, router_cost(theta) fixed/bounded
```

等价地最小化相对候选母集 oracle 的真实 regret。训练必须保留 Recall ties 和完整效用向量；唯一最优 ID 的分类准确率不是目标。

当前 exact Fast1 是该策略类中的显式可行点：令 `M=|H|`、`s_j(q)=q^T p_j^Fast`、`pi(j)=h_j`，即可恢复现有画像全扫描。因而联合模型在表示上包含基线，但这只保证基线可恢复，不保证有限样本优化或样本外性能不会退化。

## 3. 覆盖、可路由性、拟合与部署的记账

令：

```text
V_C*          = E_q max_(e in C) u_L(q,e)
V_P*          = E_q max_(e in P) u_L(q,e)
V_(F,P)*      = 固定路由类 F、动作限于 P 时的最优可实现效用
V_exact       = 实际训练所得策略按 exact slot score 路由的效用
V_approx      = 同一导出策略经 micro-index 近似路由后的效用
```

则可作如下精确记账：

```text
V_C* - V_approx
  = (V_C* - V_P*)
  + (V_P* - V_(F,P)*)
  + (V_(F,P)* - V_exact)
  + (V_exact - V_approx)
```

四项依次是：入口覆盖损失、受限路由类的可实现性损失、估计／优化损失、近似部署损失。最后一项按实际效用是有符号量；近似路由偶然改善代理选择也不矛盾。这个分解是记账恒等式，不包装成新定理或未知 query 的 Recall 保证。

A+B 的核心是：在固定 `M` 和成本下共同改变 `P` 与路由区域，使前两项的总和降低；单独追求 `V_P*` 最大，可能得到难以路由的入口池。

对固定 slot 分区 `z_theta(q)=argmax_j s_j(q;theta)`，还可定义：

```text
J_C^oracle      = (1/n) * sum_i max_(e in C) u_L(q_i,e)
J(theta,pi)     = (1/n) * sum_i u_L(q_i,pi(z_theta(q_i)))
J_cell*(theta)
  = (1/n) * sum_j max_(e in C) sum_(i:z_theta(q_i)=j) u_L(q_i,e)
```

于是：

```text
J_C^oracle - J(theta,pi)
  = (J_C^oracle - J_cell*(theta))
  + (J_cell*(theta) - J(theta,pi))
```

这里 `J_*` 均指同一有限样本上的经验量，不与上面用期望定义的样本外 `V_*` 混用。第一项是当前 flat 分区压缩逐 query oracle 策略时留下的分区／可路由性损失；第二项是 slot 语义映射的估计或优化损失。固定分区时应用下一节的闭式 `pi*`，会在同一 fit 矩阵上把第二项降为零且不劣 identity mapping；这仍不保证 audit、泛化或完整 wall。

## 4. A 与 B 的新分工

### A：从“每 hub 加面”改为“构造可路由决策槽”

- 槽是查询空间中的决策区域表示，不再预先一对一属于某个 hub。
- 多个槽映射同一入口时，自然得到该入口的多面／多区域表达；无需先给每个 hub 固定面数。
- 总槽数首先固定为当前 Fast 画像数，避免把增容量误写成机制收益。
- 路由只读 query，输出一个真实 ID；训练期真实效用、GT 和搜索结果不能成为在线输入。

### B：从“先找 H 外节点”改为“由槽映射隐式选择动作池”

- 首版候选母集固定 `C=H`，先验证现有 815/821 个入口的效用能否被受限策略取回；当前证据已显示 H 内有足够 headroom。
- `P=range(pi)` 是联合优化后实际使用的入口池；入口是否保留取决于它在可实现路由区域中的真实效用，而不是免费 oracle coverage 或几何代表性。
- 只有现有 H 联合版本通过，且覆盖项仍主导剩余损失，才进入 H 外列生成／一换一交换。H 外候选只是第二阶段，不是首轮成功的必要条件。

## 5. 一个最小、可复核的交替结构

首轮从 Fast exact 的 `theta_0` 与 identity `pi_0` 初始化。

1. **固定路由区域更新入口。** 对槽 `j` 的训练行集合 `Q_j`，若暂不施加额外唯一入口或池大小约束，则闭式最优映射为：

   ```text
   pi*(j) = argmax_(e in C) sum_(q_i in Q_j) u_L(q_i,e)
   ```

   Recall 同分再按累计 graph NDC 与真实 ID 的预注册规则破同分。多个槽可选同一 `e`。

2. **固定入口映射更新区域。** 用 `u_L(q,pi(j))` 的 cost-sensitive／tie-aware 目标更新轻量分数；训练 soft loss 只用于优化，接受与报告必须使用 hard argmax 后的真实 routed Recall。
3. **交叉折接受。** 每次重映射、split/merge 或 adapter 更新必须在未参与该次拟合的 fit fold 上验收；fit 内折是训练选择信号，不是最终无偏证据。
4. **固定容量。** 不因失败增加 M、top-m、网络层数、候选列或轮数；任何容量变化另列对照。

若两个 block 都精确最大化，同一有限训练矩阵上的目标不会下降；实际近似优化只保留“候选更新通过留出折真实效用才接受”的经验保障，不宣称全局收敛。

## 6. Affine/OOD 的正确位置

当前 Fast 路由实际按 prototype 上的 inner product 排序；prototype 为单位向量，所以对固定非零 query 与 cosine 排序等价。在线 query 未额外归一化，而原 NSG 搜索继续使用 raw query。简单 query L2-normalization 不改变当前固定 prototype 的排序，因此它不是主要候选修复。

首版 affine 只作为 A 的受限表示变量和 2×2 主效应，不作为单独创新点：

```text
s_j(q) = (Aq)^T c_j^0 + b_j
A      = I + U V^T，或预注册的 diagonal residual
```

- `c_j^0` 冻结或强锚定到 paired-Fast20K 画像；`A` 使用 identity regularization 和固定低秩／对角容量。
- 不同时自由训练 `A` 与完全自由的每槽权重，否则 `A` 可被槽权重吸收，只是重参数化。
- 首版使用“无 translation + 每槽 bias”这一种语义；不再叠加可吸收的自由平移。
- 仿射分数可折叠为 `[q;1]^T[A^T c_j^0;b_j]`；导出向量不得独立 cosine 归一化，否则改变 bias 和排序。
- 变换仅作用于 router 副本，原 raw query 仍送入冻结 NSG；否则改变原问题、GT与全部下游身份。
- WebVid 512d 与 Yandex 200d 是不同图、不同入口 ID、不同坐标系，各自拟合参数，只共享结构与超参数。二者之间不是同一 router 的简单 OOD calibration。
- CORAL/whiten-recolor 可作无标签对齐控制，但分布矩匹配不等于 finite-L 搜索效用对齐。

## 7. 最小 2×2 机制归因

在 `C=H`、`M=|H|`、single-entry、exact slot score 下先做：

| 路由分数 | identity `pi` | utility-remapped `pi` |
|---|---|---|
| 当前 Fast IP/cosine | exact Fast1 | mapping-only（B 主效应） |
| 受限 affine | affine-only（A 主效应） | joint A+B |

除逐点比较外，报告交互量：

```text
Delta_interaction = J_joint - J_affine_only - J_mapping_only + J_exact_Fast1
```

`Delta_interaction>0` 是“联合优于两个部件简单相加”的直接描述，但只有预注册样本外区间通过后才能作为机制证据。联合方向至少应超过 exact Fast1、旧 GT1-basin 标签完美恢复参考值及两个单独主效应；否则分别降级为 remapping 或 affine 组件结果。这个参考值只表示完美恢复旧几何标签时的收益，不是任意入口策略的效用上界。

现有 E20 的 512 条历史 pilot 与辅助近邻行只能做回顾性 kill-screen、loader/parity 和效应量预估，不能参与最终阈值选择后又充当新 audit。

## 8. 原创性定位：承认组件前作，但不否定整体方法

评价标准更新为：**不要求每个组成部件首次出现；要求问题定义、约束耦合、优化对象和端到端证据形成不能由最近前作直接等同的完整方法。** 这与 GATE 的贡献形态一致：其 HBKM、two-tower contrastive learning 和导航图均有先例，贡献来自将 topology awareness 与 query awareness 组织成面向图 ANN 入口问题的轻量系统。

本联合方向可以主张的候选贡献是：

1. 用真实诊断识别“Fast 已接近旧几何标签完美恢复参考值，但该参考值远低于现有 H 的真实入口效用”，据此把入口学习从 label prediction 改写为受限策略设计。
2. 在固定图、固定 raw-IP kernel、固定 slot 数下建立 Fast 可恢复的 flat slot/action factorization，以多对一映射和共享受限 metric adapter 共同改变决策区域与活跃入口池。
3. 直接以 query×entry 的 finite-L 原生搜索效用共同优化入口动作与可路由区域，而不是先最大化免费 oracle coverage 再训练 selector。
4. 以 coverage／realizability／estimation／micro-index 四项记账和 exact→approx→full-wall 顺序，证明收益来自可部署联合策略而非增容量或免费 oracle。

与最接近工作的边界：

| 前作 | 已有部分 | 本方向需要证明的不同点 |
|---|---|---|
| 本地 v4 utility tree | 多叶同 hub、真实 finite-L utility、分区与叶动作交替更新 | fixed `M=|H|` 的 flat codebook、exact Fast identity 可恢复、显式 slot/action factorization、共享受限 metric adapter 与 micro-IP 部署 |
| GATE | 小真实 hub 集、query-aware 表示、hub 导航索引 | GATE 先固定 HBKM hubs；本方向在冻结原图上让真实入口动作与受限路由区域由 finite-L 原 kernel utility 共同决定，并显式超过旧几何标签完美恢复参考值 |
| MProtSVM／Maxout／AMM | 每类多个线性面、max 与 grow/prune | 这些方法的类集合与 prototype-to-class 归属预先给定；本方向的 slot-to-entry 映射和活跃动作池也是决策变量，目标是有 ties 的搜索效用而非通用分类首次性 |
| SPOTrees／decision-focused learning | 用下游决策损失学习区域 | 本方向把真实图节点作为动作，并同时设计动作集合、slot 表示与 micro-MIPS 部署；不能把 decision loss 本身称新 |
| Hydra／algorithm portfolio | 互补候选与 instance selector 共同配置 | 本方向的候选是同一冻结图中的真实起点，受固定 MIPS 路由容量、finite-L graph-search utility 和原 kernel wall 约束；不能把 portfolio 思想称新 |
| CORAL 等 affine adaptation | 线性域对齐 | affine 只是受限路由表示／对照，非核心贡献；必须由真实搜索效用决定是否保留 |

当前可以写“有可辩护、待验证的方法／系统原创性假设”，不能写“已证明首次”或“理论创新已成立”。尤其不能主张 maxout、多原型、affine、cost-sensitive loss、portfolio、交替优化、上述恒等分解或 MIPS 本身为新。

## 9. 进入实验前的顺序门槛

1. **理论与身份锁。** 冻结 single-entry 语义、`C=H`、`M=|H|`、2×2 参数容量、fold、ties、统计族、资源和拒绝路径；当前文档还不是 execution lock。
2. **现有 H exact 门。** 先用 exact slot score 检验 joint 是否超过 exact Fast1、旧 GT1-basin 标签完美恢复参考值和两个主效应，并在 WebVid/Yandex、L64/L128 没有预注册的实质伤害。
3. **新 audit 门。** 只有回顾性 screen 未被否决，才生成合法 fit 标签并在冻结后打开新的 development audit；训练 ID accuracy、loss 或 oracle 改善不代替 routed Recall。
4. **部署门。** 只有 exact 通过才建 micro-IP/HNSW，对照同一 scorer 的 exhaustive argmax，最后测 routing、graph、total 的独立整批 wall 与 Recall–QPS。
5. **H 外门。** 只有 existing-H joint 已通过且 coverage 项仍主导，才扩候选母集；候选提出、补列、交换和 audit 隔离须另立协议。
6. **top-m 边界。** 首版只做 single。以后 top-3 必须运行真实共享搜索；不能把多个 single hitmask 相加，重复 slot 映同 ID 时还须预先冻结去重与成本语义。

主要停止条件：joint 只提高训练或 oracle、不胜任一主效应、只靠增加 M／标签／候选范围才赢、某数据集系统性受损、micro-index 或完整 wall 吞掉质量收益。失败只否决冻结配置，不外推为所有可路由联合设计不可能。

## 10. 当前状态

本版本完成的是理论更新，不是实现或实验。旧 A/B R0 的组件碰撞证据继续作为 related-work 边界，但其“独立方向关闭／只配低原创性定位”的裁决已被新的整体原创性标准取代。

下一项交付应是一个独立批准版 protocol，而不是直接从旧 A 或 B 草案拼接命令。它需要重新冻结数据角色、最小模型、2×2 容量公平性、统计门槛、调用数、wall/RSS/磁盘上限和 artifact schema；在此之前不生成标签、不训练、不搜索。
