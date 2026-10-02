# ACSG 下一阶段目标与接续

2026-09-13，今日campaign持续目标为21:00前完成现有方法改进与同机单线程QPS–Recall/失败查询图表。当前首阶段E60已完成，双集支持0/40，停止同一局部行随机动作的连续扩大；全天目标未完成。

1. E61全fit遗漏成员画像已实际完成，双集cal失败，禁止继续同公式lambda/随机seed网格。最小下一控制固定E61 missing端点，补S=(W_missing,G0)、T=(P,G_missing)，检查原全命中群14/20条新增零命中的评分/拓扑来源；回查E48/E54原协议、API及结果，使用独立版本。当前此S/T控制未运行。
2. 若交叉状态的cal有净正、失败数不增、totalNDC≤+1%，按预锁规则冻结候选，audit只报告迁移，不回流调参；无合格者保留原P，不扩参数网格。根据真实四格交互决定保护或表示修改，不能用E61分组直接自称因果。正式五L五轮纯wall留给冻结候选；历史cal/audit均重复暴露，E34历史validation2000只用于最终比较，反馈不回流训练/选型。
3. 每个主要阶段完成即写独立报告、state/handoff和下一命令。当前会话最迟10:15安全退出且无遗留native进程，监督者负责串行切换。今日建议20:00停止新训练、20:40停止新增查询、21:00交付，至少最后一小时用于冻结候选与NSG/Fast/FastGT10及匹配起点的QPS–Recall、严格GT10零命中失败率图和独立验收。

保持原base/raw-IP/NSG/GT及H815/821。正式所有方法CPU15、threads=1及OMP/BLAS/MKL1、单方法串行、整批纯wall，多次重复；GT/计数/序列化不入timer，aligned逐query保存。构建/路由/NSG/缓存分别收费。/data初始约8GiB，输出保守限额且不删除历史。

[E60报告](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/report.md)、[campaign状态](entry_method_exploration/20260913_until2100_v1/state.json)、[交接](entry_method_exploration/20260913_until2100_v1/handoff.md)。昨天[next design](entry_method_exploration/20260912_until2000_v1/closeout/next_experiment_design.md)保留设计原件，本日E60是其独立继任实测，不回写昨日封存。
