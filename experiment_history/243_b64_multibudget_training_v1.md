# E243 WebVid B64 扩训练与多预算遗漏监督

以原 GT10 soft-t1、原图、发布 SPAN4 和原有序 B32 为底。训练从原 E183 16,000 条增加到 24,192 条。新 8,192 条来自 WebVid router_train.seed20260826，逐向量字节避开完整原 20,000 画像拟合、公共测试及 seed 验证，包括训练内排重。它们与确认窗互斥。真实 K100 在 L176/192/200/208 得到 96,768 个主搜索状态。More64 用单 L200；Mixed64 用 L176、192、208，按实际 query–L–target 遗漏事件计联合覆盖。两者以同原生 E226 编译器延长原有序 B32 前缀。统一在线 raw-IP，三路原 ID 次序去重、原生精算与严格合并。Mixed52 为 Mixed 表最远路 52 对照。原报告的开发窗表述沿用模板，此轮没有在 E231 开发查询上拟合或校准。

WebVid 真 K100 确认窗 3,072 条，90 点、180 完整 CPU15 单线程批次。75.5% 目标，原 B32 L216 1,630.7 QPS，老 B64 L204 1,665.4。单预算新表 L200 75.5641% / 1,686.8，提升 +1.28%，慢遍仍 +0.86%。多预算新表 L200 75.5824% / 1,696.1，提升 +1.84%，慢遍仍 +1.81%。相对 B32 +4.01%。Mixed64 同 L 对老 B64 在 15 档召回均增加 0.2770–0.3281 个百分点，平均精算数少约 1.25 个/查询，中位完整 QPS 差 +0.09%。L200 救回 1,861、损伤 928、净增 933 个正确成员。八个固定目标均值全快，七个慢遍仍快，14 个重叠折线点均更快。Mixed64 同 L 对同样本 More64 多 48–80 个正确成员，完整 QPS 同 L 中位差接近零。主要收益来自候选覆盖与降低 L。

原旧尾表与扩样本单 L 的对照为样本覆盖变化，多 L 与单 L200 的对照同时改变有效训练深度。要判断多 L 本身的贡献，另测同样本单 L176、192、208。此结果证据限于当前身份互斥的历史公共确认窗，需在独立 seed 验证和其它数据集复核。

[完整报告](../entry_method_exploration/20261123_b64_multibudget_training_v1/report.md) · [协议](../entry_method_exploration/20261123_b64_multibudget_training_v1/protocol.md) · [训练身份](../entry_method_exploration/20261123_b64_multibudget_training_v1/models/train/roles.json) · [同期逐点](../entry_method_exploration/20261123_b64_multibudget_training_v1/analysis/points.csv) · [封存](../entry_method_exploration/20261123_b64_multibudget_training_v1/seal.json)
