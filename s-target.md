# ACSG 后续研究边界

2026-11-10，[E200四方法完整重测](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)已完成640点/1280批次，四多模态集、真实K1/K100、各20档L、每点两遍完整单线程；原生/独立数值核验与实际曲线审阅已完成。没有待恢复的正式测量或训练队列。当前默认保持E99 GT10。

接下来可据已交付曲线组织论文：COCO/WebVid直接补点有实际Recall/QPS同时改善的离散点；Flickr按质量目标取舍；Yandex优先GT10。报告完整有效与无效区间、同L费用和低召回边界，不把两次重复当统计显著性或公开测试当新盲确认。已有640点足以完成本次比较，不按结果追加预算到通过。

研究主线继续为原搜索/GT10入口与直接残差补点。当前学习选点、短名单精排导航和残差前/后门仍停止扩展；本轮GATE仅外部入口基线，未恢复E199残差门。历史M5/B32/SQ条件有效场景保留各自身份。新数据窗、预算、状态续搜、修图或新模型不属于本次后续自动队列，需有新的明确任务与冻结范围。

论文要求读[写作约定](论文写作约定.md)，当前事实读[summary](summary.md)，实现合同读[spec](spec.md)，全部证据读[E200工作目录](entry_method_exploration/20261110_multimodal_four_method_retest_v1/README.md)。此前目标及测量期状态保存在[E200原快照](entry_method_exploration/20261110_multimodal_four_method_retest_v1/source_before/s-target.md)和[最终更新前快照](entry_method_exploration/20261110_multimodal_four_method_retest_v1/reviews/root_before_final/)。
