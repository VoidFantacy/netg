# ACSG 当前任务与后续边界

2026-09-15最新用户任务是先审查GATE，再告知Deep/SIFT/GIST方法选择；接受核心机制正确的合理复现，不要求照搬作者代码缺陷。[审查已完成](entry_method_exploration/20260915_gate_reproduction_audit_v1/report.md)，新三集未启动。下一轮主方法建议GT10-hard，soft-t1只作一份预锁辅助；旧Web软/Y硬默认不回改。

接续新三集前应完成：在独立版本从GATE负例排除正例，过滤后断言互斥；明确独立QGT/fit/monitor/cal/test来源；核对SIFT实际11164866行的base与GT身份；准备原L2度量的兼容图和K1/K100评测入口。已有hop缓存仅在完整身份兼容时复用，不覆盖E96模型/结果。保留batch-first、CPU与统一kernel适配，并披露1000节点子图截断；不为追论文数值扩大超参网格。

从本次指令起，新开发选择和正式比较只测 **Recall@1、Recall@100**，K1/K100分别真实搜索并计完整端到端QPS；K100的L/ef至少100，不再测Recall@10。GT10训练目标数仍为10。新数据/模型/预算/选型规则在正式测试前冻结，仍同机单线程串行；不能按正式结果选hard/soft或按L拼赢家。当前“先检查告知”不产生后台训练/测试队列。

2026-09-15 E96用户任务已完成：三集完整四方法192点/576轮、Recall–QPS与失败率图、原始CSV、成本、报告和身份/单线程/逐query验收均已交付；不需要继续当前runner或追加网格。Web/Y GT10优于本轮GATE适配，LAION高预算保留质量与速度取舍；默认保持，后续工作以新的用户目标为准。[结果报告](entry_method_exploration/20260914_gate_new_ood_v1/report.md) · [完成记录](entry_method_exploration/20260914_gate_new_ood_v1/complete.json)。以下为E95已结束增强分支的历史停止范围。

2026-09-14，状态：**STOP_CURRENT_FIXED_H_PROFILE_GRAPH_BRANCH**。用户要求持续推进到“有更好的方法，或停止当前分支”。本轮已完成方法比较和E95实际验证；没有得到可替换GT10的新方法，现停止当前分支。默认保持Web GT10-soft-t1 / Yandex GT10-hard。[停止决定](entry_method_exploration/20260914_query_moment_graph_v1/decision.md) · [完整证据](entry_method_exploration/20260914_query_moment_graph_v1/report.md) · [复盘87](experiment_history/87_query_moment_graph_and_branch_stop.md)。

## E95历史停止范围

结束当前固定H815/821、围绕GT10的参数扰动型RL、多画像/目标分组、补边、父画像恢复和组合局部修补，以及E95 full/diag查询统计构图。没有待执行的训练、ANN、构图、QPS、依赖安装或后台会话；不恢复9月13日旧runner，不追加尺度、seed、步长、簇数、ef或训练预算来延续本分支。

E95使用原P评分恒定、查询统计仅作用离线构图，已经实际检验一个不同于局部扰动的闭式方案。两集各7952 query、两L、两半的四个候选–数据集组合全部未过冻结开发门；条件wall未启动。原E50/E52/E53/E56/E60/E89/E90诊断/对照和E94完整性能结论也已完成，不能重新列为待做首步。

此停止是当前分支的投入决策，不证明全部离线画像学习、图构造或RL无解，不终止整个ACSG。原GT10、Web局部正信号与所有负点分开保留。

## E95历史后继研究约束

当前没有必须补跑的研究产物或实验。若以后出现实质不同的研究问题，可另立新分支；先说明新的表示/动作、真实三入口联合收益、原GT10收益保留及可迁移依据。仅换优化器名称、超参数或对已有compact退化作修复，不满足重新立项的依据。不得把一般图非加性当作多步RL必然有效的证明。

新分支须在执行前冻结数据角色、预算、完整线上流程、简单对照、接受/停止条件和版本身份。相同候选/反馈数不等于相同训练wall，几何排名或未知三元组不等于已测联合效用。新方案改变base/metric/图/kernel/输入时依spec重建受影响产物。

## 数据、性能与封存

P-fit含历史train/monitor；aux/cal/audit反复使用，接受反馈计开发/训练信息。E94历史validation有既往暴露；不能按其最终坏例选动作/子集或调参。E95未打开E94最终载荷用于新实验，held-out保持未开。不得把旧开发集改名为新盲集。

如未来新分支进入性能阶段，继续同机单线程、数值库单线程、方法串行，以完整线上wall比较Recall–QPS和零命中失败；保留对应新协议的全部预算点和每轮计时，单L、NDC、插值或monitor均不构成性能GO。时间重复和跨L不增加独立query数。

原模型、NSG/base/GT、全部raw/日志/计时/选择/封存保持。9月13日限时任务早已结束；其历史state和交接不要求恢复。当前根文档可继续演进，旧snapshot/seal不改。旧下一阶段计划已保存在[E95 source_before](entry_method_exploration/20260914_query_moment_graph_v1/source_before/s-target.md)；本轮[方法比较](entry_method_exploration/20260914_query_moment_graph_v1/research.md)、[冻结最小实验](entry_method_exploration/20260914_query_moment_graph_v1/protocol.md)、[结果](entry_method_exploration/20260914_query_moment_graph_v1/report.md)及[完成核验](entry_method_exploration/20260914_query_moment_graph_v1/reviews/completion_audit.json)已经接续该计划。
