# E219 漏点 ID 粗排与 B32 尾部保留

2026-11-21，COCO K100、WebVid K1/K100。原桶复用并对最接近的两/四张表的实际候选做 512D int8 内积，与原 B32 尾部同筛，最多交换 16 个，逐查询保持原精算数。

三场景过 L192 回放门。第二公共窗完成 主网格 162 点、324 批，加密 60 点、120 批，CPU15 单线程。主网格 COCO K100 最佳同召回 QPS 差 +3.62%，慢遍仍快 2/8 点。WebVid K1 最佳同召回 QPS 差 +0.33%，慢遍仍快 1/9 点。WebVid K100 最佳同召回 QPS 差 +2.66%，慢遍仍快 2/8 点。局部加密 COCO K100 Q8-2 L224 相对加密最快达标控制 -0.95%。WebVid K100 Q8-4 L232 相对加密最快达标控制 -2.22%。生产默认按 E99/E211 合同。正式控制同批包括 GT10、完整与 fit-B32、CACHE 和 BKT8，计入全部在线开销。

[报告](../entry_method_exploration/20261121_bucket_id_reranking_v1/report.md) · [协议](../entry_method_exploration/20261121_bucket_id_reranking_v1/protocol.md) · [实测匹配点](../entry_method_exploration/20261121_bucket_id_reranking_v1/analysis/matched.csv) · [状态](../entry_method_exploration/20261121_bucket_id_reranking_v1/state.json)。
