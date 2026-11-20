# ACSG 当前结论

E212 四个真实数据集各3072条，真实 K1/K100 各7个 L。224点448批。同表的新 GT10+B32 相对旧 GT10+B32 56组返回逐字相同，完整 QPS 变化 +13.43% 至 +27.54%。固定同 L 补点平均 Recall 增加 52/56 点，完整 QPS 降低 56/56 点。 [E212 四集对比](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/report.md)。

默认标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 使用 E211 SPAN4。L2 等路径使用标量。显式标量回退调用 `acsg.set_flat_ip_batch4_enabled(false)`，在启动查询线程前设定。画像的配置以冻结输入为准。

E212 的 NSG 和新 GT10 使用同一 SPAN4，分别采用图的固定单入口和画像三入口。完整 B32 的部署取舍依据同内核两条曲线及实际达标配置。新旧 B32 的比较衡量主搜索内核的提速。

[E212 逐配置](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/analysis/same_l.csv) · [E212 门槛表](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/analysis/recall_thresholds.csv) · [E211 默认切换](entry_method_exploration/20261120_span4_production_default_v1/report.md) · [修改前文档](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/source_before/)。

[E210 独立适配](experiment_history/210_span4_four_dataset_retest_v1.md)、[E209 两窗](experiment_history/209_webvid_b32_span_confirmation_v1.md)、[E208 四集补点](experiment_history/208_b32_equivalent_speed_v1.md)及历史证据按原配置索引。旧数据范围见[存储简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。
