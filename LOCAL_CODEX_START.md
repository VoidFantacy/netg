# ACSG 本地 Codex 入口

2026-11-20 完成 E211 并切换默认。标准 Flat raw-IP 的 `ACSG::search_new(mode=2)` 默认走 SPAN4，L2 等其他距离路径走标量。四个真实数据集各3,072条，真实K1/K100各7个L，224点、448个完整CPU15单线程批次。112个新旧配对返回逐字节相同，112/112个配对通过逐点速度筛选。纯GT10完整QPS变化+13.74%至+28.35%，GT10+B32变化+13.16%至+27.94%。 当前无待恢复实验。

最新四方法实测。E212 四个真实数据集各3072条，真实 K1/K100 各7个 L。224点448批。同表的新 GT10+B32 相对旧 GT10+B32 56组返回逐字相同，完整 QPS 变化 +13.43% 至 +27.54%。固定同 L 补点平均 Recall 增加 52/56 点，完整 QPS 降低 56/56 点。 [E212 四集对比](entry_method_exploration/20261120_gt10_nsg_b32_four_way_v1/report.md)。

先读 AGENTS、summary、spec、s-target、s-experiment，再读 [E211 报告](entry_method_exploration/20261120_span4_production_default_v1/report.md)、[E211 历史卡片](experiment_history/211_span4_production_default_v1.md)、[状态](entry_method_exploration/20261120_span4_production_default_v1/state.json)及[发布验证](entry_method_exploration/20261120_span4_production_default_v1/reviews/release_dispatch.json)。

后续 raw-IP GT10 性能实验链接新构建的 ACSG 或使用[发布构建记录](entry_method_exploration/20261120_span4_production_default_v1/release/build.json)。查历史实验时使用其冻结二进制。[切换前源码与文档](entry_method_exploration/20261120_span4_production_default_v1/source_before/)及[旧数据简档](experiment_history/_maintenance/20261119_obsolete_payload_prune_v1/archive_index.md)。

GitHub 阅读入口与数据依赖见[发布快照](research_snapshots/20261120_e211_e212/README.md)。
