# GT10与B32低召回分阶段分析

2026-11-05。按用户定义，低召回是单条Recall@100<10%（命中0–9，恰好10排除）。[完整中文分析](report_zh.md)对照原NSG→GT10→GT10+B32，报告救出、新增、净变化、B32救出来源及与平均召回/完整成本的关系。

主要四个多模态集，全七个L；使用E183原完整窗口，已另从原GT与实际返回复核。没有补做搜索实验，不生成PDF。

- [四集全L失败率图](figures/01_failure_rate_all_L.png) · [SVG](figures/01_failure_rate_all_L.svg)
- [两阶段救出与新增图](figures/02_rescued_and_introduced.png)
- [L200原NSG遗留 / GT10新增问题分解](figures/03_L200_source_decomposition.png)
- [低召回修复与平均Recall收益](figures/04_tail_repair_vs_mean_recall.png)
- [全L阶段分解CSV](analysis/stage_attribution_four_multimodal.csv) · [七集附录](analysis/stage_attribution_all_datasets.csv)
- [原始返回独立实现核验](reviews/raw_audit.json) · [交付收据](delivery_validation.json)

L200核心计数：COCO 0→1→1，Flickr 0→0→0，WebVid 142→53→46，Yandex 174→86→85。GT10有救出也有新增；B32在WebVid额外救出的7条中，5条为原NSG遗留、2条为GT10新增。当前默认、研究停止边界及旧报告原件保持。
