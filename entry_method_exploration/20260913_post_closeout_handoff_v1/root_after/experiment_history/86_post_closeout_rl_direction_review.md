# 86｜9月13日收口后的 RL 方向复盘与交接

2026-09-13，用户在讨论“今天怎样改进、是否继续、效果差是否来自 RL 方向”后要求更新交接。本文是既有证据复盘和研究优先级调整，**不是 E95 或新实验**；新增训练、ANN、构图、GT、QPS 均为 0。旧实验规则、选择、模型、报告与封存保持。

## 收口状态与最终结果

当天累计执行14个串行会话。监督器于21:00:01.595123（北京时间）按原截止退出，21:00:17最终审查确认无活动项目CLI、原生实验或浏览器任务，无第15会话。完成的是限时探索及汇报任务，未建立稳定优于当前GT10默认方法的证据。监督原始记录的精确副本见[退出记录](../entry_method_exploration/20260913_post_closeout_handoff_v1/evidence/daemon_finished.json)、[最终检查](../entry_method_exploration/20260913_post_closeout_handoff_v1/evidence/review_217_final_goal_audit.json)；原路径与SHA记于[本次前件清单](../entry_method_exploration/20260913_post_closeout_handoff_v1/before_manifest.json)。

E94最终50点/250轮完整单线程wall、401独立失败query/10730全五L方法单元已交付。Web组合相对compact五L均有质量修复，但相对匹配GT10-soft五L Recall均负；L128分别为+0.270和−0.385个百分点。Yandex compact相对GT10-hard低L小正、高L有损伤。未形成稳定整体QPS–Recall前沿优势，默认保持Web GT10-soft-t1 / Yandex GT10-hard。原[最终配对表](../entry_method_exploration/20260913_until2100_v1/stage35_final_comparison_v1/analysis_v1/paired.csv)、[报告](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/report.md)不改。

## 需要分开的证据

| 问题 | 已有直接证据 | 能判断到哪里 |
|---|---|---|
| 当前 RL 是否有独立必要性 | E37画像RL是一步Gaussian参数策略，独立采样RL与成对扰动ES估计同一平滑目标；E43/E47/E53改为局部行参数及反馈接受 | 合法的策略搜索，尚未证明比简单优化更适合；不是已经学成按构图状态进行长期规划的策略 |
| 已测机会能否转成更新 | E50中，RL有净正候选时，Web184/214=85.98%、Y93/97=95.88%的确定均值更新不改变完整训练池命中 | 更新转化缺口明确；这些是旧固定状态的单步诊断，不能把最佳候选单步和当作连续模型Recall |
| 换更新方式能否缓解 | E52直接择优的Web双seed监控增量+0.3125/+0.2051pp，E47 RL对应+0.0781/+0.0098pp；Y直接择优为+0.0586/−0.0977pp。E53真实步长接受、E56纯构图RL也有局部正值 | 优化方式解释一部分问题，但跨查询迁移和seed不稳定仍在；monitor参与选点，不能称独立最终性能或普遍贪心优于RL |
| 小幅动作是否有效 | E60每集120动作，Web108、Y114在辅助集命中全空；迁移集分别93、120全空；满足原训练目标与辅助支持的状态均0/40 | 这组固定动作反馈稀疏、条件交集为空；不能解释成整个局部空间无解，也不能把全部不动说成成功风险控制 |
| 较大动作是否互相损伤 | E89父画像恢复在fit20K中，Web31/32、Y26/32动作同时增损；筛选单项净值和297/125，实际合并224/114 | 这些动作确有查询间取舍及组合非加性；与E60动作/数据角色不同，不能合并为全体RL冲突率 |
| 今日改进是否证明RL有效或无效 | E61–E92主要是确定性画像聚合、分组、静态补边和真实效用筛选，最终Web修复仍未超过P | 不把全天候选统称RL；后半程不少增量修复的是新多画像方案自己的退化 |

方法与原始证据：

- RL定义：[E37方法依据](../entry_method_exploration/20260912_offline_profile_rl_v1/method_basis.md)、[E37训练源码](../entry_method_exploration/20260912_offline_profile_rl_v1/src/train.py)、[历史26](26_offline_profile_rl.md)。E33已有边概率、E36在线多步换点是其它版本，不受“一步画像参数策略”的概括替代。
- 更新问题：[E50完整统计](../entry_method_exploration/20260912_candidate_commit_diagnosis_v1/results/runs.csv)、[历史39](39_candidate_commit_diagnosis.md)；[E52模型表](../entry_method_exploration/20260912_direct_candidate_commit_v1/results/models.csv)、[历史41](41_direct_candidate_commit.md)；[E53模型表](../entry_method_exploration/20260912_feedback_step_rl_v1/results/models.csv)、[历史42](42_feedback_step_rl.md)、[E56复盘](45_construction_only_rl.md)。完整算法轨迹会分岔，算法比较不冒充固定状态单因素因果证据。
- 动作支持与损伤：[E60全动作表](../entry_method_exploration/20260913_until2100_v1/stage1_support_v1/results/actions.csv)、[历史49](49_fixed_action_support.md)；[E89训练增损](../entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/supplement_training_v1/derivation.json)、[历史78](78_local_parent_restore.md)；[当天机制说明](../entry_method_exploration/20260913_until2100_v1/session13_report_v1/mechanism_note.md)。
- 排名与补边范围：[E88原统计](../entry_method_exploration/20260913_until2100_v1/stage29_proposal_rank_diagnosis_v1/results/summary.json)、[历史77](77_proposal_rank_diagnosis.md)。仅已测边的167/19支持事件中19/0目标能进入固定候选集前三，说明这组动作的可达性修复受评分竞争限制，不代表所有候选或评分都无效。

## 当前判断与研究取舍

**保留离线学习入口画像/小图的目标，下调当前参数扰动型RL及现有局部修补分支的优先级。** “当前RL建模或更新方式不够合适”有实验依据；“强化学习整体不适用于建图”“共享画像一定没有更好解”均超出证据。局部RL正值、GT10原有信号和后续增强失败分别保留。

不原样重复RL/ES/直接择优、批次或半径扩张、多画像分组、补边、父恢复和既有门控。尤其不能因某项相对compact变好，就替代其相对原P及完整在线费用的检验。E50更新诊断、E52/E53更新控制、E60支持检查和E89/E90并图迁移均已执行，不能重新列成待做的首步。

下一优先级是只读研究和方法重新设计：先提出能产生可迁移净收益的动作/表示假设，说明如何对齐真实三入口联合搜索效用、保留原方法收益，再决定采用监督优化、确定性/黑盒搜索或RL。若考虑多步构图RL，必须明确状态、合法动作、转移、信用分配及超出即时择优的必要性；目前没有相应新实现或多步优势证据。只有新机制成立后，才讨论在同表示、同反馈预算及单列实际wall成本下比较优化器。具体接续任务与进退条件见[s-target](../s-target.md)。

P-fit包含旧train/monitor；aux/cal/audit已反复开发使用，选择反馈计训练。E34历史validation在E94中仅用于先冻结后的最终对照，本次结果未回流选择；其本身也非全项目盲集。后续不得按最终坏例选动作、子集或参数；新阶段须重新冻结数据角色和预算，held-out保持未开。本次用户只授权文档更新，没有启动新的研究执行或延长当天运行。

当前新交接为[收口后交接](../entry_method_exploration/20260913_post_closeout_handoff_v1/handoff.md)。原第14交接及campaign state的`day_goal_complete=false`保留为当时快照；它们不覆盖监督器已完成的限时任务状态，也不指示应恢复旧runner。
