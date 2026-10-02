# ACSG 历史实验详细复盘

此目录是[s-experiment.md](../s-experiment.md)对应的详细层。主索引只提供概览；对以前实验不确定时，必须阅读本目录对应卡片及其原始证据，不凭概览决定重做或否定一类方法。

## 阅读方式

1. 在`s-experiment.md`找到实验家族、版本与状态。
2. 完整读卡片的动机、实现/监督、数据split/metric/图、实际执行、结果和成本。
3. 沿卡片链接读原protocol/config/state/gate/report；有修正时同时核对原版本与后续审计，确认哪一个才是正式解释。
4. 需要精确数字或复现命令时继续读aligned结果、日志与源码身份。缺失证据写未确认；本目录不自动授权执行原命令或读取冻结评估数据。

每卡是已有证据的实质性复盘，不是重新执行的实验。原始模型、索引、向量、日志和详细结果继续保留原目录，通过相对链接定位，不搬移或覆盖。历史报告的下一步/旧spec章节号属于当时版本，当前架构见[spec](../spec.md)、下一阶段见[s-target](../s-target.md)。

## 卡片与内容范围

| 卡片 | 覆盖 |
|---|---|
| [01 Fast与旧NETG](01_fast_and_legacy.md) | Fast正式WebVid/Yandex/LAION、旧ACO/DPC/Router及早期报告适用边界 |
| [02 Multi-view与attention](02_multiview_and_attention.md) | 三view质量、E0/E1/E1b总成本、confidence shared-alpha |
| [03 比较基线与准备](03_baselines.md) | GATE同图适配、无效版本、独立依赖/其它基线完成与未完成 |
| [04 效用与表示](04_utility_and_representation.md) | static ranker、centroid、residual、两轮modes、BTG多版 |
| [05 Oracle与probe-reroute](05_probe_reroute.md) | 免费oracle、风险检测、paid L10、restart/merge、frontier/topology chooser |
| [06 finite-beam与Atlas](06_finite_beam_and_atlas.md) | v1增量信息/成本、审计改判、v2近邻效用蒸馏 |
| [07 层次P2/P3](07_hierarchical_p2_p3.md) | 区域/门户/结构、真实执行、三项失败诊断、23trace及数据访问纠正 |
| [08 Fast根因诊断](08_fast_router_diagnosis.md) | 512双数据集、全H与组合、32项统计、v2成本修正 |
| [09 研究设计记录](09_research_designs_not_experiments.md) | 文献复审、入口调研v1–v5/A+B/C R0，以及E23后GT入口/聚类/rank/OOD微型图调研；研究原件不计作方法实验 |
| [10 C同状态干预](10_c_state_intervention.md) | E21：C0成本锁/C1状态机验收/C2有限动作oracle；按四点实质门停止 |
| [11 A+B固定槽位探索](11_ab_fixed_slot_exploration.md) | E22：完整标签/训练、线程与范围修正、NSG/Fast/A+B单线程五点探索及入口对L不变验收 |
| [12 真实三入口收益排序](12_three_entry_rank_exploration.md) | E23：固定真实入口、原kernel联合标签、Fast锚定完整W/rank8及同目标对照；执行状态见卡片 |
| [13 GT-topK硬/软画像](13_gt_topk_profiles.md) | E24：固定H、fit GT闭式画像、恢复与cal/audit、单线程validation60点；局部前沿信号，无正式GO |
| [14 两固定画像的选择性改道](14_selective_profile_gate.md) | E25：真实配对监督、Base/Dual门控、全部60点三次单线程wall；未建立跨数据收益保留/损失减少与性能优势 |
| [15 单路画像收缩](15_profile_shrinkage.md) | E26：三alpha、全体新损伤收费、50点三次单线程wall；未稳定保留收益并减少损失 |
| [16 GT10收益机制](16_gt10_mechanism.md) | E27：既有归属/画像/入口/成本归因，固定shuffle与局部exact诊断、WebVid硬画像重复wall；保留局部收益，收窄速度和因果解释 |
| [17 GT10共享入口变换](17_gt10_shared_transform.md) | C8真实三入口教师、共享linear/MLP/free、完整Recall–QPS比较与监督压缩边界 |
| [18 教师与目标对齐](18_teacher_objective_alignment.md) | E29：教师/损失2×2、完整fit诊断、110点三轮Recall–QPS与因素交互 |
| [19 等效三入口教师](19_equivalent_teacher_sets.md) | E30：严格并列集合、单/多教师与漂移控制、120点五轮Recall–QPS及推荐选择 |
| [20 训练有效性检查](20_training_effectiveness.md) | E31同目标优化、缓存真实命中与未知界、双集门停止、无新QPS |
| [21 直接收益策略](21_direct_reward_policy.md) | E32完整组合期望Recall、双集fit信号、真实开发四点对照及候选成本、开发门停止 |
| [22 HNSW图边RL](22_hnsw_edge_rl.md) | E33：真实轨迹REINFORCE、固定静态删边图、双seed与逐节点同出度随机控制；WebVid局部信号/Yandex开发失败，无QPS |
| [23 HNSW-RL性能补测](23_hnsw_rl_benchmark.md) | E34：用户另授权冻结RL/NSG/Fast/GT10五L，45点225轮单线程wall、Recall与零命中失败率 |
| [24 HNSW选点诊断](24_hnsw_selection_diagnosis.md) | E35：当前GT10强连通/已评分集合/精确画像与真实C8三入口，双集128个pilot最小验证 |
| [25 query相关换点](25_query_swap_policy.md) | E36：真实三入口差值反馈、query相关局部换点/停止、RL与同策略精确梯度控制、完整训练开发和单L成本 |
| [26 离线画像RL](26_offline_profile_rl.md) | E37：真实HNSW重建→NSG奖励、Gaussian RL/成对ES双seed、静态画像部署、50点250轮单线程曲线 |
| [27 离线画像反馈诊断](27_offline_profile_diagnosis.md) | E38：0新搜索，真实奖励/梯度分解、query批次噪声、精确μ随机/中心匹配与表示边界 |
| [28 固定参数批次诊断](28_fixed_profile_batch_diagnosis.md) | E39：固定双集两μ/八扰动，另取1024训练query，四点512方向全负，0更新并停止预算扩大 |
| [29 画像收益与损伤](29_profile_payoff_attribution.md) | E40：已有动作有限上界/静态最佳差距、覆盖与损伤分解、入口变化及query偏好，0新搜索 |
| [30 目标/其余画像隔离](30_profile_factorial.md) | E41：固定八格真实控制、WebVid局部单画像+4无损/Yandex目标零命中效应、0训练 |
| [31 被移除画像责任](31_removed_profile_factorial.md) | E42：WebVid联合致损/Yandex重复致损、条件边际与RL奖励决策、8576 NSG/0训练 |
| [32 局部画像RL/ES](32_local_profile_rl.md) | E43：固定背景的一行画像动作、真实ΔJ、预算匹配两臂；执行状态见卡片 |

## 写入规则

新卡片至少记录：身份与状态、问题与机制、训练/评估数据及访问范围、真实调用/预算、主结果、完整成本与未知项、停止理由/未测项目、可以和不可以推断的结论、版本修正、原证据/代码/命令入口。不能只放链接或一句NO_GO。

更新已有解释时保留原始实验版本，卡片明确纠正来源及影响范围，不静默改写原JSON/gate。新实验形成新条目或清楚的版本小节，并同步根目录`s-experiment.md`；新的当前结论才写入summary。依赖准备、实现验收、诊断、方法性能实验和未执行设计分开标记。

`_maintenance/20260908_document_reorganization/`仅保存本次文档整理的前后身份、审查和完整性校验，不是一个新方法实验。其中[source_before/spec.md](_maintenance/20260908_document_reorganization/source_before/spec.md)保存旧章节合同，[source_before/summary.md](_maintenance/20260908_document_reorganization/source_before/summary.md)保存迁移前的完整混合总结，保证拆分后仍可追溯。
