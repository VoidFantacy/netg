# ACSG 下一阶段目标与接续

2026-09-13，今日campaign持续目标为21:00前完成现有方法改进与同机单线程QPS–Recall/失败查询图表。当前首阶段E60已完成，双集支持0/40，停止同一局部行随机动作的连续扩大；全天目标未完成。

1. 优先探索完整P-fit20K上的实际遗漏GT10成员驱动画像聚合：保持原hard/soft raw-hub归属与每query质量1，固定一个强度，将GT10等权归属与遗漏成员平均归属混合；同时固定每query遗漏数量、随机化目标身份作机制控制。先核验完整基线反馈复用键、lambda0恢复和历史E08/E09/E22实质差异，再独立实现/锁定/实际评估。当前这里只是待实现下一阶段，不自动继承旧反馈到变更后模型。
2. 若出现开发收益，按实际gain/loss/零命中与代价检查能否迁移，固定候选后安排正式五L、五轮纯端到端wall。否则保存负结果并据覆盖/目标身份控制结果决定新方向，不扫大量同类随机方向/步数。历史cal和audit均已再次使用，不宣称未观察或盲集；E34历史validation2000只用于冻结候选的最终比较，反馈不回流训练/选型。
3. 每个主要阶段完成即写独立报告、state/handoff和下一命令。当前会话最迟10:15安全退出且无遗留native进程，监督者负责串行切换。今日建议20:00停止新训练、20:40停止新增查询、21:00交付，至少最后一小时用于冻结候选与NSG/Fast/FastGT10及匹配起点的QPS–Recall、严格GT10零命中失败率图和独立验收。

保持原base/raw-IP/NSG/GT及H815/821。正式所有方法CPU15、threads=1及OMP/BLAS/MKL1、单方法串行、整批纯wall，多次重复；GT/计数/序列化不入timer，aligned逐query保存。构建/路由/NSG/缓存分别收费。/data初始约8GiB，输出保守限额且不删除历史。

[E60报告](entry_method_exploration/20260913_until2100_v1/stage1_support_v1/report.md)、[campaign状态](entry_method_exploration/20260913_until2100_v1/state.json)、[交接](entry_method_exploration/20260913_until2100_v1/handoff.md)。昨天[next design](entry_method_exploration/20260912_until2000_v1/closeout/next_experiment_design.md)保留设计原件，本日E60是其独立继任实测，不回写昨日封存。
