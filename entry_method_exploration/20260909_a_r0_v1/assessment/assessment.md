# 方向 A R0：有限搜索效用上的多面入口表示

> 版本：`20260909_a_r0_v1`  
> 状态：`R0_NOVELTY_NO_GO_AWAITING_USER_DECISION`  
> 范围：只读历史、源码与一手前作评估；没有方法实现、标签生成、训练、搜索或评测。

> **历史版本提示（2026-09-09）：** 本文保存 standalone per-hub facet v1 当时的组件碰撞判断；其“关闭或降级”裁决已被用户否决并由[A+B联合理论](../../20260909_ab_joint_r0_v1/theory.md)取代。下文没有被改写为实验结果，组件前作仍作为新方法的强对照。

## 1. R0 结论

原提案希望给每个固定真实 hub 分配多个仿射打分面，以完整 finite-L single-entry Recall regret 提出、增加和删除面，再把所有面展平到一个微型 inner-product 索引中。经过补充的一手核查，**它不能继续作为强算法原创性候选进入实现**：

```text
NO_GO_AS_STANDALONE_ALGORITHM
OPTIONAL_DIAGNOSTIC_ONLY_IF_SYSTEMS_EMPIRICAL_FRAMING_ACCEPTED
NOT_IMPLEMENTED_NOT_RUN
```

原因不是“找到一篇完全同名的 frozen-NSG 论文”，而是提案的四个算法支柱已有直接或近直接前作：

1. 每类多个线性/仿射面、类内取最大值已有 MProtSVM、AMM/GAMM；
2. loss-augmented 最大值减正确输出的 latent 最大值已有 latent structural SVM；
3. 固定资源下的原型增添、删除、融合和非均匀容量已有 adaptive LVQ 与 Sparse Multi-Prototype；
4. 单 query 对每个对象多个向量取最大内积、把全部对象向量展平进向量索引再映回对象已有 ME-BERT/MVR；其中 ME-BERT 明确讨论 ANN/ScaNN，MVR 的公开实验使用 exact Faiss `IndexFlatIP`。

剩余相对独特的边界是：固定 raw-IP base、冻结 NSG、固定真实 H，用原生 single-entry kernel 在有限 L 下得到 query×hub Recall 矩阵，并在每次容量变化后计算真实救回与新伤害。这是有价值的 **ANN 专用问题定义和系统实验边界**，但当前没有一个依赖该结构的新提案定理、交换性质或不可被通用多原型方法吸收的算法。因此，若论文目标坚持强算法 novelty，建议关闭 A 并把 R0 资源转到 C。

若用户愿意把目标降为 systems/empirical contribution，仍可问一个较窄的问题：在完全相同的 H、标签、总面数、模型字节和在线完整 wall 下，finite-L 真实效用是否呈现普通等配额多原型无法表达、而非均匀多面容量可以稳定利用的结构？这个问题尚未测量；通过也只能先支持受限实证贡献，不能恢复“新分类器、新结构化损失、新增删算法或新 MIPS”的表述。

## 2. 观察、设计和未知必须分开

### 2.1 已观察的本地事实

1. 当前正式范围是 WebVid-2.5M 与 Yandex official first-10M，raw inner product、原冻结 NSG、K=10、L=64/128；现有 H 分别有 815/821 个真实 base ID。
2. 最近全 H 根因诊断在 WebVid 767 行、Yandex 768 行上真实枚举了两个 L 的全部 single 入口。前 512 行是历史 pilot，其余 255/256 行是围绕前 128 pilot 选出的 nearest-fit 与 random-fit 辅助行去重结果；它们不是均匀 20K fit，也不是新 calibration/audit。
3. 该诊断确认全 H single oracle 与 Fast1 之间有明显空间，且画像分数与真实 single Recall 的平均 Spearman 很弱；这说明表示瓶颈值得研究，**不证明多面表示或某个增删算法有效**。
4. 历史 sparse utility ranker 已直接使用真实 single Recall/NDC、soft utility label、query–entry interaction和难query加权；WebVid同L只有 `+0.197～+0.329 pp` 且graph NDC增加 `0.47%～1.03%`，Yandex为 `-0.042～+0.202 pp` 且NDC增加 `1.78%～3.31%`，没有端到端wall或独立构建。故“使用真实效用/soft loss”本身既不新，也不是已验证成功机制。
5. 历史 Multi-view 在同L早期有局部正变化，但正式equal-total-NDC四点Recall相对Fast为WebVid `-14.697/-4.960 pp`、Yandex `-4.103/-1.463 pp`，状态`NO_GO_ROUTING_COST`，等wall、E2–E4及held-out按停止规则未运行。这直接要求A先过exact表示门，再单独支付部署成本；不能用同L质量或MAC推断Pareto。
6. 历史 search-aware centroid 在 WebVid 有小的 Recall 正变化但 NDC 增加，未形成跨数据完整成本结论；utility residual 在 WebVid validation10K 为约 `+0.077～+0.114 pp` 的窄正信号，未做 Yandex、独立构建或完整路由 wall。
7. 最接近“一个 hub 多模式”的 target-basin modes 已在后20K拟合、前10K及 validation10K 评估。v2 anchored 的 validation 变化为 WebVid `+0.176/+0.085 pp`、Yandex `+0.017/-0.017 pp`；新增在线内积未计完整 wall。它只否决那一版几何 modes，不否决所有多面模型，也不能作为 A 的正证据。
8. 当前代码有可复用的原生 single-entry 调用、全 H count/mask/NDC/IDs 输出和纯 wall 计量结构，但没有 A 的 facet trainer、facet index 或端到端 evaluator。因此当前不是 `IMPLEMENTATION_PASS`。

