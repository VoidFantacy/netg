# E190：COCO固定候选的评分质量与完整费用

2026-10-28，用户授权“做吧”。正式38点/114完整T1轮，primary校准26点/78轮。范围COCO raw-IP、真实K100；默认E99 GT10保持。

原网格3个新评分点：2个被GT10覆盖，速度筛选1点通过。 密集GT10补充：唯一阳性L400点速度门0、预算Recall门0。 该固定评分版本尚未形成可支付的Recall–QPS改进，停止本版本，默认E99 GT10保持。

| 方法 L200 | Recall@100 | 完整QPS |
| --- | --- | --- |
| GT10 | 95.3444% | 2313.27 |
| B32 | 96.7159% | 2168.62 |
| REUSE-BLOCK | 95.5575% | 1813.32 |
| SQ8-96 | 97.2191% | 1530.95 |

同一候选pool/扫描块逐query一致。COCO L200扫描覆盖18747个遗漏；旧PQ短名单覆盖/救回2131/2131，SQ8为18747/18747。SQ8相对PQ Recall增加1.6616pp。质量机会与完整费用分开，不把扫描覆盖当免费收益。

原pool/块排序/扫描顺序逐query一致，2048码/96原metric精算上限保持；只改扫描后的评分。SQ8码按原base全库QT_8bit minmax编码，无query/GT训练；新增57.75MiB及码位置映射，不清零旧后端费用。原GT10、B32、PQ控制全包与E189一致。

原矩阵29点/87轮，另冻密集GT10补充9点/27轮；补充同窗口SQ8 L400相对阈值GT528速度-2.02%，预算Recall差-0.0398pp。原矩阵L400阳性筛选保留其原身份，候选/参数未改。预设PQ384两级方案未触发：校准PQ384遗漏覆盖/SQ8-96遗漏覆盖=0.3833，门槛0.75；未试其他宽度。

前12K冻结块表/后4K条件校准/正式10K历史曝光，B32完全排除校准。原E189 1570件seal保持；全量补全oracle、三轮bits/SHA、stdlib set第二实现、全base SQ8编码逐字核验及评分抽检通过。不同实现同一执行者，无新盲确认/K1/跨集证据。固定版本收口；Deep块检索未启动。

[完整报告](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/report_zh.md) · [六页PDF](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/ACSG_COCO固定候选排序与完整费用_20261028.pdf) · [协议](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/protocol.md) · [冻结](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/freeze.json) · [条件决定](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/selection.json) · [核验](../entry_method_exploration/20261028_coco_fixed_candidate_scoring_v1/reviews/formal_results_audit.json)。
