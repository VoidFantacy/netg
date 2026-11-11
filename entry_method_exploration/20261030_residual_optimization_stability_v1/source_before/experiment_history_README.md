# ACSG 详细实验与研究记录

更新于2026-10-29。最新正式实验是[E193](193_adaptive_completion_gate_v1.md)自适应残差开关验证；E192保留共享必要条件与受控重配，E191保留七集两K综合测试和PDF身份。当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。

下面按原卡片文件号排序，保留全部详细记录和原路径。早期卡片号与正文E编号不一定相同，不将它们重新编号。卡片中的“当前/最新/运行中/待执行”是历史原文，不代表当前队列；状态、范围和修正要沿原协议/结果复核。

[2026-10-28费用结论与接续整理](_maintenance/20261028_completion_cost_handoff_v1/README.md)单独保留修改前快照、证据派生与验证；原E187 seal及当时验收收据不回写。

[2026-10-29残差正面证据同步](_maintenance/20261029_residual_positive_evidence_sync_v1/README.md)保留历史M5/B32/SQ有效场景，与E193有限门控负结果分别陈述；只读旧实测整理，无新实验。

## 全部详细卡片

| 原卡片文件 | 原题（历史） |
| --- | --- |
| [193_adaptive_completion_gate_v1.md](193_adaptive_completion_gate_v1.md) | E193：收益异质性、理想开关与廉价门完整费用验证 |
| [192_sharing_necessity_v1.md](192_sharing_necessity_v1.md) | E192：共享必要条件、候选支持上界与受控重配 |
| [191_seven_dataset_scoring_v1.md](191_seven_dataset_scoring_v1.md) | E191：七集两K来源与评分综合测试，交付PDF |
| [190_coco_fixed_candidate_scoring_v1.md](190_coco_fixed_candidate_scoring_v1.md) | E190：COCO固定候选评分与完整费用 |
| [189_reuse_completion_routing_v1.md](189_reuse_completion_routing_v1.md) | E189：GT10入口/主返回复用与稀疏补全路由 |
| [188_completion_cost_budget_v1.md](188_completion_cost_budget_v1.md) | E188：分段费用、等价省费与硬访问预算 |
| [187_adaptive_completion_pilot_v1.md](187_adaptive_completion_pilot_v1.md) | E187：全base区域残差补全来源与费用pilot |
| [186_adaptive_completion_design_v1.md](186_adaptive_completion_design_v1.md) | E186：不同遗漏特征的补全来源与预算适配设计（纯理论） |
| [185_manifold_residual_probe_v1.md](185_manifold_residual_probe_v1.md) | E185：流形相关局部几何与残差遗漏共享 |
| [184_residual_geometry_diagnosis_v1.md](184_residual_geometry_diagnosis_v1.md) | E184：残差与空间分布、失败比例及改进比例的离线诊断 |
| [183_gt10_residual_comprehensive_v1.md](183_gt10_residual_comprehensive_v1.md) | E183：GT10与残差的七数据集及失败查询综合评测 |
| [182_m5_scale_control_v1.md](182_m5_scale_control_v1.md) | E182：同源规模、固定容量与hub密度复盘 |
| [181_m5_multimodal_transfer_v1.md](181_m5_multimodal_transfer_v1.md) | E181：MS COCO / Flickr30k 经典多模态迁移测试（2026-10-16） |
| [180_m5_k100_capacity_v1.md](180_m5_k100_capacity_v1.md) | E180：K100候选覆盖与嵌套容量（完成） |
| [179_m5_k100_objective_v1.md](179_m5_k100_objective_v1.md) | E179：同容量 K100 目标 M5 补全表 |
| [178_profile_routing_risk.md](178_profile_routing_risk.md) | E178：画像方向与真实入口匹配的风险诊断 |
| [177_entry_representation_quick.md](177_entry_representation_quick.md) | E177：代表查询、真实入口和GT10画像的有限匹配测试 |
| [176_m5_residual_completion_curve_v1.md](176_m5_residual_completion_curve_v1.md) | E176：保留原 M5 的成本优化与剩余遗漏补全 |
| [175_m5_region_budget_curve_v1.md](175_m5_region_budget_curve_v1.md) | E175：M5区域补全的公共10K五档预算曲线 |
| [174_m5_residual_regions.md](174_m5_residual_regions.md) | E174：M5 残差候选作为区域入口 |
| [173_nsg_gt_m5_public_test_retest.md](173_nsg_gt_m5_public_test_retest.md) | 173：NSG、GT10、M5 直接公共测试复测 |
| [172_all_methods_experiment_campaign.md](172_all_methods_experiment_campaign.md) | 172 五方法与三联动实验 |
| [171_overnight_algorithm_collision_and_certificates.md](171_overnight_algorithm_collision_and_certificates.md) | 171 夜间理论接续：前作碰撞与原生/响应证书 |
| [170_recall_qps_algorithm_theory.md](170_recall_qps_algorithm_theory.md) | 170：Recall–QPS 多机制算法理论研究（非实验） |
| [169_gt10_algorithm_paper_theory.md](169_gt10_algorithm_paper_theory.md) | 169 GT10具体算法与CCF B论文理论 |
| [168_theory_proxy_information_local_certificate.md](168_theory_proxy_information_local_certificate.md) | 168 GT10代理、可见信息与局部有限搜索条件 |
| [167_theory_search_response_access_cost.md](167_theory_search_response_access_cost.md) | 167 有限搜索响应与目标访问成本研究 |
| [166_target_bank_frozen_curve.md](166_target_bank_frozen_curve.md) | 166 冻结目标库的相邻预算曲线 |
| [165_query_target_transfer_online.md](165_query_target_transfer_online.md) | 165 查询→真实目标迁移与同容量目标侧控制 |
| [164_router_rank_pareto_online.md](164_router_rank_pareto_online.md) | 164 目标预算的状态到查询相对rank表 |
| [163_soft_mass_transport_pipeline_conditions.md](163_soft_mass_transport_pipeline_conditions.md) | 163 Soft目标运输、归一化与入口稳定条件 |
| [162_single_hub_geometric_certificate_opportunity.md](162_single_hub_geometric_certificate_opportunity.md) | 162 单球/单hub质量证书训练侧机会检查 |
| [161_hard_mass_interval_certificate.md](161_hard_mass_interval_certificate.md) | 161 GT10-hard完整质量的区间条件与穷举核验 |
| [160_shared_batch_full_build_identity.md](160_shared_batch_full_build_identity.md) | 160 共享批处理后的三方完整构建 |
| [159_exact_label_batch_and_rank_dispatch.md](159_exact_label_batch_and_rank_dispatch.md) | 159 精确标签批处理和消费长度的共享工程检查 |
| [158_energy_profile_routing_search_bridge.md](158_energy_profile_routing_search_bridge.md) | 158 Energy画像分数到实际搜索的连接诊断 |
| [157_energy_selection_two_source_batches.md](157_energy_selection_two_source_batches.md) | 157 固定Energy选样的两批新源检索验证 |
| [156_energy_selection_actual_full_build.md](156_energy_selection_actual_full_build.md) | 156 固定r0 Energy完整构建 |
| [155_energy_selection_without_exact_temperature.md](155_energy_selection_without_exact_temperature.md) | 155 无旧精确温度的能量选样 |
| [154_fair_default_demand_build_cost.md](154_fair_default_demand_build_cost.md) | 154 共享按需QGT后的公平默认构建费用 |
| [153_replacement_alignment_and_simple_control.md](153_replacement_alignment_and_simple_control.md) | 153 方向收益选样未超过简单能量控制 |
| [152_temperature_label_error_interaction.md](152_temperature_label_error_interaction.md) | 152 温度误差与标签误差不能独立相加 |
| [151_frozen_hybrid_two_source_batches.md](151_frozen_hybrid_two_source_batches.md) | 151 冻结混合候选的两批新源确认 |
| [150_temperature_candidates_full_build.md](150_temperature_candidates_full_build.md) | 150 两种温度公式的冻结画像与主候选完整费用 |
| [149_temperature_cdf_calibration.md](149_temperature_cdf_calibration.md) | 149 Web温度的配对CDF校准 |
| [148_demand_qgt_full_build_cost.md](148_demand_qgt_full_build_cost.md) | 148 按需QGT完整费用与浮点边界 |
| [147_demand_qgt_dependency.md](147_demand_qgt_dependency.md) | 147：按需QGT精确标签的依赖核验 |
| [146_hybrid_full_build_cost.md](146_hybrid_full_build_cost.md) | 146：冻结低标签候选的完整构建费用 |
| [145_profile_routing_search_bridge.md](145_profile_routing_search_bridge.md) | 145：画像分数到有限搜索的连接与反例 |
| [144_hybrid_target_temperature_factorial.md](144_hybrid_target_temperature_factorial.md) | 144 2048标签替换与温度因素的真实搜索检查 |
| [143_partial_exact_target_replacement.md](143_partial_exact_target_replacement.md) | 143 少量精确目标替换的方向偏差—方差 |
| [142_cheap_residual_information.md](142_cheap_residual_information.md) | 142 廉价教师信号预测方向残差 |
| [141_directional_error_and_sampling_opportunity.md](141_directional_error_and_sampling_opportunity.md) | 141 归一化画像方向误差与补标机会 |
| [140_approximate_target_residual_variance.md](140_approximate_target_residual_variance.md) | 140 近似贡献残差方差与校正预算诊断 |
| [139_approximate_supervision_scope.md](139_approximate_supervision_scope.md) | 139 近似监督费用依赖与有限总体纠偏方向 |
| [138_e125_web_fresh_check_and_policy.md](138_e125_web_fresh_check_and_policy.md) | 138 E125冻结模型Web新查询单点复测与判定策略修订 |
| [137_approximate_target_profile_cost_pilot.md](137_approximate_target_profile_cost_pilot.md) | 137 E125近似目标画像的构建费用试验 |
| [136_target_budget_fullH_opportunity.md](136_target_budget_fullH_opportunity.md) | 136 目标预算的全H单入口余量 |
| [135_gt10_gt_inclusive_build_cost.md](135_gt10_gt_inclusive_build_cost.md) | 135 GT10包含训练GT的入口层重建成本 |
| [134_gt10_profile_direction_stability.md](134_gt10_profile_direction_stability.md) | 134 GT10归一化画像稳定性和跨半亲和 |
| [133_privileged_surrogate_decision_geometry.md](133_privileged_surrogate_decision_geometry.md) | 133 特权服务代理与真实决策误差分解 |
| [132_semantic_service_linear_compile.md](132_semantic_service_linear_compile.md) | 132 E124 语义服务静态编译停止 |
| [131_target_service_privileged_gate.md](131_target_service_privileged_gate.md) | 131 E123 目标区域到真实入口服务的特权信息门 |
| [130_gt_supervision_and_decision_decomposition.md](130_gt_supervision_and_decision_decomposition.md) | 130 决策遗憾与GT监督关联的只读机制检查 |
| [129_action_coupled_ridge.md](129_action_coupled_ridge.md) | 129 E122 动作关联的预测函数正则 |
| [128_router_state_table.md](128_router_state_table.md) | 128 E121 原路由上层状态表 |
| [127_gt10_strength_review.md](127_gt10_strength_review.md) | 127 GT10强项、后继瓶颈与改进方向 |
| [126_qps_first_entry_theory.md](126_qps_first_entry_theory.md) | 126 从完整 QPS 重建入口理论 |
| [125_knn_three_point_timing.md](125_knn_three_point_timing.md) | 125 TargetKNN 三点三次轻量完整计时 |
| [124_target_budget_response.md](124_target_budget_response.md) | 124 E120 目标预算响应与查询信息审查 |
| [123_decision_alignment_audit.md](123_decision_alignment_audit.md) | 123 决策一致性与置信排序缓存审查 |
| [122_service_capability_pilot.md](122_service_capability_pilot.md) | 122 E119：响应定义入口能力与受控评分器检验 |
| [121_comparison_direction_pilot.md](121_comparison_direction_pilot.md) | E118：共享比较方向的入口收益预测（已完成） |
| [120_service_structure_theory.md](120_service_structure_theory.md) | 120｜GT10服务结构理论与旧缓存检验 |
| [119_entry_set_pilot.md](119_entry_set_pilot.md) | 119｜E117四动作入口集合试验 |
| [118_post_e116_theory_review.md](118_post_e116_theory_review.md) | 118｜E116后的入口选择理论与缓存复盘 |
| [117_entry_id_pilot.md](117_entry_id_pilot.md) | 117｜E116：固定GT10路由的H外入口绑定 |
| [116_theory_synthesis_1900.md](116_theory_synthesis_1900.md) | 116｜19:00理论研究综合收尾 |
| [115_routing_representation_theory.md](115_routing_representation_theory.md) | 115｜小图几何解释与入口表示的理论边界 |
| [114_router_work_and_theory_scope.md](114_router_work_and_theory_scope.md) | 114｜路由工作量、净收益与理论归属 |
| [113_score_topology_factorial.md](113_score_topology_factorial.md) | 113｜E115 GT10评分与小图交叉机制 |
| [112_statistical_objective_review.md](112_statistical_objective_review.md) | 112｜统计目标、教师量化与锚定几何审查 |
| [111_terminal_local_optima.md](111_terminal_local_optima.md) | 111｜E114搜索终点的局部最优性质 |
| [110_actual_comparison_support.md](110_actual_comparison_support.md) | 110｜E113实际搜索比较对支持 |
| [109_source_support_and_query_branches.md](109_source_support_and_query_branches.md) | 109｜目标支持与query内部搜索分支 |
| [108_one_hop_hub_design.md](108_one_hop_hub_design.md) | 108｜E112首行覆盖入口设计 |
| [107_timebox_theory_synthesis.md](107_timebox_theory_synthesis.md) | 107｜E107–E111限时理论综合 |
| [106_rank_core_certificate.md](106_rank_core_certificate.md) | 106｜E111 排名核心可达证书 |
| [105_first_expansion_intervention.md](105_first_expansion_intervention.md) | 105｜E110 固定三入口首展开干预 |
| [104_perfect_proxy_information_gate.md](104_perfect_proxy_information_gate.md) | 104｜E109 完美目标代理信息门 |
| [103_unit_hub_online.md](103_unit_hub_online.md) | 103｜E108 单位hub真实小图与在线wall |
| [102_initialization_factorial.md](102_initialization_factorial.md) | 102｜E107 表示与入口数的系统因素对照 |
| [101_gt10_conditional_mechanism.md](101_gt10_conditional_mechanism.md) | 101｜E106 GT10条件分解、置换与条件聚合 |
| [100_gt10_theory_review.md](100_gt10_theory_review.md) | 100｜GT10理论复盘与研究顺序调整 |
| [99_wfree_frozen_replication.md](99_wfree_frozen_replication.md) | 99｜E105 冻结 WFree 独立复验 |
| [98_query_representation_pilot.md](98_query_representation_pilot.md) | 98｜E104 查询侧非线性表示 pilot |
| [97_query_representation_research.md](97_query_representation_research.md) | 97｜查询侧表示研究与历史训练样本几何检查 |
| [96_optimized_five_dataset_retest.md](96_optimized_five_dataset_retest.md) | E103：优化后的五集完整重测 |
| [95_shared_span_batch4_comparison.md](95_shared_span_batch4_comparison.md) | E102：共享span+batch4的统一方法比较 |
| [94_faiss_nsg_comparison.md](94_faiss_nsg_comparison.md) | E101：原生 Faiss NSG 同图比较与优化价值 |
| [93_residual_search_cost_research.md](93_residual_search_cost_research.md) | E100：E99 后的剩余搜索成本与库使用核查 |
| [92_nsg_search_optimization.md](92_nsg_search_optimization.md) | E99：NSG邻居预取与候选池复制优化 |
| [91_webvid_search_cost_diagnosis.md](91_webvid_search_cost_diagnosis.md) | E98：WebVid GT10与完整HNSW搜索成本诊断 |
| [90a_yandex_test_prefix_fix.md](90a_yandex_test_prefix_fix.md) | E97 Yandex公开查询前缀接入修正 |
| [90_gate_disjoint_five_datasets_r1_r100.md](90_gate_disjoint_five_datasets_r1_r100.md) | E97：GATE正负标签修正与五集Recall@1/100 |
| [89_gate_reproduction_audit.md](89_gate_reproduction_audit.md) | 89｜GATE实用复现检查与新评测口径 |
| [88_gate_three_dataset_comparison.md](88_gate_three_dataset_comparison.md) | E96：GATE三数据集完整比较 |
| [87_query_moment_graph_and_branch_stop.md](87_query_moment_graph_and_branch_stop.md) | 87｜查询二阶统计构图与当前分支停止（E95） |
| [86_post_closeout_rl_direction_review.md](86_post_closeout_rl_direction_review.md) | 86｜9月13日收口后的 RL 方向复盘与交接 |
| [85_campaign_delivery_readiness.md](85_campaign_delivery_readiness.md) | 85｜第14会话交付核验与安全接续（非新实验） |
| [84_campaign_20260913_report.md](84_campaign_20260913_report.md) | 84｜9月13日整日汇报整理（第13会话，非新增实验） |
| [83_frozen_final_comparison.md](83_frozen_final_comparison.md) | 83｜冻结选型后的最终完整性能对照（E94） |
| [82_final_candidate_selection.md](82_final_candidate_selection.md) | E93 最终选择已冻结 |
| [81_composed_repair.md](81_composed_repair.md) | 81｜固定补边与父画像恢复的组合（E92） |
| [80_final_tooling_preparation.md](80_final_tooling_preparation.md) | 80｜最终评估工具参数化（E91，0ANN） |
| [79_cross_source_parent_restore.md](79_cross_source_parent_restore.md) | 79｜双来源支持的局部父画像恢复（E90） |
| [78_local_parent_restore.md](78_local_parent_restore.md) | 78｜真实效用筛选局部父画像恢复（E89） |
| [77_proposal_rank_diagnosis.md](77_proposal_rank_diagnosis.md) | E88 已测提议目标为何很少改变入口 |
| [76_utility_proposals.md](76_utility_proposals.md) | 76｜完整策略收益提出目标后实际单边筛选（E87） |
| [75_edge_utility.md](75_edge_utility.md) | 75｜真实单边效用筛选静态小图（E86） |
| [74_query_gate_feasibility.md](74_query_gate_feasibility.md) | 74｜路由前query向量选择的缓存可行性 |
| [73_query_shortcuts.md](73_query_shortcuts.md) | 73｜训练查询排名缺口补边 |
| [72_sibling_links.md](72_sibling_links.md) | E83 compact同hub画像连接补全 |
| [71_target_exact_utility.md](71_target_exact_utility.md) | E82 新目标画像完整排名的真实效用 |
| [70_joint_view_partition.md](70_joint_view_partition.md) | E81：query与条件GT目标联合分组 |
| [69_hub_conditioned_targets.md](69_hub_conditioned_targets.md) | E80：按真实hub条件化的GT10目标分组 |
| [68_target_space_modes.md](68_target_space_modes.md) | E79：以GT10目标方向分组的入口画像 |
| [67_child_mass_norm.md](67_child_mass_norm.md) | E78 固定图子质量范数权重 |
| [66_child_shrink_factorial.md](66_child_shrink_factorial.md) | E77 子画像固定半收缩与评分/构图四格 |
| [65_child_profile_support.md](65_child_profile_support.md) | E76 子模态支持与既有收益损伤 |
| [64_preserved_compact_levels.md](64_preserved_compact_levels.md) | E75 精简画像保留原随机层级 |
| [63_compact_wall.md](63_compact_wall.md) | E74 判断与边界 |
| [62_compact_modes.md](62_compact_modes.md) | E73 同hub完全重复画像精简 |
| [61_distinct_hub_width.md](61_distinct_hub_width.md) | E72 按真实hub计宽的小图搜索控制 |
| [60_width_wall.md](60_width_wall.md) | E71 多画像加宽的完整开发性能比较 |
| [59_width_control.md](59_width_control.md) | E70 固定小图搜索宽度控制 |
| [58_exact_triple_utility.md](58_exact_triple_utility.md) | 58. E69 完整画像前三的真实NSG效用 |
| [57_profile_ranking_diagnosis.md](57_profile_ranking_diagnosis.md) | E68 完整画像排序与原生近似入口诊断 |
| [56_multimode_wall.md](56_multimode_wall.md) | E67 多画像与重复画像控制完整wall |
| [55_multimode_index.md](55_multimode_index.md) | E66 GT10多画像单小索引 |
| [54_development_wall.md](54_development_wall.md) | E65 今日候选的历史开发集完整wall比较 |
| [53_frozen_pool_aux.md](53_frozen_pool_aux.md) | E64 今日固定候选扩大历史开发复核 |
| [52_zero_hit_mass_v2.md](52_zero_hit_mass_v2.md) | E63 零命中query质量重权 |
| [52_zero_hit_mass.md](52_zero_hit_mass.md) | E63 零命中query质量重权 |
| [51_missing_profile_factorial.md](51_missing_profile_factorial.md) | E62：遗漏画像的评分与邻接四格 |
| [50_missing_target_profiles.md](50_missing_target_profiles.md) | 50. E61 全fit遗漏GT成员画像 |
| [49_fixed_action_support.md](49_fixed_action_support.md) | 49. E60 固定动作辅助支持与迁移 |
| [48_frozen_pool_transfer.md](48_frozen_pool_transfer.md) | 48. E59 冻结模型池迁移诊断 |
| [47_accepted_action_conflicts.md](47_accepted_action_conflicts.md) | 47. E58 固定接受动作冲突诊断 |
| [46_expanded_final_comparison.md](46_expanded_final_comparison.md) | 46. E57 扩展池最终比较 |
| [45_construction_only_rl.md](45_construction_only_rl.md) | 45. E56 纯离线构图RL |
| [44_final_method_comparison.md](44_final_method_comparison.md) | 44. E55 固定候选池最终比较 |
| [43_learned_model_factorial.md](43_learned_model_factorial.md) | 43. E54 完整模型画像/邻接四格 |
| [42_feedback_step_rl.md](42_feedback_step_rl.md) | 42. E53 RL反馈步长接受 |
| [41_direct_candidate_commit.md](41_direct_candidate_commit.md) | 41. E52 连续候选择优提交 |
| [40_update_direction_radius.md](40_update_direction_radius.md) | 40. E51 更新方向与半径 |
| [39_candidate_commit_diagnosis.md](39_candidate_commit_diagnosis.md) | 39. E50 候选到均值转化诊断 |
| [38_frozen_local_rl_evaluation.md](38_frozen_local_rl_evaluation.md) | 38. E49 冻结局部画像开发与性能 |
| [37_score_topology_factorial.md](37_score_topology_factorial.md) | 37. E48 评分与邻接四格控制 |
| [36_full_feedback_profile_rl.md](36_full_feedback_profile_rl.md) | 36. E47 局部画像完整反馈RL/ES |
| [35_exact_feedback_cache.md](35_exact_feedback_cache.md) | 35. E46 完整三入口精确反馈复用 |
| [34_mean_update_control.md](34_mean_update_control.md) | 34. E45 同状态确定单步完整反馈控制 |
| [33_local_sampling_diagnosis.md](33_local_sampling_diagnosis.md) | 33. E44 固定局部动作全池与采样诊断 |
| [32_local_profile_rl.md](32_local_profile_rl.md) | 32. E43 固定背景的局部画像策略优化 |
| [31_removed_profile_factorial.md](31_removed_profile_factorial.md) | 31. E42 被移除入口画像责任与条件奖励 |
| [30_profile_factorial.md](30_profile_factorial.md) | 30. E41 目标画像与其余画像的2×2隔离 |
| [29_profile_payoff_attribution.md](29_profile_payoff_attribution.md) | 29. E40 已有画像动作的收益、损伤与入口归因 |
| [28_fixed_profile_batch_diagnosis.md](28_fixed_profile_batch_diagnosis.md) | 28. E39 固定参数的大批次方向诊断 |
| [27_offline_profile_diagnosis.md](27_offline_profile_diagnosis.md) | 27. E38 离线画像训练反馈诊断 |
| [26_offline_profile_rl.md](26_offline_profile_rl.md) | 26. E37 离线入口画像策略优化 |
| [25_query_swap_policy.md](25_query_swap_policy.md) | E36：针对query逐步换入/换出三入口 |
| [24_hnsw_selection_diagnosis.md](24_hnsw_selection_diagnosis.md) | 24 当前GT10的HNSW选点最小验证（E35） |
| [23_hnsw_rl_benchmark.md](23_hnsw_rl_benchmark.md) | 23 冻结HNSW-RL图的性能补测（E34） |
| [22_hnsw_edge_rl.md](22_hnsw_edge_rl.md) | 22 强化学习直接训练HNSW图边（E33） |
| [21_direct_reward_policy.md](21_direct_reward_policy.md) | 21 直接检索收益策略优化（E32） |
| [20_training_effectiveness.md](20_training_effectiveness.md) | 20 有界训练有效性检查（E31） |
| [19_equivalent_teacher_sets.md](19_equivalent_teacher_sets.md) | 19 等效三入口集合教师（E30） |
| [18_teacher_objective_alignment.md](18_teacher_objective_alignment.md) | 18 教师标签与训练目标对齐（E29） |
| [17_gt10_shared_transform.md](17_gt10_shared_transform.md) | 17 GT10共享入口变换（E28） |
| [16_gt10_mechanism.md](16_gt10_mechanism.md) | 16｜GT10收益机制分析与限定补测 |
| [15_profile_shrinkage.md](15_profile_shrinkage.md) | E26：单路画像收缩与损失迁移 |
| [14_selective_profile_gate.md](14_selective_profile_gate.md) | 14｜固定旧/新画像的选择性改道 |
| [13_gt_topk_profiles.md](13_gt_topk_profiles.md) | 13｜固定 H 的 GT1/GT10 × 硬/软画像 |
| [12_three_entry_rank_exploration.md](12_three_entry_rank_exploration.md) | 12｜真实三入口收益排序：完整W与rank8探索 |
| [11_ab_fixed_slot_exploration.md](11_ab_fixed_slot_exploration.md) | 11｜A+B固定槽位入口选择：完整训练与五点探索 |
| [10_c_state_intervention.md](10_c_state_intervention.md) | 10｜C 同状态一次有限入口干预：C0/C1/C2 |
| [09_research_designs_not_experiments.md](09_research_designs_not_experiments.md) | 09｜已完成研究设计与未执行提案 |
| [08_fast_router_diagnosis.md](08_fast_router_diagnosis.md) | 08｜Fast入口选择根因诊断：全H真实效用、组合与局部迁移 |
| [07_hierarchical_p2_p3.md](07_hierarchical_p2_p3.md) | 07｜目标区域与受保护候选池：P2/P3完整负结果 |
| [06_finite_beam_and_atlas.md](06_finite_beam_and_atlas.md) | Finite-beam reachability 与局部 utility Atlas 历史 |
| [05_probe_reroute.md](05_probe_reroute.md) | 入口 oracle、失败检测与 probe/reroute 历史 |
| [04_utility_and_representation.md](04_utility_and_representation.md) | 搜索效用监督与表示改造历史 |
| [03_baselines.md](03_baselines.md) | GATE 适配与比较基线准备复盘 |
| [02_multiview_and_attention.md](02_multiview_and_attention.md) | Multi-view 与 confidence-attention 实验复盘 |
| [01_fast_and_legacy.md](01_fast_and_legacy.md) | Fast v1 与旧 NETG / ACO 实验复盘 |

## 维护与归档

[2026-10-24结论同步与文档清理](_maintenance/20261024_current_state_cleanup_v1/README.md)保存清理前完整根文档、可读历史副本、引用检查和文件清单。旧数据、模型、图、失败记录及科学manifest仍在原处；维护收据不修改实验结论。
