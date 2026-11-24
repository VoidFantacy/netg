# E221 Q8 粗分安全跳过精算

2026-11-21 使用 E220 同候选和精确合并，以 Q8 粗分加原向量范数、量化重建误差及舍入余量建立上界。只有候选上界低于主返回第 K 名才免原精算；最终结果逐字节一致。11,952 个回放原精算 1,098,596 个，出具 233,695 个拒绝见证。

真实 COCO K100、WebVid K100 及基于回放追加的 WebVid K1 共 107 点、214 CPU15/T1 完整批次。COCO K100 L224 相对 Q8-fast -0.00%，相对同期达标控制 -0.38%，L232 对同期达标控制 -0.67%。WebVid K100 L232 相对 Q8-fast +0.25%，相对同期达标控制 +0.56%，L224 对同期达标控制 +0.25%。WebVid K1 L208 相对 Q8-fast +1.68%，相对同期达标控制 +2.88%，L216 对同期达标控制 +2.31%。

[报告](../entry_method_exploration/20261121_q8_certified_pruning_v1/report.md) · [协议](../entry_method_exploration/20261121_q8_certified_pruning_v1/protocol.md) · [达标结果](../entry_method_exploration/20261121_q8_certified_pruning_v1/analysis/matched.csv) · [状态](../entry_method_exploration/20261121_q8_certified_pruning_v1/state.json)。
