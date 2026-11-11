# 2026-11-11 研究同步

本次同步包含截至2026-11-10的现行根文档、E184–E200相关协议/实现/汇总结果/审计，以及2026-11-05的PDF与COCO失败查询修订。默认仍为E99 GT10，没有新增实验。

先读[当前接续入口](../../LOCAL_CODEX_START.md)、[当前结论](../../summary.md)、[实现合同](../../spec.md)。

- 最新实测：[E200报告](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)、[640点](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/points.csv)、[两轮完整计时](../../entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/rounds.csv)。
- 本对话修订：[8页PDF](../../reports/20261105_method_benefits_limits_v3/ACSG_当前方法_残差收益_低召回修复与局限_20261105.pdf)、[修订说明](../../reports/20261105_method_benefits_limits_v3/README.md)。收益图去掉A/B浅线，合并数字保持原样。
- COCO严重失败：L200原NSG→GT10→B32为0→1→1；同一查询命中97→3→3。新增发生于GT10阶段，B32未新增也未救回。[逐查询复核](../../reports/20261105_method_benefits_limits_v3/reviews/coco_raw_audit.json)。
- 方法定位：[论文写作约定](../../论文写作约定.md)；当前流程为GT10加直接B32，双塔/导航/残差门的停止边界保持。

2026-11-05的PDF是E199/E183既有证据整理，最新性能应读E200，不混拼不同轮次的绝对QPS。

[文件清单](manifest.json)逐项绑定发布内容与服务器源SHA；[外部资产边界](external_assets.md)说明未纳入Git的大资产。
