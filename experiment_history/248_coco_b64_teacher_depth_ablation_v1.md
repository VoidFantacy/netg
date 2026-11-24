# E248 COCO 同样本监督深度消融

与 E245 严格相同的 20,096 条训练、实际四档 L 主包和 exact GT。用 E226 原联合贪心编译器及原 B32 有序前缀得到四种单档表，保留 E245 冻结的多档表、原 GT10 hard 与 SPAN4。E245 同一套 3,072 个确认源组，7 档真实 K100、49 点、98 个 CPU15 单线程完整批次。全部 28 个对应历史输出字段包相同。重跑原 16,000 条 L200 的 ID、原分数、入口、画像与 E183 历史逐字一致。

所有七档在线 L 中，最佳单档均为 Single176。Mixed64 对它少 9–22 个正确成员。L196 两者分别 97.0254% 和 97.0283%，均过 97%。L192 单档在同 L 为 97.0029%。该轮 97% 最快均值是 Single192 L196 2,456.9 QPS，相对同期老 B64 L204 为 +1.28%，慢遍对快遍 −0.44%。Mixed64 的原生结果与 E245 相同，其 L196 本轮为 2,408.9 QPS，前轮 2,488.9。同期本轮最快达标实点落在 L204，较老 B64 −0.22%。同样本质量结果支持低 L 单档，COCO 的速度收益估计须看复测波动。

[完整报告](../entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/report.md) · [协议](../entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/protocol.md) · [原主包核对](../entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/analysis/original_training_l200_parity.json) · [同期逐点](../entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_coco_b64_teacher_depth_ablation_v1/seal.json)
