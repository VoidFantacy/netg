# ACSG 本地 Codex 入口

2026-11-20 完成 E210。COCO、Flickr30k、WebVid、Yandex first10M 四集各3,072条真实公开查询。真实K1/K100，各7个L，224点、448个完整CPU15单线程批次、1,376,256次正式查询，每点两遍。112个优化点返回与各自对照逐字节一致。纯GT10 QPS变化+12.64%至+30.40%，56/56点过预设筛选。接完整B32变化+11.75%至+29.65%，56/56点过筛选。四集全部已测同L预算支持内核替换候选。生产发布合同仍为E99 GT10。 当前无待恢复实验。

先读 AGENTS、summary、spec、s-target、s-experiment，再读 [E210 报告](entry_method_exploration/20261120_span4_four_dataset_retest_v1/report.md)、[卡片](experiment_history/210_span4_four_dataset_retest_v1.md)、[状态](entry_method_exploration/20261120_span4_four_dataset_retest_v1/state.json)和[验收](entry_method_exploration/20261120_span4_four_dataset_retest_v1/reviews/delivery_validation.json)。

旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。修改前根文档见[source_before](entry_method_exploration/20261120_span4_four_dataset_retest_v1/source_before/)。
