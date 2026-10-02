# 成本目标与历史重复复核

2026-09-20。只读历史核查和理论修正；0 新标签、训练、ANN、NSG、GT、构图或性能评测。保留原提案正文，纠正其研究定位，不修改项目默认或已封存实验。

## 1. 结论

原提案以 Recall 为学习目标、把 QPS 留在最终约束中，这只给出质量侧的条件分析，不能作为完整 Recall–QPS 改进方法。需要同时处理真实搜索质量和完整耗时；简单加入 NDC 惩罚也不是新方法或 QPS 保证。

原提案虽然列出 E85，却未准确展开其“query 单位方向、固定岭回归、真实命中残差、线性分数阈值切换”的直接重合；同时漏列了 20260908_v2 的完整三入口联合岭回归设计。因此撤回“本版值得作为下一优先实验”的定位，保留为尚无充分依据的结构变体。未发现已执行版本与“固定全局 64 个三元组、每个动作一个 query 线性回归器”完全一致，不等于它已有新颖性或成功依据。

## 2. 为什么学习耗时，而不是逐 query 的 QPS

按项目单线程、串行、完整搜索 wall 的口径，对 N 条查询：

`QPS = N / T_batch = 1 / mean_query_time`。

mean_query_time 指把同一批完整在线总时间分摊到查询后的均值。直接平均 `1 / t_i` 不等于整体 QPS，也不能作为等价训练目标。单条延迟易受缓存和系统波动影响，需要受控重复测量；这些困难不是忽略成本目标的理由。

应分别建模实际 Recall 和完整路径成本，再求例如：

`min_pi E[T_pi(q)] subject to E[R_pi(q)] >= r_target`。

也可固定总时间预算最大化 Recall。K1、K100 分别定义目标；改变 L 后标签和结论范围重新说明。在原 L 上同时改善是一种充分局部证据，完整曲线是否改善仍要看相同 Recall 下的完整 wall。

这里 T 包括 query 预处理、动作评分、条件性旧路由、ID 映射、NSG 和正常输出，不含 GT 评分、文件装载、诊断计数、hash 或日志。若没有重新验证可加性/缓存影响，分项估计不能直接冒充完整部署耗时。

对本原提案，令 c(q) 为新评分器成本，T_path(q,a) 为选定动作后的实际路径成本，原方法为 T0(q)。动作 0 的路径就是原 GT10：

`T_new(q) - T0(q) = c(q) + [T_path(q,pi(q)) - T0(q)]`。

因此回退到动作 0 时仍多支付 c(q)，不能把回退当作速度不退化证书。选择固定三元组时可能省掉旧路由，但主搜索可更慢，二者都须进入成本标签或经验证的成本模型。

若用拉格朗日分数 `Delta_R - lambda * Delta_T` 辅助决策，lambda 的单位和取值必须服从明确的时间/Recall 约束。正的标量收益可由一个指标的改善掩盖另一个指标的退化，不代表两个指标分别通过。当前提案尚未提供完整耗时标签或经验证的时间预测器，也没有可支持 QPS 提升的实验结果。

## 3. 已执行或已设计的直接前件

### E85：最接近原提案的简单残差评分器，已执行离线拟合

- 输入 `x=q/||q||`，目标 `y=hits_compact-hits_P`，含所有零差。
- 固定岭系数 `1/d`，训练截距，求线性代数解；`x beta+b >= 0` 选 compact，否则原 P。
- 每集 3976 fit、3976 accept。两集主模型及置换控制共 4 次拟合；线上原生模块未实现、没有 QPS。
- 原始 paired.csv：Web accept 相对 P 为 -35 个净命中（Recall@10 -0.088028 pp）、失败 +3；Y 相对 P 为 +24（+0.060362 pp），但相对 compact 为 -57（-0.143360 pp）、失败 +5。两集 gate 均 false。
- 这与原提案的简单评分、残差目标和阈值回退高度重合。差别在动作域：E85 选两套完整路由策略，本提案拟选全局固定三元组；该差别还没有化解泛化失败的证据。

