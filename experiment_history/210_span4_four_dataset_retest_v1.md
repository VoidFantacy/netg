# E210 四真实数据集 SPAN4 复测

2026-11-20 完成。COCO、Flickr30k、WebVid、Yandex first10M 四集各3,072条真实公开查询。真实K1/K100，各7个L，224点、448个完整CPU15单线程批次、1,376,256次正式查询，每点两遍。112个优化点返回与各自对照逐字节一致。纯GT10 QPS变化+12.64%至+30.40%，56/56点过预设筛选。接完整B32变化+11.75%至+29.65%，56/56点过筛选。四集全部已测同L预算支持内核替换候选。生产发布合同仍为E99 GT10。

以E209研究内核在E208相同四数据资产上复验。纯主搜索与原B32均按同图、同入口、同L匹配。两遍完整墙钟、逐字节输出、四路距离评分和附加span字节均核验。历史结果只作为可对齐前缀控制。结论适用本轮真实公开前3072条及原raw-IP图。

[报告](../entry_method_exploration/20261120_span4_four_dataset_retest_v1/report.md) · [协议](../entry_method_exploration/20261120_span4_four_dataset_retest_v1/protocol.md) · [速度配对](../entry_method_exploration/20261120_span4_four_dataset_retest_v1/analysis/matched_deltas.csv) · [状态](../entry_method_exploration/20261120_span4_four_dataset_retest_v1/state.json) · [验收](../entry_method_exploration/20261120_span4_four_dataset_retest_v1/reviews/delivery_validation.json)
