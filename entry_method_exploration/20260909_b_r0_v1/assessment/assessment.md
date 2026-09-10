# 方向 B R0：冻结图上的受限选择器感知入口交换

> 版本：`20260909_b_r0_v1`  
> 状态：`CLOSED_AT_R0_NOVELTY_COLLISION_UNRUN`  
> 范围：只读评估与协议设计；没有方法实现、训练、搜索或评测。

> **历史版本提示（2026-09-09）：** 本文只记录 H 外 fixed-m/tree-swap v1 的关闭决定。当前 A、B 已按较合理的方法层原创性标准重构为[A+B联合理论](../../20260909_ab_joint_r0_v1/theory.md)；新版本先做 existing-H flat slot/action 共设计，不是直接重启本文 pilot。

## 1. R0 结论

原先宽泛的“入口发现与轻量路由联合设计”**不能直接进入实现，也不能继续表述为高原创性候选**。新增一手材料核查表明，以下结构已有直接前作：

- 在其 adaptive-entry 组件中，保持 NSG 不变、构建小规模真实 base-ID 入口池并按 query 选单入口：Oguri–Matsui 2023/2024；其 2023 完整系统另含 PCA 与 database subsampling，本处不把整套系统等同于冻结图入口法；
- 迭代生成能补足当前 learned portfolio 的新候选并重拟合 selector：Hydra 2010；
- 容量上界 `|P|≤κ` 的 portfolio、oracle coverage 选池、实例 selector 及其端到端泛化分析：Balcan–Sandholm–Vitercik 2021；该工作不是 selector-aware 联合换池算法；
- 小规模真实 hub 集合加 learned query-aware 导航：GATE；学习式分区、复制与动态 probing 共同设计：LIRA。

因此，当前只能条件性保留一个更窄的经验问题：

> 在 base、raw-IP、冻结 NSG 和原生 single-entry kernel 都不变时，固定候选母集 `C`、部署池容量 `m`、轻路由函数类 `F` 和真实标签预算；按 `Q_fit` 交叉折上**实际 routed Recall**接受 H 外真实入口的一换一交换，能否通过一次冻结的历史-development gate，并优于同预算的 oracle-coverage／oracle-marginal 选池与旧 H 控制？

这仍不是已建立的论文贡献。列生成、交换、交叉拟合和效用分解本身均不新；ANN 特有的新可计算准则或可证性质才可能支持算法贡献。可靠的跨 workload 增益至多先支持范围严格的实证／系统贡献，不能单独补足算法原创性。

用户决定前的R0评估结论为：

```text
CONDITIONAL_READY_FOR_BOUNDED_MECHANISM_PILOT
NOT_READY_FOR_NOVELTY_CLAIM
AWAITING_USER_DECISION
```

用户于2026-09-09选择不投入该窄化pilot并转向方向A，最终状态记为`CLOSED_AT_R0_NOVELTY_COLLISION_UNRUN`。关闭理由是论文原创性碰撞下的研究优先级取舍；没有运行数据，不能解释为机制或性能已被实验否证。

## 2. 已确认事实与未确认假设

### 已确认

1. 当前正式范围是 WebVid-2.5M 与 Yandex official first-10M，raw inner product、原冻结 NSG、K=10、L=64/128；H 分别为 815/821 个真实 base ID。
2. 最近 Fast 根因诊断只证明现有 H 内存在较大的 single-entry oracle 空间：GT1-basin 距全 H 最佳 single 仍差 4.80–13.07 pp，exact C8 仍损失 3.16–6.66 pp。它**没有证明 H 外入口必要**。
3. Fast prototype 分数与真实 single Recall 的平均 Spearman 仅约 0.011–0.024；这说明几何全排序代理弱，不等于任意轻量 query-only selector 都不可学习。
4. 固定 anchor、固定三个入口、C8 足够、独立 single 命中可相加等旧前提已经被诊断撤下。
5. 历史 sparse utility ranker、search-aware centroid、utility residual、BTG、GATE 本地适配均没有建立双数据集完整成本收益。重新换 MLP、用旧 H 做 cover 后接树、或统计失败轨迹频率都不能冒充新 B。
6. 只有完整匹配 `(query ID, real entry ID, L, K, base, metric, graph, kernel)` 的旧 utility cell 可以复用。最近全 H 缓存只有 WebVid 767 行、Yandex 768 行：各含512条历史pilot，其余255/256条是围绕前128条pilot选出的 nearest-fit 与 random-fit 辅助行并去重所得，不是同质随机样本；它们不能当20K新矩阵或最终审计。