原证据：[协议](../20260913_until2100_v1/stage26_query_gate_feasibility_v1/protocol.md)、[训练源码](../20260913_until2100_v1/stage26_query_gate_feasibility_v1/src/train.py)、[配对 CSV](../20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/paired.csv)、[接受门](../20260913_until2100_v1/stage26_query_gate_feasibility_v1/results/gate.json)。

### 20260908_v2：完整三入口联合岭回归，已设计但未执行

固定 anchor 的 C8 中 21 个完整三入口动作；40 维单项/成对特征、固定 ridge；目标为相对 Fast3 的实际联合 Recall 增量减归一化 graph NDC 增量；精确比较动作，正预测才替换。state 明确 `method_implemented=false`、`new_experiments_run=false`。

因此不能说“完整动作 + 岭回归 + 残差 + 回退”此前未想过，也不能把这个未执行草案说成已验证失败。它与本提案的差别主要是 query 相关短名单/共享特征模型，对比全局固定动作库/每动作独立线性分数。

原证据：[推荐设计](../../entry_selection_research/20260908_v2/recommendation.md)、[状态](../../entry_selection_research/20260908_v2/state.json)。

### 早期 sparse utility ranker：简单内积评分与成本感知监督，已执行

query–prototype/raw-hub 加权内积，加入口/rank bias，在 Fast top32 内重排。原训练源码 targets 使用 `mean Recall - 0.05 * mean(NDC/Fast3_NDC)`，listwise soft target，不是仅学 Recall。Web 有窄范围正值，Y 未形成稳定成本收益；旧结果未包含新路由完整 QPS。

原证据：[训练源码](../../benches/run/train_sparse_utility_ranker.py)、[原分析](../../sparse_utility_ranker_results/analysis.md)、[详细复盘](../../experiment_history/04_utility_and_representation.md)。原分析最后的旧下一步建议不是当前运行队列。

### E36：真实完整三入口 + 质量/工作量奖励，已训练部署

原奖励为 `hits(S)-hits(S0)-0.1*(totalNDC(S)/totalNDC(S0)-1)`；使用非加性集合 MLP，对当前 top8 的 56 个三元组评分，至多三步交换。这里 Exact 是同策略的精确期望梯度训练对照，不是简单线性评分器，不能因名称混淆。

audit512、L128、历史 K10 的完整五轮 wall：Web 所选 RL 相对原 top3 的 Recall -0.46875 pp / QPS -9.3216%，Y +0.390625 pp / -8.2962%；总 NDC 仅 +0.3876% / +0.2832%。成本代理没有覆盖全部特征/评分/选择费用。此结果是当前候选表示和实现的证据，不是所有成本感知学习无效的证明。

原证据：[协议](../20260911_query_swap_policy_v1/protocol.md)、[训练](../20260911_query_swap_policy_v1/src/train.py)、[结果 CSV](../20260911_query_swap_policy_v1/results/points.csv)、[独立奖励核验源码](../20260911_query_swap_policy_v1/src/final_audit.py)。

E28 的共享线性/free 画像、E104 的 QLinear/WFree 也已经检验简单画像/线性评分路径；这些是单 hub 分数再选 top3，不能直接说等同固定完整动作。但它们足以排除“评分器简单”本身构成新增机制或成功依据。详情仍见原提案中的来源。

## 4. 对原理论论证的具体修正

对同一 query，`Delta_R(q,a)-Delta_R(q,b)=R(q,a)-R(q,b)`。减去共同基线不改变真实动作间的排序，也不增加信息；它有利于表达改动收益和回退，但不是独立解决可学习性的机制。

原提案的表示反例、经验次模覆盖和 `F-2Eepsilon-tau` 质量界保留其条件范围。它们没有证明当前两集的 F 足够大、epsilon 足够小，也没有证明完整耗时下降。将奖励改成 Recall–time 组合亦不会自动补齐这些条件。

后续理论应先解释实际 joint 收益为何具有可跨 query 共享的结构、可用表示为什么能预测这种结构，以及选中的动作为何能节省完整时间。不能只把旧 ridge 改成 64 个输出，或把 NDC 换名 QPS，就称为有实质改进依据的新路线。本次不据此安排新的标签或超参实验。
