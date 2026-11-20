# E207 原 B32 补点分段计时

2026-11-20 完成。COCO hard 和 WebVid soft-t1，各取公共10K的前3,072条，真实 K1/K100，L100/200/400。12个配置、48个正常批次和24个分段批次，合计221,184次计时查询。CPU15单线程，每点两遍。12个配置中，额外精算均是最大的残差阶段，占分段残差时间的60.6%–94.2%。K100/L200下，COCO/WebVid的额外精算为14.55/22.01微秒/query，查表去重1.97/2.51，合并5.29/6.07。同一配置下，COCO/WebVid可直接复用并排除的主池尾部候选为3.10/0.69个/query，全部候选未过原第K名门槛的查询占36.4%/34.8%。

重用同一份 GT10/原图、完整16K B32 和原始 raw-IP。阶段包括查表去重、额外精算和原合并。正常计时与分段计时独立，另做诊断计数，全部分段/诊断实际返回和原 B32 逐字节一致。结果另由原公共 GT 与返回包复算。先前一次编译失败原件留在 [first_build](../entry_method_exploration/20261120_b32_stage_cost_v1/reviews/first_build/)，修正诊断器的 Posting 引用限定符并排除搜索池的额外暂存槽后才开始计时。

[报告](../entry_method_exploration/20261120_b32_stage_cost_v1/report.md) · [协议](../entry_method_exploration/20261120_b32_stage_cost_v1/protocol.md) · [实测](../entry_method_exploration/20261120_b32_stage_cost_v1/analysis/summary.csv) · [状态](../entry_method_exploration/20261120_b32_stage_cost_v1/state.json) · [验收](../entry_method_exploration/20261120_b32_stage_cost_v1/reviews/delivery_validation.json)
