# Finite-beam reachability 与局部 utility Atlas 历史

本页归档真实有限 beam 轨迹诊断 v1、纠正其终止原因的 v1_audit，以及 query-only 局部 utility Atlas v2。整理于 2026-09-08；只读取既有报告、设计、配置与源码，不执行实验。本页尤其保留“trace 有增量信息”“这些信息是否足够便宜”“能否压缩为 query-only 决策”三个不同命题。当前活动计划仍以根目录 `s-target.md` 为准；旧 [finite_beam_reachability_goal.md](../finite_beam_reachability_goal.md) 是该阶段任务记录。

## 1. 为什么从 BTG 转向有限 beam 轨迹

BTG 对原始图的 basin connectivity 做扩散，但实际搜索会限制候选池容量、去重已访问节点、拒绝超过 pool bound 的节点，并根据新插入位置 rewind。两个入口即使在无限制图上连通，也未必能在给定 L、相同距离计算预算下到达目标。因此本阶段首先做诊断：在原始几何分数之外，**真正执行后的有限 beam 事件**是否解释入口效用差异？如果有，还需单独验证它们能否被压缩为不支付多入口搜索的路由信息。

这里的 candidate 是固定 Fast geometry top-8，测试每个候选的单入口搜索；不能把结果扩展为全 base 的入口空间，或未经测试的最优多入口组合。

## 2. v1：对真实 `search_new` 计数与轨迹语义做校验

### 执行契约

tracer 放在共享的真实搜索内核中；只在显式 traced 入口打开时采集，不改图、候选初始化、插入规则或输出顺序。距离均遵循活动 `DistanceComputer` 的“越小越好”顺序。核心字段及含义如下。

| 事件 | 定义与核对方式 |
| --- | --- |
| `distance_evaluations` | 每次 `dis(id)`，包含初始入口；必须等于外部 counted NDC |
| `expanded_count` | 保留候选被取出并扫描邻接表 |
| `evaluated_neighbor_count` | 有效且未访问过的邻居真正计算距离，不含初始入口 |
| `accepted_insertion_count` | 邻居插入候选池的返回位置 `< L` |
| `rejected_by_pool_bound_count` | 池已满时，新邻居不优于当前最差保留候选 |
| `rewind_count`、span | 新插入位置使游标回到当前位置或更早位置的次数与跨度 |
| best/pool-bound improvement | 接受插入使当前最优距离或满池边界严格改善的次数与幅度 |
| stagnation、frontier/pool gap | 不改善最优值的连续扩展，以及最终候选距离间隔 |
| `first_topk_gt_evaluation_*` | 首次访问 GT top-K 的时间位置；**只作监督/诊断，禁止线上特征** |

计数不变量包括 `accepted + rejected_by_pool_bound <= evaluated_neighbor_count`；重复节点在距离计算前排除。完整定义见 [冻结的 trace design](../finite_beam_reachability_diagnostics/v1/trace_design.md)。

### 数据、样本与复核

- WebVid 和 Yandex official-IP；冻结 Fast seed 20260828、底图、geometry top-8。
- 全阶段只使用 `drl_train[0:2000]`，其中前 1600 fit、后 400 audit；L64/128、K10。400 是训练集合内部审计，不是最终 held-out，也不是 validation。
- smoke：每数据集 20 query × 3 entries × 2 L，两数据集合计 240 次 traced/untraced 对照，top-10 ID 一致、距离容差 1e-6、NDC 相等。
- pilot：每数据集 2000 × 8 × 2 = 32,000 条 entry-level trace，报告显示计数不变量通过。样本行数不是 32K 独立 query。
- v1_audit 再做每数据集 120 条重复运行，全字段确定性检查通过；也检查了重复候选等问题，没有修改搜索语义来“修出”收益。

原始 trace 保存在 `finite_beam_reachability_diagnostics/v1/traces/`；manifest 保存数据、图、入口、源码与输入来源。详细报告：[v1](../finite_beam_reachability_diagnostics/v1/report.json)、[v1 audit](../finite_beam_reachability_diagnostics/v1_audit/report.json)。

## 3. v1 预测诊断：trace 有增量信息，但尚未满足轻量成本约束

### 目标与比较基线

效用为 `Recall@10 - 0.05 × graph_NDC / Fast3_graph_NDC`。在前 1600 query 上拟合 ridge（alpha=1），分别使用几何基线的 4 维特征，以及再加入 19 维真实 trace 特征；在后 400 query 上选 top-8 中的一个入口。几何特征覆盖 prototype distance、raw-entry distance、geometry rank 和 entry prior。trace 特征来自**已经执行候选搜索后**的观测，所以此时是具有特权信息的诊断/教师输入，不是已部署的免费路由特征。

