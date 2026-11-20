# ACSG 当前结论

2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，224点、448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。

GT10 画像沿各数据集原配置。启用完整 B32 时同样调用 SPAN4 主搜索，补点收益继续按实际 Recall–QPS 判断。候选池与 visited 配对、同索引并发调用、边修改和三套 L2 的标量分流均通过核对。显式回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，查询开始前设定。

[E211 报告](entry_method_exploration/20261120_span4_production_default_v1/report.md) · [逐配置配对](entry_method_exploration/20261120_span4_production_default_v1/analysis/matched_deltas.csv) · [E211 历史卡片](experiment_history/211_span4_production_default_v1.md) · [切换前源码与文档](entry_method_exploration/20261120_span4_production_default_v1/source_before/)

[E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md)、[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)、[E207 分段](experiment_history/207_b32_stage_cost_v1.md)及历史条件收益按原范围保留。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
