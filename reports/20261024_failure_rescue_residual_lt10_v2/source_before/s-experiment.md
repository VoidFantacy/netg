# ACSG 实验与研究索引

更新于2026-10-24。最新研究是E184离线诊断；最新正式性能是E183。当前判断只读[summary](summary.md)，实现合同读[spec](spec.md)，后续问题读[s-target](s-target.md)。历史卡片里的“当前/待执行”仅指原记录时点。

## 最近研究与当前依赖

| 记录 | 主题 | 状态与一句话判断 | 详细复盘 |
| --- | --- | --- | --- |
| E184 | 空间分布与失败修复 | 离线诊断完成；七集56K，无新性能，默认不变 | [卡片](experiment_history/184_residual_geometry_diagnosis_v1.md) · [六页PDF](reports/20261024_failure_rescue_residual_v1/ACSG_失败率_救回率与残差作用_20261024.pdf) |
| E183 | 七集GT10与残差综合评测 | 645点/1935完整T1；最新正式性能，默认不变 | [卡片](experiment_history/183_gt10_residual_comprehensive_v1.md) |
| E182 | 同源规模与容量密度 | 216点单轮；固定H小库优势在密度控制后不再单调 | [卡片](experiment_history/182_m5_scale_control_v1.md) |
| E181 | COCO/Flickr独立迁移 | 120点单轮；COCO受益、Flickr K100交叉 | [卡片](experiment_history/181_m5_multimodal_transfer_v1.md) |
| E180 | K100来源与嵌套扩容 | 扩容有质量收益；曲线解释以E181修正及E183新矩阵为准 | [卡片](experiment_history/180_m5_k100_capacity_v1.md) |
| E179 | 同16K目标对齐 | 小幅Recall收益，没有稳定QPS增益 | [卡片](experiment_history/179_m5_k100_objective_v1.md) |
| E178 | 画像路由风险 | 局部小L选择失配；范数匹配影响有限，未替换默认 | [卡片](experiment_history/178_profile_routing_risk.md) |
| E177 | 真实入口/代表query表示 | 有限测试无可靠默认替换依据 | [卡片](experiment_history/177_entry_representation_quick.md) |
| E176 | M5工程省费与剩余遗漏补全 | 对M5OPT无严格双升；速度和残差质量贡献分开 | [卡片](experiment_history/176_m5_residual_completion_curve_v1.md) |
| E175 | 区域补全五L曲线 | Recall多升但同L全慢，未新增双升预算组合 | [卡片](experiment_history/175_m5_region_budget_curve_v1.md) |
| E174 | 一跳区域补全 | 独立版本完成；不把邻域几何机会当净收益 | [卡片](experiment_history/174_m5_residual_regions.md) |
| E173 | 原M5公开测试 | 历史60点/180批已完成；不是当前正在执行 | [卡片](experiment_history/173_nsg_gt_m5_public_test_retest.md) |
| E172 | 五方法及三联动旧阶段 | 保留未完成范围和来源/成本记录，不作为当前恢复队列 | [卡片](experiment_history/172_all_methods_experiment_campaign.md) |
| E171 | 五机制理论与DOCX联动 | 理论阶段已完成；不把提案当已实现或新性能 | [卡片](experiment_history/171_overnight_algorithm_collision_and_certificates.md) |
| E99 | 共享NSG实现优化 | 保留当前共享核优化；旧绝对QPS不能拼入E183 | [卡片](experiment_history/92_nsg_search_optimization.md) |

## 完整历史与理论

[全部详细卡片](experiment_history/README.md)按文件原编号索引；早期卡片编号和正文实验E编号不一定相同，不按文件名前缀擅自重编号。

旧的多视角/注意力、probe-reroute、A+B、RL、多画像、有限beam及证书路线均保留其原协议、失败、修正和证据。理论文稿、SOURCE_ONLY、工具准备/验收与正式实验不是同一状态。

[范数敏感画像路由理论](entry_method_exploration/20261011_norm_aware_profile_theory_v1/theory.md)仍为THEORY_ONLY_UNIMPLEMENTED_UNTESTED；不能因有文档或源码审查就称性能通过。

查旧方法时从卡片进入协议、配置、state/gate、结果和修正，证据不足写未知。旧进程状态、期限和恢复命令已从当前入口移出，完整旧索引[归档](experiment_history/_maintenance/20261024_current_state_cleanup_v1/archive/s-experiment.md)供复核。
