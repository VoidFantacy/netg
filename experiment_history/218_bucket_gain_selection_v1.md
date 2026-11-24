# E218 入口桶净收益选择与双表动作

2026-11-21 完成。三折按 identity 隔离并重编 B32、BKT8 代表和预编漏点。COCO K100 和 WebVid K1 共有 24,047 个标签状态、509,823 个真实精确合并动作，冻结后另回放 7,953 个 dev/cal 状态。三版线性预测只用 fit 动作的最终净命中标签，在线最多选一张表，允许保留 B32。两组均无完整计时资格。COCO K100 摘要版校准净增 +206，原桶 +199，L192 所需 +412；WebVid K1 摘要版校准 +3，原桶 +6，所需 +7。

WebVid K100 固定短名单另枚举 949,006 个同预算双表动作。含双表的上限在 dev/cal 相对 B32-fit L192 分别多 +238/+59 个正确成员，单表是 +52/−129。上限使用 GT，仅限离线。正式点 0。

[报告](../entry_method_exploration/20261121_bucket_gain_selection_v1/report.md) · [协议](../entry_method_exploration/20261121_bucket_gain_selection_v1/protocol.md) · [完整补点回放](../entry_method_exploration/20261121_bucket_gain_selection_v1/analysis/replay.csv) · [双表上限](../entry_method_exploration/20261121_bucket_gain_selection_v1/analysis/double_table.json) · [状态](../entry_method_exploration/20261121_bucket_gain_selection_v1/state.json)。
