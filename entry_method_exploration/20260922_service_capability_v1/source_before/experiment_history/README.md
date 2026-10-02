# ACSG 历史实验详细复盘

最新完成记录：[121 E118共享比较方向入口收益预测](121_comparison_direction_pilot.md)，完整全H标签、12模型、140点/420轮wall及审计/图表完成；GraphCost无召回增益且更慢，默认保持，保留oracle与少量预测信息的研究边界。

最新理论记录：[120 GT10服务结构理论与旧缓存检验](120_service_structure_theory.md)，含强假设、交互谱/四块预测、margin共享条件及证据边界，不新增性能实验号。

此目录是[s-experiment.md](../s-experiment.md)对应的详细层。主索引只提供概览；对以前实验不确定时，必须阅读本目录对应卡片及其原始证据，不凭概览决定重做或否定一类方法。

跨阶段专题：[GT10：OOD 入口选择方法与实验总结](../研究方向.md) · [PDF（7页）](../GT10研究总结.pdf)（2026-09-17更新）。当前方法后直接展示 E103 四张重测图，再列 E25—E95 改进历史、E98—E103 实现优化与阶段总结；原始卡片及历史指标保留，不计作新实验。

## 阅读方式

1. 在`s-experiment.md`找到实验家族、版本与状态。
2. 完整读卡片的动机、实现/监督、数据split/metric/图、实际执行、结果和成本。
3. 沿卡片链接读原protocol/config/state/gate/report；有修正时同时核对原版本与后续审计，确认哪一个才是正式解释。
4. 需要精确数字或复现命令时继续读aligned结果、日志与源码身份。缺失证据写未确认；本目录不自动授权执行原命令或读取冻结评估数据。

每卡是已有证据的实质性复盘，不是重新执行的实验。原始模型、索引、向量、日志和详细结果继续保留原目录，通过相对链接定位，不搬移或覆盖。历史报告的下一步/旧spec章节号属于当时版本，当前架构见[spec](../spec.md)、下一阶段见[s-target](../s-target.md)。

## 卡片与内容范围

