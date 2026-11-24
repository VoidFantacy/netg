# E222 B32 组内联合短尾表

2026-11-22 完成 COCO、WebVid 的真实 K100，固定原 GT10 三入口、图、SPAN4 和 B32-fit 前缀。按会选中同一代表的训练查询聚合，从组内真实遗漏并集以最终 Top-K 净命中贪心构建 8/16 位短表。留出与公开查询均只读取一张短表，每个新增候选替换等量原尾部，实际精算预算与 B32-fit 配平。

7,953 个冻结查询状态完成开发和校准回放，15,906 行独立标量全排序核对。SHORT16 校准净增 COCO 33、WebVid 35 个，较 L192 分别缺 379、1,314 个。单组选中后，全候选乐观覆盖上限 768/4,829，16 位短表只覆盖 62/116。两个场景均核对旧候选中不存在 B32 最终遗漏的正确成员。该覆盖上限忽略损伤与最终精算排序。

两集各 11 档 L、六个方法，132 点、264 批和 811,008 次正式查询，CPU15 单线程两遍，第二公共窗已用于历史比较。两个短表的 44 个点全部被同期强控制覆盖。COCO 最接近的 SHORT8 L188 为 96.1797% / 2,377.5 QPS，完整 B32 L188 为 96.2786% / 2,401.6 QPS。WebVid 最接近的 SHORT16 L192 为 73.8734% / 1,908.6 QPS，完整 B32 L192 为 73.9990% / 1,916.0 QPS。原版 B32 继续作补点基线，生产用 E99/E211 合同。

[协议](../entry_method_exploration/20261122_joint_residual_tail_v1/protocol.md) · [报告](../entry_method_exploration/20261122_joint_residual_tail_v1/report.md) · [回放](../entry_method_exploration/20261122_joint_residual_tail_v1/analysis/replay.csv) · [覆盖](../entry_method_exploration/20261122_joint_residual_tail_v1/analysis/coverage.csv) · [完整指标](../entry_method_exploration/20261122_joint_residual_tail_v1/analysis/points.csv) · [状态](../entry_method_exploration/20261122_joint_residual_tail_v1/state.json) · [封存](../entry_method_exploration/20261122_joint_residual_tail_v1/seal.json)