### 尚待验证

1. 训练侧提出的任一 H 外候选，在隔离 query 上是否带来可复用的真实 single utility。
2. H 外候选即使不提高 `oracle_C`，是否能提供与 query 更稳定对齐、因而降低 restricted `F` 的选择损失。
3. selector-aware swap 是否在同一 `C/m/F/标签预算` 下优于 coverage-only 和 oracle-marginal 选池。
4. 质量若通过，完整 router+graph wall 是否仍形成相邻工作点上的 Recall–wall 改善。

## 3. 与最接近前作的逐项差异

| 前作/对照 | 已覆盖的机制 | 本候选仍需证明的差异 |
|---|---|---|
| Oguri–Matsui adaptive-entry component | 该组件不改 NSG；k-means 得到少量真实 base-ID 入口；query 选最近入口；完整 2023 系统还含 PCA/subsampling | 候选/交换由原生有限搜索 `u_L(q,e)` 与固定 `F` 的可实现收益决定，而非几何最近入口 |
| GATE | 先固定 HBKM hubs，再以图/查询监督学习导航表示 | 改变真实 hub ID 本身，并以 Recall@10/固定 L 的原 kernel utility 验收 |
| LIRA | query 预测 kNN 分区；模型共同决定复制和动态 probing | 单一冻结 NSG、无复制/区域索引；动作是真实 single entry ID |
| Hydra | 以候选与当前 learned portfolio 的逐实例理想化选择来配置新 solver，再重建可丢弃 solver 的 portfolio；不固定 `m` 或一换一 | 本文只能称 Hydra-inspired 固定容量适配；候选是图节点，交换须用 fit 内 routed utility 而不是 ideal portfolio max |
| Balcan 等 portfolio analysis | `|P|≤κ`；coverage greedy 选池后学习 selector，并分析端到端泛化 | 不能再把 cover、分解或“共同考虑”当创新；只检验 ANN 原生 utility 下的专门交换准则 |
| 本地 v4 效用树 | 旧 H 全效用监督、有限叶 query-only tree | B 必须允许 H 外动作，并证明其收益不是旧 H 压池/树容量变化造成 |

外部一手来源与固定作者代码入口列在 `../source_manifest.json`。本轮检索不是穷尽查新；“未找到完全同名方法”不构成首次性证明。

## 4. 唯一保留机制的数学对象

冻结数据集、L 和原 kernel，定义：

- `u_L(q,e)`：从真实 base ID `e` 单入口运行原 kernel 后的 Recall@10；
- `C = H ∪ E`：有界候选母集，`E` 必须含 H 外真实 base ID；
- `P ⊆ C, |P|=m`：部署入口池；
- `F`：固定容量、只读 raw query 的轻量路由类；
- `f_{P,-k}`：只用内部折 `k` 之外的数据、在动作池 P 上从头拟合的同一 F。

四折 routed objective 为：

```text
V(P) = (1/4) * sum_k mean_{q in fold_k} u_L(q, f_{P,-k}(q))
```

对 `e ∈ C\P`、`d ∈ P` 的选择器感知交换：

```text
Delta_route(e,d | P) = V(P - {d} + {e}) - V(P)
```

候选预筛可以使用 proposal/train 折上的 coverage 上界，但**接受交换只能看预先指定内部选择折上的实际 `Delta_route`**。外部 development audit 不参与候选生成、交换、轮数或超参数选择。

作为归因分解，对完整测量的固定 C：

```text
oracle_C - routed(P,F)
  = (oracle_C - oracle_P) + (oracle_P - routed(P,F))
```

这只是恒等分解。第一项为池覆盖损失，第二项为 restricted-F 选择损失；它不是新定理，也不给部署收益保证。

## 5. 必须并列的对照

同一 `C/m/F/标签预算` 的机制主比较至少包括：

1. `coverage_C`：标准 greedy oracle coverage 选 P，再从头拟合同一 F；
2. `oracle_marginal_C`：从 `coverage_C` 开始、最多四轮以 ideal `oracle_P` 严格增益做穷举一换一 hill-climb，再拟合 F；这是 Hydra-inspired 固定 m 适配，不是 Hydra 逐位复现；
3. `joint_C`：本文 selector-aware fixed-m swap；
4. `oldH_joint_m`：相同交换和 F，但动作禁止离开旧 H；
5. `frequency_m` 与三个预登记 seed 的 `random_m`；
6. `full_H_F`：完整旧 H 训练同一 F，仅作额外参考，不用池规模差异归因。

