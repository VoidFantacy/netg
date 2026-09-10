# 11｜A+B固定槽位入口选择：完整训练与五点探索

2026-09-09，E22。训练版本[20260909_ab_experiment_v1](../entry_method_exploration/20260909_ab_experiment_v1/README.md)，最终用户指定的评测版本[exploration_5point_v1](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/report.md)。状态 **`EXPLORATORY_NO_OVERALL_FAST_GAIN`**：规定的五点探索已完成，当前候选未显示整体胜过Fast，不继续被取消的大矩阵。不是正式统计显著性NO_GO，也不否定所有入口表示/映射方法。

## 1. 问题与机制

在E20“候选入口有搜索效用但几何画像选不中”的诊断之后，用户先要求只读研究，再授权推进推荐A+B。实现为固定H槽位的`W=P0+VZ`，rank8、V列正交、`||Z||F≤0.5√H`，加多对一`pi(slot)→真实hub`。自由Z不同于旧共享affine设计的`Z=UᵀP0`；未运行的A/B独立R0仍保留设计身份，不回写为已经执行。

在线只有raw query→Micro-HNSW→slot→真实入口→原search_new(mode2)。模型不输入L。训练把从候选入口实际搜索得到的Recall作为效用标签，因此标签带有测量时的L；这不限制模型推理可用的搜索L。最终五点都固定同一份模型，逐query入口完全一致，只有后续搜索候选池L变化。

## 2. 实际离线执行

两个数据集为WebVid2.5M和official Yandex first10M，原raw IP、原冻结NSG、K10。三QGT构建seed20260828/29/30，后20K router_train `[10000,30000)`重建paired Fast20K，前1024行为cal、接着1024行为audit。这是历史开发池，只对本次拟合隔离，不是新的项目级未见样本。

按三构建真实hub并集共享相同入口的标签计算，模型各自仍只可用本构建H。WebVid并集1912、Yandex1940；各22048条query×L64/128，完整生成84,311,552和85,546,240次搜索效用标签，薄二进制保留hitcount、GT10 mask、graph NDC。全标签结构、样本返回ID评分和列映射验收通过。

完成12个dataset×seed×训练标签L的模型拟合；包括仅W、仅mapping、联合及先W后一次mapping对照。离散mapping最大化到达槽位的fit总命中；连续软遗憾提案以hard fit命中不降验收。cal只选择预先生成的checkpoint，audit/test不参与训练。全部模型在validation开放前冻结。

标签生成wall合计6639.99秒；12次训练阶段控制器记录合计1040.85秒，含启动与轮询粒度。既有GT、QGT、图等复用，未新测GT-inclusive总离线构建成本。不能将训练阶段时间或含计数的标注时间作为在线QPS。

## 3. 中断、线程与范围修正

最初过度安排14类方法×2L×3构建×双数据集×validation/held-out，各10K、三轮端到端/路由/图搜索分项预热和计时，并错误使用16线程。服务器重启中断评测，完整标签、12个模型及已完成批次保存且hash复核通过，恢复没有重训。

用户明确所有基线测试必须单线程后，16线程记录全部退出最终主表。单线程大矩阵完成12个cal/audit批次及WebVid seed20260828的完整validation批次（1661.5秒），随后用户指出探索阶段不应测得如此详细，原控制器和NSG后续队列均停止。原输出、日志、协议、修正和部分结果全部保留，不伪称完整三seed/held-out结果。

用户最终指定L64/128/256/400/800，其他采用精简探索参数。原8–10小时估计随大矩阵取消而失效。本卡正式结果只引用下面的独立五点版本。

## 4. 最终探索范围与NSG/Fast定义

两个数据集各validation前2000条；一个QGT seed20260828；仅NSG、Fast、A+B三个方法；五个L共30点。每点单线程、一次完整预热、一次独立plain端到端wall。没有held-out、额外构建、消融或分项计时。

- NSG-Medoid沿用项目基线：原图的`index.acsg.enterpoint`固定单入口，直接调用同一原search_new(mode2)，不经过路由HNSW。没有另建图。
- Fast为已有历史Fast30K direct3，原M16/efConstruction200/ef10、HNSW seed100、heap顺序不变。
- A+B五点统一使用seed20260828、由L128搜索效用训练的联合新候选；同一W/mapping，未额外训练、重新选checkpoint或用Fast回退。它基于20K画像/效用监督，与Fast30K训练成本不同。

QPS含路由、ID映射、原图搜索、正常输出；不含GT、计数、hash、JSON、装载和建路由索引。失败严格Recall@10<0.1，即GT10零命中。按同一query统计挽救与新增失败，全query均保留。

## 5. 相对Fast的实际结果

每点N=2000；失败数列为Fast→A+B。Recall差值单位pp，QPS变化来自该次独立wall。

