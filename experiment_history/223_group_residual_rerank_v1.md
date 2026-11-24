# E223 单组全池逐查询残差交换

2026-11-22，COCO 和 WebVid 真 K100 的 E222 冻结组池及 E206 L184 主返回用于原始内积回放。新候选和原 B32-fit 可换尾部按分数最多交换 16 个，保留公共前缀，最终实际精算数逐查询一致。两集共 7,953 状态，COCO 开发/校准净增 771/768，WebVid 4,538/4,829，四窗均实现 E222 的单组覆盖上限且无损伤。额外全池原向量评分单计。

COCO 在同池使用 E216 32/64 维正交 PCA 粗分。32 维校准净增 465、64 维 614，所需 412。两臂均通过开发和校准窗，进入 COCO 11 档 L、六臂、66 点、132 个 CPU15 单线程完整计时批次。L184 的 P64 为 96.3617% / 2,750.4 QPS，Q8-cert 同 L 为 96.3561% / 2,730.3 QPS。按同期最快达标对照，P32 在 3/11 点均值快、1/11 点慢遍仍快，P64 为 1/11 和 1/11。P64 L200 为 96.7607% / 2,531.1 QPS，对同期 Q8-cert L208 的 96.9202% / 2,500.6 QPS 高 1.22%。公开查询窗已有历史使用。保留 COCO K100 条件候选及原 B32 补点基线。

[预锁协议](../entry_method_exploration/20261122_group_residual_rerank_v1/protocol.md) · [报告](../entry_method_exploration/20261122_group_residual_rerank_v1/report.md) · [全精度回放](../entry_method_exploration/20261122_group_residual_rerank_v1/analysis/exact.csv) · [低维回放](../entry_method_exploration/20261122_group_residual_rerank_v1/analysis/projection.csv) · [同期达标对照](../entry_method_exploration/20261122_group_residual_rerank_v1/analysis/matched.csv) · [冻结状态](../entry_method_exploration/20261122_group_residual_rerank_v1/state.json) · [封存](../entry_method_exploration/20261122_group_residual_rerank_v1/seal.json)