| 卡片 | 覆盖 |
|---|---|
| [119 四动作入口集合](119_entry_set_pilot.md) | E117：实际top3中选四动作、召回与时间联合浅树；32点96轮wall，未过主门，停止本版 |
| [118 E116后理论复盘](118_post_e116_theory_review.md) | 0新搜索/训练；稀疏响应、计时不稳及单/多编辑分解，四动作入口候选与历史查重，尚未执行 |
| [117 H外入口绑定](117_entry_id_pilot.md) | E116：固定GT10路由、真实三入口净收益与时间筛选；双集L128未获稳定增益，停止本版 |
| [116 19:00理论综合](116_theory_synthesis_1900.md) | 两阶段收益解释、停止条件、成本与最终身份 |
| [115 路由表示理论边界](115_routing_representation_theory.md) | 集中化保序反例、两入口XOR、多画像与非线性替代表达 |
| [114 路由工作与理论范围](114_router_work_and_theory_scope.md) | 精确工作分解、净增损、NGFix/SHEAF前作条件 |
| [113 评分与小图交叉](113_score_topology_factorial.md) | E115：四格归因与交互，混合候选门失败，完整图状态边界 |
| [112 统计与学习目标审查](112_statistical_objective_review.md) | 条件均值/缺失质量、教师量化和锚定几何，0新搜索/训练 |
| [111 搜索终点局部最优](111_terminal_local_optima.md) | E114：旧返回邻接核验，终点一致与增损，0新搜索 |
| [110 实际比较对支持](110_actual_comparison_support.md) | E113：原输出恢复；具体节点对缺少跨query支持，停止32维字典，0训练 |
| [109 目标支持与query分支](109_source_support_and_query_branches.md) | 描述性来源审查、保证范围与损失归因；4合成，0新真实搜索 |
| [108 首行覆盖H设计](108_one_hop_hub_design.md) | E112：标准次模目标的信息门；Web局部通过、Y覆盖/恢复不足，0新搜索，停止本版 |
| [107 限时理论综合](107_timebox_theory_synthesis.md) | E107–E111综合、图依赖反例及同分范围修正；默认保持，非新性能试验 |
| [106 排名核心证书](106_rank_core_certificate.md) | E111完成：条件可达下界及162点审计；同分ID边界/Y覆盖门失败，0新搜索 |
| [105 首展开干预](105_first_expansion_intervention.md) | E110完成：首排序干预修复部分三入口损失，但未超过单入口，停止候选 |
| [104 完美代理信息](104_perfect_proxy_information_gate.md) | E109完成：Y正/Web未转化，两个代理未过跨集训练门 |
| [103 单位hub实际小图](103_unit_hub_online.md) | E108完成：54点162轮wall，单位hub未形成跨集替换，GT10小图可检索性优势与精确质量分开识别 |
| [102 初始化因素](102_initialization_factorial.md) | E107完成：144点/1181184次NSG，单位hub已取得固定入口的大部分均值收益；画像与多入口优势不能预设 |
| [101 GT10条件机制](101_gt10_conditional_mechanism.md) | E106完成：匹配支持的置换未显示稳定Recall损失；GroupMean两集门失败，STOP_GROUPMEAN_CANDIDATE，原默认保持 |
| [100 GT10理论复盘](100_gt10_theory_review.md) | 非性能实验：闭式目标、平滑反例、区域覆盖与真实效用差、失败证据分层及理论先行顺序；0新搜索/训练 |
| [99 冻结WFree独立复验](99_wfree_frozen_replication.md) | E105两集各4096新源行query、真实K1/K100、128点384轮；质量与完整wall门均失败，停止本版WFree，默认保持 |
| [98 查询表示验证](98_query_representation_pilot.md) | E104两集六模型、655808次NSG、真实K1/K100；QMLP表示门失败，静态WFree仅开发正值，无新QPS |
| [97 查询表示研究](97_query_representation_research.md) | 非性能实验：旧网络能力审查、文献/表示分析、16个历史fit几何witness及未执行最小证伪协议 |
| [96 优化后五集完整重测](96_optimized_five_dataset_retest.md) | E103条件通过后的原五集完整Recall@1/100曲线更新，原模型和图保持 |
| [95 统一优化后的方法比较](95_shared_span_batch4_comparison.md) | E102统一span+batch4用于NSG、GT10、GATE，新旧36配置108plain，四集一致性及公平方法差异 |
| [94 原生Faiss与实现控制](94_faiss_nsg_comparison.md) | E101同图库基线、空槽/预取/batch4十版本40点120plain，四集64配置兼容性，生产保持E99 |
| [93 优化后剩余成本与NSG库核查](93_residual_search_cost_research.md) | E100共80000search；邻接空槽与优化后热点、路由0.50%、batch4数值检查，原生Faiss对照缺口；无新正式QPS或生产修改 |
| [91 WebVid搜索成本诊断](91_webvid_search_cost_diagnosis.md) | E98路由/图/采样与三个局部控制；550000search/36轮plain，预取与组合局部正值，主内核和默认未替换 |
| [88 GATE三数据集完整比较](88_gate_three_dataset_comparison.md) | E96三集完整base/公开10K、192点576轮单线程；Web/Y GT10支配GATE，LAION高预算质量速度取舍，失败率/成本/恢复与全部证据 |
| [87 查询统计构图与分支停止](87_query_moment_graph_and_branch_stop.md) | E95两闭式构造/原P评分恒定、两集7952真实开发失败；正式停止当前固定H画像/小图增强分支，原GT10保留 |
| [86 收口后RL方向与交接](86_post_closeout_rl_direction_review.md) | 9月13日限时任务已收口；区分更新转化、动作支持和查询损伤，下调当前RL/局部修补分支，0新实验 |
| [57 完整画像排序诊断](57_profile_ranking_diagnosis.md) | E68：0新ANN，近似缺口/93失败query排序连接；不是NSG反事实 |
| [56 多画像完整wall](56_multimode_wall.md) | E67：固定mode与duplicate、55点275轮、QPS/Recall/失败及完整回归 |
| [55 GT10多画像小索引](55_multimode_index.md) | E66：P+两模态直接3H小图、同容量重复P、7slot去重及完整开发 |
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

- [33 局部动作全池/采样诊断](33_local_sampling_diagnosis.md)：E44完整反馈证实遗漏，原入口分层未过方差门，停止该采样修订。

