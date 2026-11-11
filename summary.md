# ACSG 当前结论

更新于2026-11-10。最新完成E200四多模态集四方法加密重测：COCO/Flickr30k/WebVid/Yandex、NSG/GT10/GT10＋直接残差/外部GATE、真实K1/K100、每K20档L，共640点、1280完整CPU15单线程批次、1120万正式查询。每点恰好两遍，主QPS为两次N/wall的算术平均。**默认保持E99 GT10；残差按数据与质量目标保留，未自动全局替换。**

完整结果读[中文报告](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/report_zh.md)、[640点](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/points.csv)、[1280轮计时](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/rounds.csv)及[Recall@1](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/figures/recall_qps_k1.png)/[Recall@100曲线](entry_method_exploration/20261110_multimodal_four_method_retest_v1/analysis/final_v1/figures/recall_qps_k100.png)。全部方法共用原scalar主核，绝对QPS不与E103优化核或旧轮次拼接。

COCO、WebVid的直接残差有明确有效区间。COCO K1：残差L200为99.1200% / 2423.64 QPS，对GT10 L320的98.8800% / 1695.32，QPS +42.96%；K100：残差L200为96.7159% / 2397.12，对GT10 L256的96.6528% / 2038.59，+17.59%。WebVid K1：残差L640为91.1300% / 526.47，对GT10 L800的90.7500% / 427.63，+23.11%；K100：残差L960为90.0171% / 352.85，对GT10 L1120的89.9997% / 305.80，+15.39%。这些是实际召回与QPS均改善的离散点对，不是等Recall或插值结果。

Flickr有条件性收益：95%门槛下残差对GT10的K1/K100提速24.61%/5.07%，但K100的90%/99%门槛慢5.89%/1.95%。Yandex的B32追加收益小：L200的K1/K100仅增加0.1400/0.0570个百分点、完整平均耗时增加1.64%/2.35%；全部已达到的预定门槛组合仍以GT10更快。WebVid两K到L1600均未达到95%，Yandex K100未达到99%，不外推到未测预算。

GATE为E97外部入口基线，160个点均被同数据/K矩阵内其他方法覆盖；不等同所有学习入口无效。GT10相对NSG在Web/Yandex同L召回均提高；COCO/Flickr K100有微小下降，伴随本轮平均完整耗时减少。残差160个同L点159个Recall增加、1个持平，但每点完整耗时均增加0.32%–20.67%。默认替换不能只看有限网格未覆盖点数。

严重低召回为K100命中0–9个GT成员。L200时NSG→GT10→残差：COCO 0→1→1，Flickr 0→0→0，WebVid 142→53→46，Yandex 174→86→85；GATE分别0/0/112/126。残差进一步救出7/1条Web/Yandex问题，但没有修复COCO新增的那条，不能把平均Recall增加写成普遍解决迷失。本轮残差无逐查询命中数下降；仍有4个正确成员替换事件，涉及两个查询的不同L，均为99→99，原GT和事件计数保留。

正式batch wall合计13723.78s，完整run_suite进程14240.44s；前者已包含于后者，不重复加总。COCO/Flickr新GATE离线准备已记录费用下界2079.17s，Flickr主机重启前未提交费用未知；全部正式测量发生在恢复之后。继承资产的历史构建费用未清零。公开测试已有曝光，方法训练规模/角色不同，不称盲确认或等监督量因果消融。

全部64资格点、640点原生oracle/两轮bits、独立stdlib的640点/1280轮/480配对/96门槛/640覆盖关系与2560个payload核验通过，两张实际曲线已查看。复现与验收读[工作目录](entry_method_exploration/20261110_multimodal_four_method_retest_v1/README.md)和[详细卡片](experiment_history/200_multimodal_four_method_retest_v1.md)。本轮不生成PDF。

研究主线继续为入口改进与直接补点；此前E199学习选点、短名单精排导航和残差门控的停止边界不变。历史E173/E191/E194 M5/B32/SQ条件有效证据仍保留[原身份](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)，不因新比较撤销。前一完成阶段E199及文档报告读[历史索引](s-experiment.md)，本次修改前根文档见[E200快照](entry_method_exploration/20261110_multimodal_four_method_retest_v1/source_before/)及[测量期快照](entry_method_exploration/20261110_multimodal_four_method_retest_v1/reviews/root_before_final/)。

论文继续按[写作约定](论文写作约定.md)：入口不够好→GT10；改善入口后仍有有限预算遗漏→直接残差。训练GT与测试评测分开，线上新查询不读GT，历史替代方案按完整费用解释取舍。