Oguri–Matsui 的 metric-compatible k-means real-ID 池和 GATE 的作者对齐适配，是任何论文级结果前必须补齐的外部强基线。Oguri 池必须同时报告其原最近入口 router 与换成同一 F 的版本，以拆开池和 selector 贡献。由于作者主设定与本项目 raw-IP/Yandex 不归一化合同并不相同，适配规则必须在运行前单独冻结；不能静默把 L2 k-means 改写成 cosine/IP 后仍称逐位复现，也不能把 GATE 的结构／训练预算变化混入同图机制归因。若某个适配无法遵守本项目冻结合同，应分列为外部系统比较并明确不可逐位对齐，而不是删除该基线。

Fast1、Fast3保留为当前系统参照，但它们的路由结构与动作数不同，不替代上述同容量机制对照。

## 6. 候选提议的边界

首轮最少工程风险的 proposal 是：只用隔离 `Q_prop` 的 exact GT10，按跨 query 出现频率提出 64 个 H 外真实 ID；排除 H、去重，频率同分按 base ID。其角色只是**有界候选生成器/控制**，不是论文贡献，也不能因为某 ID 高频就称其有实际搜索效用。

现有 trace artifact 只保存聚合搜索统计，没有 visited/evaluated 节点 ID。因此“从失败轨迹提出 H 外节点”需要新增受验收的 ID emitter；它同时接近 ACO/RFix/频率节点旧思路，不建议作为首轮默认。若以后研究，必须另立版本和同预算消融。

GT-frequency 的负结果只否决该冻结候选源与本次机制配置，不证明所有可能的 H 外节点无效；但本版本失败后不得在同一 audit 上追加轨迹、扩大 C 或换 F 再宣布通过。

## 7. 用户决定与未采用草案

### D1：是否继续投入 B（已决定）

原建议给出“运行一次严格有界机制pilot”与“因原创性碰撞在R0关闭”两个选项。用户选择后者：记录`CLOSED_AT_R0_NOVELTY_COLLISION_UNRUN`并转向A；这表示未投入，不是实验否证。

### D2：pilot 容量（未批准、不适用）

推荐默认：`m=32`、axis-aligned utility tree `depth=5, min_leaf=32`、每个 L 独立、最多四轮一换一交换。这样 F 最多 32 个叶动作，与 m 一致；失败后不加深、不扩 m、不增加轮数。

备选的 196,480-call 小测试只检查 GT-frequency H 外列在历史 767/768 行上的描述性空间，不能检验 restricted-F 联合机制，可能误杀“oracle 不增但更易路由”的候选。因此不推荐用它替代主 pilot。

### D3：首轮候选来源（未批准、不适用）

推荐默认：GT10-frequency-only，原因是 split 最干净、无需新增 trace instrumentation，且会把研究问题集中到 selector-aware swap；同时明确它不是贡献。若用户要求从首轮就覆盖更强候选生成，应先单独审定 Oguri metric 适配和 residual/trace emitter，调用与实现预算需重新冻结。

### D4：pilot 数据规模例外（未批准、不适用）

推荐默认：`Q_fit=2048`、`Q_audit=1024`。这是为低原创性排除实验设置的有界 screening pilot，**明确小于 `s-target.md` 当前要求的后20K拟合合同**；即使通过，也只能进入20K复验，不能声称完成当前完整训练合同。若不接受该例外，应按20K重新核算约70M级标签调用、wall和磁盘后再决定，不能沿用11.1M预算。

### D5：统计合同（未批准、不适用）

推荐默认：fit 内交换以10,000次固定seed的query-paired bootstrap作稳定性筛选，要求 OOF mean gain 至少 `+0.05 pp` 且普通单侧90% lower bound `>0`；它只是自适应训练启发式，不作推断。最终audit把三项主比较×两数据集×两L共12项作为一族，20,000次固定seed配对bootstrap，同时保存普通95%和Bonferroni-12全族95%区间；每项主比较的四点非加权mean至少`+0.10 pp`，每个数据集对每项主比较至少一个L的全族区间下界`>0`，且任一点mean不得低于`-0.10 pp`。具体seed和单位编码写入批准版protocol lock。

D2–D5现只保留为未采用设计记录，不构成批准。B保持关闭：不创建协议锁、不实现runner、不生成split/candidate/label，也不启动搜索。若以后用户明确重开，应建立新版本、重新核查来源与本地身份并重新批准全部执行选择；本版本不能写成实验`NO_GO`。
