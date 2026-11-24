# E250 COCO 97% 同期复测

对 E245/E248 相同返回的时延波动做复测。冻结 E248 最佳召回单 L176、最快单 L192、多档 Mixed64，另保留原 B32 与老 B64。沿原 E229 的 3,072 个确认源组，8 档 L、真 K100、40 点、80 个完整 CPU15 单线程批次，共同历史原生字段逐一相同。

97% 目标，B32 L216 为 2,376.8 QPS，老 B64 L204 为 2,429.1。Single176、Single192 和 Mixed64 均在 L196 达标，完整 QPS 2,488.5、2,487.7、2,489.6，相对老版 +2.44%/+2.41%/+2.49%。慢遍对老版快遍 +1.88%/+2.12%/+2.33%。同 L 下，Single176 八档均多于 Mixed64 共 5–21 个正确成员。多档对单档的目标速度基本持平。此轮确认 E245 的 COCO 目标收益，同时保留 E248 的时延波动作为边界。

[完整报告](../entry_method_exploration/20261123_coco_b64_target_retest_v1/report.md) · [协议](../entry_method_exploration/20261123_coco_b64_target_retest_v1/protocol.md) · [同期逐点](../entry_method_exploration/20261123_coco_b64_target_retest_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_coco_b64_target_retest_v1/seal.json)
