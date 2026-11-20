# E209 WebVid 补点预取和主搜索内核

2026-11-20 完成。WebVid soft-t1 两个各2,048条查询窗口，真实K1/K100、L100/200/400，K100另测L960。71个点、142个单线程完整批次、290,816次正式查询，每点两遍。E208三个连续正向组合中0个按冻结口径在确认窗复现。SPAN4＋原B32 的完整 QPS 各点提升16.96%至22.24%，两个窗口同通过的预算为7/7。全部优化点与现用控制逐字节一致。默认 E99 GT10。

E194角色去重确认窗和公共前2048条分别比较。SPAN4沿 E102 原搜索体、当前原图及同存储，补点只用完整B32与E208固定工程版。冻结两遍完整壁钟，核算返回、附加内存、真实四路精算转发及历史可对齐前缀。原默认按项目合同。

[报告](../entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/report.md) · [协议](../entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/protocol.md) · [同期完整结果](../entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/analysis/points.csv) · [状态](../entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/state.json) · [验收](../entry_method_exploration/20261120_webvid_b32_span_confirmation_v1/reviews/delivery_validation.json)