- [34 确定均值单步控制](34_mean_update_control.md)：E45完整反馈的小正值和避损，多数更新仍质量不变，进入精确反馈复用可行性验收。

- [35 完整三入口精确反馈复用](35_exact_feedback_cache.md)：E46全部原始输出与奖励/梯度恢复，完整反馈训练的调用成本具备实测依据。

- [36 完整反馈RL/ES](36_full_feedback_profile_rl.md)：E47完成八训练，保留RL双集局部信号；统一门因WebVid ES失败停止预算扩展。

- [37 评分/邻接四格](37_score_topology_factorial.md)：E48完成500状态，区分两集不同机制，保留有限静态机会与冲突。

- [38 冻结局部画像性能](38_frozen_local_rl_evaluation.md)：E49完成开发与完整曲线，局部WebVid正值保留，未形成双集前沿增益。

- [39 候选到均值转化](39_candidate_commit_diagnosis.md)：E50全轨迹证明已测机会到确定更新的缺口，0新搜索。

- [40 更新方向与半径](40_update_direction_radius.md)：E51实测跨离散边界的机会与放大损伤，接续真实反馈接受控制。

- [41 连续候选择优提交](41_direct_candidate_commit.md)：E52真实800决策改善更新转化，保留Yandex种子间损伤差异。

- [42 RL反馈步长接受](42_feedback_step_rl.md)：固定方向真实步长接受的四训练和独立重放。

- [43 完整模型画像/邻接四格](43_learned_model_factorial.md)：固定学成模型的评分与邻接作用，训练和监控分开。

- [44 固定候选池最终比较](44_final_method_comparison.md)：cal预选候选与NSG/Fast/FastGT三指标同机单线程完整实测。

- [45 纯离线构图RL](45_construction_only_rl.md)：固定在线评分P，实际G(C)反馈训练及部署字节核验。

- [46 扩展池最终比较](46_expanded_final_comparison.md)：19候选固定选型与最新完整三指标，未改选整组保留E55。

- [47 接受动作冲突诊断](47_accepted_action_conflicts.md)：完整固定轨迹的跨查询收益/损伤、质量稀疏与失败转移。

- [48 冻结池迁移](48_frozen_pool_transfer.md)：19模型的有限收益覆盖、损伤与跨split不一致，无新搜索。

- [49 固定动作辅助支持](49_fixed_action_support.md)：E60原动作支持双集0/40，约束全不动，停止相同动作扩大。

- [50 遗漏目标画像](50_missing_target_profiles.md)：E61固定真实遗漏成员重权及随机目标控制，覆盖扩大但fit/cal净负。

- [51 遗漏画像四格](51_missing_profile_factorial.md)：E62固定评分/拓扑交换，34灾难案例混合责任，交叉态cal均失败。

- [52 零命中query质量](52_zero_hit_mass_v2.md)：E63固定2倍质量与随机身份对照，fit局部正值但cal门失败。

- [53 固定池扩大历史开发](53_frozen_pool_aux.md)：E64七模型与7952辅助行，局部正值及失败门保持分开。

- [54 今日候选开发wall](54_development_wall.md)：E65完整五L五轮及14个失败转换query，开发局部信号不替代最终验证。

- [58 E69 精确画像三入口真实NSG](58_exact_triple_utility.md)：Yandex局部效用通过、Web未过；完整缓存/回放、38942新NSG，无QPS。

- [59 E70 固定小图搜索宽度](59_width_control.md)：单个ef10→30，Y质量门通过、Web反证，完整wall待测。

- [60 多画像加宽完整wall](60_width_wall.md)：E71同批65点325轮；加宽有局部质量、QPS成本及严重失败，无稳定整体改善；932880 NSG。

- [61 E72 真实hub计宽](61_distinct_hub_width.md)：固定图distinct10，Y局部正与更低于mode30的路由NDC保留，双集原接续门失败。

- [62 E73 同hub重复画像精简](62_compact_modes.md)：完整每hub画像分数集合保持，Y辅助质量正、Web迁移反证，完整wall接续。