这些事实分别由[表示历史](../../../experiment_history/04_utility_and_representation.md)、[Multi-view历史](../../../experiment_history/02_multiview_and_attention.md)、[正式Multi-view终态](../../../target_basin_formalization/20260907_v1/report.md)、[Fast根因诊断历史卡](../../../experiment_history/08_fast_router_diagnosis.md)、[诊断协议](../../../fast_router_diagnosis/20260908_v1/protocol.md)及当前源码绑定。旧结果的同 L Recall、graph NDC 或 instrumented diagnostic wall 都不是端到端 Recall–QPS 结论。

### 2.2 只属于设计、尚未观察

- hub 的有限-L效用区域确实需要多个不连通决策块；
- 非均匀面数优于同 M 的等配额 maxout/MProtSVM；
- regret-aware 提案优于普通 hard-ID/standard validation pruning；
- exact facet scan 的收益足够覆盖微索引近似损失和在线 wall；
- 双数据集、两个 L、独立构建上存在完整 Recall–QPS Pareto 改善。

本 R0 没有生成任何支持或反驳这些假设的新数据。

## 3. 最接近前作与碰撞边界

| 前作 | 已覆盖的核心对象 | A 剩余差异与不能宣称的内容 |
|---|---|---|
| Aiolli–Sperduti 2005 MProtSVM | 每类多个线性 prototype；正确类内取最大分数；非凸目标与交替/局部优化 | 增广常数维后与 `max_j(qᵀw_hj+b_hj)` 同型；不能把“一个 hub 多面”当新表达 |
| Wang 等 2011 AMM；Djuric 等 2020 GAMM | 多 hyperplane/class；SGD；AMM 从预留零权重激活新面并按范数剪枝；GAMM 在正损失时复制分配给当前样本的正确类面；后续作者 BudgetedSVM 实现另提供每类 `-B` 上限 | A 的 grow/prune 叙事已有高度直接前作；仅把分类误差换成搜索 regret 不自动构成新算法 |
| Yu–Joachims 2009 latent structural SVM | `argmax_y max_z`；loss-augmented max 减正确输出 latent max | 令 `y=hub,z=facet,Delta=measured regret` 后，A 的损失是近直接特例；不能把该 hinge 或非凸性包装成新理论 |
| Grbovic–Vucetic 2009 adaptive LVQ | 跨类全局prototype硬上限B；为误分样本增加可能有益prototype并删除有害或少用prototype，形成非均匀容量 | 全局硬预算与add/remove已有近同通用结构；A只剩max-affine、冻结图finite-L效用和全query×hub反事实rescue/new-harm验收差异，故必须作为强基线 |
| Garg–Xiao–Dekel 2018 Sparse Multi-Prototype | 类内最大内积；资源受限；以正则融合/压缩原型并控制容量 | 非均匀每类容量和稀疏多原型不是新贡献 |
| Luan 等 2021 ME-BERT；Zhang 等 2022 MVR | 单 query 对文档多向量取 max inner product；把全部文档向量展平进向量索引并映回文档 | `facet→hub` 扁平 MIPS 是直接部署先例；ME-BERT 讨论 ANN/ScaNN，而 MVR 的公开实验用 exact `IndexFlatIP`；A 只有一个 query 向量，不需要 MUVERA 的 set–set FDE |
| Maxout、SoftTriple、Sub-center ArcFace | max-affine 及监督多中心/类已是成熟模型族 | 只能作背景/对照，不能支撑首次性 |
| GATE、Oguri–Matsui adaptive entry | 冻结或 off-the-shelf 图上的 query-aware 入口学习；真实 hub/real-ID入口 | A 的标签和多面容量不同，但“学习图入口”本身早已有前作 |

