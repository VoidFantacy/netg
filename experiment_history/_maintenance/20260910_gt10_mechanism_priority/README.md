# GT10收益机制分析：下一步优先级更新

2026-09-10夜间，用户明确要求把“弄清GT10为什么提高性能”列为明日首要计划。

本次只更新[s-target](../../../s-target.md)、[当前总结](../../../summary.md)、[历史概览](../../../s-experiment.md)和[历史13接续说明](../../13_gt_topk_profiles.md)。计划状态`GT10_MECHANISM_ANALYSIS_PLANNED_UNRUN`；没有开始新归因分析、搜索、训练或补测，不增加实验ID。

主对照为两数据集GT10 hard与matched GT1 hard。先核清性能增益和重复性，再沿目标归属、画像、三入口、主搜索和总wall逐层解释。缺失证据才安排独立小协议补测；长期2A等放到机制解释之后选择。E25/E26的75%/25%是后续增强目标，不能否定E24原有正信号。

[修改前快照](source_before/s-target.md)、[完整差异](changes.diff)、[修改前身份](before.json)、[文档验收](document_checks.json)保留优先级调整过程。spec与AGENTS逐位未改；E24/E25/E26的协议、结果、报告、状态与封存验收保持不变，其旧文档身份对应封存时刻，本次变更由此独立记录。