| 数据集 | L | ΔRecall pp | ΔQPS | 失败数 |
|---|---:|---:|---:|---:|
| WebVid | 64 | −0.325 | −14.77% | 114→135 |
| WebVid | 128 | −0.540 | −8.29% | 54→70 |
| WebVid | 256 | +0.180 | −5.33% | 24→22 |
| WebVid | 400 | +0.175 | −5.14% | 10→9 |
| WebVid | 800 | +0.130 | −1.32% | 4→3 |
| Yandex-IP | 64 | −1.450 | −17.94% | 49→80 |
| Yandex-IP | 128 | −0.775 | −11.90% | 37→53 |
| Yandex-IP | 256 | −0.215 | −9.70% | 24→29 |
| Yandex-IP | 400 | +0.105 | −7.71% | 18→19 |
| Yandex-IP | 800 | +0.135 | −4.59% | 6→4 |

相对NSG，WebVid五点Recall增加0.950–2.835pp，少5–60条失败query；Yandex增加0.255–0.570pp，少6–17条失败query。QPS变化范围为WebVid−2.74%至+1.37%、Yandex−6.36%至−1.00%。这些是逐点描述，不能仅据Recall/失败率改善称整体胜过NSG；小幅wall差异尤其需要重复测量才能讨论稳定性。全部NSG/Fast/A+B原值、相对变化及挽救/新增失败见原报告和CSV。

当前候选在小L明显劣于Fast，高L有少量质量正值但十点实测QPS都较低。不能用高L的局部正值覆盖低L退化，也不对未测L做等Recall插值或作正式Pareto结论。

## 6. 验收与解释边界

五点真实运行每点16条query与独立原kernel对照，返回ID、距离bits和NDC一致；完整2000条warm/timed输出一致。单线程配置/数值库/实际OpenMP验收通过；独立GT评分复核60000个输出。三方法每条query在五个L下所选入口均一致，确认L仅影响下游搜索。正式搜索120000次，加960次小样本原kernel比较；两个数据集评测过程wall约80.07/85.09秒。

既有训练记录显示fit Recall在WebVid从75.1765%升到78.2585%，cal从74.9805%降至74.6484%；Yandex fit从90.2990%升到93.4285%，cal从89.6289%降至89.2383%。两个cal若允许Fast1回退均选初始checkpoint0，主表没有把该回退当新算法收益。所选残差范数约1.85e−4/1.81e−4，映射仍覆盖462/435个真实入口，主要变化来自mapping。这提示训练映射增益未泛化，但没有证明一切入口学习不可能；也未用本轮缺失的分项wall归因耗时退化。

最终只有validation2K、单构建、单次wall，属于探索结论。取消的大矩阵、其余seed/held-out、正式统计门均未完成；用户已经明确缩减范围，因此不继续补齐。C仍停止，无A+B×C联动；没有扩大rank/H/训练数据救场。

## 7. 原证据

- [完整三基线报告](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/report.md)、[五点协议](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/protocol.md)、[实际命令](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/commands.md)。
- [全部指标](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/metrics.csv)、[相对比较](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/comparisons.csv)、[JSON](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/summary.json)、[判定](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/results/decision.json)。
- [正确性/入口一致性](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/reviews/final_verification.json)、[输入模型manifest](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/inputs/manifest.json)、[冻结模型记录](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/reviews/frozen_model_profile.json)、[离线成本账](../entry_method_exploration/20260909_ab_experiment_v1/exploration_5point_v1/reviews/offline_cost_ledger.json)。
- [原训练协议](../entry_method_exploration/20260909_ab_experiment_v1/protocol.md)、[全标签核验](../entry_method_exploration/20260909_ab_experiment_v1/reviews/full_labels_verified.json)、[重启恢复](../entry_method_exploration/20260909_ab_experiment_v1/recovery/reboot_20260909T1210Z/manifest.json)、[线程修订](../entry_method_exploration/20260909_ab_experiment_v1/evaluation_single_thread_amendment.md)、[探索范围暂停记录](../entry_method_exploration/20260909_ab_experiment_v1/reviews/exploration_scope_pause.json)。

## 8. 2026-09-10方法复核补充：没有新实验

用户指出新方法应与Fast匹配三个入口，并追问每槽约25条fit却从约800入口中挑赢家的统计风险，以及PyTorch、低秩梯度下降和MLP是否合适。[新研究报告](../entry_method_exploration/20260910_optimizer_research_v1/report.md)核对原代码、选中模型、旧分项结果和11篇论文的方法章节；原文与代码阅读范围见[论文表](../entry_method_exploration/20260910_optimizer_research_v1/papers.md)。

原VZ低秩只限制W，不限制pi；联合候选的fit/cal与mapping-only一致，W-only则有微小cal正值。这支持优先检查自由重映射和目标错位，不足以把失败归因于PyTorch或证明rank8耗尽容量。旧WebVid validation10K/L128分项记录显示联合单入口的图NDC从同构建Fast20K单入口约1667.94升至1804.99，路由NDC几乎相同，成本退化主要在图搜索；此范围不能外推最终双数据集五点2K的逐点耗时原因。

新建议为固定真实入口身份、三个互异入口、真实组合收益监督，以Fast锚定完整W作可诊断参考，低秩同目标作控制，共享hub端MLP作备选。论文支持离线生成向量后用轻量索引部署，没有证明本任务rank8或新提案能胜Fast。所有候选均未选定、未实现、未运行；E22实测结论和原产物保留。状态`RESEARCH_COMPLETE_METHOD_UNSELECTED_UNRUN`，下一步以[s-target.md](../s-target.md)为准。
