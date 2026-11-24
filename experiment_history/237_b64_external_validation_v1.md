# E237 WebVid 新 B64 异源验证与高召回

在取得验证结果以前按 E243 公共确认的正结果冻结 More64 与 Mixed64，保留 E234 单分数门、B32、老 B64。原仅门控的未执行协议留档。WebVid seed20260826 validation 的物理行 0–3071，3,072 条与公共 test10K、原画像拟合、全部 E243 训练按精确字节排重。原 exact raw-IP GT，真实 K100、23 档 L144–960、115 点、230 批两遍 CPU15 单线程完整计时。

75.5% 门槛，Mixed64 L208 为 75.5915% / 1,622.1 QPS，老 B64 L216 为 75.7790% / 1,569.2，达标 QPS +3.37%，慢遍对快遍 +3.30%。相对 B32 L224 加速 +3.89%。同样本 More64 在这个门槛 75.5677% / 1,624.6，较老 B64 +3.53%。E234 CutoffGate 同目标较老版 +0.46%。

Mixed64 的 14 个可比目标中均值 13 个快，慢遍 9 个快。按重叠实测折线，Mixed64 相对老 B64 22/22 点更快，描述性中位 +2.05%，同 L 完整 QPS 中位 +0.07%。高召回离散网格较粗。84% 固定目标跨过 L440 到 L560 的 +24.19% 是实际采样点比较，同召回折线读数约 +2.04%，不作为普遍速度。Mixed64 L960 达 90.0765%，同期老 B64 在已有网格未过 90%。

[完整报告](../entry_method_exploration/20261123_b64_external_validation_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_external_validation_v1/protocol.md) · [逐点](../entry_method_exploration/20261123_b64_external_validation_v1/analysis/points.csv) · [目标](../entry_method_exploration/20261123_b64_external_validation_v1/analysis/targets.csv) · [折线](../entry_method_exploration/20261123_b64_external_validation_v1/analysis/matched.csv) · [封存](../entry_method_exploration/20261123_b64_external_validation_v1/seal.json)
