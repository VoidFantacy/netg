# ACSG 当前结果摘要

2026-09-13，E60–E62三个阶段已完成。尚无可替换WebVid GT10-soft、Yandex GT10-hard的证据；今日整日目标未完成，未新增正式QPS。当前最明确的新结论是：扩大遗漏目标画像的作用范围仍有净损伤，单独冻结评分或拓扑也不能消除它。

E61固定lambda0.5，以完整P-fit20K原基线实际遗漏GT10成员重构画像，每query质量1，另设随机目标对照。missing的fit/cal/audit ΔRecall为WebVid−0.1020/−0.3906/+0.0195 pp、Yandex−0.0260/−0.1465/+0.0684 pp。cal均净增3条零命中，固定选择保留原P；audit小正值不改选型。fit入口改变8284/5602条，但fit自身净负，不能只归为迁移问题。

E62固定E61端点，补S=(Wmissing,G0)、T=(P,Gmissing)。S的cal ΔRecall为−0.1855/−0.1953 pp，T为−0.1758/−0.0488 pp，双集均未过门。WebVid T的fit+0.007 pp保留，但cal/audit负。原全命中变零命中的14/20例中，仅评分独立致零6/11例，仅拓扑4/7例，两个因素各自均足以致零1/1例，仅联合才致零3/1例。固定端点存在混合责任；不能全部归给图，也不能从极端事后分组推断可预测的困难query收益。

E60双集原J+辅助支持门0/40、约束全不动，停止相同局部动作扩大。WebVid9个辅助正动作只来自5个状态，且均train-J负；Yandex无辅助正动作。即使忽略train-J，已测WebVid正状态也少于预锁10/40。这是有限动作支持不足，不是整个画像空间不可能改善。

三阶段合计65344新NSG、971104 HNSW、336次小图构建，0新GT/梯度更新/正式QPS。E61六画像独立聚合通过；E62新增19030 NSG，176384集合/mask/缓存、88192 C/A路由恢复、8物理图与512三路parity通过。native始终单进程CPU15实际线程1；E62 Yandex曾短暂与一次提前只读分析重叠，该分析失败退出后已加完成门重跑通过，操作wall不作为严格独占性能证据，详见报告。

P-fit含旧train/monitor全部行，cal/audit历史及今天重复使用，Fast30K曾拟合全router_train，均不称盲集。E34重复使用的最终validation未进入本日训练或选择。昨日E53/E56离线局部信号与最终无稳定增量分别保留；昨日历史冻结文件和旧文档快照未改变。下一阶段及20:00–21:00正式交付窗口见[s-target](s-target.md)。

[E62报告与图](entry_method_exploration/20260913_until2100_v1/stage3_missing_factorial_v1/report.md)、[E61修正文案报告](entry_method_exploration/20260913_until2100_v1/stage2_missing_targets_v1/report_v2.md)、[E60报告](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/report.md)、[交接](entry_method_exploration/20260913_until2100_v1/handoff.md)、[昨日最终报告](entry_method_exploration/20260912_until2000_v1/closeout/final_report.md)。
