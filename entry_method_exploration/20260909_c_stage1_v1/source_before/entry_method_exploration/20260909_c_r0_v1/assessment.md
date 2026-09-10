# 方案 C R0：价值、前作、状态机与 A+B 边界

> 版本：`20260909_c_r0_v1`  
> 状态：`R0_CONDITIONAL_DIAGNOSTIC_DESIGN_ONLY_UNRUN`  
> 范围：只读调研与设计；未实现、未训练、未运行。

## 1. 结论先行

方案 C 值得保留，但只值得保留为一次成本受控、可以很早否决的机制实验，不应升为当前主线：

| 维度 | 当前判断 | 依据 |
|---|---|---|
| 研究问题 | 有价值 | A+B 只在搜索开始前读 query；C 检验真实搜索进展是否揭示可纠正的剩余错误 |
| 本地正证据 | 间接、但真实 | E13 的早期 trace 改善失败检测；E15 的 finite-beam trace 相对拟合几何特征有增量信息 |
| 本地负证据 | 强但有范围限制 | E14 最终 v4 已用 paid trace、frontier、局部 topology 和 merged Recall/NDC 监督，在 WebVid 仍显著选错替代入口；该最终版本未扩展到 Yandex。E16 query-only Atlas 在双数据集未过统计门 |
| 尚缺的关键证据 | 全部未测 | 同一个完整 `S_t` 上有限 `inject` 动作的 oracle headroom，以及 state-conditioned selector 是否胜 query-only |
| 工程成本 | 高 | 当前 `search_new` 没有 pause/resume/clone/inject/Budget API；必须新建独立状态机版 kernel |
| 宽泛原创性 | 不成立 | 动态搜索、搜索中加 pivot、live state 控制与同状态继续均有直接前作 |
| 窄方法原创性 | 低到中、条件性 | 可能位于完整状态上的一次远端强制扩展、continue abstention、成对反事实动作值、共同预登记剩余 graph-NDC cap 和逐分支实际成本这一组合；查新并不穷尽 |
| 与 A+B | 可顺序连接，不自动协同 | A+B 是 `t=0` 初始策略，C 是搜索后的残差救援；只有两者各自通过且 `AB+C` 仍改善完整 frontier 才连接 |

机器决策记为：

```text
CONDITIONAL_GO_FOR_BOUNDED_SAME_STATE_DIAGNOSTIC
NO_GO_AS_DEPLOYABLE_METHOD_OR_AB_EXTENSION_YET
```

这里的 `GO` 只允许将来另行批准一份 C0/C1 协议，不是实现或实验许可。

## 2. C 真正研究什么

固定 dataset、base、raw-IP metric、冻结 NSG、原始 pool 容量 `L`、`K=10`、起始策略 `rho`、一个 checkpoint 规则 `tau`、剩余 graph-NDC 上限 `B` 和 GT-free 候选生成器 `G`。对未在 checkpoint 前自然结束的 query，定义完整状态：

```text
S_tau^rho(q) = {
  retset[0:L], num_ids, scheduler_cursor,
  visited, expanded,
  L, K, initial_entries,
  counters_and_online_history
}
```

首版动作空间最多五个动作：

```text
A(q,S_tau) = {continue}
             union {force_expand(e) : e in G(q), e is eligible}
|G(q)| <= 4
```

令 `T_B(S,a)` 表示从该状态执行动作后，在同一个额外 graph-NDC cap `B` 内按冻结语义继续。`B` 是共同上限，不保证各分支消耗相同：自然提前终止、重复节点和无效候选都会改变实际 NDC。因此下式首先是 common-cap 下的成对质量增量，而不是等成本 Pareto 结论：

```text
Delta_R(q,S,e;B)
  = Recall@10(T_B(S, force_expand(e)))
  - Recall@10(T_B(S, continue))
```

同时保留 `Delta_NDC`、branch 是否自然提前终止和纯 wall；不把它们预先压成一个会掩盖 Pareto 关系的单标量。GT 只在两个分支结束后计算标签，不能进入 `S`、候选、checkpoint 或线上控制器。

这不是以下对象：

