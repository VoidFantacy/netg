# ACSG 当前接续入口

2026-11-10，工作区/data/netg/ACSG。最新完成[E200四多模态四方法重测](entry_method_exploration/20261110_multimodal_four_method_retest_v1/README.md)：COCO/Flickr30k/WebVid/Yandex，NSG/GT10/GT10＋直接残差/外部GATE，真实K1/K100、每K20档L，每点两遍，共640点/1280完整单线程批次/1120万正式查询。测量、原生oracle、独立数值核验和实际图形审阅完成；没有待恢复测量队列，勿据旧PID重复启动。最终交付状态读[state](entry_method_exploration/20261110_multimodal_four_method_retest_v1/state.json)及reviews/delivery_validation.json。

默认E99 GT10保持。COCO/WebVid残差有明确有效区间，Flickr按召回目标取舍，Yandex优先GT10；GATE160个点均被同期其他方法覆盖。先完整读AGENTS、summary、spec，再读s-target和s-experiment。性能主入口为[E200中文报告](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)、[640点CSV](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/points.csv)和K1/K100曲线。全部使用原scalar核，不混旧绝对QPS。

此前残差学习选点/精排导航/门控停止边界保持；E200的GATE是E97外部入口方法。旧模型、科学原件、seal与PDF保留；旧根文档见[E200 source_before](entry_method_exploration/20261110_multimodal_four_method_retest_v1/source_before/)和测量期root_before_final快照。历史M5/B32/SQ条件有效结果不撤销。

论文/汇报先读[论文写作约定](论文写作约定.md)：入口不够好→GT10；好入口后仍有遗漏→直接残差；训练GT、测试评测和线上未知答案分开，完整费用解释替代方案取舍。
