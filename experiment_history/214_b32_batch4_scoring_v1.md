# E214 四集 B32 候选四路精算

2026-11-21 完成。COCO、Flickr30k、WebVid、Yandex first10M 各使用 E212 的公共前 3,072 条。真实 K1/K100 各 7 档 L，CPU15 实际单线程，两遍完整 wall。纯 GT10、原 B32 与候选四路 B32 共用 E211 SPAN4 主图。168 点、336 批、1,032,192 次正式查询。

四路版原表、去重和候选顺序沿原实现，分组调用原生 Faiss 四路距离，尾部标量计算，沿原严格 Top-K 比较合并。14,336 条资格查询的 1,323,084 个补点分数逐位一致。两条 B32 的 56 组正式返回全部逐字节相同，112 个 GT10 或原 B32 包与 E212 字节一致。

四路 B32 完整 QPS 相对原版的范围为 −0.52% 至 +2.44%，中位数 +0.35%。均值更快 48/56，四路慢遍快于原版快遍 34/56，四路快遍慢于原版慢遍 3/56。COCO K1 和 WebVid 两种 K 的中位数分别为 +0.76%、+1.23%、+0.91%，Yandex 两种 K 分别为 −0.08%、+0.10%。L200 补点重放中 WebVid K100 由 17.13 降至 14.60 微秒/query，重放和完整搜索后的缓存条件各自解释。

固定同 L，四路版相对纯 GT10 的完整 QPS 低 0.48%–7.47%。WebVid 的 Recall@100 目标 80% 下，纯 GT10 L400 为 81.576% / 868.0 QPS，原 B32 L320 为 80.801% / 1,030.1，四路 B32 L320 为 80.801% / 1,039.4。当前证据支持将四路保留为等价工程候选。各数据集是否用补点继续按实际达标配置决定。

[报告](../entry_method_exploration/20261121_b32_batch4_scoring_v1/report.md) · [预锁协议](../entry_method_exploration/20261121_b32_batch4_scoring_v1/protocol.md) · [候选分数核验](../entry_method_exploration/20261121_b32_batch4_scoring_v1/analysis/candidate_score_parity.csv) · [独立复算](../entry_method_exploration/20261121_b32_batch4_scoring_v1/reviews/independent_audit.json) · [状态](../entry_method_exploration/20261121_b32_batch4_scoring_v1/state.json)。
