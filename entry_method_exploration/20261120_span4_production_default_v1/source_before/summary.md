# ACSG 当前结论

2026-11-20 完成 E210。COCO、Flickr30k、WebVid、Yandex first10M 四集各3,072条真实公开查询。真实K1/K100，各7个L，224点、448个完整CPU15单线程批次、1,376,256次正式查询，每点两遍。112个优化点返回与各自对照逐字节一致。纯GT10 QPS变化+12.64%至+30.40%，56/56点过预设筛选。接完整B32变化+11.75%至+29.65%，56/56点过筛选。四集全部已测同L预算支持内核替换候选。生产发布合同仍为E99 GT10。

SPAN4 只改原图的主搜索执行，原 GT10 入口、B32 补点和精确返回保持身份。速度是 CPU15 单线程当前两遍完整链路，同 L 质量已逐字节核验。补点选择与内核提速作为两个决策，召回门槛取本轮离散预算。E209 的 PF4 确认结果保留。

[E210 报告](entry_method_exploration/20261120_span4_four_dataset_retest_v1/report.md) · [四集相对速度](entry_method_exploration/20261120_span4_four_dataset_retest_v1/analysis/speed_delta.png) · [逐配置配对](entry_method_exploration/20261120_span4_four_dataset_retest_v1/analysis/matched_deltas.csv) · [历史卡片](experiment_history/210_span4_four_dataset_retest_v1.md) · [本轮前根文档](entry_method_exploration/20261120_span4_four_dataset_retest_v1/source_before/)。

[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)、[E207 分段](experiment_history/207_b32_stage_cost_v1.md)及历史条件收益按原范围保留。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
