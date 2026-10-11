# E174：沿 M5 候选扩展局部区域

当前状态：正式测量运行中。原 M5 保留，主方法为预锁 M5REG96；尚无本轮 Recall/QPS 结论。生产默认仍为 GT10。

原 M5 用训练查询的漏召回目标建立条件候选表，本轮保持完整 C 与旧合并，并把 C 中的 query-best 候选作为原 NSG 一跳区域的种子，以额外 24/96 个评分发现表外 ID。新增 TRAIN 为零。

- [冻结协议](protocol.md)与[参数锁](parameter_lock.json)
- [实际运行状态](run_state.json)
- [与原 M5 的关系](m5_relationship.md)、[代价与收益推导](theory_interpretation.md)、[分析字段范围](analysis_schema.md)
- [数据身份](reviews/data_preflight.json)、[运行前核验](reviews/preexecution_acceptance.json)
- [独立源码审查](reviews/native_source_independent_review.json)、[分析与执行器审查](reviews/analysis_runner_review.json)
- [详细历史记录](../../experiment_history/174_m5_residual_regions.md)

预锁两集、K1/K100、各两档 L，pilot 九方法、confirm 五方法，共112点336轮。所有计时结束后才读取角色 GT 做质量评价；不根据响应重新选择参数。全量返回/replay/oracle 与固定256计数分开报告，timed 每轮返回不留存，不把 untimed words 写作 timed words 证据。
