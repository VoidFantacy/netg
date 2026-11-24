# E246 WebVid K100 训练表到真 K1

直接冻结 E243 的 More64 与 Mixed64，无 K1 拟合。原 GT10 soft-t1、发布 SPAN4、图、raw-IP、原 B32 有序前缀、老 B64 及 E230 均匀 B56 作同期控制。用 E231 的 3,072 条确认身份，按原 GT100 第一名评分。主搜索、补点合并和返回均以 K1 执行。原报告中的开发窗描述为模板延续，E246 的正式计时只有一个确认窗。17 档 L、85 点、170 个 CPU15 单线程完整批次，两遍返回逐字一致。

84% 目标，B32 L200 为 1,762.9 QPS，老 B64 L184 为 84.2773% / 1,840.1。Mixed64 L168 为 84.3099% / 1,984.5，比老 B64 +7.85%，慢遍对快遍仍 +7.79%。More64 同 L 为 84.1797% / 1,983.3。Mixed64 在全部重叠曲线 16/16 点更快，中位 +6.30%。十个固定目标中八个均值快，六个慢遍快。在 80% 和 81% 达标固定 L 相同，收益约为 −0.16% 和 −0.07%，保留局部持平和负点。L200 同样精算规模，Mixed64 85.6120%，老 B64 85.0586%。

[完整报告](../entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/report.md) · [协议](../entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/protocol.md) · [逐点](../entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/analysis/points.csv) · [目标比较](../entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/analysis/targets.csv) · [封存](../entry_method_exploration/20261123_webvid_k1_b64_trained_table_v1/seal.json)