主要一手入口及固定作者代码版本见[`source_manifest.json`](../source_manifest.json)。本轮检索是定向查新而非穷尽证明；“未找到完整组合”不能抵消上述逐组件的强碰撞。

## 4. 数学对象为何不足以单独建立新颖性

对固定数据集、H、L，令真实效用为：

```text
R_i(h) = Recall@10(q_i, h; L)
R_i*   = max_h R_i(h)
r_i(h) = R_i* - R_i(h)
G_i    = {h : R_i(h) = R_i*}
```

每个 hub 有 `m_h≥1` 个仿射面，总预算 `sum_h m_h=M`：

```text
s_h(q)    = max_j (q^T w_hj + b_hj)
h_hat(q)  = argmax_h s_h(q)
ell_i(s)  = max_h [s_h(q_i) + r_i(h)] - max_{g in G_i} s_g(q_i)
```

对 exact score argmax，训练行上有 `r_i(h_hat)≤ell_i(s)`。这只是把被选动作代入第一个 max、再用其分数不低于任一最优动作分数得到的代数关系；它依赖已知行的全 H 标签，不是未知 query 的 Recall 保证。其第二项是正确输出集合中的 latent max，优化非凸，与 latent structural SVM 的标准结构一致。

将面写为 `[q;1]ᵀ[w;b]` 后，`max_h max_j` 可展平为所有 facet 的一次 inner-product maximum，再由 facet ID 映回 hub。不能独立 cosine 归一化 facet 后仍声称仿射分数保序；普通 HNSW 也不提供每 query 的认证近似误差。exact scan、exact flat-IP 与 approximate micro-MIPS 必须分开测，但这种分解属于实验卫生，不是算法创新。

## 5. 若降级重开，唯一可辩护的经验机制

可选诊断固定 H，不发现新入口、不改图、不改原 single kernel。每个 L 独立拟合，在相同总面数 `M∈{2H,4H}` 下比较等配额和非均匀容量。非均匀候选只能被描述为 **finite-L regret allocation 的系统适配**：

1. 从同 M 的等配额、tie-aware latent maxout 初始化；每个 hub 至少保留一面。
2. 在 fit 内冻结的 proposal folds 上，逐面计算 suppress-one-facet 后真实 routed regret 的变化；同时按“目标 hub 属于 `G_i`、当前选择有正 regret”的行累计每 hub 未满足 regret mass。
3. 每轮预先固定一个不超过总 M 的5%批量：移除 proposal 上损失最小且不破坏每 hub 下限的面，把槽位分给未满足 mass 最大的 hub；新面由相应冲突行的确定性加权方向初始化，再用同一 latent objective 重拟合全部面。
4. 只在该轮未参与 proposal 的 acceptance folds 上，以真实 argmax 后的 mean regret、rescued、newly harmed 和最坏数据点验收整批；不合格立即停止，不缩批重试、不换 seed。至多四轮，不能因 calibration 失败增加面数或轮数。
5. calibration 只能在 `2H/4H` 两个冻结预算中选一个全局配置；模型、scorer、tie规则和索引参数冻结后，audit 只评分一次。

这只是一个可实现、可证伪的参考算法轮廓，**不是已证明新颖或已批准的执行合同**。若重开，proposal/acceptance folds、优化器、正则、gauge、初始化、批量同分规则、每 hub cap、epoch、seed 和停止阈值都必须在新的 protocol lock 中逐项唯一化。当前草案不为不存在的 runner 写伪命令。

## 6. 强基线和析因要求

若不愿实现以下对照，就不应投入 A 的论文级诊断：

1. **同 H、同标签、同输入：** 一面/hub；同 M 等配额 MProtSVM/maxout；同 M hard-ID maxout；同 M 几何 query 多原型。
2. **通用自适应容量：** GAMM/AMM 式 clone+prune、adaptive-LVQ 式 add/remove、Sparse Multi-Prototype 式融合/稀疏控制是三个分列对照，不能任选其一代替其余。无法逐位移植时，必须冻结公平适配并把差异写明，不能删除基线。
3. **析因：** fixed allocation + regret hinge；adaptive allocation + ordinary hard-ID/standard validation pruning；adaptive allocation + proposed rescue/harm；另列 random、frequency、conflict-mass allocation。
4. **项目强参照：** Fast1、真实 Fast3、v4 utility tree；论文级阶段再加入 Oguri–Matsui 与 GATE 的作者对齐或明确不可逐位对齐的系统比较。
5. **部署序列：** exact all-facet scan 是表示 ceiling；只有它通过才测 exact flat-IP 和 approximate micro-MIPS；最后才测含路由、映射和原搜索的 full-batch wall。