- 不是从 `e` 独立完整重启，再与 probe 的 top-K 合并；
- 不是给初始入口训练另一个静态分类器；
- 不是把 `L` 当距离调用预算；`L` 仍是候选 pool 容量；
- 不是多步强化学习、动态改图或免费全 H 动作搜索；
- 不是用完整 suffix trace 预测同一 suffix；线上只能读 checkpoint 前已经发生的量。

方案的唯一待证机制可以拆成两项：

1. **状态信息价值：** `query + S_tau` 是否比同容量 `query-only` 更能决定 `continue/inject(e)`。
2. **状态复用价值：** 原位执行同一动作是否比丢弃状态后的 restart/merge 更好。

只证明其中一项，不能把另一项一并写成贡献。

## 3. 本地证据：为什么值得一个小 gate，也为什么不能乐观

### 3.1 支持继续问问题的信号

[历史 E13](../../experiment_history/05_probe_reroute.md)用只支付 `L10` 的 trace 识别“候选中是否存在至少 0.1 Recall 改善空间”：

| 数据集 | 静态 AUROC → 静态+trace | 静态 AP → 静态+trace |
|---|---:|---:|
| WebVid | `0.584258 → 0.659906` | `0.467514 → 0.557227` |
| Yandex | `0.619535 → 0.759084` | `0.336776 → 0.469471` |

这说明早期搜索行为携带“哪里可能需要救援”的增量信息，但完全没有回答该注入哪个入口。

[历史 E15](../../experiment_history/06_finite_beam_and_atlas.md)中，19 维真实 finite-beam trace 相对拟合 geometry ridge 的四个 `Delta U` 区间下界均为正；成本约束的 top-8 oracle 在 WebVid/Yandex、L64/L128 四点也都有正区间。它说明执行过程和候选空间均有诊断信号，但 trace 是候选完整搜索后才得到的 privileged teacher 信息，不是可部署的 checkpoint 特征。

### 3.2 必须正面承受的负证据

[历史 E14](../../experiment_history/05_probe_reroute.md)不是“只用几何标签”的弱基线。它已经：

- 支付 Fast3 `L10` probe；
- 在 Fast top-32 中预测另一个真实入口；
- 使用 query trace、frontier、候选亲和与一／二跳 topology；
- 以 probe 与 restart 搜索合并后的 Recall/NDC 连续效用监督，并对相对 restart 的正增益加权。

最终 v4 只在 WebVid 运行；Yandex 最终扩展因 WebVid gate 失败而未运行。WebVid top-risk 20% 的最强 `frontier + topology` chooser 在 L64/L128 相对完整 Fast 分别为：

```text
Recall: -3.371 pp / -1.416 pp
NDC:    +2.668%  / +1.036%
```

同一报告中的免费 alternate oracle 仅为 `+0.103/+1.286 pp` Recall。旧方法确实丢弃当前搜索态并重启，但“有 trace、预测相对收益、优化真实 merged utility”都已经做过；C 不能靠换一个模型名称绕过这条负证据。

[历史 E16](../../experiment_history/06_finite_beam_and_atlas.md)的 64-NN query-only utility Atlas 在四点虽有极小正均值，但全部效用区间跨 0。它只否决该具体压缩器，不证明所有 query-only 方案不可学；同时要求 C 必须显式证明 state 相对同容量 query-only 的增量。

### 3.3 不能搬用的 headroom

E20 的“全 H 最佳独立 single 比 Fast1 高 `4.80–13.07 pp`”不是 C 的 oracle 上界。进入 `S_tau` 后，visited、pool 截断、已扩展集合和剩余工作会改变入口的边际价值；静态 `u_L(q,e)` 排名可能反转或变成 no-op。C 必须重新生成 `Delta_R(q,S,e;B)`，不得复用 A+B 或 E20 的 single-entry 矩阵充当标签。

## 4. 近期与历史前作：宽泛叙事已经相撞

本轮限定检索没有找到与 C 的全部窄条件完全相同的方法，但以下一手工作已经覆盖其大部分宽泛部件。本文为便于内部索引将第一篇工作简称为 QING；原论文没有把它写成正式缩写：

