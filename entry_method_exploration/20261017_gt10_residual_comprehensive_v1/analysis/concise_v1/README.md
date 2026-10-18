# E183 四页简版

- [简版PDF](NETG_E183_NSG_GT10_残差_简版报告_20261018.pdf)
- [简版文字](report_zh.md)
- [315点绘图子集](selected_points.csv)、[L200失败表](failure_queries_L200.csv)
- [原始L200比较](selected_L200_comparisons.csv)、[数据校验清单](manifest.json)、[实际PDF视觉检查](pdf_visual_review.json)

每图只含NSG、GT10、GT10＋残差。Deep/SIFT/WebVid固定soft-t1，其余hard；残差固定对应B32，全L不切换家族。单线程完整端到端QPS为三轮中位数。仅重排既有E183结果，无新增实验、无默认替换。

Git同步报告、汇总数据、配置、源代码和审计。大型原始返回数组、训练/图二进制仍在本地，沿原manifest与SHA引用，不属于本次Git交付。完整结果、详细版与其科学记录均保留。