必须区分两种对照：

- 对“拟合的 geometry ridge”，检查 trace 是否增加预测信息。
- 对“直接使用 geometry rank-0”，检查最终所选搜索是否有成本收益。

### 实际结果

| 数据、L | trace 对拟合 geometry ridge 的 ΔU [95% CI] | 对该 ridge 的 Recall Δ | 对 geometry rank-0 的 Recall Δ | 对 rank-0 的 graph NDC Δ |
| --- | --- | --- | --- | --- |
| WebVid 64 | +0.021640 [0.008840, 0.035580] | +2.150 pp | +2.525 pp | +0.924% |
| WebVid 128 | +0.014949 [0.003760, 0.027328] | +1.425 pp | +1.200 pp | -0.193% |
| Yandex 64 | +0.018345 [0.003530, 0.034803] | +1.775 pp | +1.900 pp | +1.988% |
| Yandex 128 | +0.015689 [0.005948, 0.027322] | +1.525 pp | +0.875 pp | +1.030% |

四项 ΔU 的区间下界都为正，故不能声称 trace 没有 incremental signal。但相对 rank-0 的 0.5% graph NDC 约束仅 WebVid L128 通过；其余三项不通过，而且上表成本仍未支付产生全部 top-8 trace 的诊断搜索成本。

收益集中于少数 query：有正收益的 query 比例依次约 24%、20.75%、21.5%、25%；正收益最大的 10% query 贡献总正收益约 97%、99.17%、99.14%、99.01%。候选 pairwise 排序准确率并未普遍提高：geometry → trace 依次为 0.5358→0.5138、0.5369→0.5153、0.5082→0.5079、0.5103→0.5248，仅一项上升。局部 top-choice 收益与全候选排序准确率不是同一指标。

### v1_audit 的纠正必须保留

原 v1 报告保留了错误的 terminal 标签 `NO_GO_TRACE_NOT_INCREMENTAL`。后续审计依据上述四个正的增量效用区间纠正为：

- `TRACE_INCREMENTAL_PASS_COST_ALIGNMENT_FAIL_COMPRESSION_UNTESTED`；
- terminal：`NO_GO_NOT_LIGHTWEIGHT`。

这表示 trace 增量信息通过、成本对齐失败、压缩尚未测试。原始报告仍保留用于追溯；当前解读应采用 [v1_audit 分析](../finite_beam_reachability_diagnostics/v1_audit/analysis.md)，不能在新摘要里继续传播旧标签，也不能因为审计纠正就宣布可部署方案通过。

## 4. 审计补充：成本约束下，候选内 oracle 是否仍有空间

v1_audit 对每条 query 只允许选择 `NDC(candidate) <= 1.005 × NDC(rank-0)` 的 top-8 候选，再在可行候选中用真实效用选 oracle。这样检查收益是否全部依赖更贵的入口；仍是 GT 特权上限，不是学习结果。

| 数据、L | 成本约束 oracle ΔU | Recall Δ | 平均逐 query 相对 NDC Δ |
| --- | --- | --- | --- |
| WebVid 64 | +0.036058 | +3.125 pp | -8.396% |
| WebVid 128 | +0.016217 | +1.325 pp | -5.237% |
| Yandex 64 | +0.024678 | +2.175 pp | -5.202% |
| Yandex 128 | +0.006712 | +0.500 pp | -3.242% |

四项 oracle utility CI 下界均为正。上表 NDC 是逐 query 相对变化的均值，不能未经重算与“两个均值的比值”混用。它支持进入一个小规模 query-only 压缩试验：便宜候选确实存在；它不证明局部 query 邻域足以识别这些候选。v1 的更大 Stage E、validation 与 held-out 均未运行。

证据：[原分析](../finite_beam_reachability_diagnostics/v1/analysis.md)、[修正分析](../finite_beam_reachability_diagnostics/v1_audit/analysis.md)、[审计报告](../finite_beam_reachability_diagnostics/v1_audit/report.json)、[审计 manifest](../finite_beam_reachability_diagnostics/v1_audit/manifests/manifest.json)。

## 5. v2 distillation：query-only 局部 cost-first utility Atlas

### 假设与固定设计

文件名叫 distillation，实际试验是一个局部近邻 utility Atlas，不是训练神经网络复制 trace。复用 v1 的前 1600 条 query 与其 entry-level 标签作为 fit 库；对后 400 条 audit query，仅依赖 query 向量、当前 Fast geometry top-8 ID 和训练 Atlas。

对新 query 在 fit query 中做**精确 cosine 64-NN**诊断，再对每个当前候选收集这些邻居中该 entry 曾被测试的观测。至少 4 条观测才可用，权重为 `max(cosine,0)`；全为零时均匀加权。候选先过成本约束，再比较保守效用残差：

