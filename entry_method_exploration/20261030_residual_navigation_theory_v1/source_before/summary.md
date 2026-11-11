# ACSG 当前结论

更新于2026-10-30。E194等价省费与查询稳定性实验完成：COCO/WebVid、public与角色去重confirmation各2048query、真实K1/K100，共256正式点/768完整T1批次，另20资格点。全部原生和stdlib核验通过，无待恢复矩阵。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。

全部56个优化配对点六数组逐字节等价；B32候选次序、SQ的pool/扫描块/Top96与访问量一致。4/56配对点通过预定同L完整QPS>=+2%且三轮配对同向筛选，2/28个配置在两窗口均通过。保留2个跨窗口均通过的具体优化配置；其他配置保留原始效应，不默认推广。

| 数据 | 优化 | 通过点 | 两窗均通过配置 | 完整QPS增幅中位数 |
| --- | --- | --- | --- | --- |
| coco | OPT-B32 | 2/16 | 1/8 | +0.87% |
| coco | OPT-SQ | 0/12 | 0/6 | +0.22% |
| webvid2_5m_light_v1 | OPT-B32 | 2/16 | 1/8 | +0.62% |
| webvid2_5m_light_v1 | OPT-SQ | 0/12 | 0/6 | -0.11% |

两窗保留配置明确为COCO与WebVid的K100/L100 OPT-B32，完整QPS增幅分别为+2.18%/+2.53%、+2.34%/+2.24%（public/confirmation）。高L和K1尚未达到本轮稳定筛选；OPT-SQ的Top96改法不推广为稳定优化。

原B32的88点均未被当前GT10网格同时覆盖；原SQ的21/24点被GT10或B32覆盖，另COCO/K100/L400在两窗未被覆盖、COCO/K1/L400仅public未被覆盖。这些只是有限网格结论；尤其SQ对更强B32的费用余量小，不能称优于充分调节预算的B32。WebVid确认K100/L200的SQ救回5074成员并损失1个原命中，原/优化相同，该query净命中未下降。

省费相对原B32或原SQ；是否胜过更大L GT10及强B32，另看同窗口控制。优化不会改变原后端的候选支持与质量边界。完整逐L Recall/QPS、救损、严格失败、三轮范围和控制覆盖见[报告](entry_method_exploration/20261030_residual_optimization_stability_v1/report_zh.md)、[256点](entry_method_exploration/20261030_residual_optimization_stability_v1/analysis/points.csv)、[56配对](entry_method_exploration/20261030_residual_optimization_stability_v1/analysis/optimization_pairs.csv)、[跨窗配置](entry_method_exploration/20261030_residual_optimization_stability_v1/analysis/stability.csv)。GT10/B32共同11档L，有限网格不称全局最优或精确等Recall。

历史有效场景继续保留：[单列证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)记录WebVid M5/B32、COCO B32/SQ。E191 COCO/K1 SQ L400的99.64%/1072.26对GT10 L693的99.64%/817.09（+31.23%）属于原窗口，不能拼入本轮。E193有限学习门6/6组被GT10/B32覆盖，不否定历史有效后端或所有自适应。E192候选支持必要条件仍有效。

确认查询为COCO原未分配身份组、WebVid原源中新抽样并与已登记角色逐向量去重；确认GT全原base/raw-IP精确生成，各固定8条float64复核通过。不承诺全历史未曝光/语义独立；一套图/画像、三轮费用，非跨图/独立人员复现。旧科学产物/PDF/seal不回写；旧根字节由source_before/SHA桥接。大产物/root/acsg-e194-storage，无新PDF。