| 前作 | 已覆盖的机制 | C 仍需证明的窄差别 |
|---|---|---|
| [Query-driven Iterated Neighborhood Graph Search，2012（作者 PDF）](https://jingdongwang2017.github.io/Pubs/ACMMM12-GraphSearch.pdf)及[研究页](https://www.microsoft.com/en-us/research/publication/query-driven-iterated-neighborhood-graph-search-for-scalable-visual-indexing/) | 根据 query 与 search history 检测局部停滞，从树生成新 pivot；算法在原 priority queue、result heap 和 visited/color 历史中加入 pivot 再继续 | 不是“首次搜索中补入口”；差别只能是单 checkpoint、有限远端动作、显式 `continue`、成对 counterfactual value、共同剩余 cap 与逐分支实际成本记录 |
| [ANNiE，PVLDB 2026](https://www.vldb.org/pvldb/vol19/p3820-wang.pdf)及[作者代码](https://github.com/CaucherWang/ANNiE) | 在同一 live greedy search 中自适应检测 homing→refining，一次调用 GBDT 预测总 NDC，并继续原 pq/visited/heaps | 已覆盖一次 state-conditioned checkpoint 和同状态继续；不选远端 entry，不做 inject/force-expand 或 continue-vs-inject 标签 |
| [LAET，SIGMOD 2020](https://www.pdl.cmu.edu/PDL-FTP/BigLearning/mod0246-liA.pdf) | 固定搜索检查点读取 query/start/中间距离特征，预测所需总工作并恢复当前搜索 | 动作仍是停止预算，而不是远端入口干预 |
| [DARTH，SIGMOD 2026](https://arxiv.org/abs/2505.19001) | 从运行中状态周期性预测当前 Recall，动态决定停止或继续 | state/adaptive control 已知；动作集合和监督目标不同 |
| [Ada-ef，SIGMOD 2026](https://arxiv.org/html/2512.06636) | 从一次 live HNSW 的早期距离估计 query-specific ef，截断现有集合并继续 | 调 beam/终止，不注入远端动作 |
| [Learning to Route in Similarity Graphs，ICML 2019](https://proceedings.mlr.press/v97/baranchuk19a.html) | 学习 query-node 路由分数并在搜索每步选择已有候选扩展，缓解局部最优 | 已覆盖 learned within-search routing；不做一次远端 entry/abstention 的状态反事实 |
| [SHEAF，2026-07 预印本](https://arxiv.org/html/2607.12229v1) | 两次浅 probe 的 answer-set flux 预测每 query beam；讨论但未实现 warm-start | probe 本身是两次独立搜索，不是原位入口干预；其 flux bound 只约束两个 probe 结果间的 Recall 变化 |
| [GATE，KDD 2025](https://arxiv.org/abs/2506.15986) | 在 base-graph traversal 前用 query-aware 表示选择真实 hub | 只选初始入口；不读取 live state 或预测剩余动作价值 |
| [NGFix/RFix，SIGMOD 2026](https://arxiv.org/html/2510.22316) | 用历史／在线查询识别 OOD hard region 并修改图边，使后续查询受益 | 在查询之间改图；不是当前 query 的同状态一次干预，且 C 冻结原图 |

因此不能声称：首次自适应图搜索、首次搜索历史驱动 pivot、首次 learned checkpoint、首次同状态恢复、首次 learned routing、首次多入口或首次 OOD 修复。可以谨慎保留的候选贡献单位是：

> **在可等价恢复的完整 NSG finite-beam 状态上，以固定剩余 graph-NDC cap 和有限 GT-free 候选，学习一次带 abstention 的 `continue`／远端 `force-expand` 成对边际价值，并将自然插入、restart/merge 和 continuation-only 控制置于同一个原生 runner。**

这是定向而非穷尽查新；在完成更广查新、作者实现级核对和端到端实验前，不使用“首个”表述。

## 5. 当前代码为什么不能直接做 C

当前实现可提供一些材料，但没有可恢复状态 API：

- [`Neighbor`](../../ACSG/ACSG.h)含 `id/distance/flag`；`flag`只表示仍留在 retset 中的候选是否待扩展。
- [`SearchTrace`](../../ACSG/ACSG.h)明确是 diagnostic-only 汇总，并写明不含 routing state；其中 GT 字段更不能整体交给线上模型。
- [`search_new`](../../ACSG/ACSG.cpp)的外部 `retset_buf`只省去重复分配；每次调用仍 `resize(L+1)` 并全部重置。
- `num_ids`、调度游标 `k`、`updated_pos`、当前 stagnation 和循环终态全在调用栈内；函数一次跑到底。
- `VisitedTable`每节点一字节，只表示距离曾经被计算，不能区分“已扩展”“已评分待扩展”“已评分但被 pool 淘汰”。
- 当前没有 checkpoint、step、pause、resume、clone、inject 或 remaining-NDC cap；`search_L`还是共享对象成员，而非独立 state 字段。

因此 C 不是给现有接口加一个 callback。若将来获批，必须新增并版本化一个独立 `SearchState`／state-machine kernel，保留原 `search_new` 作为不可回归的基线。

### 5.1 最小可恢复状态

```text
identity:
  base / graph / metric / kernel SHA
  query identity, L, K, initial entry IDs

scheduler:
  retset[0:L] = {id, distance, pending_flag}
  num_ids, next cursor k

membership:
  visited snapshot/overlay
  expanded-ID set

budgeted execution:
  completed-expansion checkpoint marker
  consumed and remaining graph NDC
  current node / neighbor offset / updated_pos when a cap cuts a row

GT-free online history, if used:
  expansion/accept/reject/rewind/stagnation counters
  bounded distance or result-change window
```

`visited`与`expanded`必须分开；被 pool 淘汰的待扩展点只靠现有 `flag` 无法恢复。每个分支要有独立 `DistanceComputer` 并绑定同一 raw query；图和 base 可以只读共享。

checkpoint 首版只允许出现在一次完整邻接扩展结束后。若 `B` 在后续邻接扫描中耗尽，必须预先定义：在下一次 `dis(id)` 前停止、未实际计算的节点不标 visited、保存 neighbor offset，并从当前合法 retset 返回 top-K。不得按结果临时切换为“整行原子扩展”。

### 5.2 clone 成本不是小细节

正式 base 下，一份当前 `VisitedTable`约为 WebVid 2.5 MB、Yandex 10 MB。若 20K query、两个 L、`continue + 4 inject` 五支都朴素深拷贝，仅 visited 的复制流量约为 `0.50 TB / 2.0 TB`；这是设计量，不是实测时间。线上只执行一个动作，无需五支 clone，但仍要支付 state bookkeeping。

标签生成应优先考虑不可变前缀加 branch overlay、touched-ID rollback log 或复用 table 后重放稀疏 visited IDs；无论选哪一种，都要先过字节／顺序等价验收，不能以优化为由改变搜索语义。

## 6. 首版动作与成本合同

为正面承受 E14，独立 C 首测应冻结一套 paired Fast3 起始策略；不同时改变初始路由。最多四个候选由一个冻结 query-only 生成器在 audit GT 不可见时给出，真实 ID 合法且去重。首版只让 checkpoint 时**尚未 visited**的入口成为有效动作，其他候选映射为 no-op 并计入覆盖统计。

`force_expand(e)`固定为：

1. 支付一次 `dis(e)`，随后标 visited；
2. 按原距离和 pool bound 尝试把 `e` 插入当前 retset；
3. 无论 `e` 是否留在 pool，只扫描其邻接行一次；
4. 合法未访问邻居按原 visited、距离、插入、pool 截断和 rewind 规则处理；
5. 强制扩展及其实际邻居距离全部扣 `B`，然后回到原调度器；
6. 同一个 `e`永不重复扩展。

“只按原距离自然插入、不保证扩展”作为固定机制控制。若它与 force-expand 同样有效，应选更简单语义；不能先看结果再把主动作互换。

当前图 `R=64`，一次动作最多引入 `1+64=65` 次距离计算；重复／padding 会降低实际数。若 `B<65`，首版不开放该动作，避免主要语义被邻接行截断支配。实际 NDC 即使在相同 cap 下也可能因自然终止不同，必须逐 branch 保存；最终还要测 wall。

在 checkpoint 前自然结束的 query 直接返回原结果，记为 `early_finished`。无合法候选、候选已 visited 或分支无变化也保留在**全体 query 无条件均值**中，增益记零；survivor 条件结果只能辅助解释，不能作为方法主结论。

## 7. 最小阶段与停止条件

### C0：协议锁，未授权

先另立批准版 protocol，冻结：起始 Fast 版本、每个 L 的唯一 checkpoint、`B`、最多四个候选及生成成本、force/natural 语义、partial-row 规则、split、统计族、资源上限、artifact schema 和停止条件。本 R0 不替代该 protocol。

### C1：state-machine parity

必须全部通过：

- 不设 cap、不注入时，`pause → serialize/clone → resume` 与原 `search_new` 的 top-K IDs、distances、NDC 和 expansion 顺序一致；
- 同一 `clone(S)`重复 continue 完全确定，各分支无 visited/retset 污染；
- plain、count、trace 结果一致，计数和 pure-wall 分离；
- 非法／重复入口、已 visited、立即被 pool 拒绝、distance tie、rewind、B 恰在邻接行耗尽和自然提前终止均有单元例；
- state 保存的 L 与调用身份一致，不受共享 `search_L` 并发改变。

任一项失败只记工程未通过，停止质量解释。

### C2：同状态有限动作 oracle

冻结后只运行 `continue`、natural insert、最多四个 force-expand 分支和有限动作 oracle。所有 query—including early-finished/no-eligible—进入无条件统计。

进入学习前应预注册实质门。与项目现有开发门一致的建议起点是：四个 dataset×L 点上，有限动作 oracle 相对 continue 的无条件平均 Recall 均至少 `+0.5 pp`、主比较族校正区间下端均大于 0，并且在实际 NDC envelope 内有非零动作覆盖。C2 只证明共同 cap 下是否存在有限动作 headroom；它不证明 branch 等成本，也不构成 Pareto GO。最终部署标准仍更高；本数值只是下一版协议需由用户确认的建议，不是已批准门槛。

以下任一出现即停止当前 C：无条件 oracle 空间消失；收益只在筛后的 survivor 中出现；只有全 H/GT 候选、多个 checkpoint 或多步 RL 才有空间；收益来自看结果后改变动作或 `B`。

### C3：状态信息 × 状态复用的机制析因

在相同 prefix、候选、工作 cap、模型容量和 split 下做：

| 决策输入 \ 执行方式 | 丢弃状态 restart + merge | 原位共享状态 |
|---|---:|---:|
| query-only | Q/R | Q/I |
| query + checkpoint state | S/R | S/I，即 C |

另加 native continue、always-inject、natural-insert、continuation-only 状态控制器及各动作空间 oracle。这个 2×2 分别回答：

```text
状态信息增量 = S/I - Q/I
状态复用增量 = S/I - S/R
```

交互量只作描述，不能替代逐格对照。C 至少要在四个点上胜 continue 与同容量 query-only，且原位执行胜公平 restart/merge；learned policy 还应保留预注册比例的 finite-action oracle headroom，干预率不能为零。任何一项失败，停止当前动作／表示，不扩全 H chooser、不堆模型、不进入多步 RL。

### C4：独立完整 wall

只有 C3 通过，才测 candidate generation、state maintenance、feature summary、controller、injection 和 graph suffix 的独立整批 wall；方法顺序轮换，routing/graph/total 与 count/plain 分列。最终仍执行项目统一标准：双数据集至少两个相邻点上，同 Recall QPS `>=+10%` 或同 QPS Recall `>=+1 pp`，并有校正区间支持。随后才可能申请三独立构建与冻结后的 held-out；同 L Recall、等 graph NDC 或 count-mode QPS 都不是 Pareto GO。

## 8. 与 A+B：唯一自然接口是“先起跑，后救援”

A+B 与 C 的时间位置不同：

```text
q
  -> frozen A+B: 选择 t=0 的真实入口 e0，并产生固定 shortlist
  -> 原 NSG 执行到 checkpoint，得到 S_tau
  -> C: continue 或 force_expand(一个仍未访问的候选)
  -> 保持同一状态完成 suffix
```

这是一种自然的模块接口，但不是先验协同。A+B 优化的是独立起跑效用 `u_L(q,e)`；C 优化的是条件边际 `Delta_R(q,S,e;B)`。更好的初始入口可能让 C 的 headroom 消失，也可能把剩余 query 变成更难、更偏的尾部。

### 8.1 候选怎样从 A+B 输出

若 A+B 将来独立通过 exact、micro-index 和 full-wall gate，可冻结其部署版：

1. top-1 真实 ID 作为初始入口；
2. 固定取 `k_slot` 个 slot，按分数顺序经 `pi(slot)`映射成真实 ID；
3. 去掉初始 ID 与重复 ID，最多交给 C 四个；
4. 候选不足就保留更少动作，由 continue 补齐，不持续扩大扫描直到凑够四个。

A+B 的 `pi`允许 many-to-one，top slots 可能映射成同一入口；因此必须“固定 slot 工作量后映射去重”。持续 oversample 会造成每 query 可变路由成本。Micro-HNSW 的 top-a slot 也不等于按 `max_{j:pi(j)=e} s_j`精确排好真实 entry，必须另验 exact→micro shortlist identity 和召回。

这些 runner-up 分数描述初始动作，不保证是当前 state 的互补救援入口。首个联动实验要把 A+B shortlist 当作廉价候选生成器／控制，而不能称为已学会 conditional complementarity。

### 8.2 起始策略改变后必须重标

```text
P(S_tau | Fast3) != P(S_tau | deployed A+B)
```

exact A+B 与最终 micro A+B 也可能产生不同初始 ID 和状态分布。正确顺序是先冻结包括近似路由在内的部署 A+B，再在它实际诱导的 prefix 上 cross-fit 生成 C 标签。Fast-C 模型、exact-AB-C 模型、旧 `u_L` 矩阵或 E14 标签都不能直接迁移。

### 8.3 只有两边独立通过后才做联动 2×2

| 初始策略 | 无 C | 有按该策略状态重训的 C |
|---|---:|---:|
| paired Fast | Fast | Fast + C_Fast |
| frozen deployed A+B | AB | AB + C_AB |

在匹配的成本工作点可报告：

```text
I = (J_AB+C - J_AB) - (J_Fast+C - J_Fast)
```

QPS 是二维 frontier，不能直接做代数相减。`AB+C`胜 AB 且整体 Pareto 改善，就可以作为模块组合采用；只有 `I` 的预注册区间稳定为正且 joint 胜 AB、Fast+C 时，才称“协同／两时间尺度联合策略”。`I≈0`但组合最好，只能称可叠加；`I<0`说明两者偏替代，不应强写联动。

### 8.4 明确不联动的情形

任一条件成立，就保持 C 独立或关闭：

- A+B 自身 exact、micro 或 full-wall gate 未通过；
- A+B 状态上的有限动作 oracle 没有剩余 headroom；
- state-conditioned 不胜 query-only，或原位不胜 restart/merge；
- shortlist 多数重复、已 visited，或与当前 frontier 同一局部区域；
- 只有全 H 扫描、GT、未来 suffix、免费候选距离或可变候选数才有增益；
- 无法支付 deployed A+B 上的 on-policy/cross-fit 重标；
- state、top-a、controller 与动作的完整 wall 抹掉 Recall–QPS 收益。

如果 C 在 Fast 上有效、在 A+B 后失效，C 仍可作为独立 Fast 救援方向，但不并入 A+B；如果 A+B 失败而 C 成功，则保留 Fast+C，不让 C 充当挽救 A+B 叙事的工具。

## 9. 当前决定与下一步边界

当前 A+B 仍是较低在线风险的主方向。C 不再被逻辑上写成“只有 A+B 失败才有意义”，因为它研究的是不同时间点的真实状态；但资源排期仍应先让 A+B 作出协议／首门决定，避免同时修改静态 router 和搜索 kernel。

若用户未来单独批准 C，下一交付不是 learner，而是一份 C0 协议与最小 state-machine parity 实现计划。只有 C1 parity 和 C2 finite-action oracle 都通过，才值得训练；只有 C3 证明状态信息与状态复用两个主效应，才值得计时；只有 C4 Pareto 通过，才讨论与冻结 A+B 的联动。

本轮没有执行以上任何阶段。