若 adaptive 只胜 Fast/单面但不胜同 M 普通多原型，应降级为普通 maxout 组件；若只靠 loss 或容量变化取胜，删除不成立的算法叙事。

## 7. 标签与成本事实

完整逻辑标签矩阵为：

```text
fit:        20,000 * 2 L * (815 + 821) = 65,440,000
cal+audit:   2,048 * 2 L * (815 + 821) =  6,701,056
total:                                      72,141,056 native single-entry calls
```

8条/数据集的全 H `count/plain/repeat` 验收另需 `78,528` 次；cal+audit 上真实 Fast3 描述性质量另需 `8,192` 次。因此，若从零执行，已列质量阶段的调用数是 `72,227,776`，失败/重试也必须计入批准版硬上限。已有诊断最多只有255/256条辅助 fit 行可能按完整复用键节省部分 cell；旧512 pilot不能用作新的 calibration/audit，节省不能扩张范围。

完整键必须包含 query ID、真实 hub ID、L、K、base、metric、graph、kernel 和标签定义。现有767/768行矩阵只能用于派生 runner 的 loader/parity smoke 或合法 fit cell 复用；不能替代20K拟合矩阵、表示 gate 或 audit。

仅保存每 cell 的 `hitcount:uint8 + hitmask:uint16 + graph_ndc:uint32` 为504,987,392 B（约505 MB）。若每cell再保存top10 `int32` IDs，IDs单独增加2,885,642,240 B（约2.886 GB），两者合计3,390,629,632 B（约3.391 GB，未计元数据）。参考协议默认只为确定性parity行保存完整IDs，使新产物硬限保持1 GiB；若用户要求全部IDs，必须将硬限显式提高到5 GiB。

E20 的旧主 job 约1.34M次调用/数据集，job wall约54–59秒，其中全 H instrumented search wall另分 L 记录。它是含加载、路由和诊断逻辑的旧作业，不是 A 的纯 wall，也不是当前硬件下72.14M调用的实测 ETA。若重开，首个重任务启动后观察约一分钟，再依据本版实际吞吐报告 ETA；参考上限建议标签累计wall≤4小时、训练≤8小时、单重进程、16线程、RSS≤20GiB，而不是把线性外推当承诺。

## 8. 条件 gate 与停止边界

这些 gate 只有在用户选择 systems/empirical 重开后才有意义：

- **G0 实现/身份：** split与拒绝路径、真实ID、原single入口消费、GT后置、count/plain/repeat、C++/Python exact scorer、facet→hub、tie/export、分块恢复与所有SHA全部通过。失败只修实现，不作方法结论。
- **G1 calibration freeze：** 只从预注册的2H/4H与固定算法中选一个全局配置；不得按单数据集或单L分别挑最好。随后锁模型、scorer、统计和索引配置，才可生成/打开 audit 标签。
- **G2 exact representation：** adaptive exact facet 必须在同一主比较族中同时胜一面、同M等配额maxout、同M几何多原型，以及分列的同M GAMM、adaptive-LVQ和Sparse Multi-Prototype适配，并胜Fast1；报告真实Recall/regret、rescued/newly harmed、ties、活跃面、每hub面数和稀有hub。任一主机制门失败，不追加模型家族、面数、轮数或再次使用该audit。
- **G3 deployment：** 仅 G2 通过后才建微型 raw-IP facet index。近似选择损失必须小于预先冻结的 exact 收益份额，再测含 query预处理、facet路由、映射、入口初始化、visited/reset和原搜索的完整 wall。GT/hash/JSON/count排除，routing、graph和total分列；五轮独立full-batch并轮换方法顺序。
- **正式阶段：** 只有开发 G3 通过，才另行申请三独立构建、validation/held-out和最终同Recall QPS `≥+10%` 或同QPS Recall `≥+1 pp` 门槛。当前 R0 不授权其中任何一步。

数值统计阈值、比较族和 exact→approx 可接受损失必须由用户在执行前批准；本 R0 不用事后阈值代替决定。

## 9. 当前唯一关键选择

推荐选择：

```text
CLOSE_A_AT_R0_FOR_NOVELTY_COLLISION_AND_PROCEED_TO_C
```

备选仅在用户主动接受较低原创性时成立：

```text
REOPEN_A_AS_BOUNDED_SYSTEMS_EMPIRICAL_DIAGNOSTIC
```

选择推荐项表示研究优先级关闭，不能写成性能失败；选择备选项也不代表 A 通过 novelty gate，只是授权下一版先实现 G0 和 exact 表示诊断。用户选择前，状态保持等待，不实现或运行。
