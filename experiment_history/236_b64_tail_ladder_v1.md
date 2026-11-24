# E236 WebVid 第三路单分数分档

固定 E231 WebVid GT10 soft-t1、SPAN4、真 K100、B32 与原 B64 有序行。按已有主结果第 100 名负内积分箱，以实际同档的成员净增和额外精算数做有序深度动态规划。训练允许六档 40/48/52/56/60/64，最终校准冻结动作只有 40 和 64。在 E234 同身份校准中，相对固定 Far40 多精算 72,564 个、多命中 593 个。固定 Far52 多精算 83,950 个、多命中 436 个。该策略是另一个预算更紧的二档截止分。

确认窗 3,072 条，75 点、150 批 CPU15 单线程完整计时。75.5% 目标在 L208 为 75.6976% / 1,636.6 QPS，比老 B64 L204 慢 1.57%。74.5% 同 L192 比老 B64 快 0.49%，慢遍对快遍 +0.32%。全重叠折线 10/14 个点更快，中位差 +0.11%。按召回目标保留条件证据，第三路扩成更多档位没有获得额外质量收益。

[完整报告](../entry_method_exploration/20261123_b64_tail_ladder_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_tail_ladder_v1/protocol.md) · [校准](../entry_method_exploration/20261123_b64_tail_ladder_v1/models/calibration.json) · [同期逐点](../entry_method_exploration/20261123_b64_tail_ladder_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_tail_ladder_v1/seal.json)