- [63 E74 精简画像完整wall](63_compact_wall.md)：55点275轮，Y局部召回/失败及描述性前沿正值，Web损伤，91个失败转换query；未最终验证。

- [64 E75 精简保留原层级](64_preserved_compact_levels.md)：随机流/完整保留层级验收及真实NSG效用、固定接续门。

- [65 E76 子画像支持](65_child_profile_support.md)：旧返回关联诊断，不把低支持或组合信用当因果。

- [66 E77 子画像半收缩四格](66_child_shrink_factorial.md)：Web部分修复、Y方向损伤，交互及原门分列。

- [67 E78 固定图子质量范数](67_child_mass_norm.md)：质量占比与统一降权控制，旧收益保留/新损伤分列，双集门失败。

- [68 GT10目标空间分组画像](68_target_space_modes.md)：E79，目标/置换对照与完整双集辅助反馈、原A/P/Q恢复及失败查询。

- [69 同hub条件GT目标分组](69_hub_conditioned_targets.md)：E80，条件权重/流式目标特征与原P、compact、全局目标分组完整对照。

- [70 query与条件GT联合分组](70_joint_view_partition.md)：E81，原Q初始化、等权联合目标与原P/compact/E80条件分组同批对照。

2026-09-13第8串行会话：

| 新卡片 | 已执行范围 |
|---|---|
| [71 新目标完整排名效用](71_target_exact_utility.md) | E82，3593缺失键真实补齐，六诊断门失败 |
| [72 同hub补边](72_sibling_links.md) | E83，固定旧边追加与同节点度近邻控制，双集失败 |
| [73 查询排名补边](73_query_shortcuts.md) | E84，fit排名缺口投票，Web局部修复但完整门失败 |
| [74 query向量选择缓存](74_query_gate_feasibility.md) | E85，固定岭前3976训练/后3976接受，双集失败，0新ANN |

第9串行会话：[75 E86真实单边效用筛边](75_edge_utility.md)，训练正值与Web局部迁移保留，双集完整门失败。

[76 E87完整策略收益提议边](76_utility_proposals.md)：实际53/9候选、16/0边合并，Web局部修复、Y零更新，双集门失败。

[77 E88提议排名](77_proposal_rank_diagnosis.md)：0新ANN；167/19支持事件中19/0目标可进前三。

- [78 局部父画像恢复（E89）](78_local_parent_restore.md)：单组真实NSG效用筛选与固定图并图，双集接受门失败。

- [79 双来源父画像恢复（E90）](79_cross_source_parent_restore.md)：Web双源训练收益部分迁移但未过完整门，Y零更新。

- [80 最终评估工具准备（E91）](80_final_tooling_preparation.md)：参数化v3、旧完整批回归，0新ANN/最终选择。

第11串行会话：

- [81 固定补边与父恢复组合（E92）](81_composed_repair.md)：Web组合局部修复保留，完整开发门失败。
- [82 统一最终选型（E93）](82_final_candidate_selection.md)：77资格/41独立评分，实际模型先于最终载荷冻结。
- [83 冻结最终对照（E94）](83_frozen_final_comparison.md)：50点250wall及401完整失败query，尚无稳定整体默认替换收益。

第13串行会话：[84 整日结果汇报整理](84_campaign_20260913_report.md)，复用E94的中文图/PDF、完整401query离线浏览与机制说明；非新增实验，0训练/ANN/QPS，原封存保持。

第14串行会话：[85 交付核验与安全接续](85_campaign_delivery_readiness.md)，核验既有交付封存并补齐实际六页PDF审查来源，0新增实验；当时整日目标待监督收口。随后21:00监督退出与最新研究取舍见[86 收口后RL方向与交接](86_post_closeout_rl_direction_review.md)，旧阶段封存不改。

- [E97 Yandex测试前缀接入修正](90a_yandex_test_prefix_fix.md)：1万行声明/10万行文件不匹配的前置拦截、限定冻结修订与后台恢复。

- [E97 GATE修复与五集Recall@1/100](90_gate_disjoint_five_datasets_r1_r100.md)：800点、2400次wall及重画图。

- [92 NSG实现优化](92_nsg_search_optimization.md)：E99，先Git备份、预取与保持等距顺序的有效池复制；Web四点新旧对照、其他四集全query一致性。