1. 相对 rank-0 的预测 NDC 增幅均值 + 1 SE 必须 ≤ 0.005。
2. 预测 utility residual 均值 - 1 SE 必须 > 0。
3. 从可行候选中选效用下界最大者，否则保留 geometry rank-0。

这里 1 SE 是固定启发式 margin，不是已校准的概率保证。模型线上输入不含 GT、probe 或 trace；已有 trace 只用于构造 fit 标签。HNSW 只在设计里作为将来替代精确近邻扫描的可能部署方式，本阶段**未实现、未计时、未验证**。在线图 probe 为零，不代表在线路由成本为零：扫描 1600 个 query、64 邻居聚合、top-8 候选决策仍需支付。

### 执行范围与预设 gate

仅复用同一 `drl_train` 前 2K：fit `[0,1600)`、audit `[1600,2000)`；WebVid/Yandex、L64/128、K10、top-8、neighbors=64、min_observations=4、cost_limit=0.005、confidence_margin_se=1、cost_weight=0.05。该 400 query 已参与 v1 审计，不能称为新鲜独立测试。没有访问 validation 或 held-out。

训练内 gate 要求各数据集/预算的 utility 增益 95% CI 下界为正，同时平均 Recall 不下降、平均相对 graph NDC 增幅不超过 0.5%，且 reroute fraction ≥1%，避免只靠完全不改道的真空通过。最终报告中成本/Recall/非零改道条件通过，效用 CI 条件全部失败。

### 实际结果

| 数据、L | ΔU [95% CI] | Recall Δ | 平均逐 query 相对 graph NDC Δ | 改道率 |
| --- | --- | --- | --- | --- |
| WebVid 64 | +0.001794 [-0.001420, +0.006320] | +0.200 pp | +0.214% | 9.00% |
| WebVid 128 | +0.000387 [-0.003999, +0.004588] | +0.025 pp | -0.370% | 18.00% |
| Yandex 64 | +0.000048 [-0.005857, +0.004316] | +0.025 pp | +0.420% | 11.00% |
| Yandex 128 | +0.000313 [-0.000562, +0.001284] | +0.050 pp | +0.384% | 12.75% |

所有效用区间跨 0，未通过固定门槛。平均可用候选 WebVid 为 5.11、Yandex 为 6.845，最少为 0，说明 top-8 局部支持并非处处充分。保存的 Atlas 大小分别为 3,585,806 / 1,589,006 bytes；这些只是产物存储大小，不包含完整 Fast/底图，不是训练总成本或线上时延。

### 判定与禁止外推

最终 `decision.json` 为 `NO_GO_NOT_PREDICTABLE`。准确含义是：这套 64-NN、至少 4 次局部观察、1 SE margin、top-8 候选的 query-only 局部平均方法，在复用的 400-query 训练内审计上没有建立可靠正效用。不能扩写为所有 query-only 模型或所有蒸馏都不可预测，也不能把 v1 trace 的诊断增量直接算到这个学生方法名下。

未执行内容包括扩大库、扫更多参数、神经学生、HNSW 部署路由、validation、held-out 和正式端到端 Recall–QPS。该具体分支停止；之后任何新提案必须有独立活动计划和成本门槛，不能把本页历史当作运行许可。

证据：[冻结设计](../finite_beam_reachability_diagnostics/v2_distillation/design.md)、[实现](../benches/run/run_cost_constrained_reachability_distillation.py)、[WebVid 完整报告](../finite_beam_reachability_diagnostics/v2_distillation/webvid/report.json)、[Yandex 完整报告](../finite_beam_reachability_diagnostics/v2_distillation/yandex/report.json)、[最终 decision](../finite_beam_reachability_diagnostics/v2_distillation/decision.json)。两数据集目录保留 `atlas_fit.npz`、两档 `routes_train_audit_l*.npy`；报告保存输入及源码来源信息。

## 6. 整条证据链如何使用

| 已观察到 | 仍未证明 |
| --- | --- |
| 真正有限 beam 轨迹相对拟合几何基线有增量信息 | 该信息能以足够低的线上成本获得 |
| top-8 中存在满足逐 query 成本约束的更优 oracle | query-only 学习器能可靠选中它 |
| v2 小幅平均正值且改道不为零 | utility 改善显著且跨数据/预算稳定 |
| smoke 与重复 trace 的语义/计数检查通过 | 完整生产环境的端到端 QPS 和稳定性通过 |

历史结论需要按版本引用：v1 的旧 terminal 已被 v1_audit 纠正；v2 是压缩试验的独立失败门槛。两者都保留原产物及证据，不能通过覆盖旧报告把演进过程抹掉，也不能把训练内 pilot 改称正式 held-out 结论。
