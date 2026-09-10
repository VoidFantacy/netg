# P2 既有证据的解释与下一行动

本清单在性能结果出来前制定；不包含 GO/NO-GO 结论、不改变 gate，也不启动新实验。只重算已有 count、trace、model/labels 产物。`geom_probability/oracle_probability` 对应协议中的 weighted。适用于“oracle 路由有潜力，但区域保护收益弱或负”的分流。

## 先确认能比较什么

- 按 dataset、query ID、L、K、graph/model/Fast checksum 对齐；count/plain 结果一致后才解释。`geom_unified↔geom_uniform↔geom_probability`、`oracle_unified↔oracle_probability` 必须具有相同完整 route，包括入口顺序、默认种子、anchor、区域与权重。
- 分开列 `oracle_unified−geom_unified`（区域选择及对应门户、顺序和去重后种子数变化）、两组 regional−unified（区域队列整体策略）、`geom_probability−geom_uniform`（容量分配及随容量变化的调度）。统一池和区域池同时改变保留与扩展顺序；当前五项对照不能证明“仅候选保护”的单因素因果。
- 10K aligned count 描述 pilot 分布；预选小样本 trace 只提供具体路径证据，不能估计全体发生率。5 timing rounds 不增加独立 Recall 样本；oracle 不进入部署 frontier。若只有 count/trace/model，不能给 QPS、等 wall 收益或部署判断。

## 四类诊断

| 问题 | 只用已有证据的可证伪检查 | 可支持的判断与下一行动 | 不能推出 |
| --- | --- | --- | --- |
| 区域选择或权重是否失配 | 对 count 的 geometric/oracle `regions` 比较 top4 集合、顺序；计算 oracle **所选 top4 内**被 geometric 同时选中的条件权重和，并与 `oracle_unified−geom_unified` 的逐 query 差值配对。重建所有 query 的实际整数容量，比较 probability/uniform；相同 route 且容量完全相同时，二者结果应一致，否则返回实现审计。 | 区域失配与 oracle 优势一致，仅支持当前画像存在预测缺口；若容量几乎不变，说明当前概率分配没有形成充分不同的机制，不能称其更优。先做这些已有数组的交叉表，检查两个 L、两个数据集是否同向。 | oracle weights 已在 top4 内归一化，未输出其原始总质量；不能恢复 pilot 绝对 GT 区域覆盖率或未选区域分布。`model.fit_top4_oracle_target_mass` 不能代替 pilot；跨区域边可访问，区域质量也不是搜索 Recall 上界。集合差异受等质量区域 tie 影响，不能都算错误。 |
| 固定门户是否不够好 | 从 model 核对每区两门户及其 fit 频次选择规则/fallback（未输出逐门户实际频次）；从 trace 核对它们实际成为去重种子、是否扩展。沿 `discover.parent` 回溯已发现目标到 portal/Fast-anchor/default 根，比较 oracle 下两种池的发现树。 | 若同一门户在任一同图对照到达目标，已证明该门户存在一条实际可走路径。大量收益依赖 anchor、门户被早期淘汰等只是定位线索；先报告逐种子发现树和未扩展原因，避免把队列阻塞错判为门户质量。 | first-discovery 根不是门户边际贡献；共享 visited、种子顺序和后续调度均会改变归属。“未发现目标”不能证明门户无效。当前没有换门户且保持其他因素固定的对照，因此门户优劣只能记假设。 |
| 候选竞争是否解释损益 | 用 `analyze_traces.py` 重建队列容量、accept/reject/evict/expand。对同 route 的 rescued/newly-harmed **返回 GT ID**，回溯赢方首次发现路径，查输方哪些已发现祖先被拒绝或在扩展前淘汰；同时核对反向 harm 证据、共享池/区域池实际容量与额外扩展/NDC。 | 存在“赢方扩展、输方未扩展”的非终点祖先支持候选竞争解释；两种方向都必须列出。结合完整 10K 比较判断新增保留/扩展是否带来收益；若全体比较无机制收益且 trace 无支持，按计划关闭保护分支，不能借 oracle 路由优势自动让保护机制通过。 | GT 节点本身被拒绝/淘汰不等于 Recall 损失：其距离已进入独立 global top-K。首次发现树的祖先不是唯一必要桥，不能排除未记录的替代路径；证据不能单独分离保留与调度因果。 |
| 是否真是图连接瓶颈 | 查同图、同门户的另一池或 L128 是否已到达 L64 漏掉的目标，及其跨区域首次发现路径。若已有路径，反驳该目标“结构上不可达”的解释；若两者均没发现，记录为未识别原因。 | 现有路径可把特定失败收窄到有限预算搜索/队列过程。对未发现目标，保持“门户/预算/调度/连接尚未分离”；仅据当前 count/trace/model 不触发辅助图。 | trace 只记录首次发现边，不包含全部邻接、已 visited 边和未发现 GT 的 ID/位置；少见跨区发现、低 Recall 或 oracle 失败都不能证明缺边、断连或必须加边。全图 cut fraction 也不是 query 可达性证明。 |

## 有界分流

1. 先做上表的**已有证据重算**；缺字段就记 `NOT_IDENTIFIABLE_FROM_SAVED_EVIDENCE`，不把缺失解释补成事实，不为此读取 held-out。
2. 只有实际支持“oracle 潜力且预测/门户瓶颈可定位”，才按原计划讨论最多一次表示或划分修订；本版本总计仍最多两次有新证据的机制修订。修订前只写一个假设、一个保持图/预算/fit 隔离的对照和否证条件；不得同时改画像、门户、分区、容量，使变化无法归因。先证明该修订针对观测缺口；没有定位证据则停在诊断，不自动增加模型。
3. 队列机制收益与路由收益分别汇报。仅一数据集有效须解释适用条件；oracle 也无潜力则停止当前配置。P5/P6 的实质性能门槛仍独立执行，P2 oracle 潜力不替代它们。截止后只整理现有证据，不再补实验。

实现依据：[protocol.json](../protocol.json)、[build_p2_model.py](build_p2_model.py)、[run_p2_evaluation.py](run_p2_evaluation.py)、[analyze_traces.py](analyze_traces.py)、项目 `benches/bench_hierarchical_eval.cpp` 的 `select_regions/route_online` 与 trace 输出。
