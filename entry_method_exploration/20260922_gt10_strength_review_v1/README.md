# GT10现状、机制与改进方向：阅读入口

2026-09-22研究，截止北京时间17:00。默认WebVid GT10-soft-t1、Yandex GT10-hard及生产E99保持；没有新性能胜者。

- [11页PDF：主报告、改进方向、文献核对](GT10现状与改进方向.pdf)
- [可搜索网页版本](report.html) · [主报告Markdown](report.md)
- [理论推导与反例](theory.md)：独立附录，不包含在上述PDF内。
- [改进方向与停止条件](directions.md)：先完善机制/边界，再证伪低成本路由状态信息；改大图/预算另立范围。
- [15项一手来源](literature/review.md)：明确全文方法核对、摘要与作者仓库的阅读层次。
- [解释审查](reviews/interpretation_review.md) · [数值核验](reviews/numeric_audit.json) · [交付与来源检查](reviews/completion_audit.json)

本轮增加的是旧缓存的23点响应、4组全H分布与同批候选覆盖统计、4幅PNG/SVG/PDF图及理论整理。原始证据没有被改写，新增数据不是新鲜测试，也不构成新方法验收。图、理论和oracle应连同主报告中的条件使用。

`src/`保留分析/绘图/文档生成与核验脚本；多数输出拒绝覆盖。若复核应另建输出版本，不在已有交付目录直接重复执行。报告渲染依赖隔离在`/tmp/acsg_gt10_review_document_tools`，不修改项目环境；已交付PDF/HTML可直接阅读，独立公式附录见theory.md。

`reviews/`保留首次字体和CLI打印失败，成功交付以pdf_verification.json为准。最终状态/时间见[state.json](state.json)，整体文件身份见最终manifest.json。
