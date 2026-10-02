# 9月13日研究进展简报

**尚未找到稳定优于当前GT10起点的新方法，默认保持。** Web的补边＋父画像恢复组合修复了compact的部分损失，最终同批五L均有质量改善；相对GT10-soft P仍五L落后。Yandex compact低L小幅正向、高L出现损伤。

全部曲线来自同批历史validation2000，50点、250轮；CPU15、实际及数值库单线程，完整路由＋原NSG＋输出计时。五轮QPS波动不支持稳定整体加速。最终数据已有历史暴露，本次反馈未回流训练或选型。

下表为从原始返回独立集合评分的L128结果（成员是GT10目标；救回/新增失败按query计）：

| 对照 | 新找回成员 | 丢失成员 | Recall变化 pp | 救回 / 新增失败 |
|---|---:|---:|---:|---:|
| Web组合 / compact | 66 | 12 | +0.270 | 4 / 0 |
| Web组合 / GT10-soft P | 274 | 351 | -0.385 | 14 / 13 |
| Y compact / GT10-hard P | 144 | 130 | +0.070 | 8 / 6 |

零命中才算失败，命中1个不失败；净失败减少不保证总Recall提高。成员增损与逐query净命中变化正负部也不同，全部15组两种口径均已核对原表。跨L重复query不作独立样本，以上为最终结果的描述性复算，不是新实验或新性能点。

完整失败表保留401条独立query的全五L、各方法GT10/入口/返回，共10730单元；救回和新增损伤两个方向均保留。

[完整实验报告](../stage35_final_comparison_v1/report.md) · [QPS–Recall图](../stage35_final_comparison_v1/analysis_v1/figures/recall_qps.png) · [QPS–失败率图](../stage35_final_comparison_v1/analysis_v1/figures/failure_qps.png) · [按L三指标](../stage35_final_comparison_v1/analysis_v1/figures/three_metrics_by_L.png) · [双向失败案例](../stage35_final_comparison_v1/supplement_v1/figures/failure_cases_both_directions.png) · [401查询全表](../stage35_final_comparison_v1/supplement_v1/failed_queries_all_L.csv) · [15组复算](member_failure_balance.csv)。

本会话新增训练/ANN/构图/GT/QPS均为0，沿用E94实测成本700800 NSG、560000 HNSW；994.213秒native操作与695.047秒纯wall分别记录。继承训练和GT完整成本缺项保持未知。原定20:00前交接；实际文档收尾超时，未新增训练或查询。整日21:00目标未标完成。
